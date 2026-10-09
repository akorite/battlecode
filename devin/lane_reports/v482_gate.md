# abyss_v482 gate — queenHideUntil 390→300 on v476

Variant: workspace/abyss_v482 = cp -r abyss_v476, one-line diff
`int queenHideUntil = 390 → 300` (common.hpp:261).

Boards (seeds 8, seed-start 1, jobs 20, both seats):
- v482_mir: cand v482 vs base v476, --maps all
- v482_elim: cand v482 vs base v376, maps devil,trauma,islands,tower_defense,
  slithery_fight,portals,trophy,weakhold

## Interim tallies (running)

| checkpoint | v482_mir | v482_elim |
|---|---|---|
| ~10 min | 32/64 = 50.0% | 27/40 = 67.5% |
| ~30 min | 50/99 = 50.5% | 51/83 = 61.4% |

Per-map (v482_elim @83): devil 5/11, islands 2/8, portals 8/12,
slithery_fight 6/7, tower_defense 9/12, trauma 4/12, trophy 8/11,
weakhold 9/10.

Per-map (v482_mir @99): all ~50% — Colosseum 3/6, arena 3/6, australia 1/2,
autarky 2/4, big_empty 1/2, default 3/6, default_small 2/4, devil 3/6,
dilemma 3/6, islands 1/2, maze 2/4, portals 3/5, qOS 3/6, schooltime 2/4,
slithery 1/2, stripes 3/6, stronghold 2/4, TD 3/6, trauma 2/4, trophy 3/6,
unsw 1/2, weakhold 3/6. No bleed map.

## FINAL

- **v482_elim: 81/128 = 63.3%** vs v376 (weakhold 15/16, slithery 13/16,
  TD 12/16, trophy 11/16, portals 10/16, islands 8/16, trauma 7/16,
  devil 5/16)
- **v482_mir: 176/352 = 50.0%** vs v476 — literal coin flip, every map
  within noise of 50% (max deviation islands 7/16, unsw 8/14).

Verdict: hideUntil 300 on v476 = +13.3pp vs v376 on the elim set, zero
mirror regression. PASS.
