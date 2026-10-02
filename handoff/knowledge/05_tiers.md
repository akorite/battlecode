# Tier analysis — what elo actually costs

*Tier names from the community stats site: Plankton <1000, Shrimp 1000–1300, Tunafish 1300–1600, Swordfish 1600–1900, Shark ≥1900.*

## The gradient

| Tier | Team-games | Peak alive | Suicides/g | Sonar/action | Deaths/g | Elim% | Side-B% |
|---|---|---|---|---|---|---|---|
| Shark | 27,758 | 38.3 | 24.8 | 2.77 | 242 | 48% | 65% |
| Swordfish | 38,609 | 34.1 | 22.3 | 2.32 | 227 | 40% | 50% |
| Tunafish | 11,767 | 21.7 | 5.4 | 1.28 | 152 | 34% | 47% |
| Shrimp | 545 | 19.8 | 22.0* | 0.77 | 104 | 41% | 30% |
| Plankton | 81 | ~19 | ~0 | 0.80 | ~190 | 62% | — |

*Shrimp suicides are noisy (small n).

**Tunafish → Shark is the great wall:** +76% swarm, +116% sonar, +360% suicides, +59% deaths. Below Tunafish the game isn't even the same game — empty boards, silent sonar, swarms that never reach critical mass.

## Elo calibration — what a gap is worth

Measured win rate of the higher-elo team vs elo gap (favorite = higher elo):

| Elo gap | Favorite win% | n |
|---|---|---|
| ~0 | 50.1% | 9,571 |
| +25 | 56.0% | 10,653 |
| +50 | 56.4% | 8,227 |
| +75 | 60.9% | 6,541 |
| +100 | 63.6% | 5,593 |
| +125 | 66.8% | 4,284 |
| +150 | 68.0% | 2,827 |
| +175 | 71.3% | 2,408 |
| +200 | 73.0% | 1,543 |
| +225+ | 82.8% | 7,782 |

Roughly logistic: +100 elo ≈ 64%, +200 ≈ 73–83%. Slightly *steeper* than standard elo (which predicts ~64% at +100 and ~76% at +200) — meaning the ladder is well-calibrated at small gaps and the top genuinely separates from the pack.

## What separates the tiers, in order of importance

1. **Sonar saturation** — 0.77 → 2.77 pings/action. Coordination is the first thing that scales.
2. **Swarm mass** — 21.7 → 38.3 peak. Bodies = territory = eval logits.
3. **The suicide doctrine** — 5.4 → 24.8 per game. The conversion mechanic is elite-only; low tiers suicide rarely and without collection.
4. **Death discipline** — counter-intuitively, Sharks die *more* (242 vs 152) — they churn deliberately; Tunafish deaths are accidental.
5. **Side-B exploitation** — 47% → 65%. Reading committed moves is a skill.

## Language check

49 of the top 50 are C++. The CPU budget (100M points/turn/dragon) effectively requires it for the coordinated-swarm style. Python occupies the bottom of the ladder almost exclusively — Plankton and Shrimp are disproportionately Python (a real constraint, not just culture).

## What it takes to climb

From Tunafish to Swordfish: turn sonar from noise into protocol (1.3 → 2.3 pings/action — the same jump as adding a real messaging layer), and hold ~34 dragons instead of ~22.

From Swordfish to Shark: add the economy (sui 22 vs 22 is flat — the difference is *collection*), master the bell (48% elim vs 40%), and exploit move order (65% side-B).
