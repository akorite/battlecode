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
| v482_mir | v482 hide300 | v476, all-maps | 79/162 = 48.8% (running) | flat — no self-regression |
| vL3b_all | hideUntil 330 | v481, all-maps | 51/103 = 49.5% (running) | flat — no self-regression |
| vL3c_all | hideUntil 360 | v481, all-maps | 18/37 = 48.6% (running) | flat — no self-regression |

## v482_elim per-map (final, n=16/map)

weakhold 15/16, slithery_fight 13/16, tower_defense 12/16, trophy 11/16,
portals 10/16, islands 8/16, trauma 7/16, devil 5/16.

Interpretation: queen un-hides at r300 instead of r390 → +13pp vs the v376
elim baseline with zero mirror regression vs v476 (49%, every map ~50%).
The elim-set gain is real — un-hiding early pays where boards are small and
the queen becomes a forager sooner. devil (5/16) and trauma (7/16) remain
the soft maps.

L3b/L3c on the v481 lineage: dead-flat mirror boards so far (the v481 base
already differs from v476 — these measure regression only, not uplift vs
v376). No bleed map on either.
