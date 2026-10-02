# 14. Architecture study — our bot vs the post-queen meta (Oct 1)

Scope: workspace/abyss (submitted v95) vs measured top-5 bench data + 13_slay_queen_meta.md.

## 14.1 Our pipeline (as built)

Per-dragon per-turn (`policy.hpp`):
1. `buildBase/buildTargets` — BFS distance fields from world state (walls, pearls, enemies).
2. `buildFriendFields/buildSquadTargets` — allied swarm fields; squad/hunt/escort assignments
   (escort = stay within escortRadius of a grower; only assigned midGame+).
3. `scoreFrom` — greedy beam over first-step options: move-eat / trade-h2h / block / wait.
   Multipliers: growerDanger, queenDanger (on our queen), territory/space/hunt/pull weights.
4. `trySplit` — emits SPLIT when headRoom + budget allow; grower queen buds until queenBudUntil.
5. `sprintTrade` — last resort: spend length for a kill reach (maxSteps ~ freeSteps+len-2).
6. Fallbacks: `hasRoomyMove` → deterministic legal move → nothing (= noValidAction death).

Roles are implicit, not declared: `isGrower` (champ always + weakest units while swarm is small),
everyone else hunts/feeds. Communication: **none** — no tagged sonar protocol (echoes only
serve as wall/range sensing). No inter-dragon memory of heard state; each dragon re-derives
everything from its own view each turn.

## 14.2 Gap table

| component | ours | meta-best | patchable? | effort |
|---|---|---|---|---|
| Queen survival | always-grower + 2x danger; dies r5-74 unscreened; noValidAction kills when boxed | escort ring ~9-10 tiles, ~2 exits kept open, enemy ≥20 tiles away | YES — policy.hpp escort assignment (extend to r0, widen radius, add "exit-count" danger term); needs boxed-queen fallback move | 0.5 session |
| Tagged sonar | zero msgs; echoes unused for intel | u64 tagged protocol (ours exists in abyss_dev), queen hub ~400 pings/g | YES — merged in abyss_dev (MsgEnemy incl. queen flag, heard fields feed EnemyField pulls); needs A/B + relay hub role | 0.5 (mostly verify) |
| Swarm scaling | splits ~100-430/g but gets early-wiped on violent maps (<25 splits by r150); peak ~35 | peak 45-50, splits ~270/g | PARTLY — split gating is fine; the wipe is a brawl-positioning problem (danger weights + head-count), tune params | sweep lane |
| Corpse economy | feedHead_ steers weak units to feed growers/queen | WHQ: 51 suicides/g feeding queen to len 34.7 | YES — policy.hpp feed block already prefers queen; need suicide-funnel (deliberate death into queen zone) not just opportunistic feeding | 1 session |
| Sprint | sprintTrade kill-dive only | surgical: ~150-176/g winners, dives+escapes | YES — widen sprintTrade to escape+surgical (cap free steps, avoid transit spam); movement lane covers | lane |
| Queen assassination | slay trade when adjacent (+queenTradeSlack) | Stockfish: sonar-located queen, converged squad | YES-ish — heardEnemy queen flag in dev build + hunt pulls; needs dedicated assassin squad role | 1 session |
| Map doctrine | brawl overrides only (mapBrawl w*h<=700) | per-map elo; doctrine switch (open vs corridor vs portal) | YES — adjustByMap() exists; extend class detection | small |
| noValidAction deaths | ~21% of deaths all teams; our queen died of it r10 | exit-aware queen positioning | YES — queen danger term for exit count + emergency any-legal-move fallback | small |

## 14.3 Specific answers

(a) Queen sonar hub — feasible inside the framework: dev build already packs role-2 queen
beacons + enemy-queen flags into u64 msgs. What's missing vs Cutlery: a *hub* role (queen stays
central, relays far heard-state), and heard-state persistence beyond heardMemory rounds.
Patchable — no rewrite. Est. 0.5 session on top of dev build.

(b) Queen-hide doctrine needs two things the policy can't express yet: (i) a "stay small"
mode where the queen refuses feeding and stays len 2 until r300+, (ii) a "return home/keep
exits" positional term — current scoring has no concept of home or exit count, only danger
fields. Both are additive in scoreFrom/isGrower — patchable, ~1 session (QUEEN-DOCTRINE lane
is testing exactly this).

(c) Best effort/return for ~1940:
1. **Sonar protocol-3 merge** (dev build) — biggest measured deficit: 0 intel vs 2-4 pings/action;
   unlocks coordinated hunts + queen tracking. Merge after A/B.
2. **Queen protection package**: early escort + exit-awareness + any-legal-move fallback —
   directly targets the r5-74 queen deaths that decide games.
3. **Corpse-feed-queen + assassin squad** — the WHQ/Stockfish combination: queen fed to len 30+,
   enemy queen hunted via sonar. Needs lanes' results first.

Order: sonar merge → queen protection → feed/assassin. Param sweeps and movement retune
continue in parallel lanes.
