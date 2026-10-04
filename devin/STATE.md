# STATE — ladder iteration (updated ~23:20 UTC Oct 3)

## Ladder
- Team 351 "Cognoscenti". Goal: top-20 (~1955 Elo) by Oct 10 qualifiers.
- **LIVE: v112 (sub 16175, building→active) = v108 + wallguard.** Guard
  redirects any provably-fatal first step (seen-kelp edge OR own body) to a
  free exit; covers single-step and path[0]. Strict superset of v106's guard.
- v106 record before v112: 4W-6L ranked; losses corridor maps; zero
  schooltime drawn so guard unverified on ladder.

## Honest-gate scoreboard (kmatch.py, 22-map pool, seeds 2, both sides)
- v108 vs v104: 47.7% — parity, current clean base
- v112 vs v104: 48.9% — parity + wallguard = free insurance → SUBMITTED
- v110 (v108+wh2): 40.0% — DEAD (wh2 unproven-veto pins queen on foggy maps)
- v111 (v108+swarmTrap): 36.9% — DEAD (corridor-pocket veto bleeds islands/
  slithery/weakhold)
- v109 (v108+wh2+pearl): 42.0% — DEAD
- Honest baseline: v104 = 48.6% vs cf, 38.9% vs combat

## Lanes (4 workers)
- pearl (d74f44be, devin/pearl): forage-first opening; v2 = 52.8% vs combat,
  52.1% vs v104; v3 gating (hunts restored). Needs map-gating vs big maps.
- whfix (d50d6e85, devin/whfix): wh2 bounced — unproven veto over-fires;
  iterate maze-gated or tighter bound, full-pool gate ≥50% + no 0/4.
- starve (c85884d3, devin/starve): swarmTrap bounced — needs conveyor-vs-
  survivable-pocket discrimination or deadend writeup.
- qsiege (64ec12ca, devin/qsiege): NEW — mid-game queen encirclement deaths
  (H2H/hitWall r50-450, all-4-exits-blocked). Pick ONE fix: exit-freedom
  scoring / convergence trigger / pocket-depth limit.
- losssurvey (d1bd4e24): done, terminated.
- explore lane: mode histograms + margins + transitions done; thrash quantified, sticky-mode prototype next

## Harness facts
- kmatch.py = honest A/B (paired seats). gate_v10X.sh = single embedded pair,
  wins-phase labels wrong for 2nd opponent — do not use.
- `strings runner | grep bota_` reveals embedded pair dirs.
- unswbc CLI at ~/.venv-bc/bin/unswbc; API via unswbc.api.request(key).
- Edge seen-flag = fog of war; unseen edges model open (kind=0) → hitWall.
- Death histogram: hitWall 2174, hitSelf 1734, H2H 1513 — all 1-step moves.

## Next
- v112 ladder review at 60+ ranked games (from activation ~23:15).
- Integrate pearl v3 or qsiege fix, whichever passes first.
- Backlog: stripes/devil openings, mid-game H2H defense tuning, STATUS.md.
