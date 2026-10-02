# Cutlery — strategy deep dive

Rank-era elo ~2134 · 1406 games analyzed (1194 eval-scored) · win rate 70.1%

## Numbers

| metric | value |
|---|---|
| games | 1406 |
| win rate | 70.1% |
| peak alive dragons | 40.3 |
| splits / game | 462.1 |
| suicides / game | 0 |
| deaths / game | 251.0 |
| sonar pings / action | 2.34 |
| pearls eaten / game | 216.0 |
| avg rounds | 363.0 |
| elimination rate | 48% |
| sprint share | 0.5% |
| side-B win rate | 74% |

## Death signature

| cause | share |
|---|---|
| hitWall | 0.2% |
| hitSelf | 0.2% |
| hitOtherBody | 2.3% |
| hitHeadToHead | 19.1% |
| noValidAction | 78.2% |

## Win-probability trajectory (eval engine, P(this team wins) by decile)

| decile | P(win) |
|---|---|
| 0% | 51.1% |
| 10% | 53.9% |
| 20% | 55.7% |
| 30% | 56.4% |
| 40% | 56.6% |
| 50% | 59.0% |
| 60% | 62.4% |
| 70% | 65.1% |
| 80% | 68.7% |
| 90% | 69.1% |

Endgame logit parts (mean over all its games, positive = ahead): bodies +3.46, ground +0.21, champion +0.20, fights +0.01, economy -0.02.

## Mid-game winners-gap (its winning-side feature deltas at 50% progress)

| feature | winner−loser |
|---|---|
| terr | +148.39 |
| total | +23.4 |
| eat | +14.43 |
| alive | +4.68 |
| lost_len | +4.56 |
| pearls_near | +3.75 |
| deaths | +2.58 |
| champ_enemy_d | +2.24 |

## Swarm shape (avg alive dragons per 5% of game)

`3.6 9.0 12.8 16.6 20.2 22.8 24.8 26.1 26.8 27.6 28.6 29.0 29.3 29.2 27.0 24.7 22.6 21.5 20.5 19.2`

## Maps

Best: Autarky 84% (146g), Schooltime 80% (152g), Trophy 78% (133g), Slithery Fight 77% (148g), Portals 74% (137g).  Worst: Devil 54% (131g), Prisoners Dilemma 60% (143g), Queen Of Spades 63% (138g).

## Head-to-head vs elo≥1800 (most-played)

| opponent | W–L | n |
|---|---|---|
| Kamikaze | 65–30 | 95 |
| forgot to mention | 43–37 | 80 |
| calc | 38–27 | 65 |
| we love gru | 48–2 | 50 |
| 龙虎豹 | 33–17 | 50 |
| cheji bt | 29–21 | 50 |
| 3.14159265 | 29–19 | 48 |
| avid coders | 39–7 | 46 |
| Cache me outside | 23–22 | 45 |
| Team SKKU | 37–8 | 45 |
| Stockfish | 28–17 | 45 |
| Check Raise | 22–18 | 40 |

## Era presence

| era | games |
|---|---|
| sep29 | 100 |
| sep30 | 1161 |
| scrim | 145 |

## Strategy theory — the suffocation web

Cutlery wins by **out-producing everyone**: 462 splits per game is the highest measured anywhere — nearly double the field's ~240. The philosophy reads as *maximal expansion, minimal risk-taking*: dragons replicate relentlessly into every pocket of space, weave a dense interleaved web, and simply refuse to die to anything except their own crowding — **78% of its dragon deaths are noValidAction** (boxed in), versus ~13% for the average team. hitWall is a flat 0.0: its movement code never lets a dragon touch kelp, and head-to-head trades (19%) are accepted only on its terms.

The tell-tale is what it *doesn't* do: no suicides (0.0 across 1,400+ games), moderate sonar (2.34/action — coordination, not omniscience), almost no sprinting. It converts CPU budget into breadth-first claim-staking. When dragons get boxed in — the natural consequence of saturating a region — they die and drop pearls inside already-owned territory, feeding the swarm that replaced them. The mid-game eval gap is the classic Cutlery pattern: **+148 tiles of territory** at 50% with only modest alive advantage (+4.7) — its dragons are spread thin across space rather than clustered.

Watch its alive curve: it peaks later than everyone else (~60% mark, 29.3 dragons) and stays high — the web keeps replacing losses until the board is literally full. Its worst maps are Devil (54%) and Prisoners Dilemma (60%) — tight maps where its web chokes itself faster than it chokes the opponent; its best are the open/structured maps (Autarky 84%, Schooltime 80%).
