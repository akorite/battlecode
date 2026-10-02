# cheji bt — strategy deep dive

Rank-era elo ~2081 · 1541 games analyzed (1168 eval-scored) · win rate 73.8%

## Numbers

| metric | value |
|---|---|
| games | 1541 |
| win rate | 73.8% |
| peak alive dragons | 42.6 |
| splits / game | 203.6 |
| suicides / game | 123.1 |
| deaths / game | 181.0 |
| sonar pings / action | 2.45 |
| pearls eaten / game | 270.0 |
| avg rounds | 314.0 |
| elimination rate | 60% |
| sprint share | 1.2% |
| side-B win rate | 76% |

## Death signature

| cause | share |
|---|---|
| hitWall | 0.0% |
| hitSelf | 0.1% |
| hitOtherBody | 3.9% |
| hitHeadToHead | 27.9% |
| noValidAction | 68.1% |

## Win-probability trajectory (eval engine, P(this team wins) by decile)

| decile | P(win) |
|---|---|
| 0% | 54.3% |
| 10% | 59.2% |
| 20% | 60.9% |
| 30% | 64.3% |
| 40% | 64.7% |
| 50% | 65.4% |
| 60% | 65.8% |
| 70% | 69.6% |
| 80% | 70.4% |
| 90% | 73.1% |

Endgame logit parts (mean over all its games, positive = ahead): bodies +4.72, ground +0.37, champion +0.43, fights +0.06, economy -0.04.

## Mid-game winners-gap (its winning-side feature deltas at 50% progress)

| feature | winner−loser |
|---|---|
| terr | +310.28 |
| total | +28.51 |
| eat | +17.21 |
| alive | +9.94 |
| pearls_near | +7.91 |
| lost_len | -4.14 |
| champ_enemy_d | +3.67 |
| deaths | -1.49 |

## Swarm shape (avg alive dragons per 5% of game)

`3.6 8.9 12.2 15.4 18.3 20.7 22.5 24.4 26.0 27.4 28.6 30.0 31.1 31.8 25.0 23.9 23.9 24.5 25.2 26.0`

## Maps

Best: Queen Of Spades 96% (141g), Default 91% (158g), Schooltime 90% (157g), Trophy 80% (156g), Devil 78% (147g).  Worst: Portals 48% (159g), Slithery Fight 48% (152g), Autarky 67% (161g).

## Head-to-head vs elo≥1800 (most-played)

| opponent | W–L | n |
|---|---|---|
| Kamikaze | 68–26 | 94 |
| fandagong | 70–10 | 80 |
| 龙虎豹 | 51–25 | 76 |
| forgot to mention | 34–31 | 65 |
| Drago et al | 42–23 | 65 |
| we love gru | 53–7 | 60 |
| Peanut Butter | 38–18 | 56 |
| Cutlery | 21–29 | 50 |
| Z-A | 44–5 | 49 |
| w daniel ma | 36–13 | 49 |
| wawow830 | 36–10 | 46 |
| Teto, run! | 34–6 | 40 |

## Era presence

| era | games |
|---|---|
| sep29 | 93 |
| sep30 | 1331 |
| scrim | 117 |

## Strategy theory — the territory banker

cheji bt runs the most complete **economic engine** on the ladder: 123 suicides/game + the highest pearl harvest of any team measured (270/game) + the highest territory differential of all teams at mid-game (+310 tiles, the largest feat gap in the dataset) + the shortest games (314 rounds) + the highest elimination rate (60%). This is a *terraforming* bot: it doesn't just feed a champion, it converts dragon mass into controlled space.

Its alive curve is unique — it peaks at 65% (31.8) like others, then **dips to ~24 and regrows to 26** by game's end. The swarm sacrifices itself mid-game and the survivors re-split into a fresher wave — a two-generation strategy: the first wave farms and dies into pearls, the second wave eats them and finishes the game.

It's also the only elite that visibly *sprints* (1.2% of moves — 4× anyone else) — bursts of speed to reach corpse-pearls or cut off lanes, paid for in segments it plans to suicide anyway. 73.8% win rate, second-best measured, with its only real weakness being portal-heavy maps (Portals 48%, Slithery Fight 48%) where wrapping lanes dissolve the territorial lock it builds.
