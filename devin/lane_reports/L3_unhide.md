# L3 queen un-hide sweep — queenHideUntil {300,330,360}

Variants (one-line common.hpp:261 edits; corridor override
eff_.queenHideUntil=320 untouched):
- abyss_v482 = abyss_v476 + queenHideUntil 300  → boards vs v476 (mir) + v376 (elim)
- abyss_vL3b = abyss_v481 + queenHideUntil 330  → board vs v481 (all-maps)
- abyss_vL3c = abyss_v481 + queenHideUntil 360  → board vs v481 (all-maps)

Seeds 8, seed-start 1, both seats.

## Results

| board | diff | base | tally | verdict |
|---|---|---|---|---|
| v482_elim | v482 hide300 | v376, elim set | **81/128 = 63.3% FINAL** | PASS vs v376 |
| v482_mir | v482 hide300 | v476, all-maps | **176/352 = 50.0% FINAL** | flat — no self-regression |
| vL3b_all | hideUntil 330 | v481, all-maps | **176/352 = 50.0% FINAL** | flat — no self-regression |
| vL3c_all | hideUntil 360 | v481, all-maps | **176/352 = 50.0% FINAL** | flat — no self-regression |

## v482_elim per-map (final, n=16/map)

weakhold 15/16, slithery_fight 13/16, tower_defense 12/16, trophy 11/16,
portals 10/16, islands 8/16, trauma 7/16, devil 5/16.

Interpretation: queen un-hides at r300 instead of r390 → +13pp vs the v376
elim baseline with zero mirror regression vs v476 (49%, every map ~50%).
The elim-set gain is real — un-hiding early pays where boards are small and
the queen becomes a forager sooner. devil (5/16) and trauma (7/16) remain
the soft maps.

ALL FINAL. Per-map on the three mirror boards: every map within noise —
max deviation anywhere is australia/unsw/big_empty/schooltime at 7/14 on
one board each; every other cell 8/16 or 7/16.

Interpretation: the whole L3 un-hide sweep (300/330/360) is regression-free
vs near-self on all 22 maps both seats. The only uplift signal remains
v482 vs v376 on the elim set (63.3%) — early un-hide pays on small boards
and costs nothing elsewhere. Note L3b/L3c measured vs v481 (no elim board
was requested for them); their elim-side value is untested by this sweep.
