# explore lane — section-8 ideas, log-only first
Tried: mode-histogram debug build `abyss_x_modes` (v113 copy + BC_DEBUG + canonical `m=` mode per dragon-turn: qhide/qlead/queen/assassin/feeder/champ/grower/attack/intercept/support/escort/forage + bud/lean/lead flags); aggregator `tooling/modehist.py`. Mirror-identical vs v113 over 12 games = log-only confirmed.
Mechanism (6 maps × s7 both sides, ~96k dragon-turns): forage 56-91% early-mid; **feeder dominates post-300: 47-77% of all turns on stronghold/schooltime/trauma** — the late game IS the suicide-march to the champion; combat jobs (attack+intercept+support) peak ~15% early then 3-8%; escort ≈ trauma-only (20.8% mid, 6.4% stronghold, ~0 elsewhere); assassin 4-12% where it activates (schooltime/TD/trauma) but only ~25-30% of assassin turns end "assassinate" — rest fall to forage/stalk (target beyond BFS horizon); champ emerges post-300 (5-11%); grower rare (2-8%); bud flag = 100% on starvation maps (TD/trauma/dilemma, never exit breed phase) vs 4-19% rich; lean ~0-1%; lead flag 90% on devil only.
Queen-mode detail: qhide present only schooltime (NC>=600 gate); queen+qhide turns often end trapped-free (schooltime cover scrums).
Tried (2nd item, same debug build): would-be-choices log — runner-up why + score margin per turn (`s=`, `wb=` fields). **Margins: p50 = 0 on every map; 88-98% of turns knife-edge (≤2).** Most ties are same-why equivalents (two forage dirs), but cross-why knife-edges exist where they matter: forage↔stalk ≈24-26% of forage knife turns (schooltime/stronghold), assassin↔forage+stalk ~1000 turns on schooltime. Mechanistic explanation for the "all param lanes inert" history: scores are so tied that mode assignment, not weights, decides behavior — weight tuning must target cross-why knife-edges, not global thresholds.
Tried (3rd): mode-transition log (`pm=` on flip, `modePrev` on World — per-process memory; children start clean). Aggregation x_modes_trans (trauma/stronghold/schooltime s7, ~81k turns): **jobs thrash — support stints avg 1.6-1.8r, attack 2.1r, escort 2.8-4.6r, assassin ~5.6r before flipping back to forage/feeder.** A→B→A flips ≤4r: forage↔support 388-555, feeder↔forage 188-586, escort↔forage 168-360, assassin↔feeder 225 per map-pair. Hundreds of dragon-turns/game diverted mid-commute.
Tried (4th, first structural prototype): `abyss_x_sticky` = x_modes + BC_STICKY job-hysteresis — World::StickyJob {kind,key,job,until,at} written each turn by commitSticky(); applySticky() re-applies a dropped hunt(seen+worth)/escort(grower within 6cheb, no quota)/assassin(heardMemory window); sticky feeder keeps marching to last-known champ cell (fresh resolution renews the 12r hold, re-applied feeds don't — no stale-forever loop). Feeders also ignore feedMaxLen while held.
Mechanism (trauma s7, v1→v2): feeder↔forage flips 68→~0 (feeder stints 20r→58r), escort↔forage 186→117, champ↔feeder 23→25 (selfChamp contest, unhandled), assassin flaps ~gone. v1 failed because re-validation reused the same gates that flap (enemy-seen for hunts is the real signal-loss bound — ghost-chasing stays out per the wHuntHeard lesson). ms/turn flat (70.6 vs 70.5).
A/B (5 maps s7 both sides vs v113, n=10): **70.0% (7/10), BIG 83%** — stronghold+trauma sweeps; devil/dilemma/schooltime split. alive@r499 34.7 vs 28.7, longest 11.5 vs 9.3, queen-death parity (0.7 each). Flap deltas vs x_modes_trans baseline: stronghold feeder↔forage 586→30, escort↔forage 360→125, forage↔support 555→498; trauma escort↔forage 168→117, feeder↔forage 35→0, feeder stint 20→58r; schooltime forage↔support 388→223, attack↔forage 300→234, assassin↔feeder 225→153. Remaining flaps: forage↔support/attack = invisible-enemy label-noise (no pull target → ~zero cost), champ↔feeder = selfChamp contest.
Tried (5th): `abyss_x_asfix` — assignAssassin gates on b.cheb but the assassinate pull runs BFS; added distToHead(INF)→return so unreachable dragons don't take squad slots. A/B vs v113 (schooltime+trauma+stronghold, s7+8, n=12): **33% — REJECTED**. Mechanism worked (assassin turns → 'assassinate' 830/836 schooltime vs ~25% before: real attempts doubled) but outcomes fell (longest 12.8 vs 14.2). Read: unreachable members were zero-cost padding for the assassinForce check — honest squads commit more dragons from farther out and pay full diversion cost while still losing on length. Load-bearing inefficiency; don't ship. If assassins get revisited: cap commitment (count/duration), don't fix the gate.
Verdict: sticky = positive candidate (65% n=20, needs rebase onto current best); asfix dead. Remaining: stickyTtl sweep (6/20), sticky vs outside bots (abyss_combat) for cross-opponent evidence.
Cross-opponent read: sticky vs abyss_combat 40% (4/10); paired control v113 vs combat 50% — the -10 delta is exactly the schooltime pair (v113 swept 2/2, sticky split 1/2); dilemma 0/2 is lineage trait (v113 also 0/2), not sticky's. Sticky ~par vs benchmark with a schooltime soft spot, consistent with the schooltime split in the direct A/B.
Lane addendum (SPSA tuning): `abyss_x_tune` = v120 copy; driver `tooling/tuner.py` runs coordinate probes (plan `devin/tune_plan.txt`): copy→sed-patch common.hpp→kmatch vs abyss_combat on stronghold/trauma/schooltime/devil/trophy s7 both sides (5 games/probe); rows append to `devin/tuning.md`. Params: feedRound, queenFeedRound, champFallbackRound, splitEnemyDist, queenTradeSlack, sprintMax, wExposed, exposureMode, queenDanger, survivalDanger. islands.map not in local pool → trophy substituted.
Tune lane r1+r2 done (devin/tuning.md): combat fixture saturates (v-lineage structurally loses devil/trophy side-B → ceiling 8-2, all scalar probes neutral). Rebased to v127-replica + abyss_cf (50% baseline, discriminating). Movers: splitEnemyDist=2 (6-4/+15.0 — beats v120's ship), feed triple→330 (5-5/+15.8 margin), exposureMode=1 (6-4, anti-stacks with feed330), combo sd2+f330 (6-4/+12.3). sprintMax peaked at 3, relays at 330. Danger weights all flat. Top-3 vectors shipped to integrator.
Tune lane r4 (steering-3/4): relays peak @370 vs cf; fear radius (heardEnemyReach) flat; em1/em2 add early queen deaths → rejected; portal probes (wPortalScout=8, combo) 7-3 but collapse r499 totals (45 vs 116) — elim-win lever, hand to earlyecon routing fix. Final S2 vectors: sd2 (6-4, r100 deficit halved, tot 136), feed330 (longest 41.2), sm2 (tot 162, dlen +15.0).

## pace (re-explore bias) — 2026-10-04
- `abyss_x_pace` = abyss_x_tune + BC_PACE: World::myVisit (per-dragon last-head round), +wPacePenalty 2.0 danger on cells headed within paceMemory 10r; queen exempt (sealed-cell pacing is doctrine).
- Target: schooltime frontier pacing (r135-170: ~15-19 dragons/side in 4-9 cell loops, incl both queens by design). Mechanism confirmed: revisit_frac 0.27→0.14 vs cf pairing baseline.
- vs abyss_x_tune (same base, s7, 5 maps): 5-5; schooltime swept 2-0, alive@r499 23.5 vs 3.7. Trauma-A flip = the only loss.
- vs abyss_cf (s7, schooltime/stronghold/trauma): 4-2, longest@end 36.0 vs 13.7, stronghold swept, no elim flags. Remaining pacers: exempt queens + all-exits-visited dither.
- s8 recheck (trauma+stronghold): trauma swept 2-0 (s7 flip = knife-edge noise), stronghold 0-2 — net vs own base ~7-7, map noise everywhere except schooltime 2-0 (the fix's target). Tooling: tooling/loophist.py measures pacing windows.

## qOS mutual-elimination mechanism — 2026-10-04
- Repro: x_tune self-play queen_of_spades s1-s6, 12 games. MUTUAL-ELIM at s6 (r36: starters id2+id3 both h2h; r45: A queen id0 h2h with B child). Plus s2 r32 partial (id1,id2 starters). Queen dies 1.0/game both sides; h2h = 17.2 deaths/game/side on this map.
- MECHANISM (replay-verified): the world is a torus — `Board::id()` applies `x%=W, y%=H` unconditionally in stepRaw, on every map, not just qOS. Two dragons march straight lines on the same wrapped axis approaching the seam from opposite ends: raw-grid distance ~30 (invisible to each other under fog) while toroidal distance shrinks 1/turn. Both step through the wrap on the same round, land adjacent head-on, engine kills both. id1 trace: (0,29)→(0,33) straight S for 6r; id2: N at (0,0)→wrap→(0,34) adjacent — neither had adjacency data until death. Same at s6 r36 (id3: (5,34)→(4,34) S; id2: (4,1)→(3,0) N→wrap).
- WHY OUR CODE MISSES IT: (a) `crossing = dest != b.id(X+DX,Y+DY)` compares against the MODULO'd naive cell — a wrap step reads identical to a normal step → the wBlind blind-exit busy-check and wPortalLoiter never fire on seam crossings (wFog still pays via !crossing). (b) All enemy-danger (enemyDist_, heardEnemyReach, head-in-reach) only covers VISIBLE or HEARD enemies — a far-side-seam enemy is in neither set, zero danger until collision. (c) Straight-line forage on knife-edge scores commits both starters to the seam in the opening; ~15-20% of seeds have opening geodesics crossing the same seam region → the r~36 multi-starter wipe.
- Escort hypothesis (2) refuted: kills are starter-pair head-ons on the seam, not body-wall collisions. Partners were the opposing starter/child, no escort wall at the kill cell.
- FIX IMPLICATION (structural, not param): (1) detect wrap steps as crossings — |dx|>1 or |dy|>1 — and price the invisible far side like portals (wBlind busy-check). (2) seam-boundary occupancy: standing on a wrap-boundary row/col in fog = an invisible enemy can arrive next turn; add a seam-exposure danger on ending turns there. (3) heard-relay already BFS-wraps correctly — only fully-invisible head-ons are uncovered. Any fix must be torus-aware everywhere, not qOS-special-cased: the seam exists on all maps.

## v143 C-pack attribution — 2026-10-04
- Base: workspace/abyss_v143 (origin/devin/v120 = v139 + a_portal10). Singleton variants abyss_v143c{1,2,3} — one piece each. Fixture: weakhold,trophy,stronghold,qOS,dilemma ×2 seeds both seats (n=20). Tags: c1attr(+c1attr2 dilemma), c2solo, c3solo. Earlier c1attr also covered portals.
- C1 (unproven veto queen-scoped `(unproven && queen_)`): fixture 8-12. dilemma 0-4 BOTH seats/seeds — the bleed. Elsewhere clean 2-2; portals (extra) 4-0 sweep = the gain. qDead flat all maps (dilemma 4-4). VERDICT: bleeds dilemma — queen veto on unproven pins her on that map; safe nowhere until dilemma understood. Possible mechanism: dilemma's fog layout makes her room "unproven" and the unconditional veto overrides loopRoom rescue.
- C2 (queen bud gate `queen_&&hiding_&&r>=50&&parentRoomy<2`, hasRoomyMove→roomyMoves count): 10-10 dead-even, every map 2-2, weakhold-B went 1-1 (NO flatline on this base), qDead flat (stronghold +1 cand = single flip). VERDICT: SAFE here — the transcription-bug-fixed base doesn't reproduce the mainline weakhold-B flatline in this gate. r>=100 variant not built (its flatline trigger never fired).
- C3 (!queen_ reverse-split fallback): 10-10 pairs but queen-death signature — stronghold qd cand3/base1 + s2 BOTH-seat loss, qOS cand3/base2. weakhold 3-1 gain offsets. VERDICT: MIXED/bleeds queen lives — blocking the queen's boxed-in reverse-split kills her in corridors the fallback used to rescue. If kept, pair with the box-feed path coverage check.
- Net: none of C1/C2/C3 individually explains a uniform 10-15pt regression — each bleeds a different map (dilemma, none, stronghold+queens). Combined-stack residual likely = sum of map-specific bleeds + the still-missing mainline factor.

## tune r5 — S2 vectors on v143 — 2026-10-04
- Re-gated the delivered vectors on abyss_v143 vs abyss_cf (same fixture/protocol): sd2 6-4/+5.8, f330 4-6/+6.4, sm2 4-6/+6.8, rel370 4-6/+7.4 — control v143-noop 4-6/+7.7. ALL ≤ control. v143 already embodies the gains (feed360+portal10); the vector set's marginal value on this base is ~0 at fixture resolution. sd2 flagged unresolved-needs-multiseed.

## v149 vs v138 map-class audit — 2026-10-04 (tag audit149, all 22 maps ×2 seeds both seats)
Bells model verified in data: r499 = queenEnd → longest → total. Format: map | cand W-L | lock | mech.

| map | W-L | lock | mechanism |
|---|---|---|---|
| autarky | **0-4** | cand loses both seats/seeds | queen dies hitH r197-391 every game; s2B cand dominated len56/tot79 but queen dead vs base's alive@5 → bells queenEnd kills. Feed is FINE (qEat 30 on B) — the bleed is queen EXPOSURE to h2h, not econ. |
| tower_defense | **1-3** | both-seat loss s2 | early queen deaths → elims: cand qd @40 hitWall (s2B, base ALSO wall@40 s2A but its swarm outlasted), @135/@275 h2h. Elim map: queen fragility decides. |
| big_empty | **1-3** | — | all 8 queens die h2h r49-98 (killbox). Then longest decides: cand tot DOMINATES (723-915 vs 497-683) but longest loses 43-61 vs 44-65 — v149 spreads food across swarm, v138 concentrates post-queen-death. Funnel arrives too late / leaks. |
| stronghold | 2-2 | side-locked | s1B: cand qd@195hitO vs base alive@22 → queen-death loss. s2A: BOTH alive, cq3<bq10 → queen-feed race lost (s2B won cq17>bq4). qEat tracks it: 94v77 won, 15v83 lost. |
| islands | 2-2 | side-locked(s1) | s1 both seats lost: cand queen dies early (@206hitSELF, @142h2h) + longest deficit vs base q-alive-385/308 + base qEat 23 vs cand 2-11. s2 flips. Queen-survival + feed race, not structural. |
| schooltime | 2-2 | side-locked | both queens alive@3 sealed-hide — pure longest contest. |
| trauma | 2-2 | side-locked | queens alive; queenEnd decides seats (cq25>bq21 won). |
| portals | 2-2 | — | queens alive both sides; longest swaps seats. |
| slithery_fight | 3-1 | side-locked | s1A won cq21 vs dead base queen — bells queenEnd. s1B loss cq†422 vs bq3: cand queen died @422 while base's lived at 3 → flip. |
| weakhold | 3-1 | side-locked | cand queens alive 2/4 vs base 0/4 — the pocket doctrine holds; one split B loss. |
| unsw | 2-2 | side-locked | queens dead all; longest decides seats. |
| maze | 2-2 | — | queens dead all; longest seat-flips. |
| australia | 2-2 | — | queens dead all; tot decides seats (441/45 dominant vs 88/268 crushed). |
| default | 3-1 | side-locked | s2B loss: cand queen @15 early h2h vs base alive till 78ish; rest clean. |
| default_small | 3-1 | side-locked | s2B loss on longest 19/28 (queens dead both). |
| devil | 2-2 | side-locked | elim race seat-locked; cq4 won A. |
| dilemma | 2-2 | side-locked | cand A loses @25 hitSelf BOTH seeds — A-seat queen self-kill structural pattern (matches earlier C1 dilemma bleed: this map is a queen-trap geometry). |
| trophy | 2-2 | side-locked | elim race; cand queen dies @42-80 vs base @26-73 — seat decides. |
| stripes | 2-2 | — | elim race seat-flips; cand B wins. |
| queen_of_spades | 2-2 | — | seat-flip per seed (NOT locked): genuinely contested; all queen deaths h2h incl. the r36-class seam events. |
| Colosseum | 2-2 | — | elim race seat-flips. |
| arena | 3-1 | side-locked | s2B one loss @13h2h early; elim race. |

AGGREGATE: cand queens@499 9/53 vs base 8/53 — global parity, but the loss maps all fail the SAME column: cand queen dies while base's lives (autarky, td, stronghold s1B/s2A, islands s1), or cand queen out-fed on bells (stronghold/islands qEat 2-11 vs base 23-83). Loss class = QUEEN SURVIVAL (exposure to h2h/wall pre-endgame) + QUEEN-FEED FUNNEL on bells races. Next mechanism targets in order: (1) autarky-class queen h2h exposure (all 4 losses are her fights, feed fine), (2) td-class early queen wall/fog deaths @40 → elim, (3) islands/stronghold-class queen-feed rate (v149 feeds her less than v138 on shared bells races). Non-issues: total/econ (dominates big_empty/schooltime tot columns), sealed-queen maps (schooltime/trauma/portals all healthy).

## Rules-checker: portal exit / freeze / move-cost — 2026-10-04 (tooling/rulescheck.py, replays from audit149 islands+qOS+portals ×2 seeds)

**Q1 PORTAL EXIT — confirmed heading-preserving, NOT 180°.** Engine: `TileAfterCrossing(state, partnerEdge, heading)` at engine/src/helpers.cc:92-99 — horizontal partner edge → `(x, heading==S ? y : y-1)`, vertical → `(heading==E ? x : x-1, y)`. Exit tile = far side of partner edge, in direction of travel; partner edge comes from the EDGE kind-2 portalId pairing in the map text. 96/96 replay transits (12 files, 0 mismatches) land exactly on that formula — zero rotation. Exit tile IS computable but only once both ends are known (which our pairing code correctly requires). Where OUR code actually breaks: no rotation assumption in notePortal (world.hpp:351-377, vision-only pairing), but the `dir^2` "opposite" idiom guesses neck=behind-head — wrong for portal-crossed bodies (real neck = entry-side cell): **world.hpp:215-219 `board.nb[head*4 + (t.dir^2)]`, same idiom policy.hpp:161,365.** That's the hidden 180°-class bug the review meant.

**Q2 FREEZE BUG — persists, but it's starvation-loops not literal stasis.** All 4 audit149 portals games: ZERO transits by either bot all game, eaten 5v2 in 499r, zero B-side splits, alive but longest 3-5/total 8-11, stats seat-locked. Movement itself is healthy (2-step moves fire, no static-lock). So the C0 dest=-1 scout path exists (policy.hpp:1187-1197) but dragons still never cross: hypothesis — `wPortalLoiter` (policy.hpp:1643) penalizes standing on portalSide cells when not crossing, repelling dragons from portal lips so the scout/vision pairing never completes. Unverified at bot level; the freeze is econ collapse, not a move bug.

**Q3 MOVE COST — vendored model wrong vs deployed 1.2.7.** Replay-derived (4900+ multistep moves, ~6000 updates/file, ≤0.25% tail-sim residual): EVERY step pushes head + sheds 1 tail segment; a step onto a pearl skips the shed (net grow). NO extra payment for step index >0 — vendored engine/src/actions.cc:11 `mustPayForStep` pay-pop is absent in the deployed wasm's observable behavior (islands r157 dragon95 [W,W]: tail popped exactly once per step, no pearl). Observed step counts up to 5 incl. len5→5, len4→3 routinely → cap ≈ L steps (vendored's effective L-1 falsified); the `can't pay` len>2 guard exists in wasm but can't bind under len-conserving slither. **Where our code is wrong**: common.hpp:385 `freeSteps=(L+3)/4` invents a free/paid boundary that doesn't exist — real cost of an n-step move is just n normal slither sheds (len-neutral) minus pearls eaten. Consumers: policy.hpp:178-215 twoStep accounting, :482-505 `reach=min(freeSteps(L)+L-2, slayMaxSteps)` (≈right cap by accident at small L — freeSteps+L-2 ≈ L+3L/4-2... for len5: 2+3=5 matches — but wrong cost model and over-allows for L≥9), :830 enemy kill-reach, sprintTrade sites. Fix implication: reach per dragon ≈ min(L, cap) steps, cost = len-neutral minus pearls; our sprint math overcharges len 4-8 by 1-2 segments and may underuse multi-step.

**SCOUT TIMING (v151 wScout=2 question)**: early transits r<50 exist only on qOS and are SEAT-geometry artifacts — B-side starter crosses at r14-50 when v149 sits B (the dest=-1 scout DOES fire: v149-B first transit r14 both seeds vs v138-B r64/144). But outcomes don't follow them: v149-B early-transited s1 (lost) and s2 (won). On islands (the contested open bell map) ZERO transits before r50 by either bot in all 4 games — all crossings r60+; the s2 wins had more TOTAL transits (34+17 vs 17+19 losses) = late-mid portal use correlates, early doesn't. Read: forced pre-50 blind crossings are not the win mechanism (each blind transit costs fog risk + the scout's econ time); pairing's value is downstream (world-model completeness enabling r60+ transits where wins correlate). If scout needs a gate: pair early but don't force the crossing itself — and note wPortalLoiter may be fighting the scout (Q2 hypothesis) by repelling dragons from the lips they must stand on to pair.

## pace149: BC_PACE ported to v149 — 2026-10-04 (workspace/abyss_x_pace149 = abyss_v149 + myVisit + paceMemory10/wPacePenalty2.0, queen exempt; tag pace149, n=20 vs abyss_v149)

Gate: **12-8 (60.0%)**, pairs W4 S4 L2. schooltime 3-1, trauma 3-1, unsw 3-1, stronghold 2-2, **islands 1-3 (the bleed)**.

Mechanism check — the loop-breaker channel is NOT what wins here: v149's base revisit_frac (r100-400 mem10) already sits at 0.157-0.201 both bots on schooltime+islands — the 0.27 pacing disease measured on the old v120 base is gone on v149 (its portal/champion changes suppressed it independently). pace149 shaves it only marginally (0.163-0.196) with no consistent separation. The +60% instead lands entirely on QUEEN columns: queen alive@end 55% vs 40%, queen len@end 7.2 vs 4.4, queen non-ram deaths HALVED 0.150 vs 0.350, kept-after-theirs-died 57% vs 17%, queen dead any 0.45 vs 0.60. schooltime s1A = textbook bells flip: base queen hitWall@316 while cand queen held @3. So on v149 the +2.0 anti-backtrack bias works as a generic keep-moving pressure that incidentally protects queens — not as a pacing fix. alive@499 dips 15.4 vs 18.2 (swarm trades harder); longest@end flat 31.8 vs 31.2.

islands bleed mechanism: every queen dies h2h there anyway (qEnd 0/0 all 8), so queenEnd can't decide — the post-queen-death LONGEST race does, and cand lost it 3/4 by 1-7 (30/32, 31/38, 32/33; won 36/25). Re-explore bias fragments the champion funnel on fully-contested maps: cand alive 12.5 vs base 15.8, longest convergence slower. Same class as big_empty's audit bleed (tot dominates, longest loses).

Verdict for integrator: mergeable at 60% w/ queen-column upside, but mind the islands-class regression — if it repeats on a second seed, consider exempting the designated champion (selfChamp_) from myVisit decay so the funnel stays put, or gating the penalty to non-feeding workers only. Copy in workspace/abyss_x_pace149 on this branch.

## v159 seam-crossing fix — gated, mechanism CORRECTED — 2026-10-04 (workspace/abyss_v159, tags v159_seam + v159_seam2, n=20 each vs abyss_v149)

Gates: BOTH 10-10, every per-game metric identical to 2 decimals, mirror end-states — the seam terms as specced are DEAD CODE on this fixture. Why, and what the replays actually show (this corrects BOTH the spec premise and my earlier qOS diagnosis):

**1. Vision is toroidal — wrap landings are never blind.** engine/src/protocol.cc:27-34 `IsInVision` wraps coordinates (`offset<=3 || offset>=size-3` in both axes). A dragon at x=0 sees x=W-1..W-3. So a wrap step's dest is ALWAYS inside the 7x7 window → `!w_.visible(dest)` can never be true for it → the wBlind busy-check cannot attach to wraps (verified: staged build had the code; 20+20 games byte-identical outcomes, wrap counts seat-locked identical, e.g. qOS s1 A=16/B=28 for BOTH seat assignments). My earlier "mutually invisible under fog" claim was wrong: two dragons approaching through the seam within ±3 SEE each other the whole way.

**2. The mutual-elims are pursuit/trade geometry, not blindness.** actions.cc:47-53: h2h = stepping onto a cell CURRENTLY occupied by an enemy head (both die); onto a body kills only the mover. Replay-verified kill shapes: id8(24,34)-N vs id4(0,34)-S — same row, adjacent THROUGH the seam (W=25) — one steps onto the other's head cell. Workers DELIBERATELY h2h via the trade code (policy.hpp:1204-1231: squad/slay/tradeOk all `!queen_`-gated) — most mutual worker deaths are designed aggression (qOS s1: 12 h2h deaths split 8A/4B; devil: 26/22 h2h + mass hitSelf/hitWall).

**3. The queen's real seam exposure = enemy TRADES into her.** She can't h2h-initiate (queen-gated), so her h2h deaths are enemy workers trading INTO her seen head — decided by the ENEMY's tradeOk math, not her avoidance. Defense that exists: wQueenRam zone (seen-enemy sprint reach) — but it's fed by the wrong freeSteps+L-2 reach model (Q3): a len-5 enemy can actually sprint ~5 cells, not 2+3 — her safe-zone is under-priced vs reality. THE LEVER for queen h2h rate is the reach-model fix, not an avoidance term.

**4. What v159 actually is now:** v149 + queen-only `wQueenSeam=2.0` on ending a turn on a boundary row/col whose far-side edge is UNSEEN (`!b.side(dest,boundary-dir).seen` — the honest "unexplored territory could lurk there" check; not-currently-visible version was dead since seam neighbors are always in vision). Also confirmed wrap steps keep paying wFog for unseen seam edges (kelp risk) — an earlier draft that folded wraps into `crossing` would have stripped it; restored. Still gate-inert on the elim fixture (queen boundary landings are corridor-forced).

VERDICT: do not merge seam avoidance as specced — the premise (blind far side) is false in-engine. If queen h2h on qOS/devil-class maps matters, the fix is the enemy-reach model (freeSteps→~L) feeding wQueenRam, possibly + a "don't end in a seen enemy's step-1 reach when she'd win the trade" term that already exists as wQueenRam — just needs the corrected reach. abyss_v159 kept on branch as reference for the seamFog idiom.

## v157 LIVE loss census — 2026-10-05 (tooling/ladder_census.py; deploy cutoff 2026-10-04T01:04:54Z from team elo-history reset; 40 v157-era matches, 30 replays analyzed)

Record **17-13 (57%)**. vs DeepSeek-V4.1-Flash@1765 **1-4** (the top-20 band we must beat), vs life-is-NP-hard@1692 3-1, vs Milk Dragon@1489 11-8, vs Hydra@1615 1-1.

**Loss classes (13):**
- **both-dead-race / longest-concentration: 6 (46%, dominant)** — queens mutually die (h2h×4 @r110-251, hitOtherBody×2), bells then decides on LONGEST and we lose it while WINNING total-length: australia-A 22v27 (tot 248v158), australia-A2 34v49 (tot 299v111!), unsw-B 29v32 (tot 321v265), default-A 15v26, default-B 18v20, islands-B TIED 24v24 → lost total 84v223. Same mechanism as v149's big_empty audit bleed — the post-mutual-queen-death funnel doesn't converge one long dragon. This is now THE biggest live loss class.
- **queen-dead-solo: 4** — MAZE CLUSTER ×3 (hitWall@198, hitWall@110, hitSelf@127 — maze-specific queen trap, worth a replay look), autarky-B h2h@433 (the audit bleed persists live).
- **elim: 2** — devil-A h2h@70→elim, qOS-B h2h@191→elim.
- **feed-race: 1** — trauma-B starved (tot 18v115, both queens alive short@2v5).

**Queen-survival theorem confirmed live: our queen alive@end → 15/16 wins (94%)**; sole exception = the trauma starvation. 9/13 losses carry our queen's death; 4/4 DeepSeek losses had queen deaths.

**Portal fix — VERIFIED in live games:** portals-map transits 520+710/game total (ours ≈273+355) vs **0 transits in all 4 v149 audit games** — the dest=-1 pairing fix demonstrably moved transits. Islands 338-409 teleports/game starting r1-2 (wrap+portal mix, both bots cross early there); australia 72-98; qOS 47. The freeze/starvation-loop disease is dead on live; both portals games WON (incl. e=43v1430 bells steal via queenEnd 7v0).

**Small-map pearls (our eaten60 live vs v149 self-play audit avg):** trophy 51/44 vs 38.5 ↑; devil 17(L)/78(W) vs 46.2 mixed; default 8/11 vs 21.1 ↓; dilemma 10 vs 15.8 ↓; maze 28-32 vs 33 ≈; autarky 20-28 vs 32 ≈; weakhold 4-6 vs 6.2 ≈. Early-econ on small maps is flat-to-down vs the audit baseline but small-map ladder record is strong regardless (swept trophy/devil/dilemma/weakhold/td vs Milk Dragon) — the losses there are queen-death driven, not pearl driven.

**vs the v149 census:** same skeleton — queen exposure + longest-concentration — but the center of mass moved OFF small-map pearls (fixed/irrelevant) and ONTO (a) the both-dead longest funnel (6/13) and (b) maze-class queen traps (3/13). Next-lever ranking live: (1) post-mutual-death longest convergence, (2) maze queen-trap mechanism read, (3) DeepSeek-class opponents: their queens live to bells while ours die @110-251 — enemy queen-survival differential is the elo gate.

## v168 LIVE loss census — 2026-10-05 (deploy ~02:00Z per orchestrator; cutoff 02:00:00Z; 23 games, all replays)

Record **9-14 (39%) — a regression vs v157's 17-13 (57%).** Opponents: 1234@1703, okbro, wawow830, DeepSeek@1767, I-wanna-go-to-CHINA@1511.

**Loss classes (14):**
- **queen-dead-solo: 7 (50%)** — trauma h2h@393, autarky h2h@257, stripes h2h@173, unsw hitWall@204, and **hitSelf ×3** (australia-B@326, autarky-B@291, maze-B@195) — queen self-kills are NEW in the live signature (v157 census: zero solo hitSelf queen deaths).
- **elim: 3** — td-A h2h@132, dilemma-A h2h@446, trophy-B h2h@142 (all queen h2h → team elim).
- **both-dead-race: 3** — australia-A h2h@170 (ln 26v36 tot 145v166), trauma-A h2h@349 (15v19, 15v86), australia-B h2h@127 (**ln 24v28 w/ tot 462v31** — the mutual-death longest funnel persists: swarm dominates, longest loses).
- **feed-race: 1** — schooltime-A starved (tot 3v229).

**Queen mortality COLLAPSED: our queen reached end in only 4/23 games (17%) vs ~53% in v157.** Queen h2h deaths ×8 (@127-446) + hitSelf ×3. Queen-alive → 3/3 wins (weakhold, dilemma, portals — all queenEnd bells steals); the other 6 wins came with BOTH queens dead (0v0 → our swarm takes longest/total). DeepSeek went 2-1 with 2 queen h2h kills of us.

**Portal fix still verified live:** portals 280 transits (ours 135, r34-494), maze-wraps 415, australia 172/34, dilemma 37. Transit channel healthy; freeze remains dead.

**Small-map pearls (our eaten60 vs audit baseline):** default 18 (recovered vs v157's 8-11), dilemma 7-10 ↓, trophy 25 ↓, autarky 34/19 ≈, maze 32 ≈, weakhold 9 ↑, schooltime 9 ↓, stripes 3-6 ≈. Losses remain queen-driven not pearl-driven.

**v168 vs v157 read:** the both-dead-longest funnel persists (6→3 only because opponents' queens now often survive OUR death — solo-dead went 4→7). Headline: **something in v168 makes our queen die far more — 8 h2h + 3 hitSelf, only 17% reaching bells.** hitSelf tripling is the sharpest new signal (queen walking into her own body — champ-funnel/anchor interaction?); h2h surge consistent with the reach-model/trade-ok zone changing around her. Recommend: replay-pull the 3 queen-hitSelf kills (m1098343@326, m1098353@291, m1098354@195) for the trap geometry before any more ship decisions.

## sub#118/v168 60-game loss census, pocket taxonomy — 2026-10-05 (replays DO download — classified from real qDeadReason + alive@r50, not score-line guesses)

Last 60: **30-30**; v168-era (post-02:00Z) **9-14**, pre-era 21-16. Our elo fell 1617→1572 across the skid.
Classes: **1** = queen self-kill (hitWall/hitSelf/hitOtherBody), **2** = elim or early-deficit→h2h (alive50 gap ≥4), **3** = bells/other.

**(a) Class dominance by opponent band:**
- vs 1500-1750 (17 losses): **CLASS 2 dominates — 8/17** (6 elims + 2 deficit-h2h), CLASS 3 bells 5, CLASS 1 4.
- vs 1750+ (13 losses): **CLASS 3 bells 6/13**, CLASS 1 selfkill 4, CLASS 2 elim 3. Top band kills us on bells after queen h2h deaths (their queens reach end-state, ours die @110-257), not by out-splitting us early.
- vs <1500: 0 losses in window.

**(b) Early-deficit→elim correlates with SMALL/pocket maps:** Devil (5v21 — biggest gap), Trophy ×2 (4v14, 3v8), Trauma (4v10), Stripes (2v5), Tower Defense ×2 (2v4, 2v2), weakhold (4v4), Dilemma (6v3), qOS (3v4) + 1 deficit-h2h on Australia (14v18). True open-map elims: none — the elim class is pocket/small-map territory where a few-dragon deficit compounds to full elimination. Caveat: ~half the 2-elims had EVEN a50 (weakhold 4v4, td 2v2, qOS 3v4) — those are queen-pickoff→snowball elims, not early-split deficits; real opening-race losses are Devil/Trophy/Trauma/Stripes.

**Diagnostic games 1098973-80 + 1099009-17 (12g vs 1234/okbro/DeepSeek): v168 went 4-8.** Wins: weakhold, dilemma, stripes(elim of them), default. Losses: CLASS3-bells 5 (australia, trauma×2, autarky, schooltime, stripes), CLASS2 3 (td elim, dilemma elim, trauma deficit-h2h). Pattern matches the census: no CLASS1 selfkills in the diagnostic set, bells losses are post-queen-death on open maps, elims on small maps.

**Headline:** queen-mortality story from the v168 replay-census holds — h2h queen deaths drive both the bells losses (1750+ band) and the pickoff→elim games (1500-1750); CLASS1 selfkills cluster on maze/autarky/australia wraps (4 vs each band); true early-swarm-deficit losses are a small-map-only phenomenon.

## Live census + top-team structural study — 2026-10-05 (140 recent matches; 21 top-team replays: okbro/DeepSeek/1234)

**Elo trajectory:** v168 skid bottomed at 1572 (~02:50Z), recovered to 1601 @04:15Z; rank ~136→122. Trajectory is climbing but still ~350pts under the 1955 target.

**Per-opponent records (v168-era, n=140):** wawow830@1590 19-17, zzz3nith@1639 12-13, nooberGamer@1641 8-7, okbro@1785 **2-7**, Hydra@1537 3-2, Quantify@1432 3-2, SuitedConnectors@1596 1-4, STAR@1688 2-3, 1234@1698 1-3 (all-era 3-6), DeepSeek@1761 2-2 (all-era 3-6), CHINA@1529 3-2, MilkDragon@1494 4-5, life-is-NP-hard@1709 2-1.
**Beatable read:** mid band 1520-1650 ≈ coin-flip (50-53%); occasional wins vs 1688-1709 (STAR, NP-hard, 1234); **vs 1750+ we go ~4-9** — the DeepSeek/okbro wall is the top-20 gate. Anomaly: SuitedConnectors@1596 1-4 (worth a replay pull — mid-band bot beating us 4:1).

**STRUCTURAL deltas top bots run that we don't (from okbro/dseek/1234 replays):**
1. **Late-swarm drawdown.** Winners end at dragonCount **2-14** (dseek 4-9, okbro 3-25, 1234 2-13) vs our typical 10-25. Peak-alive hits r150-380 then the swarm CHURNS down (splits300+ still 73-279 — they keep splitting AND dying, they don't throttle spawning). On islands dseek-B won ln 28v19 tot **61v243** — conceded the whole total-length bell on purpose.
2. **Funnel concentration.** Winner longest/total ratio 20-50% (dseek 28/61=46%, 1234 38/73=52%); our v168 losses run 5-18% (australia-B 24/462!). Post-queen-death we keep 15-43 spread foragers; they already have ONE long dragon + a handful of blockers. Our champ-anchor-at-r330 is the right idea but the swarm never collapses into it — the both-dead-race funnel gap IS this.
3. **Queen feed-rate.** In our losses to top teams their queen ate 4-10x ours (maze 60v5, unsw 47v6, australia-B 44v9, autarky 23v1, trophy 26v9). Their queen's survival to bells (oldest dragon + longest) is what wins the queenEnd bell — we don't feed her at that rate on contested maps.
4. **Escort density costs are accepted.** Their hitSelf/hitWall deaths land within ±2 of an ALLY head ~75-90% (1234: 45/50 hitWall; dseek 85/90; ours ~30-40% by contrast) — i.e. they run tight body screens and eat the congestion kills. Deaths drop NO pearls (engine/pearls.cc — beds only, verified) so it's screen-formations, not corpse-feeding.

**Mechanism implication for integrator:** the ranked levers in order — (a) post-death/late funnel collapse (converge swarm into 1 dragon + blockers r300+; longest is THE contested bell), (b) queen feed-rate on contested maps (their qEaten 15-60), (c) keep trade volume (they h2h 130-198/game — our trade code is on the right track, don't dampen it).

## v168 census refresh + 1700+ milestone study — 2026-10-05 (~04:45Z; last-60 all seat-A scrims)

**Last 60: 29-31.** Classes (new taxonomy): **bell-qdead 10, late-elim r150-400 10, bell-longest 6, bell-bothdead 3, bell-qlen 1, early-elim 1.** vs the stated baseline (bell 31%/late-elim 26%/early-elim 26%): ours is **bell 65%, late-elim 32%, early-elim 3%** — opening elims are solved; mass moved to queen-death bells + mid-game elims.
Map clusters: **Tower Defense→late-elim ×4** (queen h2h@97-236 then snowball), **Maze→bell-qdead ×3** (hitWall×2, h2h), **Schooltime→bell-longest ×3** (live-queen funnel losses 28v41, 11v22, 30v30-tie→tot), UNSW→bothdead ×2 (queen hitSelf ×2!). Portals bell-qlen was ln 3v66 econ annihilation.

**5 most recent losses vs 1700+ (Ron Squad@1700 ×4 + 1234@1700): r50 competitive → r150-300 separation.** Winners out-SPLIT and out-ATE us 2-8x mid-game, not in the opening:
- australia-1107368: r50 13v18 → r150 alive **8v63**, splits 33v112, eaten 110v201 by r300.
- maze-1107372: even@150 then eaten **106v240** by r300.
- portals-1107369: **TOTAL FLATLINE — our 1 alive @r50, ZERO splits all game, eaten 30v602.** Portals engine-failure signature is back vs Ron Squad (lost ln 3v66).
- default-1107371: deficit 9v20@150 → eliminated r256.
- australia-1099017 (vs 1234): even@150 (44v43, 41v43 eaten) then out-eaten 212v291 by r300 — sustained mid-game econ, no opening gap.
Headline: **the 1700+ differential is the r150-300 split/econ engine, not openings.** At r50 we're roughly even; they convert to 2-8x more splits + pearls while our engine stalls (portals being the extreme).

**Ladder state:** elo **1601** (recovered from 1572 skid), rank ~122. Last-40: **19-21.** Bleed opponents: Ron Squad@1700 **1-4 NEW**, SuitedConnectors@1598 1-4, zzz3nith@1639 12-13, wawow830@1590 15-15, 1234@1700 1-2, DeepSeek@1761 1-1 (v168 era). No sub-1500 losses.

## Census refresh — newest 60 games 2026-10-05 ~07:30Z (still v168; elite-band feed: chad gdp@2107, KnightCapital@1981, nooberGamer@1803, JKS/Um_nik@1740-50, Nitronics@1733)

**Record 22-38 (37%)** — elo slid to 1579. Opponent band jumped to 1660-2100.

**Top-3 causes (38 losses):**
1. **bell-bothdead 12** — both queens die, we lose longest/total. Islands ×4, Portals ×2, UNSW ×2, australia, maze, td, trauma. hw asymmetry inside these: opponent hitWall+self 162-716 vs our 10-167 — they throw 2-4x more bodies at walls/collisions and STILL win on funnel concentration (ln their 33-64 vs our 11-34).
2. **late-elim 11** — queen h2h @26-341 then snowball elim. Autarky ×5 (!), qOS ×3, weakhold, td, australia. Queen picks fights pre-r260 on small maps vs elite swarm and the fall is terminal.
3. **early-elim <250: 9 (RESURGENT — was 1 last census)** — Stripes ×4, qOS ×2, autarky, devil, td. All queen h2h @49-228 vs elite openers; a50-gap pattern same as before.

Trailing: queen-ram 2 (islands, dilemma — down from ~8-9 dominant share, consistent with self-kill fix holding: **zero solo queen hitSelf this batch vs 3 last census**), corridor-attrition 2 (schooltime), queen-other 2.

**Delta vs last census:** bothdead 3→12 (exploded — vs this band their queen dies too but their funnel survives, ours doesn't), early-elim 1→9, self-kill solo deaths 3→0 (v168's fix confirmed live), queen-ram share shrank hard.

**Conveyor check (3 worst losses + 1 attrition, nva r120-499):** OUR nva = 0,1,4,2 per game — **the mid-feed conveyor is NOT firing on ladder** (vs the 8-11/window local rate). Meanwhile the ELITE opponents run nva=23-204/game: chad gdp weakhold B=149 stall-deaths while winning e=609v2, KnightCapital isles B=204-range. Read: their feed-conveyor queues sacrifice stalled workers by the hundred and the funnel still delivers — our near-zero nva means the conveyor never engaged, and our econ in the same games was e=2-142 vs their 245-1784. If v168 shipped the conveyor, it isn't reaching its firing condition on ladder.

## Census refresh — newest 40 games (2026-10-05 ~07:41Z, still v168 sub#118)

**Record 19-21.** Same elite feed (chad gdp, Knight Capital, nooberGamer, Um_nik, JKS, 1234, Nitronics, Ron Squad, Oswald).

**Loss classes (n=21):** both-dead-race **10** (48% — islands×4, unsw×2, portals, slithery, aus), elim **6** (29% — autarky×2, aus, weakhold, td, qOS), queen-dead-solo **4** (dilemma×2, islands, portals), feed-race **1** (schooltime — both queens alive ql 3v3, lost tot 18v195).

**Queen death reason audit (all 21 losses):** own-fault (hitWall/hitSelf/hitOtherBody) **10** — hw×5, **hitSelf×2 NEW** (m1120482 unsw@193, m1120450 islands@79), hob×3; h2h **10**; none 1. The self-kill fix did NOT hold: hitSelf is back plus a large hitWall/hitOtherBody own-fault cluster — **9 of 14 bell losses have our queen die by her own fault**, not by rams.

**Profile shift vs previous census:** elim share 53%→29% (early-elim gone, late-elims remain on autarky/td/qOS), bothdead still #1 (12→10), feed-race stable at 1. New: queen own-fault deaths now dominate the bell losses.

## Queen feed-rate anatomy — how elite queens actually eat (13 sides qe≥15, 44 replays)

Method: tooling/queenfeed.py — attributes each pearl-eat to the eater id (head==tile same round), queen = min starter id per team (team via split team-field + sonar ally union-find). Stationarity = queen head unchanged ≥5r. Escort = allies within Chebyshev 3 at eat round; lengths from exact split bodies + eaten growth.

**Verdict: elite queens are escorted ROAMERS, not plants — and the feed is a LATE-game behavior.**
- **97% of high-feed eats (510/524) happen while roaming** — planted_eats ≈ 0 for every qe≥15 queen.
- **68% of high-feed eats (354/524) happen at r200+**, heaviest in r400-499: Knight isles-B 29@400+, unsw-A 36@400+, maze-B 41@400+, dilemma-A 36@300+. Feeding is the reward for winning the mid-game territory fight, not an opening plan.
- **"Feeders" are escort screens, not deliverers** (there IS no delivery mechanic — queens eat only tiles their own head lands on): escort median len=4 (cheap small workers), esc_n 0.6-3.5. Knight's 108-eat queen ran esc_n=3.5 len-4s.
- High-feed queens stay mobile to the end: cells/100r = 30-90 at r400+ (e.g. Knight queen 48→65). Ours either die mid-game or seal (schooltime both queens cells=4/100r, qe=1 — sealed queens CANNOT be fed at all; that map decides on total).
- Feed rates: Knight isles-B 108, noober isles-B 57, Nitronics dil-A 56, unsw-A 50, maze-B 49, unsw-B 48 — vs our losses 0-18.

**Prediction for v202 queen-plant (stationary anchor r320+):** a planted queen's eat ceiling ≈ respawns on her own tile (~0/100r) — anchor+hover CANNOT match roaming feed-rate; hoverers can't deliver (no feed action exists). Plant's real value = queenEnd-bell survival conversion (0→small-len vs the dead-queen 0s we keep posting — 9 own-fault deaths this window argues FOR the plant). But it CONCEDES the qlen bell vs surviving roamers (elite fed queens post len 25-108). NET: plant is a loss-reducer vs bothdead/queen-dead bleeds, not a feed engine; if the goal is matching elite qEaten, the mechanism to copy is escorted-roam (escort screen + safe pearl-field pathing r300+), not planting.

## Census — 30 newest RANKED games (2026-10-05 ~13:34Z, v168)

**Record 11-19** (vs mostly 1440-2050 band). Losses classified from replays (map/end/qDead/longest/total per side).

**Per-cause × per-map table:**

| map | losses | causes |
|---|---|---|
| Around UNSW | 4 | bothdead ×4 |
| Islands | 4 | bothdead ×3, elim ×1 |
| Schooltime | 2 | live-queen ×2 (tot/longest bells) |
| Australia | 2 | bothdead ×1, elim ×1 |
| Maze | 1 | bothdead |
| Slithery Fight | 1 | bothdead |
| Trauma | 1 | queen-dead |
| Portals | 1 | live-queen (qlen 6v24) |
| Devil | 1 | elim |
| Trophy | 1 | elim (early — queen h2h@63, elim@100) |
| weakhold | 1 | elim |

**Totals: bothdead 10 (53%), elim 5 (26%), live-queen bell 3 (16%), queen-dead-solo 1.** vs the 07:41Z census: same shape — bothdead dominant at ~50%, elims stable ~26%, queen own-fault deaths 8/19 (hitWall×6, hitSelf×1@67 isles, hitOtherBody×1) vs h2h×8 — self-kill cluster persists.

**Opponent signatures:**
- **chad gdp @2049 (0-6 this window):** econ steamroll on every map type — eaten 1279-3534, longest 43-110; wins BOTH ways (2 elims, 3 bothdead, 1 live-queen). Signature quirk: their queen dies early by noValidAction (@2-3, twice!) or trades cheaply — they don't need a live queen; the funnel swarm IS the queen.
- **Mid-band beaters:** Oswald@1556 ×3 (mixed: our queen dies then bells/elim), Hydra@1575 ×3 (bothdead×2 + trophy early-elim), Wapowpow@1659 ×2 (bothdead×2), single losses to 1234/tozoman/Nexus/nooberGamer — all same signature: our queen dies early-ish (67-239) → their funnel out-lives us at bells.
- **Anomaly:** "That's That, and This is This" @1441 beat us on Devil — queen h2h@106 → elim@418 (low-elo elim loss, worth a replay pull for mechanism).
- **Pattern:** nobody beats us while our queen lives — all 3 live-queen losses are bells where BOTH queens survived (schooltime×2 + portals qlen 6v24); every other loss has our queen die @63-408.
