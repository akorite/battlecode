# STATE — autonomous ladder iteration (2026-10-03)

## Goal
Top-20 ladder rating on game.battlecode.au (team Cognoscenti id 351) before qualifiers snapshot 10 Oct 2026.

## Ladder state (live, API-verified 2026-10-03)
- Rank 136 / Elo 1463. Top-20 cutoff ~1955 → ~490 Elo gap, 7 days.
- Live bot: abyss_v104 (submission 15960, active). Ranked record 79W/1D/99L (43.8%).
- vs 1500+ opponents: NeungzAI 7/13, zach 4/11, meowest 2/8, Sponge 0/5.
- abyss_v105 = REGRESSION (41.7% vs v104) — never submit.
- Loss survey (worker, 96 losses): queen death precedes ~every elimination.
  Buckets: mid r51-200 13 (hitHeadToHead 12, hitWall 9), late r201+ 7,
  early r6-50 3, r0-5 schooltime 6. Zero timeouts. Report: devin/lanes/losssurvey.md.

## Current work — v106 schooltime fix (IN GATE)
- Bug: coiled queen on schooltime issues r1 `MOVE N` into own neck → hitSelf
  auto-loss. Deterministic 11/11 local + 6/6 ladder in v104. ~20% of losses.
  Timing-sensitive: any extra per-turn work (debug logs) flips the choice;
  hence an output-layer guard, not a policy patch.
- Fix: main.cpp emit path — if chosen step's dest ∈ body∪ownExtra, redirect to
  first safe adjacent dir (body vacated cells only freed by engine, never by us).
- Gate so far: schooltime 5/5 survive r5 (was 0/5). All-17-map deaths phase:
  ZERO NEW r0-5 self-deaths vs v104 baseline (autarky/dilemma/help/slithery
  deaths identical in v104 — pre-existing). Wins phase running vs cf+combat.

## Lanes / workers
- me (integrator): schooltime fix → submit v106 → review → iterate.
- losssurvey worker: DONE, branch devin/losssurvey pushed.
- whfix worker (d50d6e85…): running, weakhold/TD queen-death dive.
- pearl lane: pending SWE-2 slot (cap 5) — retry spawn.

## Known hazards
- wasm build cache stamps ONLY .cpp — header edits reuse stale wasm. Use fresh
  dir names (v106 not v104-edit) or rm ~/.cache/unswbc/wasmbots/<dir>-*.
- Replay dl: fetch 302 Location WITHOUT auth header. battles API = latest-100 only.
- BC_KEY at ~/.unswbc/keys.json — never print/commit.

## Next 3 actions
1. Finish wins phase → if parity-vs-v104 vs cf/combat: submit v106, git-tag.
2. Integrate whfix output when worker settles; spawn pearl worker on slot free.
3. 60+ ranked-game review of v106 → keep/revert, update log.md loss table.
