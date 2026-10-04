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
