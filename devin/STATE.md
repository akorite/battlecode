# STATE — autonomous ladder iteration (2026-10-03)

## Goal
Top-20 ladder rating on game.battlecode.au (team Cognoscenti id 351). Ladder Elo ~1500, leaders 1900+. Qualifiers snapshot bots+ratings 10 Oct 2026 — must be live and stable before then.

## Current best
- Local ship candidate: abyss_v104 (commit 232c080) — 59.4% vs abyss_st on paired 9600-seed fixtures.
- Flagship reference: abyss_v102 — 63.6% vs abyss_st (176g, my j0005 run).
- abyss_v105 = REGRESSION (41.7% vs v104) — DO NOT SUBMIT.
- Ladder state: PENDING BC_KEY — will record submissions/Elo when key lands.

## Lanes
- Lane A (fixes): Schooltime queen suicide, in-reach queen kills (slayQueen already in v104 — verify live), protectLead, round-keyed sonar (already in v104).
- Lane B (queen): feed queen/consolidation — cf timing merged (320); v105 deadQ failed. Next: caged-queen detection (schooltime feeder waste ~1800 turns), ally-aware exit legality (seal done right).
- Lane C (tuning): param vectors per map class + CMA-ES/SPSA on kvmrun. NOT started.
- Lane D (review/research): ladder game review, opponent modelling, per-map doctrine.

## Backlog (ranked)
1. Read ladder state (BC_KEY): which version is live, per-map ratings, last 100 games.
2. Local gate for v104 (control vs starter, all-17-map queen-death check r0-5, 2 outside opponents).
3. Schooltime r1 queen suicide repro + fix (v104 may already fix via deadEnd veto — verify).
4. Caged-queen detection for schooltime feeders (~1800 wasted turns).
5. Ally-aware exit legality (seal done right — mechanism, not danger price).
6. Early-pearl intake gap: 7.4 vs top teams' 18.8 per first-30r on small maps — forage-first opening.
7. Round-keyed anti-replay sonar — verify present in v104 (WaterCandle echo).
8. Opponent classification in first 30-60r -> strategy profile switch.
9. Beam search 2-4 turns over joint moves (bounded, cheap eval).
10. Behaviour-clone top-team decisions from replays (parse_replay.py; post-1-Oct games only).

## Rules (from prompt sec 4)
- Separate message tags per team in local tests (keyed sonar now default).
- Outside opponents, not just self-play; ~6 max parallel games; halve on any timeout.
- Spot-check side attribution x3; report per map; use ALL-unlocked on side-locked maps.
- Pass = no timeouts, no NEW r0-5 queen deaths on all 17 maps, >= best vs 2 outside opponents.
- Ladder decides keep/revert; <60 ranked games = no verdict; -40 Elo over 60g = revert.

## Next 3 actions
1. Wait for BC_KEY -> pull submissions/Elo/matches.
2. Control run abyss_v104 vs starter (small, seed1) + schooltime queen-death repro.
3. Write devin/log.md + first STATUS.md, push branch.
