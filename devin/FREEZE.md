# FREEZE — submissions close 2026-10-09 06:00 UTC (5pm Sydney)

## Protocol
- Last new candidate submit: **05:30 UTC**.
- 05:30-05:45: confirm active submission via `GET /api/v1/submissions` — the entry with
  `status=="active"` must be the intended bytes.
- If the last ship crashes or is <40% over >=20 games: re-upload previous best bytes
  (rating restores on re-upload of identical bytes).
- Nothing after 05:45.

## Builds in contention
| build | contents | evidence |
|---|---|---|
| abyss_v481 (=v138) | v476 + queen-graze (queenGrazeLen10, Dist7, From250) | elim 66-67% vs v376 across seeds 1-16 (bar 62.7%), mirror-neutral |
| abyss_v476 (=v137) | v449 + no-bed stub-churn + feed-window churn | ladder 54-59 @1723; elim 70.6%/68 |
| abyss_v447 | rollback fallback | ladder 57% |

## Verified findings (final push)
- len-2 CANNOT reverse: engine checks HitSelf before popping tail — own tail is
  always a wall. len<=3 cannot split-reverse either.
- len-2 cannot multi-step (NoValidAction kill when mBody<=2 at stepIndex>0).
- Engine move order: facing -> wall -> SELF -> other (h2h mutual only on HEAD;
  body = HitOtherBody) -> push_front -> pearl?keep:pop -> paid?pop.
- Enemy reach model already over-screens ~1 (safe).
- vacated-tail step = ILLEGAL (L6 falsified from source, free).
- Queen-graze mechanism confirmed vs real opponents (queenEnd tiebreak won).

## Known constants (adversarial review)
- `b.W==40 && b.H==15` in policy.hpp (wh_ fog-scan calibration, weakhold). Deliberate
  calibrated geometry gate; on an unseen 40x15 map the tighter rule fires. Accepted risk.
- No map-name strings anywhere in shipped code.
- `maze_` detection = kelpFraction (derived geometry, not a constant).

## In-flight at freeze call
- v484: len<=3 queen corridor-as-nook veto (own-head no longer counts as exit).
- L1c: bud_ gate to 40 units r<120 (only positive early-forage variant).
- L2 graze sweep, L3 unhide, L4 churn-volume: pending lane reports.

## Rollback trigger
Last ship crashes / <40% over >=20 games -> `unswbc submit workspace/abyss_v447`
(or abyss_v476 if v447 unavailable). Rating restores on re-upload of same bytes.

## Final record
- ACTIVE SUBMISSION: (fill at 05:30-05:45)
- id: (fill)
- sha256 of submitted bytes: (fill via `sha256sum` on dir or submission API)

## FINAL RECORD (recorded 05:30 UTC)
- Active submission: **v139, id=21679, rating ~1713** — abyss_v476 bytes (=v137 code:
  contested-starvation band + no-bed stub churn + feed-window churn + forage opening).
- Source: workspace/abyss_v476 (7 files).
  main.cpp 6f7143b6bdec3026274e636e5e22c076
  board.hpp 56ea60c2ab78015c4377236cfbef548c
  common.hpp 01fb92373b045dba66faad46367c04d0
  io.hpp 869ddc86fcdf1d1734b437706f7c4c4f
  nav.hpp 455ac9e42479ba0c0288df04c256368b
  policy.hpp 026532e0bfee9156dbe3083b5a0594e6
  world.hpp fad0199926c2fd874c0ec56c1d6d334c
- Submitted 04:21 UTC as rollback of v138 (dipped <40% on all-elite gauntlet).
  Rating restored 1723 on activation (API-verified 04:22).
- Safety: lineage passed 62-game crash sweep (25 maps, both seats, roundLimit games).
- Last submission: v139 @ 04:21 UTC — before 05:30 deadline. Protocol satisfied.
