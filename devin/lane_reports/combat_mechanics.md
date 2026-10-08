# Combat mechanics forensics — top-10 bots vs ours (explore lane)

Data: 234 fresh top-10 leaderboard replays (~/bc/ladder_replays, teams aAah/FtM/chad/55/545/larp/Cultery/horse/WeHaveQuizzes/SSS) + 235 of our own (ladder_replays_v168). Analyzer: tooling/combatforensics.py. All numbers per-side-per-game unless noted.

## 1. Head-to-head engagements — winners ram SHORTER heads, disciplined

| initiator | n | init/vic len ratio | init>=vic | init<0.5*vic |
|---|---|---|---|---|
| top winner-side | 14191 | mean 1.49, med 1.5 | **92%** | 5% |
| top loser-side  | 13569 | mean 1.39, med 1.5 | 83% | 8% |
| our winner-side (v168) | 11628 | mean 1.65 | 94% | 6% |
| our loser-side | 11164 | mean 1.41 | 84% | 8% |

- Engine kills BOTH on head collision; "who initiates" = whose move path ended on the enemy head.
- Top teams' h2h is a DELIBERATE favorable trade: 92% of initiations attack a head ≤ own length (median 1.5x advantage). Suicide rams into 2x+ heads are rare (5%).
- Our length discipline is already comparable (94%) — NOT a differentiator.
- Implementable: keep the len-ratio gate (attack only vic_len <= own_len); the gap is not pick-quality.

## 2. Escort formations — thin screens at DIAGONAL corners

- Winner queens carry **1.6-1.8 allies within Chebyshev-3** vs losers' 1.0-1.4 (ours: 1.1-1.5). Longest dragon: 1.6 vs 1.1-1.3.
- Shape: escorts sit overwhelmingly at the **four diagonal offsets (±1,±1)** — ~4x more than orthogonal (N/E/S/W). It's a loose screen ahead of the body, not a tight orthogonal box.
- Modest density — escort is a harassment/buffer layer, not a wall. Implementable: give champ/queen pathing a soft "allies on diagonals" bonus rather than requiring a fixed ring.

## 3. Multi-step actions — winners move farther per turn; the difference is REACH volume, not exotic tech

Move-step-count histogram (60-game sample):

| steps | top bots | ours |
|---|---|---|
| 1 | 94.2% | 92.3% |
| 2 | 4.7% | 7.3% |
| **3+** | **1.7%** (~400/game) | **0.7%** (~120/game) |

- Multistep (steps>=2) volume: top winners ~1047/game/side vs top losers ~373; our winners ~717 vs losers ~440.
- Classification: 94% transit, ~1.3% hunt (path ends on enemy head), ~1.6% escape (started adjacent to enemy head, moved away). Top winners hunt-multistep 58% more than losers (1933 vs 1221); ours is FLAT (1358 vs 1389) — our sprint/trade targeting doesn't get more aggressive when winning.
- Implementable: the delta is 3+-step pursuit/escape paths (ours cap at ~2). Their sprint model budgets longer paths — worth cloning the *usage pattern* (pursue when ahead on local numbers, escape when behind) rather than the reach formula.

## 4. Torus edge usage — ubiquitous transit, negligible as a kill vector

- 371k wrap-steps across 234 games (~1600/game) — wraps are normal movement for them (spawn orientation heavy: B side 272k vs A 99k).
- Multistep actions containing a wrap: 6506. Wrap-involved h2h initiations: **182 total (<1/game)** — wraps are NOT a kill technique, just transit.
- Ours: 250k wrap-steps, 233 wrap-h2h — same shape. No gap.
- Implementable: nothing to copy; our earlier "seam ambush" hypothesis stays dead — nobody weaponizes wraps.

## Net read vs our v424 single-step+occasional-twoStep model

1. **Clone: longer pursuit/escape paths.** Their 3+-step moves are 2.4x our rate; ours are stuck at exactly-2. Longer paths feed both hunt (initiate favorable h2h from 3+ cells) and escape.
2. **Clone: hunt-when-winning asymmetry.** Top winners push +58% hunt-multisteps vs losers; ours is flat — gate sprint aggression on local-numbers advantage.
3. **Skip: h2h length gate** (ours already matches 92-94% discipline) and **torus mechanics** (no delta).
4. **Cheap win: diagonal escort bias** around champ/queen (+0.3-0.5 ally density at ±1,±1 corners).
