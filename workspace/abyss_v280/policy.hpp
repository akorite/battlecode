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
            // Champion plant: once the feed window nears, the elected champion
            // locks onto its current cell instead of roaming — feeders die at a
            // stationary head, not at where she was 15 rounds ago (WaterCandle
            // locks ~r330 for an r380 feed). Needs room to pace a long body.
            // Anchor lives in World: Policy is rebuilt every turn — a per-turn
            // member just chases the head (found in review: v149a's "plant" was
            // really only a deceleration pull, the board win came from r330).
            if (selfChamp_ && w_.t.round >= p_.feedRound - p_.champPlantLead && w_.t.round < p_.feedStop) {
                if (w_.champAnchor < 0 && regionReach(w_.head) >= 12) w_.champAnchor = w_.head;
            } else w_.champAnchor = -1;
        }
        if (p_.sonarOn) emitSonar();
        buildBase();
        if (p_.slayAlways && !queen_) {
            Choice sl;
            if (slayQueen(sl)) return sl;
        }
        // s0 identity must exist before buildTargets (Policy rebuilt per turn).
        s0scout_ = !queen_ && !grower_ && !lead_ && w_.init.id == w_.champId() + 2
                   && w_.t.round < p_.s0Until && w_.board.portalOpen_;
        buildTargets();
        if (!lean_) buildFriendFields();
        else noFriendFields();
        // Pocket-geometry gate: every mechanism below exists for bait-pocket
        // maps (deg<=1 bed appendages). On maps with none the worker deltas
        // are pure perturbation — dilemma's queen lane is knife-edge enough
        // that any early worker reroute flips her into the kill column.
        if (!anyBait_) {
            for (Target const& t : targets_)
                if (bait(t.cell)) { anyBait_ = true; break; }
        }
        // v135b: pocket mechanisms fire only where calibrated — small bait
        // maps (weakhold 600). On maze (1152, has deg-1 beds) the starving
        // pulls + skipped worker scans cost ~7pts — size-gate them out.
        pocketMap_ = anyBait_ && w_.board.NC <= 700;
        if (pocketMap_) noteFoodReach();
        buildSquadTargets();
        worker_ = !queen_ && !grower_ && !lead_ && !assassin_;
        // Starving on safe food: nothing edible in reach that isn't a bait bed.
        // Then a suicide-eat (enter the appendage, take its pearls, wedge-die)
        // out-values orbiting a food desert — v119's swarm economy tolerates
        // those deaths because each baby banks pearls first. Not starving:
        // bait cells stay excluded and the deadEnd veto keeps us out.
        starving_ = worker_ && pocketMap_ && foodReach_ < p_.starveLocal;

        // End-game feeding (see Params::feedRound). Under the hide doctrine
        // feeders wake earlier (queenFeedRound) and walk to the queen at the
        // closer queenFeedMargin; before feedRound the queen is the only target.
        int feedAt = p_.queenHide ? std::min(p_.feedRound, p_.queenFeedRound) : p_.feedRound;
        feedAge_ = 0;
        feedBurst_ = false;
        // Mid-window die-in-place (pocket): our r120+ dead-pool already
        // dies ~45/game at open cells for nothing; winners churn their
        // len<=3s ON the swarm so the drops get re-collected. An idle
        // short worker (no local food, no hunt, no escort) recycles on the
        // swarm centroid — every position comes from live role-0 beacons.
        if (feedHead_ < 0 && worker_ && !grower_ && p_.midFeedRound > 0
            && b.NC >= p_.midFeedMinTiles
            && w_.t.round >= p_.midFeedRound && w_.t.round < p_.feedStop
            && L_ <= p_.midFeedMaxLen && hunts_.empty() && escortOf_ < 0) {
            bool foodNear = false;
            for (Target const& t : targets_)
                if ((t.belief > 0.02 || t.countdown >= 0)
                    && distToHead(myDist_, t.cell) <= p_.midFeedFoodDist) { foodNear = true; break; }
            if (!foodNear) {
                int beacon[64]; int n = 0;
                for (World::Seen const& o : w_.others)
                    if (!isEnemy(o) && o.head >= 0 && n < 64) beacon[n++] = o.head;
                for (World::Heard const& h : w_.heard)
                    if (h.cell >= 0 && h.role == 0 && w_.t.round - h.round <= p_.heardMemory
                        && n < 64) beacon[n++] = h.cell;
                if (n >= 3) {
                    // Densest beacon is the true swarm centre; an arithmetic
                    // mean lands mid-map when the cluster straddles a torus seam.
                    int best = -1, bestCnt = -1;
                    for (int i = 0; i < n; i++) {
                        int cnt = 0;
                        for (int j = 0; j < n; j++)
                            if (b.cheb(beacon[i], beacon[j]) <= 6) cnt++;
                        if (cnt > bestCnt) { bestCnt = cnt; best = beacon[i]; }
                    }
                    feedHead_ = best;
                    feedAge_ = 1;
                }
            }
        }
        if (!lead_ && !queen_ && !assassin_ && w_.t.round >= feedAt && w_.t.round < p_.feedStop && L_ <= p_.feedMaxLen) {
            int bestLen = L_ + p_.feedMargin - 1;
            int qMargin = p_.queenHide ? p_.queenFeedMargin : p_.feedMargin;
            if (p_.champOne) {
                // One champion: our queen while she lives, else the longest dragon the team knows of.
                if (champHead_ >= 0 && !selfChamp_) {
                    feedHead_ = champHead_;
                    feedAge_ = champAge_;
                    // Stamp the anchor with the EVIDENCE round, not now —
                    // the estimate itself may already be stale (age laundering).
                    champAnchor_ = champHead_;
                    champAnchorRound_ = w_.t.round - champAge_;
                    champAnchorId_ = champId_;
                } else if (!selfChamp_ && champAnchor_ >= 0
                           && (champAnchorId_ == w_.chId || (champAnchorId_ == w_.ourQueen && w_.ourQueen >= 0 && !w_.queenDead(w_.ourQueen)))
                           && w_.t.round - champAnchorRound_ <= std::min(p_.champAnchorAge, p_.feedHeardDie)) {
                    // The champion is off-vision: converge on its last known position and
                    // die there — the conveyor must not stall waiting for a fresh report.
                    // Skipped when: we ARE the champ (selfChamp_), a new champ took over
                    // (id mismatch, covers observed death + re-election), the window
                    // clamped to feedHeardDie closed (zombie feeder window), or the team
                    // can see the anchor cell is empty (known-empty die-in-place).
                    if (w_.visible(champAnchor_)) champAnchor_ = -1;
                    else {
                        feedHead_ = champAnchor_;
                        feedAge_ = w_.t.round - champAnchorRound_;
                    }
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
                // handled below, outside the feed-window gate
            }
        }
        if (feedHead_ >= 0) {
            int d = distToHead(myDist_, feedHead_);
            // Conveyor radius: only feeders already within feedRadius of the
            // target recycle; farther dragons keep foraging rather than walk a
            // gauntlet they die in (feed-window h2h > nva gains at distance).
            if (p_.feedRadius > 0 && d > p_.feedRadius) { feedHead_ = -1; feedAge_ = 0; }
            else {
            grower_ = false;
            hunts_.clear();
            escortOf_ = -1;
            feedBurst_ = w_.t.round - feedAt <= p_.feedBurstRounds
                         && feedAge_ <= p_.feedHeardDie && d <= p_.feedBurstDist;
            bool live = feedAge_ == 0;
            // A champion we only heard (off vision) still takes the drop if the report is fresh.
            bool heardNear = !live && p_.champOne && feedAge_ <= p_.feedHeardDie;
            int fd = p_.champOne ? p_.champFeedDist : p_.feedDist;
            if (d <= fd && L_ >= 2 && w_.t.units >= p_.feedMinUnits && (live || heardNear || !p_.champOne)) {
                // Die in place: an illegal SPLIT is a noValidAction death that
                // works even when the neck cell is blocked; the body drops
                // beside the champion's head.
                Choice c;
                c.split = true;
                c.n = 0;
                c.why = "chfeed";
                c.score = 1e9;
                return c;
            }
            }
        } else if (!assassin_ && w_.t.round >= p_.feedRound && L_ >= p_.feedMargin && !p_.champOne) {
            grower_ = true;  // nobody visible is longer: we are the one being fed
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
        // Queen self-kill fix (1c follow-on): a vetoed dead-end step may only win
        // when EVERY move is vetoed — a scared queen who still has an open move
        // must never be routed into a pocket she cannot leave (weakhold seat-A
        // fog-nook hitWall at r37). Workers keep F2's least-bad ordering.
        if (queen_) {
            bool anyOpen = false;
            for (int d = 0; d < 4; d++)
                if (first[d].dest >= 0 && first[d].why != "deadend") anyOpen = true;
            for (Cand const& cd : cands)
                if (cd.c.dest >= 0 && cd.c.why != "deadend") anyOpen = true;
            if (anyOpen) {
                for (int d = 0; d < 4; d++)
                    if (first[d].why == "deadend") first[d].score = -1e18;
                for (Cand& cd : cands)
                    if (cd.c.why == "deadend") cd.c.score = -1e18;
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
                if (c.dest < 0) {
                    // Blind portal crossings keep their scout score at every
                    // depth — there is nothing to search past a teleport.
                    if (c.why == "scout") t[d] = c.score;
                    continue;
                }
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
            if (first[d].dest < 0 && first[d].why != "scout") continue;
            Choice c = first[d];
            c.score = total[d];
            if (c.score > best.score) best = c;
        }
        for (size_t i = 0; i < cands.size(); i++) {
            Choice c = cands[i].c;
            c.score = ctot[i];
            if (c.score > best.score) best = c;
        }
        if (best.dest < 0 && best.why != "scout") {
            // Nothing legal: first try a tile we only gave up as a teammate's last exit,
            // otherwise any well-formed move beats the default suicide.
            best.dir = w_.t.dir;
            best.dest = b.nb[w_.head * 4 + best.dir];
            best.why = "trapped";
            // Doomed: die alone. Prefer an enemy head (trade); a physically free
            // move still beats certain suicide (exit-reserved free cells next —
            // the reservation may be stale); then bodies; a teammate's head last.
            int bestRank = 99;
            for (int d = 0; d < 4; d++) {
                int n = b.nb[w_.head * 4 + d];
                int hid = n >= 0 ? w_.occHeadId[n] : -1;
                bool enemyHead = false, friendHead = false;
                for (World::Seen const& s2 : w_.others)
                    if (s2.id == hid) (isEnemy(s2) ? enemyHead : friendHead) = true;
                bool own = n >= 0 && (ownCell(n) || std::find(w_.ownExtra.begin(), w_.ownExtra.end(), n) != w_.ownExtra.end());
                bool physFree = n >= 0 && w_.occ[n] < 0 && !own;
                bool qRes = std::find(queenExits_.begin(), queenExits_.end(), n) != queenExits_.end();
                int rank = enemyHead ? 0 : friendHead ? 9 : qRes ? 10 : physFree ? (base_[n] >= INF ? 6 : 4) : (n < 0 ? 8 : 7);
                if (rank < bestRank || (rank == bestRank && rank >= 4 && champAnchor_ >= 0
                        && n >= 0 && (best.dest < 0 || b.cheb(n, champAnchor_) < b.cheb(best.dest, champAnchor_)))) {
                    bestRank = rank;
                    best.dir = d;
                    best.dest = n;
                    best.why = rank <= 4 ? "trapped-free" : "trapped";
                }
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
        // Queen pinned: every one-step landing is inside a rammer's reach.
        // Reverse-split cannot save her (she stays put); a paid multi-step run can.
        if (queen_ && p_.queenEscape) {
            std::vector<int> blk = ownBlk();
            bool anyLegal = false, anySafe = false;
            for (int d = 0; d < 4; d++) {
                int t = b.nb[w_.head * 4 + d];
                if (t < 0 || blk[t] > 1) continue;
                anyLegal = true;
                if (!rammed(t)) anySafe = true;
            }
            if (anyLegal && !anySafe) {
                std::string pth;
                if (queenEscape(pth, blk)) {
                    Choice e;
                    e.dir = dirFromChar(pth[0]);
                    e.dest = -1;
                    e.path = pth;
                    e.pathCost = std::max(0, static_cast<int>(pth.size()) - freeSteps(L_));
                    e.why = "escape";
                    e.score = 1e9;
                    return e;
                }
            }
        }
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
    bool corrSet_ = false;
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

    // Starving signal: belief that can actually be collected (in reach and,
    // below baitLen, not behind a single exit). Drives the persist bonus.
    void noteFoodReach() {
        foodReach_ = 0;
        bool short_ = pocketMap_ && L_ < p_.baitLen;
        for (Target const& t : targets_) {
            if (t.belief <= 0.02 || myDist_[t.cell] == INF) continue;
            if (short_ && bait(t.cell)) continue;
            foodReach_ += t.belief;
        }
    }

    bool timeUp() {
        if (!timedOut_ && clockNow() >= deadline_) timedOut_ = true;
        return timedOut_;
    }
    Nav nav_;
    double foodReach_ = 0;          // reachable, collectible belief (starving signal)
    bool worker_ = true;            // no doctrine role: not queen/grower/lead/assassin
    bool anyBait_ = false;          // a bait cell (deg<=1 provable) seen this game — raw detector
    bool pocketMap_ = false;        // anyBait_ && small map — gates pocket mechanisms
    bool starving_ = false;         // worker with little reachable non-bait food — suicide-eats allowed
    double bedBelief(int c) const {
        for (Target const& t : targets_)
            if (t.cell == c) return t.belief;
        return 0;
    }
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
    struct EnemyField { int id; int head; int visible; int reachBoost; std::vector<int> dist; };
    std::vector<EnemyField> enemies_;  // the nearest visible enemy heads, with their BFS fields
    std::vector<EnemyField> heardEnemies_;  // relayed enemy sightings, with their BFS fields
    std::vector<int> myDist_;     // from our head as it is now
    std::vector<Hunt> hunts_;
    int escortOf_ = -1;           // head tile of the grower we escort, -1 none
    int feedHead_ = -1;           // head of the longer teammate we are walking to, -1 none
    int champAnchor_ = -1;        // last-known champion position: feeders converge there while the champ is off-vision
    int champAnchorRound_ = -999; // round the anchor was last refreshed
    int champAnchorId_ = -1;      // champ id the anchor belongs to (cleared on re-election/death)
    int feedAge_ = 0;             // rounds since feedHead_ was seen (0 = in vision now)
    std::vector<int> regionSize_; // wall-connected component size per cell (static walls, computed once)
    bool feedBurst_ = false;      // this worker is inside the champ front-load window
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
    // Geometric size of the region containing `cell` (walls bound it — a
    // Schooltime queen is sealed in a 2x2 at 4 of 2400 tiles). Static map
    // property; result capped at 40. Unknown/out-of-range cell -> not sealed.
    int regionReach(int cell) {
        Board const& b = w_.board;
        if (cell < 0 || cell >= b.NC) return 40;
        std::vector<int> seen(b.NC, 0), q(1, cell);
        seen[cell] = 1;
        for (size_t i = 0; i < q.size() && q.size() < 40; i++)
            for (int d = 0; d < 4; d++) {
                int n2 = b.nb[q[i] * 4 + d];
                if (n2 >= 0 && !seen[n2]) { seen[n2] = 1; q.push_back(n2); }
            }
        return (int)q.size();
    }
    int queenReach_ = -1;
    std::vector<int> queenExits_;   // queen's free exits we reserved (workers keep off)
    int queenReach() {
        if (queenReach_ < 0) queenReach_ = regionReach(w_.queenCell);
        return queenReach_;
    }
    void locateChamp() {
        champHead_ = -1;
        champAge_ = 0;
        champLen_ = 0;
        champId_ = -1;
        champIsQueen_ = false;
        selfChamp_ = false;
        queenReach_ = -1;
        queenExits_.clear();
        if (w_.t.round < std::min(p_.queenFeedRound, p_.feedRound) - 40) return;
        bool queenReady = !p_.queenHide || w_.t.round >= p_.queenHideUntil;
        if (queenReady && w_.ourQueen >= 0 && !w_.queenDead(w_.ourQueen) && queenReach() < 20)
            queenReady = false;  // sealed queen is no champion — feed the longest dragon
        if (queenReady && w_.ourQueen >= 0 && !w_.queenDead(w_.ourQueen) && w_.queenRound >= 0 && w_.t.round - w_.queenRound <= p_.champMemory) {
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
    bool s0scout_ = false;          // first worker on a portal mission (early transits)
    int assassinCell_ = -1;       // where the enemy queen was last reported (or seen)

    // Our sonar traffic for the turn: a beacon in every direction, plus one
    // enemy report aimed where a teammate is likeliest to pick it up.
    void adjustByMap() {
        // Maze maps (Portals: walls on ~28% of edges) paralyse the swarm if every
        // corridor mouth counts as a pocket — drop pocket fear there.
        maze_ = w_.kelpFraction() > p_.mazeKelpFrac;
        if (maze_) eff_.wPocket = 0.0;
        // Corridor-class maps (<=2000 tiles: maze/trauma/weakhold/portals/slithery)
        // resolve by mid-game attrition — the late feed window (360) forfeits the
        // fight; keep the proven 320-era consolidation timing there.
        if (!corrSet_ && w_.init.w * w_.init.h <= 2000) {
            corrSet_ = true;
            eff_.feedRound = 320;
            eff_.queenFeedRound = 330;
            eff_.champFallbackRound = 320;
            eff_.queenRelayFrom = 300;
            eff_.champRelayFrom = 370;
            eff_.queenHideUntil = 320;
            eff_.midEnd = 400;
        }
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
        // On small elim boards the melee is decided by net length: trading
        // down by even 1 bleeds the swarm (autarky: 55-60% of our h2h dead
        // are -1 trades we chose). Big open boards keep the +1 slack for tempo.
        int slack = w_.board.NC <= p_.tradeSlackMaxTiles ? p_.tradeSlackSmall : p_.tradeSlack;
        return w_.t.units >= (lead_ ? p_.leadTradeMinUnits : p_.tradeMinUnits) && myLen <= enemyLen + slack;
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
    // Enemy kill-reach: freeSteps + len-1 (arriving at len 1 still kills on h2h,
    // per the lead_ branch's own rule). -2 under-screens len2-3 rams by a tile.
    int reachOf(int visible) const { return std::min(std::max(freeSteps(visible) + visible - 1, 1), p_.reachCap); }
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
            int exits = 0, exit = -1, exn = 0;
            int exCells[4];
            for (int d = 0; d < 4; d++) {
                int n = b.nb[s.head * 4 + d];
                if (n >= 0 && blk[n] <= 1) { exits++; exit = n; exCells[exn++] = n; }
            }
            if (exits == 1) base_[exit] = INF;
            // Queen self-kill fix (1b): queens move first, so a teammate standing on
            // one of her last two exits is a wall she cannot clear. Workers never
            // end a turn on them.
            if (s.id == w_.ourQueen && exits == 1)
                for (int i = 0; i < exn; i++) {
                    base_[exCells[i]] = INF;
                    queenExits_.push_back(exCells[i]);
                }
        }
    }

    void buildTargets() {
        Board const& b = w_.board;
        if ((int)regionSize_.size() != b.NC) {
            // Static wall-connected components: workers get lured into pockets by
            // forage targets inside them (the one-sided hitWall bleed on corridor
            // maps). A region label makes pocket topology known from r1.
            regionSize_.assign(b.NC, 0);
            std::vector<int> seen(b.NC, 0), q;
            for (int c = 0; c < b.NC; c++) {
                if (seen[c]) continue;
                q.clear(); q.push_back(c); seen[c] = 1;
                for (size_t i = 0; i < q.size(); i++)
                    for (int d = 0; d < 4; d++) {
                        int n = b.nb[q[i] * 4 + d];
                        if (n >= 0 && !seen[n]) { seen[n] = 1; q.push_back(n); }
                    }
                for (int x : q) regionSize_[x] = (int)q.size();
            }
        }
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
        // The planted champion hovers its anchor: a moderate fixed pull keeps it
        // findable (~3-5 cells) while local respawns still outbid the drift —
        // full freeze starved it between drops on stronghold (44 vs 61 bell loss).
        if (w_.champAnchor >= 0) targets_.push_back({w_.champAnchor, 1.2, -1, 0.0});
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
        // The designated scout routes straight to the nearest unpaired lip;
        // belief-0 targets bypass friend-claim so the pull always reaches it.
        if (s0scout_) {
            bool anyPaired = false;
            int best = -1, bd = INF;
            for (auto const& pe : w_.portalEnds) {
                if (pe.second.size() == 2) { anyPaired = true; continue; }
                World::PortalEnd const& e = pe.second.front();
                int lips[2] = {e.orient == 0 ? b.id(e.x, e.y - 1) : b.id(e.x - 1, e.y),
                               b.id(e.x, e.y)};
                for (int c2 : lips)
                    if (b.bed[c2] != 1 && b.cheb(c2, w_.head) < bd) { bd = b.cheb(c2, w_.head); best = c2; }
            }
            if (!anyPaired) {
                if (best >= 0) {
                    int rot = b.id(b.W - 1 - b.X(best), b.H - 1 - b.Y(best));
                    if (b.bed[rot] != 1) targets_.push_back({rot, 0.0, -2, p_.s0Portal});
                }
                else if (w_.spawnCell >= 0) {
                    int wp = b.id(b.W - 1 - b.X(w_.spawnCell), b.H - 1 - b.Y(w_.spawnCell));
                    if (b.cheb(wp, w_.head) > 4 && b.bed[wp] != 1)
                        targets_.push_back({wp, 0.0, -1, p_.s0Far});
                }
            }
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
                int boost = 0, rr = reachOf(s.visible);
                for (int c = 0; c < b.NC; c++) {
                    if (w_.seenPearl[c] && nav_.dist[c] <= rr && boost < 4) boost++;
                }
                enemies_.push_back({s.id, s.head, s.visible, boost, nav_.dist});
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
            int boost = 0, rr = reachOf(hp->len);
            for (int c = 0; c < b.NC; c++) {
                if (w_.seenPearl[c] && nav_.dist[c] <= rr && boost < 4) boost++;
            }
            heardEnemies_.push_back({hp->role == 1 ? -2 : -1, hp->cell, hp->len, boost, nav_.dist});
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

    // True when c provably has a single usable exit: three of its edges are
    // seen-blocked. Entering head-first is a wedge for anyone too short to
    // reverse out — weakhold's row-0/row-14 beds are exactly this bait.
    bool bait(int c) const {
        int walls = 0;
        for (int d = 0; d < 4; d++) walls += w_.board.nb[c * 4 + d] < 0;
        return walls == 3;
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
            if (k == 0 && !queen_ && e.kind == 2 && e.partnerOrient < 0) {
                c.dest = -1;
                c.score = p_.wScout - (p_.wBlindQuiet * (1.0 + 0.25 * L));
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
            int cover = 0;
            for (World::Seen const& s2 : w_.others)
                if (isEnemy(s2) && s2.id != hid && s2.head >= 0 && b.cheb(s2.head, dest) <= 2) cover++;
            for (World::Seen const& s : w_.others) {
                if (s.id != hid || !isEnemy(s)) continue;
                if (cover > 0 && !queen_) return c;  // covered victim: ram = our head alone
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
        if (space < need && newL >= 4 && !queen_ && static_cast<int>(body.size()) == newL) {
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
        bool baitEat = starving_ && bedBelief(dest) > 0;
        if (p_.trapOn && !viaReverse && !baitEat && (queen_ || (p_.workerScan && pocketMap_ && k == 0))) {
            wallScratch_.assign(b.NC, 0);
            for (int oc : nb2) wallScratch_[oc] = INF;
            for (int oc : w_.ownExtra) wallScratch_[oc] = INF;
            // Queen self-kill fix (1a): teammate HEADS within 2 tiles of the queen
            // are walls in her dead-end scan — they move after her and stay
            // blocked for her whole turn, so they read as the nook plug she
            // cannot clear. Body middles are deliberately not walled: escorts
            // in open space must not shrink her reachable region (weakhold
            // seat-A route regression).
            if (queen_) {
                for (World::Seen const& s : w_.others)
                    if (!isEnemy(s) && b.cheb(s.head, w_.head) <= 2)
                        wallScratch_[s.head] = INF;
            }
            // wh4: the fog-walls scan only runs on small maps — on big maps a
            // small seen component + thin fog boundary describes corridors as
            // well as pockets, and the veto pinned the queen.
            bool so = p_.trapSeenOnly != 0 && (p_.trapMaxTiles == 0 || b.NC <= p_.trapMaxTiles);
            // earlyecon (ee_fix120): the wh4 fog scan is the weakhold pocket fix —
            // but on other small maps its shrunk tiny/tree vetoes pin the queen
            // (every seen blob looks tiny/closed under fog) and halved budding.
            // Keep the fog scan where it was calibrated (weakhold 40x15); elsewhere
            // read v104's optimistic scan for tiny/tree/loopRoom and keep only the
            // unproven mouth veto from a second seenOnly scan.
            bool wh_ = b.W == 40 && b.H == 15;
            Scan sc = nav_.deadEnd(b, dest, wallScratch_, p_.trapScanCells, so && wh_);
            bool loopRoom = sc.cycle && sc.cells > newL && sc.frontier == 0;
            bool tiny = sc.cells <= newL + p_.trapMargin && sc.frontier == 0;
            bool tree = sc.exhausted && !sc.cycle && sc.frontier == 0;
            // seenOnly: fog walls the scan, so a small region may just be unexplored.
            // That is still a trap risk for the queen — she needs proof of room, not
            // proof of a trap. Veto when the confirmed-open room is too small.
            bool unproven = false;
            if (so && wh_) {
                unproven = !sc.cycle && sc.cells <= p_.trapSafeCells && sc.frontier <= p_.trapFrontier;
            } else if (so) {
                Scan sc2 = nav_.deadEnd(b, dest, wallScratch_, p_.trapScanCells, true);
                unproven = !sc2.cycle && sc2.cells <= p_.trapSafeCells && sc2.frontier <= p_.trapFrontier;
            }
            // Queen self-kill fix (1a2): a tile with <2 free exits is a nook —
            // her own body frees next turn but an ally or enemy standing there
            // will not. Corridors (neck + ahead) still count 2.
            bool fewExits = false;
            if (queen_) {
                int ex = 0;
                for (int d = 0; d < 4; d++) {
                    int n = b.nb[dest * 4 + d];
                    if (n < 0) continue;
                    int o = w_.occ[n];
                    if (o >= 0 && o != w_.init.id) continue;
                    ex++;
                }
                fewExits = ex < 2;
            }
            // C4 corridor rule (queen): a deg-2 run contested by another dragon is
            // a head-on wedge — the blocker isn't a wall in the dead-end scan.
            // Walk the run from the deeper open neighbour; veto on a non-self
            // segment inside it or sitting on its far-end cell.
            bool corridorWedge = false;
            if (queen_ && !fewExits) {
                int open = 0, deeper = -1;
                for (int d2 = 0; d2 < 4; d2++) {
                    int n = b.nb[dest * 4 + d2];
                    if (n < 0) continue;
                    int o = w_.occ[n];
                    if (o >= 0 && o != w_.init.id) continue;
                    open++;
                    if (n != head) deeper = n;
                }
                if (open == 2 && deeper >= 0) {
                    int cur = deeper, prev = dest;
                    for (int step = 0; step < 8; step++) {
                        int o = w_.occ[cur];
                        if (o >= 0 && o != w_.init.id) { corridorWedge = true; break; }
                        int deg = 0, nxt = -1;
                        for (int d2 = 0; d2 < 4; d2++) {
                            int n = b.nb[cur * 4 + d2];
                            if (n < 0) continue;
                            int oo = w_.occ[n];
                            if (oo >= 0 && oo != w_.init.id) continue;
                            deg++;
                            if (n != prev) nxt = n;
                        }
                        if (deg > 2 || nxt < 0) break;
                        prev = cur; cur = nxt;
                    }
                }
            }
            if (!loopRoom && (tiny || tree || unproven || fewExits || corridorWedge)) {
                c.stepTerm = -2000 + sc.cells;  // least-bad largest region wins if all vetoed
                // F2: a vetoed step must still be pickable — except for a sealed
                // queen, whose 'trapped-free' keeps her in her safe room (walking
                // out of it gets her killed; schooltime 18.8% regression gate).
                if (!queen_ || regionReach(body.front()) >= 20) c.score = c.stepTerm;
                c.terminal = true;
                c.why = "deadend";
                return c;
            }
        }

        nav_.bfs(b, dest, blk, p_.horizon);
        std::vector<int> const& dist = nav_.dist;

        double value = 0;
        bool short_ = worker_ && pocketMap_ && newL < p_.baitLen && !starving_;
        // Bed camping: a worker next to a live site hovers for the respawn
        // instead of ranging to the next bed — winners farm beds this way and
        // that is where the 4-17x split gap comes from.
        bool camp_ = worker_ && !queen_;
        if (camp_) {
            camp_ = false;
            for (Target const& t : targets_) {
                int dd = dist[t.cell];
                if (dd != INF && dd <= p_.campNear && t.countdown >= 0) { camp_ = true; break; }
            }
        }
        // v135b: on non-pocket maps the bait check inside the hot loop is pure
        // instruction cost — the depth-clip tax flips long saturated games
        // (maze). Two loop bodies keep the off path instruction-identical.
        if (!short_)
        for (Target const& t : targets_) {
            if (t.cell == dest && t.countdown != -2) continue;
            int dd = dist[t.cell];
            if (dd == INF) continue;
            if (!eaten.empty() && std::find(eaten.begin(), eaten.end(), t.cell) != eaten.end()) continue;
            int m = dd + 1 + k;  // moves from now, counting the ones already planned
            double v = t.belief * gp(m);
            if (t.countdown >= 0 && t.belief < 0.5)
                v = std::max(v, 0.9 * gp(std::max(m, t.countdown + 1)));
            if (camp_ && dd > p_.campNear) v *= p_.campFar;
            if (v > 0) {
                int fd = friendDist_[t.cell];
                if (fd < m || (fd == m && friendId_[t.cell] < w_.init.id)) v = 0;
                else if (enemyDist_[t.cell] < m) v *= p_.enemyCloserFactor;
            }
            v += t.explore * gp(m);
            if (worker_ && !starving_ && p_.workerRegionNorm > 0) {
                int rs = regionSize_[t.cell];
                if (rs < p_.workerRegionNorm) v *= (double)rs / p_.workerRegionNorm;
            }
            if (assassin_) v *= p_.assassinForage;  // on mission: pearls are a detour
            value += v;
        }
        else
        for (Target const& t : targets_) {
            if (t.cell == dest && t.countdown != -2) continue;
            int dd = dist[t.cell];
            if (dd == INF) continue;
            // Bait cells: a bed behind a single exit is lethal below baitLen
            // (the only way out runs through our own body, and reverse needs 4).
            // It is not food for us — count it out of the pull entirely.
            if (bait(t.cell)) continue;
            if (!eaten.empty() && std::find(eaten.begin(), eaten.end(), t.cell) != eaten.end()) continue;
            int m = dd + 1 + k;  // moves from now, counting the ones already planned
            double v = t.belief * gp(m);
            if (t.countdown >= 0 && t.belief < 0.5)
                v = std::max(v, 0.9 * gp(std::max(m, t.countdown + 1)));
            if (camp_ && dd > p_.campNear) v *= p_.campFar;
            if (v > 0) {
                int fd = friendDist_[t.cell];
                if (fd < m || (fd == m && friendId_[t.cell] < w_.init.id)) v = 0;
                else if (enemyDist_[t.cell] < m) v *= p_.enemyCloserFactor;
            }
            v += t.explore * gp(m);
            if (worker_ && !starving_ && p_.workerRegionNorm > 0) {
                int rs = regionSize_[t.cell];
                if (rs < p_.workerRegionNorm) v *= (double)rs / p_.workerRegionNorm;
            }
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
            if (!short_ || !bait(h.cell)) value += p_.wHot * h.rate * fp(m);
        }

        // Frontier reach: prefer regions that keep unseen tiles BFS-reachable.
        // A starving worker in a seen pocket gets a corridor-routed pull toward
        // the exits; the deadEnd veto above keeps unseen appendages off-limits,
        // so the pull cannot reward walking into the pockets it reveals.
        // Inert for roles with their own doctrine and once the map is seen.
        if (worker_ && starving_) {
            int nu = 0, ndu = INF;
            for (int c2 = 0; c2 < b.NC; c2++) {
                if (w_.seenRound[c2] < 0 && dist[c2] != INF) {
                    nu++;
                    ndu = std::min(ndu, dist[c2]);
                }
            }
            value += p_.wFrontier * nu;
            // Fog approach: the per-tile explore pull is ~0.001 at corridor
            // distances, so workers orbit in a value desert around pocket
            // mouths. Pay real weight (long-range discount) for getting the
            // nearest unseen tile closer — BFS-routed, inert once map is seen.
            if (ndu != INF) value += p_.wFogPull * fp(ndu);
            // Starving hysteresis: keep walking the current heading rather than
            // orbiting a corridor mouth while nothing edible is in reach.
            if (k == 0 && foodReach_ < p_.starveLocal && body.size() >= 2 &&
                d < 4 && b.nb[body[1] * 4 + d] == body[0])
                value += p_.wPersist;
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
            double wf = p_.wFeed * (feedBurst_ ? p_.feedBurstMult : 1.0);
            if (!p_.feedFar) {
                if (dd != INF) value += wf * gp(dd + k);
            } else if (dd != INF) {
                value += wf * fp(dd + k);
            } else {
                // Past the BFS horizon: walls are unknown, so pull by torus distance (x1.3 for detours).
                value += wf * fp(static_cast<int>(1.3 * b.manh(dest, feedHead_)) + k);
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
        if (queen_ && !hiding_ && !lead_ && p_.wQueenLeash > 0
            && b.NC >= p_.queenLeashMinTiles) {
            // Top-team queens orbit ~5.6 inside their own swarm and never
            // isolate; ours drifts to ~13.7 exposed (autarky study). The ram
            // kill needs no ally within 2 tiles — keep her inside cover.
            int fd = friendDist_[dest];
            if (fd == INF) fd = 64;  // unreachable pocket = isolation, not free
            if (fd > p_.queenLeashDist) {
                value -= p_.wQueenLeash * (fd - p_.queenLeashDist);
                if (why.empty()) why = "leash";
            }
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
            if (friendDist_[dest] <= 2) favour *= p_.coveredFavour;
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
                if (friendDist_[dest] <= 2) favour *= p_.coveredFavour;
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
                if (dd <= std::max(freeSteps(e.visible) + e.visible - 1, 1) + e.reachBoost) danger += p_.wLeadReach * newL * mult;
            }
        }
        if (queen_ && !lead_ && k == 0 && p_.wQueenRam > 0) {
            // Queen ram screen: 94% of queen deaths are len2-3 rams stepping onto her.
            // A tile inside a seen OR fresh heard enemy's sprint reach is priced fatal —
            // not soft — so she never ends a turn where a rammer can arrive this round.
            bool adj = p_.qRamAdj > 0 && b.NC >= p_.qRamAdjMinTiles;
            int floor_ = adj ? 0 : 1, bonus = adj ? p_.qRamAdj : 0;
            for (EnemyField const& e : enemies_) {
                int dd = e.dist[dest];
                if (dd > floor_ && dd <= reachOf(e.visible) + e.reachBoost + bonus) danger += p_.wQueenRam * newL * mult;
            }
            for (EnemyField const& e : heardEnemies_) {
                int dd = e.dist[dest];
                if (dd > floor_ && dd <= reachOf(e.visible) + e.reachBoost + bonus) danger += p_.wQueenRamHeard * newL * mult;
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
            if (w_.t.round >= p_.blindGrace || queen_ || !b.portalOpen_)
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
        // Queen self-kill (two-way reservation): workers clear her exits; she in
        // turn keeps off cells on or beside seen ally heads — queens move first,
        // so an ally's current tile is a wall she cannot clear.
        if (queen_ && k == 0) {
            for (World::Seen const& s : w_.others)
                if (!isEnemy(s) && b.cheb(s.head, dest) <= 1) danger += p_.wQueenAlly;
            // Fog preference: landing on a tile nobody currently sees is how she
            // walks into unseen kelp — prefer seen-safe cells (a bonus, not a veto).
            if (!crossing && !w_.visible(dest)) danger += p_.wQueenFog;
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

    // Can any seen or fresh-heard enemy sprint onto `cell` this round?
    // Same reach the queen's ram screen prices (adjacency bonus on big maps).
    bool rammed(int cell) const {
        int bonus = (p_.qRamAdj > 0 && w_.board.NC >= p_.qRamAdjMinTiles) ? p_.qRamAdj : 0;
        for (EnemyField const& e : enemies_)
            if (e.dist[cell] <= reachOf(e.visible) + e.reachBoost + bonus) return true;
        for (EnemyField const& e : heardEnemies_)
            if (e.dist[cell] <= reachOf(e.visible) + e.reachBoost + bonus) return true;
        return false;
    }

    // Queen escape sprint: 1-step evasion cannot beat ceil(L/4)+L-2 approach
    // geometry — when every legal landing is inside a rammer's reach she is
    // already dead. Pay tail length for a multi-step MOVE to a tile no enemy
    // reaches this round. Intermediates only need to be free: the rammer can
    // only intercept at a head, and the resolution is simultaneous.
    bool queenEscape(std::string& path, std::vector<int> const& blk) {
        Board const& b = w_.board;
        int maxSteps = std::min(freeSteps(L_) + L_ - 2, p_.qEscapeMax);
        if (maxSteps < 2) return false;
        std::vector<int> dist(b.NC, INF), from(b.NC, -1), dirTo(b.NC, -1);
        std::vector<int> q{w_.head};
        dist[w_.head] = 0;
        int bestEnd = -1, bestSteps = INF, bestSafety = -1;
        for (size_t qi = 0; qi < q.size(); qi++) {
            int c = q[qi];
            if (dist[c] >= maxSteps) continue;
            for (int d = 0; d < 4; d++) {
                int n = b.nb[c * 4 + d];
                if (n < 0 || dist[n] != INF || blk[n] > 1) continue;
                dist[n] = dist[c] + 1;
                from[n] = c;
                dirTo[n] = d;
                q.push_back(n);
                if (!rammed(n)) {
                    int safety = INF;
                    for (EnemyField const& e : enemies_) safety = std::min(safety, e.dist[n]);
                    for (EnemyField const& e : heardEnemies_) safety = std::min(safety, e.dist[n]);
                    if (dist[n] < bestSteps || (dist[n] == bestSteps && safety > bestSafety)) {
                        bestSteps = dist[n];
                        bestSafety = safety;
                        bestEnd = n;
                    }
                }
            }
        }
        if (bestEnd < 0) return false;
        std::string rev;
        for (int c = bestEnd; c != w_.head; c = from[c]) rev += DCH[dirTo[c]];
        path.assign(rev.rbegin(), rev.rend());
        return true;
    }

    bool trySplit(Choice& out, Choice const& bestMove) {
        Board const& b = w_.board;
        if (w_.t.units >= w_.init.unitLimit || !w_.bodyKnown()) return false;
        if ((bestMove.eat && !bud_ && !hiding_ && !worker_) || bestMove.why == "trade" || bestMove.why == "defend" || bestMove.why == "slay") return false;
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
            // x3: a small-map queen out-grows keep = base + round/30 and never buds
            // (Stripes: first split at r42, opponents r16). Cap her base while the
            // brood is still building, gated on the breed phase not a tile count.
            if (queen_ && bud_ && w_.t.round < 100) keepBase = std::min(keepBase, 2);
            int keep = keepBase + w_.t.round / p_.growerKeepEvery;
            if (L_ < keep + p_.growerChild) return false;
            n = p_.growerChild;
        } else {
            if (L_ < p_.swarmSplitLen) return false;
            // Late game: the tiebreak is the longest dragon, so stop splitting and let
            // length pile up, unless the army needs rebuilding.
            if (w_.t.round >= p_.growRound && w_.t.units >= p_.lateSplitUnits) return false;
            // Worker-bud: a long parent buds off a child already at split
            // length; short parents halve as before.
            n = (L_ >= p_.swarmBudLen) ? p_.swarmBudChild : L_ / 2;
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
            if (!queen_) {
                int cover = 0;
                for (World::Seen const& s2 : w_.others)
                    if (isEnemy(s2) && s2.id != e.id && s2.head >= 0 && b.cheb(s2.head, e.head) <= 2) cover++;
                if (cover > 0) continue;  // covered victim: sprint-ram = our head alone
            }
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
