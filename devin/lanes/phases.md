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
- **GROW** (→ consolAt, or swarm collapse): keep replacing losses, nobody feeds.
  Champion election warms up (champFallbackRound = consolAt-40); champ relays arm at consolAt-30
  (~5M/turn each, per review guidance). tradeSlack=0, tradeMinUnits=6.
- **CONSOLIDATE**: feed machinery on (feed/queenFeed/fallback = now), relays already running,
  champMargin=3 (stable election), all splitting off, queen stops budding. tradeSlack=0.
- **PROTECT** (r>=452 AND teamBestLen >= foeBestLen+8, hysteresis via monotonic phase): feedStop=now,
  near-pacifist (tradeSlack=-1, tradeMinUnits=12).

`consolAtRound()` picks the CONSOLIDATE round by map class — steering-3 replaced the
w*h dimension gate with computed SHAPE features over SEEN topology (fog of war):
`open = tiles > phaseOpenTiles(2000) || (kelpEdgeFrac < 0.15 && deg1Frac < 0.02 && half the
edges observed)`; unseen maps default to corridor. This reproduces the integrator partition
(corridor: maze, trauma, weakhold, portals, slithery, dilemma, trophy, stripes, devil, qOS,
td, autarky, default vs open: islands, schooltime, unsw, australia, big_empty, stronghold) —
only miss is trophy, which is brawl-gated anyway. Class results: corridor → 320 (v104's own
feed timing), open → 320+NC/50 clamped 355-390 (~r360), ≤700 brawl → 999 (never).

**Queen escort switch** (steering-3 evidence: 89% of pre-r100 queen deaths are len2-3 movers
on unescorted queens; our queen dead by r330 in 20/22 open-map games): under phaseCtl the
idle-escort block also arms at `phaseQueenEscortFrom`=40 during OPEN/GROW — an escort body
takes the cheap h2h hit instead of the queen.

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
4. ~~Wider feed ring~~ (s0c, REVERTED at s0f): champFeedDist 2→3, feedMaxLen 6→8 — drops land
   too far out; leaked to bystanders. Kept 2/6.
5. **Drop-zone deference** (s0d): in CONSOLIDATE+, non-champ dragons zero pearl beliefs within
   `champDropZone`=3 cheb of the heard champion — drops stopped being eaten by whichever ally
   stood closest (the parked champ was gaining ~+6 off ~50 dropped pearls).
6. ~~Home-biased camp anchor~~ (s0e, REVERTED): anchoring toward queenCell parked the champ on
   cold corner beds — 12.5% autarky vs 37.5% without. Nearest-hot-bed anchor kept.
7. **Queen camps in CONSOLIDATE** (s1a+): `queen_ && phase>=CONSOL` parks at the nearest hot bed
   like the elected champ — she is the beacon feeders die into (v104's queen survives to r500
   2x ours). Champ itself already carries growerDanger=3.0 > queenDanger=2.0 — no extra fear.

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
pending s0b analysis). Final twin-build measure (akdbg phases-ON vs offdbg phases-OFF, 5 games):
median depth 4 vs 4 — no measurable CPU delta from the phase layer (it is a per-turn O(1) param
rewrite + one O(NC) anchor scan per champ-lifetime).

## Results

| run | matchup | result |
|-----|---------|--------|
| ph1_aut2 (v1, interrupted) | autarky vs v104 | 2/4 |
| ph2_aut5 (camp+gossip+margin, consolAt 417) | autarky vs v104 | **60%** (6/10): A-seat 4/5 incl. 2 elims + c66 bell, B-seat 2/5 |
| ph3_aut5 (locateChamp warmup fix, consolAt ~379) | autarky vs v104 | 60% (6/10): A 4/5, B 2/5 |
| ph4_dbg_def (collapse fix) | default s2 vs v104 | 2/2 ELIMINATIONS r282-285 |
| s0b_phases (mech 1-3, feeds@2/6) | autarky,weakhold,default,trauma vs v104, 4 seeds | autarky 12.5% (1/8), weakhold 0%, default 62.5% (5/8), trauma 0% — longest@499 ~10-20 vs 25-48 |
| s0c_phases (+feed ring 3/8) | autarky,trauma vs v104, 4 seeds | autarky 12.5% (1/8), trauma 25% (2/8), longest 10.2 vs 29.5 |
| s0d_phases (+drop-zone deference) | autarky,trauma vs v104, 4 seeds | autarky **37.5%** (3/8), trauma 25% (2/8), longest 10.1 vs 26.8 |
| s0e_phases (+home-biased anchor) | autarky,trauma vs v104, 4 seeds | autarky 12.5% (1/8) — home anchor parks champ at COLD corner beds; REVERTED |
| s0f_phases (ring back to 2/6, keep defer) | autarky vs v104, **8 seeds** | autarky **31.2%** (5/16), longest 18.5 vs 35.5 — deference retained |

## S1 — local tournament (paired seats, 4 seeds per map)

vs **abyss_v104** (s1a = pre-axis consolAt 240+NC/7; s1c = corridor/open axis):

| map | s1a win% | s1c win% | note |
|-----|----------|----------|------|
| weakhold | 62.5% | **62.5%** | was 0% pre-phases |
| trophy | 50% | 50% | brawl class (≤700) — never consolidates in s1c |
| default | 50% | **62.5%** | corridor 320 |
| autarky | 25% | **37.5%** | corridor 320 window — champ hit 41 as seat B |
| trauma | 12.5% | 12.5% | corridor 320 still loses attrition |
| stronghold | 0% | 0% | v113 also 0/8 — not a regression |
| **ALL** | 33.3% | **37.5%** | axis added +4.2 overall, +12.5 autarky/default |

vs **abyss_cf** (s1b, same 6 maps): ALL 37.5% — autarky 62.5%, trophy 62.5%, default 50%,
weakhold 12.5%, trauma 12.5%, stronghold 25%.

Kill criteria: **zero r≤5 queen deaths** in s1a (48) and s1c (48) replays (parse-checked:
early deaths are ids 2-13 — the standard opening brawl on both bots).

### CPU/turn (abyss_akdbg vs abyss_offdbg twin run, autarky+default)
The phase layer is a per-turn O(1) param rewrite plus one O(NC) anchor scan per champ — cost
shows in search `depth=` within the fixed 75ms budget: median depth 4 phases-ON vs 4 phases-OFF
(5 games). No measurable CPU delta.

## Full 22-map gate vs abyss_v104 (gate_phases, 4 seeds both seats — w*h-axis build,
before the steering-3 feature classifier which is partition-equivalent)

**ALL 35.8% — honest negative vs the v113 baseline.** Per-map (baseline in parens):

| map | gate | map | gate | map | gate |
|-----|------|-----|------|-----|------|
| Colosseum | 62.5% | australia | 50% (37.5) | islands | 37.5% |
| arena | 25% (50) | autarky | 37.5% (50) | maze | 0% (0) |
| default_small | 37.5% (37.5) | big_empty | 37.5% | portals | 12.5% (12.5) |
| devil | 50% | default | 62.5% (50) | schooltime | 87.5% |
| **dilemma** | **0% (50)** | queen_of_spades | 62.5% (50) | **slithery_fight** | **0% (25)** |
| stripes | 37.5% (62.5) | stronghold | 0% (0) | trauma | 12.5% (37.5) |
| tower_defense | 62.5% (75) | trophy | 50% | **unsw** | **0% (25)** |
| | | weakhold | 62.5% | | |

**NEW 0/8 maps vs baseline: dilemma, slithery_fight, unsw.** Regressions also on trauma
(-25), stripes (-25), arena (-25), autarky (-12.5), tower_defense (-12.5). Gains on
weakhold, default, qOS, australia, schooltime, Colosseum, devil.

Mechanism read: `alive@r499 38.8 vs 9.2` (we hold the swarm) but `longest@end 17.5 vs
30.4` and `alive@r50 5.7 vs 6.5` — the phase machine over-produces late and under-produces
early: the GROW-doctrine param rewrite weakens the r50-100 elimination economy (steering-3's
6.7d/16.4L@r25 → 10.3d/25.5L@r50 benchmarks), and consolidation still doesn't convert the
swarm into a champ on big maps. SMALL 45.0% vs BIG 28.1% — the open-class axis is the
worst seat.

**Verdict: net-worse than v113 baseline across the ladder spread — do not ship as-is.**
Options: (a) iterate on the early-econ axis (GROW doctrine is likely where dilemma/
slithery/unsw regress — phase gates replaced budAlive/split gates that drove elim-map
production); (b) keep the machine phaseCtl=0-inert for integrator cherry-picks (consensus
gossip + drop deference + warmup fix are independent wins per S0). The steering-3
classifier + queen-escort switch landed after this run — they are partition-equivalent
resp. additive and were not what lost the maps.

## Steering-4 iteration (v6, post-gate)

CONSOLIDATE recipe from computers' decoded +130:

- **Front-loaded feed window**: `queenFeedRound = consolAt - phaseFeedBurst(20)` during
  GROW — feeders wake early and walk to the heard champ head, so arrivals concentrate in
  the window's first ~20 rounds (winners stack 12.9 recycles into r360-379; we had ~5.3).
  Measured on s2a_feed replays: 13-21 deaths in consol+20 — in-band.
- **In-place deaths at the champ's head**: `champFeedDist 2→1` in CONSOL — the champ is
  parked so adjacent suicide lands drops at its head (was: hitSelf at distance 2 scattered
  drops). Winners die in place on the champ's path (~50 noValidAction/game); ours now die
  adjacent rather than scattered.
- **Champ lock ~r330**: election warmup already at consolAt-40 (open ≈r328) — kept.
- Phase transitions verified on debug replays: autarky OPEN→52→320→452,
  schooltime 0→75→368→452 — classifier lands corridor/open correctly.

s2a_feed (autarky,schooltime × 2 seeds vs v104, akdbg): **4/8 = 50%** (schooltime B 2/2
incl. r197 elim, autarky A 1/2 c30 bell, schooltime A 1/2); champ lengths c30-48 vs the
gate's 12-14. L@300 still 9-14 (target ≥10 borderline).

### reg_phases (v6, dilemma/slithery/autarky/unsw/trauma × 4 seeds vs v104): **12.5%**

dilemma 0/8 (ALL eliminated r73-237 — production collapse), slithery 12.5%, trauma 12.5%,
unsw 12.5%, autarky 25% (A-seat elims win). Mechanism: `alive@r50 1.5 vs 6.0`,
`splits@r60 7.5 vs 13.5`, splits r0-25 counted in replays — 6-9 vs v104's 12-15. The
early-econ regression is the v6 **unscoped queen escort** (r40 escorts pulled ~3 foragers
off every corridor game in the production war) PLUS trade doctrine drift:

- v7 fix A: `tradeSlack=0`→1 / `tradeMinUnits`→4 in OPEN+GROW — refusing +1-shorter
  mutual kills left enemy killers alive adjacent → `splitEnemyDist=2` blocked our splits
  (compounding: fewer units, more enemy proximity, fewer splits).
- v7 fix B: `phaseQueenEscortFrom` scoped to `mapIsOpen()` — the queen-duel evidence is
  big-map bells (our queen dead by r330 in 20/22 open-map games); elim maps end before
  r330 and need every forager. Corridor maps no longer pay the escort tax.

### v7_check (dilemma/slithery/autarky/unsw × 4 seeds vs v104): **34.4%** (was 12.5%)

| map | v6 | v7 | note |
|-----|----|----|------|
| dilemma | 0% | **50%** | A-seat: eliminated v104 at r49 every seed; B-seat: deterministic r92 elim loss (asymmetric map side?) |
| autarky | 25% | **50%** | incl. B-seat r443 elim c37 |
| slithery_fight | 12.5% | 25% | |
| unsw | 12.5% | 12.5% | residual: open-map champ gap (longest@end 19 vs 31) |

Trade-doctrine restore + corridor-escort removal recovered the elim maps. Remaining
deficit concentrates in open-map champ conversion — v104's queen-champ reaches ~31 while
our elected champ plateaus ~19 (front-load + fd=1 improved conversion but not enough on
the biggest maps).

### v8/v9 (open-map iteration, unsw+slithery × 4 seeds vs v104)

v8 (consolAt clamp 368 + NC-scaled burst): slithery 37.5%, unsw 0/8 — alive@r499 62 vs 22,
longest@end 18.2 vs 28.6.
v9 (CONSOL feedMaxLen=10): unsw 12.5% (first unsw win, c24 bell), slithery 12.5% — net
12.5% overall. Conversion still capped: longest@end 18.8 vs 30.6.

### v10 result (feedHeardDie 8): unsw 0/8, slithery 25% — 12.5% net

feedHeardDie=8 did not convert the swarm either. Residual is ARCHITECTURAL: v104's
queen-champ IS the consolidation point (feeders die into her path and she walks over the
pearls); our elected champ is elected ~r300+, often the wrong dragon, and eats drops only
when its path crosses them. alive@r499 62 vs 21 / longest@end 18.6 vs 27.6 across v8-v10.

**Lane verdict: honest negative overall.** The phase machine is mechanically verified
(transitions 52/320/452 corridor, 75/368/452 open; seen-topology classifier; front-load
13-21 deaths in consol+20; in-place deaths; open-scoped escort; hysteresis) and wins
elim-map econ (dilemma+autarky 50% in v7), but open-map bells stay ~12-37% — the
elected-champ architecture cannot out-feed v104's queen-champ. Recommend: keep phaseCtl
as a research switch (off in any shipped bot), cherry-pick the independent S0 wins
(saturating gossip, drop-zone deference, locateChamp warmup fix — all phaseCtl-gated but
trivially portable), and treat open-map consolidation as its own lane if pursued.

## Still weak

- B-seat autarky bells: our champ lands 8-16 vs their 35-39 (A-seat we reach 12-66). Feed throughput
  in the ~75-110-round window still trails v104's 170-round window.
- PROTECT phase never triggered yet in observed games (we never hold +8).
- Feed conversion ceiling: ~19-22 suicide deliveries/window; our swarm loses ~35+ bodies to
  head-to-head attrition that never reach the walk. Home-anchor (s0e) did NOT fix it — the
  remaining gap is walk attrition through the contested mid-field on autarky-class maps.
- Diagnosis of the residual gap: v104's queen-champ parks deep by doctrine; feeders die into her
  in friendly territory. Our elected champ camps mid-map → transit deaths. s0d added drop-zone
  deference (allies don't steal the drops); queen-camp added for s1a.
- Trauma remains the unresolved map (12.5% both axes): corridor attrition decided before our
  consolidation window pays — same pattern the integrator measured on corridor classes.
