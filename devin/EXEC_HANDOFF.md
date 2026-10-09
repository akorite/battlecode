# Cognoscenti — executive handoff (Oct 9 ~01:55 UTC)

UNSW Battlecode bot "Cognoscenti" (team 351, user akorite). Goal: best possible
ladder standing before the qualifier; original ask was top-20.

## Deadlines
- **Submissions freeze: Oct 9 06:00 UTC (~4h from now)** — the last ACTIVE
  submission becomes the qualifier bot.
- Post-freeze: 3-4h autoscrims on the SAME 17-map pool → seeds snapshotted.
- Qualifier: Oct 10 6pm Sydney, best-of-7, ALL UNSEEN MAPS, top-10 eligible
  advance.

## Current live build: v138 = abyss_v481 (rating ~1738, fresh)
Lineage stack (each piece shipped on a positive gate):
- v263-era architecture (61% real record base)
- roam-leash: worker forage discounted ×0.4 beyond ~10 tiles of the swarm,
  active only r≥150
- contested-starvation band: starving workers suicide-eat bait beds
  (starveLocal 2.5, all maps)
- universal queen hide: queen stays len-2, flees threats, all maps
- **stub-churn economy** (the campaign's best mechanism): len-2 pawns ram-die
  (wall>self>nva) near a teammate ≤2, throttled id%3==round%3, units≥45, r≥60.
  Replicates winners' corpse-recycling (verified in engine source + replays:
  ~55-58% of their pawn drops are eaten by allies within 2 cells)
- **queen-graze** (shipped ~45 min ago): hiding queen banks length up to 10
  while enemyDist>7 and r≥250; sheds the excess into workers under threat.
  Targets measured queenEnd forfeits (4/11 bell losses were `longest` wins
  lost because our len-2 queen faced their len-11-15 queen).

## Ratings arc
- Today: peaked **1772** (v137), equilibrium ~1738-1766. Old lineage (v122)
  plateaued ~1690 and still holds the best raw record 157-100 (61%) at lower
  opposition level.
- Seed band ~90-105. Top-20 needs ~2150 — out of reach in-window.

## Verified loss anatomy (25-replay census of v137)
- 9/16 losses = contested-starvation (ate <35% of pearls)
- 10/16 reached the bell (r499); ~4/11 bell losses forfeited on queenEnd
- Structural gap vs 1700+ teams: **2x per-unit early forage throughput**
  (eff .052 vs .105 pearls/unit-round from r0) → 2.9x splits → 2.3x heads by
  r120. Compounding production gap; ~180 param/mechanism variants washed on it.

## Bracket (seed ~95-100)
- R1 vs Error 418 (~1300) — should be routine
- R2 vs **π** (~2043-2307): nva-stall churn ~67/game; queen dies h2h med r128;
  starves under early contested pressure. Counter = early bed contest +
  mid-game queen hunt (our profile already).
- R3 vs **Sabotage-d** (~2214-2312): heaviest wall-donation churn seen (166
  suic/game, splits 289); only loses to heavier churn volume or early-queen
  snowball r0-100.

## In flight
- v481 independent-seed confirm: 20/23 on seeds 9-16 (replicating 67%/118 on
  seeds 1-8) — rules out seed luck.
- v482 gate on a lane VM: queen un-hide at r300 vs 390 (param-only).
- Lane validating queenEnd-decides-bell on top-20 replays.

## Freeze decision (T-1h, ~05:00 UTC)
- Keep v138 if early ladder record ≥ v137's pace (52%+ vs similar bracket).
- Rollback if it craters (<40% over ≥30 games): resubmit dir `abyss_v447`
  (verified, 57% record) or `abyss_v449`-lineage v476 dir.

## Key paths / commands
Repo: `/home/ubuntu/bc` branch `devin/v120`.
- Variant dirs: `workspace/abyss_vXXX/` (v447 = rollback, v476 = v137, v481 = v138)
- Verdict log: `devin/hypotheses.md`; state: `devin/STATE.md`; freeze plan:
  `devin/FREEZE.md`; forensics: `devin/lane_reports/` (bracket_final.md,
  starve_counter.md, pawn_donation.md, wall_churn.md)
- Match runner: `cd /home/ubuntu/bc && WABT_BIN=/home/ubuntu/bc-tools/wabt/bin
  ~/.venv-bc/bin/python tooling/kmatch.py run --cand X --base Y --maps <csv>
  --seeds 8 --seed-start N --jobs J --tag T` → results/T/games.jsonl (candWin)
- Ladder: `curl -s "https://game.battlecode.au/api/v1/submissions?limit=N" -H
  "Authorization: Bearer $BC_KEY"`; matches: `python3 tooling/ladder.py
  matches --team 351 --n N`; replays: `tooling/ladder.py replays`
- Submit: `cd workspace/abyss_vXXX && ~/.venv-bc/bin/unswbc submit . -n NAME
  -d "desc"`

## Hard rules (user-set)
BC_KEY never printed/committed; rollback always allowed; no map-name/size
tables; safety guards queen-only; never veto worker splits or opening moves;
≤12 submissions/hr; log hypotheses; adversarial review before submit; push
every candidate to GitHub; eliminated-class testbed bar = 62.7% vs abyss_v376
on 8 elim maps.
