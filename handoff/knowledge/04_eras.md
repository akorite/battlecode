# Era analysis — how the meta evolved Sep 26 → Oct 1

*Era buckets: E1 = Sep 26–28, E2 = Sep 29, E3 = Sep 30 pre-freeze, E4 = Sep 30 23:00→Oct 1 03:00 (autoscrim window). Counts are team-games (2 per match).*

## The meta table

| Era | Team-games | Peak alive | Splits/g | Suicides/g | Sonar/action | Deaths/g | Pearls/g | Elim% | Side-B% |
|---|---|---|---|---|---|---|---|---|---|
| E1 (Sep 26–28) | 3,276 | 26.6 | 188 | 19.5 | 1.66 | 173 | 130 | 37% | 49% |
| E2 (Sep 29) | 9,348 | 31.0 | 227 | 18.2 | 1.99 | 208 | 155 | 37% | 52% |
| E3 (Sep 30) | 51,910 | 34.6 | 244 | 20.3 | 2.45 | 225 | 173 | 44% | 59% |
| E4 (autoscrim) | 14,226 | 33.6 | 240 | 23.6 | 2.48 | 221 | 168 | 40% | 48% |

## The direction of the week

In ~5 days the ladder moved: **swarm +30%, sonar +50%, deaths +30%, pearls +33%, eliminations +18%**. Every pointer points the same way — the meta was converging on coordinated mass + conversion, and it was converging *fast*.

The Sep 25 pearl-schedule randomization sits just before our densest coverage. Its fingerprint is the E1→E2 jump: teams that had hardcoded spawn schedules lost their edge overnight and the survivors were the ones already fighting for space — splitting and sonar both jumped in lockstep.

## Tier × era matrix (per-game rates)

| Tier | E1 | E2 | E3 | E4 |
|---|---|---|---|---|
| Shark | 91g pk42 sui16 son3.2 d250 | 2,314g pk41 sui47 son2.8 d246 | 25,598g pk39 sui26 son2.7 d242 | 4,151g pk38 sui23 son2.9 d243 |
| Swordfish | 2,001g pk34 sui56 son2.6 d223 | 14,951g pk34 sui30 son2.4 d236 | 44,165g pk34 sui21 son2.4 d228 | 12,955g pk35 sui30 son2.6 d235 |
| Tunafish | 1,799g pk21 sui6 son0.7 d154 | 2,826g pk22 sui4 son1.2 d165 | 4,966g pk21 sui6 son1.5 d145 | 2,630g pk23 sui7 son1.4 d149 |
| Shrimp | 221g pk25 sui29 son0.4 d151 | 74g pk20 sui72 son2.8 d90 | 180g pk12 sui2 son1.0 d48 | 70g pk23 sui0 son0.1 d116 |
| Plankton | — | 15g pk14 sui0 son0.3 d143 | 81g pk21 sui0 son0.7 d181 | — |

Two striking reads:

1. **Sharks already knew.** In E1, Sharks were running 42-peak swarms with 3.2 sonar — roughly the final-state numbers. The week's "evolution" is mostly Swordfish and Tunafish *catching up* to a meta the top had already found. Shark suicides actually *fell* (47 → 23) once the novelty wore off — they tried the corpse economy and kept it selectively.
2. **Tunafish never evolved.** Flat ~21-23 peak, ~6 suicides, ~1.4 sonar across every era. The tier gap is not a knowledge gap that closed — it's an architecture gap that persisted.

## The submission-freeze effect

E4 is post-freeze (bots immutable) — a controlled sample of final-strategy vs final-strategy. Side-B advantage collapses back to 48% (from 59%) once the field is all frozen final builds — suggesting the mid-E3 spike was matchup-rotation noise, not a structural shift. Suicide rate ticks up (23.6/g — season high) — the corpse economy was the meta at freeze.

## Per-team era notes

| Team | Games by era | Pattern |
|---|---|---|
| Cutlery | E1 31 / E2 181 / E3 1,143 / E4 110 | climbed through E3 consolidation |
| forgot to mention | E1 45 / E2 241 / E3 976 / E4 155 | suicide doctrine refined mid-season |
| cheji bt | E1 38 / E2 297 / E3 1,078 / E4 173 | two-wave strategy solidified late |
| calc | E1 22 / E2 155 / E3 722 / E4 70 | peak swarm achieved in E3 |
| SSS | E1 14 / E2 142 / E3 601 / E4 75 | efficiency approach unchanged |

## Reading for your own bot

The meta was still moving at freeze — nobody found the optimum. The safest bet for next season is whatever the E4 equilibrium was: ~38-peak swarm, ~2.7-2.9 sonar saturation, selective suicide (~23-30/g for Sharks), champion-feeding endgame.
