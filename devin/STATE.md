# STATE — autonomous ladder iteration (2026-10-03)

## Goal
Top-20 ladder rating on game.battlecode.au (team Cognoscenti id 351) before qualifiers snapshot 10 Oct 2026.

## Ladder state (live, API-verified)
- Rank 136 / Elo ~1479. Top-20 cutoff ~1955 → ~480 Elo gap, 7 days.
- LIVE bot: **abyss_v106** (submission 16084, activated ~18:40 UTC).
  Ranked so far: 5 matches, 1W-4L — too early for verdict (need 60+).
- v104 retired (79W/1D/99L = 43.8%); v105 = known regression, never submit.
- Loss survey (96 losses): queen death precedes ~every elimination; mid-game
  h2h (12) + hitWall (9) biggest buckets; r0-5 schooltime suicides 6; 0 timeouts.

## Harness facts (learned today)
- kvmrun runner = ONE embedded bot pair; --name-a/--name-b cosmetic labels only.
  Old gate_v10X.sh wins phase mislabeled the second matchup + faked side-swaps.
  Verify any runner: `strings $RUNNER | grep bota_`. **kmatch.py is the honest
  harness** (builds reversed-seat runners for real both-sides).
- Map pool on ladder incl. weakhold, tower_defense, stripes, trauma, maze,
  islands, unsw, australia — all in unswbc templates/maps (kmatch BC_MAPS).
- wasm cache stamps ONLY .cpp — header edits reuse stale wasm. Fresh dir names.
- Replay dl: fetch 302 Location WITHOUT auth. battles API = latest-100.
- BC_KEY at ~/.unswbc/keys.json — never print/commit.

## Version pipeline
- v106 (guard): LIVE, collecting ladder record.
- v107 (v106+wh1): FAILED gate (31%) — wh1 unproven veto pinned queen on open maps.
- v108 (v106 + unified trapped-fallback rank): gate clean vs cf 45.6% (68g),
  deaths baseline-only. Combat check running (gate-v108-combat, kmatch honest).
- **v109 (v108 + wh2 + pearl)** — merged from two worker lanes:
  wh2 = queen trap scan treats fog as wall + frontier discriminator
  (trapSeenOnly=1, trapSafeCells=12, trapFrontier=2; weakhold pockets fixed,
  no open-map pin; 54.2% vs v104 wh/td/trauma; 0 own wall deaths).
  pearl = forage-first opening (openUntil=48, openDanger 1.0, openQueenDanger
  1.8, openQueenKeep 3; +13.9pp vs combat, parity cf, +14% pearls@30;
  kept regressions stripes/devil/default/qos small-n).
  Status: compiles, deaths gate = baseline pattern only. kmatch gates running:
  gate-v109-cf then gate-v109-combat (22 maps × 2 seeds × both sides).

## Lanes / workers
- me (integrator): merge, gate, submit, review.
- whfix worker (d50d6e85…): DONE — abyss_wh2 shipped on devin/whfix.
- pearl worker (d74f44be…): DONE — abyss_pearl v2 shipped on devin/pearl.
- losssurvey: DONE.

## Next 3 actions
1. v109 gates → if ≥v104 baseline vs cf+combat: submit v109 (git-tag), leave v106 verdict to its 60-game review.
2. Log v108/v109 results + v106 ladder table in devin/log.md.
3. Backlog: mid-game queen-defense (12 losses), hitWall pathing (9), stripes/devil openings, caged-queen, ally-aware exits.
