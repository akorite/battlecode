# Lane: losssurvey — ladder loss-cause survey

Pure-analysis lane. No bot changes. Deliverable: loss-cause data from live ladder replays.

## Methodology

1. `battles?limit=100` → latest 100 battles (ids 937711..978868, 2026-10-03 06:02–17:26 UTC).
   Pagination params (`before`, `offset`) are silently ignored — latest-100 is all we get.
   Fetching again later extends coverage; keep `ladder_data/battle_details.json` as cache.
2. `battles/<id>` per battle → per-game `mapName`, `winner` (a/b), `hasReplay`.
   Our side = 'a' iff `match.teamAId == 351`. API is rate-limited (~1 req/1.5s sustainable);
   429s recover with a few seconds of backoff.
3. `battles/<game_id>/replay` → **302 to signed R2 URL; refetch Location WITHOUT the auth
   header** (urllib auto-redirect forwards it and R2 400s). 96/96 loss replays fetched, ~287KB gz.
4. `tooling/replay_metrics.py <file>` works directly on the downloaded file
   (gzip→depack→capnp via `handoff/tooling/parse_replay.py`). `map` field is null in
   ladder replays — take `mapName` from the API. `botA`/`botB` hold submission ids
   (15960 = abyss_v104, 14613 = v101-revert); all 96 replays' our-side bot matched the
   expected submission.
5. Scripts + caches: `tooling/losssurvey_collect.py` (collector),
   `ladder_data/` (raw JSON: battles_list, battle_details, games, replay_index,
   loss_metrics.jsonl, loss_merged.json), `ladder_replays/` (96 .replay files — big, local).

## Findings (v104 = live bot, 30 ranked losses in window)

**Queen survival is THE loss axis.** 29/30 v104 losses had our queen die; the one
exception was an Autarky starvation (+49 eat60 gap). Every `teamEliminated` loss (16/30)
followed a queen death. Opponent queen died within 10 rounds of ours in only ~4% of
queen-death losses — we are losing duels, not trading.

| # | bucket | n (v104) | est. Elo gain |
|---|--------|----------|----------------|
| 1 | **Schooltime r1 queen hitSelf** (deterministic bug) | 6 | highest — see below |
| 2 | **Mid-game queen death r51-200** (h2h 12 total, hitWall 9) | 13 | high — biggest bucket |
| 3 | **Late queen death r201+** | 7 | medium |

### 1. Schooltime r1 hitSelf — deterministic regression, ~20% of v104 losses

All 6 v104 Schooltime games: queen dies `hitSelf` on round 1, both sides (3× side-A,
3× side-B). v101 never did this. Mechanism (verified in replay 974917/973117):

- r0: queen `split` → engine rotates her rear segment: parentBody `[[3,2],[3,1]]`,
  child takes `[[2,2],[2,1]]` — her neck now sits **north** of head.
- r1: bot issues `move N` (planned before/without observing post-split body) → head
  steps into own neck → hitSelf.
- Same stale-geometry kills the fresh child at r0: child `[[2,2],[2,1]]` facing S
  issues `move N` into its own tail (dragon 6, r0, hitSelf).
- Opponent runs the same scripted split (their child suicides too — e.g. dragon 7) but
  their queen's r1 move happens to be safe → free win for them.

Schooltime is currently W0/L6 on v104 — the map is an auto-loss. Fix: re-derive legal
moves from post-split body before the queen's r1 action (or ban N for her first move
when neck is north). Expected: converts ~6 auto-losses per 30-game window into ~50/50
games → roughly +3 wins/30 ≈ +30-50 Elo.

### 2. Mid-game queen death r51-200 — 13/30 v104 losses

- `hitHeadToHead` 12/30 overall (mean r146): queen hunted/rammed. Worst maps:
  Tower Defense (3), Queen Of Spades (2), Stripes, Trophy, Devil, Autarky.
  v104's slay feature makes our queen aggressive; she also gets hunted — check whether
  slay-commit leaves her exposed when reach is contested.
- `hitWall` 9/30 (mean r134): queen pathing into kelp/walls mid-game. Clusters on
  weakhold (2), Trauma (2), Tower Defense, Queen Of Spades, Australia, Prisoners
  Dilemma. Likely navigation/wall-edge bug rather than combat — replays show she
  drives into static walls while travelling (e.g. 978580 r23, 976478 r146).

### 3. Late queen death r201+ — 7/30

Endgame queen loss at r233-372 (h2h 4, hitWall 2, hitSelf 1) while consolidating.
Lower priority: fixing early+mid buckets shrinks this naturally.

### Secondary observations

- Non-Schooltime hitSelf: only 2 (Portals r263, Islands r251) — late-game, rare.
- Pearl starvation rarely kills alone: only 1/30 v104 losses had queen alive at end.
  Large eat60 gaps (Devil +59, Autarky +47-54, Islands +38-46) accompany queen deaths —
  they decide *how quickly* a lost queen becomes a wipe, not whether we lose.
- No timeouts in any of the 96 losses. Ship-gate concern is clear here.
- Opponent spread: we split ~even with ~1430-1470 (so-lonely 13W/12L on v104) and lose
  to 1500+ (NeungzAI 7/13, zach 4/11, meowest 2/8, Sponge 0/5 all-window). Top-20 push
  needs converting the 1500s (9W/21L) — that's the queen-survival buckets, not new offense.

## Actionable ranking for bot lanes

1. **Fix Schooltime r1 hitSelf** (post-split geometry): deterministic, high confidence,
   big share. Also re-check the same stale-plan class for fresh children (they suicided too).
2. **Queen defense vs hunts** (hitHeadToHead r37-347): evaluate escort/keep-away or
   stricter slay commit conditions; 12 losses.
3. **Queen hitWall pathing** (9 losses): audit nav on weakhold/Trauma — she runs into
   static walls mid-map, not combat deaths.
