
## H-C4: corridor wedge veto (reproduced → implemented)
- **Claim (report5 §C4):** queen dies entering a 1-wide run contested by another dragon at the far end (Autarky r70 ally head, Maze r131 enemy body) — two-way reservation only covers cells next to her head.
- **Fix:** queen-only veto — dest with exactly 2 open neighbours starts a deg≤2 walk (≤8 cells); any non-self seen segment in the run or on its exit cell ⇒ treated as deadend (stepTerm −2000, terminal, demoted below open moves).
- **Falsifier:** autarky pair record should improve; queen non-ram deaths on corridor maps must not rise.
- **Result:** smoke +60%/20g (autarky 2/4→4/4). qNonRam 0.35 vs 0.25 — watch on full board.

## H-C5: exit-reservation scope (reproduced → implemented v2)
- **Claim (report5 §C5):** unconditional ≤2-exit reservation costs Devil (8/24 vs 15/24 without) — marks both exits INF in crowded openings.
- **v1 (len≤2 && head≤2 gate):** FAILED — reservation never fired (queenLen rarely ≤2); queen non-ram 0.35 vs 0.05, kept 12.5% vs 60%. Rejected.
- **v2 (regionReach<30 gate):** reserve only when she is geometrically pocketed — open-field crowding exempted.
- **Falsifier:** devil ≥ v143 without queen non-ram regression elsewhere.
- **Result:** smoke 60%/20g combined with C4; devil 2/4 same-pairs. Full 68g gate running.

## H-C5 resolution: all reservation forms wash (parked)
- **v3 (end-block-only):** ending-legality reject on her exits, no transit INF — 46%/68 vs v143, queen metrics even but big-map bells lost (autarky/islands pair losses). REJECTED.
- **v4 (end-block always + transit-INF pocketed AND r>=60):** 45%/20 smoke — the r60 delay re-opened the autarky farm corridor during formation. REJECTED.
- **v5 (transit-INF when pocketed, end-block always — union):** 45%/20 — corridor-exit end-block is itself an econ cost. REJECTED.
- **Verdict:** protection pays ≈ what landing-rejections cost in every scope tested. Parked; the doomed-fallback exit-last ranking stays (free).

## H-C4 attribution fix: corridor veto is inert at n=20
- v148 = v143 + C4 alone: 50%/20, ALL metrics identical to base to the decimal — the veto ~never fires on the smoke set. The earlier autarky 4/4 was the C5 region-gate, not C4. Kept in the stack (queen-only, free insurance).

## H-PLANT: champion lock (WC recipe — shipped to gate)
- **Claim (report6/user):** WC locks their champion ~r330 and converges feeds on a stationary head; ours roams so drops scatter (29% adjacency).
- **Fix:** champFallbackRound 400→330 + w_.champAnchor — self-elected champ locks onto its head cell (needs regionReach>=12) until feedStop; moderate bel=1.2 anchor target keeps it hovering ~3-5 cells (2.5 froze it and starved the champ: stronghold 44 vs 61).
- **Bug found in review:** anchor must live in World — Policy rebuilds per turn so a per-turn member only decelerated (v149a). Fixed before gate.
- **Result (deceleration variant):** 51.5%/68 vs v143 — longest@end +2.9, qNonRam −31%, qlen@end +0.3, pairs 3W/29S/2L.
- **Result (true lock):** 60%/20 consolidation smoke — autarky+unsw converted, ZERO pair losses, qAlive@end doubled (0.333 vs 0.167), kept-after-theirs 44% vs 0%. 68g vs v138 running.

## H-SCORE: r499 scoring is lexicographic (VERIFIED 35+/0 miss)
- **Model:** winner = max(queenEnd, then longest, then total) — queen's end-length FIRST (0 if dead), longest dragon second, team total third.
- **Evidence:** all 35 r499 replays in v149L_v138 predicted with zero misses, including both counterintuitive stronghold cases (lost 96-vs-47-longest with dead queen; won 41-vs-45 with qEnd 17 vs 4).
- **Doctrine consequences:** (1) queen survival to 499 auto-wins vs dead-queen boards; (2) qlen@end is literally the primary score — feeding her is the top mechanism; (3) champ lock handles only the both-dead (0=0) axis; (4) "queen wins length races" is literal, not metaphor.
- v149's win edge IS this: qlen@end 3.79 vs 2.65 (+43%).

## H-FEEDFLOOR/H-UNHIDE: both wash (v150, 50%/20)
- feedMinUnits 3→8 on >2000-tile maps + queenHideUntil 390→300: qlen@end IDENTICAL (3.167), alive@end +2.3, unsw pair loss. Queen dies 75% before unhide matters; when she lives, feeders still can't reach her. REJECTED — binding constraint is survival+reach, not timing.
- CONFIRMED BUG (priority 1): kParams line `p.champFallbackRound = 360` overrode the 330 decl — live v149 ran 360. Fixed in source; next build carries it.

## 2026-10-04 (post-restart batch)

**H-PORTAL2 (scout picker fix)** — mechanism: scout moves scored +5.8 but never selectable (dest<0 skipped in pick loop; safeFirst vetoed). Fix: pick/depth/fallback allow why=="scout", queen excluded, wScout 6→2.
- S0: portals freeze BROKEN — 900 pearls eaten vs 5, longest 21 vs 5. ✓ mechanism
- S1 (24g, pre-queen-gate+wScout6 binary): **41.7% — NEGATIVE.** Worker stream-through → deaths 59 vs 42, escort drain, qDead 0.79 vs 0.67. v151b (queen-gate + wScout=2) re-gating.

**H-MIRRORHUNT-final (autarky)** — corrected aim (queen's mirror, seen-symmetry): **37.5%/24 — DEAD, parked permanently.**

**H-QFEED (earlyecon, 4-variant)** — feeding queen r200+ negative in every config (sacrifice > drops; death cell walls her). Screens: qs2 +5.5pp qAlive@end at 50% pair = marginal. **Queen-feed CLOSED; survival is escort/evasion-geometry bound.** Pending: pocket's threat-conditional escort + queen-anchor.

**H-TORUS (explore)** — Board::id() wraps unconditionally; qOS mutual-elims = invisible seam-approach h2h (17.2/game/side). Earlyecon checking loss asymmetry on queen before building a guard.

**H-PACE (explore)** — BC_PACE revisit-penalty on v127 base: schooltime swept 2-0, alive@499 23.5 vs 3.7, longest 36 vs 13.7 vs cf. Porting to v149 base now — first artifact with big alive@end deltas.

**H-CHFEED (pocket v150 merge)** — die-in-place SPLIT-0 works (22.2/game, 23% adj vs 18%) but 45%/20 wash. Gap identified: queen-champ never plants → stale-head feed deaths. Feeds into v153 spec (queen anchor + threat escort).

## H-QTRAP (2026-10-04) — phantom loopRoom disables ALL queen dead-end vetoes
- Observation: dilemma queen deterministic hitSelf@r25 both seeds; replay shows her walk a 1-wide cul-de-sac (14,11->15) scoring "forage" +1 at r20 while the seenOnly scan flagged unproven=1.
- Mechanism: `loopRoom = sc.cycle && sc.cells > newL && sc.frontier == 0` is computed on the OPTIMISTIC (fog=open) scan; on every map except weakhold (so && wh_), fog leaks phantom cycles → loopRoom always true → `!loopRoom` gates the veto off. Queen dead-end veto never fired outside weakhold.
- Also found: C1-class "unproven" flag was computed correctly (unp=1) but ignored.
- Fix (v156): loopRoom requires proven loop in the seenOnly scan; a proven-exhausted non-cyclic thin-frontier region counts as `tree`.
- Prediction: dilemma queen survives r20-25 (picks N/E at r20); queen dead-by-pocket deaths drop on all small maps.
- Kill condition: v156 <50% vs v149 on the elim-map fixture, or queen pinned into starvation.

## H-RAMREACH — 2026-10-04
- Mechanism: the queen's ram screen prices an enemy's kill-reach as
  freeSteps + L - 1, ignoring pearls: a rammer that eats mid-path gains
  segments and out-ranges the screen by one tile per pearl eaten. Real
  reach = free + L - 1 + pearls-on-path (rules audit).
- Fix (v160): per-enemy reachBoost = count of seen pearls inside its
  reach field (cap 4), added to the queen ram/lead/heard screens.
- Prediction: on pearl-rich queen-death maps (qOS/stripes/dilemma),
  cand queen dies measurably less often (qDead/game down, more
  r66-elims like the s2-B win survived).
- Kill condition: 24g board <52% or new r0-60 queen deaths vs v149.
- Status: GATING (tag v160_ramr).

## Composite plan (flagship v16x)
- Base v157 (portal picker + C5; autarky 68g board pending) +
  qRamAdj (pocket's weakhold-dim adjacency ram fix, verified 4/8 wh) +
  reachBoost if v160 passes + pocket's v153 queen module (anchor +
  threat-conditional escort + evasion) when delivered + v159 seam fix.
- Each piece only merges if its own gate passes — v142 composite lesson.

## H-QMOD composite (v163) — 2026-10-04
- v163 = v157( portal+C5 ) + portalGuess=0 + reachBoost + qRamAdj +
  pocket v153 (queen soft-localization + threat-escort + die-in-place).
- pocket's three-gate attribution on the SAME 20g set: latch 65% /
  locked pivot 50% / none 40% — the soft-latch IS the mechanism.
- Note: v153 gates used champFallbackRound=360 (live semantics);
  v163 keeps 360 for measurement fidelity, flagged in review.
- Prediction: ≥55% vs v149 on 17-map board, qlen@end up,
  queen-dead down on escort maps.
- Status: GATING (tag v163_full, 68g).

## H-C5MARG (resolved 2026-10-03)
**Question:** does C5 (queen exits==1 reservation) inside v157 hurt queen survival (autarky's read: kept-after-theirs 24.2% vs 38.5%)?
**Test:** v165 (portal-only) vs v157, 15 maps × 2 seeds × both seats = 60 games.
**Result:** v165 = 41.7% (0W/25S/5L) — **C5 is net-positive inside v157.** qlen@end 3.89 vs 2.78. autarky's in-composite read inverted; the exit-reservation buys queen length that scores tier-1.
**Decision:** KEEP C5 in the flagship line. v157 shipped.

## H-FLAGSHIP-168
v168 = v157 + reachBoost + qRamAdj + die-in-place(SPLIT-0). Board vs v149 running (75%/8 early).
v169 = v168 + feedBurst staged behind it.

## H-SELFKILL — queen self-kill is the top band-loss leak (OPEN, building)

**Mechanism** (pocket diag, 11 band losses): 6/11 = the queen corners HERSELF —
hitWall×2, hitSelf×2, hitOtherBody×2 at r68-494. In 3 games our longest was
equal/better: the self-kill alone forfeits lexicographic key-1. The calibrated
trap scan (unproven-room veto) was gated `W==40 && H==15` — dead on every map
those deaths happened.

**Prediction**: with the scan on for the queen on every map (v173:
`wh_ = queen_||pocketMap_`), queen non-ram deaths drop on autarky/maze/unsw/
australia without pinning her on open maps. Kill condition: queen non-ram
deaths/game doesn't drop OR queen-dead rises (she pins herself to death).

**Build**: v173 = v168 + qRamAdj ungated (adjacency screen was also dims-gated —
OFF on trophy/devil/stripes/australia where 5/11 rams landed) + wh_ as above.
Smoke: 12 diagnostic maps, both seats.

## H-EARLYDEF — early swarm deficit on elim maps (OPEN)

**Mechanism** (same diag): a3-5 vs a8-21 at r50 → ram → elim. We DO split ~9-10x
by r60 — bounded by pearl intake (20 vs 29 @r50) and swarmSplitLen=4 (need 2
pearls/worker to split). Prediction: swarmSplitLen 4→3 (v174) fields +1-2 units
by r50 on elim maps without collapsing fights. Kill: alive@r50 doesn't rise or
early losses worsen on the elim set (trophy/devil/stripes/weakhold/arena/
dilemma).

## Gate rule change: 75% (was 70%) — increments are dead; only structural
moves ship now. v168 stays live until a candidate clears 75%/≥100g.

## H-FEEDCAP — feedMaxLen=6 leaves consolidation half-done (OPEN, built)

**Mechanism** (m1098277 Australia, 43 dragons/462 total lost longest 24 vs 28):
only len<=6 dragons feed; mid-size units (7-23) can neither feed nor be elected
→ swarm stays distributed, champ underfed. 45 noValidAction deaths fired but
drops went to a churning election target (autarky saw 9 champs re-elected).

**Prediction**: fMax = champLen_-1 when champHead_>=0 (v176) converges to one
long dragon on BIG maps; longest@end rises on australia/unsw/autarky without
attrition collapse (feedMinUnits=3 floor). Kill: alive@end drops >20% with no
longest@end gain (over-consolidation into a dead champ).

## v173 post-mortem — FAIL 39.6%/48
wh_=pocketMap_ suppressed budding on pocket maps (splits@r60 -16%, the
documented pin regression), queen-dead flat 0.75 — pure cost. Reverted;
wh_ dims table stays pending a legal feature. qRamAdj isolated to v177.

## H-WALLBLEED — fleet hitWall attrition is one-sided (OPEN)

**Data** (m1100855 trauma live loss, team-B=us): 275 hitWall + 55 noValidAction
vs opponent's 14 total. Deaths spread all rounds (peak r350-400), clustered in
OUR territory (x0-39, y0-23 of 48-wide board) — foraging into dead-end pockets,
then least-bad = wall death. Opponent never does this.

**Mechanism**: workers forage into shrinking pockets with no region-awareness;
when cornered the eval has only lethal moves. Same root cause as queen
self-kill but fleet-wide. Worker-side fix must be scoring/foraging-target
(rules ban worker vetoes only on splits/openings; a pocket-avoidance bias in
forage scoring is a legal preference, not a safety veto — needs care).

**Kill condition**: if pocket's room-shrink variant (queen-only) drops
wall-deaths/game in its gate, extend the mechanism to worker forage targets.

## H-QUEENCOST — the dominant evaluative frame (CONFIRMED PATTERN)

Every candidate that drains units near the queen kills her more, and a dead
queen forfeits key-1 regardless of longest. v176 proved the mechanism works
(longest@end +15%) yet lost (queen-dead 0.812 vs 0.750). v175 same shape.
Rule for all future candidates: queen-alive@end and queen-dead/game are the
PRIMARY gate metrics — a variant can win longest/alive and still be a kill
if it taxes her escort or her drop supply.

## v174/v175/v176 post-mortems
- v174 (splitLen 3): 0%/24 — len-3 children too fragile; production halved.
  The early deficit is INTAKE/fragility, not split rate. DEAD.
- v175 (C7+champMargin): 47.9%/48 — champMargin stays autarky-only.
- v176 (feedMaxLen relax): 46.9%/32 — consolidation works but taxes queen.
- v177 (adj-ungate): 50%/48 identical — keep as zero-cost insurance (the
  ungate only fires vs ladder rams; self-play can't produce them).
