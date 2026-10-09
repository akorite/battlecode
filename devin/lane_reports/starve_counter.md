STARVE-COUNTER: why 1700+ teams starve us in contested zones
=============================================================
Corpus: all 20 recent h2h replays vs the teams beating us —
hm(221), life is NP hard(30), DeepSeek-V4.1-Flash(776),
NUSW(262) — + 48 of their games vs other opponents as winner
baseline. Eats = pearl removals attributed to nearest head d<=1.
Analyzer: devin/pocket:tooling/starve_counter.py.
Loss record in corpus: 5-15. 9/20 losses had us <35% of pearls
(matches the 52v417 / 48v450 / 75v591 signature).

AGGREGATE (medians, 15 losses):
                    us      them    ratio
  eats/game        523     1039     2.0x  (33% share)
  eats r0-120       78      290      3.7x
  eff r0-120       .051     .079     1.55x (per unit-round)
  unit-rounds120   1537     2562     1.67x
  splits r0-120     35      102      2.9x
  alive @r120       18       41      2.3x
TIME-SLICE (the gap is FRONT-LOADED, not accumulated):
  eff r0-60        .053     .106     2.0x
  eff r61-120      .052     .105     2.0x
  unit-rounds r0-60  434      781     1.8x  | r61-120 886/1899 2.1x
Their-vs-others baseline: winners eff120 .079, losers .064 —
the .079 figure is their norm vs everyone; we sit at loser level.

CONTESTED-ZONE METRICS — mostly parity; NOT the separator:
  contested SHARE of eats: us 24% vs them 15% (we contest more,
    share-wise, and still lose)
  steals (ate while enemy equidistant-or-closer): 23 vs 20
  ally density <=4 cells at contested eats: 1.9 vs 2.4 (theirs
    higher only because more units exist)
  drop recycling rate: 47% vs 47%; contested-zone re-eats 43v68
    (volume, not rate)

THE SINGLE LARGEST MECHANISM = early unit-level forage
throughput, ~2x ours at EVERY window from r0. Their stubs
convert ~0.105 pearls/unit-round from the opening bell vs our
~0.052, which (a) regrows parents to len-4 resplit ~2x faster
(splits120 102v35) and (b) fields 2.3x the heads by r120. The
contested-zone behaviors the loss narrative blamed (contested
claim rate, steals, crowding) measure at parity or favor us —
they do not out-fight for food; they out-produce. The starvation
is a throughput gap that compounds into a headcount gap, exactly
the intake-census + opening-cadence signature, now measured
against the actual tormentors.

WHERE IT'S WORST: open maps — Islands (5-44% share), Trauma (8%),
Australia (9%), Devil (11-12%), Queen Of Spades (23%), weakhold;
we hold closer on tight maps (Portals 43%, Slithery 35-40%,
Maze 38%). In our 5 wins their alive120 med = 1 (early elim).

IMPLICATION: fixes that push into contested beds or raise claim
aggression address a parity channel; the ~2x per-unit early
intake gap (targeting/approach efficiency, r0-60 especially) is
the lever — every point of eff120 closes ~1.67x headcount AND
~1.55x per-unit yield simultaneously (they multiply).
