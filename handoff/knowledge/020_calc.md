# calc — strategy deep dive

Rank-era elo ~2060 · 964 games analyzed (815 eval-scored) · win rate 76.5%

## Numbers

| metric | value |
|---|---|
| games | 964 |
| win rate | 76.5% |
| peak alive dragons | 48.2 |
| splits / game | 264.4 |
| suicides / game | 23.9 |
| deaths / game | 245.0 |
| sonar pings / action | 3.92 |
| pearls eaten / game | 212.0 |
| avg rounds | 361.0 |
| elimination rate | 50% |
| sprint share | 0.2% |
| side-B win rate | 78% |

## Death signature

| cause | share |
|---|---|
| hitWall | 57.6% |
| hitSelf | 0.2% |
| hitOtherBody | 11.9% |
| hitHeadToHead | 20.7% |
| noValidAction | 9.8% |

## Win-probability trajectory (eval engine, P(this team wins) by decile)

| decile | P(win) |
|---|---|
| 0% | 54.6% |
| 10% | 59.6% |
| 20% | 61.0% |
| 30% | 64.6% |
| 40% | 67.1% |
| 50% | 68.3% |
| 60% | 69.3% |
| 70% | 68.0% |
| 80% | 70.5% |
| 90% | 74.8% |

Endgame logit parts (mean over all its games, positive = ahead): bodies +5.38, ground +0.40, champion +0.42, fights +0.07, economy -0.04.

## Mid-game winners-gap (its winning-side feature deltas at 50% progress)

| feature | winner−loser |
|---|---|
| terr | +207.81 |
| total | +39.03 |
| eat | +17.43 |
| alive | +13.84 |
| lost_len | +9.08 |
| champ_enemy_d | +3.3 |
| pearls_near | +3.04 |
| deaths | +1.88 |

## Swarm shape (avg alive dragons per 5% of game)

`3.6 8.0 11.5 15.3 18.9 22.5 25.5 28.3 30.9 33.0 34.9 36.6 38.0 37.3 37.6 35.6 35.0 31.8 29.4 24.3`

## Maps

Best: Default 89% (92g), Devil 89% (101g), Trophy 86% (91g), Autarky 85% (103g), Queen Of Spades 85% (80g).  Worst: Slithery Fight 51% (89g), Prisoners Dilemma 69% (102g), Schooltime 69% (104g).

## Head-to-head vs elo≥1800 (most-played)

| opponent | W–L | n |
|---|---|---|
| wawow830 | 76–10 | 86 |
| Teto, run! | 74–6 | 80 |
| Cutlery | 27–38 | 65 |
| Just Keep Swimming | 58–2 | 60 |
| Z-A | 38–12 | 50 |
| C-- | 30–15 | 45 |
| Quant Merch Trader | 33–7 | 40 |
| w daniel ma | 30–4 | 34 |
| 3.14159265 | 16–14 | 30 |
| Peanut Butter | 19–11 | 30 |
| avid coders | 26–3 | 29 |
| bread first search | 19–7 | 26 |

## Era presence

| era | games |
|---|---|
| sep29 | 74 |
| sep30 | 792 |
| scrim | 98 |

## Strategy theory — the maximal swarm, controlled

calc fields the **biggest sustained swarm measured** (peak 48.2 alive — the only team consistently pushing past 40) and the best win rate of the top ten (76.4%). It pairs that mass with near-saturated sonar (3.92/action — the ceiling) and a wall-hugger's death profile (58% hitWall — it pushes boundaries like 3.14159265 but less suicidally).

Unlike the suicide school, calc keeps its dragons alive to occupy space (elim 51%, and it *also* wins at length at round 500). Its eval curve is the most dominant of the field: 0.55 → 0.75, monotone, the largest end-game spread — calc doesn't win knife fights, it wins by steadily out-classing the board. Mid-game feat gaps are all maximum-or-near: terr +208, total +39, alive +13.8 — it beats you on every axis at once rather than on one gimmick.

Weakness: Slithery Fight at 51% — the huge open farming map rewards marathon efficiency, and calc's crash-prone mass leaves segments on kelp there.
