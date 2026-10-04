
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
