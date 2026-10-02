# Stockfish — strategy deep dive

Rank-era elo ~2092 · 1094 games analyzed (936 eval-scored) · win rate 71.5%

## Numbers

| metric | value |
|---|---|
| games | 1094 |
| win rate | 71.5% |
| peak alive dragons | 42.5 |
| splits / game | 254.3 |
| suicides / game | 0 |
| deaths / game | 236.0 |
| sonar pings / action | 3.74 |
| pearls eaten / game | 213.0 |
| avg rounds | 365.0 |
| elimination rate | 52% |
| sprint share | 0.3% |
| side-B win rate | 72% |

## Death signature

| cause | share |
|---|---|
| hitWall | 32.7% |
| hitSelf | 37.3% |
| hitOtherBody | 10.8% |
| hitHeadToHead | 19.2% |
| noValidAction | 0.0% |

## Win-probability trajectory (eval engine, P(this team wins) by decile)

| decile | P(win) |
|---|---|
| 0% | 53.5% |
| 10% | 57.5% |
| 20% | 62.7% |
| 30% | 63.3% |
| 40% | 64.8% |
| 50% | 62.9% |
| 60% | 65.7% |
| 70% | 69.4% |
| 80% | 73.1% |
| 90% | 71.2% |

Endgame logit parts (mean over all its games, positive = ahead): bodies +4.09, ground +0.19, champion +0.22, fights +0.02, economy -0.02.

## Mid-game winners-gap (its winning-side feature deltas at 50% progress)

| feature | winner−loser |
|---|---|
| terr | +175.59 |
| total | +38.01 |
| alive | +10.03 |
| eat | +7.09 |
| pearls_near | +2.8 |
| big5 | +2.32 |
| champ_enemy_d | +1.99 |
| lost_len | +1.63 |

## Swarm shape (avg alive dragons per 5% of game)

`3.6 8.9 13.0 17.5 21.4 24.5 26.9 29.0 30.6 32.1 33.4 30.7 30.1 29.6 29.4 26.9 24.8 23.4 22.3 22.0`

## Maps

Best: Portals 87% (109g), Schooltime 82% (120g), Trauma 80% (109g), Slithery Fight 78% (105g), Default 75% (114g).  Worst: Prisoners Dilemma 52% (111g), Autarky 57% (115g), Queen Of Spades 63% (102g).

## Head-to-head vs elo≥1800 (most-played)

| opponent | W–L | n |
|---|---|---|
| 龙虎豹 | 46–19 | 65 |
| forgot to mention | 24–36 | 60 |
| SilverSamurai | 37–13 | 50 |
| wawow830 | 37–11 | 48 |
| we love gru | 46–0 | 46 |
| Cutlery | 17–28 | 45 |
| w daniel ma | 34–10 | 44 |
| bread first search | 26–14 | 40 |
| y | 34–1 | 35 |
| fandagong | 28–2 | 30 |
| Team SKKU | 9–21 | 30 |
| avid coders | 24–6 | 30 |

## Era presence

| era | games |
|---|---|
| sep29 | 6 |
| sep30 | 934 |
| scrim | 154 |

## Strategy theory — the sensor platform

Stockfish saturates the sonar channel harder than almost anyone (3.83 pings/action — 96% of theoretical max) and pairs it with zero suicides and a hard information-age build. The cost shows in its death mix: 37% self-collisions + 33% wall deaths — it spends the vision budget knowing where everything is, then drives into it anyway at speed. This is a bot whose *perception* is elite and whose *steering* is merely very good.

The eval curve is the strongest steady climb in the set (0.54→0.71, monotone, no mid-game dip): Stockfish accumulates advantage continuously rather than in a phase. Its big5 differential (+2.3 at mid-game) shows its top-5 dragons specifically dominate — champion-quality dragons kept in a coordinated pack rather than isolated. On Portals it's nearly unbeatable (87%): sonar rays traverse portals in this ruleset, so its information advantage compounds on the map designed to hide things.
