# Battlecode Abyss — ladder-climb handoff bundle

Everything a fresh Devin session needs to build and iterate a top-20 bot for UNSW Battlecode 2026 ("Abyss").

## Contents

- `abyss-framework/` — Cat's paradise shared C++ bot (SongyuQi-Francisco/battlecode-abyss-framework): grower/swarm roles, phase schedule, Params in common.hpp. Fork this — do not write from scratch.
- `tooling/` — working replay pipeline: `capnp_reader.py` + `depack.py` (packed Cap'n Proto decoder, no deps), `parse_replay.py` (replay → events/state), `bceval_adapter.py` (xCirno1 eval engine via importlib), `analyze2.py` (per-game stats extractor).
- `knowledge/` — 22 strategy docs: rules, game flow, eval engine, eras, tiers, maps, doctrines, deaths/sonar, top-20, h2h matrix, method, prior-competition research + 10 per-team deep dives.
- `data/game_stats_sample.jsonl` — 3k analyzed games (full schema) for calibration.
- `sample_replays/` — 12 real replays for testing the decoder offline.

## What the human must supply

1. **This zip** (attach to the session, or the box path if reusing this VM).
2. **A game.battlecode.au account** — username/password or the session cookie for `unswbc submit` (needs a joined team; submissions are zip uploads, 12/hour).
3. Optionally: a local clone of `github.com/unswcpmsoc/battlecode` for reference.

## Key facts the session needs

- Toolkit: `uv tool install unswbc` → `unswbc new cpp` → `unswbc run` (add `--sandbox` to price CPU-points like the judge) → `unswbc submit`.
- Rules: ≤64 dragons, ≤500 rounds, MOVE/SPLIT/SUICIDE, ≤4 sonar pings/action, win = longest dragon at 500 or elimination.
- Meta target: peak ~38-42 alive, sonar ≥3/action, ~240 splits/g, C++ only.
- Eval objective: xCirno1/battlecode-eval (public weights) — use as offline objective for tuning.
