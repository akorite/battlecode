# How dragons die + the sonar economy

## Death causes — global mix

Across 59,544 games, per team per game (~220 deaths):

| Cause | Global share | What it means |
|---|---|---|
| hitWall | ~30% | kelp contact — the map's kill floor |
| hitSelf | ~24% | own body — crowding/churn |
| hitHeadToHead | ~21% | mutual kills — the kamikaze market |
| hitOtherBody | ~12% | ran into enemy body |
| noValidAction | ~13% | boxed in — saturation marker |

## Team death signatures

A team's death mix is its fingerprint — the single most diagnostic stat:

| Team | hitWall | hitSelf | hitBody | h2h | boxed-in | reading |
|---|---|---|---|---|---|---|
| Cutlery | 0.4% | 1.3% | 4.9% | 18.9% | **74.6%** | dies only by saturation |
| forgot | 0.4% | 1.2% | 4.4% | 15.0% | **78.7%** | same + deliberate suicide on top |
| cheji bt | 1.3% | 1.9% | 3.2% | 15.1% | **78.2%** | boxed-in + suicide loop |
| Cache | 8.5% | **63.0%** | 15.2% | 9.5% | 3.8% | rams itself constantly |
| ddabap | 7%* | ~65%* | — | — | — | self-rammer |
| 3.14159265 | **60.9%** | 8.6% | 4.8% | 9.7% | 15.5% | wall-pusher |
| calc | **57.6%** | 10.4% | 9.1% | 14.4% | 8.3% | wall-pusher |
| zitian | ~51% | — | — | — | — | wall-rider |
| SSS | 0.6% | 5.3% | 4.6% | 25.9% | 13.7% | cleanest — dies fighting |
| PPP | 33.5% | 25.9% | 11.9% | 14.7% | 13.8% | over-extension chaos |
| Sponge | 13.6% | 24.7% | 16.0% | 21.7% | 23.8% | attrition profile |

*ddabap shares approximate from lower-res table.

**The clean split:** suicide-school teams die ~78% boxed-in (their only deaths are saturation+deliberate), wall-pushers die ~58-61% on kelp, biomass teams die on themselves (~63%), and only SSS dies primarily in combat (26% h2h).

## The sonar economy

### Composition — who the channel serves

Globally: **kelp 58%, allies 39%, enemies 3.5%.** Sonar is a map-scanner and a mailing list, not a radar.

| Map | kelp | ally | enemy | note |
|---|---|---|---|---|
| Default | 51% | 40% | 8.9% | most enemy contact |
| Trophy | 37% | 54% | 9.1% | densest self-traffic |
| Trauma | 75% | 24% | 0.7% | open, few contacts |
| Portals | 64% | 36% | 0.0% | rays wrap through portals, never touch |
| Queen Of Spades | 67% | 27% | 6.4% | lanes |
| Slithery Fight | 54% | 45% | 1.4% | dense but no enemy contact |
| Devil | 50% | 47% | 3.2% | compact war |
| Prisoners Dilemma | 56% | 38% | 5.9% | corridors |
| Autarky | 50% | 43% | 6.5% | mixed |
| Schooltime | 63% | 32% | 5.7% | structured |

Enemy-facing rays are almost never the point — except on combat maps where ~9% of pings touch an enemy (the informational kill-channel).

### Volume — who talks how much

| Team | pings/action | share of max (4) |
|---|---|---|
| calc | 3.92 | 98% |
| Sabotage-d | 3.91 | 98% |
| PPP | 3.86 | 97% |
| Stockfish | 3.83 | 96% |
| 3.14159265 | 3.78 | 95% |
| ddabap | 3.87 | 97% |
| DESTINY 3 | 3.81 | 95% |
| Cutlery | 2.35 | 59% |
| forgot | 1.72 | 43% |
| cheji bt | 2.15 | 54% |
| Sponge | 1.27 | 32% |
| Cache me outside | 0.40 | **10%** |

Sonar usage is orthogonal to rank: two of the three highest elos barely use it (forgot 1.72, Cutlery 2.35) while rank-20 w daniel ma saturates at 3.91. It's a *choice* about architecture — how much state lives in the swarm vs in the heads.

### The interception problem

Every ping is received by every dragon on the ray — friend and enemy. Elite protocols all do the same thing: **tag + sender id + payload** (Loong's documented 64-bit format) so a dragon can verify a message is "mine" and not an echo of enemy traffic. The channel being public is why there is no stealth meta — there can't be.
