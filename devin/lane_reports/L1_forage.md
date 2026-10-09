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

## Gate decisions at ~40 games

| variant | n | win% | eaten60 Δ | splits60 Δ | verdict |
|---|---|---|---|---|---|
| L1a bed-targeting | 39 | 43.6% | -0.5 | -0.2 | KILLED (<50%) — countdown-bed weight moved nothing; beds were already targeted |
| L1b split-timing | 40 | 48.7% | -2.2 | -1.3 | KILLED (<50%) — len-5 buds hurt: parent keeps len-1, dies to any h2h, splits60 DROPPED |
| L1c heads-by-120 | 39 | 52.6% | +0.6 | +0.1 | RUNNING — only positive variant; second board launched seeds 9-16 |

L1b mechanism postmortem: earlyBudLen=5 makes len-5 workers bud len-4 children → parent keeps len-1 →
len-1 parents die to any enemy head contact → net splits60 fell vs base. The "resplit sooner" idea
needs keep≥2, not len-1 stumps.

L1a postmortem: countdown floor already existed (0.9*gp(max(m,cd+1))); +0.6 early weight was
indistinguishable — respawning beds are not the intake bottleneck.

Boards live: L1c_gate (seeds 1-8), L1c_gate2 (seeds 9-16). Final numbers when complete.

## Near-final read (n=320/704)

| board | n | win% | eaten60 Δ | splits60 Δ | alive50 Δ |
|---|---|---|---|---|---|
| L1c seeds 1-8 | 180 | 50.6% | -0.0 | -0.0 | +0.3 |
| L1c seeds 9-16 | 140 | 48.6% | -0.2 | -0.1 | +0.4 |
| **combined** | 320 | **49.7%** | ~0 | ~0 | +0.35 |

L1c is washing too — a coin-flip clone of v476 on every intake metric. The wider breed window
adds no early-unit advantage (early buds happen anyway) and no early-intake advantage.

## Verdict (all three variants)

**All three L1 mechanisms wash ~50%.** The 2× per-unit intake gap r0-60 does not live in:
- respawn-bed target weighting (countdown floor already covered it),
- early split threshold (len-5 buds are strictly worse — len-1 stumps),
- breed-phase unit cap (bud window is not binding early).

This is the fourth consecutive ~50% production-side knob (claim-veto TTL/bypass/exclusion + these).
The intake gap survives unchanged under forced extra production — consistent with it being
*pathing/conversion* quality, not volume: our stubs die or wander before converting
(starvation@60 58% vs 42% under identical spawn geometry).

## Suggested next probe (not a volume knob)

Per-unit distance-travelled per pearl eaten r0-60 (conversion efficiency per step), and
early-stub survival curve (deaths by age r0-60). Both measurable on existing replays.

Boards run to completion for the final table; ETA ~1h.
