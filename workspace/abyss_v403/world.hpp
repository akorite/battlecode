#pragma once

#include "board.hpp"
#include "io.hpp"

namespace bc {

// What one dragon process knows. Rebuilt from scratch by every process: a split
// child inherits nothing, so everything here must be recomputable.
//
// Everything is learnt from vision: terrain, portals, pearl beds, their countdowns
// and how fast each bed refills.
struct World {
    Init init;
    Board board;

    // pearls, from vision only
    int simRound = -1;
    std::vector<int> next;        // countdown per tile while tracked from vision, -1 unknown
    std::vector<int> lastSpawn;   // round a tracked countdown ran out (a pearl likely spawned), -1 never
    std::vector<int> seenRound;   // last round the tile was in vision, -1 never
    std::vector<int8_t> seenPearl;
    std::vector<int16_t> maxCd;   // largest countdown ever seen on a bed: its refill gap, roughly
    std::vector<int16_t> cdObs;   // rounds a countdown was seen on the bed

    // this turn
    Turn t;
    int head = -1;
    std::vector<int> body;        // own body, head first; may be a prefix while the tail is unknown
    std::vector<int> ownExtra;    // own segments seen in vision but not part of the tracked prefix
    std::vector<int> occ;         // tile -> dragon id occupying it (other dragons), -1 free
    std::vector<int> occHeadId;   // tile -> id if it holds another dragon's head
    std::vector<int> visRound;    // == t.round when the tile is in this turn's vision
    std::vector<int> occSeen;     // last round another dragon was seen on the tile, -1 never
    struct Seen { int id; char team; int head; int headDir; int visible; };
    std::vector<Seen> others;     // other dragons with a visible head

    // Tagged sonar: teammate beacons and relayed enemy sightings, by dragon id.
    // Beacon senders are always ours (the tag is team-secret); enemy reports are
    // positions a teammate saw within the last round.
    struct Heard { int id; int cell; int len; int role; int round; };
    std::vector<Heard> heard;            // teammate beacons, latest per sender
    std::vector<Heard> heardEnemies;     // relayed enemy sightings, latest per position
    std::vector<Heard> heardFood;        // broadcast food clusters, latest per cell
    // Freshest evidence (sight, her own beacon, or a relayed MsgQueen) of where our queen is.
    int queenCell = -1, queenLen = 0, queenRound = -1;
    // Best non-queen champion candidate known (longest teammate; ties lowest id), same sources.
    int chId = -1, chCell = -1, chLen = 0, chRound = -1;
    int champAnchor = -1;                // self-elected champion's locked cell (persists across turns)
    int firstRound = -1;                 // first round this process observed (children start late)
    int echoEnemy = 0;                   // enemy echoes this turn (enemy + enemyHead)

    // Portal ends seen, by portal id: (orient 0 = hE / 1 = vE, x, y). A portal is only
    // walkable once both ends are known (Board::stepRaw treats an unpaired end as a wall).
    struct PortalEnd { int orient, x, y; };
    std::vector<std::pair<int, std::vector<PortalEnd>>> portalEnds;
    int spawnCell = -1;             // first decide's head ~ spawn tile (S0 mirror waypoint)
    int startCell = -1;                  // first head cell observed (~ spawn for opening-born dragons)
    bool manyPortals_ = false;   // sticky: >portalGuessEnds distinct portal ids ever seen -> dense-portal map
    int startUnits = -1;          // UNIT_COUNT on round 0 (starting dragons per team), -1 unknown

    // Starting dragons get the first ids (both teams). Round 0 tells us how many there are;
    // a split child born later cannot know, and assumes 2 per team.
    int initialCount() const { return startUnits > 0 ? 2 * startUnits : 4; }
    bool isInitial(int id) const { return id < initialCount(); }
    // The designated early champion. Dragons are created in alternating spawn
    // order, so our lowest id is 0 for A and 1 for B; if a map does not follow
    // that, the slot simply points at nobody (no early champion).
    // Queens are ids 0 and 1, one per team, but which is ours varies per game and
    // split children get the next free id regardless of team, so id parity says
    // nothing. ourQueen is learned: we are the queen (id <= 1), we saw id 0/1 with
    // its team letter, we heard a beacon from id 0/1, or a teammate's beacon told
    // us. Until then fall back to the old parity guess.
    int ourQueen = -1;
    int ourQueenSrc = -1;  // how we know: 3 we are her, 2 seen with team letter, 1 her own beacon, 0 relayed
    void learnQueen(int id, int src) {
        if (src >= ourQueenSrc) { ourQueen = id; ourQueenSrc = src; }
    }
    int champId() const { return ourQueen >= 0 ? ourQueen : (init.id & 1); }
    // The enemy team's queen: the other one of {0, 1}.
    int enemyQueen() const { return 1 - champId(); }

    // Queen death tracking (queen-kill lane): where each queen was last seen, and the
    // round we judged her dead — she vanished from a cell we can see that now shows
    // the pearls she dropped. A later sighting clears the mark.
    struct QueenTrack { int round = -1; std::vector<int> cells; int deadRound = -1; };
    QueenTrack qtrack[2];
    bool queenDead(int id) const { return id >= 0 && id <= 1 && qtrack[id].deadRound >= 0; }
    int theirQueenDeadHeard = -1;  // round a teammate's beacon last said their queen is dead, -1 never
    bool theirQueenDead() const { return queenDead(enemyQueen()) || theirQueenDeadHeard >= 0; }
    // Map classes, keyed on properties every dragon sees at INIT (so the whole
    // team agrees without coordinating): the 32x16 killboxes and 25x25 trophy
    // are brawls where farming early gets you eaten.
    bool mapBrawl() const { return init.w * init.h <= 700; }

    // Fraction of seen edges that are kelp. High values mean a maze (Portals),
    // where pocket-fear paralyses the swarm into pacing its spawn corner.
    double kelpFraction() const {
        int seen = 0, kelp = 0;
        for (Edge const& e : board.hE) if (e.seen) { seen++; kelp += e.kind == 1; }
        for (Edge const& e : board.vE) if (e.seen) { seen++; kelp += e.kind == 1; }
        return seen ? static_cast<double>(kelp) / seen : 0.0;
    }

    bool visible(int c) const { return visRound[c] == t.round; }

    bool bodyKnown() const { return static_cast<int>(body.size()) == t.length; }

    void start(Init const& in) {
        init = in;
        keySonarTag(in.team);
        if (in.id <= 1) learnQueen(in.id, 3);
        board.init(in.w, in.h);
        next.assign(board.NC, -1);
        lastSpawn.assign(board.NC, -1);
        seenRound.assign(board.NC, -1);
        seenPearl.assign(board.NC, 0);
        visRound.assign(board.NC, -1);
        occSeen.assign(board.NC, -1);
        maxCd.assign(board.NC, 0);
        cdObs.assign(board.NC, 0);
    }

    int visTile(int col, int row) const { return board.id(board.X(head) + col - 3, board.Y(head) + row - 3); }

    // ---- pearls ---------------------------------------------------------------

    void tickTo(int round) {
        while (simRound < round) {
            simRound++;
            for (int c = 0; c < board.NC; c++) {
                if (next[c] < 0) continue;
                if (--next[c] <= 0) {
                    lastSpawn[c] = simRound;
                    next[c] = -1;  // the next gap is unknown until we see the bed again
                }
            }
        }
    }

    // Probability a pearl is on tile c right now.
    double belief(int c, Params const& p) const {
        if (seenRound[c] == t.round) return seenPearl[c] ? 1.0 : 0.0;
        double b = 0;
        if (seenPearl[c]) b = std::pow(p.seenDecay, t.round - seenRound[c]);
        if (lastSpawn[c] > seenRound[c]) b = std::max(b, std::pow(p.spawnDecay, t.round - lastSpawn[c]));
        return b;
    }

    // ---- per turn --------------------------------------------------------------

    void observe(Turn const& turn, Params const& p) {
        t = turn;
        if (static_cast<int>(portalEnds.size()) > p.portalGuessEnds) manyPortals_ = true;
        // Few-portal mid-size maps only: dense-portal maps starve on phantom
        // routes; tiny maps' queens die on lanes. Weakhold has ZERO portals —
        // require at least one portal end seen (bisect fix).
        board.portalOpen_ = board.NC > p.portalGuessMinTiles && board.NC <= p.portalGuessMaxTiles && !manyPortals_ && !portalEnds.empty();
        board.portalGuess_ = board.portalOpen_ && t.round < p.portalGuessUntil;
        if (firstRound < 0) firstRound = t.round;
        if (t.round == 0 && startUnits < 0) startUnits = t.units;
        // own head from the parts list (segments of one dragon come head first)
        std::vector<int> visibleOwn;
        for (Part const& part : t.parts)
            if (part.id == init.id) visibleOwn.push_back(board.id(part.x, part.y));
        head = visibleOwn.empty() ? board.id(t.tiles[24].x, t.tiles[24].y) : visibleOwn.front();
        if (spawnCell < 0) spawnCell = head;
        if (startCell < 0) startCell = head;

        tickTo(t.round);

        // learn edges; portal ends are remembered by id and paired once both are seen
        bool changed = false;
        for (int r = 0; r < 8; r++)
            for (int c = 0; c < 7; c++) {
                int cell = visTile(c, r);
                Edge& e = board.hE[cell];
                if (e.kind != t.hRows[r][c].kind) e = Edge{t.hRows[r][c].kind, 1}, changed = true;
                else e.seen = 1;
                if (e.kind == 2) changed |= notePortal(t.hRows[r][c].pid, 0, board.X(cell), board.Y(cell));
            }
        for (int r = 0; r < 7; r++)
            for (int c = 0; c < 8; c++) {
                int cell = visTile(c, r);
                Edge& e = board.vE[cell];
                if (e.kind != t.vRows[r][c].kind) e = Edge{t.vRows[r][c].kind, 1}, changed = true;
                else e.seen = 1;
                if (e.kind == 2) changed |= notePortal(t.vRows[r][c].pid, 1, board.X(cell), board.Y(cell));
            }
        if (changed) board.rebuild();

        for (VisTile const& v : t.tiles) {
            int c = board.id(v.x, v.y);
            seenRound[c] = t.round;
            visRound[c] = t.round;
            seenPearl[c] = v.pearl;
            if (v.pearlIn >= 0) {
                board.bed[c] = 1;
                next[c] = v.pearlIn;
                learnGap(c, v.pearlIn, p);
            } else {
                board.bed[c] = 0;
            }
        }

        // own body: the contiguous visible prefix is authoritative, older tracking fills
        // the rest. A body that leaves vision and comes back shows up non-contiguous.
        size_t k = visibleOwn.empty() ? 0 : 1;
        while (k < visibleOwn.size() && adjacent(visibleOwn[k - 1], visibleOwn[k])) k++;
        ownExtra.assign(visibleOwn.begin() + k, visibleOwn.end());
        visibleOwn.resize(k);
        std::vector<int> merged = visibleOwn;
        if (!body.empty() && !visibleOwn.empty()) {
            // body was advanced by our last move; keep the tracked part beyond the visible prefix
            for (size_t i = visibleOwn.size(); i < body.size(); i++) merged.push_back(body[i]);
        }
        // The neck is always one step back along DIR (portals are symmetric), even when
        // it is out of vision because the body runs through a portal.
        if (merged.size() == 1 && t.length >= 2) {
            int neck = board.nb[head * 4 + (t.dir ^ 2)];
            if (neck >= 0) merged.push_back(neck);
        }
        if (static_cast<int>(merged.size()) > t.length) merged.resize(t.length);
        body.swap(merged);

        occ.assign(board.NC, -1);
        occHeadId.assign(board.NC, -1);
        others.clear();
        for (Part const& part : t.parts) {
            if (part.id == init.id) continue;
            int c = board.id(part.x, part.y);
            occ[c] = part.id;
            occSeen[c] = t.round;
            if (part.head) {
                occHeadId[c] = part.id;
                others.push_back({part.id, part.team, c, part.facing, 0});
            }
        }
        for (Seen& s : others)
            for (Part const& part : t.parts)
                if (part.id == s.id) s.visible++;
        if (ourQueenSrc < 2)
            for (Part const& part : t.parts)
                if (part.id <= 1) { learnQueen(part.team == init.team ? part.id : 1 - part.id, 2); break; }

        // Our queen: any visible part is fresh evidence (head preferred); a remembered position that is in
        // view with no queen on it means she moved off or died, so the evidence is dropped (otherwise relays
        // keep a dead queen alive and feeders loiter at her grave).
        if (ourQueen >= 0 && ourQueen != init.id) {
            int cnt = 0, partCell = -1, headCell = -1;
            for (Part const& part : t.parts)
                if (part.id == ourQueen && part.team == init.team) {
                    cnt++;
                    if (partCell < 0) partCell = board.id(part.x, part.y);
                    if (part.head) headCell = board.id(part.x, part.y);
                }
            if (cnt > 0) {
                queenCell = headCell >= 0 ? headCell : partCell;
                queenLen = std::max(cnt, queenLen);
                queenRound = t.round;
            } else if (queenRound >= 0 && queenRound < t.round && queenCell >= 0 && visible(queenCell)) {
                queenRound = -1;
            }
        }
        // Champion evidence from sight. A remembered champion whose cell we now see empty of her is gone.
        if (chId >= 0 && chRound >= 0 && visible(chCell)) {
            bool here = false;
            for (Seen const& s : others)
                if (s.id == chId && s.team == init.team) here = true;
            if (!here) chRound = -1;
        }
        for (Seen const& s : others)
            if (s.team == init.team) noteChamp(s.id, s.head, s.visible, t.round, p);

        // Queen death tracking: a queen seen last round who is gone from a cell we can
        // see now — with the pearls she dropped sitting on it — is dead. An enemy-queen
        // sighting also clears a teammate's stale 'their queen is dead' beacon.
        for (int q = 0; q <= 1; q++) {
            QueenTrack& qt = qtrack[q];
            std::vector<int> cells;
            for (Part const& part : t.parts)
                if (part.id == q) cells.push_back(board.id(part.x, part.y));
            if (!cells.empty()) {
                qt.round = t.round, qt.cells.swap(cells);
                qt.deadRound = -1;  // seen alive: any earlier mark was wrong
                for (Part const& part : t.parts)
                    if (part.id == q && part.team != init.team) theirQueenDeadHeard = -1;
                continue;
            }
            if (qt.deadRound < 0 && qt.round == t.round - 1)
                for (int c : qt.cells)
                    if (visible(c) && seenPearl[c]) { qt.deadRound = t.round; break; }
            qt.cells.clear();
        }

        // tagged sonar inbox
        for (uint64_t m : t.msgs) {
            if (p.sonarKeyed ? !msgOursKeyed(m, t.round, init.team) : !msgOurs(m)) continue;
            int sid = msgSender(m);
            if (sid == init.id) continue;  // our own ping bounced off our body
            int cell = board.id(msgX(m), msgY(m));
            if (msgType(m) == MsgChamp) {
                // sender field = the champion's id: a report about him, relayed by someone else
                if (msgChampIsQueen(m)) learnQueen(sid, 0);
                noteChamp(sid, cell, msgLen(m), t.round - msgChampAge(m) - 1, p);  // +1 per hop: relays only age
            } else if (msgType(m) == MsgFood) {
                bool dup = false;
                for (Heard& h : heardFood)
                    if (h.cell == cell && h.round >= t.round - 6) { dup = true; break; }
                if (!dup) heardFood.push_back({sid, cell, msgLen(m), 0, t.round});
            } else if (msgType(m) == MsgEnemy) {
                int elen = std::min(msgLen(m), 15);
                bool dup = false;
                for (Heard& h : heardEnemies)
                    if (h.cell == cell && h.round >= t.round - 4) { dup = true; break; }
                if (!dup) heardEnemies.push_back({sid, cell, elen, msgEnemyIsQueen(m) ? 1 : 0, t.round});
            } else {
                if (sid <= 1) learnQueen(sid, 1);  // only our team passes the keyed tag
                else if (msgQueenInfo(m) != 0) learnQueen(msgQueenInfo(m) - 1, 0);
                bool found = false;
                for (Heard& h : heard)
                    if (h.id == sid) { h.cell = cell; h.len = msgBeaconLen(m); h.role = msgRole(m); h.round = t.round; found = true; break; }
                if (!found) heard.push_back({sid, cell, msgBeaconLen(m), msgRole(m), t.round});
                noteChamp(sid, cell, msgBeaconLen(m), t.round, p);
                if (msgTheirQueenDead(m)) theirQueenDeadHeard = t.round;
            }
        }
        echoEnemy = t.echoes[3] + t.echoes[4];
    }

    // Fold one piece of evidence ("dragon `id` was at `cell` with length `len` on `round`") into the
    // queen / champion-candidate records. Our queen is tracked separately: she is the champion
    // whenever she is alive. Everyone else competes on (length desc, id asc).
    void noteChamp(int id, int cell, int len, int round, Params const& p) {
        if (id == init.id) return;
        if (id == ourQueen) {
            if (round >= queenRound) { queenCell = cell; queenLen = len; queenRound = round; }
            return;
        }
        bool stale = chRound < 0 || t.round - chRound > p.champMemory;
        if (stale || (id == chId && round >= chRound) || len > chLen || (len == chLen && id < chId))
            if (!(id != chId && !stale && round < chRound - 8)) {  // an old report must not oust a fresher champion
                chId = id; chCell = cell; chLen = len; chRound = round;
            }
    }

    void pruneHeard(Params const& p) {
        std::vector<Heard> keep;
        for (Heard const& h : heard)
            if (t.round - h.round <= p.heardMemory) keep.push_back(h);
        heard.swap(keep);
        keep.clear();
        for (Heard const& h : heardEnemies)
            if (t.round - h.round <= p.heardEnemyMemory) keep.push_back(h);
        heardEnemies.swap(keep);
        keep.clear();
        for (Heard const& h : heardFood)
            if (t.round - h.round <= p.heardFoodMemory) keep.push_back(h);
        heardFood.swap(keep);
    }

    // Remember a portal end; pair both ends (like the engine: the two edges sharing an id)
    // as soon as both are known. Returns true when the board's links changed.
    bool notePortal(int pid, int orient, int x, int y) {
        std::vector<PortalEnd>* ends = nullptr;
        for (auto& pe : portalEnds)
            if (pe.first == pid) ends = &pe.second;
        if (!ends) {
            portalEnds.push_back({pid, {}});
            ends = &portalEnds.back().second;
        }
        for (PortalEnd const& e : *ends)
            if (e.orient == orient && e.x == x && e.y == y) return false;
        ends->push_back({orient, x, y});
        if (ends->size() != 2) return false;
        PortalEnd const& a = (*ends)[0];
        PortalEnd const& b = (*ends)[1];
        Edge& ea = a.orient == 0 ? board.hE[board.id(a.x, a.y)] : board.vE[board.id(a.x, a.y)];
        Edge& eb = b.orient == 0 ? board.hE[board.id(b.x, b.y)] : board.vE[board.id(b.x, b.y)];
        ea.kind = eb.kind = 2;
        ea.partnerOrient = static_cast<int8_t>(b.orient);
        ea.px = static_cast<int16_t>(b.x);
        ea.py = static_cast<int16_t>(b.y);
        eb.partnerOrient = static_cast<int8_t>(a.orient);
        eb.px = static_cast<int16_t>(a.x);
        eb.py = static_cast<int16_t>(a.y);
        return true;
    }

    // A bed's countdown right after a spawn is its whole gap, so the largest one seen
    // estimates the gap from above as the bed keeps being watched. Beds are counted
    // as hot (fountains) once enough small countdowns have been seen.
    void learnGap(int c, int cd, Params const& p) {
        if (cd > maxCd[c]) maxCd[c] = static_cast<int16_t>(std::min(cd, 30000));
        if (cdObs[c] < 30000) cdObs[c]++;
        bool hot = cdObs[c] >= p.hotObs && maxCd[c] <= p.hotGap;
        // Policy's hot-bed pull reads the gap range from the board.
        board.gapMin[c] = board.gapMax[c] = static_cast<int16_t>(hot ? std::max<int>(1, maxCd[c]) : 0);
    }

    bool adjacent(int a, int b) const {
        for (int d = 0; d < 4; d++)
            if (board.nb[a * 4 + d] == b) return true;
        return false;
    }

    // Called after choosing a move so next turn's merge has the right prefix.
    void advanceBody(int dest, bool grows) {
        body.insert(body.begin(), dest);
        if (!grows && !body.empty() && static_cast<int>(body.size()) > t.length) body.pop_back();
    }
};

}  // namespace bc
