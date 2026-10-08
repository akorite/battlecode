# Freeze decision — Oct 9 2026 06:00 UTC

## LIVE: v137 = abyss_v476 (submitted 17:21 UTC Oct 8, active)
v449 + stub-pool churn (len-2 pawns ram-die near teammate ≤2, mod-3 throttle,
units≥45, r≥60, enemyDist>2) extended through the feed window.

## Verification summary
- elim testbed (trophy/trauma/devil/portals/stripes/weakhold/maze, seeds 1-8): 71.9%/32 vs v376 (control bar 62.7%)
- fresh seeds 16+: ~55%/22 (harder seed range; combined 64.8%/54 vs control 62.7%/110 — still positive)
- mirror vs own strong build (v449, all maps): 51.5%/68 — neutral-positive
- ladder: 56%/25, Elo 1711-1734 (campaign high)

## Decision rule
Keep v137 unless its record over the pre-freeze window craters <40%/40g.
Fallback: resubmit workspace/abyss_v447 (v133 code, 57% lifetime record).
v447_smoke board verifies the dir builds/runs.

## Post-freeze
Autoscrims 3-4h on SAME map pool (churn verified there) -> seeds snapshot ->
qualifier Oct 10 6pm Sydney, best-of-7 ALL UNSEEN MAPS, top-10 advance.

## Bracket (seed ~95-98, Elo ~1700)
R1: Error 418 (~1297) — routine
R2: pi/3.14159265 (~2043) — self-jams corridors, starves vs contested pressure = churn's verified class
R3: Sabotage-d (~2150)

## All shipped mechanisms (verified, in live build)
- v131: starving_ on all maps + contested forage 0.5->0.85 (replay-derived, ladder-verified)
- v132/v133: starveLocal 2.5 (contested-starvation band fires) + hunt-when-winning slack
- v135/v136/v137: stub-pool churn (the elim-class counter; recipe optimum after 7 ablations)

## Dead axes (do not retest without new evidence)
len-3 churn, consumer<=3, body-ram channel, churnFrom30, max-churn, bed-cycle positioning,
victim-margin trades, claim TTL, corridor income, champ-bed anchor (2x), feedBedStep (2x),
divestiture-shed, conveyor orbit, paid multi-step moves.
