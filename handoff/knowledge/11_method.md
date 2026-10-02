# Method, sources & how to use the data

## Pipeline

1. **Collect** — `GET /games?teams={id}&page={n}` on game.battlecode.au; embedded SvelteKit objects give {id, teams, elo, map, at, hasReplay}. Swept ~170 teams × up to 80 pages each → 80,940 unique matches.
2. **Download** — `GET /api/matches/{id}/replay` → 302 → signed R2 URL → gzip'd packed Cap'n Proto. ~0.7MB each, ~58GB total, zero failures.
3. **Decode** — hand-rolled packed-Cap'nProto depacker (no pycapnp needed) + schema pulled from the site's own viewer bundle. ~1.1s/game CPU-bound.
4. **Analyze** — per team per game: ~60 counters (actions by type, splits, suicides, deaths by cause, sonar pings by hit-kind, pearls eaten, instruction budget, timeouts) + per-round alive history + per-round split/death/sonar histograms (20 buckets).
5. **Evaluate** — xCirno1/battlecode-eval integrated via importlib (module loads, weights loaded manually): P(team A wins) every 50 rounds + 23-feature snapshots at 25/50/75% + end-game logit decomposition.

## Coverage

| Item | Count |
|---|---|
| Unique replays | 80,940 (~58 GB) |
| Games analyzed | 59,544+ (loop running) |
| Eval-scored | 25k+ |
| Teams | ~952 on ladder; ~170 swept |
| Window | Sep 21 – Oct 1, 2026 |

Eval coverage policy: all pre-Sep-29 games + all games involving top-10 teams + a 1-in-8 sample of the rest — biased toward high-elo and early-era.

## Data files

- `game_stats_snapshot_v3.jsonl.gz` — one JSON per line per game: `id, a, b{name,elo}, winner, map, rounds, endReason, teams{A,B}{splits,suicides,deaths,death_*,sonar,sonar_*,actions,moves,sprints,instr,pearlsEaten,...}, dragonHistory{A,B}[per-round alive], eval[[round,P]...], feat{r25,r50,r75}, parts_end{bodies,ground,champion,fights,economy,side}`.
- `team_profiles/profiles.json` — pre-computed fingerprints for the top 10 (curves, maps, h2h, parts).
- `team_profiles/NN_*.md` — per-team deep dives.
- `deep_dive/*.md` — this package.

## Known caveats

- `sui/g` figures are per-team per-game (a "both teams" number is ~2×).
- Era aggregates have a composition caveat: later eras are denser in high-elo games; per-team era trends control for this.
- Sonar "enemy hit" rates undercount true contact — a ray that hits kelp 1 tile before an enemy reports kelp.
- The 952-team elo comes from battlecode-stats' data branch; the live leaderboard showed 170 teams at scrape time.

## OSS sources

- `overyonder/the-loong-game` — 18-post strategy diary (sonar protocol, roles, coil+feed, "splitting does most of the work")
- `Lachy-Dauth/battlecode-stats` — unofficial stats + full elo history
- `SongyuQi-Francisco/battlecode-abyss-framework` — shared C++ bot (common Params)
- `xCirno1/battlecode-eval` — the eval engine

## The loop

A background daemon re-runs collect → download → analyze ~every 10 min; new games (post-freeze autoscrims, livestream matches) accumulate. Snapshot this session: 59.5k analyzed at file-generation time.
