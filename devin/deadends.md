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
