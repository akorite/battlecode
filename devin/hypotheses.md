
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
