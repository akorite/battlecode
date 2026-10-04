# Lane: mirror-hunt fix (B1) — abyss_v143hunt

Re-tasked from Devin Bot: v142's B1 mirror-hunt aimed at `rot(startCell)` — the
hunter's own start point-rotated, which lands on an ENEMY WORKER spawn, not the
enemy queen. Fix: aim at the mirror of OUR QUEEN's start, with per-map symmetry
(x-mirror vs point-rot) detected from seen features.

Base: `abyss_v143` (fetched from devin/v120; = v139 + a_portal10, no B1 machinery).
Ship: `workspace/abyss_v143hunt` = v143 + corrected mirror-hunt, params
`huntMirror=1, huntRound=25, huntLenMax=3, huntSquad=3, huntSpawnMax=30, wHuntMirror=2.0`.

## What was built

1. **Queen-start tracking** (`world.hpp`): `queenStartCell` = our queen's spawn
   cell. Set at INIT when `init.id == champId()` (the queen sees her own start);
   otherwise learned from the queen's beacon `parts` or `noteChamp(id==ourQueen)`
   — i.e. the queen's first observed/broadcast cell. Workers get it via the
   normal champ-propagation path (same place `queenCell` comes from).
   Caveat: it's the queen's first *observed* cell, which can drift 0-9 cells
   from her true spawn if she's already walked before her first beacon.

2. **Symmetry detection from seen features** (`policy.hpp::symClass()`): SYMMETRY
   is map-file metadata the bots never see at INIT, so it's inferred. Three
   hypotheses voted on seen edges + beds: "y"→x-mirror `(W-1-x, y)`,
   "x"→y-mirror `(x, H-1-y)`, "xy"→point-rot `(W-1-x, H-1-y)`. Each seen
   horizontal/vertical edge and each bed votes against hypotheses whose
   mirrored position doesn't show the matching feature. Edge mirror mapping
   follows mapgen `me()` exactly — rotation flips edge orientation (hE[c] under
   "x"/"xy" lands at edge-y `(h-y)%h`, not `rot(c)`'s top edge; vE[c] under
   "y"/"xy" lands at edge-x `(w-x)%w`). Returns 1="y", 0="xy", 2="x"; tie-break
   prefers y > xy > x. Self-corrects as features are seen — targets update
   every turn.

3. **Mirror-hunt assignment** (`assignAssassin`): worker-class dragon, round ≥
   `huntRound`, enemy queen alive, our `firstRound ≤ huntSpawnMax`, `L ≤
   huntLenMax`, not queen/grower/lead → target `mirrorCell(queenStartCell)`
   (falls back to own startCell if queen unseen). Exempt from
   `assassinMaxDist=16` proximity gate (mirror target is cross-map by design).
   Squad = `huntSquad=3` nearest; pull = `wHuntMirror` applied at the assassin
   slot (replacing `wAssassin` pull for hunters).

4. **Debug**: `mh=1 ac=<cell> qs=<queenStart> sym=<vote>` in the dragonLog for
   hunters (debug twin `abyss_v143hdbg`, BC_DEBUG build, not shipped).

## Verified mechanism (debug replays, dbg4 run)

| map | true SYMMETRY | vote | hunters' ac vs real enemy queen |
|-----|---------------|------|------------------------------|
| devil | y | y/x-mirror | **0-2 chebyshev** — ac lands on/near her start cell |
| islands | y | y/x-mirror | **1-3 cheb** (was 22-38 before the symClass fix) |
| queen_of_spades | xy | xy/rot | **1 cheb** |
| trophy | y | y/x-mirror | at/near queen start |

- Queen-start drift measured small on these maps (queen beacons early).
- symClass observed self-correcting mid-hunt on qos (early x votes flipped to
  rot as edges were seen); hunter retargets each turn.
- Hunters close real distance to the enemy queen: e.g. 45→31, 34→24, 15→8
  chebyshev before dying/expiring; kills not expected (hunters are L≤3 vs
  grown queen) — value is disruption + scouting, and kills when she's still
  small.
- All 22 ladder maps: `y` = devil/islands/schooltime/trophy (4), `xy` = the
  rest (18); no `x`-sym map exists in the set — the third vote is insurance
  for generated maps.

## Smoke results

| run | vs | maps × seeds | result |
|-----|----|--------------|--------|
| v143h_smoke (pre-symClass binary) | abyss_v143 | devil,islands,qos,trophy,weakhold ×2 | 60% (islands 4/4, weakhold 3/4, devil 2/4, qos 2/4, trophy 1/4) |
| v143h_smoke2 (**final binary**) | abyss_v143 | same | **50%** (islands 75%, devil/qos/weakhold 50%, trophy 25%; ALL-unlocked 50%) |

20-game sample → CI [30,70]; the two smokes bracket the truth as "roughly
neutral at n=20". Devil is spawn-side-locked (~97% pre-determined): its 2/4
is just the seat split, both A-seat games won incl. one where BOTH queens
died h2h (ours r51, theirs r83 — ours died first and we still converted).

### Queen-kill forensics (smoke2, games.jsonl)

Hunts land real kills — enemy queens dead by head-to-head inside/near the
hunt-arrival window: trophy r26, qos r48 & r76, devil r83 & r91 (and r133).
Aggregate: in-reach queen kill rate at dist 2 → 1.000 (2/2 opps) vs base
0/0 opps. Kill model works as designed.

Defensive cost is visible too: our queen dead (any)/game 0.80 vs 0.65.
In every loss our queen died h2h at r26-99 — while 3 workers are away
hunting, the home queen is thinner on escorts. Net at this sample: offense
pays ≈ what defense costs → 50%.

Trophy 1/4 anatomy: the win is the clean case (their queen dead r26 h2h →
snowball elim r120); the losses are our queen dying h2h at r26/47/49 before
the hunters mattered.

## v151 = v149 + hunt (integrator follow-up)

`workspace/abyss_v151` = abyss_v149 (v143 + C4 veto + champ-plant +
champFallbackRound 330) + the identical hunt patch, `huntMirror=1` ON.
Merge applied clean (offsets only — champ-plant is selfChamp_-only, C4 is
queen-only, hunters are L<=3 workers; no interaction).

**Gate v151 vs v149** — devil,queen_of_spades,trophy,weakhold,default,unsw
×2 seats = 24g:

| map | win% | notes |
|-----|------|-------|
| devil | 50% | seat-lock as usual |
| queen_of_spades | 50% | |
| unsw | 50% | both wins = big-champ bells c34/33, c41/27 |
| trophy | 25% | |
| weakhold | 25% | |
| default | 25% | |
| **ALL** | **37.5%** | ALL-unlocked 31.2% |

**The question — does consolidation change the exposure cost?**
**No — it raises the stakes of a dead queen.** Numbers:

| metric | hunt on v143 | hunt on v149 |
|--------|--------------|--------------|
| enemy-Q h2h kill r<100 (connection) | 5/20 | 6/24 |
| own-Q h2h dead r<100 | 9/20 | 10/24 |
| own-Q dead any round | 16/20 (80%) | 21/24 (87.5%) |
| longest@end (r500 gms) | 20.7 vs 22.7 | **21.1 vs 31.1** |
| alive@r499 | ~10.5 vs 10.8 | 17.3 vs 20.7 |
| win% | 50% | **37.5%** |

Kill/connection rates are unchanged — the hunt still lands ~25% early
h2h kills (trophy r26 again, devil r83/91, qos r48/76). What changed is the
penalty for the mutual-queen-trade the hunt provokes: v149's planted champ
consolidates whether or not the queen lives, but only for the *intact*
team — "queen kept after theirs died" 18% vs 50%, and v149-base
longest@end grew +8.4 over v143-base while v151's stayed flat (+0.4 over
v143hunt). On v143 mutual queen death left both sides scrambling; on v149
it leaves their 31-champ machine vs our hunt-depleted feed economy
(ppt 0.060 vs 0.075 — 3 hunters = 3 missing feeders).

**Verdict: honest negative on this base — do not promote.** Machinery is
correct and param-gated (`huntMirror=0` = v149 byte-equivalent path); it
needs either (a) huntSquad throttled post-huntRound so feeders recover, or
(b) hunts called off once our own queen is threatened (escort carve-out),
before it's net-positive against a consolidation bot.

## Files

- `workspace/abyss_v151/` — v149 + hunt machinery, huntMirror=1 (gate-negative; do not promote as-is).
- `workspace/abyss_v143hunt/` — shipped bot (v143 + hunt machinery).
- `world.hpp`: `queenStartCell` field + three set-sites (init/parts/noteChamp).
- `common.hpp`: hunt params block (L349-356).
- `policy.hpp`: `mirrorHunt_`, assignAssassin hunt branch + dist-cap exemption +
  squad/pull, `symClass()`, `mirrorCell()`, dbg fields.
- Diff vs v143 is additive; with `huntMirror=0` the code path is a no-op.

## Notes for integrator

- Hunt is OFF-safe: `huntMirror=1` ships in v143hunt; `huntMirror=0` compiles
  the assignment branch out at the `rep==NULL` path (still leaves dbg fields).
- The `assassinMaxDist` exemption is deliberate — mirror-hunt needs cross-map
  targets; regular rep-based assassin keeps its 16-cell gate.
- queenStartCell's beacon drift: acceptable now (ac within 0-3 cheb); if a map
  makes the queen walk far before her first beacon, hunters aim at her *walked*
  position — arguably still fine (that's where she actually is).
- Watch-items if shipped: (a) own-queen exposure while 3 hunters are away
  (0.80 vs 0.65 deaths/game — tighten huntSquad or add an escort carve-out if
  it reproduces at n>20); (b) trophy early-loss pattern; (c) huntRound=25 on
  corridor maps spends workers during the production war.
- Debug twin `abyss_v143hdbg` left on-box uncommitted (BC_DEBUG build; dragonLog
  shows `mh=1 ac= qs= sym=` for hunters).
