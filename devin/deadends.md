# Dead ends this session (see also knowledge/17_deadends.md + 20_devin_lane_evals.md)

## v118 early-feed (5 smokes, all <50% vs v117)
feedBigRound=100 on NC>1300 (+relay/fallback pulls):
- minUnits=3: swarm suicides to 5 alive (33%)
- minUnits=20 floor: champ starves at endgame (43.8%)
- units>=30 converge-gate: (37.5%)
- +queenHideUntil=100: unsw 4/4 but slithery 0/4 australia 1/4 (43.8%)
- +calm-gate (unhide only if no enemy<=8): broke unsw too (31.2%)
VERDICT: early champion by feed-timing is a dead end in this form. The r320 all-in
feed already wins its longest-dragon share; early versions donate dragons into
contested space before territory settles. Champion growth should ride swarm size
(pearl/feed restore), not the calendar. Opponents' 40@300 champs may come from
organic queen foraging + pocket safety, not earlier convergence.

## v120 openMaxTiles=1200 (2 smokes, both <50%)
Extending forage-first opening to 700-1200 tile maps (QoS/autarky/default/maze/trauma):
- plain 1200: 42.5% — autarky 75% but QoS 12.5%, default 37.5%, maze 37.5%
- +enemy-arrival gate (open_ off when enemy<=10): 32.5% — per-dragon flickering breaks
  swarm coherence; longest crashed 29.6 vs 41.1.
VERDICT: the opening only fits <=700 non-maze maps. Autarky's gain isn't capturable by
NC or local enemy gates — contestedness needs swarm-level state, not a tile count.

## abyss_pocket hotFar pulls (2 smokes, <50%)
Past-horizon fountain pull for starving dragons (wHot*hotFar*fp(1.3*manh), gated
foodLocal<0.05): hotFar=0.5 → 25% on weakhold self-play (queen deaths +); hotFar=0.25,
queen/grower/lead excluded → 37.5%, stark side asymmetry (A 3/4, B 1/4).
Weakhold repro vs combat: we out-eat them to r60 (11.5 vs 1.5 pearls) then flatline —
they hit 27 alive, we die at 4. BUT self-play shows v119 CAN grow 20-40 swarms on
weakhold — starvation only bites under contest. Fix needs corridor-aware exit pathing,
not manh-greed toward fountains through walls. Code left in workspace/abyss_pocket.

## abyss_scale reproduction knobs (2 smokes vs combat, both dead)
The 2x-throughput gap vs combat is NOT a knob:
- swarmSplitLen=3 + splitEnemyDist=1 + splitRoom=6: 4.2% — splits DOWN (3.6v4.2),
  dragons can't reach len-3 to split anyway. Gate isn't binding; survival is.
- swarmSplitLen=2 + growerChild=1 (cheap len-1 children): 12.5% — alive@r50 crashed
  to 1.05; len-1 children die instantly. Swarm-density reproduction is a system
  (density protects children), can't be imported by a param.
Bud engine diagnosis for whoever picks this up: queen buds only when
L_>=keep+2 where keep=4+round/30 (len>=8@r60, >=16@r300), worker splits need
len>=4 + enemy-ban 2 + roomy-move both halves — under contest neither fires.
