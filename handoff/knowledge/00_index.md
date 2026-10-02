# Abyss deep-analysis package — index

*UNSW Battlecode 2026 "Abyss" · 80,940 replays · 59,544+ games analyzed · Sep 21 – Oct 1, 2026*

## Files

| File | Contents |
|---|---|
| `01_rules.md` | Rule-by-rule analysis — what each mechanic produces at scale (sprint is dead, suicide is the elite fork, sonar is a broadcast) |
| `02_game_flow.md` | The four phases: expansion → collision → consolidation → the bell; winner/loser divergence curves |
| `03_eval_engine.md` | bceval dissected — calibration, feature weights, the mid-game winner signature, per-team logit fingerprints |
| `04_eras.md` | Era-by-era meta evolution Sep 26→Oct 1 + tier×era matrix |
| `05_tiers.md` | Elo tiers — what separates Shark from Tunafish, elo calibration, the language divide |
| `06_maps.md` | All 10 maps profiled — marathon/reference/sprint archetypes, death fingerprints, who's good where |
| `07_doctrines.md` | The 8 strategy families ranked by evidence + doctrine-vs-doctrine reads |
| `08_deaths_sonar.md` | Death-cause fingerprints by team and map + sonar composition/economy |
| `09_top20.md` | Top-20 table + reads on ranks 11–20 |
| `10_h2h.md` | Top-10 head-to-head matrix + rock-paper-scissors reads |
| `11_method.md` | Pipeline, coverage, caveats, sources, data format |
| `12_prior_comps.md` | MIT/Cambridge/Halite/Battlesnake postmortems — what prior winners did + parallels to Abyss |

## Sister packages

- `team_profiles/` — one `.md` per top-10 team (deep strategy reverse-engineering) + `profiles.json` (raw fingerprints)
- `battlecode_season_analysis_v3.html` — the combined interactive report (charts + tables)
- `game_stats_snapshot_v3.jsonl.gz` — full per-game stats (59k lines, includes eval curves)

## The five-line summary

1. Territory + biomass decide games; eval's `bodies` logit dominates everything.
2. Winners diverge by 20% of progress (+2.9 dragons); by 60% it's +12.8 — comebacks are rare (16% from <30%).
3. Suicide isn't death, it's conversion — the elite doctrine banks body into fed champions.
4. Sonar is 58% map-scan, 39% self-talk, 3.5% enemy contact — a signed-protocol mailing list, not radar.
5. The map picks the doctrine: marathon boards print feeding economies; corridor maps reward walls and kamikazes.
