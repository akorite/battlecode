# Lane 5a: team phase controller

**Task:** one macro layer + explicit state machine (OPEN / GROW / CONSOLIDATE / PROTECT_LEAD) deciding
phase from round, map features (not names), queen state, and length/dragon counts; it drives the feed
window, forage-vs-feed balance, trade willingness and vetoes — replacing the scattered round-gates
(feedRound, queenFeedRound, champFallbackRound, *RelayFrom, growRound, midEnd, lateSplitUnits,
queenBudUntil, queenHideUntil). Behind param switch `phaseCtl` (kParams sets it 1). Phase logged per
turn in BC_DEBUG (`ph=`).

Worker: session devin-13f9c33210b04125bd9da40bc7345e09, branch `devin/phases`, bot `workspace/abyss_ak`
(v113 + phase machine), debug build `workspace/abyss_akdbg` (same + BC_DEBUG).

## Confirmed cause (one line, from autarky lane)

Our doctrine consolidates on a fixed clock (~r320) while the attrition war still runs — we freeze
production, bleed ~19 length through r300-400, and the feed suicides scatter because the champion they
die for is re-elected every few rounds; winners keep producing (~39 dragons at r400) and consolidate
one stable champion late.

## Design

`World.phase` (per-dragon persistent memory, Policy is rebuilt per turn) holds a monotonic phase:

- **OPEN** (r0 → 18+NC/28, clamped 25-75): produce only. All feed/relay/grow gates at 999,
  lateSplitUnits=unitLimit (never stops splitting), tradeSlack=0, tradeMinUnits=8.
- **GROW** (→ 240+NC/7 clamped 290-425, or swarm collapse): keep replacing losses, nobody feeds.
  Champion election warms up (champFallbackRound = consolAt-40); champ relays arm at consolAt-30
  (~5M/turn each, per review guidance). tradeSlack=0, tradeMinUnits=6.
- **CONSOLIDATE**: feed machinery on (feed/queenFeed/fallback = now), relays already running,
  champMargin=3 (stable election), all splitting off, queen stops budding. tradeSlack=0.
- **PROTECT** (r>=452 AND teamBestLen >= foeBestLen+8, hysteresis via monotonic phase): feedStop=now,
  near-pacifist (tradeSlack=-1, tradeMinUnits=12).

Collapse trigger is *relative* — `units <= 8 && units*2 <= peakUnits` — a fresh 6-dragon team at openAt
is not a collapse (bug fix: absolute threshold flipped default games straight OPEN→CONSOL at r54 and
starved them).

## Mechanisms added on top of the phase machine (after S0 instrumentation)

1. **locateChamp warmup gate**: its internal `min(feedRound,queenFeedRound)-40` gate blocked the
   election all through GROW (feedRound=999) — first self-champ appeared ~r476, 60 rounds late.
   Under phaseCtl the phase-owned champFallbackRound is the only gate. Consensus now forms by ~r380.
2. **Camping champion**: elected champ in CONSOLIDATE+ parks at the nearest pearl bed
   (`wChampCamp` pull). Its relayed position stops churning -> feeder drops land within reach.
   (Feed-target cells were churning across 115+ distinct cells/10r before.)
3. **Saturating champ gossip**: forwarders emit the champ report on every free ray that doesn't hit
   an enemy (was: 1 ray/turn) — heard-champ coverage went from ~30% to ~75-90% in-window.

## S0 (mechanism evidence — abyss_akdbg vs abyss_v104, replays kept)

Autarky seat-A game: election from r379 (window r339+), dominant champ cell stable r450+,
self-champ held title 38+ rounds parked at a bed. Bell won 37 vs (their) ... see s0b table below.

### Bugs found by S0 instrumentation
- Cascade transition: OPEN->GROW inside one call let the same call re-evaluate GROW->CONSOL; combined
  with the absolute `units<=8` collapse, default flipped to CONSOL at r54 (production frozen,
  eliminated r157-210). Fixed with else-if chain + peak-relative collapse; default s2 then
  ELIMINATED v104 r282-285 both seats.

### CPU/turn
Every turn spends its full 75ms budget by design (search deepens until the deadline) — the real CPU
metric is `depthReached`: median 5 pre-saturation (s3 autarky debug game), vs ... (post-saturation
pending s0b analysis).

## Results

| run | matchup | result |
|-----|---------|--------|
| ph1_aut2 (v1, interrupted) | autarky vs v104 | 2/4 |
| ph2_aut5 (camp+gossip+margin, consolAt 417) | autarky vs v104 | **60%** (6/10): A-seat 4/5 incl. 2 elims + c66 bell, B-seat 2/5 |
| ph3_aut5 (locateChamp warmup fix, consolAt ~379) | autarky vs v104 | 60% (6/10): A 4/5, B 2/5 |
| ph4_dbg_def (collapse fix) | default s2 vs v104 | 2/2 ELIMINATIONS r282-285 |
| s0b_phases (all fixes) | autarky,weakhold,default,trauma vs v104, 4 seeds | running |

## Still weak

- B-seat autarky bells: our champ lands 8-16 vs their 35-39 (A-seat we reach 12-66). Feed throughput
  in the ~75-110-round window still trails v104's 170-round window.
- PROTECT phase never triggered yet in observed games (we never hold +8).
