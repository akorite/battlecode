#pragma once

#include "nav.hpp"
#include "world.hpp"

namespace bc {

struct Choice {
    bool split = false;
    int dir = N;
    int n = 0;
    int dest = -1;
    bool eat = false;
    double score = -1e18;
    std::string why;
    // search bookkeeping
    std::string sprint;      // multi-step MOVE (a sprint trade), empty for one step
    bool terminal = false;   // trade or vetoed: nothing to search past it
    double stepTerm = 0;     // what this step alone earns (eat bonus minus danger)
    int newL = 0;
    std::string path;        // multi-step MOVE through free tiles ("NE"), empty for one step
    bool midEat = false;     // the step before the last one on `path` ate a pearl
    int pathCost = 0;        // segments paid for steps beyond freeSteps(L)
};

// Roles are decided locally every turn from shared facts, so teammates agree
// without talking:
//   grower  - a starting dragon, or anyone long. Farms, buds off short children, avoids fights.
//   swarm   - everyone else. Escorts visible growers, forms squads on long enemies:
//             the closest swarm dragon trades heads, the next (squadSize-1) wait a few
//             tiles back and eat the ceil(L/2) pearls the dead enemy drops.
class Policy {
  public:
    int depthReached() const { return depthReached_; }
    // Debug string for the per-turn LOG line (champion lane tracing).
    std::string dbg() const {
        return " id=" + std::to_string(w_.init.id) + " U=" + std::to_string(w_.t.units) + " g=" + std::to_string(grower_) +
               " fh=" + std::to_string(feedHead_) + " fa=" + std::to_string(feedAge_) + " sc=" + std::to_string(selfChamp_) +
               " qr=" + std::to_string(w_.queenRound) + " ql=" + std::to_string(w_.queenLen) +
               " ch=" + std::to_string(champHead_) + " hd=" + std::to_string(w_.heard.size()) +
               " oq=" + std::to_string(w_.ourQueen) + " hx=" + std::to_string(w_.board.X(w_.head)) + " hy=" + std::to_string(w_.board.Y(w_.head));
    }

    Policy(World& w, Params const& p, double deadline, Out& out) : w_(w), eff_(p), p_(eff_), deadline_(deadline), out_(out) {
        gammaPow_.resize(kPowSize);
        gammaPow_[0] = 1.0;
        for (int i = 1; i < kPowSize; i++) gammaPow_[i] = gammaPow_[i - 1] * p_.gamma;
        farPow_.resize(kPowSize);
        farPow_[0] = 1.0;
        for (int i = 1; i < kPowSize; i++) farPow_[i] = farPow_[i - 1] * p_.gammaFar;
    }

    Choice decide() {
        Board const& b = w_.board;
        adjustByMap();
        L_ = w_.t.length;
        queen_ = w_.init.id == w_.champId();
        lead_ = p_.protectLead && w_.theirQueenDead() && !w_.queenDead(w_.champId());
        hiding_ = p_.queenHide && queen_ && w_.t.round < p_.queenHideUntil && w_.board.NC >= p_.hideMinTiles;
        grower_ = isGrower(w_.init.id, L_) && !hiding_;
        bud_ = w_.t.units < p_.budAlive;
        open_ = bud_ && w_.t.round < p_.openUntil && openMapOk();  // forage-first opening, map-gated
        feedHead_ = -1;
        feedAge_ = 0;
        // A fresh child's setup can eat most of its first turn late in the game:
        // then play a lean one-step turn.
        lean_ = clockNow() > deadline_ - p_.leanMargin;
        w_.pruneHeard(p_);
        if (p_.champOne && !queen_) {
            locateChamp();
            if (selfChamp_) grower_ = true;  // the team's champion plays safe and does not hunt
        }
        if (p_.sonarOn) emitSonar();
        buildBase();
        if (p_.slayAlways && !queen_) {
            Choice sl;
            if (slayQueen(sl)) return sl;
        }
        buildTargets();
        if (!lean_) buildFriendFields();
        else noFriendFields();
        buildSquadTargets();

        // End-game feeding (see Params::feedRound). Under the hide doctrine
        // feeders wake earlier (queenFeedRound) and walk to the queen at the
        // closer queenFeedMargin; before feedRound the queen is the only target.
        int feedAt = p_.queenHide ? std::min(p_.feedRound, p_.queenFeedRound) : p_.feedRound;
        feedAge_ = 0;
        if (!lead_ && !queen_ && !assassin_ && w_.t.round >= feedAt && w_.t.round < p_.feedStop && L_ <= p_.feedMaxLen) {
            int bestLen = L_ + p_.feedMargin - 1;
            int qMargin = p_.queenHide ? p_.queenFeedMargin : p_.feedMargin;
            if (p_.champOne) {
                // One champion: our queen while she lives, else the longest dragon the team knows of.
                if (champHead_ >= 0 && !selfChamp_) {
                    feedHead_ = champHead_;
                    feedAge_ = champAge_;
                }
            } else {
                if (w_.t.round >= p_.feedRound) feedFallback(bestLen);
                // The queen is the win condition: feed her ahead of any longer dragon.
                // A role-2 beacon means she is alive even off-vision. Under
                // hide-and-feed she comes out at queenHideLen (2), so a length-delta
                // margin would bar every feeder; feed her once she is queenFeedMargin.
                for (World::Seen const& s : w_.others)
                    if (!isEnemy(s) && s.id == w_.champId() &&
                        (p_.queenHide ? s.visible >= qMargin : s.visible > L_ + qMargin - 1)) {
                        feedHead_ = s.head;
                        feedAge_ = 0;
                        break;
                    }
                for (World::Heard const& h : w_.heard)
                    if (h.id == w_.champId() && h.role == 2 && !w_.queenDead(w_.champId()) &&
                        (p_.queenHide ? h.len >= qMargin : h.len > L_ + qMargin - 1)) {
                        feedHead_ = h.cell;
                        feedAge_ = std::max(1, w_.t.round - h.round);
                        break;
                    }
            }
            if (feedHead_ >= 0) {
                grower_ = false;
                hunts_.clear();
                escortOf_ = -1;
                int d = distToHead(myDist_, feedHead_);
                bool live = feedAge_ == 0;
                // A champion we only heard (off vision) still takes the drop if the report is fresh.
                bool heardNear = !live && p_.champOne && feedAge_ <= p_.feedHeardDie;
                int fd = p_.champOne ? p_.champFeedDist : p_.feedDist;
                if (d <= fd && L_ >= 2 && w_.t.units >= p_.feedMinUnits && (live || heardNear || !p_.champOne)) {
                    // Step into our own neck: we die here and the pearls land by its head.
                    Choice c;
                    c.dir = w_.t.dir ^ 2;
                    c.dest = b.nb[w_.head * 4 + c.dir];
                    c.why = "feed";
                    c.score = 1e9;
                    return c;
                }
            } else if (!assassin_ && w_.t.round >= p_.feedRound && L_ >= p_.feedMargin && !p_.champOne) {
                grower_ = true;  // nobody visible is longer: we are the one being fed
            }
        }

        // Depth 1 is the plain one-step evaluation; then deepen while the CPU budget lasts.
        std::vector<Choice> first(4);
        std::vector<std::vector<int>> firstBody(4);
        std::vector<int> none;
        for (int d = 0; d < 4; d++) first[d] = scoreFrom(w_.body, L_, d, 0, none, &firstBody[d]);

        // Free multi-steps: the first freeSteps(L) steps of a MOVE cost nothing, so
        // every legal first step also gets up to three non-backtracking continuations,
        // each scored like a one-step move on the state after both steps. Budgeted:
        // only when a second step can be free (or cheaply paid), and capped so the
        // depth-1 evaluation grows less than 2.5x.
        struct Cand {
            Choice c;
            std::vector<int> body;   // own body after both steps
            std::vector<int> eaten;  // pearl tiles taken along the path
        };
        std::vector<Cand> cands;
        if (p_.twoStep && !lean_ && (freeSteps(L_) >= 2 || L_ >= 5)) {
            int order[4] = {0, 1, 2, 3};
            std::sort(order, order + 4,
                      [&](int x, int y) { return first[x].score > first[y].score; });
            int evals = 0;
            std::vector<int> body2;
            for (int pass = 0; pass < 3 && evals < p_.twoStepCap; pass++) {
                for (int oi = 0; oi < 4 && evals < p_.twoStepCap; oi++) {
                    int d = order[oi];
                    Choice const& c1 = first[d];
                    if (c1.dest < 0 || w_.occ[c1.dest] >= 0) continue;  // illegal, or a trade (dies)
                    int d2 = pass == 0 ? d : pass == 1 ? (d + 1) & 3 : (d + 3) & 3;
                    int t2 = b.nb[c1.dest * 4 + d2];
                    if (t2 < 0 || w_.occ[t2] >= 0 || base_[t2] >= INF) continue;
                    bool self = false;
                    for (int x : firstBody[d])
                        if (x == t2) {
                            self = true;
                            break;
                        }
                    // The tail that step 1 vacated may or may not be enterable at
                    // step 2 (engine step semantics are unclear); skip it to be safe.
                    if (!self && !c1.eat && !w_.body.empty() && t2 == w_.body.back()) self = true;
                    if (self) continue;
                    // Step 2 is free iff it fits inside freeSteps(L); past that it costs
                    // a segment, allowed only when the dragon keeps >= 2 after paying.
                    bool paid = freeSteps(L_) < 2;
                    if (paid && (L_ < 4 || c1.newL - 1 < 2)) continue;
                    evals++;
                    std::vector<int> eaten2{c1.dest};  // stepped on: its value is spent
                    Choice c2 = scoreFrom(firstBody[d], c1.newL, d2, 0, eaten2, &body2);
                    if (c2.dest < 0) continue;
                    Cand cd;
                    cd.c = c2;
                    cd.c.dir = d;
                    cd.c.path = std::string(1, DCH[d]) + DCH[d2];
                    cd.c.midEat = c1.eat;
                    cd.c.pathCost = paid ? 1 : 0;
                    double ate1 = c1.eat ? p_.eatBonus : 0.0;
                    cd.c.stepTerm = c2.stepTerm + ate1;
                    cd.c.score = c2.score + ate1;
                    if (paid) {
                        cd.c.newL = c2.newL - 1;
                        if (body2.size() > 1) body2.pop_back();  // paid off the tail
                    }
                    cd.body = body2;
                    if (c1.eat) cd.eaten.push_back(c1.dest);
                    if (c2.eat) cd.eaten.push_back(c2.dest);
                    cands.push_back(cd);
                }
            }
        }
        std::vector<double> ctot(cands.size());
        for (size_t i = 0; i < cands.size(); i++) ctot[i] = cands[i].c.score;

        std::vector<double> total(4);
        for (int d = 0; d < 4; d++) total[d] = first[d].score;
        depthReached_ = 1;
        std::vector<double> tc(cands.size(), -1e18);
        for (int depth = 2; depth <= p_.maxDepth && !lean_ && !timeUp(); depth++) {
            std::vector<double> t(4, -1e18);
            bool complete = true;
            for (int d = 0; d < 4 && complete; d++) {
                Choice const& c = first[d];
                if (c.dest < 0) continue;
                if (c.terminal) { t[d] = c.score; continue; }
                std::vector<int> eaten;
                if (c.eat) eaten.push_back(c.dest);
                double rest = searchFrom(firstBody[d], c.newL, depth - 1, 1, eaten);
                if (timedOut_) complete = false;
                t[d] = rest <= -1e17 ? -900.0 : c.stepTerm + rest;
            }
            for (size_t i = 0; i < cands.size() && complete; i++) {
                Cand const& cd = cands[i];
                if (cd.c.terminal) { tc[i] = cd.c.score; continue; }
                std::vector<int> eaten = cd.eaten;
                double rest = searchFrom(cd.body, cd.c.newL, depth - 1, 1, eaten);
                if (timedOut_) complete = false;
                tc[i] = rest <= -1e17 ? -900.0 : cd.c.stepTerm + rest;
            }
            if (!complete) break;
            total = t;
            ctot = tc;
            depthReached_ = depth;
        }
        Choice best;
        for (int d = 0; d < 4; d++) {
            if (first[d].dest < 0) continue;
            Choice c = first[d];
            c.score = total[d];
            if (c.score > best.score) best = c;
        }
        for (size_t i = 0; i < cands.size(); i++) {
            Choice c = cands[i].c;
            c.score = ctot[i];
            if (c.score > best.score) best = c;
        }
        if (best.dest < 0) {
            // Nothing legal: first try a tile we only gave up as a teammate's last exit,
            // otherwise any well-formed move beats the default suicide.
            best.dir = w_.t.dir;
            best.dest = b.nb[w_.head * 4 + best.dir];
            best.why = "trapped";
            // Doomed: die alone. Prefer an enemy head (trade), then kelp / our own body /
            // a teammate's body (only we die); a teammate's head would take it with us.
            int bestRank = 99;
            for (int d = 0; d < 4; d++) {
                int n = b.nb[w_.head * 4 + d];
                int hid = n >= 0 ? w_.occHeadId[n] : -1;
                bool enemyHead = false, friendHead = false;
                for (World::Seen const& s2 : w_.others)
                    if (s2.id == hid) (isEnemy(s2) ? enemyHead : friendHead) = true;
                int rank = enemyHead ? 0 : friendHead ? 9 : 5;
                if (rank < bestRank) {
                    bestRank = rank;
                    best.dir = d;
                    best.dest = n;
                }
            }
            for (int d = 0; d < 4; d++) {
                int n = b.nb[w_.head * 4 + d];
                if (n < 0 || w_.occ[n] >= 0 || base_[n] < INF || ownCell(n)) continue;
                best.dir = d;
                best.dest = n;
                best.why = "shared-exit";
                break;
            }
            if (best.why == "trapped") {
#ifdef BC_DEBUG
            for (int d = 0; d < 4; d++) {
                int n = b.nb[w_.head * 4 + d];
                char const* r = n < 0 ? "kelp" : n == b.nb[w_.head * 4 + (w_.t.dir ^ 2)] ? "neck"
                              : w_.occ[n] >= 0 ? "dragon" : base_[n] >= INF ? "exit" : "own";
                best.why += std::string(" ") + DCH[d] + ":" + r;
                if (n >= 0 && w_.occ[n] >= 0) best.why += std::to_string(w_.occ[n]);
            }
#endif
            }
        }

        if (p_.sprintTrades && best.why != "trade" && best.why != "defend" && !lean_) {
            std::string path;
            if (sprintTrade(path)) {
                Choice s;
                s.dir = dirFromChar(path[0]);
                s.dest = -1;  // we die with the target: no body to track
                s.sprint = path;
                s.why = "sprint-trade";
                return s;
            }
        }

        Choice split;
        if (trySplit(split, best)) return split;
        // Boxed in: splitting keeps the front half still this turn while the rear half
        // (a new dragon that moves right away) walks off and frees room.
        if (best.score < -500 && p_.champOne && p_.boxFeedDist > 0 && !queen_ && L_ >= 2 && w_.t.round >= p_.queenFeedRound &&
            w_.t.round < p_.feedStop) {
            // Boxed in beside the champion: die here instead of splitting out, so the
            // drop lands next to her.
            if (champHead_ >= 0 && champAge_ <= p_.feedHeardDie + 3 && b.cheb(champHead_, w_.head) <= p_.boxFeedDist) {
                Choice c;
                c.dir = w_.t.dir ^ 2;
                c.dest = b.nb[w_.head * 4 + c.dir];
                c.why = "box-feed";
                c.score = 1e9;
                return c;
            }
        }
        if (best.score < -500 && L_ >= 4 && w_.t.units < w_.init.unitLimit) {
            // Reverse: keep a 2-long stub here, the child (our old tail, facing out)
            // leaves with the rest.
            split.split = true;
            split.n = L_ - 2;
            split.why = "reverse";
#ifdef BC_DEBUG
            for (int d = 0; d < 4; d++)
                split.why += std::string(" ") + DCH[d] + ":" + std::to_string(first[d].dest) + "/" + std::to_string(int(first[d].score)) + "/" + first[d].why;
            split.why += " best=" + best.why;
#endif
            return split;
        }
        return best;
    }

  private:
    struct Target {
        int cell;
        double belief;
        int countdown;  // rounds until the bed spawns, -1 none
        double explore;
    };
    enum class Job { None, Attack, Support };
    struct Hunt {
        World::Seen const* enemy;
        double gain;     // length we expect to come out ahead by
        Job job;
        bool threat;     // it is closing in on one of our growers
    };

    static constexpr int kPowSize = 256;
    std::vector<double> gammaPow_;
    double gp(int k) const { return k < 0 ? 1.0 : k >= kPowSize ? 0.0 : gammaPow_[k]; }
    std::vector<double> farPow_;
    double fp(int k) const { return k < 0 ? 1.0 : k >= kPowSize ? 0.0 : farPow_[k]; }
    struct Hot { int cell; double rate; };
    std::vector<Hot> hot_;

    World& w_;
    Params eff_;              // the doctrine-adjusted copy of the base params
    Params const& p_;         // every read below goes through the adjusted copy
    Out& out_;
    double deadline_ = 1e9;         // seconds on the turn clock
    bool timedOut_ = false;
    int depthReached_ = 0;
    std::vector<int> blkScratch_;
    std::vector<int> wallScratch_;
    std::vector<double> belief_;    // per tile, for lookahead pearl pickup
    std::vector<int> countdown_;

    bool lean_ = false;
    bool bud_ = false;                // breed phase: swarm below budAlive — split over eating, avoid contact
    bool open_ = false;               // forage-first opening: bud_ && round < openUntil, map-gated
    bool openMapOk() const {
        int nc = w_.board.NC;
        if (nc <= p_.openMaxTiles && !(maze_ && nc > p_.openMazeMinTiles)) return true;
        return w_.startUnits >= p_.openMinUnits && nc <= p_.openBroodTiles;
    }
    bool maze_ = false;               // kelp fraction above mazeKelpFrac (corridors: fog stays priced)

    void noFriendFields() {
        Board const& b = w_.board;
        friendDist_.assign(b.NC, INF);
        friendId_.assign(b.NC, -1);
        enemyDist_.assign(b.NC, INF);
        friends_.clear();
        enemies_.clear();
        std::vector<int> blk = ownBlk();
        nav_.bfs(b, w_.head, blk, p_.horizon);
        myDist_ = nav_.dist;
    }

    bool timeUp() {
        if (!timedOut_ && clockNow() >= deadline_) timedOut_ = true;
        return timedOut_;
    }
    Nav nav_;
    int L_ = 2;
    bool grower_ = false;
    bool queen_ = false;            // we are this team's queen (lowest id)
    bool hiding_ = false;           // queen playing small under queenHide
    bool lead_ = false;             // their queen dead, ours alive: pure survival now

    // Always take the enemy-queen kill: if her head is in sight and a path of free tiles within
    // ceil(L/4)+L-2 steps leads onto it, MOVE there. Legality under the engine's payment rule: the first
    // freeSteps(L) steps are free, every later step needs length >= 3 at that moment and costs a
    // segment, so n steps need n <= freeSteps(L) + L - 2 (eating only helps, we assume none). All
    // lower-id dragons have moved already and higher ids move after us, so tiles free now stay free.
    // Path tiles must be in vision (nothing unseen can be standing there) and cross seen edges only.
    bool slayQueen(Choice& out) {
        Board const& b = w_.board;
        World::Seen const* q = nullptr;
        for (World::Seen const& s : w_.others)
            if (isEnemy(s) && s.id <= 1) { q = &s; break; }  // queens are ids 0 and 1: theirs is the enemy-team one
        if (!q || L_ < 2) return false;
        if (p_.slayExemptLongest && w_.queenDead(w_.champId())) {
            // Our queen is dead: the longest dragon decides a double-queen-dead tiebreak.
            // Spare it when another teammate is in sight to take the kill.
            bool longest = true, other = false;
            for (World::Seen const& s : w_.others) {
                if (isEnemy(s)) continue;
                other = true;
                if (s.visible > L_ || (s.visible == L_ && s.id < w_.init.id)) longest = false;
            }
            for (World::Heard const& h : w_.heard)
                if (h.len > L_ || (h.len == L_ && h.id < w_.init.id)) longest = false;
            if (longest && other) return false;
        }
        int reach = std::min(freeSteps(L_) + L_ - 2, p_.slayMaxSteps);
        std::vector<int> blk(b.NC, 0);
        for (int c = 0; c < b.NC; c++)
            if (w_.occ[c] >= 0) blk[c] = INF;
        for (int c : w_.ownExtra) blk[c] = INF;
        markBody(blk, w_.body, L_);
        std::vector<int> dist(b.NC, INF), from(b.NC, -1), dirTo(b.NC, -1);
        std::vector<int> qu{w_.head};
        dist[w_.head] = 0;
        int bestSteps = INF, bestFrom = -1, bestDir = -1;
        for (size_t qi = 0; qi < qu.size(); qi++) {
            int c = qu[qi];
            if (dist[c] + 1 > reach) break;
            for (int d = 0; d < 4; d++) {
                int n = b.nb[c * 4 + d];
                if (n < 0 || !b.side(c, d).seen) continue;
                if (n == q->head) {
                    if (dist[c] + 1 < bestSteps) bestSteps = dist[c] + 1, bestFrom = c, bestDir = d;
                    continue;
                }
                if (dist[n] != INF || blk[n] > 1 || !w_.visible(n)) continue;
                dist[n] = dist[c] + 1;
                from[n] = c;
                dirTo[n] = d;
                qu.push_back(n);
            }
            if (bestSteps < INF) break;  // BFS order: the first hit is a shortest path
        }
        if (bestSteps == INF) return false;
        std::string rev(1, DCH[bestDir]);
        for (int c = bestFrom; c != w_.head; c = from[c]) rev += DCH[dirTo[c]];
        out.sprint.assign(rev.rbegin(), rev.rend());
        out.dir = dirFromChar(out.sprint[0]);
        out.dest = -1;  // we die with her
        out.why = "slay-reach";
        out.score = 1e9;
        out.terminal = true;
        return true;
    }
    std::vector<int> base_;       // other dragons' segments = INF, plus own stray segments
    std::vector<Target> targets_;
    std::vector<int> friendDist_; // min distance from any visible teammate head
    std::vector<int> friendId_;
    std::vector<int> enemyDist_;
    struct FriendField { int id; bool grower; int head; int len; std::vector<int> dist; };
    std::vector<FriendField> friends_;
    struct EnemyField { int id; int head; int visible; std::vector<int> dist; };
    std::vector<EnemyField> enemies_;  // the nearest visible enemy heads, with their BFS fields
    std::vector<EnemyField> heardEnemies_;  // relayed enemy sightings, with their BFS fields
    std::vector<int> myDist_;     // from our head as it is now
    std::vector<Hunt> hunts_;
    int escortOf_ = -1;           // head tile of the grower we escort, -1 none
    int feedHead_ = -1;           // head of the longer teammate we are walking to, -1 none
    int feedAge_ = 0;             // rounds since feedHead_ was seen (0 = in vision now)
    int champHead_ = -1;          // where the champion is (freshest evidence), -1 unknown
    int champAge_ = 0;            // rounds since that evidence
    int champLen_ = 0;
    int champId_ = -1;
    bool champIsQueen_ = false;
    bool selfChamp_ = false;      // queen-less team and we are the longest dragon known: we are the champion

    // Who is the champion? Our queen while she is alive (any evidence <= champMemory rounds old:
    // sight, her beacon, or a relayed report); otherwise, from champFallbackRound, the longest
    // dragon known (ties: lowest id), possibly ourselves. Everybody runs the same rule on
    // gossiped evidence, so the team converges on one champion instead of each long dragon
    // electing itself.
    void locateChamp() {
        champHead_ = -1;
        champAge_ = 0;
        champLen_ = 0;
        champId_ = -1;
        champIsQueen_ = false;
        selfChamp_ = false;
        if (w_.t.round < std::min(p_.queenFeedRound, p_.feedRound) - 40) return;
        if (w_.ourQueen >= 0 && !w_.queenDead(w_.ourQueen) && w_.queenRound >= 0 && w_.t.round - w_.queenRound <= p_.champMemory) {
            champHead_ = w_.queenCell;
            champAge_ = w_.t.round - w_.queenRound;
            champLen_ = w_.queenLen;
            champId_ = w_.ourQueen;
            champIsQueen_ = true;
            return;
        }
        if (w_.t.round < p_.champFallbackRound) return;
        if (w_.chRound >= 0 && w_.t.round - w_.chRound <= p_.champMemory) {
            champHead_ = w_.chCell;
            champAge_ = w_.t.round - w_.chRound;
            champLen_ = w_.chLen;
            champId_ = w_.chId;
        }
        // Nobody (us included) is long enough to be worth feeding: forage on (a remnant of length-3
        // dragons feeding each other wiped out a whole team on default s101).
        if (std::max(L_, champHead_ >= 0 ? champLen_ : 0) < p_.feedMargin) {
            champHead_ = -1;
            return;
        }
        if (champHead_ < 0 || L_ > champLen_ || (L_ == champLen_ && w_.init.id < champId_)) {
            selfChamp_ = true;
            champHead_ = -1;
        }
    }

    // Old-style target (champOne off): the longest visible teammate >= bestLen+1, or any heard grower.
    void feedFallback(int bestLen) {
        for (World::Seen const& s : w_.others)
            if (!isEnemy(s) && s.visible > bestLen) {
                bestLen = s.visible;
                feedHead_ = s.head;
                feedAge_ = 0;
            }
        for (World::Heard const& h : w_.heard)
            if (h.role >= 1 && h.len > bestLen) {
                bestLen = h.len;
                feedHead_ = h.cell;
                feedAge_ = std::max(1, w_.t.round - h.round);
            }
    }
    bool assassin_ = false;       // assigned to the queen-assassin squad this turn
    int assassinCell_ = -1;       // where the enemy queen was last reported (or seen)

    // Our sonar traffic for the turn: a beacon in every direction, plus one
    // enemy report aimed where a teammate is likeliest to pick it up.
    void adjustByMap() {
        // Maze maps (Portals: walls on ~28% of edges) paralyse the swarm if every
        // corridor mouth counts as a pocket — drop pocket fear there.
        maze_ = w_.kelpFraction() > p_.mazeKelpFrac;
        if (maze_) eff_.wPocket = 0.0;
        return;  // brawl overrides stay off pending their own A/B
        if (!w_.mapBrawl()) return;
        eff_.champRound = eff_.champRoundBrawl;
        eff_.growerMinUnits = eff_.growerMinUnitsBrawl;
        eff_.heardMemory = eff_.heardMemoryBrawl;
        eff_.feedRound = eff_.feedRoundBrawl;
    }

    uint64_t stamp(uint64_t m) const { return p_.sonarKeyed ? msgStamp(m, w_.t.round, w_.init.team) : m; }

    void emitSonar() {
        Board const& b = w_.board;
        // role 2 = the queen herself: teammates can feed her and tell she's alive.
        int role = (w_.init.id == w_.champId()) ? 2 : (grower_ ? 1 : 0);
        role |= (w_.ourQueen >= 0 ? w_.ourQueen + 1 : 0) << 2;
        uint64_t beacon = msgBeacon(w_.init.id, b.X(w_.head), b.Y(w_.head), L_, role,
                                    p_.protectLead && w_.theirQueenDead() ? 1 : 0);
        World::Seen const* foe = nullptr;
        // The queen outranks any longer enemy: her position feeds the assassin squad.
        for (World::Seen const& s : w_.others)
            if (isEnemy(s) && s.id == w_.enemyQueen()) { foe = &s; break; }
        if (!foe)
            for (World::Seen const& s : w_.others)
                if (isEnemy(s) && (!foe || s.visible > foe->visible)) foe = &s;
        int eDir = -1;
        if (foe) {
            // prefer the ray that delivers to a visible ally (closest to the foe)
            int bestAlly = -1, bestD = INF;
            for (int d = 0; d < 4; d++) {
                int hit = firstOnRay(d);
                if (hit >= 0 && w_.occ[hit] >= 0 && !ownCell(hit)) {
                    bool ally = false;
                    for (World::Seen const& s : w_.others)
                        if (s.id == w_.occ[hit] && !isEnemy(s)) ally = true;
                    if (ally) {
                        int dd = b.cheb(hit, foe->head);
                        if (dd < bestD) { bestD = dd; bestAlly = d; }
                    }
                }
            }
            if (bestAlly < 0) {
                // no visible teammate on a ray: rotate among dirs not blocked by us
                for (int k = 0; k < 4 && bestAlly < 0; k++) {
                    int d = (w_.t.round + w_.init.id + k) & 3;
                    int hit = firstOnRay(d);
                    if (hit < 0 || !ownCell(hit)) bestAlly = d;
                }
            }
            eDir = bestAlly;
        }
        // Two pings a turn keep the protocol alive without eating the decision
        // budget: each SONAR line plus its ping cost ~5M points on a ~75M budget.
        // Rotating the beacon direction still covers the ring over four turns.
        int bDir = (w_.t.round + w_.init.id) & 3;
        // Champion relay (champion lane): whoever knows where the champion is tells one more
        // teammate; the champion herself tells every free ray. Receivers re-forward, so the
        // position gossips across the swarm and feeders far away can still walk to her.
        int rDirs = 0;  // bitmask of relay rays
        int rId = -1, rCell = -1, rLen = 0, rAge = 0, rQueen = 0;
        if (p_.champRelay && p_.champOne && w_.ourQueen >= 0) {
            bool self = false;
            if (queen_ && w_.t.round >= p_.queenRelayFrom && w_.t.round < p_.feedStop) {
                rId = w_.init.id; rCell = w_.head; rLen = L_; rQueen = 1; self = true;
            } else if (selfChamp_ && w_.t.round >= p_.champRelayFrom && w_.t.round < p_.feedStop) {
                rId = w_.init.id; rCell = w_.head; rLen = L_; self = true;
            } else if (w_.queenRound >= 0 && !w_.queenDead(w_.ourQueen) && w_.t.round >= p_.queenRelayFrom && w_.t.round < p_.feedStop &&
                       w_.t.round - w_.queenRound <= p_.champRelayAge) {
                rId = w_.ourQueen; rCell = w_.queenCell; rLen = w_.queenLen; rAge = w_.t.round - w_.queenRound; rQueen = 1;
            } else if (w_.chRound >= 0 && w_.t.round >= p_.champRelayFrom && w_.t.round < p_.feedStop &&
                       w_.t.round - w_.chRound <= p_.champRelayAge) {
                rId = w_.chId; rCell = w_.chCell; rLen = w_.chLen; rAge = w_.t.round - w_.chRound;
            }
            if (rId >= 0 && self) {
                for (int d = 0; d < 4; d++)
                    if (d != eDir && d != bDir) rDirs |= 1 << d;
            } else if (rId >= 0) {
                int bestD = -1, bestS = -1;
                for (int k = 0; k < 4; k++) {
                    int d = (w_.t.round / 2 + w_.init.id + k) & 3;  // rotate so successive turns cover the ring
                    if (d == eDir || d == bDir) continue;
                    int hit = firstOnRay(d);
                    int sc = 1;  // unseen: may reach a teammate beyond vision
                    if (hit >= 0) {
                        sc = 0;
                        if (!ownCell(hit))
                            for (World::Seen const& s : w_.others)
                                if (s.id == w_.occ[hit]) sc = isEnemy(s) ? 0 : 3;
                    }
                    if (sc > bestS) { bestS = sc; bestD = d; }
                }
                if (bestD >= 0 && bestS > 0) rDirs |= 1 << bestD;
            }
        }
        for (int d = 0; d < 4; d++) {
            if (d == eDir) {
                // Enemy-queen sightings carry a flag so hunters know who to kill.
                out_.sonar(d, stamp(msgEnemy(w_.init.id, b.X(foe->head), b.Y(foe->head), foe->visible,
                                            foe->id == w_.enemyQueen() ? 1 : 0)));
            } else if (d == bDir) {
                out_.sonar(d, stamp(beacon));
            } else if (rDirs >> d & 1) {
                out_.sonar(d, stamp(msgChamp(rId, b.X(rCell), b.Y(rCell), rLen, rQueen, rAge)));
            }
        }
    }

    // First occupied tile on the ray from our head in direction d, while the ray
    // is still inside vision; -1 = nothing seen on it.
    int firstOnRay(int d) const {
        Board const& b = w_.board;
        int c = w_.head;
        for (int i = 0; i < 6; i++) {
            int n = b.nb[c * 4 + d];
            if (n < 0) return -1;
            if (!w_.visible(n)) return -1;
            if (w_.occ[n] >= 0 || ownCell(n)) return n;
            c = n;
        }
        return -1;
    }

    bool ownCell(int c) const {
        for (int x : w_.body)
            if (x == c) return true;
        for (int x : w_.ownExtra)
            if (x == c) return true;
        return false;
    }

    bool isEnemy(World::Seen const& s) const { return s.team != w_.init.team; }
    // The designated early champion grows into the tiebreak dragon; anyone else
    // promotes once long enough to matter or once the swarm is established.
    bool isGrower(int id, int len) const {
        if (len >= p_.promoteLen) return true;
        if (id == w_.champId()) return true;  // the queen never fights
        bool growPhase = w_.t.units >= p_.growerMinUnits || w_.t.round >= p_.growRound;
        return growPhase && (w_.isInitial(id) || id == w_.champId());
    }
    // Head-on trades are one-for-one: worth it while our army is not tiny and we do
    // not give up much more length than we take.
    bool tradeOk(int myLen, int enemyLen) const {
        return w_.t.units >= (lead_ ? p_.leadTradeMinUnits : p_.tradeMinUnits) && myLen <= enemyLen + p_.tradeSlack;
    }
    bool survival() const { return w_.t.units <= p_.survivalUnits && !open_; }  // a small brood is a start, not a remnant

    // Whoever has more heads around a trade site eats most of the pearls the two dead
    // dragons drop. Counts heads near `site`, leaving out ourselves and the enemy we
    // would trade with (`skip`, -1 none).
    bool localOk(int site, int skip) const {
        Board const& b = w_.board;
        int mine = 0, theirs = 0;
        for (World::Seen const& s : w_.others) {
            if (s.id == skip || b.cheb(s.head, site) > p_.localRadius) continue;
            (isEnemy(s) ? theirs : mine)++;
        }
        return mine >= theirs;
    }
    // How far an enemy head can move in one turn: a MOVE of k steps needs length k + 1.
    int reachOf(int visible) const { return std::min(std::max(freeSteps(visible) + visible - 2, 1), p_.reachCap); }
    bool midGame() const { return w_.t.round >= p_.earlyEnd; }
    bool lateGame() const { return w_.t.round >= p_.midEnd; }

    std::vector<int> ownBlk() const {
        std::vector<int> blk = base_;
        markBody(blk, w_.body, L_);
        return blk;
    }

    // Distance from a precomputed field to any tile next to `head` (the head itself is blocked).
    int distToHead(std::vector<int> const& dist, int head) const {
        Board const& b = w_.board;
        int best = INF;
        for (int k = 0; k < 4; k++) {
            int n = b.nb[head * 4 + k];
            if (n >= 0) best = std::min(best, dist[n]);
        }
        return best;
    }

    void buildBase() {
        Board const& b = w_.board;
        base_.assign(b.NC, 0);
        for (int c = 0; c < b.NC; c++)
            if (w_.occ[c] >= 0) base_[c] = INF;
        for (int c : w_.ownExtra) base_[c] = INF;

        // Never take a teammate's last way out.
        std::vector<int> blk = base_;
        markBody(blk, w_.body, L_);
        for (World::Seen const& s : w_.others) {
            if (isEnemy(s)) continue;
            int exits = 0, exit = -1;
            for (int d = 0; d < 4; d++) {
                int n = b.nb[s.head * 4 + d];
                if (n >= 0 && blk[n] <= 1) exits++, exit = n;
            }
            if (exits == 1) base_[exit] = INF;
        }
    }

    void buildTargets() {
        Board const& b = w_.board;
        targets_.clear();
        belief_.assign(b.NC, 0.0);
        countdown_.assign(b.NC, -1);
        for (int c = 0; c < b.NC; c++) {
            double bel = w_.belief(c, p_);
            int cd = (b.bed[c] == 1 && w_.next[c] >= 0 && w_.next[c] < p_.horizon) ? w_.next[c] : -1;
            belief_[c] = bel;
            countdown_[c] = cd;
            // Forage-first opening: swarm dragons get a stronger scout pull so the
            // brood fans out onto fresh beds instead of circling known ground.
            double exv = (open_ && !queen_ && !grower_) ? p_.openExplore : p_.exploreValue;
            double ex = w_.seenRound[c] < 0 ? exv : 0.0;  // never-seen tile
            if (bel > 0.02 || cd >= 0 || ex > 0) targets_.push_back({c, bel, cd, ex});
        }
        hot_.clear();
        for (int c = 0; c < b.NC; c++) {
            if (b.bed[c] != 1 || b.gapMax[c] <= 0) continue;
            double rate = 2.0 / (b.gapMin[c] + b.gapMax[c]);
            if (rate >= p_.hotRate) hot_.push_back({c, rate});
        }
        // Unpaired portal ends: pull dragons to their lip cells so a scout can
        // cross and learn the partner, opening the far half of the map. Maze-only:
        // on open maps the pull outbids real food and parks workers on the lips.
        if (w_.kelpFraction() > p_.mazeKelpFrac)
            for (auto const& pe : w_.portalEnds) {
                if (pe.second.size() != 1) continue;
                World::PortalEnd const& e = pe.second.front();
                int lips[2] = {e.orient == 0 ? b.id(e.x, e.y - 1) : b.id(e.x - 1, e.y),
                               b.id(e.x, e.y)};
                for (int c2 : lips)
                    if (b.bed[c2] != 1) targets_.push_back({c2, 0.0, -1, p_.wPortalScout});
            }
    }

    void buildFriendFields() {
        Board const& b = w_.board;
        friendDist_.assign(b.NC, INF);
        friendId_.assign(b.NC, -1);
        enemyDist_.assign(b.NC, INF);
        friends_.clear();
        enemies_.clear();
        std::vector<int> blk = ownBlk();
        // Only the nearest heads matter; this bounds CPU when 60+ dragons crowd the vision.
        std::vector<World::Seen const*> near;
        for (World::Seen const& s : w_.others) near.push_back(&s);
        std::sort(near.begin(), near.end(), [&](World::Seen const* x, World::Seen const* y) {
            return b.cheb(x->head, w_.head) < b.cheb(y->head, w_.head);
        });
        if (static_cast<int>(near.size()) > p_.maxRivalFields) near.resize(p_.maxRivalFields);
        for (World::Seen const* sp : near) {
            World::Seen const& s = *sp;
            nav_.bfs(b, s.head, blk, p_.horizon);
            if (isEnemy(s)) {
                for (int c = 0; c < b.NC; c++) enemyDist_[c] = std::min(enemyDist_[c], nav_.dist[c]);
                enemies_.push_back({s.id, s.head, s.visible, nav_.dist});
                continue;
            }
            for (int c = 0; c < b.NC; c++) {
                int d = nav_.dist[c];
                if (d < friendDist_[c] || (d == friendDist_[c] && d != INF && s.id < friendId_[c])) {
                    friendDist_[c] = d;
                    friendId_[c] = s.id;
                }
            }
            friends_.push_back({s.id, isGrower(s.id, s.visible), s.head, s.visible, nav_.dist});
        }

        // Heard teammates extend friendDist_ past vision (skip ids we can see -
        // their live field is fresher), and relayed enemies get their own fields.
        auto seenIds = [&](int id) {
            for (World::Seen const& s : w_.others)
                if (s.id == id) return true;
            return false;
        };
        std::vector<World::Heard const*> hf;
        for (World::Heard const& h : w_.heard)
            if (!seenIds(h.id) && w_.t.round - h.round <= p_.heardFresh) hf.push_back(&h);
        std::sort(hf.begin(), hf.end(), [&](World::Heard const* x, World::Heard const* y) {
            return b.cheb(x->cell, w_.head) < b.cheb(y->cell, w_.head);
        });
        if (static_cast<int>(hf.size()) > p_.maxHeardFields) hf.resize(p_.maxHeardFields);
        for (World::Heard const* hp : hf) {
            nav_.bfs(b, hp->cell, blk, p_.horizon);
            for (int c = 0; c < b.NC; c++) {
                int d = nav_.dist[c];
                if (d < friendDist_[c] || (d == friendDist_[c] && d != INF && hp->id < friendId_[c])) {
                    friendDist_[c] = d;
                    friendId_[c] = hp->id;
                }
            }
        }
        heardEnemies_.clear();
        std::vector<World::Heard const*> he;
        for (World::Heard const& h : w_.heardEnemies) he.push_back(&h);
        // Queen sightings always get a field: the assassin squad navigates by them.
        std::sort(he.begin(), he.end(), [&](World::Heard const* x, World::Heard const* y) {
            if ((x->role == 1) != (y->role == 1)) return x->role == 1;
            return b.cheb(x->cell, w_.head) < b.cheb(y->cell, w_.head);
        });
        if (static_cast<int>(he.size()) > p_.maxHeardEnemyFields) he.resize(p_.maxHeardEnemyFields);
        for (World::Heard const* hp : he) {
            nav_.bfs(b, hp->cell, blk, p_.horizon);
            // id -2 marks a relayed sighting of their queen.
            heardEnemies_.push_back({hp->role == 1 ? -2 : -1, hp->cell, hp->len, nav_.dist});
        }

        nav_.bfs(b, w_.head, blk, p_.horizon);
        myDist_ = nav_.dist;
    }

    // How many visible swarm teammates are closer than us to `head` (ties by id).
    int swarmRank(int head, int mine) const {
        int rank = 0;
        for (FriendField const& f : friends_) {
            if (f.grower) continue;
            int d = distToHead(f.dist, head);
            if (d < mine || (d == mine && d != INF && f.id < w_.init.id)) rank++;
        }
        return rank;
    }

    void buildSquadTargets() {
        Board const& b = w_.board;
        hunts_.clear();
        escortOf_ = -1;
        assassin_ = false;
        assassinCell_ = -1;
        if (grower_ || queen_) return;  // the queen never hunts or escorts
        assignAssassin();

        // Enemy heads near one of our visible growers are threats whatever their length.
        for (World::Seen const& e : w_.others) {
            if (!isEnemy(e)) continue;
            bool threat = false;
            double protect = 0;
            for (FriendField const& f : friends_)
                if (f.grower && b.cheb(f.head, e.head) <= p_.escortRadius) {
                    threat = true;
                    for (World::Seen const& s : w_.others)
                        if (s.id == f.id) protect = std::max<double>(protect, s.visible);
                }
            double gain = threat ? std::max<double>(protect, e.visible) - L_ : e.visible - L_;
            // Their queen is always worth hunting: a head-to-head kills her at any length.
            bool queenTgt = e.id == w_.enemyQueen();
            // Forage-first opening: swarm dragons eat and split, not skirmish —
            // only their queen and genuine grower-threats still pull a mission.
            bool worth = queenTgt || (threat ? e.visible >= 2
                                             : (p_.openHunt || !open_) && tradeOk(L_, e.visible));
            if (!worth) continue;
            int mine = distToHead(myDist_, e.head);
            if (mine == INF) continue;
            int rank = swarmRank(e.head, mine);
            Job job = rank == 0 ? Job::Attack : rank < p_.squadSize ? Job::Support : Job::None;
            // Assassins keep the mission: only their queen or a grower threat counts.
            if (assassin_ && !queenTgt && !threat) job = Job::None;
            if (job != Job::None) hunts_.push_back({&e, gain, job, threat});
        }
        if (assassin_)
            for (World::Seen const& e : w_.others)
                if (isEnemy(e) && e.id == w_.enemyQueen()) assassinCell_ = e.head;  // live fix beats the report

        // Idle escort: stay near the closest visible grower — the queen first —
        // if we are among its first escorts.
        if (!assassin_ && hunts_.empty() && midGame()) {
            int bestD = INF;
            for (int pass = 0; pass < 2 && escortOf_ < 0; pass++) {
                for (FriendField const& f : friends_) {
                    if (!f.grower) continue;
                    bool isQueen = f.id == w_.champId();
                    if ((pass == 0) != isQueen) continue;
                    int d = distToHead(myDist_, f.head);
                    if (d == INF || d >= bestD) continue;
                    if (swarmRank(f.head, d) < p_.escortCount) {
                        bestD = d;
                        escortOf_ = f.head;
                    }
                }
            }
        }
    }

    // Queen-assassin assignment, computed locally so every teammate ranks itself
    // against the same shared picture (visible friends + heard swarm beacons).
    // The freshest queen-flagged relay within assassinMaxAge picks the squad: the
    // assassinCount swarm dragons nearest its cell go, provided their combined
    // length plausibly fights through to her.
    void assignAssassin() {
        if (hiding_) return;
        Board const& b = w_.board;
        World::Heard const* rep = nullptr;
        for (World::Heard const& h : w_.heardEnemies)
            if (h.role == 1 && w_.t.round - h.round <= p_.assassinMaxAge &&
                (!rep || h.round > rep->round || (h.round == rep->round && h.cell < rep->cell)))
                rep = &h;
        if (!rep) return;
        int cell = rep->cell;

        // Candidates: me plus every swarm dragon whose position is shared —
        // visible teammates via their fields, heard swarm beacons via Chebyshev
        // (one metric for all so the ranking is consistent across processes).
        struct Cand { int d, id, len; };
        std::vector<Cand> cand;
        int mine = b.cheb(w_.head, cell);
        if (mine > p_.assassinMaxDist) return;  // too far: a nearer squad re-forms around the next report
        cand.push_back({mine, w_.init.id, L_});
        for (FriendField const& f : friends_)
            if (!f.grower) cand.push_back({b.cheb(f.head, cell), f.id, f.len});
        auto seenIds = [&](int id) {
            for (World::Seen const& s : w_.others)
                if (s.id == id) return true;
            return false;
        };
        for (World::Heard const& h : w_.heard)
            if (h.role == 0 && !seenIds(h.id))
                cand.push_back({b.cheb(h.cell, cell), h.id, h.len});
        std::sort(cand.begin(), cand.end(), [](Cand const& x, Cand const& y) {
            return x.d != y.d ? x.d < y.d : x.id < y.id;
        });
        double force = 0;
        bool in = false;
        for (int i = 0; i < p_.assassinCount && i < static_cast<int>(cand.size()); i++) {
            force += cand[i].len;
            if (cand[i].id == w_.init.id) in = true;
        }
        if (in && force >= rep->len * p_.assassinForce) {
            assassin_ = true;
            assassinCell_ = cell;
        }
    }

    Hunt const* huntAt(int headCell) const {
        for (Hunt const& h : hunts_)
            if (h.enemy->head == headCell) return &h;
        return nullptr;
    }

    bool nextToEnemyHead(int cell, int& enemyLen, bool& isHunt, int& enemyId) const {
        Board const& b = w_.board;
        enemyLen = 0;
        enemyId = -1;
        isHunt = false;
        bool found = false;
        for (World::Seen const& s : w_.others) {
            if (!isEnemy(s)) continue;
            for (int d = 0; d < 4; d++)
                if (b.nb[s.head * 4 + d] == cell) {
                    found = true;
                    if (s.visible >= enemyLen) { enemyLen = s.visible; enemyId = s.id; }
                    if (huntAt(s.head)) isHunt = true;
                }
        }
        return found;
    }

    // One step from a simulated state: `body` (head first, true length L) after k of
    // our own moves this turn-plan, with `eaten` pearls already taken along the way.
    // k = 0 is the real move; deeper k is lookahead with other dragons held still.
    Choice scoreFrom(std::vector<int> const& body, int L, int d, int k, std::vector<int> const& eaten,
                     std::vector<int>* nextBody = nullptr) {
        Board const& b = w_.board;
        Choice c;
        c.dir = d;
        int head = body.front();
        int dest = b.nb[head * 4 + d];
        if (dest < 0) {
            // A portal whose partner we have not seen still crosses — the engine
            // teleports the head to the far neck. Score the crossing as exploration
            // so a dragon learns the pair and the far half of the map opens up.
            Edge const& e = b.side(head, d);
            if (k == 0 && e.kind == 2 && e.partnerOrient < 0) {
                c.dest = -1;
                c.score = p_.wScout - p_.wBlindQuiet * (1.0 + 0.25 * L);
                c.why = "scout";
                c.terminal = true;
            }
            return c;
        }
        for (int x : body)
            if (x == dest) return c;  // own segment, tail included
        if (w_.occ[dest] < 0 && base_[dest] >= INF) return c;  // own stray segment or a teammate's last exit

        if (w_.occ[dest] >= 0) {
            if (k > 0) return c;  // lookahead treats other dragons as walls
            // Stepping onto an enemy head kills both. Swarm does it on squad targets;
            // anyone does it when the trade is clearly good.
            int hid = w_.occHeadId[dest];
            for (World::Seen const& s : w_.others) {
                if (s.id != hid || !isEnemy(s)) continue;
                Hunt const* h = huntAt(s.head);
                double gain = s.visible - L;
                if (h && !grower_ && !queen_) {
                    c.dest = dest;
                    c.score = 100.0 + h->gain;
                    c.why = h->threat ? "defend" : "trade";
                    c.terminal = true;
                } else if (s.id == w_.enemyQueen() && (assassin_ || L + p_.queenTradeSlack >= s.visible) && !grower_ && !queen_) {
                    c.dest = dest;
                    c.score = 80.0 + gain;
                    c.why = "slay";
                    c.terminal = true;
                } else if (tradeOk(L, s.visible) && !grower_ && !queen_) {
                    c.dest = dest;
                    c.score = 50.0 + gain;
                    c.why = "trade";
                    c.terminal = true;
                }
            }
            return c;
        }

        c.dest = dest;
        bool taken = std::find(eaten.begin(), eaten.end(), dest) != eaten.end();
        if (k == 0) c.eat = w_.seenRound[dest] == w_.t.round && w_.seenPearl[dest];
        else c.eat = !taken && (belief_[dest] >= 0.5 || (countdown_[dest] >= 0 && countdown_[dest] <= k));
        int newL = L + (c.eat ? 1 : 0);

        std::vector<int> local;
        std::vector<int>& nb2 = nextBody ? *nextBody : local;
        nb2.clear();
        nb2.reserve(body.size() + 1);
        nb2.push_back(dest);
        nb2.insert(nb2.end(), body.begin(), body.end());
        if (!c.eat && static_cast<int>(nb2.size()) > newL) nb2.pop_back();
        c.newL = newL;

        std::vector<int>& blk = blkScratch_;
        blk = base_;
        markBody(blk, nb2, newL);

        int need = std::min(static_cast<int>(p_.spaceFactor * newL) + p_.spaceMargin, b.NC / 2);
        int space = nav_.flood(b, dest, blk, need + 1);
        // Reverse by splitting: a dragon of 4+ can split off everything but a 2-long stub;
        // the child's head is our tail and faces out. So a dead end (a fountain corridor,
        // a pocket) is fine as long as the tail side has room; it costs the 2-long stub.
        bool viaReverse = false;
        if (space < need && newL >= 4 && static_cast<int>(body.size()) == newL) {
            int childNeed = std::min(static_cast<int>(p_.spaceFactor * (newL - 2)) + p_.spaceMargin, b.NC / 2);
            std::vector<int> blk2 = base_;
            for (size_t i = 0; i + 1 < body.size(); i++) blk2[body[i]] = INF;
            int tail = body.back();
            int room = 0;
            for (int q = 0; q < 4 && room < childNeed; q++) {
                int n = b.nb[tail * 4 + q];
                if (n >= 0 && blk2[n] <= 1) room = std::max(room, nav_.flood(b, n, blk2, childNeed + 1) + 1);
            }
            if (room >= childNeed) viaReverse = true;
        }

        // Queen dead ends (trapOn): a closed region with no loop is a trap the queen
        // never leaves — fountain corridors, tree pockets. The swarm can lose a stub;
        // she cannot. Only our own body walls the scan: a cell it plugs stays plugged
        // while she cannot advance, while anything else may move off.
        if (queen_ && p_.trapOn && !viaReverse) {
            wallScratch_.assign(b.NC, 0);
            for (int oc : nb2) wallScratch_[oc] = INF;
            for (int oc : w_.ownExtra) wallScratch_[oc] = INF;
            Scan sc = nav_.deadEnd(b, dest, wallScratch_, p_.trapScanCells);
            bool loopRoom = sc.cycle && sc.cells > newL;
            bool tiny = sc.cells <= newL + p_.trapMargin;
            bool tree = sc.exhausted && !sc.cycle;
            if (!loopRoom && (tiny || tree)) {
                c.stepTerm = -2000 + sc.cells;  // least-bad largest region wins if all vetoed
                c.terminal = true;
                c.why = "deadend";
                return c;
            }
        }

        nav_.bfs(b, dest, blk, p_.horizon);
        std::vector<int> const& dist = nav_.dist;

        double value = 0;
        for (Target const& t : targets_) {
            if (t.cell == dest) continue;
            int dd = dist[t.cell];
            if (dd == INF) continue;
            if (!eaten.empty() && std::find(eaten.begin(), eaten.end(), t.cell) != eaten.end()) continue;
            int m = dd + 1 + k;  // moves from now, counting the ones already planned
            double v = t.belief * gp(m);
            if (t.countdown >= 0 && t.belief < 0.5)
                v = std::max(v, 0.9 * gp(std::max(m, t.countdown + 1)));
            if (v > 0) {
                int fd = friendDist_[t.cell];
                if (fd < m || (fd == m && friendId_[t.cell] < w_.init.id)) v = 0;
                else if (enemyDist_[t.cell] < m) v *= p_.enemyCloserFactor;
            }
            v += t.explore * gp(m);
            if (assassin_) v *= p_.assassinForage;  // on mission: pearls are a detour
            value += v;
        }

        // Long-range pull toward fountains nobody visible is closer to.
        for (Hot const& h : hot_) {
            int dd = dist[h.cell];
            if (dd == INF) {
                // beyond the BFS horizon: no pull (keeps CPU bounded)
                continue;
            }
            int m = dd + 1 + k;
            // A fountain cluster feeds several dragons; yield only to a teammate already on it.
            if (friendDist_[h.cell] < m && friendDist_[h.cell] <= p_.hotYield) continue;
            value += p_.wHot * h.rate * fp(m);
        }

        std::string why;
        for (Hunt const& h : hunts_) {
            int dd = distToHead(dist, h.enemy->head);
            if (dd == INF) continue;
            if (h.job == Job::Attack) {
                // Aim at the head and at the tile it is facing into.
                int ahead = b.nb[h.enemy->head * 4 + h.enemy->headDir];
                if (ahead >= 0 && dist[ahead] != INF) dd = std::min(dd, dist[ahead]);
                value += p_.wHunt * (1.0 + h.gain / 4.0) * gp(dd + k);
                why = h.threat ? "intercept" : "hunt";
            } else {
                value += p_.wSupport * gp(std::abs(dd + k - p_.supportRing));
                if (why.empty()) why = "support";
            }
        }
        if (feedHead_ >= 0) {
            int dd = distToHead(dist, feedHead_);
            if (!p_.feedFar) {
                if (dd != INF) value += p_.wFeed * gp(dd + k);
            } else if (dd != INF) {
                value += p_.wFeed * fp(dd + k);
            } else {
                // Past the BFS horizon: walls are unknown, so pull by torus distance (x1.3 for detours).
                value += p_.wFeed * fp(static_cast<int>(1.3 * b.manh(dest, feedHead_)) + k);
            }
            why = "to-feed";
        }
        if (escortOf_ >= 0) {
            int dd = distToHead(dist, escortOf_);
            if (dd != INF) value += p_.wEscort * gp(std::abs(dd + k - p_.escortRing));
            if (why.empty()) why = "escort";
        }
        if (hiding_) {
            // Small and hidden: stay inside the swarm's cover.
            int fd = friendDist_[dest];
            if (fd != INF) value += p_.wHideFriend * gp(fd + k);
            if (why.empty()) why = "hide";
        }
        if (assassin_ && assassinCell_ >= 0) {
            // Converge on the reported cell and its neighbours. No pull past the
            // BFS horizon: chasing ghosts through fog is how the squad bleeds.
            int dd = distToHead(dist, assassinCell_);
            if (dd != INF) {
                value += p_.wAssassin * gp(dd + k);
                why = "assassinate";
            }
        }

        // Relayed enemy sightings: the swarm drifts toward them when it has
        // nothing better; growers keep clear of their reach even out of sight.
        double heardDanger = 0;
        for (EnemyField const& e : heardEnemies_) {
            int dd = distToHead(dist, e.head);
            if (dd == INF) continue;
            if (grower_ || hiding_) {
                // The hiding queen relocates away from reported positions: a
                // report near her means the hunt is closing in.
                if (dd <= p_.heardEnemyReach)
                    heardDanger += p_.wHeardEnemy * (hiding_ && !lead_ ? p_.wQueenFlee : 1.0);
            } else if (hunts_.empty()) {
                // The swarm converges on their queen much harder than a random enemy.
                value += (e.id == -2 ? 3.0 * p_.wHuntHeard : p_.wHuntHeard) * gp(dd + k);
                if (why.empty()) why = e.id == -2 ? "slay-stalk" : "stalk";
            }
        }

        double danger = 0;
        int enemyLen = 0;
        bool huntNext = false;
        double mult = (grower_ || hiding_) ? p_.growerDanger : survival() ? p_.survivalDanger : 1.0;
        if (queen_) mult *= p_.queenDanger;
        if (lateGame()) mult *= 2.0;
        // Forage-first opening: the extra breed-phase fear tax is what starves the
        // pearl race; base danger terms still apply.
        if (bud_) {
            double dm = open_ ? (queen_ && p_.openQueenDanger >= 0 ? p_.openQueenDanger : p_.openDanger)
                              : p_.budMult;
            mult *= dm;
        }
        int enemyId = -1;
        if (nextToEnemyHead(dest, enemyLen, huntNext, enemyId)) {
            // Parking next to an enemy head hands it the choice (and the drops). Only a
            // trade we would take anyway, with the local numbers, makes that acceptable.
            bool wanted = !grower_ && !queen_ && (huntNext || tradeOk(newL, enemyLen) ||
                                     (enemyId == w_.enemyQueen() && (assassin_ || newL + p_.queenTradeSlack >= enemyLen)));
            double favour = 1.0;
            if (p_.exposureMode == 0) favour = wanted ? 0.0 : 1.0;
            else if (p_.exposureMode == 1) favour = wanted && localOk(dest, -1) ? p_.exposedFavour : 1.0;
            else favour = wanted && localOk(dest, -1) ? 0.0 : 1.0;
            danger = p_.wDanger * newL * mult * favour;
        }
        if (k == 0 && p_.exposureMode != 0) {
            // Sprint reach: an enemy of length Le can MOVE up to Le - 1 steps onto our head.
            for (EnemyField const& e : enemies_) {
                int dd = e.dist[dest];
                if (dd <= 1 || dd > reachOf(e.visible)) continue;
                bool local = localOk(dest, -1);
                if (p_.exposureMode == 2 && local) continue;
                bool wanted = !grower_ && (huntAt(e.head) || tradeOk(newL, e.visible));
                double favour = wanted && local ? p_.exposedFavour : 1.0;
                danger += p_.wExposed * newL * mult * favour;
            }
        }
        if (lead_ && queen_ && k == 0) {
            // Leading: every enemy but their dead queen moves after ours, so any head whose full
            // sprint reach (ceil(L/4)+L-2 over free tiles) covers this tile can kill her this round.
            for (EnemyField const& e : enemies_) {
                int dd = e.dist[dest];
                if (dd <= 1) continue;  // adjacent heads: counted above
                // Enemy kill-reach is +len-1: head-to-head kills both, so a rammer
                // arriving at len 1 still takes our queen. (Our own slay uses -2 —
                // we only commit when we land at len 2+.)
                if (dd <= std::max(freeSteps(e.visible) + e.visible - 1, 1)) danger += p_.wLeadReach * newL * mult;
            }
        }
        if (queen_ && p_.wTailStrike > 0 && k == 0) {
            // Tail-strike: a length-N enemy can U-turn split so its old tail becomes
            // a new head that acts the same turn. Head within `visible` of dest means
            // a tail adjacent to dest is possible. Queen-only fear.
            for (EnemyField const& e : enemies_) {
                int dd = e.dist[dest];
                if (dd >= 0 && dd <= e.visible) danger += p_.wTailStrike * newL * mult;
            }
        }
        if (grower_) {
            // Keep a buffer: enemy heads two steps away are a problem too.
            for (World::Seen const& s : w_.others)
                if (isEnemy(s) && distToHead(dist, s.head) <= 1) danger += p_.wDanger * p_.growerDanger;
            danger += heardDanger * mult;
            heardDanger = 0;
        }
        if (hiding_) {
            danger += heardDanger * mult;
            heardDanger = 0;
        }

        // Pockets: a tile whose only other way out is one more tile is where dragons get sealed in.
        int exits = 0;
        for (int q = 0; q < 4; q++) {
            int n = b.nb[dest * 4 + q];
            if (n >= 0 && n != head && blk[n] <= 1) exits++;
        }
        // forage lane: a short dragon skipped an adjacent pearl because the eating tile paid
        // wPocket/wFog (1.5-1.75) against eatBonus 1.0. Not the queen: a pocket is how she dies.
        bool eatShort = c.eat && L <= (open_ ? p_.openEatLen : p_.pocketEatLen) && !queen_;
        if (exits <= 1 && k == 0 && !eatShort) danger += p_.wPocket;  // corridors would pile this up along a plan
        // Through a portal the far side may be out of vision. Only the real first step
        // pays for that (lookahead leaves vision all the time), and only much when we
        // recently saw dragons around the exit.
        if (k == 0 && !w_.visible(dest) && dest != b.id(b.X(head) + DX[d], b.Y(head) + DY[d])) {
            bool busy = false;
            for (int q = -1; q < 4 && !busy; q++) {
                int n = q < 0 ? dest : b.nb[dest * 4 + q];
                busy = n >= 0 && w_.occSeen[n] >= 0 && w_.t.round - w_.occSeen[n] <= p_.blindMemory;
            }
            danger += busy ? p_.wBlind * (1.0 + 0.25 * newL) : p_.wBlindQuiet;
        }
        // Heads parked next to a portal are what dragons coming through it crash into
        // (they cannot see us). Pass through or move on; do not loiter there.
        // Only pacing counts: staying beside a portal without going through it. Walking up
        // to a portal and crossing it is free.
        bool crossing = dest != b.id(b.X(head) + DX[d], b.Y(head) + DY[d]);
        if (k == 0 && b.portalSide[dest] && b.portalSide[head] && !crossing) danger += p_.wPortalLoiter;
        // Fog of war: a never-seen edge might be kelp, and stepping into kelp
        // kills. Long dragons pay more — they have more to lose.
        if (k == 0 && !crossing && !b.side(head, d).seen && !eatShort) {
            // Forage-first opening: on open maps the swarm must cross unseen edges
            // to reach fresh beds; kelp-ful mazes keep the full price.
            double fogMult = (open_ && !queen_ && !grower_ && !maze_) ? p_.openFog : 1.0;
            danger += p_.wFog * (1.0 + 0.25 * newL) * (assassin_ ? p_.assassinFogMult : 1.0) * fogMult;
        }

        c.stepTerm = (c.eat ? p_.eatBonus : 0.0) - danger;
        if (viaReverse) c.stepTerm -= p_.wReverse;
        c.score = value + c.stepTerm + p_.wSpace * std::min(space, need) / need;
        if (space < need && !viaReverse) {
            c.score = -1000.0 + space;  // vetoed, kept only as a last resort
            c.terminal = true;
        }
        c.why = space < need ? "cramped" : !why.empty() ? why : (c.eat ? "eat" : "forage");
        return c;
    }

    // Best score reachable from this state within `depth` more moves; NaN-free,
    // returns -1e18 when no move is legal. Sets timedOut_ when the deadline passes.
    double searchFrom(std::vector<int> const& body, int L, int depth, int k, std::vector<int>& eaten) {
        double best = -1e18;
        std::vector<int> next;
        for (int d = 0; d < 4; d++) {
            if (timeUp()) return best;
            Choice c = scoreFrom(body, L, d, k, eaten, &next);
            if (c.dest < 0) continue;
            double v = c.score;
            if (depth > 1 && !c.terminal) {
                if (c.eat) eaten.push_back(c.dest);
                std::vector<int> child = next;
                double rest = searchFrom(child, c.newL, depth - 1, k + 1, eaten);
                if (c.eat) eaten.pop_back();
                // A dead end deeper down is as bad as it looks; otherwise add what this step earned.
                v = rest <= -1e17 ? -900.0 : c.stepTerm * gp(k) + rest;
            }
            best = std::max(best, v);
        }
        return best;
    }

    bool trySplit(Choice& out, Choice const& bestMove) {
        Board const& b = w_.board;
        if (w_.t.units >= w_.init.unitLimit || !w_.bodyKnown()) return false;
        if ((bestMove.eat && !bud_ && !hiding_) || bestMove.why == "trade" || bestMove.why == "defend" || bestMove.why == "slay") return false;
        for (Hunt const& h : hunts_)
            if (h.job == Job::Attack) return false;  // attackers stay whole and committed

        int n = 0;
        if (w_.t.round >= p_.feedRound) return false;  // feeding phase: consolidate, never split
        if (hiding_) {
            // Bud everything above queenHideLen into a worker, staying small.
            if (L_ < p_.queenHideLen + 2) return false;
            n = L_ - p_.queenHideLen;
        } else if (grower_) {
            if (lateGame()) return false;  // the longest dragon decides the tiebreak
            // The queen's own length decides the game: stop budding workers from
            // her body once the economy phase ends.
            if (w_.init.id == w_.champId() && w_.t.round >= p_.queenBudUntil) return false;
            // Forage-first opening: the queen buds down to openQueenKeep so the
            // brood multiplies sooner; afterwards the normal keep floor returns.
            int keepBase = (open_ && w_.init.id == w_.champId() && p_.openQueenKeep >= 0)
                               ? p_.openQueenKeep : p_.growerKeepBase;
            int keep = keepBase + w_.t.round / p_.growerKeepEvery;
            if (L_ < keep + p_.growerChild) return false;
            n = p_.growerChild;
        } else {
            if (L_ < p_.swarmSplitLen) return false;
            // Late game: the tiebreak is the longest dragon, so stop splitting and let
            // length pile up, unless the army needs rebuilding.
            if (w_.t.round >= p_.growRound && w_.t.units >= p_.lateSplitUnits) return false;
            n = L_ / 2;
        }
        int enemyBan = open_ ? p_.openEnemyDist : p_.splitEnemyDist;
        for (World::Seen const& s : w_.others)
            if (isEnemy(s) && b.cheb(s.head, w_.head) <= enemyBan) return false;

        int keep = L_ - n;
        std::vector<int> parent(w_.body.begin(), w_.body.begin() + keep);
        std::vector<int> child(w_.body.rbegin(), w_.body.rbegin() + n);

        // Parent must still have a roomy move with the child as a wall, and vice versa.
        std::vector<int> blk = base_;
        for (int c : child) blk[c] = INF;
        markBody(blk, parent, keep);
        if (!hasRoomyMove(parent.front(), blk, keep)) return false;

        blk = base_;
        for (int c : parent) blk[c] = INF;
        markBody(blk, child, n);
        if (!hasRoomyMove(child.front(), blk, n)) return false;

        out.split = true;
        out.n = n;
        out.why = grower_ ? "bud" : "split";
        return true;
    }

    // A sprint trade: MOVE 2..sprintMax steps (a length-L dragon has at most L - 1) through
    // free tiles onto an enemy head we are allowed to trade with, where we have the local
    // numbers to eat the drops. Picks the longest such enemy, then the shortest path.
    bool sprintTrade(std::string& path) {
        Board const& b = w_.board;
        if (grower_ || queen_ || L_ < 3) return false;
        int maxSteps = std::min(p_.sprintMax, freeSteps(L_) + L_ - 2);
        std::vector<int> blk = ownBlk();
        // BFS over tiles free right now (blk <= 1: no dragon, not our body).
        std::vector<int> dist(b.NC, INF), from(b.NC, -1), dirTo(b.NC, -1);
        std::vector<int> q{w_.head};
        dist[w_.head] = 0;
        for (size_t qi = 0; qi < q.size(); qi++) {
            int c = q[qi];
            if (dist[c] + 1 >= maxSteps) continue;  // the last step goes onto the head itself
            for (int d = 0; d < 4; d++) {
                int n = b.nb[c * 4 + d];
                if (n < 0 || dist[n] != INF || blk[n] > 1) continue;
                dist[n] = dist[c] + 1;
                from[n] = c;
                dirTo[n] = d;
                q.push_back(n);
            }
        }
        int bestLen = -1, bestSteps = INF, bestEnd = -1, bestDir = -1;
        for (EnemyField const& e : enemies_) {
            if (e.visible < 2) continue;
            bool allowed = huntAt(e.head) != nullptr || tradeOk(L_, e.visible) ||
                           (e.id == w_.enemyQueen() && (assassin_ || L_ + p_.queenTradeSlack >= e.visible));
            if (!allowed || !localOk(e.head, e.id)) continue;
            for (int d = 0; d < 4; d++) {
                // stand on `pre`, step d onto the head
                int pre = -1;
                for (int k = 0; k < 4; k++) {
                    int n = b.nb[e.head * 4 + k];
                    if (n >= 0 && b.nb[n * 4 + d] == e.head) pre = n;
                }
                if (pre < 0 || dist[pre] == INF) continue;
                int steps = dist[pre] + 1;
                if (steps < 2 || steps > maxSteps) continue;
                if (e.visible > bestLen || (e.visible == bestLen && steps < bestSteps)) {
                    bestLen = e.visible;
                    bestSteps = steps;
                    bestEnd = pre;
                    bestDir = d;
                }
            }
        }
        if (bestEnd < 0) return false;
        std::string rev(1, DCH[bestDir]);
        for (int c = bestEnd; c != w_.head; c = from[c]) rev += DCH[dirTo[c]];
        path.assign(rev.rbegin(), rev.rend());
        return true;
    }

    bool hasRoomyMove(int head, std::vector<int> const& blk, int len) {
        Board const& b = w_.board;
        int need = std::min(std::max(static_cast<int>(p_.spaceFactor * len) + p_.spaceMargin, p_.splitRoom), b.NC / 2);
        for (int d = 0; d < 4; d++) {
            int n = b.nb[head * 4 + d];
            if (n < 0 || blk[n] > 1) continue;
            if (nav_.flood(b, n, blk, need + 1) >= need) return true;
        }
        return false;
    }
};

}  // namespace bc
