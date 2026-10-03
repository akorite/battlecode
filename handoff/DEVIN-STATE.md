# Copy-paste handoff prompt (Devin session state, 2026-10-03 ~14:30 UTC)

You are continuing the UNSW Battlecode "Abyss" bot project in repo `akorite/battlecode`
(branch `claude/bot-improvements-77hsvh`, PR #1). Read `knowledge/20_devin_lane_evals.md`
first — it has every lane result, verdict, and postmortem, plus the eval protocol.

## State

- **Ship candidate: `workspace/abyss_v104`** (commit 232c080) = flagship v102 + cherry-picked
  verified mechanisms: slayQueen (100% in-reach queen-kill conversion), protectLead,
  deadEnd queen veto, round-stamped keyed sonar, cf consolidation timing, tail-strike fear.
- Flagship v102 measured **63.6% vs live `abyss_st`** (176 clean games). v104 = **59.4% vs
  st on paired 9600-seed fixtures** vs v102's 58.3% — marginally ahead, under the 65% bar.
  If uploading now: use v104.
- **v105 dropped** (dead-queen early consolidation): regressed 41.7% vs v104 / 44.4% vs st
  on j0020, and +3/−11 paired locally. The lane file stays in `workspace/abyss_v105` for
  reference but is not a candidate.
- All other lanes dropped or neutral — see the table in `knowledge/20_devin_lane_evals.md`.
  Params are inert (they move margins; losses are discrete structural events).
- **Pending: j0019** = v104 all-maps benchmark vs v102+st (352 games, seeds 9500-9503),
  running on worker wkr2b — its result is the formal ship-vs-65% confirmation.

## Environment (Ubuntu VM)

- `~/bc-tools/env.sh` exports KVMRUN, BC_PY (~/.venv-bc/bin/python — need ≥3.11), UNSWBC_PKG,
  WABT_BIN, SIMDE_INC, KVMRUN_CC. Source it before any kmatch/kvmrun use.
- `~/bc` = eval worktree; main repo `/home/ubuntu/repos/battlecode`.
- `~/queue` = devin-queue worktree: `jobs/<id>.json`, `claims/`, `results/<id>/`,
  `workers/<id>.json` heartbeats (≤20min). Results are gitignored — `git add -f`.
- Match runner: `cd ~/bc && source ~/bc-tools/env.sh && $BC_PY tooling/kmatch.py run
  --cand BOT --base OPP --maps <list> --seeds N --seed-start S --jobs 4 --tag TAG --keep-replays`
- Replay forensics: `handoff/tooling/parse_replay.py` (event types: dragonAction/
  dragonUpdate/dragonDeath/sonarPing/roundStart/pearlCountdown/turnStart/dragonSplit/tileChange).
- Map sets: SMALL=10 small, BIG=12 big, MID=6, std=SMALL+MID, all=22; `--maps` takes comma lists.
- kvmrun rules (AGENTS.md): serial benchmarks, paired seed sets, never WASM_RT_SEGUE_FREE_SEGMENT.

## Rules of engagement

- Every lane = one hypothesis vs flagship, mechanism metrics reported alongside W/L
  (queen deaths, longest@r499, eaten@r60, adj-eat rate, dist-2 kill rate).
- Clean evals require team-keyed sonar + paired explicit seeds; tuning seeds 1000s,
  eval seeds 8500-9700 disjoint.
- When dropping a lane: postmortem approach-wrong vs implementation-wrong (user's rule).
- Adversarial code review on every diff before it ships.
- weakhold is a documented structural loss (sonar ~2.4 cells, unwitnessed queen deaths) —
  do not iterate on it.
- Timeline: qualifiers ~Oct 10; the user's upload step is manual.

## Open threads worth trying next

1. Collect j0019 → ship/no-ship vs 65%; if under, v104 still beats v102 → upload v104.
2. Small-map elimination races (~55% of losses) — every lane neutral so far; needs a
   mechanism that changes discrete brawl outcomes, not weights.
3. Escorted queen-hunt (assassin role exists unused): kill their queen EARLIER than ours dies
   to flip queen-fate games — the only decisive lever that produced wins (slay) untried at scale.
4. Salvage: caged-queen detection (schooltime), ally-aware exit *legality* (seal done right).
