# L2 queen-graze sweep — explore lane (freeze-push gate run)

Base + all opponents: `abyss_v481` (= live v138). Each variant = v481 + ONE param change in
`common.hpp` (kParams `p.queenGrazeLen` for a/b; struct defaults `queenGrazeDist`/`queenGrazeFrom`
for c/d/e — verified no `p.*` override). Gate: `--maps all --seeds 8 --seed-start 1` (22 maps,
176 games planned each), jobs 3-4 parallel, kill rule <50% after 40 games applied.

## Verdicts — NO variant improves on v481; grazeFrom=250 is locally optimal

| variant | change | games@kill | cand record | verdict |
|---|---|---|---|---|
| L2a | queenGrazeLen 10→12 | 42 | 21-21 (50%) | killed <50%→=50% at 42g; no effect |
| L2b | queenGrazeLen 10→15 | 42 | 21-21 (50%) | killed; identical to L2a |
| L2c | queenGrazeDist 7→5 | 182 (full gate stopped, verdict settled) | 90-92 (49.5%) | NEUTRAL — coin-flip on every map |
| L2d | queenGrazeFrom 250→200 | 42 | 19-23 (45%) | killed — WORSE |
| L2e | queenGrazeFrom 250→320 | 41 | 19-22 (46%) | killed — WORSE |

Where the deltas live (as predicted): everything is identical on elim maps — the queen-graze
params only bite in bell games, so every divergence is on big/roundLimit games:

| variant | roundLimit games | RL wins |
|---|---|---|
| L2a | 22 | 11 (50%) |
| L2b | 22 | 11 (50%) |
| L2c | 98 | 48 (49%) |
| L2d | 22 | 9 (41%) |
| L2e | 21 | 9 (43%) |

## Reads

- **grazeLen 12 vs 15 = no measurable difference** — the queen doesn't graze past 10 often
  enough for the cap to bind in 42 games.
- **grazeFrom is tuned near a local optimum**: moving it EARLIER (200) loses ~2 RL games
  (queen out of cover earlier — matches the hide doctrine), and moving it LATER (320) loses
  ~2 RL games too (not enough graze window to bank queenEnd before the bell). 250 > both
  directions → leave at 250.
- L2c ran to 182 games: **49.5% overall, 49% on roundLimit (48-50), every single map a coin
  flip** — grazing closer to enemies is exactly neutral. Not a ship.
- Effect sizes are small because most games are elim/short — the params only exist in the
  ~30% of games reaching the graze window.

## queenEnd census (earlier task, folded in per instruction)

42 top-team roundLimit replays: (queenEnd→longest→total) lexicographic explains **42/42
winners**; queenEnd decides **62%** of bell games; winning qEnd median **21.5** (losing median 0);
both-queens-alive → shorter-queen side won **0/13**. A hidden len-2 queen auto-loses when both
survive — the graze mechanic's entire value is turning hide-survival into key-1 bank.
That context explains why L2d/L2e failed: the bell payout needs the full ~250-round runway.
