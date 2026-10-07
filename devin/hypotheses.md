
## H-C4: corridor wedge veto (reproduced → implemented)
- **Claim (report5 §C4):** queen dies entering a 1-wide run contested by another dragon at the far end (Autarky r70 ally head, Maze r131 enemy body) — two-way reservation only covers cells next to her head.
- **Fix:** queen-only veto — dest with exactly 2 open neighbours starts a deg≤2 walk (≤8 cells); any non-self seen segment in the run or on its exit cell ⇒ treated as deadend (stepTerm −2000, terminal, demoted below open moves).
- **Falsifier:** autarky pair record should improve; queen non-ram deaths on corridor maps must not rise.
- **Result:** smoke +60%/20g (autarky 2/4→4/4). qNonRam 0.35 vs 0.25 — watch on full board.

## H-C5: exit-reservation scope (reproduced → implemented v2)
- **Claim (report5 §C5):** unconditional ≤2-exit reservation costs Devil (8/24 vs 15/24 without) — marks both exits INF in crowded openings.
- **v1 (len≤2 && head≤2 gate):** FAILED — reservation never fired (queenLen rarely ≤2); queen non-ram 0.35 vs 0.05, kept 12.5% vs 60%. Rejected.
- **v2 (regionReach<30 gate):** reserve only when she is geometrically pocketed — open-field crowding exempted.
- **Falsifier:** devil ≥ v143 without queen non-ram regression elsewhere.
- **Result:** smoke 60%/20g combined with C4; devil 2/4 same-pairs. Full 68g gate running.

## H-C5 resolution: all reservation forms wash (parked)
- **v3 (end-block-only):** ending-legality reject on her exits, no transit INF — 46%/68 vs v143, queen metrics even but big-map bells lost (autarky/islands pair losses). REJECTED.
- **v4 (end-block always + transit-INF pocketed AND r>=60):** 45%/20 smoke — the r60 delay re-opened the autarky farm corridor during formation. REJECTED.
- **v5 (transit-INF when pocketed, end-block always — union):** 45%/20 — corridor-exit end-block is itself an econ cost. REJECTED.
- **Verdict:** protection pays ≈ what landing-rejections cost in every scope tested. Parked; the doomed-fallback exit-last ranking stays (free).

## H-C4 attribution fix: corridor veto is inert at n=20
- v148 = v143 + C4 alone: 50%/20, ALL metrics identical to base to the decimal — the veto ~never fires on the smoke set. The earlier autarky 4/4 was the C5 region-gate, not C4. Kept in the stack (queen-only, free insurance).

## H-PLANT: champion lock (WC recipe — shipped to gate)
- **Claim (report6/user):** WC locks their champion ~r330 and converges feeds on a stationary head; ours roams so drops scatter (29% adjacency).
- **Fix:** champFallbackRound 400→330 + w_.champAnchor — self-elected champ locks onto its head cell (needs regionReach>=12) until feedStop; moderate bel=1.2 anchor target keeps it hovering ~3-5 cells (2.5 froze it and starved the champ: stronghold 44 vs 61).
- **Bug found in review:** anchor must live in World — Policy rebuilds per turn so a per-turn member only decelerated (v149a). Fixed before gate.
- **Result (deceleration variant):** 51.5%/68 vs v143 — longest@end +2.9, qNonRam −31%, qlen@end +0.3, pairs 3W/29S/2L.
- **Result (true lock):** 60%/20 consolidation smoke — autarky+unsw converted, ZERO pair losses, qAlive@end doubled (0.333 vs 0.167), kept-after-theirs 44% vs 0%. 68g vs v138 running.

## H-SCORE: r499 scoring is lexicographic (VERIFIED 35+/0 miss)
- **Model:** winner = max(queenEnd, then longest, then total) — queen's end-length FIRST (0 if dead), longest dragon second, team total third.
- **Evidence:** all 35 r499 replays in v149L_v138 predicted with zero misses, including both counterintuitive stronghold cases (lost 96-vs-47-longest with dead queen; won 41-vs-45 with qEnd 17 vs 4).
- **Doctrine consequences:** (1) queen survival to 499 auto-wins vs dead-queen boards; (2) qlen@end is literally the primary score — feeding her is the top mechanism; (3) champ lock handles only the both-dead (0=0) axis; (4) "queen wins length races" is literal, not metaphor.
- v149's win edge IS this: qlen@end 3.79 vs 2.65 (+43%).

## H-FEEDFLOOR/H-UNHIDE: both wash (v150, 50%/20)
- feedMinUnits 3→8 on >2000-tile maps + queenHideUntil 390→300: qlen@end IDENTICAL (3.167), alive@end +2.3, unsw pair loss. Queen dies 75% before unhide matters; when she lives, feeders still can't reach her. REJECTED — binding constraint is survival+reach, not timing.
- CONFIRMED BUG (priority 1): kParams line `p.champFallbackRound = 360` overrode the 330 decl — live v149 ran 360. Fixed in source; next build carries it.

## 2026-10-04 (post-restart batch)

**H-PORTAL2 (scout picker fix)** — mechanism: scout moves scored +5.8 but never selectable (dest<0 skipped in pick loop; safeFirst vetoed). Fix: pick/depth/fallback allow why=="scout", queen excluded, wScout 6→2.
- S0: portals freeze BROKEN — 900 pearls eaten vs 5, longest 21 vs 5. ✓ mechanism
- S1 (24g, pre-queen-gate+wScout6 binary): **41.7% — NEGATIVE.** Worker stream-through → deaths 59 vs 42, escort drain, qDead 0.79 vs 0.67. v151b (queen-gate + wScout=2) re-gating.

**H-MIRRORHUNT-final (autarky)** — corrected aim (queen's mirror, seen-symmetry): **37.5%/24 — DEAD, parked permanently.**

**H-QFEED (earlyecon, 4-variant)** — feeding queen r200+ negative in every config (sacrifice > drops; death cell walls her). Screens: qs2 +5.5pp qAlive@end at 50% pair = marginal. **Queen-feed CLOSED; survival is escort/evasion-geometry bound.** Pending: pocket's threat-conditional escort + queen-anchor.

**H-TORUS (explore)** — Board::id() wraps unconditionally; qOS mutual-elims = invisible seam-approach h2h (17.2/game/side). Earlyecon checking loss asymmetry on queen before building a guard.

**H-PACE (explore)** — BC_PACE revisit-penalty on v127 base: schooltime swept 2-0, alive@499 23.5 vs 3.7, longest 36 vs 13.7 vs cf. Porting to v149 base now — first artifact with big alive@end deltas.

**H-CHFEED (pocket v150 merge)** — die-in-place SPLIT-0 works (22.2/game, 23% adj vs 18%) but 45%/20 wash. Gap identified: queen-champ never plants → stale-head feed deaths. Feeds into v153 spec (queen anchor + threat escort).

## H-QTRAP (2026-10-04) — phantom loopRoom disables ALL queen dead-end vetoes
- Observation: dilemma queen deterministic hitSelf@r25 both seeds; replay shows her walk a 1-wide cul-de-sac (14,11->15) scoring "forage" +1 at r20 while the seenOnly scan flagged unproven=1.
- Mechanism: `loopRoom = sc.cycle && sc.cells > newL && sc.frontier == 0` is computed on the OPTIMISTIC (fog=open) scan; on every map except weakhold (so && wh_), fog leaks phantom cycles → loopRoom always true → `!loopRoom` gates the veto off. Queen dead-end veto never fired outside weakhold.
- Also found: C1-class "unproven" flag was computed correctly (unp=1) but ignored.
- Fix (v156): loopRoom requires proven loop in the seenOnly scan; a proven-exhausted non-cyclic thin-frontier region counts as `tree`.
- Prediction: dilemma queen survives r20-25 (picks N/E at r20); queen dead-by-pocket deaths drop on all small maps.
- Kill condition: v156 <50% vs v149 on the elim-map fixture, or queen pinned into starvation.

## H-RAMREACH — 2026-10-04
- Mechanism: the queen's ram screen prices an enemy's kill-reach as
  freeSteps + L - 1, ignoring pearls: a rammer that eats mid-path gains
  segments and out-ranges the screen by one tile per pearl eaten. Real
  reach = free + L - 1 + pearls-on-path (rules audit).
- Fix (v160): per-enemy reachBoost = count of seen pearls inside its
  reach field (cap 4), added to the queen ram/lead/heard screens.
- Prediction: on pearl-rich queen-death maps (qOS/stripes/dilemma),
  cand queen dies measurably less often (qDead/game down, more
  r66-elims like the s2-B win survived).
- Kill condition: 24g board <52% or new r0-60 queen deaths vs v149.
- Status: GATING (tag v160_ramr).

## Composite plan (flagship v16x)
- Base v157 (portal picker + C5; autarky 68g board pending) +
  qRamAdj (pocket's weakhold-dim adjacency ram fix, verified 4/8 wh) +
  reachBoost if v160 passes + pocket's v153 queen module (anchor +
  threat-conditional escort + evasion) when delivered + v159 seam fix.
- Each piece only merges if its own gate passes — v142 composite lesson.

## H-QMOD composite (v163) — 2026-10-04
- v163 = v157( portal+C5 ) + portalGuess=0 + reachBoost + qRamAdj +
  pocket v153 (queen soft-localization + threat-escort + die-in-place).
- pocket's three-gate attribution on the SAME 20g set: latch 65% /
  locked pivot 50% / none 40% — the soft-latch IS the mechanism.
- Note: v153 gates used champFallbackRound=360 (live semantics);
  v163 keeps 360 for measurement fidelity, flagged in review.
- Prediction: ≥55% vs v149 on 17-map board, qlen@end up,
  queen-dead down on escort maps.
- Status: GATING (tag v163_full, 68g).

## H-C5MARG (resolved 2026-10-03)
**Question:** does C5 (queen exits==1 reservation) inside v157 hurt queen survival (autarky's read: kept-after-theirs 24.2% vs 38.5%)?
**Test:** v165 (portal-only) vs v157, 15 maps × 2 seeds × both seats = 60 games.
**Result:** v165 = 41.7% (0W/25S/5L) — **C5 is net-positive inside v157.** qlen@end 3.89 vs 2.78. autarky's in-composite read inverted; the exit-reservation buys queen length that scores tier-1.
**Decision:** KEEP C5 in the flagship line. v157 shipped.

## H-FLAGSHIP-168
v168 = v157 + reachBoost + qRamAdj + die-in-place(SPLIT-0). Board vs v149 running (75%/8 early).
v169 = v168 + feedBurst staged behind it.

## H-SELFKILL — queen self-kill is the top band-loss leak (OPEN, building)

**Mechanism** (pocket diag, 11 band losses): 6/11 = the queen corners HERSELF —
hitWall×2, hitSelf×2, hitOtherBody×2 at r68-494. In 3 games our longest was
equal/better: the self-kill alone forfeits lexicographic key-1. The calibrated
trap scan (unproven-room veto) was gated `W==40 && H==15` — dead on every map
those deaths happened.

**Prediction**: with the scan on for the queen on every map (v173:
`wh_ = queen_||pocketMap_`), queen non-ram deaths drop on autarky/maze/unsw/
australia without pinning her on open maps. Kill condition: queen non-ram
deaths/game doesn't drop OR queen-dead rises (she pins herself to death).

**Build**: v173 = v168 + qRamAdj ungated (adjacency screen was also dims-gated —
OFF on trophy/devil/stripes/australia where 5/11 rams landed) + wh_ as above.
Smoke: 12 diagnostic maps, both seats.

## H-EARLYDEF — early swarm deficit on elim maps (OPEN)

**Mechanism** (same diag): a3-5 vs a8-21 at r50 → ram → elim. We DO split ~9-10x
by r60 — bounded by pearl intake (20 vs 29 @r50) and swarmSplitLen=4 (need 2
pearls/worker to split). Prediction: swarmSplitLen 4→3 (v174) fields +1-2 units
by r50 on elim maps without collapsing fights. Kill: alive@r50 doesn't rise or
early losses worsen on the elim set (trophy/devil/stripes/weakhold/arena/
dilemma).

## Gate rule change: 75% (was 70%) — increments are dead; only structural
moves ship now. v168 stays live until a candidate clears 75%/≥100g.

## H-FEEDCAP — feedMaxLen=6 leaves consolidation half-done (OPEN, built)

**Mechanism** (m1098277 Australia, 43 dragons/462 total lost longest 24 vs 28):
only len<=6 dragons feed; mid-size units (7-23) can neither feed nor be elected
→ swarm stays distributed, champ underfed. 45 noValidAction deaths fired but
drops went to a churning election target (autarky saw 9 champs re-elected).

**Prediction**: fMax = champLen_-1 when champHead_>=0 (v176) converges to one
long dragon on BIG maps; longest@end rises on australia/unsw/autarky without
attrition collapse (feedMinUnits=3 floor). Kill: alive@end drops >20% with no
longest@end gain (over-consolidation into a dead champ).

## v173 post-mortem — FAIL 39.6%/48
wh_=pocketMap_ suppressed budding on pocket maps (splits@r60 -16%, the
documented pin regression), queen-dead flat 0.75 — pure cost. Reverted;
wh_ dims table stays pending a legal feature. qRamAdj isolated to v177.

## H-WALLBLEED — fleet hitWall attrition is one-sided (OPEN)

**Data** (m1100855 trauma live loss, team-B=us): 275 hitWall + 55 noValidAction
vs opponent's 14 total. Deaths spread all rounds (peak r350-400), clustered in
OUR territory (x0-39, y0-23 of 48-wide board) — foraging into dead-end pockets,
then least-bad = wall death. Opponent never does this.

**Mechanism**: workers forage into shrinking pockets with no region-awareness;
when cornered the eval has only lethal moves. Same root cause as queen
self-kill but fleet-wide. Worker-side fix must be scoring/foraging-target
(rules ban worker vetoes only on splits/openings; a pocket-avoidance bias in
forage scoring is a legal preference, not a safety veto — needs care).

**Kill condition**: if pocket's room-shrink variant (queen-only) drops
wall-deaths/game in its gate, extend the mechanism to worker forage targets.

## H-QUEENCOST — the dominant evaluative frame (CONFIRMED PATTERN)

Every candidate that drains units near the queen kills her more, and a dead
queen forfeits key-1 regardless of longest. v176 proved the mechanism works
(longest@end +15%) yet lost (queen-dead 0.812 vs 0.750). v175 same shape.
Rule for all future candidates: queen-alive@end and queen-dead/game are the
PRIMARY gate metrics — a variant can win longest/alive and still be a kill
if it taxes her escort or her drop supply.

## v174/v175/v176 post-mortems
- v174 (splitLen 3): 0%/24 — len-3 children too fragile; production halved.
  The early deficit is INTAKE/fragility, not split rate. DEAD.
- v175 (C7+champMargin): 47.9%/48 — champMargin stays autarky-only.
- v176 (feedMaxLen relax): 46.9%/32 — consolidation works but taxes queen.
- v177 (adj-ungate): 50%/48 identical — keep as zero-cost insurance (the
  ungate only fires vs ladder rams; self-play can't produce them).

## 2026-10-05 ~19:00Z — Full-gate verdicts (v206, v208, v209)
- v206_full (leash≥400 composite): 52.7%/201 — FAILS ≥55/LB>50. Killed at 201.
- v208_corr (deadEnd r≥30 on trauma+TD): 45%/20 — dead on its own target maps.
- v209_full (v206 + tradeSlack=0 NC≤900): ~52.7%/203 — fails. Small-arm 54.0 zero-ish pairs was real; BIG arm drifted to ~51.5 (the marginal doesn't transfer to >900 boards where slack=1 still applies).
- v210 fired: tradeSlack=0 globally — tests whether the -1-trade bleed exists on open boards too (smoke on the >900 subset).
- earlyecon closure: presence-priced worker evasion dead BOTH sides of reach boundary (inside-reach dodge converts death mode, outside-reach buffer taxes forage w/ h2h flat). Remaining surfaces: body-geometry escort screens, spawn placement.
- Honest arithmetic: v200-lineage ≈ +3pts vs live. The 55/LB50 bar needs ~56% — nothing in the lineage reaches it without another mechanism-class gain.
- v210 global tradeSlack=0: 47.6%/42 on >900 boards — dead (open boards need the +1 tempo)
- v211 density pull w=1.5: 36.4%/33 — dead; 4th clustering-restriction family member. Blob is a RESULT of production, not a cause to imitate.
- v212 NC-scaled budAlive (18+NC/512 cap 24): smoking, trending flat ~50%/38
- v213 queen escape sprint: built (paid multi-step out of a full ram pin; fires only when every 1-step landing is in enemy reach)
- v209_full FINAL: 52.7%/220 — fails gate. Lineage maxes ~+3 vs live.
- Refill retargeted to proven-only set (Knight Capital/chad gdp/nooberGamer/1234/verity/tozoman/Wapowpow/TonyS/Sarvottam/Oswald/Nexus/Larper/JRN/Hydra), 72 queued.
- Elo 1600, last-80-set window -51 elo net (challenge drift, autoscrims at parity).

## 2026-10-04 swarm-metrics reframe (v209_full cross-tab, decisive)

Parse of all 220 v209_full replays cross-tabbed queen deaths x outcome:
- LOSSES (104): bothQdead 64 | ourQdead+theirQlive 31 | bothQlive 9
- WINS (116): bothQdead 64 | theirQdead+ourQlive 37 | bothQlive 15

IMPLICATION: 70% of losses are decided by swarm metrics (longest/total),
NOT queen survival — both queens die in 64 and key-2 longest still loses.
Queen-defense mechanisms have a ~31-game theoretical ceiling minus their
mobility costs = net ~0 (confirmed: v213 52%, v215 45%, v216 46%).
THE GAME IS PRODUCTION VOLUME: winners split ~164/game vs our ~44,
eat 2-4x. Remaining avenue with +5 headroom = grower-scarcity fix
(promoteLen) + budding rate (growerKeepBase) + spawn placement
(earlyecon spec: split only near density centroid).

Verdicts: v213 queen-escape WASH 51.7%/118 (fires ~2/34 by design — rescue
not shield); v214 selfChamp-escape DEAD 46%/76 (champ pays tail to flee =
shrinks its own score); v215 escort-ring-2 DEAD ~45%/38 (clogs queen);
v216 qRamAhead+2 DEAD ~46%/50 (wider ring = more flee tax); v217
queen-champ anchor staleness SAFE 47%/34 0-pair-loss (rare-state fix,
kept for composite); v218 promoteLen 10->7 in flight; v219
growerKeepBase 4->2 in flight.

## 2026-10-05 PM volume tests round 2 (vs v209, all-maps s3)

DEAD/WASH: v218 promoteLen7 41%, v219 keepBase2 44%, v220 growerChild3 47%,
v221 slackMax1700 50%, v222 champ-pull 47%, v223 dedie(len<=3) 44%,
v224 feedRadius20 46%, v226 dedie+bait-midfeed 48%.
ALIVE: v225 lateSplitUnits 20->9999 = 53.8%/26 early — post-r300 worker-split
gate release; swarm keeps churning (winners field 2x alive count mid-game).
v228 = v225 + feedRound 400->430 (split freeze lift into feed window) fired.
v227 = swarmSplitLen 4->8 (winners split at ~9.7 pre-len, children ~5
survivable + instantly productive) fired.

earlyecon CLOSED spawn placement: timing veto falsified, spawnInner all
radii dead (45.8/45.8/50). Their decisive datum: winners' parents split
at plen~9.7 vs ours ~7.2 -> children born ~len5 not ~len2. Chain is
production volume <- parent survival to len5+ <- survival surface closed.

## 2026-10-05 PM3 lanes converge on funnel structure
pocket (sd/dc stats): deliberate feeders die ~4 cells from bud site,
~8-10 from rolling longest — die-in-blob, no path-to-anchor. The
discriminator is VOLUME + COMPACTNESS: winners split median 164/g
(peak 426-591) vs our ~44; deaths 93/g deliberate vs our ~40 cap.
midFeed already implements die-in-blob; gap = bud volume (food intake
upstream) + swarm tightness ~10 cells around anchor.
autarky (adversarial): v200-line anchor machinery verified live;
residual queen-champ hole = champAnchorId_==ourQueen != chId (v217
fixed exactly this — in v235). feedBurstDist 14 > feedRadius 12 dead
slack. qRamAdjMinTiles shape-blind on qOS/trophy/weakhold.
earlyecon: deadEnd U-turn premise engine-verified; spawn closed.

## 2026-10-05 PM5 lane verdicts
earlyecon DECISIVE: standing army equal at every checkpoint (3.5/2.9
r25, 8.2/8.2 r100) — winners run 3x THROUGHPUT (splits 1.9x/3x/3.5x).
Pearl intake at PARITY — food not the bottleneck; births-per-food is.
Gap front-loaded: 1.9 vs 3.6 splits by r25; their parents split at
~9.7 pre-len (children len~5 productive) vs ours halving at len4.
autarky FALSIFIED cohesion: nn tightness is a readout of army size
not a lever; winners hold MORE territory (+2.2 cenDist). Do NOT build
wCohere centroid pulls. Only live signal = straggler suppression
(-2.3pp, entangled with survival).
EXPERIMENTS FIRING vs live: v237 (composite minus midFeed-small),
v238 (v237+slay-stalk<=900), v239 (v237+workerBud len10->child5).
v235_live final ~53.6%/335 — fails bar; BIG arm 57% worked, SMALL
arm 49.7% dragged by midFeed-everywhere.

## 2026-10-07 ~04:45Z ladder-forensics cycle
- Portals paralysis root cause hunt: m1326800 ddabap W — we produced
  2 splits all game (3 units trapped/starving 400r) vs their 571.
  Mirror games show BOTH sides produce only 2-4 on portals — map is
  starvation-class for our code; ddabap portals-navigates to food.
  Suspected unrouteable portals: board.NC > portalGuessMinTiles(512)
  was strict -> portals (NC=512) excluded; manyPortals_ kills dense
  guesses too. v380 (guessEnds 24, minTiles 500): 46%/26 — guess
  routing did NOT unlock production. Scout-crossing machinery exists
  but units still starve. Verdict: mechanism deeper than routing.
- v379 splitRoom 8->4 gated NC<900: 48.8%/41 — dead, roomy veto was
  not the corridor blocker.
- v376 mirror (ship-relevant): BIG 55.6%/45 SMALL 47.5%/40 ~n85.
  Ladder read since ship: Elo 1608->1649 net-positive organic.
- ~105 variants on lineage. Param space exhausted; next levers are
  map-doctrine or search, not params.

## 2026-10-07 ~05:30Z food-net extension verdicts
- v381 young-cover (len<=3 stay near blob, foodDist cap 6): 48.6%/37
  BIG 52.9 SMALL 45 — dead.
- v382 heardFoodDist 18->40: 44.4%/18 — dead.
- v383 broadcast bed countdowns (foodBedWindow 10): 44.4%/18 — dead.
- v379 splitRoom4 NC<900: 48.8%/41 — dead.
- v380 portalGuess on dense maps + Portals NC: 46.2%/26 — dead.
NET FAMILY at local optimum; all five extensions negative/wash.

## Autarky lane conveyor-geometry forensic (top-10 replays)
- Feed ring is dChamp 4-8 (not point-blank); champ anchors inside
  ~8 of swarm centre. OUR anchors resolve ~19.5 out — v385 adds
  wChampHome pull toward densest-beacon centre.
- Winners' queens bud at r0-1 med 0.5 (~86%); ours ~53% r0-1
  (55/123 measured on v376 replays — roomy check blocks the rest).
  v384 retries queen's early bud at smaller child sizes.
- Queen orbit ~8-12 (earlier 5.6 did not replicate on this set).
- nva deaths inside swarm for everyone (med dAlly 2).

## 2026-10-07 ~11:30Z forensic-port cycle
LANE FINDINGS LANDED:
- pocket corridor census: winners forage dead-end branches 34-482
  entries/g vs our 6.6 — len-2 walks in eating pearls, dies at tip,
  len-1s sweep. We BANNED ourselves from that income (v201 veto
  cost -16% eaten/g). Retired for len<=3 workers.
- pocket queen census (220g): queen alive in ALL wins, dead in 89%
  of losses. Killers approach visibly 4-7 cells for ~5r while she
  drifts ~3 (no evasion). 11/49 rammers were newborn len-2 splits
  born adjacent — no warning window possible.
- autarky conveyor geo: feed ring dChamp 4-8, champ inside ~8 of
  swarm centre (ours resolve ~19.5 out). v385 adds wChampHome pull.
- autarky r0-bud: winners' queens split r0-1 at 86% vs our ~53%
  (measured on v376 replays, roomy-check blocks at spawn).
- pocket stub-churn: winners suicide len-2 stubs ~250/g in-blob
  beside pearls vs our ~10/g len-3. Volume gap, not site.

VERDICTS:
- v384 queen-bud-retry: DEAD FLAT 50%/74 — retrying bud sizes
  doesn't move the needle.
- v385 champ-home: 53%/32 borderline positive, folded into v390.
- v386 corridor-len<=3: 53.3%/60 POSITIVE (weakhold splits 2->78
  in unlocked-channel test).
- v387 queen see-flee: flat 50%/24 — wash.
- v388 churn-max (foodDist 3, maxLen 3): DEAD 27%/11 — over-churn.
- v389 splitLen3 on big: DEAD 33%/9 — len-3 fatal even open maps.
- v263 vs v376 head-to-head: 45%/30 — lineage did NOT drift;
  v263's 61% record was a weaker-field artifact.
IN FLIGHT: v390 = v386 + v385 composite, 176g vs v376.

## 2026-10-07 ~15:30Z verdicts
- v390 composite (corridor+champhome): 51.2%/80 — champhome drags it.
- v385 champ-home solo: 50.0%/66 DEAD.
- v386 corridor alone: 56.2%/80 looked positive; on INDEPENDENT seeds
  (v386b s5-8): 50.0%/170. Combined 126/250 = 50.4% — SEED LUCK, wash.
- v391 heardEnemy reach6/w2: 46.4%/69 DEAD (over-flee costs forage).
LESSON: corridor economy port did NOT transfer — our len<=3 units
enter corridors but don't convert the income to wins (they die at
tips dropping pearls, but our swarm lacks the len-1 sweeper density
winners field to collect them). Seed-1-4 positivity was luck.
STATUS: ~120 variants on v376 lineage, 10 consecutive fails/washes.
Forensic-port vein exhausted this round. Elo ~1643 stable.

## 2026-10-07 ~19:30Z
- v392 split-rate (eat-veto off growers + parent roomy->1): 51.8%/164
  WASH. The explore lane's rate-prescription (77 vs 43 splits by r120)
  didn't convert: extra splits die as fast as they spawn.
- ~15 consecutive dead/wash mechanisms on v376 lineage.
CONCLUSION: the rate gap is a DOWNSTREAM symptom — intake per unit
is the binding constraint, bound by swarm coverage, bound by rate.
Circular: no single lever enters the loop. v376 architecture at its
local ceiling (~50-52% vs any perturbation).

## Cycle 03-Oct (~05:00Z)
- v396 blob-bot negative control: 4.9%/41 — doctrine stack load-bearing, no churn shortcut
- v398 all-in kamikaze (swarm hunts enemy queen when our queen dead + theirs alive): 50%/36 dead — killing their queen doesn't convert
- v399 coveredFavour 0.15→0.32: 55%/40 — drifting, borderline
- v400 roam-leash OFF until r150 (pocket intake census: +73% gap lives in r0-120; leash strangles ramp): 60%/30 tracking — tl100 +65% mechanism-verified
- v401 centroid-leash (nearest-friend → swarm centroid): 56%/25 — noise
- sweep.py automated param search ~19 evals: 5 flags, all confirms regressed to ~50% — seed-luck screen needs >=58% stage-A
- Standing: everything converges 50-53%; intake loop is circular; v400 is the live shot

## v128 SHIPPED (~10:30Z) = abyss_v400
v376 + roam-leash gated r>=150. Gate: 115/206=55.8%, LB(90)=50.1,
seats 58/103+57/103. First replicated mechanism in ~130 variants:
leash strangled r0-120 forage (pocket +73% intake gap lives in ramp);
tl100 +65% mechanism-verified. Rolled back instantly if it regresses.
