# queenEnd key-1 validation — bell (roundLimit) games (explore lane)

Sample: 42 roundLimit games from 234 top-team ladder replays (leaderboard top-10 sides:
aAah/FtM/chad/55/545/larp/Cultery/horse/WeHaveQuizzes/SSS; games vs other opponents included).
For each: winner, queen end-length both sides (full body-tracked replay), longestDragon, totalLength.

## Verdict: CONFIRMED — (queenEnd → longestDragon → totalLength) lexicographic, 42/42 (100%)

The ordering reproduces every winner with zero mismatches. queenEnd is key-1 and sits
FIRST — it is compared before longest, not after.

## (a) Which key actually decides?

| deciding key | games | share |
|---|---|---|
| queenEnd (queens differ) | 26 | **62%** |
| longest (queenEnd tied — virtually always both queens dead) | 16 | 38% |
| total (first two tied) | 0 | 0% |
| full tie | 0 | 0% |

So "win longest, lose on queenEnd" is the NORM, not an edge case: **62% of bell games are
decided purely by which side's queen survives longer.** The queenEnd-tied games collapse
to the longest key because both queens are dead (median losing qEnd = 0).

## (b) Median winning queen end-length

- Winner queenEnd: **median 21.5, mean 25.9**
- Loser queenEnd: median 0 (dead)
- Winner with queenEnd = 0: 13/42 (31%) — winning with a dead queen is common (funnel wins longest)
- Winner with queenEnd ≤ 2: 13/42 — a hidden len-2 queen is a losing queen when hers is alive

## (c) Does a hidden len-2 queen auto-lose when both queens survive?

**Yes — 13 games had both queens alive at the bell; the shorter-queen side won 0/13.**
A len-2 hider survives the combat phase and still loses the bell outright. Hiding buys
survival only; it forfeits key-1. The banked-queen games (qEnd 17-52) are where roundLimit
wins concentrate; a len-2 queen only avoids losing when the opponent's queen is ALSO dead
(and then it's a longest fight anyway).

## Numbers for the ship decision

- Feeding the queen (or champ) to qEnd ≥ ~20 converts ~62% of bell games.
- A dead queen forfeits key-1 entirely: dead-vs-alive = automatic loss regardless of
  longest/total (the 4-losses-winning-both-keys pattern from the field census is this rule).
- Both-dead → pure longest fight — the funnel matters only as the tiebreak.
