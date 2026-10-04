# Lane: earlyecon — which post-v104 mechanism halves early splits on elim maps

Worker: session devin-381c0534c59845a9ac5e7187c20b5658, branch `devin/earlyecon`.
Base copy: `workspace/abyss_econ` = live `abyss_v119` (sub 16258, downloaded from
/api/v1/submissions/:id/download — remote branches only carry <= v113).

Mission numbers (v119 vs v104, devil+stripes+td, 24g): splits@r60 5.1 vs 9.6,
alive@r50 4.4 vs 6.8, pearls@r60 14.2 vs 25.1; v119 still wins via attrition
(wall deaths 16 vs 32).

## Mechanism map (exact v104->v119 delta on the early path)

| suspect | version | where | kill-switch | gate |
|---|---|---|---|---|
| wh4 trap-scan/queen pin | v113 | policy.hpp ~1121: queen deadEnd scan `seenOnly` + `unproven` veto (cells<=8 && frontier<=1); tiny/tree fire on the fog-shrunk region | `p.trapSeenOnly=0` reverts scan+veto to v104 exactly | NC<=700: devil, stripes, tower_defense ACTIVE; qos(875), default(1024), autarky(972) inert |
| open_ scout pull | v117 | policy.hpp: `open_=bud_&&r<48&&openMapOk()`; swarm gets openExplore .12, openDanger 1.0, openFog .3, openEatLen4, hunts queen+grower-only, queenKeep 3, enemyBan 1 | `p.openUntil=0` (openMinUnits=99 only kills the already-dead brood clause) | NC<=700 non-maze: stripes/td likely, devil is maze_(.238) -> off |
| scoped guards | v106+v112, scoped v116 | main.cpp: `guardOn = r<40 || id==champId()`; safeFirst redirects provably-fatal first step (seen-kelp/own body) | `guardOn=false` (v104 had no guard) | all maps r<40 |
| queen ram screen | v119 | policy.hpp ~1289: queen !lead_ k==0 dest inside seen enemy sprint reach -> +30*newL*mult (heard: +2) | `p.wQueenRam=0` | all maps |

Non-suspects checked and cleared: trySplit has no wh4 floor-cap (splits are
hasRoomyMove(parent)+hasRoomyMove(child) floods only); deadQ consolidation is
queen-dead only; trapped-fallback rank tweak is endgame; openEnemyDist=1
*relaxes* the split ban vs splitEnemyDist.

Pin mechanism for (a): pinned queen -> child hasRoomyMove fails inside her
pocket -> no buds -> splits collapse. For (b): scout pull moves workers off
adjacent-pearl eating -> fewer pearls -> less length -> fewer splits.

## Bisect results (all vs abyss_v119, 6 maps x seeds 1-8 x both sides = 96g, jobs 2)

splits60 / eaten60 / alive50 = cand-side means (base-side in parens on the map rows
of the run); pairW = cand pair-wins. Controls qos/default/autarky were identical
c/b in every run (map gates confirmed: nothing fires above NC 700).

| cand | edit | devil spl/eat/alv | stripes | tower_def | pairW |
|---|---|---|---|---|---|
| ee_v104 (reference) | — | 23.4 / 62.9 / 13.0 | 4.2 / 8.6 / 3.8 | 1.6 / 3.2 / 2.0 | 57/96 (59.4%) |
| ee_notrap | trapSeenOnly=0 | 22.8 / 57.9 / 12.3 | 4.6 / 9.4 / 3.6 | 1.6 / 3.4 / 2.3 | 51/96 (53.1%) |
| ee_noopen | openUntil=0 | 20.5 / 51.9 / 10.8 | 5.0 / 8.2 / 3.1 | 1.2 / 3.5 / 2.4 | 50/96 (52.1%) |
| ee_noguard | guardOn=false | = v119 mirrors | = | = | 48/96 (50.0%) |
| ee_noram | wQueenRam=0 | = v119 mirrors | = | = | 49/96 (51.0%) |
| v119 baseline | — | ~18.7 / 45 / 9-10 | ~4.5 | ~1.2 | — |

**Verdict: hypothesis (a) — wh4's fog-walled trap-scan is the pin.** notrap alone
restores ~v104 splits on devil/stripes/td (hypothesis (c) floor-cap refuted by
reading: no such cap exists). open_ contributes modestly on devil only (its
scout pull eats some pearls; stripes/td deltas are noise-level). Guards and the
ram screen are dead code on this axis — bit-mirrors.

Mechanism: under fog walls the seenOnly BFS region always reads tiny/closed ->
tiny (cells<=newL+2) and tree (exhausted, no cycle) vetoes fire on ordinary open
ground, the queen is refused entry to bud-length rooms, and splits halve. The
same vetoes on weakhold's cul-de-sac pockets are what saves her there — so a
straight revert reopens the weakhold deaths wh4 fixed.

## Fix (workspace/abyss_econ, on v119)

Dual-scan + weakhold-dims gate in the queen deadEnd block (policy.hpp ~1128):

- `wh_ = b.W==40 && b.H==15` (weakhold's cul-de-sac beds): full wh4 fog scan —
  bit-identical to v119, verified mirror 16g (metrics equal, qNonRam 0.00/0.00).
- other NC<=700 maps: optimistic scan (v104) for tiny/tree/loopRoom + a second
  seenOnly scan feeding ONLY `unproven` (mouth signature: cells<=8, frontier<=1)
  — keeps partial trap awareness where it doesn't pin.
- NC>700: unchanged v119 code path.

First iteration kept unproven everywhere and reopened weakhold queen deaths
(1.00/game vs v119's 0.07) — unproven alone doesn't reproduce wh4's save there
(the pocket vetoes that fire are tiny/tree on the shrunk scan), hence the dims
gate.

**ee_fix (abyss_econ vs v119, 96g): 52/96 = 54.2%** — devil spl 22.9/16.9 eat
58.1/42.6 alv 12.4/9.2; stripes 4.1/3.6, 9.6/6.8; td 1.6/1.2; controls+weakhold
bit-mirrors (ee_fix2_wh 16g: qNonRam 0.00/0.00). Devil qNonRam 0.56 vs 0.25 =
v104-level queen exposure (the fog scan also saved her on devil) — pair still
wins; that's the accepted trade.

**ee_fix120 (abyss_econ120 = same patch on v120, vs v120, 112g incl weakhold):
61/112 = 54.5%** — devil 11/16 (spl 25.2/16.7 eat 60.1/40.1 alv 13.1/8.9, tl50
33.2/23.5 eat100 134/110), stripes 12/16 (4.3/3.8, 10.2/6.6), td 7/16, controls
+ weakhold all bit-mirrors. The fix is confirmed forward-portable to live.

## 5c job/role allocator (workspace/abyss_jobs, on v120)

v120 = origin/devin/v120's workspace/abyss_v120 (v119 + splitEnemyDist 2->1).
Port of explore lane's abyss_x_sticky (70% vs v113) per coordinator review:
'x' assassin hold dropped (fresh assignAssassin re-forms per report; 14-round
ghost-chases were the bleed), feedMaxLen enforced on held feeders (L_ > cap
releases the hold), swarmRank quota kept on re-added hunts, no debug code.
NEW: 'g' forage claim — chosen move's argmax target cell becomes a sticky
commute (wStickyForage pull for stickyForageTtl); released when a teammate's
proximity claim wins (friendDist_) or the bed is seen-and-spent. The "shared
pearl-claim map" is the existing friendDist_ proximity claims + the beacon
picture; the claim layer adds commitment so knife-edge argmax can't flap.

S0 evidence gate: pearls + total len @25/50/100/200 (top teams 118 tl@r200 vs
our 66). Metrics added to tooling/replay_metrics.py (n/tl/eat checkpoints);
ee_table.py prints them.

**jobs_s0 (abyss_jobs vs v120, 96g): 46/96 = 47.9% — S0 FAIL.** 'g' claims
help where the game is a long economy (devil spl 21.9/18.5 eat 52.5/46.5
tl200 71.7/50.7; autarky tl50 29.1/25.2; qos eat200 123/88) but the 0.8-strength
commute pull drags workers past fresher food on tight maps (stripes spl 3.5/4.5
tl200 11.0/18.1; td tl200 13.0/24.9; default eat60 18.1/20.2).

**abyss_jobs2**: 'g' claims gated to r<60 (claims are an opening tool; late
commutes were the overstay) + wStickyForage 0.3 (tie-break strength — loses to
any real new value).

**jobs2_s0: 50/96 = 52.1%** — devil spl 19.9/19.3 eat 50.7/46.9 tl50 26.0/24.6;
stripes still 3.5/4.5; default/autarky splits dip. Claims at tie-break strength
are near-neutral: the wins shrink with the wins' mechanism.

**abyss_jobs3**: claims OFF entirely (`forageClaims=0`), holds only — isolates
the sticky layer.

**jobs3_s0: 42/96 = 43.8% — holds alone lose.** 'h' is the only hold that can
fire pre-120 ('e' gated midGame r>=120, 'f' ~r330): extended hunts during the
forage window starve econ on every elim map (devil spl 17.6/20.4, stripes
3.5/4.5, default 8.8/10.5, tl200 down across the board).

**abyss_jobs4** = jobs2 + all holds gated r>=60 (partition: claims own the
opening, holds own the midgame).

**jobs4_s0: 48/96 = 50.0%** — devil +1.3 spl, default +0.6 (partition works
there) but stripes still 3.5/4.5 identically in EVERY variant.

Deterministic check on stripes-s1 replays: jobs4 is bit-identical to v120 until
r193, so the stripes regression can't come from holds (gated r>=60) — first
divergences per seed: s2 r16, s3 r38, s5 r47 = claims firing pre-60.

**abyss_jobs5** = jobs4 + claimMinDist 6 (only far targets worth commuting;
stripes is 24x12 so most claims should never form).

**jobs5_s0: mid-run** — stripes s2 still diverges at r16 (a far target on
stripes IS >=6 away) so distance-gating alone doesn't close it.

**abyss_jobs6** = jobs5 + commitSticky disabled entirely (claims-only
ablation): attributes the residual stripes dip to claims vs holds cleanly.

**abyss_jobs7** = jobs5 + claim margin gate: commit 'g' only when top1-top2
target margin < claimMargin*gp(dist) (0.2) — the claim exists to stop knife-edge
argmax flapping, so it only forms where the flap actually is. Clear-order
targets (stripes' local beds) never claim. Runs: results/jobs6_s0, jobs7_s0.

Allocator read so far: sticky HOLDS are the net drag on elim maps (jobs3
43.8%, jobs4 50.0% with them pushed past r60); CLAIMS are near-neutral at
tie-break strength and are the only remaining lever for S0's tl@r200 gap
(top teams 118 vs our 66). If jobs6/7 don't move tl25-100 on devil/autarky
without losing stripes/td, the honest report is: forage claims don't move the
econ needle — the marginal-choice binding is too weak an instrument for a
66->118 gap, which likely needs structural econ changes (bud cadence/bed
coverage), not assignment stickiness.

Fixtures: results/ee_<variant>/{games.jsonl,replays/,ee_<variant>.log},
results/jobs_s0/ results/jobs{2..7}_s0/
