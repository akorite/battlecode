# The eval engine — what bceval measures and what it says wins

*Model: xCirno1/battlecode-eval. 23 per-team features, 120 weights, logistic antisymmetric scorer. We ran it every 50 rounds on 25k+ games.*

## How it works (mechanically)

- **23 features per side**, diffed: `P(A) = σ(w · (f_A − f_B))` — symmetric by construction, so `P(A)+P(B)=1` always.
- **Features:** alive/total lengths, biggest-5 dragon lengths, pearls eaten, pearls in reach, territory tiles, supply lines, champion↔ally/enemy distances, king-vs-king, deaths, lost length.
- **Weights:** 120 coefficients interpolated between knots at rounds 0/125/250/375/500 — so feature importance *evolves* across the game.
- **Groups:** bodies / economy / fights / ground / champion / side — the parts decomposition lets us see *which axis* a team won on.
- **Calibration:** trained on 5,678 replays across 18 maps and 60+ bots; side-B measured at −0.119 logits (a real handicap term).

## Verdict: it works

Winner's mean P by progress decile: **51 → 56 → 60 → 63 → 65 → 67 → 69 → 72 → 77 → 89%**. Monotone, smooth, and confident at the right times — no weird discontinuities. Median prediction at game end: ~88.8%.

Calibration check (P=50–55% games): those games actually break near 50/50 — the model isn't just confident, it's right-sized.

## What it's weighting

Endgame logit decomposition for *winning* sides (mean over all eval games):

| Part | Mean logit | Meaning |
|---|---|---|
| bodies | +3.0 to +5.4 | swarm count × length — **dominates everything** |
| ground | +0.2 to +0.5 | territory tiles |
| champion | +0.2 to +0.5 | champion positioning/size |
| fights | ≈ 0 | local engagements |
| economy | ≈ 0 | pearls hoarded vs eaten |
| side | −0.12 | B-handicap term |

The game, reduced to one model's weights: **more dragons, longer dragons, more tiles — in that order.** Pearls mean nothing unless converted into a dragon. Fights matter only insofar as they change body count.

## The mid-game winner signature

Mean winner−loser feature differentials at 50% progress:

| Feature | Diff | Reading |
|---|---|---|
| territory | +250 tiles | decisive single signal |
| total length | +36 | mass |
| pearls eaten | +19 | realized income, not stockpiles |
| alive | +12 | body count |
| **lost_len** | **+11.8** | winners churn MORE length — churn is investment |
| pearls_near | +5.3 | collection radius |
| champ-ally dist | −1.8 | champion inside the swarm, not hunting alone |

Same at 75%: terr +324, total +50, lost_len +18 — advantages compound, never revert.

## Comebacks

16% of winners were at some point below 30% win-probability. The model's largest single-round-interval swings are ~0.4 P — games do flip, but usually in Phase 2 when a swarm fight is genuinely decisive.

## Per-team fingerprints through the model's lens

| Team | bodies | ground | champion | fights | economy | reads as |
|---|---|---|---|---|---|---|
| cheji bt | +4.7 | +0.37 | +0.4 | ~0 | ~0 | territory engine |
| calc | +5.4 | +0.4 | +0.5 | ~0 | ~0 | pure mass |
| Cutlery | +3.5 | +0.3 | +0.3 | ≈0 | ~0 | swarm without battle |
| forgot to mention | +2.9 | +0.2 | +0.5 | ~0 | ~0 | conversion machine |
| Stockfish | +3.2 | +0.3 | +0.4 | ~0 | ~0 | coordinated mass |
| SSS | +1.4 | +0.1 | +0.2 | ~0 | ~0 | execution over mass |

The model confirms what the counters showed: there are (at least) three distinct ways to win — mass (calc), conversion (forgot/cheji), and execution (SSS) — and they leave different logit signatures.
