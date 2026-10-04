# Lane: 5b queen-safety module (escort + ram-screen)

Mission (from integrator): "escort role <=3 tiles + 1-2 ply lookahead vs sprint
rams — killer is lone len2-3 ram, no ally within 3 tiles, 76%". Corridor
doctrine: queen deaths are seat/map-locked; the escort's job is keeping her
EATING (she wins length races) + intercepting lone rams, not bodyguarding.
Gate EVERYTHING behind computed map flags; hoist per-node checks into
per-decide flags (judge clock is virtual — added CPU clips search depth).

Candidate: `workspace/abyss_qsafe` = v135 (pocket port, NC<=700 gate) + module.
Branch: devin/queen.

## What the module is (3 parts)

1. **Adjacency ram screen** (carried over from devin/pocket, commit 14333a1):
   head-to-head kills land *beside* her head and `e.dist` over `ownBlk` reads
   rams along her body line as INF. Fix: min-dist over the destination's 4
   neighbors, `qRamAdj=1`. Gated `qAdj_ = qRamAdj>0 && W==40 && H==15`
   (weakhold only — ungated cost stripes+arena pairs, see pocket.md).
2. **Threat-triggered escort**: idle workers (not assassin, `hunts_.empty()`,
   midGame, no existing escort target) converge on the queen's cell ONLY while
   an enemy is within `qEscortThreat=8` cheb of her seen cell (FriendField
   champId) or freshest `role==2` heard beacon within `heardFresh`. Distance
   cap `qEscortDist=14` BFS, `swarmRank < escortCount` so at most escortCount
   join. Standing escort rejected earlier — this bounds the econ cost to the
   rounds that matter; workers that can SEE the ram hunt it instead (hunts_
   non-empty), so the escort covers workers who only heard the threat.
3. Per-decide flags only: `queenCell_`/`qThreat_`/`qAdj_` computed once in
   buildSquadTargets; the hot scoring loop only reads `escortOf_` as before.

## S0-S1 results (paired seeds, both seats)

**Mission map — weakhold vs abyss_combat (same 4 seeds):**
- v135 baseline (qsbase): 50.0% (4/8), pairs 1W/2S/**1L**; queen died 6/8.
- abyss_qsafe (qsc1): **62.5% (5/8), pairs 1W/3S/0L**; queen died 5/8.
- Mechanism numbers moved: queen-dead/game 0.750 -> 0.625, non-ram queen
  deaths 0.375 -> 0.250, "queen kept after theirs died" 2/7 -> 3/7.
- The wins are queen-survival games: qsafe queen alive at r499 in 3 games
  (s1-B, s2-A, s3-B) where combat's queen died r210/233/—. On weakhold the
  round-limit score is a queen-length race: s1-B won 2-alive-vs-18 purely on
  queen survival.

**Regression set vs v135 (identical code minus module):**
- weakhold+dilemma (qs1): 0W/8S/0L — zero pair losses, zero new r0-5 queen
  deaths (earliest = dilemma r13 h2h, seat-locked, identical vs v135).
- stripes+arena (qs2): 0W/8S/0L — metrics identical to 3 decimals (3.812 vs
  3.812 deaths/game); module is inert off-weakhold. On blitz maps
  `hunts_.empty()` almost never holds near a pressured queen, so the escort
  cannot even form — the trigger is naturally tight.

## Honest attribution caveat

The +1 win and queen-survival deltas are the module AS A WHOLE vs v135. I did
not ablate escort-vs-screen on this base (pvc4/pvc6 on the pocket branch =
4/8 with the screen alone; qsafe = 5/8 — consistent with the escort adding
one more survival, but n=4 seeds, could be noise). The escort provably costs
nothing where it can't help (qs2 identical) and the pair-set is clean.

## Verdict: SHIP abyss_qsafe for integration

- weakhold vs combat: 4/8 -> 5/8, one fewer pair loss than v135.
- 16/16 regression pairs held vs v135 across 4 maps.
- No new r0-5 queen deaths (S1 kill criterion).

Not done / next: escort attribution ablation (qRamAdj-only on v135) if the
port wants to isolate; "keep her eating" refinement (queen-bed proximity pull)
if escort alone proves thin on ladder; S2 ladder challenges vs
FtM/Vibing/SSS/Sponge on starvation maps — ASK integrator first, none run.

## Files

- `results/qs1/` qsafe vs v135 weakhold+dilemma (replays)
- `results/qs2/` qsafe vs v135 stripes+arena
- `results/qsc1/` qsafe vs combat weakhold (replays)
- `results/qsbase/` v135 vs combat weakhold baseline
- prior forensics + rejected variants: `devin/lanes/pocket.md` on devin/pocket

---

# Steering-3/4 iteration (v2)

Targets (integrator): prevent the qOS r36 mirror-h2h signature WITHOUT vetoing
the queen; escort >=1 ally within 3 tiles; sprint reach `freeSteps+len-1`;
B1 hunt = 2-3 expendable len2-3 toward the enemy queen's mirror after r25
(baseline .33 kills/game r100-250); leash ~8 tiles of start pre-r100 on elim
maps (queen dies median 14 out); don't park adjacent (v138 reserves exits).

## What v2 adds on top of the shipped v1 module

4. **Queen kill-veto tier** (`qVetoReach`, `wQueenVeto=500`): at k==0 a dest
   inside any *seen* enemy's this-turn reach (`freeSteps+len-1`) scores
   `wQueenVeto*newL*mult - dd` — near-veto that still prefers distance. Soft
   `wQueenRam` pricing keeps covering the wider near-miss ring; heard enemies
   stay soft. Ungated — it's an engine-rule correctness check, not a map flag.
5. **`qEnemyLenMin=3` len floor in the queen screen** (the bug that made the
   naive veto useless): `Seen.visible` counts VISIBLE SEGMENTS — a len-3 ram
   glimpsed head-only at the vision edge reads 1 -> reach 1 -> nothing in its
   2-step kill zone is flagged (this is exactly how the qOS r32 kill walked
   in: e2v1 at the fatal decision). Real dragons can't be len-1
   (MIN_DRAGON_LENGTH=2), so visible==1 always means tail-hidden: floor at the
   len2-3 killer profile. Also applied to the `lead_` screen's len-1 formula.
6. **B1 mirror-hunt** (`huntMirror`, r>=25): when no fresh role-1 queen
   sighting exists, expendable opening-born workers (len<=huntLenMax=3,
   firstRound<=30) rank by `swarmRank < huntSquad=3` and set
   `assassin_`/`assassinCell_` to the xy-mirror of `w_.startCell` (new World
   field = first observed head = spawn region for opening-born). Reuses the
   assassin lane end-to-end: mission-keeping, enemy-queen trade logic
   (`assassin_ || L+queenTradeSlack >= len`), sighting handoff (a real
   role-1 rep replaces the guess automatically). Fog pull via
   `wHuntMirror=2.0 * fp(1.3*manh)` (feedFar pattern) — sighting pulls stay
   BFS-only. `theirQueenDead()` stops the hunt.
7. **Pre-r100 leash** (`wQueenLeash=0.5`, `leashDist=8`, `leashUntil=100`,
   NC<=2000): soft overshoot penalty per cheb tile past 8 from `startCell`.
   Torus-cheb makes her "far" cells on wrap maps read ~7 anyway — won't fight
   the qOS/Trophy portal scripts; binds her hiding-phase wander on elim maps.

## Verified mechanism (debug replays)

- qOS s2 cand-B r32 kill (the steering repro): pre-fix she steps S into a
  len-3 enemy's sprint cell (both die h2h); with the floor+veto S scores
  -16197 vs W 0 and she escapes THROUGH THE WRAP, surviving to r111 (fog kill
  — enemy never seen, `ne=0`, no module can price an unseen ram).
- v135-side queen still dies r32 in the mirror game — seat/map-locked as
  expected; the fix saves only the patched side.

## v2 A/B (same 4 seeds both seats)

**vs v135 regression (qs6, ship build):**
- queen_of_spades 2W/1S/1L — pair-wins s1+s4, split s3, pair-loss s2 (the one
  loss: B-seat weakness, queen survives r32->r111 but team still loses;
  present identically in the v1 module and the veto-only build — map geometry)
- weakhold 0W/4S/0L, dilemma 0W/4S/0L — clean parity
- queen dead/game 0.875 vs 1.000; "queen kept after theirs died" 3/12 vs 0/12
- zero r0-5 queen deaths in the 24 replayed games (S1 kill criterion)

**vs v135 stripes+arena (qs7):** 2W/6S/0L — clean, plus 2 pair-wins
(mirror-hunt converts on blitz maps).

**vs abyss_combat weakhold (qsc3):** 4/8, pairs 0W/4S/0L — v1's 5/8 was one
flip inside the same noise band (n=4; across builds weakhold lands 4-5/8);
queen-dead 0.875 vs combat 1.000, "queen kept after theirs died" 1/7 vs 0/1.

**Rejections (honest A/B):**
- `wQueenLeash` (steering-4 leash) — qs8: qOS -> 0W/2S/2L, stripes gains a
  pair loss. Reverted to 0.0 (same inert-param convention as wQueenFlee).
- `huntMirror` ablation (qnh1, hunt off): identical 4/8 vs combat weakhold —
  hunt is not the weakhold cost and wins pairs elsewhere; kept ON all maps.

## Verdict v2: SHIP abyss_qsafe

- The qOS r32 mirror-h2h is mechanically prevented (verified in replay).
- Pair-set vs v135: 4W/15S/1L (20 pairs / 40 games, 5 maps) — the only loss
  is the pre-existing qOS-s2 geometry loss, not introduced by v2.
- No new r0-5 queen deaths; queen survives measurably better (0.875 vs 1.000
  dead/game; 3x the kept-alive rate after the enemy queen dies).

## v2 notes / not done

- qOS s2 pair-LOSS persisted across v1/v2/v2+floor — flag for integrator.
- Fog rams (killer never in anyone's vision) are out of scope for pricing —
  escort sensor coverage is the only counter; v138 exit-reservation noted.
- Escort ring is 3 all-around, not front-arc; killers flank side 65% — an
  arc-aware escort target is the next refinement if the data wants it.
- Champion-channelling (feeders die AT the champion head) is a different lane.
- S2 ladder challenges: ASK integrator first — none run.
