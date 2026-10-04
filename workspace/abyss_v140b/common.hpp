#pragma once

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

namespace bc {

// Direction order matches the engine: North is y-1.
enum Dir : int { N = 0, E = 1, S = 2, W = 3 };
inline constexpr int DX[4] = {0, 1, 0, -1};
inline constexpr int DY[4] = {-1, 0, 1, 0};
inline constexpr char DCH[4] = {'N', 'E', 'S', 'W'};
inline constexpr int INF = 1 << 29;

inline int dirFromChar(char c) {
    switch (c) {
    case 'N': return N;
    case 'E': return E;
    case 'S': return S;
    case 'W': return W;
    }
    return -1;
}

// ---- tagged sonar protocol -------------------------------------------------
// Directed u64 message layout:
//   [63:48] tag 0xC0A1 | [47:32] sender id | [31:28] type | payload
//   beacon: [27:20] x, [19:12] y, [11:4] len, [3:2] queen id + 1 (0 unknown), [1:0] role (0 swarm, 1 grower, 2 queen)
//   enemy : [27:20] x, [19:12] y, [11:4] len(clamped 15), [3:0] reserved
// The tag is keyed on our team letter (World::start sets it): both sides of a local
// self-play game run this code, and with one shared tag each side accepted the other's
// beacons (an enemy queen beacon could even overwrite our queen identity). No team
// uses the bare 0xC0A1 any more, so the old bots (abyss_st) and we ignore each other too.
inline uint64_t kSonarTag = 0xC0A1ull << 48;
inline void keySonarTag(char team) { kSonarTag = uint64_t(0xC0A1 ^ (team == 'A' ? 0x1111 : 0x2222)) << 48; }
//   champ : [47:32] = the CHAMPION's id (not the relayer's), [27:20] x, [19:12] y, [11:4] len, [3] 1 = it is our queen,
//           [2:0] coarse age code (0-3 exact, then 4-7, 8-15, 16-31, 32+)
//
// Round-keyed sonar (queen-kill lane, sonarKeyed=1): the top 16 bits become a hash of
// (secret, team, round, payload). A fixed tag can be recorded and fired back by the
// opponent (WaterCandle replays pings); a message is accepted for this round or the
// last, since a lower-id sender is heard the next round, so an echo from an older
// round fails (a false accept is ~1 in 65k). Keyed on team too, so self-play
// cross-talk stays impossible.
inline constexpr uint64_t kSonarSecret = 0x6A09E667F3BCC908ull;
inline uint64_t mix64(uint64_t z) {
    z += 0x9E3779B97F4A7C15ull;
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ull;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBull;
    return z ^ (z >> 31);
}
inline constexpr uint64_t kPayloadMask = (1ull << 48) - 1;
inline uint64_t sonarKey(uint64_t m, int round, char team) {
    uint64_t k = kSonarSecret ^ (m & kPayloadMask) ^ (uint64_t(uint32_t(round) & 0x3FF) << 48) ^ (uint64_t(uint8_t(team)) << 58);
    return mix64(k) >> 48;
}
inline uint64_t msgStamp(uint64_t m, int round, char team) { return (m & kPayloadMask) | (sonarKey(m, round, team) << 48); }
inline bool msgOursKeyed(uint64_t m, int round, char team) {
    uint64_t tag = m >> 48;
    return tag == sonarKey(m, round, team) || tag == sonarKey(m, round - 1, team);
}
enum MsgType : int { MsgBeacon = 0, MsgEnemy = 1, MsgChamp = 2 };

//   beacon: [27:20] x, [19:12] y, [11:5] len (clamped 127), [4] their queen seen dead,
//           [3:2] queen id + 1 (0 unknown), [1:0] role (0 swarm, 1 grower, 2 queen)
inline uint64_t msgBeacon(int id, int x, int y, int len, int role, int theirQueenDead = 0) {
    return kSonarTag | (uint64_t(id & 0xFFFF) << 32) | (uint64_t(MsgBeacon) << 28) |
           (uint64_t(x & 0xFF) << 20) | (uint64_t(y & 0xFF) << 12) |
           (uint64_t(std::min(len, 127) & 0x7F) << 5) | (uint64_t(theirQueenDead & 1) << 4) | uint64_t(role & 0xF);
}
inline uint64_t msgEnemy(int id, int x, int y, int len, int isQueen = 0) {
    return kSonarTag | (uint64_t(id & 0xFFFF) << 32) | (uint64_t(MsgEnemy) << 28) |
           (uint64_t(x & 0xFF) << 20) | (uint64_t(y & 0xFF) << 12) |
           (uint64_t(len & 0xFF) << 4) | uint64_t(isQueen & 0xF);
}
// Relay of where the champion (our queen while alive, else the longest dragon known) was last
// seen/heard (champion lane): every dragon that knows a fresh position forwards it, so feeders
// far from the champion can still walk to her and the team agrees on one champion.
inline uint64_t msgChamp(int champId, int x, int y, int len, int isQueen, int age) {
    return kSonarTag | (uint64_t(champId & 0xFFFF) << 32) | (uint64_t(MsgChamp) << 28) |
           (uint64_t(x & 0xFF) << 20) | (uint64_t(y & 0xFF) << 12) |
           (uint64_t(std::min(len, 255) & 0xFF) << 4) | (uint64_t(isQueen & 1) << 3) |
           uint64_t(age < 4 ? age : age < 8 ? 4 : age < 16 ? 5 : age < 32 ? 6 : 7);
}
inline int msgChampIsQueen(uint64_t m) { return int((m >> 3) & 1); }
inline int msgChampAge(uint64_t m) {
    // upper bound of each bucket: a relayed report can only look OLDER than it is, so gossip can never refresh evidence
    static constexpr int kAge[8] = {0, 1, 2, 3, 7, 15, 31, 40};
    return kAge[m & 7];
}
inline bool msgOurs(uint64_t m) { return (m >> 48) == (kSonarTag >> 48); }
inline int msgType(uint64_t m) { return int((m >> 28) & 0xF); }
inline int msgSender(uint64_t m) { return int((m >> 32) & 0xFFFF); }
inline int msgX(uint64_t m) { return int((m >> 20) & 0xFF); }
inline int msgY(uint64_t m) { return int((m >> 12) & 0xFF); }
inline int msgLen(uint64_t m) { return int((m >> 4) & 0xFF); }      // enemy and champ reports
inline int msgBeaconLen(uint64_t m) { return int((m >> 5) & 0x7F); } // beacons only: len moved for the dead bit
inline bool msgTheirQueenDead(uint64_t m) { return (m >> 4) & 1; }
inline int msgRole(uint64_t m) { return int(m & 0x3); }
// beacon bits [3:2]: which id is our queen as the sender knows it (0 unknown, 1 -> id 0, 2 -> id 1)
inline int msgQueenInfo(uint64_t m) { return int((m >> 2) & 0x3); }
inline bool msgEnemyIsQueen(uint64_t m) { return (m & 0xF) != 0; }

// Every tunable number lives here. These are plain hand-set starting values,
// not tuned ones: tuning them is the first thing to try.
struct Params {
    // pearl value
    double gamma = 0.80;              // discount per move of distance
    double eatBonus = 1.0;            // eating right now
    double exploreValue = 0.03;       // per never-seen tile
    double seenDecay = 0.97;          // belief a pearl we saw is still there, per round
    double spawnDecay = 0.985;        // belief an unseen spawned pearl is still there, per round
    double enemyCloserFactor = 0.5;   // pearl an enemy head reaches first
    int pocketEatLen = 3;             // non-queen dragons this short pay no wPocket/wFog on a step that eats (forage lane)
    int horizon = 48;                 // BFS depth considered
    int maxRivalFields = 12;          // distance fields computed for the nearest visible heads
    int maxDepth = 10;                // lookahead cap for the anytime search
    double leanMargin = 0.045;        // < this much turn clock left at decide(): one-step turn only

    // safety
    int spaceMargin = 3;              // reachable tiles needed: spaceFactor * length + margin
    double spaceFactor = 2.0;         // eating keeps the tail still, so plain length is optimistic
    double wSpace = 0.6;              // mild preference for open space
    double wDanger = 1.5;             // per own segment, tile next to an enemy head
    double wPocket = 1.5;             // entering a tile with a single way onward
    double wReverse = 1.5;            // entering a dead end we can only leave by a reverse split
    double wBlind = 2.0;              // portal into unseen tiles where dragons were seen lately
    double wBlindQuiet = 0.3;         // portal into unseen tiles with no recent sightings
    int blindMemory = 6;              // rounds a sighting near a portal exit stays relevant
    double wPortalLoiter = 1.0;       // ending a move on a tile beside a portal
    double wScout = 6.0;              // bonus for crossing a portal whose partner is unseen
    double wPortalScout = 4.0;        // explore-target weight on the lip of an unpaired portal
    int portalScoutUntil = 60;        // pull scouts to unpaired portal lips only before this round
    double wFog = 1.0;                // stepping through a never-seen edge (could be a wall)
    double mazeKelpFrac = 0.22;       // learned kelp fraction above this -> maze: wPocket off

    // phases
    int earlyEnd = 120;               // hunting squads switch on here ("mid game")
    int midEnd = 450;   // feed@360: double danger only after feeders established                 // late game: growers stop splitting, play safest

    // roles: growers (the starting dragons, or anyone long) farm and stay safe;
    // the swarm (split children) escorts, hunts and scavenges.
    int promoteLen = 10;              // any dragon this long plays as a grower
    int growerKeepBase = 4;           // grower keeps at least base + round/keepEvery segments
    int growerKeepEvery = 30;
    int growerChild = 2;              // growers bud off children this long
    double growerDanger = 3.0;        // extra danger multiplier for growers
    int swarmSplitLen = 4;            // swarm dragons split in half at this length
    int splitEnemyDist = 1;           // no split with an enemy head this close
    int splitRoom = 8;                // both halves need this much reachable room to split
    int budAlive = 18;                // below this unit count we are in the breed phase
    double budMult = 1.8;             // extra enemy-danger weight while breeding (contact-averse)

    // Forage-first opening (pearl lane): while the swarm is still breeding AND
    // the round is early (open_ = bud_ && round < openUntil) eat beats evade —
    // v104 ate ~7.4 pearls by r30 on small maps where top teams eat ~18.8.
    // Everything here is scoped to open_ and inert while openUntil == 0.
    int openUntil = 0;                // rounds the forage-first opening runs (0: off)
    double openDanger = 1.0;          // danger multiplier that replaces budMult while open_
    double openQueenDanger = -1.0;    // the queen's own replacement while open_ (<0: openDanger; = budMult exempts her)
    int openEnemyDist = 1;            // split ban radius that replaces splitEnemyDist while open_
    int openHunt = 0;                 // hunts while open_: 0 = their queen + grower-threats only, 1 = normal
    int openQueenKeep = -1;           // queen keep floor while budding during open_ (<0: growerKeepBase)
    int openEatLen = 4;               // eating steps ignore wPocket/wFog at <= this len while open_
    double openFog = 0.3;             // wFog multiplier while open_ (swarm dragons, non-maze maps)
    double openExplore = 0.12;        // per-tile scout value while open_ (swarm dragons)
    int openMaxTiles = 700;           // opening allowed on boards up to this many cells
    int openMazeMinTiles = 200;       // kelp-maze veto applies only above this size (arena survives)
    int openMinUnits = 99;            // v115+: brood clause disabled — open_ only on <=700-tile non-maze maps
    int openBroodTiles = 1300;        // ...on a board no bigger than this

    // free multi-steps: the first ceil(L/4) steps of a MOVE are free, so moves
    // of 2+ tiles cost nothing for L >= 5. We generate 2-step continuations of
    // each legal first step and score where they land.
    int twoStep = 1;                  // 0: one-step moves only
    int twoStepCap = 6;               // max extra 2-step evaluations at depth 1 (<2.5x cost)
    double wStepRisk = 0.0;           // per paid segment in a multi-step move (reserved)

    // economy / attrition
    int growerMinUnits = 40;          // growers exist only once the army is this big...
    int growRound = 300;              // ...or from this round
    int champUnits = 10;              // starting dragons promote to grower once the army is this big...
    int champRound = 30;              // ...or from this round, whichever comes first

    // Slay Queen: the lowest-id dragon on each team is its queen. Ours farms
    // defensively and is fed; theirs is worth dying for.
    double queenDanger = 2.0;         // extra danger multiplier on the queen herself
    int queenTradeSlack = 3;          // extra length slack when trading into their queen
    int queenBudUntil = 250;          // queen buds workers only before this round

    // Queen-kill lane: if the enemy queen's head is reachable by a sprint through free
    // tiles, take the trade immediately — whatever else this dragon was doing can wait.
    int slayAlways = 1;               // 0: old behaviour (length gate, growers never trade)
    int slayMaxSteps = 12;            // hard cap on the kill path (vision bounds it anyway)
    int slayExemptLongest = 1;        // our queen seen dead: our longest known dragon is the tiebreak, spare it

    // Protect the lead (queen-safety): at round 500 a dead queen counts 0, so once their
    // queen is confirmed dead ours only has to live. Feeding stops (it gains nothing and
    // costs units), head trades need a real army, and the queen fears every enemy's full
    // sprint reach, not just the adjacent ones.
    int protectLead = 1;              // 0: off
    double wLeadReach = 1.5;          // queen: per own segment, ending inside any enemy's sprint reach
    int leadTradeMinUnits = 8;        // the swarm trades heads only with at least this many units

    // Dead-end lookahead for the queen: a closed kelp region with no loop is a trap she
    // never escapes (fountain corridors, tree pockets). The swarm can afford a lost stub;
    // she cannot. (from the autarky lane's deadEnd scan, queen-scoped here)
    int trapOn = 1;                   // 0: off
    int trapScanCells = 32;           // BFS budget per candidate destination
    int trapMargin = 2;               // region <= length + this: a sure trap
    int trapSeenOnly = 0;             // 1: fog counts as a wall in the queen trap scan
    int trapSafeCells = 12;           // seenOnly: veto when proven-open room is this small
    int trapFrontier = 2;             // seenOnly: veto only when fog boundary is this thin
    int trapMaxTiles = 0;             // seenOnly applies only when NC <= this (0 = every map)

    // Frontier reach (weakhold pocket exit): a starving worker parked inside a
    // fully-seen pocket keeps ~450 unseen tiles within BFS reach but never
    // takes them — exploreValue * gamma^m is ~0.001 at corridor distances.
    // Counting unseen tiles reachable from the candidate gives a BFS-routed
    // pull toward exits (manhattan pulls died against walls, qsiege lane).
    // Self-gating: zero once the map is fully seen.
    double wFrontier = 0.004;         // per unseen tile reachable from the candidate
    double wFogPull = 6.0;            // pull toward the nearest unseen tile (BFS dist, gamma-weighted)
    int baitLen = 4;                  // beds in 1-exit cells only count as food at >= this length
    // Starving hysteresis: a worker with no reachable real food value sits in a
    // 2x2 orbit at corridor mouths — every direction scores ~0, so junction
    // noise flips the argmax each turn. Pay its current heading so it keeps
    // walking until something edible is in reach.
    double starveLocal = 0.75;        // reachable belief below this = starving
    double wPersist = 0.5;            // bonus for continuing the last move's heading
    int workerScan = 1;               // deadEnd scan on workers (k==0 only)
    int pullAfter = 60;               // fog/frontier pulls only after this round (queen lanes resolve early)
    int starveAge = 40;               // rounds without growth = really starving (belief lies about empty beds)
    int sonarKeyed = 1;               // 1: round-keyed hash tag (rejects replays), 0: fixed team-keyed tag

    // Hide-and-feed queen doctrine (alternative to the always-grower queen):
    // before queenHideUntil she plays like a swarm member — small, near
    // teammates — and buds every segment above queenHideLen into workers.
    // From queenHideUntil she is a pure grower; feeders may die for her from
    // queenFeedRound at the closer queenFeedMargin.
    int queenHide = 0;                // 1: hide-and-feed, 0: always-grower
    int queenHideUntil = 390;
    int hideMinTiles = 600;       // she needs a big map to disappear into         // she stays small before this round
    int queenHideLen = 2;             // length she keeps while hiding
    double wQueenRam = 30.0;          // queen-only: tile inside a seen enemy's sprint reach (ram screen)
    double wQueenRamHeard = 2.0;     // same for fresh heard enemies (fog rams are len2-3)
    double wQueenAlly = 4.0;          // queen: landing on/beside a seen ally head (two-way exit reservation)
    double wQueenFog = 2.0;           // queen: landing tile not currently visible (prefer seen-safe cells)
    double wQueenFlee = 0.0;          // hiding queen's fear of relayed enemy sightings (heardDanger; stage-2 OFF — A/B'd worse, see lane report)
    int queenFeedRound = 360;         // feeders wake for her from this round
    int queenFeedMargin = 2;          // feeders die for her once she is at least this long
    double wHideFriend = 0.8;         // hiding queen's pull toward teammates
    int lateSplitUnits = 20;          // after growRound the swarm splits only below this many units
    int tradeMinUnits = 4;            // below this many units we do not trade heads
    int tradeSlack = 1;               // trade if own length <= enemy visible length + slack
    int survivalUnits = 3;            // at or below: extra caution
    double survivalDanger = 3.0;

    // squads
    int squadSize = 3;                // per enemy target: 1 attacker + (squadSize-1) supporters
    int escortCount = 3;              // swarm dragons that stay around a visible grower
    int escortRadius = 5;             // enemy head this close to a grower is a threat
    int escortRing = 3;               // escorts hold this distance from the grower
    int supportRing = 3;              // supporters hold this distance from the target, ready to eat
    int qEscortThreat = 8;            // 5b: escorts form only while an enemy is within this of the queen's cell
    int qEscortDist = 14;             // only workers already this close to her cell volunteer
    int qRamAdj = 1;                  // weakhold-dims only: ram-adjacency reach bonus (head-to-head kills beside her head)
    int qVetoReach = 1;               // queen: dest inside an enemy's this-turn kill reach = lethal tier
    int qEnemyLenMin = 3;             // edge-seen enemies under-read len (head only); killers are len2-3
    double wQueenLeash = 0.0;         // queen overshoot penalty (steering-4 leash; stage OFF — A/B'd worse, see lane report)
    int leashDist = 8;
    int leashUntil = 100;             // comfort zone only before this round
    double wQueenVeto = 500.0;        // lethal-tier penalty minus dd (near-veto, still prefers distance)
    int huntMirror = 0;               // B1: with no fresh queen sighting, expendables hunt her start mirror
    int huntRound = 25;               // B1: mirror-hunters release at this round
    int huntLenMax = 3;               // B1: expendable cap (len <= this hunts)
    int huntSquad = 3;                // B1: at most this many mirror-hunters
    int huntSpawnMax = 30;            // B1: only dragons born this early know the spawn region
    double wHuntMirror = 2.0;         // B1: pull toward the mirror target (weaker than sighting pull)
    double wHunt = 1.5;
    double wEscort = 0.8;
    double wSupport = 0.6;

    // head-on trades and sprints (a MOVE of k steps needs length k + 1)
    int localRadius = 3;              // heads this close (Chebyshev) to a trade site count as local
    int reachCap = 3;                 // enemy sprint reach considered: min(visible length - 1, cap)
    double wExposed = 1.2;            // per own segment, ending within an enemy head's reach
    double wTailStrike = 0.0;         // queen: enemy head within its own length of our dest (tail can spawn a rammer)
    double exposedFavour = 0.35;      // multiplier when we have the local numbers there
    int sprintMax = 3;                // our own sprint trades: at most this many steps
    int sprintTrades = 1;             // 0: no sprint trades
    // How enemy heads count as danger:
    // 0: next to an enemy head, unless we would trade with it; sprint reach ignored
    // 1: anywhere inside an enemy's sprint reach, reduced where we have the local numbers
    // 2: like 0, plus sprint-reach danger only where enemies outnumber us
    int exposureMode = 0;

    // end-game feeding: the longest dragon breaks a round-500 tie. A small dragon that
    // sees a teammate at least feedMargin longer walks to its head and dies there,
    // dropping ceil(L/2) pearls where it will eat them.
    int feedRound = 400;
    // ---- champion lane (abyss_v102_champ): one champion; our queen while she lives ----
    int champOne = 1;                 // 1: feeders feed only the champion (queen, else the team's longest known)
    int champMemory = 40;             // rounds a sighting/beacon/relay stays a usable pull target
    int champFallbackRound = 400;     // queen-less champion (longest known dragon) from this round (= old feedRound)
    int champFeedDist = 2;            // champion feeds die when this close to a tile beside its head (feedDist 1 let her walk away)
    int feedFar = 1;                  // 1: feed pull uses the long-range discount gammaFar (+ manhattan pull past the BFS horizon)
    int feedHeardDie = 2;             // die in place beside a champion we only HEARD if the report is <= this many rounds old (0 off)
    int boxFeedDist = 6;              // boxed-in dragon within this many tiles of the champion dies in place (0 off)
    int feedMinUnits = 3;             // a feeder dies only while the team has >= this many dragons (do not wipe a remnant out)
    int champRelay = 1;               // 1: dragons that know the champion's position forward it (MsgChamp)
    int champRelayAge = 30;           // forward only reports at most this old (the age is coarsely coded)
    int queenRelayFrom = 330;         // queen position relay starts at this round
    int champRelayFrom = 330;         // queen-less champion relay starts at this round
    int champMargin = 0;              // challenger must exceed the heard champion's length by
                                      // this to take the title (0: any +1 takeover — churns on
                                      // large swarms; feed suicides scatter across a moving target)
    int feedStop = 490;               // later sacrifices cannot be eaten in time
    int feedMargin = 4;
    int feedMaxLen = 6;               // only small dragons feed
    int feedDist = 1;                 // die when this close to a tile next to the big head
    double wFeed = 3.0;

    // hot beds (fountains): fast-respawning beds, valued as a long-range pull
    // proportional to their yield rate (pearls per round).
    int hotObs = 3;                   // a bed is hot once this many countdowns were seen on it...
    int hotGap = 10;                  // ...and none exceeded this
    double hotRate = 0.1;             // mean respawn gap <= 10 rounds
    double wHot = 2.0;
    double gammaFar = 0.93;           // discount per move for the long-range pull
    int hotYield = 4;                 // yield a hot bed only to a teammate this close to it

    // sonar
    int sonarOn = 1;                  // 0: silence
    int heardMemory = 14;             // rounds a heard beacon stays valid
    int heardEnemyMemory = 8;         // rounds a relayed enemy sighting stays valid
    int maxHeardFields = 4;           // extra BFS fields for heard teammates
    int heardFresh = 3;               // beacons this fresh can claim pearls like sight
    int maxHeardEnemyFields = 3;      // extra BFS fields for heard enemies
    double wHeardEnemy = 1.0;         // grower danger per segment inside a heard enemy's reach
    int heardEnemyReach = 3;          // heard enemy is dangerous within this BFS distance
    double wHuntHeard = 0.0;          // idle swarm pull toward a relayed enemy position (0: ghost chases starved the swarm)

    // Queen-assassin squad: while a relayed enemy-queen sighting is fresh, the
    // K closest swarm dragons drop forage/feed duty and converge on the report.
    int assassinCount = 3;            // squad size (K)
    double assassinForce = 0.5;       // assign only if the K's combined length >= heard len * this
    double wAssassin = 3.0;           // pull toward the reported cell (vs wHunt = 1.5)
    int assassinMaxAge = 5;           // report staleness cutoff in rounds
    int assassinMaxDist = 16;         // no cross-map pilgrimages: only nearby swarm dragons go
    double assassinForage = 0.3;      // fraction of pearl value an assassin still pursues
    double assassinFogMult = 3.0;     // extra fog fear while on mission (wall dives were the bleed)

    // Doctrine overrides on brawl maps (World::mapBrawl): knife fights first,
    // farming second.
    int champRoundBrawl = 70;         // the champion waits out the knife fight
    int growerMinUnitsBrawl = 55;     // growers appear only once the swarm is big
    int heardMemoryBrawl = 8;         // small maps go stale fast
    int feedRoundBrawl = 380;         // feed earlier: games end sooner
};

inline Params const kParams = [] {
    Params p;
    p.queenHide = 1;  // this variant runs the hide-and-feed doctrine
    // v104 = qk minus queen-escape removals (paired analysis: removals threw 20 queen-fate
    // games via hitSelf+h2h) + cf consolidation timing + tail-strike queen fear:
    // pearl lane: forage-first opening — while breeding and round < 48, drop the
    // breed-phase fear (openDanger 1.0 vs budMult 1.8), split within 1 of enemy
    // heads, hunt only their queen and grower-threats, bud the queen to keep 3,
    // cheap fog for the swarm on open maps, stronger scout pull.
    p.openUntil = 48;               // gated: open_ engages only where it wins (pearl4)
    p.openQueenKeep = 3;
    p.openQueenDanger = 1.8;          // queen exempt from the relief: keeps budMult-level fear
    p.feedRound = 360;
    p.champFallbackRound = 360;
    p.feedRoundBrawl = 300;
    p.wTailStrike = 2.0;
    p.trapSeenOnly = 1;               // wh4: weakhold pocket fix — fog is a wall for the queen
    p.trapSafeCells = 8;              // wh4: veto only the tiny mouth signature
    p.trapFrontier = 1;               // wh4: single-cell fog aperture only
    p.trapMaxTiles = 700;             // wh4: small maps only — big maps get v104-identical scans
    return p;
}();

// Free movement steps per turn under Slay Queen rules (post Oct 1 update):
// the first ceil(L/4) steps of a MOVE cost nothing, the rest cost a segment each.
inline int freeSteps(int len) { return (len + 3) / 4; }

// Seconds since process start. In the judge's sandbox the clock is virtual and
// advances 1 ns per CPU point spent (unswbc sandbox.py: now = spent + slept_ns),
// so the 100M-point turn budget is 0.1 s on this clock.
inline double clockNow() {
    static auto const start = std::chrono::steady_clock::now();
    return std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
}

// Seconds of that clock the search may spend per turn: 0.075 = 75M of the 100M
// points. Test builds may override it to keep native local games short.
#ifndef BC_TURN_BUDGET
#define BC_TURN_BUDGET 0.075
#endif

}  // namespace bc
