# forgot to mention — strategy deep dive

Rank-era elo ~2070 · 1357 games analyzed (1076 eval-scored) · win rate 69.8%

## Numbers

| metric | value |
|---|---|
| games | 1357 |
| win rate | 69.8% |
| peak alive dragons | 40.7 |
| splits / game | 277.8 |
| suicides / game | 205.6 |
| deaths / game | 261.0 |
| sonar pings / action | 1.66 |
| pearls eaten / game | 216.0 |
| avg rounds | 334.0 |
| elimination rate | 54% |
| sprint share | 0.4% |
| side-B win rate | 77% |

## Death signature

| cause | share |
|---|---|
| hitWall | 0.0% |
| hitSelf | 0.2% |
| hitOtherBody | 1.8% |
| hitHeadToHead | 19.4% |
| noValidAction | 78.7% |

## Win-probability trajectory (eval engine, P(this team wins) by decile)

| decile | P(win) |
|---|---|
| 0% | 51.8% |
| 10% | 56.5% |
| 20% | 57.4% |
| 30% | 59.0% |
| 40% | 58.6% |
| 50% | 57.4% |
| 60% | 57.5% |
| 70% | 59.5% |
| 80% | 61.7% |
| 90% | 66.6% |

Endgame logit parts (mean over all its games, positive = ahead): bodies +3.73, ground +0.28, champion +0.31, fights +0.04, economy -0.02.

## Mid-game winners-gap (its winning-side feature deltas at 50% progress)

| feature | winner−loser |
|---|---|
| terr | +142.29 |
| eat | +18.78 |
| total | +14.65 |
| lost_len | +11.56 |
| alive | +6.75 |
| deaths | +4.36 |
| champ_enemy_d | +3.02 |
| champ_ally_d | -1.38 |

## Swarm shape (avg alive dragons per 5% of game)

`3.6 9.7 13.3 16.8 20.1 22.9 25.0 26.7 28.0 28.9 29.9 30.3 30.9 31.0 31.6 27.0 23.4 22.3 21.3 20.7`

## Maps

Best: Prisoners Dilemma 82% (136g), Devil 77% (132g), Autarky 77% (141g), Queen Of Spades 76% (127g), Trophy 74% (133g).  Worst: Portals 48% (134g), Default 54% (139g), Slithery Fight 68% (141g).

## Head-to-head vs elo≥1800 (most-played)

| opponent | W–L | n |
|---|---|---|
| SSS | 51–49 | 100 |
| Cache me outside | 53–43 | 96 |
| 龙虎豹 | 69–16 | 85 |
| Cutlery | 37–43 | 80 |
| Peanut Butter | 53–17 | 70 |
| cheji bt | 31–34 | 65 |
| Stockfish | 36–24 | 60 |
| Z-A | 36–9 | 45 |
| w daniel ma | 36–9 | 45 |
| fandagong | 38–7 | 45 |
| 3.14159265 | 18–25 | 43 |
| bread first search | 26–16 | 42 |

## Era presence

| era | games |
|---|---|
| sep29 | 40 |
| sep30 | 1152 |
| scrim | 165 |

## Strategy theory — the suicide engine

`forgot to mention` is the purest expression of the **corpse-feeding economy**: 206 deliberate suicides per game — the most on the ladder — paired with the #2 elo's 69.8% win rate. Its deaths mirror Cutlery's profile (79% boxed-in, 0% wall) — it *also* fills territory until saturation — but instead of letting boxed-in dragons die passively, it **converts them**: a saturated length-L dragon becomes ⌈L/2⌉ pearls exactly where it stood, and the champion harvests them.

This is the coil-and-feed doctrine the Discord was asking how to mimic. The economics are why it wins: every dead dragon refunds half its body as food, so its real efficiency is ~2× the naive — pearls eaten 216/game while spending 206 dragons' worth of segments as deposits. The eval signature confirms it: **+11.6 lost_len advantage at mid-game** (it *loses more* length to deaths than opponents and still wins) and champion_ally_d −1.4 — the champion rides inside its own swarm.

It barely talks: 1.66 pings/action, the lowest of the suicide-school teams, because the strategy is mechanical — expand, saturate, detonate, feed. Games end fastest of any elite (334 rounds avg, 54% eliminations): the swarm collapse is violent on both sides, and it wins the exchange. Only Portals beats it (48%) — the map where wrapping lanes break its saturation pattern.
