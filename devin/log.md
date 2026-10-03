# Submission + verdict log (autonomous ladder job)

## losssurvey lane — ladder loss-cause survey (2026-10-03)

Data window: last 100 battles returned by `battles?limit=100` (battle ids 937711..978868,
2026-10-03 06:02–17:26 UTC). API ignores pagination params (`before`/`offset`/`limit` all
return the same latest-100 window), so this is the max retrievable.

- 409 games total, **179 ranked** (W83 / L96 / D0), 230 unranked.
- Ranked splits by our submission: **abyss_v104 (live) W29/L30**, v101-revert W54/L66.
- Replays downloaded for all 96 ranked losses; metrics via `tooling/replay_metrics.py`
  (per-side: win, end, rounds, queen-death round/reason, eaten60, splits60, queenEnd,
  alive50/499, longest, total, ppt). Side identified via match `teamAId==351` — verified
  against replay `botA`/`botB` submission ids (96/96 match).
- No TLEs in any loss replay (0 dragonAction `tle` flags on our side).

### Loss buckets — abyss_v104 (30 ranked losses)

| bucket | n | share |
|---|---|---|
| B1 queen dead r0-5 (all Schooltime r1 hitSelf) | 6 | 20% |
| B2 queen dead r6-50 | 3 | 10% |
| B3 queen dead r51-200 (hunt/wall mid-game) | 13 | 43% |
| B4 queen dead r201+ (late) | 7 | 23% |
| B5 queen alive, outscored | 1 | 3% |

Queen-death causes on v104: hitHeadToHead 12, hitWall 9, hitSelf 8 (6 = Schooltime r1),
alive 1. 16/30 losses ended `teamEliminated` — and **every** teamEliminated loss had our
queen die first (mean qDeadRound ~101 across all 96 losses): queen death ⇒ cascade.

### Loss buckets — v101-revert (66 ranked losses, for trend)

B3 36, B4 15, B2 9, B6 4, B5 2. Causes: h2h 28, hitWall 23, hitOtherBody 6, hitSelf 3,
alive 6. **No r0-5 queen deaths** — the Schooltime r1 suicide is a v104 regression.

### Per-map ranked W/L (v104 era only, post-14:27 UTC)

| map | W | L | notes |
|---|---|---|---|
| Schooltime | 0 | 6 | every loss = queen hitSelf r1 |
| Trauma | 1 | 3 | |
| Stripes | 2 | 3 | |
| Tower Defense | 3 | 3 | |
| weakhold | 0 | 3 | |
| Queen Of Spades | 1 | 3 | |
| Autarky | 2 | 2 | |
| Around UNSW | 3 | 1 | |
| Australia | 2 | 1 | |
| Trophy | 1 | 1 | |
| Devil | 2 | 1 | |
| Portals | 2 | 1 | |
| Islands | 0 | 1 | |
| Prisoners Dilemma | 1 | 1 | |
| Default | 4 | 0 | |
| Maze | 2 | 0 | |
| Slithery Fight | 3 | 0 | |

### Per-map ranked W/L (full 179-game window, both submissions)

| map | W | L | loss qdead causes (top) | mean qDeadRound | mean eat60 gap |
|---|---|---|---|---|---|
| Schooltime | 2 | 11 | hitSelf 6, hitWall 3 | 100 | +5 |
| Tower Defense | 6 | 10 | h2h 7, hitWall 3 | 143 | +3 |
| weakhold | 2 | 8 | hitWall 8 | 70 | +9 |
| Around UNSW | 7 | 8 | hitWall 5, h2h 2 | 180 | +8 |
| Queen Of Spades | 3 | 7 | hitWall 3, h2h 4 | 88 | +18 |
| Trauma | 3 | 7 | h2h 2, hitWall 2, hitSelf 1 | 286 | +2 |
| Devil | 8 | 6 | h2h 5, hitSelf 1 | 55 | +59 |
| Stripes | 6 | 6 | h2h 5, hitWall 1 | 144 | +8 |
| Trophy | 7 | 5 | h2h 5 | 68 | +39 |
| Islands | 4 | 5 | h2h 2, hitOtherBody 1 | 147 | +38 |
| Slithery Fight | 5 | 5 | hitWall 2, hitOtherBody 2 | 300 | +174* |
| Australia | 3 | 4 | hitWall 2, h2h 2 | 129 | +20 |
| Autarky | 5 | 4 | h2h 3 | 86 | +47 |
| Portals | 8 | 3 | hitSelf 1 | 263 | +18 |
| Maze | 3 | 3 | h2h 1, hitOtherBody 1 | 190 | -2 |
| Default | 8 | 3 | hitOtherBody 1, h2h 2 | 104 | +6 |
| Prisoners Dilemma | 3 | 1 | hitWall 1 | 23 | +12 |

*Slithery Fight gap inflated by one blowout; median gap is ~10. (eat60 gap = opp eaten60 − ours;
positive = opponent ate more pearls by r60.)

### Per-opponent ranked W/L (full window)

| opponent | ~elo | W | L |
|---|---|---|---|
| so-lonely | 1432 | 30 | 30 |
| NeungzAI | 1527 | 7 | 13 |
| zach | 1521 | 4 | 11 |
| meowest | 1652 | 2 | 8 |
| I wanna go to CHINA | 1442 | 7 | 8 |
| Sponge(Albert and Bob) | 2192 | 0 | 5 |
| doofenshmirtz good incorporated | 1645 | 6 | 4 |
| EternalWisdom | 1641 | 2 | 3 |
| Mr Aura | 1411 | 2 | 3 |
| Ron Squad | 1478 | 3 | 2 |
| bsg | 1352 | 3 | 2 |
| 天天开心 :( | 1647 | 3 | 2 |
| 404 Not Found | 1367 | 3 | 2 |
| Human Learning | 1382 | 4 | 1 |
| Low Cortisol | 1455 | 4 | 1 |
| LOOPING THE FUNCTIONS | 1272 | 3 | 1 |

By opp elo band: 1200s W3/L1, 1300s W13/L7, 1400s W45/L45, 1500s W9/L21,
1600s W13/L17, 2100s W0/L5. Mean opp elo on wins 1467 vs losses 1529.
Net elo change over window: −78.

v104-era per-opponent: so-lonely W13/L12 (~1432), Sponge W0/L5 (~2192),
meowest W0/L5 (~1653), bsg W3/L2, 天天开心 :( W3/L2, 404 Not Found W3/L2,
Low Cortisol W4/L1, LOOPING THE FUNCTIONS W3/L1.

### Top-5 loss buckets (all 96 ranked losses, ranked by count)

1. **Queen dead mid-game r51-200: 49** (h2h 28-ish, hitWall ~14, hitSelf ~4)
2. **Queen dead late r201+: 26** (consolidation/endgame queen loss)
3. **Queen dead early r6-50: 12**
4. **Queen dead r0-5: 6** — all Schooltime r1 hitSelf, all on v104
5. **Queen alive, outscored: 7** (only 3 with r60 pearl gap >10)

Pearl starvation (eaten60 gap >10) co-occurs in 48/96 losses but is a contributing
factor, not the proximate kill — queen death is present in 89/96 losses and strictly
precedes all 38 teamEliminated finishes.

### v104 loss detail (all 30)

See `ladder_data/loss_merged.json` (gitignored data; reproduced in lane note). Replays
cached in `ladder_replays/<gameId>.replay` (local only), index `ladder_replays/index.jsonl`.
