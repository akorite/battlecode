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

**jobs5_s0: 48/96 = 50.0%** — stripes s2 still diverges at r16 (a far target
on stripes IS >=6 away) so distance-gating alone doesn't close it.

**abyss_jobs6** = jobs5 + commitSticky disabled entirely (claims-only
ablation). **jobs6_s0: 50/96 = 52.1%** — qos 12/16, splits/eaten flat-ish,
stripes still 3.5/4.5.

**abyss_jobs7** = jobs5 + claim margin gate (commit only when top1-top2 margin
< 0.2*gp): **jobs7_s0: 39/93 = 41.9%** — inverted intent: on dense-bed maps
EVERYTHING is knife-edge so the gate claims more, not less. Rejected.

**abyss_jobs8** = jobs6 + claimMinTiles 300 (claims only where commutes are
real; stripes 288 out): **jobs8_s0: 50/96 = 52.1%** — stripes STILL 3.5/4.5
with claims provably unable to fire. That broke the "claims cause stripes"
theory.

Root cause of the stripes mystery (deterministic replay + debug-build proof):
**the judge clock is virtual — 1ns per CPU point — and the search is
iterative-deepening bounded by BC_TURN_BUDGET=0.075 (75M points).** Turns
saturate (ms=75 in every dragonLog), so the last depth level always ends
mid-way; ANY added instruction deterministically flips whether that level
completes -> the pick changes. Debug proof on stripes-s2 r16, identical
world: v120 reached depth=6 (move W); jobs8d — every feature logically inert
— reached depth=5 (move S). jobs9 (forageClaimCell hoisted once-per-decide)
and jobs10 (all per-node claim work gated on a canClaim_ flag -> ~0 added
instrs on stripes) STILL diverge at identical events (s2 r16/636, s3 r38,
s1 r193): the boundary sits within ~1-2 compares of the deadline. On
CPU-saturated maps, added code cannot be behavior-inert — there is no
measurement floor below which a variant mirrors.

So per-map attribution: stripes (and likely td/default partial dips) measure
"added code costs depth-completion" — a tax every variant pays — NOT a claim
or hold mechanism. Mechanism attribution holds on the non-saturated reads:
holds lose broadly (43.8% jobs3 — depth-clip noise can't explain -6pts
uniformly across maps+phases); claims mildly positive (52.1% three ways).

**jobs9_s0: 50/96 = 52.1%** (identical to jobs6/jobs8 — hoisting moved where
the instructions live, not the count). devil tl200 95.6/25.2, qos tl100
18.1/14.1 — some econ-metric movement but splits/eaten flat.

**abyss_jobs10** = canClaim_-gated loops (zero added instrs when claims
can't exist). **jobs10_s0: 46/96 = 47.9%** — devil 17.1/21.1; stripes still
3.5/4.5 despite ~0 added instrs on it. The claims-family spread 47.9-52.1%
across 4 configs IS the overhead-noise band; no config separates signal
from the depth-clip tax.

### S0 verdict (96g set, vs v120)

NOT PASSED as specified. Decomposed:
- Sticky job HOLDS (h/e/f): net loss on elim maps — 43.8% alone, ~-6pts
  everywhere; 'h' hunts extended through the forage window is the main
  bleed. The explore lane's 70%-vs-v113 result does not transfer to v120
  on this set.
- Forage CLAIMS ('g'): 47.9-52.1% across 4 configs — the spread IS the
  noise band (the configs differ only in where the added instructions
  live). qos 12/16 and devil tl200 highs hint positive but the same data
  shows devil splits down in jobs10; nothing survives a strict read.
- The S0 target (66 -> ~118 tl@r200) is not movable by assignment
  stickiness alone: no variant moved splits60/eaten60 on the elim set.
  The gap is structural (bud cadence / bed coverage / search depth), not
  per-dragon-assignment.

Recommendation: ship the econ fix (abyss_econ120, +4.5pts verified twice);
park the allocator at 'g'-claims-only-if-cheap (jobs6/9 config) — any
further investment should go to making the feature cost ~0 instructions
(register-level, outside the deadline-bound search) before more mechanism
tuning, since on saturated maps the tax, not the mechanism, dominates the
measurement.

Fixtures: results/ee_<variant>/{games.jsonl,replays/,ee_<variant>.log},
results/jobs_s0/ results/jobs{2..7}_s0/

## Birth-stall diagnosis (v104-level econ vs current; mission 3)

Corpora (96 side-games each, 3 elim maps × 8 seeds × both sides,
--keep-replays): diag_v104 = abyss_v104 vs abyss_v120;
diag_v104e = abyss_v104 vs abyss_econ120 (the shipped fix). Analyzer:
devin/lanes/birthdiag.py — per-side birth timelines split by queen-parent
(min initial id) vs worker-parent, matched ±15r.

Splits≤60 totals (per-16-side-games):

| map | v104 | v120 | v104 | econ120 |
|-----|------|------|------|---------|
| devil | 373 | 280 | 372 | 261 |
| stripes | 38 | 22 | 38 | 35 |
| tower_defense | 8 | 7 | 8 | 8 |

Residual after ee_fix120 (diag_v104e):
- devil: queen-parented splits≤60 56 vs 36; econ120 queen dies r52 vs
  v104's r68 (15/16 vs 16/16 deaths — devil kills every queen, the
  timing is the diff = the accepted exposure trade).
- stripes: gap closed early (35 vs 38; queen 22 vs 24) and econ120
  out-splits late (297 vs 173 total).
- td: even.

Missing-birth decomposition (v104 births with no counterpart ±15r):
122 vs v120, of which worker-parented 103 — the collapse is
cascade-dominated, not queen-dominated (queen-missings 19, 18 on stripes
= the pin, already fixed).

### One line of cause

The residual stall is INTAKE-side, not cadence or coverage or depth-clip:
on devil, econ120 eats 25% less by r25 (5.4 vs 7.2) while unit count is
still even (n25 6.7 vs 7.2) — fewer pearls per dragon, not fewer dragons —
which compounds to n50 -31% (9.0 vs 13.1) and swarm wipe by r200
(n200 0.9 vs 18.1). The veto still refusing mouth cells v104 flooded —
`unproven` — is the leading mechanism suspect (it remains active on
non-weakhold maps in the shipped fix). Queen-death-timing is second-order.

### Experiment results: abyss_unprov / abyss_noram / abyss_noopen

Attribution (devil queen vs worker eats r<=30, head-cell on removed
pearls): v104 queen 73 vs econ120 37 across 16 side-games; workers
133 vs 148 (~even). The intake deficit is THE QUEEN'S. stripes queen
50 vs 44; td even.

- unprov_d (unproven veto off on non-wh): intake bit-equal
  (eat25 5.9/5.9 devil, 2.6/2.6 stripes, 1.5/1.5 td); only qNonRam
  +0.06-0.19. REFUTED as intake cause — veto rarely fires on these maps.
  Queen pick at the divergent turn identical to econ120's.
- noram_d (wQueenRam/wQueenRamHeard = 0): near-mirror — spl60/eat
  identical, wins 50%, qNR 0.44 vs 0.38 devil. REFUTED — screen rarely
  binds. Queen pick identical again.
- Replay trace (devil s1-8, mirrored pairs): the first same-side
  divergence is always the new worker at r1-r4 (id7/8, move N vs E) —
  systematic, direction-consistent. Queen path divergence r8-15 is
  downstream. v104 queen emits multi-step ['S','S'] moves; econ120 emits
  single steps/splits — she covers half the ground.
- open_ is LIVE on all three elim maps: openMapOk() = NC<=700 &&
  !(maze&&big) → true on devil/stripes/td; openMinUnits=99 only kills
  the fallback clause. open_ is post-v104 (v104's Params lack openUntil)
  and rewrites the whole early swarm: openExplore/openFog for workers,
  openDanger 1.0 vs budMult 1.8, openEnemyDist 1, openQueenKeep 3.
  The r1 id7 divergence (v104 W vs econ S, every seed) is openExplore/
  openFog reshaping the worker's first pick.
- lean_ NEVER fires (0/10k turns, debug builds); twoStep params identical.

noopen_d (econ120 + openUntil=0) verification: does queen eat25/splits60
recover toward v104.


### Result: `open_` is the residual stall — openUntil=0 recovers v104 econ

noopen_d (abyss_noopen = econ120 + openUntil=0, vs abyss_econ120, 48g):

| map | metric | econ120 | noopen | v104 ref |
|-----|--------|---------|--------|----------|
| devil | eat50 | 26.6 | 42.9 | 39.6 |
| devil | n50 | 8.8 | 13.9 | 13.1 |
| devil | spl60 | 15.6 | 26.6 | 23.3 |
| devil | n200 | 5.9 | 12.9 | 18.1 |
| devil | wins | .38 | .62 | — |
| stripes | spl60 | 2.1 | 2.1 | 2.4 |
| td | spl60 | 0.5 | 0.5 | 0.5 |

weakhold 16g mirror: w .50/.50, qNR 0.00/0.00, deaths flat, eat ~equal.
qos/default/autarky: openMapOk NC<=700 → open_ never fires there;
unaffected by construction.

**Cause line**: the residual pre-r200 birth stall on elim maps is the
post-v104 forage-opening (`open_`, live wherever NC<=700 && !maze — i.e.
devil/stripes/td/weakhold): under it the swarm's first picks go scouting
(openExplore/openFog for workers; divergence seed = new worker's r1
pick, every seed) and the queen's lane-foraging collapses (devil queen
eats<=30: 37 vs v104's 73; her multi-step ['S','S'] lane moves vanish) —
a mechanism trading early intake for map coverage, not a cadence veto,
coverage veto, or depth-clip. The cascade is worker-parented (103/122
missing births) atop the queen's halved intake (36 vs 56 q-splits<=60).

**Fix**: `p.openUntil = 0` — one line (abyss_noopen ≡ abyss_econ121,
ship candidate). Verified: devil spl60 +71%, eat50 +61%, n200 +118%,
wins 62%; stripes/td/weakhold mirrors; pair-set maps unaffected by
gate. Cost accepted: devil qNR 0.44 vs 0.25 (foraging-queen exposure,
same trade ee_fix shipped).

## Steering-3: action-A — dual-scan vs F2 veto-hole bisect (in flight)

Coordinator's question: on ≤2000-tile maps v134 thins tl@r100 vs v120 (30.3
vs 34.8); vs 1234 our tl@r100 is 42 vs 57. Is the dual-scan or the F2
veto-hole slowing r25-100?

**Discovery (git forensics): the whole v122 correctness pack never shipped.**
F2 = dead-end veto `c.score = c.stepTerm` (v122/v123 only). The v129 rebuild
off v120 dropped it — v129, v133, v134, v135 (LIVE) all lack it, along with
F3 (`!queen_` viaReverse), reachOf(-1), theirQueenDead expiry, advanceBody
recompute. So "the F2 veto-hole" is literally a hole in live: a vetoed
queen move keeps score **0.0** — it OUTRANKS any negative-scoring legal
move (veto leaks: she enters traps the scan flagged) — and all-vetoed →
empty best → trapped fallback.

**Variants on v135 (live base):**
- `abyss_a_f2` = v135 + `c.score = c.stepTerm` (F2 restore)
- `abyss_a_nods` = v135 with dual-scan reverted (single seenOnly scan = v133
  semantics)
- `abyss_a_f2nods` = both
- `abyss_a_fpack` = v135 + full pack restore (F2+F3+reachOf+queenDead-expiry
  +advanceBody) — follow-up if F2 alone moves

**Prior evidence already weighs in (ee_fix120 vs v120, 112g):** dual-scan on
v120 base was growth-POSITIVE — tl100 22.5 vs 19.1 (+18%), devil 52.9 vs
40.2, stripes 18.2 vs 7.5; elims suffered 14 vs 24. So the r100 thinning in
the v134-vs-v120 comparison isn't the scan itself — it's the rest of the
v133 lineage (feed stack) or the F2 hole interacting.

**Ladder obs (24 elim-map replays vs 1234/meowest/WaterCandle, v134-era):**
bimodal — we OUT-grow the band in wins (vs 1234 n=16: tl25 9.1/8.9, tl50
16.9/11.4, tl100 32.7/10.9, eat100 49.8/17.1), but the pre-r200 elim losses
are driven by queen h2h RAM deaths <r50 — Prisoners Dilemma queen dies r12
in all 3 seat-B games (seat-locked knife-edge), Trophy r46/45/31/33 h2h,
Default r43 hitWall. Pocket-leak (hitWall/hitSelf in dead-ends) is NOT the
dominant ladder signature — rams are.

Gate runs (devil,dilemma,trophy,default,stripes,td,qos ×8s×2seats, jobs2):
a_f2_v135, a_nods_v135, a_f2nods_v135 — table below when they land.

### Bisect result (both runs complete, 112g each)

**a_f2 vs v135: PERFECT MIRROR — F2 is inert on the elim corpus.**
Every metric identical to the 10th on every map; per-game margins
seat-for-seat identical. The score-0 leak on vetoed moves never binds here.
The F2 hole cannot be the r25-100 thinner (it is still missing from live —
restoring it neither helps nor hurts elim maps; its original value was
queen-self-kill protection, unmeasured here).

**a_nods vs v135: dual-scan is strongly growth-POSITIVE — reverting it is
the catastrophe.** 43.8% pair (nods loses).

| map | tl100 nods/v135 | n100 | eat50 | note |
|-----|------|------|-------|------|
| devil | **37.2 / 54.1** | 14.4/21.4 | 27.1/40.8 | -31% — reverting starves the favored seat too |
| stripes | **8.0 / 19.2** | 3.1/7.7 | 3.1/6.7 | -58% |
| dilemma | 6.0/7.0 | 2.0/3.0 | 18.0/16.0 | strict veto delays q-death r13->r113, doesn't save (h2h) |
| trophy | 50.0/45.9 | 20.2/18.3 | 28.6/27.1 | nods slightly ahead here (+9%) |
| td | 11.2/11.5 | 3.9/4.2 | 2.4/2.6 | ~mirror |
| default/qos | mirror | mirror | mirror | so=false, scan never differs |
| ALL | 21.7/25.3 | 8.4/10.0 | 14.6/16.6 | -14% tl100 |

**Verdict: neither.** Dual-scan is the best growth mechanism we own on elim
maps (+14% tl100 overall, +45% devil, +140% stripes vs the strict veto);
the F2 hole is inert. The v134-vs-v120 thinning the coordinator measured
(30.3 vs 34.8 tl100) lives in the rest of the v133 lineage — midEnd450,
hideUntil320, feedRoundBrawl — NOT the scan. Recommend decomposing that
slice next (v133 vs v133-minus-feedstack on corridors).

### Structural finding: spawn-side lock on devil/stripes
Per (map,seed) one seat always reaches ~64-93 tl100 (devil) / ~20-34
(stripes) and the other stalls at ~5-26/~2-10 — IDENTICAL margins for both
bots in the a_f2 run (deterministic mirror). The stalled side's queen dies
~r28-90 h2h crossing for food → elimination <r200. This matches the ladder
signature (h2h rams <r50 in PD/dilemma r13 seat-lock): the pre-r200 elim
class is **queen-lane lethality on the starved lane**, not a foraging
deficit. No symmetric econ mechanism fixes the starved seat — the fixable
unit is queen survival there (5b escort / hide doctrine territory).

### Third suspect surfaced during the bisect: pocket stack on elim maps
While verifying what gates `pocketMap_`: deg-1 BED cells per map (bait cells
only count when they hold a bed): devil **24**, td **11**, stripes **11**,
weakhold 3, portals 8, trophy 4 (NC<=700 -> pocketMap_ live on all of them).
Dilemma has 0 -> pocket never fires (knife-edge queen lane untouched, as the
comment intends). On devil/stripes/td the worker k==0 deadEnd scan + baitLen
food-skip + starving pulls are ALL live — a real CPU+forage suspect that
post-dates v120 (came in v135's pocket work; NOT in v134, so it cannot
explain the coordinator's v134-vs-v120 30.3/34.8 number — that one reduces
to dual-scan+misc on corridors, both legs now exonerated/inert).
Launched `a_nopocket` (pocketMap_ forced false) vs v135 on the elim set.

### Bisect final (all 3 legs, 112g each vs v135): NEITHER suspect is the thinner
| leg | pairW | verdict |
|-----|-------|---------|
| a_f2 (F2 restore) | 50.0% | **bit-mirror — F2 inert on elim corpus** |
| a_nods (no dual-scan) | 43.8% | **dual-scan growth-POSITIVE** (devil -31% tl100, stripes -58% without it) |
| a_fpack (full pack) | 48.2% | net-negative (devil -28% tl100, trophy qd<50 worse) |
| a_nopocket (pocketMap_ off) | 50.0% | neutral — not the thinner either |

Structural: elim maps spawn-side-locked — per seed one seat hits ~64-93
tl100 devil, other stalls ~5-26 regardless of bot; stalled queen dies
~r28-90 h2h. Pre-r200 elim = queen-lane lethality on the starved seat,
not a foraging deficit.

### Steering-4: portal routing + don't-stall-short-of-bed
Winner data: 1.3-3.1 portal transits by r25 on QoS/Trophy/Default vs our
0.0-0.1 (first transit r33-45, usually queen). Root cause candidates in
our code: (a) unknown portal partner -> nb=-1 -> BFS never routes through;
(b) wPortalBlind penalizes crossings even when scouting cleared far side.
Fix direction (per steering): unseen portal = passable w/ symmetric-tile
partner; no blind penalty r<30; scout-first then workers route on belief.
Winner opening scripts + pearl benchmarks (r25/r50): Devil 12/54,
Trophy 10/44, Stripes 8/24, QoS 6/20, Default 6/18, PD 20/35, TD 1/4.
S0: own portal transits by r25 > 0 and pearls@r25 toward benchmarks.

### Steering-4 progress: portal routing
Baseline (v135 side, 16g/map): transits<=r25 default 1, qos 0, trophy 0,
stripes 24 (in-corridor pairs), first transits r30-49 — matches winner-gap
data (their 1.3-3.1 by r25 on qos/trophy/default).
Pearl benchmarks vs ours (eat25/eat50): qos 0.7/7.8 vs 6/20, trophy
5.9/25.8 vs 10/44, stripes 2.4/6.1 vs 8/24, default 8.2/15.2 vs 6/18
(ahead at r25, behind r50), dilemma 16.5/16.5 vs 20/35.

**a_portal** (v135 + unpaired-portal->point-rot landing guess in nb[] +
blindGrace=30 workers + scout-crossing blindQuiet drop pre-30, queen keeps
blind): transits<=r25 qos 13, trophy 6, default 20, dilemma 32, stripes 21 —
mechanism delivers early transits everywhere. But pair 41.2% overall:
qos **+81% (13/16)** tl100 23.0/15.7, trophy **+56% (9/16)** tl100 58.7/42.0;
dilemma **0/16** (workers desert the queen lane — transits 32<=r25),
default -37.5% (12 pairs = guess flood), stripes -31% (16 ends, transits
already native). qd<50: dilemma 0 vs 8 (portal crossing SAVES her lane but
starves the swarm), trophy 5 vs 5, qos 4 vs 4, default 2 vs 1.

Split exactly on unpaired-end count: qos 4 / trophy 2 win; dilemma 8 /
stripes 16 / default 24 lose (phantom-route flood).
**a_portal2** = a_portal + gate `portalGuess_`: unpairedEnds <= 4 AND
round < 50 (board flag set in observe(); dilemma/default/stripes revert to
scout-only behaviour, qos/trophy keep the guess). In flight.

### Pending: don't-stall-short-of-bed (devil/stripes — no portals)
v135 stalls 2-4 tiles short of centre bed (devil A-seat x<=16 r25 vs bed
x14-17; belief=0 for never-seen beds -> only generic explore pull).
Beds are dense on devil (156/512) so local greed stalls the east push.
Candidate: frontier-depth explore bonus or centre-ward opening bias.

### don't-stall diagnosis (devil s1 A-seat, v135 replay): NOT a forage-belief problem
Traced head paths: the queen pushed east 3,4 -> 17,4 by ~r35 and died
hitHeadToHead r37 at the centre bed. Later splits SPAWN at x13-19
(contested centre) and die r32-100 in waves (hitSelf/hitWall/
hitOtherBody/h2h). The 'stall' = survivors orbiting x9-12 while pushers
die at x14-17. Dragons reaching the rate-30 centre fountain die in the
centre fight — pushing harder increases deaths, not pearls.
Devil centre: 46 beds, only 5 deg-1 (bait-skip NOT the blocker); all 12
rate-30 beds are centre, all 16 rate-10 on stripes mostly centre.
=> the devil/stripes stall is the SAME queen-lane/combat class as the
   whole pre-r200 elim problem: whoever survives the centre fight eats the
   fountain. Fix axis = centre survivability (pocket discipline on hitSelf/
   hitWall, queen escort/screen for the h2h), NOT exploration pull.
   a_deep (deep-explore weight): bit-mirror — explore term never wins
   argmax vs belief, confirming weight-tuning can't fix this.

### a_portal6 — PASS (57.5%, 80g, gated portal package)
v135 + [unpaired-portal -> point-rot landing guess in nb[], blindGrace=30
workers (queen keeps wBlind/wBlindQuiet), scout-crossing blindQuiet drop
pre-30] — ALL behind `portalOpen_` gate: NC in (512,900] && !maze && <=2
distinct portal ids seen (sticky manyPortals_ latch). On qos/trophy the
package is live; dilemma(512)/stripes(288)/td(512)/default(1024)/devil(512)
are hard-excluded -> bit-mirror.
| map | pairW | tl100 c/b | transits<=r25 | eat50 |
|-----|-------|-----------|---------------|-------|
| qos | **13/16 (81%)** | 20.6/16.6 | 13 (was 0), first r14 | 14.1/7.5 +88% |
| trophy | **9/16 (56%)** | 60.3/44.1 | 6 (was 0), first r10 | 27.4/26.9 |
| dilemma | 8/16 | mirror | mirror | mirror |
| default | 8/16 | mirror | mirror | mirror |
| stripes | 8/16 | mirror | mirror | mirror |
| ALL | **46/80 57.5%** | 25.6/21.5 | elim<200 21 vs 26 | qd<50 28/28 |

Gate design history: a_portal (ungated) 41.2% — floods on many-portal maps;
a_portal2 (<=4 unpaired ENDS) broken — count was per-end not per-pid;
a_portal3 (<=2 pids sticky) opened pre-30 window on dilemma before 3rd pid
seen; a_portal4 (guess only) proved the guess itself starves dilemma.
Final gate is deterministic per map (NC from init, no leak window).
S0: transits<=r25 >0 delivered (qos 13, trophy 6); pearls@r25 toward
benchmark (qos 2.5 vs target 6 — doubled from 0.7, still short; transits
0.8/game vs winners 1.3-3.1).
Candidate for staging: workspace/abyss_a_portal6 (v135 + gated package).
Open work for this lane: devil/stripes centre-fight survivability (the real
'stall' mechanism — overlaps 5b escort/screen + hitSelf/hitWall discipline).

### a_portal7 — S0 scout mission, INERT (57.5%, identical to a_portal6)
Design: first worker (init.id == champId()+2, alternating initial ids) gets
lip target s0Portal=9.0 while s0scout_ && round<28 && portalOpen_.
Result: bit-equivalent metrics to a_portal6 — the mission NEVER fires.
Cause: on qos/trophy the nearest portal sits ~6 cells from spawn, outside
vision radius 3; no unpaired end is ever in portalEnds during the window.
Replay check (qos s1): id3 (=S0 for seat B) still crossed at r56 — saw the
(4,3) end ~r40, 16-round forage lag. Correct decode of EDGE index is
row*(W+1)+x (row even=hE top of tile(x,row/2), odd=vE left of tile
(x,(row-1)/2)): qos pairs vE(4,3)<->vE(9,33) = winner's far-bed line,
vE(16,1)<->vE(21,31); trophy hE(12,6)<->hE(12,22) = winner's (12,5) landing.

### a_portal8 — waypoint pre-sighting (in flight)
S0 mission v2: until ANY pid pairs — if an unpaired end is seen, lip target
(s0Portal=10); else mirror-waypoint target at pointRot(spawnCell)
(s0Far=7, >4 cheb away) — sends the scout to the far quadrant where portals
sit; window extended to s0Until=60 (covers first-sighting lag). Ends on
first pairing (size==2 in portalEnds).

### a_portal10 — S0 scout mission, LIVE + PASS (57.5%, 80g, mission verified)
Root cause of p7-p9 inertness found by BC_DEBUG logging through the replay
(abyss_p9dbg instrument): **Policy is a fresh per-turn object** (main.cpp
news it every round) — s0scout_ assigned at decide():~101 AFTER
buildTargets():82 was dead-on-arrival to the target builder on EVERY turn,
not just the first. s0b (flag as seen inside buildTargets) was 0 in all
~1000 logged decides while s0=1 at decide end. Whole block was dead code.

Two fixes in p10:
1. s0 identity computed BEFORE buildTargets (early-worker test
   !queen_&&!grower_&&!lead_ — assassin_ always false pre-squad).
2. t.cell==dest skip exemption via countdown==-2 sentinel — the crossing
   step's dest IS the guess landing (= rot(lip) target), so the pull died
   exactly at the crossing choice (the p9 hover). Also tested the
   zero-compare alternative (push rot of BOTH lips, sibling pull survives
   skip): qos collapsed 37.5% vs sentinel's 87.5% on identical seeds —
   reverted. Sentinel adds 1 compare per target-eval: default gained 1W
   (depth-clip flip, harmless direction).

Final gate (a_portal10b, 80g vs v135, both seats):
| map | pairW | tl100 c/b | transits<=r25 | eat50 | elim<200 | qd<50 |
|-----|-------|-----------|---------------|-------|----------|-------|
| qos | **12/16 (75%)** | 26.9/13.7 | **19 (was 0), first r12** | 16.3/8.2 +99% | 1/6 | 3/7 |
| trophy | **9/16 (56%)** | 45.7/57.7 | **6 (was 0), first r11** | 33.1/24.8 +34% | 7/8 | 3/7 |
| dilemma | 8/16 | mirror | mirror | mirror | mirror | mirror |
| stripes | 8/16 | mirror | mirror | mirror | mirror | mirror |
| default | 9/16 | ~mirror (+1W) | ~mirror | ~mirror | ~mirror | ~mirror |
| ALL | **46/80 57.5%** | | | | 22/30 | 25/33 |

vs a_portal6: same pair, better where it was designed to bite — qos tl100
26.9 vs p6's 20.6, transits 19 vs 13, first transit r12 vs r14; trophy
eat50 33.1 vs 27.4 (more intake) but tl100 45.7 vs 60.3 (scout survives
the centre fight less — same trade class as don't-stall). Same 57.5% pair
with the mechanism now PROVEN to fire (p6's transits came only from the
guess+blindGrace passive package; p10's scout actively routes).

S0 metric: transits<=r25 19 qos / 6 trophy (>0 both, benchmark-ward);
eat25 qos 3.2 vs winner benchmark 6 (was 0.7 pre-gate; moving, still short).
Transits 1.2/game qos — inside winners' 1.3-3.1 band now.
Candidate for staging: workspace/abyss_a_portal10 (supersedes a_portal6 —
same pair, verified mission, debug-channel proven).

### abyss_v143qs — qsafe port onto v143 (pocket lane): smoke 45%, mechanism fires, net-negative
Port (per steering): qVetoReach=1/wQueenVeto=500 lethal tier in BOTH
ram-screen loops, qEnemyLenMin=3 ev-floor (lead loop + queen loop),
qEscortThreat=8/qEscortDist=14 threat-escort, qAdj_=W40xH15 adjacency gate,
wQueenLeash=0 (ported inert), huntMirror machinery NOT ported.
base=abyss_v143 (=v139+p10+portalEnds-empty fix), 20g, 5-map smoke x2 seeds.
| map | pairW | tl100 c/b | splits60 | qNonRam c/b | qd |
|-----|-------|-----------|----------|-------------|-----|
| qos | 2/4 | 19.2/24.2 | 7.8/7.5 | 0/0 | 3h2h/4h2h |
| trophy | 2/4 | **26.7/64.3** | 11.8/16.5 | 0/1 | 3h2h/3h2h+1body |
| dilemma | 2/4 | 0/0 (r24 elims) | 8.0/8.0 | 0/0 | 2h2h/2h2h |
| default | 2/4 | 32.7/22.7 | 10.5/9.8 | 0/2 | 3h2h/1h2h+2body |
| stripes | **1/4** | 12.8/13.5 | 3.0/3.0 | 0/1 | 4h2h/3h2h+1wall |
| ALL | **9/20 (45%)** | 18.3/24.9 | 7.6/8.8 | **0/4** | qd<50 8/5 |

Mechanism verdicts:
- Evasion lever FIRES: queen non-ram deaths 0 vs 4 in 20g (the class the
  veto tier targets); queen-kept-after-theirs-died 45.5% vs 33.3%.
- Threat-escort is INERT on this set: abyss_v143qv (qEscortThreat=0) is
  bit-identical across all 20 games — qThreat escorts never slotted in
  (either never true when idle, or escortCount filled by grower escorts).
- The bleed is the ram-screen rewrite itself: trophy tl100 collapsed
  -58% (26.7 vs 64.3). Either ~10 extra compares in the hot danger loops
  on saturated maps (depth-clip tax) or the veto re-routes the queen off
  her forage lane — both plausible, not separated in a 2-seed smoke.
- splits60 -1.1, eat50 -3.1, alive50 -1.9 — early econ pays for evasion.

Lane read: qsafe's protection is real but the 20g smoke is net-negative
(-5pts). Not a ship at these params. If the integrator wants the lever,
the cheap isolations are: (a) veto+floors only (drop qAdj_ nb-min —
weakhold-dims only, pure tax elsewhere), (b) wQueenVeto scaled to ~wQueenRam
tier instead of 500x, (c) replicate on 4+ seeds — trophy tl100 swings hard
on single seeds (one 64-tl game dominates a 4-game mean).

### abyss_v143qk — qsafe isolation (a): veto/floor only — PARKED at 45%
v143 + ONLY qVetoReach=1/wQueenVeto=500 kill-tier (seen-enemy ram loop) +
qEnemyLenMin=3 ev-floor (lead + queen seen loops). No qAdj_, no escort
code, no leash — the whole auxiliary qsafe block absent.
Gate vs v143, same 20g smoke: **45% pair (9/20, 0W/9S/1L) — NOT PASSED**
(needed >=55% and nonRam<=1; nonRam leg passed 1 vs 3).
| map | pairW | tl100 c/b | splits60 | queen deaths c/b |
|-----|-------|-----------|----------|------------------|
| qos | 2/4 | 19.2/24.2 | 7.8/7.5 | 3h2h / 4h2h |
| trophy | 2/4 | 26.7/64.3 | 11.8/16.5 | 3h2h / 3h2h+1body |
| dilemma | 2/4 | 0/0 (r24) | 8.0/8.0 | 2h2h / 2h2h |
| default | 2/4 | 34.0/20.3 | 10.5/9.8 | 2h2h+1body / 1h2h+2body |
| stripes | 1/4 | 12.8/13.5 | 3.0/3.0 | 4h2h / 3h2h+1wall |
| ALL | 9/20 | 18.5/24.5 | 7.6/8.8 | nonRam 1/3, qd<50 8/5 |

Isolation verdict: the veto/floor piece alone reproduces the full qs
regression — identical pair count, identical trophy tl100 collapse
(26.7 vs 64.3), same stripes pair loss. qAdj_/escort/leash contributed
NOTHING to the bleed (proved by subtraction). The cost is the queen's
fear-priority reorder itself: with every ram-reach dest near-vetoed,
she detours off the forage lane and the swarm starves — surviving to
be rammed later anyway (h2h deaths 15 vs 13; queen kept 45% vs 33% —
she survives MORE but it doesn't convert).
default is the exception — tl100 34.0/20.3 (+67%): on the open map the
veto dodges real rams without forking her off-lane. The failure is
trophy/stripes-class: corridor maps where "safe" is a funnel.

qsafe parked per steering threshold. Awaiting the queen-evasion-vs-
front-arc design (killer-geometry escort: 96% mover-kills, side/front
arcs, 65% visible 2+ rounds out) — that escort needs measured arcs, not
this concentric-fear model.

## QUEEN FEED (v2#2 second half): abyss_v149qf — NOT PASSED (40% pair)

Mechanism (per spec): expendable len-2/3 workers adjacent (cheb<=1) to
the LIVE queen's head die in place mid-game so she eats the drops —
the elected-champ die-in-place path extended to [qFeedRound, feedAt).
Params: qFeedRound=200, qFeedDist=1, qFeedMaxLen=3, qFeedAge=8,
guarded by worker_ + feedMinUnits + !queenDead + fresh queenRound.
Verdict vs abyss_v149 (devin/v120 HEAD), 5-map x2-seed x2-seat smoke
(autarky/islands/unsw/default/stronghold, tag v149qf_smoke):

- pair: 8/20 = 40% (0W/8S/2L). autarky 1/4, stronghold 1/4, rest 2/4.
- Target metrics ALL moved backward:
    qlen@end     2.944 vs 4.333   (she gets SHORTER, not longer)
    qAlive@end   0.167 vs 0.278   (she dies MORE, not less)
    longest@end  33.5  vs 32.9    (~flat, +0.5)
- Mechanism fires: d_hitSelf up on 4/5 maps (autarky +3.3, default
  +1.2, islands +6.0, stronghold +24.3; unsw -5.6). tl200 bit-identical
  on every map — pre-200 behavior untouched, so the delta is the qfeed
  window itself.
- Per-map queenEnd c/b: autarky 0.0/0.5, default 2.2/0.0, islands
  0.0/0.0, stronghold 13.2/19.0, unsw 0.0/0.0 — nowhere net-positive.
- She still dies h2h: qDeadReason mostly hitHeadToHead both sides;
  qDeadRound mixed (autarky 299/284 later, islands 220/196 later,
  default 138/193 EARLIER).

Why it fails (read): mid-game the queen is ram-threatened, not
pearl-starved — she forages fine, so a corpse-drop next to her head
doesn't convert to length before an enemy head arrives. The sacrifice
just removes a forager near the colony core (and possibly a blocking
body she needed). The 2-3 pearls a len-2/3 drops can't buy back the
lost forage round-trips. stronghold's +24 hitSelf/game shows the die
fires heavily where workers crowd her — pure tax.

qfeed parked at qFeedRound=200 / len<=3 / cheb1. If revisited: the
spec's premise "every pearl on her compounds" needs her to LIVE —
maybe gate the die behind no-visible-enemy (she already has
wQueenRam-gated safety evaluation; a suicidal drop beside a threatened
queen is a donation to the rammer).

Files: workspace/abyss_v149/ (base ref), workspace/abyss_v149qf/,
results/v149qf_smoke/.

## QUEEN FEED v2 (lexicographic-scoring reframe): 4-variant series — feed NEGATIVE, screen ~neutral

Steering reframe (verified): r499 bells score lexicographically —
queen end-length, then longest, then team total. Spec: (a) keep her
ALIVE to 499, (b) drops adjacent to her head r200-feedStart,
(c) die-in-place extension. All runs: vs abyss_v149, same 5-map x2-seed
x2-seat smoke (autarky/islands/unsw/default/stronghold), jobs 2.

| variant | mechanism | pair | qlen@end | qAlive@end | longest@end |
|---|---|---|---|---|---|
| v149qf   | qfeed die-in-place r200+ cheb1 len<=3 | 40% (8/20) | 2.94/4.33 | .167/.278 | 33.5/32.9 |
| v149qs2  | screen hardens r200: wQueenRam x3 +1 ring | 50% (10/20)| 3.17/3.06 | .333/.278 | 31.1/33.2 |
| v149qfs2 | qs2 + qfeed gated no-enemy-reach       | 45% (9/20) | 2.94/4.22 | .167/.222 | 34.0/33.8 |
| v149qs3  | screen r150 x6 +2 ring                 | 45% (9/20) | —         | —         | —         |
| v149qs4  | qs2 + queen-adjacency wDanger x10      | 45% (9/20) | —         | —         | —         |

qs3/qs4 per-map queen detail: autarky qAlive 0.50 vs 0.25 BOTH variants
(qlen 3.0/0.8 and 1.2/0.8) — the ONLY survival gains in the series, and
they live on the single open map. default/islands/unsw: queen dies by
h2h/wall identically regardless (islands: fear converts her deaths to
hitWall x3 — same deaths, different mode). stronghold: 13.0/13.0 both
sides (protected either way).

Findings:
1. (b)+(c) feeding is UNIFORMLY negative — every feed variant cut
   qlen@end below base. Sacrifice cost > drop value: a len-2/3 worker
   is worth more foraging than the ~2-3 pearls she eats off the corpse,
   and the death cell can wall her. Safety-gating (no enemy reach of
   queenCell) doesn't rescue it — the tax is intrinsic.
2. (a) screens give a real but SMALL survival gain — qs2: qAlive@end
   +5.5pp at exactly 50% pair (neutral). Dose response: autarky qAlive
   0.50 vs 0.25 at both mult6+b2 and adjx10 — but islands pays for it
   (she flees into walls). Fear screens only work where escape
   geometry exists; on constrained maps they convert death mode, not
   death rate.
3. The actual kill vector confirmed: in-reach queen kill rate is
   100% at every distance — once an enemy head is adjacent she is
   dead. Adjacency was priced at wDanger=1.5/seg — qs4 raised it x10
   for her post-200 with no downside vs qs2 but no extra gain either.
4. CONCLUSION: queen-survival is escort/evasion-geometry bound
   (pocket's lane), not fear-screen bound and not feedable in
   self-play. Feeding the primary tiebreaker fails because in OUR
   self-play she rarely lives to eat — the (a) precondition is the
   real bottleneck and it belongs to the front-arc escort work.

Candidate if integrator wants the marginal piece: workspace/abyss_v149qs2
(neutral-pair, +5.5pp queen-alive, ~zero instruction cost — 4 hoisted
members + constants). Else parked: abyss_v149qf/qfs2/qs3/qs4 + results/
{v149qf,v149qs2,v149qfs2,v149qs3,v149qs4}_smoke.

## QUEEN FEED v3 (feeder-reach variant): abyss_v149qf2 — 30% pair, thread closed

Per steering-2 spec: feed queen as champion r200+ on open maps +
keep-her-near-start pre-r100. Full feeder-REACH unblocked this time:
feedAt=200 when NC>=600 (openFeed_), locateChamp window follows
(was floored r320), feedMargin waived for queen-champ (FtM feeds her
from len 2), nobody self-elects over her, queen relay opens r160,
plus spawn leash pull r<100 (wQueenLeash 0.6).

Verdict vs abyss_v149@devin/v120-HEAD (autarky/stronghold/default/unsw/
islands x2 x2 seats, tag v149qf2_smoke): **30% pair (6/20)** — 1W/4S/5L.
- qlen@end 2.13 vs 3.13, qAlive@end .133/.200, queen-dead .85/.75 —
  worse on every queen metric.
- autarky 3/4 (75%) — the ONLY map the feed ever helps, again.
- unsw 0/4, stronghold 1/4, islands 1/4, default 1/4 (s1 both seats
  team-eliminated r231/r383 — swarm starved while feeders walked).

Conclusion (3 strikes): die-in-place (40%), gated feed (45%), full
feeder-reach (30%) — feeding the queen is negative in EVERY form in
self-play. Workers are worth more foraging/fighting than as drops;
autarky is the only exception and the dose can't survive the other
four maps. Queen-feed thread CLOSED at mechanism level.

## TORUS-SEAM AUDIT: symmetric attrition — STANDING DOWN per spec

Verified the claim on 24 v149L-vs-v138 ladder replays (6 seam maps,
devin/lanes/seamdiag.py): h2h deaths classified by death-cell position.

h2h deaths AT edge cells (x=0/W-1 or y=0/H-1 — the strict seam sig):
| map | ours | theirs | notes |
|---|---|---|---|
| queen_of_spades | 12/57 | 10/57 | real class (~20% of h2h) |
| tower_defense | 11/34 | 7/34 | funnel chains, positional |
| stripes | 3/26 | 3/26 | small |
| weakhold | 2/28 | 1/28 | small |
| devil | 0/85 | 0/85 | edge cells are walls — no seam play |
| dilemma | 0/36 | 0/36 | same |
Strict wrap-adjacent kills (heads |dx|=W-1 or |dy|=H-1): only 4 total
in 237 h2h deaths — the kills happen AT the seam ring, not across the
wrap. All edge deaths are ~mutual pairs; the 28-vs-20 net is td/qos
funnel chains (multiple ours dying on one theirs), not a guard gap.

QUEEN seam exposure: zero strict wrap-deaths. Within ring-2 of the
edge: ours 8/15 of her h2h deaths, theirs 5/16 — slightly asymmetric
but n=31 queen h2h deaths total; driven by stripes/td positional
density, not the invisible-march mechanic (which produced 0 queen
deaths in the corpus). VERDICT: symmetric fair-attrition on the seam —
per spec, standing down on the queen-only seam guard. If revisited:
td is where edge kills concentrate asymmetrically (11 vs 7).

## v158 FRONT-LOAD FEEDERS — PASS 62.5% pair (15/24), first feed-variant pass

Mechanism (v3 late-game spec #4): feedBurst_ = nearest-ring front wave
at window open — worker within feedBurstDist=14 of champHead_, report
age <= champMemory, round - feedAt <= 20 → wFeed x3 pull. Everything
else reused (champOne election, champFeedDist=2 die-in-place, anchor).

Gate vs abyss_v149@devin/v120-HEAD, 6-map x2-seed x2-seat (unsw,
islands, stronghold, default, autarky, schooltime; tag v158_frontload,
replays kept):

- pair: **15/24 = 62.5% (3W/9S/0L)** — ZERO pair losses on any map.
  islands 100% (2W), stronghold 75% (1W/1S), rest 50%.
- Required metrics: qlen@end **3.41 vs 1.91 (+79%)**, longest@end
  **32.7 vs 28.6 (+14%)**, queen-dead/game 0.625 vs 0.625 (flat),
  alive@end 18.6 vs 16.5.
- Feed drops: the base ALREADY dies massively in the window (unsw
  156 hitSelf r360-380 alone); cand vs base deltas are mixed
  (schooltime +16 r380-420, stronghold +9, unsw/islands slightly
  down) — the win is CONVERSION not volume: more of the drops land
  on her (qlen@end nearly doubled) because the near-ring wave
  actually arrives inside the window.
- This is the first feed variant that pays — the difference vs the
  dead v149qf series: feeding the ELECTED champ (late, anchored,
  alive by definition) not the roaming queen mid-game.

## SMALL-MAP BUD (v3 #3): verified firing — no change needed

Code at policy.hpp (queen_ && bud_ && round<100 → keepBase=min 2)
is present and live: bud_ = units<18 opens early on all maps,
hiding_ cannot starve it (queenHide=0). Replay check on
v149L-v138 stripes/devil/td/weakhold/dilemma: queen splits fire
r0-56 everywhere incl. td r11 and stripes r11/29 — the keep floor
is already low where it matters. No NC gate in code — it fires on
every map during the breed phase, not just NC<=700.

Candidate for staging: workspace/abyss_v158.

## Enemy echoes + cheap sonar recon (v3 item 5) — detection surface dump

Goal: earlier queen-ram warning via sonar. What the protocol actually carries
(common.hpp, io.hpp, world.hpp, emitSonar in policy.hpp):

- `t.echoes[5]` (ECHOES line, protocol 3): per-TURN aggregate hit counts of OUR
  OWN pings by kind {kelp, ally, allyHead, enemy, enemyHead} — a count, no
  direction, no position. `w_.echoEnemy = echoes[3]+echoes[4]` is populated in
  world.hpp:322 but NOTHING in policy reads it — the alarm hook exists unwired.
- `heardEnemies` (world.hpp:295+): teammate-relayed MsgEnemy sightings
  {id, cell, len<=15, role(isQueen), round}, deduped by cell within 4 rounds,
  fresh <= heardEnemyMemory=8. Already feeds grower danger (wHeardEnemy),
  the queen's soft heard-ram screen (wQueenRamHeard=2.0 vs wQueenRam=30),
  and the assassin squad.
- Enemy beacons/pings CANNOT be decoded: `msgOursKeyed` (round-keyed hash +
  team secret) rejects every non-ours msg before parsing — deliberate
  anti-spoof hardening. "Their own beacon traffic" is unreadable by design.
  Per-ping direction is not returned to the sender (aggregate only), so even
  our own echo is directionless.

Replay measurement (v158_frontload/replays, 24 kept, 5 maps, sonarPing +
dragonUpdate + dragonDeath events):

- Queen echo selectivity: her pings hit an enemy on only 1-9% of her turns
  (autarky 250/2664, unsw 17/1316, islands 14/1584, default 74/1552).
- Predictive power: 6/20 queen h2h deaths had an echo <=5 rounds before death
  — ~5-30x over-represented vs base rate. Rare, high-precision alarm.
- Warnability ceiling: the killer was VISIBLE TO ANY of our dragons within the
  9 rounds before her death in only 4/20 deaths (autarky 2/4, islands 2/3,
  default 0/6, unsw 0/7). Most rammers traverse fog nobody watches: the heard
  relay has nothing to relay. Combined echo+heard coverage <= ~half of deaths;
  detection alone cannot fix the invisible majority.

Prototype abyss_v157e (= v157s + echo guard, ~4 compares in the queen heard
loop): EnemyField gains `round` (staleness); heard-enemy reach widens
+(age/qEchoAge=2); when echoEnemy>0 the heard report prices at wQueenRam
(full fatal) instead of wQueenRamHeard=2.0 (param qEchoRam). Gate:
autarky,islands,unsw,default,stronghold x2 seeds both seats vs abyss_v157s,
tag v157e_echo.

Replay payload evidence (default-s1-abyss_v158-abyss_v149v2): 21565 sonarPing
events total, ~10.7k per team — BOTH teams' pings are recorded at replay level
with {senderId, dir, origin, end, hitKind, hitId, value}. Enemy pings hit OUR
bodies 110x that game (their 'enemy'/'enemyHead' = us) yet their value field is
an opaque keyed hash — nothing decodable reaches us at runtime; the replay
visibility does NOT correspond to a runtime channel.

Gate v157e (echo guard: echoEnemy>0 -> heard price wQueenRam, heard reach
+age/2), 20g vs abyss_v157s, tag v157e_echo:
| map | pair | tl100 c/b | verdict |
|---|---|---|---|
| islands | 2/4 | 86.5/86.5 | bit-mirror |
| unsw | 2/4 | 152.5/152.5 | bit-mirror |
| stronghold | 3/4 | 58.2/58.2 | mirror + 1W |
| default | 2/4 | 31.7/15.3 | +107% tl, real win |
| autarky | 1/4 | 33.5/36.5 | -8%, loss |
| ALL | 10/20 (50%) | 72.5/69.8 | neutral-positive |

Queen deaths by reason (20g): h2h c10/b9, nonRam c9/b10, alive@end 1/1 —
survival identical; the echo slice is too thin to move her death rate at 20g.
The mechanism fires where signals exist (default won) and is bit-inert where
they don't (3 maps mirror) — consistent with the ~50% warnable ceiling.

Gate v157e2 = e1 + qEchoFog umbrella (echo>0 -> wQueenFog x6): BIT-IDENTICAL
to e1 on all 20 games — on echo turns her chosen dests were already visible;
the fog response was saturated. Adds zero; not counted separately.

Gate v157e3 = e1 + qEchoAim (queen beacon aims at freshest heard enemy):
45% pair (9/20). Replay-verified firing: queen enemy-hit rate 2.6%->3.0%
(+15%), pings 9635 vs 8379 — the aim works, but its coverage gain is too
small to matter and it costs beacon reach (stronghold lost e1's +1W).
default still positive (35.0/15.0 tl100). qd<50 3/3, h2h 10/10.

VERDICT (v3 item 5): the sonar channel is real but signal-starved.
(a) Enemy beacon traffic is unreadable by design — keyed filter.
(b) Our own echo is directionless and rare (queen hits enemy 1-9% of turns).
(c) Warnable ceiling ~half of queen h2h deaths; killers are seen by any
    teammate only 4/20 — fog rams are invisible to every instrument.
(d) e1 is a marginal keepable: +107% default tl100, zero measured regression,
    ~4 compares — mirrors qs2 in the "free upside on open maps" bucket.
    workspace/abyss_v157e, params qEchoRam/qEchoAge (+inert qEchoAim knob).
(e) Ram-warning at coverage level needs vision/escort geometry, not pings.
    Sonar detection lane closed at honest marginal; no further variants worth
    the quota-free gate time.

## Early-attrition classification (first-62-round deaths, v158-era self-play replays)

Corpus: 24 kept replays (v158_frontload), dragonDeath+dragonAction+dragonUpdate
aligned per round. Victim vs initiator: whether OUR last move closed distance
to the killer's pre-move head (their step onto us = victim).

Per-map reasons <=r62 (both seats pooled):
| map | h2h victim | h2h initiated | hitWall | hitSelf | hitOtherBody |
|---|---|---|---|---|---|
| unsw | 68 | 42 | 68 | 18 | 4 |
| autarky | 46 | 22 | 16 | 0 | 0 |
| default | 24 | 24 | 2 | 0 | 0 |
| schooltime | 10 | 6 | 2 | 8 | 0 |
| islands | 12 | 0 | 4 | 8 | 4 |
| stronghold | 0 | 0 | 0 | 0 | 2 |
| ALL | 160 (63%) | 94 (37%) | 94 | 34 | 10 |

Length mix of initiated trades (manhattan head-tail proxy): len2-suicide 90
(cheap ram, ~always good), wash-equal 66, slack+1 52, genuinely-shorter 28,
VIOLATION (own len > theirs+1 while visible) 22. Fog-ambush deaths 26.

Read: the early deficit is NOT fights-we-shouldn't-take in the tradeSlack
sense — true violations are ~9% (22/254). Two real classes instead:
1. **Victim-side h2h = the dominant bleed (63%)**: their len2-3 rammers choose
   the trade against our longer dragons — same kill-door as the queen work
   (adjacency decides; whoever initiates wins). Fix axis = worker-side
   dodge-when-outgrown (we lose len k+2 for their len k), i.e. evasion
   geometry for non-queens, not tradeSlack tuning.
2. **unsw hitWall 68 (~1/3 of that map's early attrition)**: fog wall-dives —
   a nav class, orthogonal to combat policy.
Self-play symmetry caveat: both sides bleed identically here; the vs-1750+
asymmetry (a3-5 vs a8-21 @r50) can't be read from self-play deaths alone —
what this shows is WHERE ours come from.

## feedBurst re-gate on live base (abyss_v168)

v158c = v168 + feedBurst only (same params: 14-ring, <=20r, x3), 24g fixture
vs abyss_v168, tag v158c_burst: **45.8% pair (11/24, 2W/7S/3L) — below the
55% merge bar.** The mechanism still works on the primary axis — qlen@end
1.158 vs 0.474 (+144%) — but longest@end -10% (31.8 vs 35.4) flips the net.

Per-map qlen@end c/b: autarky 1.62/0.00, schooltime 1.12/1.12, rest ~0/0.
longest@end losses: autarky 13.3/18.4, schooltime 14.3/19.6, unsw 13.3/14.1,
stronghold 22.1/24.0 — the burst feeds a NON-QUEEN elected champ on queen-
dead boards (queen dead ~80% of games here) and starves the longest axis.
On the v149v2 base the same mechanism was +79% qlen AND +14% longest; v168's
different base (wScout 2.0, qRamAdj merged) inverts the trade.

Rescue under gate: abyss_v158d = v158c + burst restricted to champIsQueen_
(drift-cadence feed for non-queen champs, burst only when feeding the actual
queen — the autarky case that already worked). Tag v158d_burst.

v158d (queen-only burst): **50.0% pair (12/24), bit-inert on 5/6 maps** —
on unsw/islands/stronghold/default/schooltime the elected champ during the
burst window is never the live queen (qDead ~0.8/game), so the gate mirrors
base stats everywhere except autarky, which keeps qlen@end 1.62/0.00 and
narrows the longest@end cost to -2.5 (vs -5.1 full-burst).

Verdict on the merge ask: neither burst form meets the 55% bar on v168 —
full 45.8% (net negative: starves longest@end feeding non-queen champs),
queen-only 50% (marginal free-upside: +autarky qlen, bit-mirror elsewhere).
If the integrator still wants it, abyss_v158d is the safe param'd form —
qEcho-style "open-map upside" bucket, not a flagship merge at this base.

## Early-swarm fragility classification (r10-50 deaths, elim maps)

Corpus: a_nods_v135 + ee_fix120 replay dirs (v135/v120-era self-play —
representative early game; v168 shares the same r<60 mechanics). Taxonomy
per coordinator: rammed = hitHeadToHead (initiator = our last move closed
distance to killer's pre-move head; else victim), cornered = hitSelf/
hitOtherBody, wall = hitWall fog-dive, trapped = noValidAction, len-at-death
= manhattan head-tail proxy.

| map | deaths | rammed victim | rammed init | cornered | wall | splits A/B |
|---|---|---|---|---|---|---|
| devil | 424 | 171 (len2 65/3 62/4 44) | 92 | 118 (28%) | 32 | 464/459 |
| trophy | 128 | 89 (len2 44/3 37/4 8) | 26 | 2 | 2 | 213/163 |
| dilemma | 136 | 96 (len2-4 even) | 24 | 8 | 0 | 184/120 |
| default | 240 | 140 | 88 | 6 | 2 | 282/252 |
| weakhold | 64 | 0 | 0 | 0 | 64 | 64/80 |
| stripes | 25 | 17 | 2 | 0 | 1 | 24/53 |
| qos | 68 | 32 | 8 | 8 | 16 | 60/88 |
| autarky | 224 | 160 | 64 | 0 | 16 | 238/236 |
| td | 8 | 0 | 0 | 0 | 8 | 15/16 |

Findings:
1. **Victim-side rams ~60-70% on devil/trophy/dilemma/autarky** — their
   len2-3 rammers pick the trade; len3 is the modal victim length (94+37+
   62+32...). Early units die outgrown, not out-built.
2. **devil cornered = 118/424 (28%)**: self/body collisions — corridor
   self-traffic, the only class spawn-spread would directly shrink.
3. **weakhold + td early deaths are ~100% hitWall** — fog nav on open
   maps; separate class, not attrition-vs-them.
4. **Split cadence is seat-asymmetric** (dilemma 184 vs 120 A/B, stripes
   24/53, qos 60/88, trophy 213/163) — map-side effect, not a
   bot-vs-bot production gap visible in self-play.
5. Adjacent-eat rate 0.76: short dragons skip ~1/4 of adjacent pearls
   chasing far targets — the eat-adjacent mechanism's headroom.

Mechanism gated: abyss_v168y = v168 + youngEat (+1.0 eatBonus for
L<=3 && round<60, workers only) — growth-over-move for early units.
Gate 20g trophy,devil,stripes,dilemma,weakhold vs abyss_v168, tag
v168y_youngeat.

Gate v168y (youngEat +1.0 for L<=3 workers r<60), 20g vs abyss_v168:
**50% pair (10/20, 2W/6S/2L) — flat/negative.** devil +1 pair, stripes +1,
trophy -1, weakhold -1, dilemma mirror.

Mechanism failed to move its own lever: adjacent-eat rate 0.750 vs 0.760
(DOWN). splits@r60 10.7/10.3, alive@r50 6.83/6.78, pearls@r60 24.5/23.1 —
all inside noise. Side effect: wall+self+body deaths 24.5 vs 15.95/game
(+54%) — young dragons pay the higher eat-value stepping INTO pockets/
fog cells (the pocketEatLen waiver already covered their eat steps; the
added bonus just picks dead-end eats more often).

Verdict: growth-over-move is not the bleed — the classification already
said it (victim-rams ~63% + cornered-traffic ~28%-devil, not intake).
Early fragility needs the dodge-when-outgrown defense for workers (their
len2-3 rammers picking trades against our len3-4) — evasion-geometry,
same door as the queen work; or the devil corridor crowding fix
(spawn-spread) for the 28% self-traffic class. Neither is a forage-value
change. Recommend scoping one of those two next; v168y parked.

## Top-team early-split study (24 ladder loss replays, all eliminations)

Corpus: ladder_replays/ — our losses vs stronger bots. Every axis measured
per len<=3 non-queen dragon, r10-50, split by winner-side (W = opponents)
vs our side (L), and by survivor vs died<=r50 cohorts.

**Result: winners' short-dragon survival is NOT a behavior diff — it's
production volume.** Every behavioral axis matches ~1:1:

| axis | W_surv | W_died | L_surv | L_died |
|---|---|---|---|---|
| dAlly (clump) | 4.64 | 4.45 | 5.13 | 3.69 |
| dEnemy mean | 5.56 | 3.07 | 6.02 | 3.46 |
| dEnemy<=3 frac | 0.50 | 0.67 | 0.43 | 0.76 |
| threatened flee/hold/engage | .36/.48/.16 | .23/.43/.34 | .39/.44/.17 | .28/.47/.26 |
| rel-frontier pos | +0.02 | — | +0.09 | — |
| outnumbered at death | — | 0.47 | — | 0.29 |

- Their shorts ride the same frontier, keep the same ~2.5-cell enemy
  buffer as ours, flee/hold/engage at the same rates, clump LESS than
  ours (we are the more-clustered swarm and still die). Our dead are
  actually MORE supported at kill sites (29% outnumbered vs their 47%).
- Winners' dead shorts die MORE isolated — they push children into
  fights alone: trade ammunition, not escorted foragers.

**The actual diff — split cadence:** splits <=r60, W 276 vs L 113 (2.4x),
92% len-2 children both sides. By 10-round window:

| rounds | W splits | L splits |
|---|---|---|
| 0-9 | 40 | 33 |
| 10-19 | 23 | 12 |
| 20-29 | 32 | 10 |
| 30-39 | 52 | 14 |
| 40-49 | 62 | 24 |
| 50-59 | 60 | 19 |
| 60 | 7 | 1 |

Winners ACCELERATE through the trade war (r30-60 spawn rate ~2.6x ours);
our production tapers to near zero after the opening while alive@50 is
near-equal (37-89/team — these games are volume wars, not the a3-5 early-
deficit profile). Their doctrine: churn len-2 ammunition faster than the
attrition burns it. Ours: conserve and lose the exchange rate.

Mechanism candidates this points at (not yet gated): sustained len-2
production r30+ on elim maps — the bud/keepBase floor stops splitting
after the opening; winners keep spawning through the fight. Aligns with
v174's negative result direction: len-3 children too fragile, but len-2
is exactly what winners spam. Also connects to the 63% victim-h2h read:
if their rammers are disposable ammunition, dying to them isn't a
survival problem — it's a replacement-rate problem.

## PD/Trauma r150-250 death classification (10 ladder losses, team A = us)

Corpus: pdtd_replays/ — 4 Prisoners Dilemma + 6 Trauma losses (ladder.py
replays --team 351, opponents 1432-1790 Elo). All team-A losses.

**Prisoners Dilemma — colony-wipe class, driven by split-volume deficit
(NOT pearl race, NOT queen ram):**

| match | end | eats<=50 A/B | splits<=50 A/B | queen deaths | A deaths r150-250 |
|---|---|---|---|---|---|
| m1106137 zzz3nith 1639 | teamElim@58 | 52/33 | 7/29 | B h2h@58 | — |
| m1100125 STAR 1688 | teamElim@76 | 40/37 | 8/24 | A h2h@26, B wall@27 | — |
| m1102882 Quantify 1432 | teamElim@195 | 21/23 | 10/14 | B h2h@40, A h2h@195 | 5 self, 2 h2h |
| m1098973 okbro 1790 | teamElim@448 | 45/6 | 9/17 | B h2h@446 | 14 hitWall |

- We OUT-EAT them on PD (21-52 vs 6-37) — intake is not the loss.
- They out-PRODUCE 2-4x (14-29 children vs our 7-10 by r50) and convert
  the volume into colony elimination at r58-448. Same mechanism as the
  top-team study: len-2 ammunition churn vs our taper.
- Queen ram is a co-factor only once (m1100125 mutual queen death ~r26);
  in 2/4 the ELIMINATION happens with their queen already dead — the
  swarm finishes the job without her.

**Trauma — bells-attrition class, all 6 roundLimit (never wiped):**

| match | A deaths r150-250 (reasons) | B | queen deaths | eats<=50 A/B |
|---|---|---|---|---|
| m1098980 DeepSeek 1761 | 39 (26 wall/5 h2h/6 self/2 body) | 32 | A h2h@393 | 2/5 |
| m1099009 1234 1698 | 68 (62 wall/6 h2h) | 73 | A wall@168, B h2h@349 | 27/6 |
| m1100855 SuitedConn 1587 | 33 (25 wall/7 body/1 nv) | 34 | B h2h@343 | 19/5 |
| m1104492 nooberGamer 1641 | 35 (33 self!) | 30 | — | 2/6 |
| m1106113 wawow830 1590 | 1 | 1 | B wall@155 | 4/1 |
| m1106125 wawow830 | 0 | 0 | — | 5/1 |

- ~80% of mid-window deaths are hitWall/hitSelf — corridor/fog nav
  bleed, symmetric-ish both sides but we lose the longest@end margin
  (e.g. 16L vs 17L). Queen rammed in only 1/6; our queen even hitWall'd
  herself @168 in one.
- eats<=50 on Trauma are 1-27/side (sparse map); we out-eat opponents
  here too. The r50 pearl benchmark (~29) is not the discriminating
  variable on these maps — attrition to the bells is.
- Classification: NAV-class loss (wall/self in fog corridors), not an
  early-econ class. Flagging for the nav/geometry lane, not solvable
  by production.

**Candidate built: abyss_v168c = v168 + churn floor**
`churnTiles=900, churnAlive=28, churnKeep=3` — on <=900-tile elim maps,
non-queen growers bud at flat keep 3 (vs keepBase + round/30 ratchet)
while units < 28. Directly targets the measured PD gap (splits 7-10 vs
14-29): our keep ratchet prices out budding exactly when the exchange
war starts. ADDS growth; no mobility/econ restriction. Queen untouched
(she already has the keepBase<=2 bud floor). Gate: 24g elim set vs v168.

### abyss_v168c churn floor — gate results (24g elim set vs v168)

- **v1 (grower-keep only): bit-identical** — non-queen growers barely
  exist on elim maps; splits flow from the queen (keep<=2 floor, ~1/game)
  and the swarm half-path. churn_ never bound a decision.
- **v2 (+ worker-bud: swarm workers bud child=2 keeping churnKeep=3 at
  L>=5 instead of halving): 41.7% pair (10/24), dilemma 0/4.**
  splits@60 10.4 vs 11.4 (DOWN), queen dead 0.792 vs 0.625 (UP),
  pearls@60 22.7 vs 24.9. All other maps bit-mirror.
- Mechanism of the miss: at L>=6 bud gives child len-2 where halving
  gave len-3; len-3 children out-survive len-2 in self-play (v174:
  len-3 already fragile), so the bud chain produces weaker ammunition
  and fewer second-generation splitters. Parent keep identical (3).
  Net: churn bud trades child strength for shape — wrong trade vs a
  halving swarm.
- **Deeper conclusion: the PD production gap is upstream of split
  rules.** Opponents' worker-parent splits 14-29 need len-4+ workers
  reaching the front; ours die at len 2-3 (the 63% victim-ram class)
  before producing anything. alive@~50 is near-equal (37-89/team) —
  the winners' churn and our conservation arrive at similar counts, but
  their dead children bought trade geography; ours' dead children
  bought nothing. The fixable surface remains worker survival/evasion
  (evasion-geometry lane), not production knobs — both knobs tested
  (flat keep, worker-bud) are inert or negative.

**Parked:** abyss_v168c (both forms) — results/v168c_churn{,2}/.

## Worker survival under sprint-reach threat — mechanism study (34 ladder losses)

Corpus: ladder_replays/ (24) + pdtd_replays/ (10). Threatened turn =
len2-4 worker with an enemy head inside ITS sprint reach (d <= eLen-1,
eLen<=4). ~33k threatened turns measured, r10-100.

**Their workers respond EXACTLY like ours — every axis identical:**

| axis | W (top teams) | L (us) |
|---|---|---|
| flee/hold/engage | .44/.37/.18 | .48/.34/.18 |
| converge toward nearest ally | .23 | .25 |
| mean exits at dest | 1.90 | 1.87 |
| exits when dying soon | 1.78 | 1.76 |
| exits when living | 1.98 | 1.93 |
| post-threat h2h death <15r | .40 | .37 |
| ally convergence on threat | +0.074 | +0.076 |
| h2h deaths r10-60 (raw) | 67 | 45 |
| killer/victim len mix | symmetric | symmetric |

No winner template exists at the decision level. The survivorship
signature (exits: lived 1.98 vs died 1.78) is universal, not theirs.

**BUT the kill door is real and dodgeable — in OUR losses:**
- 88 attributable victim-h2h deaths: **80% had the killer already inside
  ITS sprint reach at our last decide** (dkh 1: 30, dkh 2: 53), and
  **95% had a free step that increased distance** — visible, in-reach,
  escapable. Only ~20% were true fog approaches.
- Root cause in code: `exposureMode = 0` — the worker sprint-reach
  screen (dd 2..reach pricing) is DISABLED; workers pay wDanger only
  for dd<=1 adjacency. The queen has wQueenRam; workers have nothing
  in the band where 60% of the kills land.

**Gate: abyss_v168x = v168 + exposureMode=1 — 45.8% (11/24), NEGATIVE
but diagnostic:**
- h2h deaths FLAT: 15.46 vs 15.46 — the screen did NOT cut ram deaths
- wall+self+body **+40%: 45.5 vs 32.5** — fleeing workers dive into
  walls/corpses; the dodge converts death MODE not rate
- pearls@60 down 21.8/23.9 (forage tax even threat-gated)
- upside: longest@end +2.0, queen-kept 0.625/0.357
- Structural read: exits ~1.9 means corridor maps offer nowhere to go.
  Soft fear = forage tax (this), hard fear = wall dives. Evasion on
  these maps is geometry-bound, not price-bound.

**Synthesis (3 studies now):** every worker micro-behavior — clump,
standoff, flee/engage, convergence, exit choice, ammo length — is
identical across teams. The ONLY asymmetric variable is split volume
(2.4x). Remaining open levers for elim class: (a) pre-contact nav —
route workers around contested ground before entering reach (nav
lane), (b) volume parity (churn doctrine — needs stronger ammo than
len-2 buds produced). Worker-side in-reach evasion is now CLOSED at
mechanism level: exposureMode proven dead, never re-test.

## Mechanism spec: pre-contact buffer (presence-only evasion)

**Design:** unlike exposureMode (dead at 45.8% — dodges INSIDE reach,
converts death mode on 1.9-exit corridors), the buffer prices the ring
JUST OUTSIDE an enemy's sprint reach. A worker whose forage dest sits
in `dd in (reachOf(e), reachOf(e)+bufferR]` pays wBuffer*newL*mult.
The incentive is to never ENTER reach — enemy presence-only, zero
effect when no enemy ring covers the dest. Non-queen, non-grower,
L<=bufferLen only.

**Code site:** policy.hpp scoreFrom, inside the `k == 0` block directly
after the exposure screen — reuses `EnemyField::dist[dest]` (BFS from
each seen enemy head, already computed for the hunt/stalk pulls).
No new search; 4-8 enemies x per-dest lookup, cheaper than the
exposure loop it sits beside. Danger accumulates the same way so the
forage pull can still out-vote it where the food is dense.

```cpp
if (k == 0 && p_.wBuffer > 0 && !queen_ && !grower_ && L_ <= p_.bufferLen) {
    for (EnemyField const& e : enemies_) {
        int dd = e.dist[dest];
        int rr = reachOf(e.visible);
        if (dd > rr && dd <= rr + p_.bufferR)
            danger += p_.wBuffer * newL * mult;
    }
}
```

**Params (common.hpp, beside wExposed):** `wBuffer` (0=off),
`bufferR` (ring width beyond reach), `bufferLen` (worker cap).

**Predicted counter-movement (vs v168, 24g elim set):**
- h2h_small deaths −10-20% (the dd=2 kill band thins)
- alive@50 +0.3-0.8, splits@60 +0-1 (more workers reach productive len)
- pearls@60 −0-5% (the presence-only tax is bounded by ring coverage)
- wall+self+body flat ±5% — if +15% it's the v168x mode-conversion again
**Kill condition:** pair <55% OR wsb deaths +15% OR pearls@60 −10%.

**Sweep table (all vs abyss_v168, 24g elim set, both seats):**

| variant | wBuffer | bufferR | bufferLen | pair | notes |
|---|---|---|---|---|---|
| v168b1 | 0.75 | 2 | 3 | **45.8%** (1/9/2) | h2h 19.0/18.7 flat, pearls@60 −12% (21.3/24.1), alive@50 6.3/7.1 |
| v168b2 | 1.50 | 2 | 3 | **41.7%** (1/8/3) | h2h 17.1/17.2 flat, wsb −41% (14.5/24.7), longest@end 9.75/26 |
| v168b3 | 1.50 | 1 | 3 | **50.0%** (0/12/0) | every map dead-split; h2h 15.9/15.1, pearls@60 −13% (21.5/24.7), alive@50 6.2/7.0 |

**Sweep verdict — pre-contact buffer is DEAD (kill condition met: pair<55%
at every dose).** The signature is consistent across the ring widths:
h2h deaths FLAT at all three points (19.0/18.7, 17.1/17.2, 15.9/15.1) —
pricing the buffer ring never touches the rams; they walk through it
because the ring overlaps the productive forage band (enemies graze where
the pearls are). The only dose response is on the TAX side: pearls@60
−12-13% at every dose, splits@60 −1, alive@50 −0.7-0.9. Narrowing the
ring (bufferR 1) removes the loss but keeps the tax — no dose exists
where evasion pays.

**Combined closure:** inside-reach dodge (exposureMode, v168x 45.8%)
converts death mode; outside-reach ring (wBuffer, b1-3 ≤50%) taxes
forage with h2h flat. Presence-priced worker evasion is closed at BOTH
sides of the reach boundary — marked do-not-retest. The 63% victim-ram
bleed is not reachable by pricing workers' own movement: remaining
surfaces are (a) production parity (dead at v174/v168c forms — needs a
different churn form), (b) escort/body-geometry (a rammer can't move
through our other dragons — an ally-screen, not a fear price), or
(c) spawn placement so children don't forage into contested corridors.

## Spawn-position forensics (spec+numbers, 35 replays / 5279 splits)

### Survival by spawn->enemy distance (BFS on real walls)
| d_enemy | n | mean life | p(life>=20r) |
|---|---|---|---|
| 1-2 | 1430 | 35.1 | **0.473** |
| 3 | 1979 | 46.3 | 0.585 |
| 4-5 | 1076 | 38.8 | 0.514 |
| 6-7 | 440 | 38.1 | 0.534 |
| 8+ | 354 | 49.3 | 0.605 |

Gradient exists but is shallow: the dangerous band (d<=2) costs ~11pp
of 20r-survival vs d>=8. Modal spawn is d=3 (37% of all splits) — even
"safe" spawns die at corridor attrition rates.

### Spawn geometry ours (A) vs theirs (B) — the premise fails
| side | n | d_enemy mean/med | d_own-centroid | own heads<4 | pct >=3 own |
|---|---|---|---|---|---|
| A (us) | 1258 | 3.91/3 | 17.5 | 1.36 | 0.138 |
| B (them) | 4021 | 3.61/3 | 15.2 | 1.29 | 0.130 |
| — r<=60 only | | | | | |
| A | 246 | **5.19/3** | — | 1.19 | — |
| B | 436 | **4.36/3** | — | 0.96 | — |

**Our early children already spawn SAFER than theirs** (5.19 vs 4.36
enemy dist r<=60) and we still lose the war. W-side d_cen 14.8 vs L 19.4
is blob-size confounded (winners have bigger blobs by definition).
d_parent=3 for 67% of splits — spawn cell is mechanical (tail-side
offset), only WHEN is choosable.

### Dilemma knife-fight verdict: YES, winners out-split early
Per-game splits (A=us / B=them), winner marked:
- we win (3 games): r0-30 ~8 vs ~5, r30-60 ~1 vs ~0 — BOTH sides taper;
  we win knife fights where nobody ramped (early wipe/queen kill).
- we lose (4 games): r0-30 **5-7 vs 9-17**, r30-60 **0-2 vs 3-16** —
  theirs compound (~2x seed -> ~4x window-2), ours flatline ~0.
- Parent profile r0-30: our splitting parents plen+clen ~= 7.2 total vs
  their 9.7 — their early parents are +2.5 length before splitting.
- Queen-parent share ~10-11% both sides; 90% is worker-parent churn.

### Mechanism verdict: spawn-timing veto — REJECTED (data falsifies it)
Proposed lever (delay splits while parent in contested ground) bounds:
- population affected: 22-27% of splits sit at d_enemy<=2
- upside: +11pp survival on <=1/4 of children = +2.6pp aggregate
- cost: delayed production on the single variable that decides games
- plus: our spawns are already safer than winners' — no differential
  to capture. Predicted counter: splits@r60 -20%, alive@50 ~+0.1.
**Do not build.** (c) spawn placement — closed, falsified.

### What the forensics DO show
The chain is: worker-parent split volume (2-9 vs 14-29 by r50)
<- parents reaching plen~5+ (theirs split from ~9.7 pre-split len
r0-30 vs our ~7.2) <- workers surviving past len-3 <- the closed
evasion surface. Every link upstream of "production ramp" is a
survival link. With (a) in/out-reach pricing closed and (c) spawn
timing falsified, the only untested member of the closure list is
(b) escort/body-geometry — physical cover via allied bodies, not a
fear price. Caveat: ally-clump is already measured-flat (dAlly
4.64/5.13, we clump MORE and die more) so a body-screen must change
positions relative to THREAT vectors, not allies alone.

## Early-elim classification (19 ladder/pdtd losses, teamEliminated <=r300)

### Cause counts
| class | n | share |
|---|---|---|
| (a) our queen rammed (h2h, theirs outlives) | **10** | 53% |
| (b) queen-v-queen mutual | 0 | 0% |
| (c) colony attrition (queen outlives or dies non-h2h) | 6 | 32% |
| (d) pearl deficit at r50 (<50% of winner's) | 3 | 16% |

Queen-ram is the top class and it is EARLY: death rounds
26,32,33,39,47,50,57,88,168,184 — median ~50. Matches STATE.md
"lone len-2/3 rammer onto stationary queen" (pocket lane owns).
On PD specifically the wipe is colony-class (worker-parent split
deficit) per the earlier study — attrition/ram overlap: 3 of the
"attrition" games also end with queen h2h but AFTER their queen
already died (the wipe decides it, not the queen).

### Winner vs loser state (all 19 losses; L=us, W=them)
| round | alive L/W | splits L/W | pearls L/W |
|---|---|---|---|
| r25 | 3.5/2.9 | **1.9/3.6** | 4.9/5.5 |
| r50 | 5.4/5.1 | **3.2/9.9** | 15.6/13.7 |
| r100 | 8.2/8.2 | **6.3/21.8** | 32.8/33.4 |

### Decisive answer: winners do NOT field a bigger standing army —
they run ~3x unit THROUGHPUT. Standing alive is equal at every
checkpoint (3.5/2.9, 5.4/5.1, 8.2/8.2) while cumulative splits go
1.9x -> 3x -> 3.5x. Their children die faster (ammunition churn);
ours die slower but produce less. Pearl intake is at PARITY
(15.6/13.7 @r50, 32.8/33.4 @r100) — food is not the bottleneck;
conversion of food into births is.

### "Is our opening too slow?" — yes, measurably: 1.9 vs 3.6 splits
by r25. The deficit is front-loaded (already ~2x by r25, not just
the r30-60 taper from the earlier study). Consistent with the
queen-bud reading: their queens/parents split from ~9.7 pre-split
len r0-30 vs our ~7.2 — they reach productive length sooner and
cycle immediately. The opening speed gap is upstream of every
later production deficit measured in this lane.
