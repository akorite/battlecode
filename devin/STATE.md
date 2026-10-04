# Battlecode state — refreshed 2026-10-04 ~08:45 UTC

## Ladder
- Elo ~1576 (v135 live as sub v112; v134 re-uploaded as sub v114 to stop the dilemma/portals bleed while v137 gates)
- Team 351 (Cognoscenti). Quota: 60 game-starts/hr.
- Band 1550-1849: ~40-45%; top-4: 1-31. Top-20 cutoff ~1955.

## Version line
v120 (splitEnemyDist=1) → v133 (feed@360 on open maps, corridor ≤2000 revert) → v134 (+ee dual-scan) → v135 (+pocket bait-fix, has A1 defect live) → v137 candidate (=v135 + F2 score gated on sealed-queen + F3 + F13 + A2 sealed-queen≠champion). v136 (autarky election fix) gated 50.9%, hold.

## Steering-3 order (active)
A. Early growth elim maps — targets r25 6.7d/16.4L, r50 10.3d/25.5L, r100 20d/50L (earlyecon lane owns)
B. Feed-window champion-pearl measurement + feeder-only guard (target <10 self-hits/30r, longest>33)
C. Review fixes before uploads (F2/F3/F13/A2 in v137; open: F12, F15, feature-gates, champId_ trace)
D. 17-map both-seat vs FtM/Vibing++/SSS/Sponge/Computers(112), ≥100g per verdict

## Stop list
feed-date moves; map-name tables (w*h, W==40); queen-risk trades; <100g verdicts; one-seat drills; rating reads as verdicts.

## Lanes
- autarky devin-13f9c…: 5a phase controller + computed map features (replaces w*h/40x15 gates)
- earlyecon devin-381c…: pre-r200 elimination / action A targets
- pocket devin-5d3c…: 5b escort+hunt (target ≤.06 queen lost <r250; B1 hunt bonus; qOS r36 mutual-elim open)
- explore devin-9793…: SPSA tuner + sticky (per explore addendum)

## Pending review/verification
- qOS r36 all-4-dead mutual elimination — no shipped fix touches it
- champId_ fragmentation trace (12-55% late turns think selfChamp_)
- dual-scan r100 cost vs v133 on ≤2000 maps (30.3 vs 34.8 flag)
