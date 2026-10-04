# STATE — ladder iteration (updated ~01:10 UTC Oct 4)

## Ladder
- Team 351 "Cognoscenti". Goal: top-20 (~1955 Elo) by Oct 10 qualifiers.
- **LIVE: v119 (sub 16258) = v116-guard-scope + pearl opening + queen ram screen.**
- v117 band: 7-13 vs 1650+ (Nitro 2-3, Quaker 1-4, 1234 2-3, IW 2-3).
- Elo 1520. Weak spots: weakhold/starvation maps, devil (25%), early econ halved.

## Honest-gate scoreboard (kmatch.py)
- v119 = live (v116+pearl+queen-screen); v117 sub 16206 idle
- v108 vs v104: 47.7% — parity, current clean base
- v112 vs v104: 48.9% — parity + wallguard = free insurance → SUBMITTED
- v110 (v108+wh2): 40.0% — DEAD (wh2 unproven-veto pins queen on foggy maps)
- v111 (v108+swarmTrap): 36.9% — DEAD (corridor-pocket veto bleeds islands/
  slithery/weakhold)
- v109 (v108+wh2+pearl): 42.0% — DEAD
- Honest baseline: v104 = 48.6% vs cf, 38.9% vs combat

## Lanes (4 workers)
- pocket (5d3c6001, devin/pocket): weakhold starvation — dragons can't reach
  fields past horizon; integrator far-pull failed 25-37%; needs corridor-aware exit.
- earlyecon (381c0534, devin/earlyecon): bisect wh4/open_/guards — splits@r60
  halved since v104 on elim maps (devil 25%).
- autarky (13f9c332, devin/autarky): elim-map tempo (running, no branch yet).
- explore (97938483, devin/explore-modes): isolated lane per explore-steering.md.


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

## Steering (Keitaro, 4 Oct 00:00) — key facts
- Round-500 win rule (426 top-team replays): longer queen wins 210/210; equal queens → longer longest dragon wins 214/214. Dead queen = len 0.
- Guards killed the feed: v104's boxed-in dragons dying beside the champion FED it. hitSelf r300-399: 30.3 (v104) → 10.4 (v106) → 12.7 (v112). Longest r499: 30.8 → 13.3 → 13.0. ACTION A: scope guards queen-only or r<40.
- v113 grows better (27.8 drag, 69 len r100 vs opp 22.6/60; 720 pearls vs 481) but doesn't consolidate (15.3 vs 28.9 longest r499).
- Elimination maps (Stripes/Trophy/Devil/Dilemma/QoS/Autarky/TD/Default): winner ahead by r25 (6.3v5.3 dragons), far by r50. Opening 0-50 IS the game there.
- Round-500 maps: winners' longest 9.4 vs 7.1 at r200, 16.8 vs 12.0 at r300. Islands/Schooltime/Australia → longest dragon decides.
- Queen deaths: 94% are len2-3 rams on unguarded queens (0 allies within 3 tiles). Median ram death r131.
- Stop: guards on non-queen dragons; whole-board vetoes; 88-gate verdicts (±10 noise); mixed-field records (compare by tier).
- Benchmark bots: Bot(11), test4(19), Sabotage-d(46). Sonar: no fixed tags.
