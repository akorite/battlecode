# Sponge(Albert and Bob) — strategy deep dive

Rank-era elo ~2061 · 529 games analyzed (441 eval-scored) · win rate 59.0%

## Numbers

| metric | value |
|---|---|
| games | 529 |
| win rate | 59.0% |
| peak alive dragons | 37.3 |
| splits / game | 226.2 |
| suicides / game | 29.9 |
| deaths / game | 215.0 |
| sonar pings / action | 0.86 |
| pearls eaten / game | 174.0 |
| avg rounds | 355.0 |
| elimination rate | 48% |
| sprint share | 0.3% |
| side-B win rate | 62% |

## Death signature

| cause | share |
|---|---|
| hitWall | 37.0% |
| hitSelf | 13.2% |
| hitOtherBody | 11.2% |
| hitHeadToHead | 24.7% |
| noValidAction | 13.9% |

## Win-probability trajectory (eval engine, P(this team wins) by decile)

| decile | P(win) |
|---|---|
| 0% | 52.7% |
| 10% | 52.3% |
| 20% | 52.2% |
| 30% | 53.7% |
| 40% | 53.8% |
| 50% | 53.7% |
| 60% | 54.6% |
| 70% | 53.1% |
| 80% | 51.3% |
| 90% | 57.4% |

Endgame logit parts (mean over all its games, positive = ahead): bodies +1.79, ground +0.06, champion +0.08, fights -0.00, economy -0.00.

## Mid-game winners-gap (its winning-side feature deltas at 50% progress)

| feature | winner−loser |
|---|---|
| terr | +47.33 |
| total | +12.51 |
| lost_len | -4.84 |
| pearls_near | +2.9 |
| eat | -2.36 |
| deaths | -1.81 |
| big5 | +1.78 |
| alive | +1.61 |

## Swarm shape (avg alive dragons per 5% of game)

`3.6 8.3 11.6 15.1 18.1 20.9 23.0 24.4 25.8 26.1 26.5 26.6 27.3 26.8 25.9 24.3 22.1 19.0 17.4 16.2`

## Maps

Best: Devil 82% (56g), Portals 74% (54g), Prisoners Dilemma 60% (48g), Slithery Fight 59% (51g), Schooltime 55% (58g).  Worst: Trophy 47% (51g), Default 48% (52g), Trauma 53% (53g).

## Head-to-head vs elo≥1800 (most-played)

| opponent | W–L | n |
|---|---|---|
| 3.14159265 | 10–30 | 40 |
| Computers | 25–15 | 40 |
| w daniel ma | 25–10 | 35 |
| Cutlery | 18–16 | 34 |
| Cache me outside | 10–19 | 29 |
| Quant Merch Trader | 20–5 | 25 |
| forgot to mention | 7–13 | 20 |
| Team SKKU | 12–8 | 20 |
| WeHaveQuizzes | 14–6 | 20 |
| y | 17–3 | 20 |
| cheji bt | 9–11 | 20 |
| SSS | 8–10 | 18 |

## Era presence

| era | games |
|---|---|
| sep30 | 414 |
| scrim | 115 |

## Strategy theory — the defensive finisher

Sponge is the inverse of the field's aggression: lowest sonar of any top team measured (0.86/action — a fifth of the elite norm), mid-tier splits, mid-tier deaths, and an eval curve that **stays dead flat at ~0.52–0.55 until the 80% mark** before ticking to 0.57 at the end. Sponge doesn't accumulate a mid-game lead — its feat differentials at 50% are *negative* (out-eaten −2.4, fewer pearls near − wait, pearls_near +2.9 positive but eat −2.4, lost_len −4.8 meaning it loses less length, deaths −1.8).

Read: Sponge survives the mid-game on defense and converts at the 500-round bell — its games are decided on longest-dragon scoring, not mid-game dominance. 59% win rate (lowest of the ten) but consistent: it never blows up early, never throws a lead, and on Devil it's an 82% monster — tight maps where its compact swarm can't be flanked. The right mental model is a spoiler bot: it drags every game to the judge's tiebreak criteria and wins on discipline.
