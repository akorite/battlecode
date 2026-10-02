# Cache me outside — strategy deep dive

Rank-era elo ~2066 · 1244 games analyzed (1057 eval-scored) · win rate 69.3%

## Numbers

| metric | value |
|---|---|
| games | 1244 |
| win rate | 69.3% |
| peak alive dragons | 43.2 |
| splits / game | 332.6 |
| suicides / game | 0 |
| deaths / game | 312.0 |
| sonar pings / action | 0.27 |
| pearls eaten / game | 235.0 |
| avg rounds | 363.0 |
| elimination rate | 49% |
| sprint share | 0.2% |
| side-B win rate | 76% |

## Death signature

| cause | share |
|---|---|
| hitWall | 2.8% |
| hitSelf | 62.9% |
| hitOtherBody | 18.5% |
| hitHeadToHead | 15.9% |
| noValidAction | 0.0% |

## Win-probability trajectory (eval engine, P(this team wins) by decile)

| decile | P(win) |
|---|---|
| 0% | 53.1% |
| 10% | 60.9% |
| 20% | 61.3% |
| 30% | 60.8% |
| 40% | 61.6% |
| 50% | 60.4% |
| 60% | 62.7% |
| 70% | 64.0% |
| 80% | 65.4% |
| 90% | 68.0% |

Endgame logit parts (mean over all its games, positive = ahead): bodies +2.79, ground +0.27, champion +0.24, fights +0.09, economy -0.03.

## Mid-game winners-gap (its winning-side feature deltas at 50% progress)

| feature | winner−loser |
|---|---|
| terr | +120.96 |
| lost_len | +21.13 |
| total | +21.1 |
| eat | +12.66 |
| alive | +9.27 |
| pearls_near | +5.29 |
| deaths | +3.94 |
| champ_enemy_d | +1.77 |

## Swarm shape (avg alive dragons per 5% of game)

`3.6 9.9 14.6 18.8 22.1 24.7 26.9 28.4 30.2 31.2 32.1 31.8 31.7 31.3 31.3 31.1 30.8 30.5 30.5 27.3`

## Maps

Best: Trauma 91% (123g), Prisoners Dilemma 77% (133g), Default 74% (144g), Autarky 73% (128g), Queen Of Spades 72% (94g).  Worst: Devil 54% (136g), Trophy 57% (129g), Schooltime 62% (137g).

## Head-to-head vs elo≥1800 (most-played)

| opponent | W–L | n |
|---|---|---|
| Team SKKU | 74–27 | 101 |
| forgot to mention | 43–53 | 96 |
| 龙虎豹 | 59–16 | 75 |
| Peanut Butter | 50–17 | 67 |
| SHINK AI 6500 | 42–18 | 60 |
| C-- | 36–9 | 45 |
| Cutlery | 22–23 | 45 |
| fandagong | 36–4 | 40 |
| 中国必须人能飞😡 | 25–11 | 36 |
| SilverSamurai | 24–11 | 35 |
| w daniel ma | 29–5 | 34 |
| 3.14159265 | 15–16 | 31 |

## Era presence

| era | games |
|---|---|
| sep26_28 | 2 |
| sep29 | 48 |
| sep30 | 1044 |
| scrim | 150 |

## Strategy theory — the chaos biomass

Cache me outside is the ladder's great paradox: the **lowest sonar usage measured** (0.27 pings/action — ~7% of cap), zero suicides, 63% of its deaths are self-collisions (rams its own swarm constantly) — and a 69% win rate. How? Its alive curve is unique: after reaching ~31 dragons at 55% it **never declines** — flat ~31 through 95% of the game. Where every other team's swarm bleeds away, Cache me outside's persists.

Theory: a pure *biomass engine*. It grows continuously (332 splits/g — second highest), pathing is greedy-local (hence self-collision — dragons don't yield to each other, they just crash and respawn through the corpse-pearl cycle), and there's no coordination to sabotage. 310 deaths/game with 63% self-kill is not waste here — it's the churn that recycles segments into pearls inside its own swarm mass, an *accidental* version of the suicide economy other teams do deliberately.

It beats forgot to mention head-to-head 53–43 and smashed Team SKKU 74–27 — the mass simply outlasts coordinated opponents. Its blind spot is the same: no sonar means it can't hunt; it wins by being unkillable-in-aggregate. Worst maps are the tight ones again (Devil 54%).
