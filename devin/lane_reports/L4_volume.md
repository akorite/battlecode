# L4 stub-churn volume — gate results on shipped no-bed v481 base

Base: workspace/abyss_v481 (extracted from origin/devin/v120 @17b6747, churnNeedBed=0).
Variants: L4a churnMod 3→2, L4b churnMinUnits 45→40, L4c churnFrom 60→50.
Gate: `kmatch --maps all --seeds 8 --seed-start 1 --jobs 14`, paired both-sides, tags L4a/b/c.

## Scores (final, gates stopped at ~80g — conclusions stable)

| variant | n | score | decisive pairs |
|---|---|---|---|
| L4a (churnMod 2) | 82 | **47.6%** (39.0) | 2 pair losses (unsw s1, schooltime s2) — KILLED |
| L4b (minUnits 40) | 83 | **50.6%** (42.0) | 0 — no-op |
| L4c (from 50) | 78 | **50.0%** (39.0) | 0 divergent games at all — dead param |

Every other pair splits 1-1 — no rot, but also no lift. **All three are outcome-neutral.**

## Why: the churn gate is a near-no-op by construction

Gate chain (policy.hpp:251): `L_==2 && !queen && !grower && !hiding && !assassin &&
units>=45 && round>=60 && id%churnMod==round%churnMod && enemyDist>2 && friendDist<=2`.

Alive-unit trajectories (v481 self-play replays, units = alive dragons per side):
- Colosseum: max 41 — **never reaches 45**
- dilemma: max 15 — never
- stripes: max 41 — never
- devil: winner side 94 rounds ≥45 (in the blowout, post-decision)
- trophy: 8 rounds ≥45

**units≥45 only happens after the swarm war is already decided** — churn is gated to
fire in games we're already winning. In contested games the swarm oscillates ~10-40
alive and the gate never opens. So `churnMinUnits 45→40` widens a window that barely
exists, and `churnFrom 60→50` is dead code (units≥45 before r60 ~never happens —
L4c produced **zero divergent games in 30 pairs**).

## Divergence analysis (same-side cand-vs-base stat signature per pair)

- **L4a**: 10/32 pairs diverged, all on big maps (islands, australia, slithery,
  schooltime, maze, stronghold, big_empty, devil s2, unsw, default). Extra churn is
  real but symmetric noise: dDeaths −57…+53 direction-dependent, dLongest −27…+38
  random. On islands s1: +24/+16 deaths both directions, longest −2/+4 — churns more,
  wins the same.
- **L4b**: 2/33 diverged (islands +10 deaths; stronghold base produced +27/+50
  LONGER champs both directions — noise).
- **L4c**: 0/30 diverged — pure dead param.
- Small maps: 100% identical play — elim games end before units≥45.

L4a's one decisive result (unsw s1, both directions lost): longest tied 36v36 as A
(total 170v277 down), 35v49 as B — a single bad-trajectory pair, CI still contains 50.

## Verdict

**Kill all three** — not because they rot (they don't: ~50%), but because they can't
do anything. The throttle constants aren't the bottleneck. Churn volume is capped by
the *preconditions*, not the rate:

1. `churnMinUnits=45` — fires only in decided games. The contested phase (where
   Sabotage-d/π out-churn us, units ~15-40) is structurally unreachable.
2. `L_==2`-only + `friendDist<=2` + `enemyDist>2` — a tiny eligible pool even when
   units is high enough.

If a churn-volume lever is still wanted before freeze, the useful deltas are:
- `churnMinUnits 45→~20-25` (reaches contested mid-game), or a second tier
  (churn at units≥20 with tighter friendDist/enemyDist guards),
- eligibility widened to `L_<=3`,
- keep churnMod (it perturbs trajectories ±50 deaths/game — real churn, random sign).

Anything narrower is provably a no-op: identical replays.

Method note: `out.log` lines don't survive into kvmrun replays — gate firing was
measured via alive-trajectory reconstruction + same-side stat signatures instead.
