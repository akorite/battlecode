# Bracket opponent profiles — R2=314, R3=46, R16=87 (explore lane)

Data: ~16 freshest replays each (~/bc/opp_{314,46,87}); analyzer tooling/oppprofile.py.
Caveat: several pulled games are 46-vs-87 head-to-heads (same match in both samples — kept, they inform both profiles).
All three share a skeleton: **single-champ dominance (longest@end ~5-6x the 2nd-longest) + queen dies by h2h in EVERY elim loss + massive churn (260-410 own deaths/game)** — they win by volume-recycling, not by keeping units alive.

## Team 314 "3.14159265" (~2044) — trapped-econ grinder

- Record 7-9; eats 1304/game (away-frac 0.32). Deaths 414/game: **noValidAction 45%** (2957) — they die TRAPPED more than anyone else profiled, far-field (60% >20 from spawn). Their swarm over-commits deep lanes and self-jams.
- Queen: qEnd 4.7 median 3 — NOT a banker; dies h2h @58-373 in 6/16. qbuds 2.8. Roam ~7.
- Champ: longest@end 31, dominance **5.7x** second-longest — the most champ-dependent of the three.
- Loss anatomy: roundLimit losses have queen dead early (h2h @58-111) + swarm thins to 1-5 alive.
- **Exploit:** chokepoint/trap pressure — their nva rate means corridors already kill them; contested narrow mouths + stall plays amplify it. Kill the champ dragon → collapse (nothing else carries length). RoundLimit grinders: they nearly never elim us (2/16) — a bells-survival counter (queen alive → queenEnd → longest) beats them.

## Team 46 "Sabotage-d" (~2214) — early-ram queen, bimodal banker

- Record 11-5; eats 806/game. Deaths 261/game: h2h 1337 + **hitWall 1197 (29%)** + nva 1006 — wall-splatter heavy.
- Queen: qEnd mean 16 median 0 — BIMODAL: either banks huge (Maze qE105, Default 59, Portals 41, Trauma 48) or dies early ramming — **every one of their 3 elim losses opens with queen h2h @11-61**. qbuds 3.6.
- Champ: longest@end 35, dominance 5.3x.
- **Exploit:** offer her the trade — keep OUR queen adjacent-covered early on contact maps; their queen commits to h2h within ~r60. If she dies and ours lives → their elim becomes our bells win (they've lost every game where their queen died first and ours survived... and 2 roundLimit losses came with queen alive but out-fed: Trauma qE48 vs a longer enemy queen — out-feeding her also works).

## Team 87 "WeHaveQuizzes" (~2301) — congestion-heavy brood-queen

- Record 11-5; eats 921/game (away 0.33). Deaths 300/game: **hitWall 1312 + nva 1427 = 57% congestion/trap**; h2h only 1194.
- Queen: qEnd mean 16 med 0 — bimodal like 46's; qbuds 5.8/game (highest — UNSW game hit 30 buds; she doubles as brood-mother). Dies h2h 9x.
- Champ: longest@end 37, dominance 5.2x.
- **Exploit:** congestion is their biggest self-killer — pocket/corridor maps (maze, autarky, dilemma-class geometry) maximize their hitWall+nva bleed; queen-ram bait works like 46's (9 early h2h deaths). Their swarm is the thinnest at end of the three in losses.

## Cross-cutting counter-builds (ranked)

1. **Queen-survival pivot (all three):** every elim loss in all 48 replays opens with THEIR queen dying h2h @11-61 while ours would live — protected-queen opening flips their elim scripts into our bells wins.
2. **Champ-assassination:** L1/L2 ~5-6 means their totalLength is one dragon deep — killing the longest collapses the longest key AND total simultaneously.
3. **Trap/corridor pressure:** 314 (nva 45%) and 87 (congestion 57%) self-jam in narrow geometry — prioritize contested mouths/pockets over open-field fights on those matchups.
4. None of the three dominates contested beds (away-fracs all ~0.3) — eats come from home-field recycling; cutting THEIR home eat volume via lane pressure is viable but secondary.
