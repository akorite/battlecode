
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

## 03-Oct ~15:00Z — v129 SHIPPED = abyss_v407
v400 + bed-camping (worker within 3 of live bed: far targets x0.25).
Combined gate: 59.0%/117 vs v400 over two independent seed sets.
The parked-crop mechanism from pocket's census transferred on the
v400 base. Micro-variants racing: v412 campFar .12, v413 campNear 4.
Dead: v409 splitskirm 43%, v410 regroup pull 21%, v411 widefeed 46%,
v406 noleash 42.5% (leash is net-positive post-150 — phase-gate optimal).

## 2026-10-07 — THE GATE FALSIFIED (major methodology finding)
Ladder audit: v122 (abyss_v263) 157W-100L = 61.1% REAL; v123-v129 combined ~46%.
Every post-v122 ship passed its mirror gate (53-59% vs parent) yet the lineage
regressed on ladder. Mirror gates measure delta-vs-parent, not ladder strength —
mechanisms can beat the mirror while being weaker vs real opponents.
Elo 1610->1496 in ~1h under v129 (2-8). ROLLBACK: resubmitted v263 as v130.
New protocol: candidate must ALSO beat abyss_v263 (best-ladder build), not just
live. Experiment running: v407 vs v263 head-to-head.
Also: real date ~Oct 7 — qualifier Oct 10 is ~3 days out.

## Oct 7 late — mechanism portability falsified twice
- v420 (leash r>=150 on v263): 43.5%/23 — the leash HURTS on the v263 base.
- v419 (bed-camp on v263): 45.7%/46 — camp doesn't transfer either.
- Conclusion: mechanisms are CONTEXT-BOUND — they won mirror gates inside their own
  lineage's coupled system, not as standalone doctrines.
- v130 (rollback to v263 code): Elo recovered 1496 -> ~1692 in ~2h. v122's 61% real
  record re-confirming. v130 stays live unless a candidate beats BOTH v263 AND v407.
- v421 fired: v407 + v263 queen doctrine (hideMinTiles 600, unhide 390) — tests whether
  the universal-hide is what breaks transfer to real opponents.

## Oct 8 ~00:30 — v423 starveall = first ladder-derived mechanism win
- Replay forensics vs real opponents: both sides ~14 alive at r100-150 but their
  per-unit intake is 10x ours (28 vs 1 splits/bin). Our workers yield contested
  beds (enemyCloserFactor) then starve — and starving_ only fires on pocket maps.
- v423 = starving_ on ALL maps (one-line: drop the pocketMap_ gate). Combined
  60%/70 mirror on the v263 base (main 63%, independent confirm 56%) — biggest
  persistent win of the campaign, and it targets a REAL divergence not a mirror artifact.
- v130 holding ~1690. If v423 finishes ~58%+ combined it ships as v131 — its
  payoff shows on ladder, rollback = resubmit v263 again.

## Oct 8 ~03:00 — v131 SHIPPED (abyss_v424)
- v263 + starveall (starving_ all maps) + contest (enemyCloserFactor .85)
- Mirror: 56.2%/64 vs v263 — thin edge but the mechanism is mirror-blind by
  construction (contesting only pays vs opponents that actually push).
- Ladder-derived: replay forensics showed opponents out-contest us 10:1 on
  shared beds at identical swarm size. Rollback = resubmit abyss_v263.
- v422 contest-alone 55.3%/114, v423 starveall-alone 55.5%/110 — both positive.

## Oct 8 ~06:30 — camp port dead a third time
- v426 = v424 + bed-camp: 36.8%/19. Camp mechanism confirmed non-portable to
  the v263 lineage on three separate attempts (v419 45.7%, v426 36.8%).
- v425 queen-scan x4: 51.6%/31 — wash in mirror (trap deaths too rare to move it).
  Cheap protection, may keep for the next composite anyway.
- Portals anomaly: opp won a bell game having eaten 2 pearls — queenEnd 5 beat
  our dead queen (hitWall r354). queenEnd decides when their queen survives.

## Oct 8 ~09:00 — food-net port dead; boxed-child churn testing
- v427 food gossip on v424: 48.5%/68 — third mechanism-class that dies on the
  v263 lineage (camp, leash, food-net all fail to transfer).
- v425 queen-scan: 45.3%/75 dead.
- v428 = v424 + boxed-child splits (small children born sealed still allowed in
  economy phase — churn babies): early 57%/14.
- v131 ladder: 10-12 vs upward-matched field, ~par. Verdict at ~25 games.

## v431 = BC_PACE re-explore bias (Oct 8 ~05:00)
- Lane census (explore, devin/explore-modes @2c1e49f): TD deaths 73% within 15
  of own spawn, 60% self-congestion (hitSelf 42/101 + hitOtherBody 19/101);
  Islands 37% >20 tiles, 54% h2h — TD is home-orbit starvation, not contest.
- Port of explore lane's pace149 (12-8/60% vs v149 base on old lineage):
  per-dragon myVisit[cell]=round on head, dest recently headed (<paceMemory=10)
  gets +2.0 danger; queen exempt (hide pacing is doctrine).
- Board: v431_pace vs v424, all maps, seeds 200-203.

## v431 dead 36.4%/33 — pace penalty kills melee
- Re-explore bias (wPacePenalty 2.0 on recently-headed cells) wins open maps
  (default 2/2, weakhold 2/2) but loses every elim/melee board (TD 0/2, stripes
  0/2, maze 0/2, trauma 0/2, stronghold 0/2, portals 0/2). Avoiding revisits
  prevents re-engagement in fights. Portability falsified again.

## v432 = starving-pull dedup (testing)
- Starving block pulls ALL workers to the same nearest unseen tile (global
  min) — the TD home pile-up mechanism (73% deaths ≤15 of spawn, 60%
  self-congestion). Each unit now min-hash-picks its own unseen target
  (h = c2*2654435761 ^ id*2246822519, argmin). Board v432_dedup, seeds 300s.

## v433 = park-and-crop countdown value (testing)
- Soon-respawn beds (cd<=8) score as live pearls at walking distance
  (0.9*gp(m) not gp(max(m,cd+1))): waiting is free when idle. friendDist
  yield + id-tiebreak parks ~1 worker per bed. Targets the adjN gap
  (their units stand beside pearls ~7-10x more). Board v433_camp, seeds 400s.

## v430 starveLocal=1.5 confirm: DEAD 45.2%/42.

## Cycle 11 (Oct 8): TD/Islands starvation class — 10 mechanisms, all wash/dead

Root cause CONFIRMED via testbed (v424 vs v376 reproduces eaten-2v447):
TD = symmetric 32x16, spawn enclaves exit single-corridor into shared
central farm. Junction seal race ~r30 decides; loser starves in-enclave
(forage flatline, not production flatline — units alive, eat ~0).

Mirror-blindness doctrine: mirror boards cannot score starvation-class
fixes (shared food in self-play). Validation = vs abyss_v376 on real
failure seeds.

Verdicts: v431 pace 36.4% DEAD | v432 dedup 52.8%/176 wash+ | v433 beds-
as-pearls 44.7% DEAD | v434 starving-bedpark 42.4% DEAD | v435 hideMinUnits
52.0%/125 wash | v436 open_-fp 57%/14 noise (s702 flip, s701 same) |
v437 crumb-ban == v436 (open_ maze-vetoed on TD: kelp 0.71>0.22, NC150>200)
| v438 dash-gate WORSE (deep pushes overextend, sealed s700-A).

Param/policy space exhausted on v263 lineage. HOLD v131 through snapshot.

## Cycle 12 (Oct 8-9, pre-freeze): bracket forensics + divestiture mechanism

BRACKET (tournaments?tab=qualifier): seed 98 @1664 → R1 Error418(1298)
→ R2 3.14159265/π(314, ~2044) → R3 Sabotage-d(46, ~2214) → R16 ~seed7-10.
META across bracket tier: all three = single-champ dominance (longest 5-6x
2nd) + early-ram queen (dies h2h @11-61 in EVERY elim loss) + massive churn
(260-410 deaths/game). π extra-weak: noValidAction 45% — self-jams corridors;
starves out vs aggressive contest (dev test 1 swept them 0-6, eat ratios
0.25-0.5). Counter = contested-mouth pressure + queen-survival opening —
exactly the v441 mechanism class.

LANE VERDICTS (all 4 reported):
- pocket opening-doctrine: r1 opener already optimal; post-opener cadence
  gap is cycle-time (they re-split 2-4x faster); NO contest asymmetry —
  eCF 0.85 matches field (explains v444 eCF1.0 wash: 50%/26).
- explore combat: h2h len-discipline already matches (92-94%); escorts sit
  on (±1,±1) diagonals not orthogonal; 3+-step paths 2.4x our rate; torus
  not weaponized.
- autarky conveyor: feeder suicides ambient all-game (d2 spike = die-beside
  -head); capture is swarm-vacuum not point-to-champ; NEW mechanism —
  shed-all divestiture: 6/22 bell games, parent keeps 2 births 28-53 champ.
- earlyecon cadence: era2 resplit 25r vs their 8r (cycle time again).

v441 = starveLocal 2.5 (v131's contested-band completion): mirror 56.0%/116
tracking; vs-v376 testbed 56.2%/16. v442 (4.0) over-fires 48.8%. v444
(+eCF1.0) neutral 50%. v439 move-cost engine fix wash 52.9%/170 — confirms
co-adapted base. v440 feedRadius16 dead.
v445 = v441 + divestiture-shed (r430+, longest dragon keeps-2 births all
→ mobile champ + heading unlock) + diagonal-escort bias (wEscortDiag .35).
Board vs v441: 9 maps × 8 seeds × 2 seats = 144g.

v445 divestiture-shed: DEAD 41.4%/29 — mechanism backfired. Our longest
@r430 ~14-18 (winners' 28-53); shedding keep-2 births a ~12-16 champ while
the mirror's champ grows to 22-24 → we LOSE the longest key we would have
won. Mechanism only pays at winner-scale bodies; doesn't apply at ours.
Escort-diag was bundled in v445 — delta not isolated.

## cycle 13 (final push, freeze Oct-9 06:00 UTC)
- v447_vs_v263 FINAL: 46.9%/130 mirror — stack loses to base in self-play
- v263_vs_v376 (real-opponent testbed): 56.1%/114 — v263 does NOT lose to real opponents either; earlier 44.7%/38 was noise
- v447_vs_v376: 60.0%/80 → vs real opposition v447 ≈ +4pts over v263, mirror undersells contest stack as predicted
- v449 (universal hide, hideMinTiles 600→0): 51.5%/66 tracking wash — small-map queen-survival adds nothing measurable
- v448 donor-liquidation DEAD (50%/56): feeders never adjacent enough at len≤12 window
- v133 LIVE: 13-7 ladder (65% early tracking)
- Doctrine update: mirror-vs-mirror gates lose ALL contest/starvation signal; vs-v376 testbed is the representative check
- v453 queen anti-box (wQueenBox spacing while hiding): DEAD 44.8%/87, queen-dead c71/b61 — spacing penalty pushed her off cover into open-field rams. Boxing is real (ladder replays: ~33% of queen deaths hitSelf/hitOtherBody while cornered by own swarm) but spacing remedy inverts it.
- v134 (universal hide) live: 7-3 early (70%)
- v447_openmaps FINAL: 34.7%/95 — v447 loses ~35% on open-farm class vs v263 in MIRROR only; vs-v376 triangular check (v447 60% vs v263 56%) says v447 still better vs real opposition. Open-map bleed = mirror artifact.
- v454 three-step forage (paid 3rd step for intake tempo): DEAD HARD 32.4%/74 — eaten -10%, splits -9%. Tempo theory falsified: paid segments cost more than arrival speed gains. The 2.4x multi-step gap in winner replays = symptom of longer dragons, not cause.
- v134 live 7-3. Freeze build decision pending v134's ~50-game record vs v133's 64%.
- v455 midFeed widen (r60, len<=7): DEAD FLAT 51.6%/128, eaten +1.6%, splits +0.2% — churn window already saturated.
- v456 small-map budMult 1.0 (workers fight through breed phase, queen keeps 1.8): mirror 50%/40 neutral. vs v376 elim testbed: tracking +2.5pts vs v449 control at low n (69.2%/26 vs 66.7%/24). First real elim-class test design: small maps only vs REAL opponent, since mirror is structurally blind to fight-while-breeding.
- v134 (LIVE): losses still elim-class; fresh replay shows Z-A out-splitting us 31v9 by r60 on Trophy via fight-while-breeding churn (247 hitWall suicides, 598/603 adj-eat conversion on Autarky).
- CLAIM FORENSICS (pocket lane): 91.4% seen pearls never taken (ours) vs 34-45% (opp/top); 72.7% of pearls within cheb-2 of a friendly head rot 3+ rounds. Claim = pure distance, no TTL, growers claim, starving no bypass. Adjacent-drop conversion at parity 82%.
- v458 = claimTTL 4 (standing pearls contestable) + starving-bypass: early 46.4%/28, eaten -27% — contested convergence may waste trips. Tracking.
- v457 = openUntil 0 (kill forage-opening): elim mirror 47.2%/53 (dilemma 6/6 sweep, devil/trophy bleed), vs v376 real 55.1%/49 trophy 5/6. Conflicted — elim mirror artifact risk.
- v456 = budMult 1.0 elim: DEAD (49.1%/116 mirror; vs-v376 testbed equal to control).
- v134: 16-9 = 64% (tracking v133).
- CONTROL BASELINE for elim reads: v449 vs v376 on small maps = 62.7%/110. Any candidate-vs-v376 must EXCEED this, not just beat 50%.
- v457 openUntil=0: DEAD — elim mirror 52.3% BUT vs-v376 53.1% << control 62.7%. open_ forage-opening is net-POSITIVE on elim maps (opposite of earlyecon lane's finding on the v120 base — mechanism depends on lineage).
- v458 claimTTL+starving-bypass: mirror 49.4%/77 (eaten -16%), vs-v376 61.8%/34 ≈ control — neutral. Likely dead.
- v460 heard-claims-don't-veto: mirror 56.2%/32 tracking; vs-v376 testbed fired.
- v134: 16-14 stalled (0-5 waddledee upset). v263-era record 61% still the best single-sub record ever.
- ENGINE FACT (actions.cc Kill): dead dragons drop ceil(len/2) pearls on alternate body cells. Bodies DO drop — wall_churn's "bodies drop nothing" is wrong. Beds: occupancy blocks the countdown-0 spawn (pearls.cc TrySpawnPearl) — dying ON a bed drops the pearl AND frees the +4r respawn.
- autarky_elim: children die h2h <=15r at 47-67% vs winners' 3-21% — our pawns feed the ENEMY. Winners' pawns die hitWall at adj<=2 of own swarm (drops feed them). hitOtherBody 17v3. First-split eligibility 87 vs 218 reach len-4.
- opening_cadence: gap opens r20-60 via first-split eligibility, not cadence (resplit 6-7r parity). openUntil=0 REVERSED on v449 lineage — keep 48.
- v461 (fightMinLen=4: len<4 workers don't initiate h2h anywhere incl sprintTrade): boards fired vs v449 mirror + vs v376 elim testbed. Control: v449 beats v376 62.7% on small maps — must EXCEED to ship.
- v461 fightMinLen=4: DEAD — mirror 41.7%, elim vs-v376 55.1% < 62.7% control. Child h2h trades were net-fair (tradeOk already gates); vetoing loses wars.
- v463 pawn-donation (len-2 suicide near len>=4 ally): DEAD — elim 57.8% < control; drops not consumed (no anchored champ nearby), net -1 per death.
- v464/v465 champ-bed-anchor: BOTH DEAD (37.5%) — walking the champ to a bed cluster or anchoring there pulls her out of position; the anchor-at-head choice is load-bearing.
- v462 feedBedStep: WINNER tracking — 60.8%/74 big maps (feed deaths step onto adjacent spent beds: body drop + freed respawn). Full-map confirm + v466 NC>=900 gate running. Ships if confirm holds.
- v466 NC>=900-gated feedBedStep: DEAD (48.6%/74) — the big-map edge did not replicate off the dedicated seed set; seed luck.
- v462 full: DEAD (50.9%/116).
- v467 stub-churn (lane-corrected recipe: len-2 on/beside bed + ally<=2 + units>=45 + mod-3 throttle, wall/self/nva ram): elim 66.2%/80 vs v376 control 62.7% — VERIFIED elim-class gain (weakhold 16/16, TD 13/16). Mirror 51.3%/76. SHIPPED as v135.
- v468 churn+bedStep composite: bedStep dilutes (elim 63.8%/47 < v467's 66.2%). Dropped bedStep from ship.
- v135 (abyss_v467) stub-churn shipped: elim 66.2%/80 vs control 62.7% (+4% on shared maps).
- Churn ablations vs v376 elim: no-bed (v470) 70.6%/68 = BEST; body-channel (v469) 67.9%/56; max-churn composite (v471: no-bed+units35+mod2+body) 63.6%/33 + mirror 50% — over-churning rots drops. Bed gate unnecessary; consumer-proximity is the causal piece.
- v468 churn+feedBedStep: elim 60%/80 — feedBedStep confirmed dead second time.
- v470 SHIPPED as v136 (one-param relaxation of v135: pawn dies anywhere near ally<=2).
- Churn axes resolved: len-3 (v474) 69.6%, consumer<=3 (v475) 68.0%, body-ram (v472) 61.5%, churnFrom30 (v473) 63.2% — all below v470's 70.6%. Shipped recipe optimal.
- v470 vs v449 on elim maps: 50%/18 — parity vs own strong build (v449 also strong there).
- v476 churn-through-feed-window (far pawns recycle when champ feed unreachable): elim 71.9%/32, mirror 50%/26. SHIPPED as v137.
- v136 ladder: 53%/30 early, Elo 1677 climbing — churn works on ladder.
- FREEZE Oct 9 06:00 UTC (~11h). Pick = v137 live unless record craters <40%; rollback = resubmit abyss_v447 (v133, 57% record).
- v477 elim-class victim-margin (tradeOk requires enemyLen>=myLen+2 on NC<=900): elim 70.4%/27 ~ v476 parity; mirror vs v476 tracking <50% early — gate doesn't add on elim, may cost mirror. Pending.
- ENGINE AUDIT (actions.cc): Kill DOES drop ceil(len/2) pearls on body segments 0,2,4 (lane 'bodies drop nothing' claim was wrong — drops on head cell get eaten fast, look like 'no drop'). h2h kills victim THEN rammer. Step onto ANY occupied cell (ally or enemy body) = hitOtherBody death for mover — no team check. mustPayForStep pops tail for steps 2+ (len-2 cant pay = nva death = chfeed mechanism). Eating pearl = tail kept (+1 len).
- Lane reports closed: claimTTL v458 neutral (61.8% vs control); opening_cadence resplit-rate parity confirmed (worker 6-7r both) — gap is first-split eligibility (218 vs 87 reach len-4); hitOtherBody ally deaths 17v3 = congestion geometry not fixable via gates tested.
- v477 victim-margin DEAD: elim 69.0%/42 (parity w/ v476 71.9), mirror 44%/25. Equal-ram gate removes trades that were net-fine — mutual kill also clears their unit pre-recycle. Autarky 'children die h2h' asymmetry isn't exploitable via tradeOk margin.
- v478 bed-cycle positioning (on-bed die unthrottled + adjacent-bed step first): elim tracking 44%/9 early — bed-walk may stall churn tempo. Pending.
- v137 LADDER: 57%/30, Elo 1734 — campaign high. Churn verified on ladder, not just testbed.
- v479 onBed-unthrottled (on-bed pawns die instantly, no walk-step): elim 66.7%/27, mirror 50%/22 — parity with v476, no gain. DEAD. Recipe complete.
- v476_elim_b (fresh seeds 16+): 59.2%/71 — combined 63.1%/103 vs control 62.7% — positive but thin on larger sample; first-seed read ran hot. Mirror vs v449 51.5%/68 + ladder 56-60% are the stronger evidence.
- FREEZE BUILD = v137 (abyss_v476). Rollback = abyss_v447 dir (git-clean v133 code). Monitor until 06:00 UTC.
- v480 queen-intercept (len<=5 ram enemies within 2 of our queen, bypass cover): elim 62.1%/58 (< control), mirror 50%, qDead equal 8/17 — dead. Attacker-adjacent-geometry too rare to convert; pawns baited into dead trades.
- RECIPE SPACE CLOSED: every lane-report mechanism now tested or falsified across ~175 variants. Live build = optimum.
- FULL-SAMPLE VERDICT (v476/v137): elim vs v376 58.9%/192 (first-seed reads ran hot), mirror vs v449 52.8%/72, vs v447-rollback elim 47.8%/90 but +21% splits/+16% eaten economy profile. Ladder 53-57% ~1700-1737 = campaign-high zone. Mechanism is real but modest vs own builds; keeps the winners' signature that transfers to unseen maps.
- FREEZE: v137 locked-in barring <40%/40g collapse. Rollback = abyss_v447 (git-clean v133, 57% lifetime).

### v481 (sub v138) — queen-graze — SHIPPED
- Mechanism (from 25-loss replay census): bell losses route through queenEnd — we won `longest` in 4/11 bell losses but lost anyway (hidden len-2 queen vs their 11-15). Fix: hiding queen banks length to queenGrazeLen=10 while enemyDist>7 && r>=250; sheds excess into workers under threat (stash never wasted).
- Gate vs v476: mirror 51%/109 (neutral+, mechanism is mirror-thin but banked length does flip self-play bells); elim vs v376 testbed 66%/111 (bar 62.7% — the elim-class read where queen deaths/decided games live).
- Loss census (25 replays): 9/16 starve-class (eat <35%), 10/16 reached bell, qDead median 193 (4 early / 5 late). Opponent wall-churn 100-250/game confirmed; ours ~50 — relaxations stay falsified.

## 2026-10-09 02:30 UTC — engine-source audit (actions.cc verified against replay)

CONFIRMED FROM SOURCE:
- Step() checks own-body occupancy BEFORE popping tail: stepping onto ANY own cell = HitSelf
  always. A len-2 dragon can never reverse; the tail cell is a permanent wall. len<=3 cannot
  even split-reverse (both halves need len>=2). This is the hidden-queen hitSelf/hitWall death
  mechanism — cornered with tail-side as the only exit.
- mustPayForStep kills via NoValidAction when mBody<=2 at stepIndex>0 — len-2 cannot multi-step.
- Engine move order: facing set -> wall check -> SELF check -> other-dragon check (h2h mutual
  kill only when landing exactly on their HEAD; body = HitOtherBody suicide) -> push_front ->
  pearl? keep tail : pop_back -> paid? pop_back again.
- reachOf (freeSteps+len-1) over-screens real enemy reach (freeSteps+len-2) by ~1 — safe.
- fewExits vetoes {head}-only nooks correctly but counted head as an exit, so 1-wide corridors
  pass by design. v484: for L_<=3 queen, head excluded from ex count — corridors read as
  one-way nooks (she can't U-turn through them anyway).
- L6 falsified for free: "vacated-tail step" is ILLEGAL (hitSelf pre-pop check). Dead.

HYPOTHESES QUEUE (next cycles):
H1 [L5] len-2 can't reverse -> enemy len-2/3 hunters approaching our queen are also
   committed: their tail blocks their retreat. If our queen's flee keeps an enemy
   hunter's tail facing a wall/corridor, the hunter can't disengage -> squad kills it.
   Cheap: in flee/escape scoring prefer exits where any adjacent enemy len<=4 has its
   tail toward a wall (they can't U-turn either). UNBUILT.
H2 [L6] enemy sonar echoes: heardEnemies role!=1 gives enemy HEAD positions+len via
   relay — a dedicated "echo-hunt" pull for champId+5/+6 squads toward freshest
   role-0 enemy reports r150-300 = proactive interception. UNBUILT (assassin covers role-1).
H3 [L4-variant] churn on THREATENED stubs: current churn excludes enemyDist<=2. A len-2
   pawn about to be eaten anyway should prefer dying on a friendly head's adjacent cell
   (drop feeds us) vs enemy reach. UNBUILT.
H4 [L2-verified] queen-graze works (elim +66-67%, queenEnd mechanism confirmed vs real
   opponents, mirror-blind 50%). Shipped v138.
- v483 mirror-scout KILLED 45%/58 (kill rule). Mirror-cell pull dragged scouts off forage
  for no early-queen kill — the pull only matters once the assassin net sees her.
- v484 len<=3 corridor veto: elim 68/109=62.4% (at/below v376 bar 62.7 — v481 scored 66-67%),
  mirror 48%/98. Wash-to-slight-negative: pinning her in rooms costs more than the
  no-reverse traps it prevents. KILLED unless final read >64%.
- L4 structural: churnMinUnits=45 only fires in decided games (contested games run 15-40
  alive). v485=churnMinUnits 25, v486=25+len<=3 — gating vs v481 now.
