# L1 early-forage push — 3 variants on abyss_v481, gated vs abyss_v476

Goal: close the 2× per-unit intake gap r0-60 (eff .052 vs .105, starve_counter).
Boards: L1a_gate, L1b_gate, L1c_gate — cand vs abyss_v476, --maps all --seeds 8 --seed-start 1 --jobs 16 (352 games each). Kill <50% after 40.

## Diffs (vs abyss_v481)

- **L1a bed-targeting**: common.hpp + `earlyBedW=0.6`; policy.hpp both target-scoring loops:
  countdown-floor `0.9*gp(max(m,cd+1))` → `(0.9 + (worker_ && r<120 ? 0.6 : 0))*gp(...)`.
  Early workers weight beds about to respawn ~1.7× — arrive as the pearl lands.
- **L1b split-timing**: common.hpp + `earlyBudLen=5`; policy.hpp trySplit:
  `n = (L_ >= (r<60 ? earlyBudLen : swarmBudLen)) ? swarmBudChild : L_/2`.
  Len-5 workers bud a split-ready len-4 child during r<60 (was len≥6) — parents resplit sooner.
- **L1c heads-by-120**: common.hpp + `earlyBudAlive=40`; policy.hpp bud_ flag:
  `bud_ = units < (r<120 ? 40 : budAlive)` — breed phase stays open to 40 units through r120.

## Running numbers

(in progress)
