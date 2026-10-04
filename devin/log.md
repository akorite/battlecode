# Submission + verdict log (autonomous ladder job)

## 2026-10-03 — v106 submitted (server id 16084)
- Fix: output-layer own-segment step guard (main.cpp emit path). Redirects any
  single-step move whose dest is in body/ownExtra to first safe adjacent dir.
- Target: schooltime coiled-queen r1 hitSelf (~20% of v104 losses; 6/6 ladder,
  11/11 in earlier-session local repro via unswbc pipeline).
- Local gate: schooltime 5/5 survive r5; all-17-map deaths phase zero NEW r0-5
  self-deaths vs v104 baseline; wins vs cf+combat IDENTICAL to v104 (44%/44%,
  per-map identical) — the guard never fired: bug is build/timing-conditional,
  dormant under kvmrun builds, live on the ladder. Zero timeouts, zero crashes.
- CAVEAT: local repro absent under this fixture — verdict rests on ladder.
- whfix worker landed abyss_wh1 (trapSeenOnly fog-as-wall queen trap scan,
  weakhold 8/8 pocket suicides → 0/8, own gate clean). Merged into abyss_v107
  (guard + wh1), queued behind v106.

## 2026-10-03 — v107 gate FAIL (do not submit as-is)
- v107 = v106 guard + wh1 trapSeenOnly. 68-game fixture vs cf+combat: 31% vs
  v104's 44%. Regressed: big_empty 4→0, default 2→0, devil 2→0, trauma 4→2.
- Cause: `unproven` veto (seen-cells<=12) fires on open maps — early vision is
  sparse, every dest looks unproven, queen pinned. Bounced to whfix worker for
  frontier-bounded iteration (abyss_wh2).
- Deaths phase still clean: zero new r0-5 self-deaths vs v104 baseline.

## 2026-10-03 ~20:05 UTC — gate forensics + v109 merge

**Runner-pair discovery (IMPORTANT harness correction):** kvmrun runner binaries
embed ONE bot pair; `--name-a/--name-b` are cosmetic labels. gate_v10X.sh's wins
phase ran one runner for BOTH cf and combat → whichever opponent wasn't embedded
was mislabeled. v108's gate actually ran (v108, cf) everywhere: honest read =
45.6% vs cf over 68 games (≥ v104's 44% baseline), deaths clean. The -a/-b
"sides" were extra seeds, not seat swaps. kmatch.py is the honest harness
(builds reversed-seat pairs). Always verify: `strings $RUNNER | grep bota_`.
- v108: deaths identical to baseline; 45.6% vs cf (68g). Queued behind v106.
- v106 ladder: 5 ranked matches 1W-4L (early). Tracker: tooling/v106track.py.
- Workers landed: abyss_wh2 (trapSeenOnly+frontier, weakhold pockets fixed,
  no open-map pin; 54.2% vs v104 on wh/td/trauma) and abyss_pearl v2
  (forage-first opening; +13.9pp vs combat, parity cf, +14% pearls@30;
  kept regressions: stripes/devil/default/qos small-n).
- **abyss_v109 = v108 + wh2 + pearl** merged (disjoint hunks; kParams:
  trapSeenOnly=1, openUntil=48, openQueenKeep=3, openQueenDanger=1.8).
  Compiles; deaths gate clean (baseline pattern only).
  Honest kmatch gates running: gate-v109-cf (22 ladder maps), then combat.

## ~20:45 UTC — v109 = REGRESSION, v110 queued, pearl bounced

- v108-combat honest gate: **42.0%** (37/88, 22 maps) ≥ v104's 38.9% baseline → v108 gate-clean.
- v109 (v108+wh2+pearl) vs v104 honest: **42.0%** (37/88) — NET REGRESSION.
  SMALL maps 60% (dilemma 4/4, schooltime 4/4, td/trophy/arena/ds 3/4) but
  BIG 27%: australia/maze/portals/slithery/stronghold/trauma all 0/4.
  Mechanism: forage-scatter starves the brood on big maps (queenLen@end
  0.365 vs 2.0; wall+self+body deaths 96 vs 73). Pearl lane bounced to
  worker for a map-gated variant (abyss_pearl4 on devin/pearl).
- v110 = v108 + wh2 (trapSeenOnly=1 + frontier discriminator) built.
  Honest gate vs v104 (22 maps, gate-v110-v104) running.
- New worker c85884d3: weakhold starvation dive (alive@499 ~2 vs 21).
- v106 ladder: ~3W-4L ranked at 9 matches (Slithery/TD losses are endgame
  attrition, not guard failures — guard held, no r0-5 schooltime deaths).

## ~21:40 UTC — v110 also regresses; wh2 isolated as the bleeder; starve → v111

- v110 (v108+wh2) vs v104 honest: **40.0%** (34/85) — same big-map collapse
  as v109 (BIG 28.9%; trauma/stronghold/slithery/portals/autarky/default 0/4).
- v108 vs v104 honest: **47.7%** (41/86, parity within CI) → the ~8pp bleed
  is wh2's unproven veto, not pearl (pearl only added noise on top).
  Mechanism: trapSeenOnly makes fog a wall → unproven veto over-fires on
  big foggy boards → queen pinned; plus mid-game queen hitSelf on trauma.
- whfix worker (d50d6e85) bounced: iterate veto to be maze-gated or die.
- starve worker landed `abyss_starve` (devin/starve): swarmTrap=1 — non-queen
  dragons on maze maps get deadEnd scan (seenOnly=false → proven-closed
  only), veto exhausted && !cycle && cells <= trapSafeCells. weakhold
  16.7→33.3% vs cf, 66.7→100% vs v104, controls flat; cost eaten60 -2-3.
  Base was its own v109 reconstruction → transplanted to **abyss_v111**
  (v108 + swarmTrap only, maze_ → kelpFraction inline since v108 lacks
  pearl's maze_ flag). Honest 22-map gate running (gate-v111-v104).

## ~22:10 UTC — v111 dead; v106 ladder 4W-6L; all lanes iterating

- v111 (v108+swarmTrap) vs v104: **36.9%** — regression. Corridor maps
  bled (islands 1/4, slithery 1/4, weakhold 2/4 vs v108's 4/4). Lane-local
  gate missed maps where pockets are survivable. Starve worker bounced
  with conveyor-vs-survivable-pocket discrimination requirement.
- Pattern across v109/v110/v111: every trap/fog veto bleeds big maps.
  v108 ≈ v104 parity (47.7%) remains the only clean delta.
- v106 ladder (10 ranked, no schooltime drawn): 4W-6L, -77 net Elo;
  losses Trophy/Stripes/Slithery/Trauma — pre-existing corridor weakness,
  guard untested (zero schooltime matches since activation).

## ~22:40 UTC — hitWall mechanism found; v112 (wallguard) gating

- Death-reason histogram over 25 ladder replays: hitWall 2174, hitSelf 1734,
  H2H 1513 — ALL at 1-step moves (multi-step deaths ~0). Not blind pathing.
- Mechanism: unseen edges model as open (kind=0). Planner emits c.dir (or
  path[0]) across a seen-kelp edge when trapped/stale; the v106 selfguard
  only fired on ownSeg → wall steps went out unguarded.
- v112 = v108 + wallguard: output layer redirects any provably-fatal first
  step (dest<0 OR ownSeg) to a free exit; covers single-step AND path[0]
  (path truncates to the safe step). Provably safe: replaces a step that is
  certainly fatal with any free exit, else no-op. Gate vs v104 running.
- Queen-siege losses (mid-game H2H/hitWall encirclement) remain the biggest
  open loss class — next lane after guards settle.

## ~23:15 UTC — v112 SUBMITTED (id 16175)

- v112 gate vs v104: **48.9%** (43/88) — parity with v108's 47.7%, no
  regression; wallguard is a strict superset of v106's live selfguard
  (covers seen-kelp first steps + path[0], not just own-body).
  Submitted: replaces v106's protection with strictly more coverage.
- git tag pending at activation.

## ~23:45 UTC — v112 self-challenges (user: call battles ourselves)

- Fired 8 ranked (Nitronics/JKS/1234/Sarvottam) + ~8 unranked (top-3)
  battles via tooling/challenge.py post. ~28 games.
- Mid-results: 6W-8L. Portals W×3 vs ranked teams (v104-zero map → flip!),
  Devil 2/2, weakhold W vs Sarvottam. Autarky 0/3, Trauma L, TD L.
- **m995333 Schooltime: id0 deaths = NONE — guard held on ladder.**
  Loss was pure endgame attrition (queen alive all game).
- Still bleeding: queen H2H/wall mid-game on some wins (survivable),
  early r0-5 swarm hitWall on big maps.

## ~00:20 UTC Oct 4 — v113 SUBMITTED (v112 + wh4)

- whfix worker iterated wh2→wh4: seenOnly scan gated on NC<=trapMaxTiles=700
  (small maps get pocket veto; big maps byte-identical v104 scans).
  Its own honest 22-map gate: 50.0%, no 0/4, no timeouts — PASS.
- v113 = v112 + wh4 trap-scan block + frontier semantics + params.
  Honest gate vs v104: **46.4%** — parity with v112's 48.9% (CI overlap);
  queen non-ram deaths 0.310 vs 0.369, queen-kept 0.318 vs 0.171,
  td 2/4→4/4. wh4 mechanism confirmed in merged form.
- Self-challenge tally for v112: ~11W-12L; Portals W×3 vs ranked (flip),
  Devil 2/2, Australia + Slithery W; Schooltime guard held (0 id0 deaths).

## ~00:35 UTC — v113 ACTIVE (sub 16183); challenge quota note

- v113 building→active. Self-challenge batch 2 partially fired:
  ranked vs Nitronics + JKS (10 games), unranked 1 more; then 429:
  per-hour start cap (~4 games left; refills ~33min) + 120 req/min.
  Queue remaining batch after refill.

## ~00:55 UTC — queen-death census (v112+v113 self-challenges, ~40 games)

- id0 deaths: 13 games, reasons: H2H×6, hitWall×4, hitSelf×2, hitOtherBody×1.
  None at r1-5 earliest was r7 (Default win anyway). r33+ for the rest —
  mid-game combat attrition, exactly the qsiege lane target.
- Guard tracking: schooltime 2/2 games with ZERO queen deaths (was ~80%
  r1 suicide before the guard).
- New lanes: autarky (13f9c332) spawned — 0/4-0/6 everywhere, worst map.
  whfix terminated post-wh4-ship.
- v113 challenges so far 4W-7L; quota refills ~30min for next batch.

## 23:30 UTC — self-challenge census + v114 build
- Elo 1513 (was ~1463). Ranked record overall 54W-71L; self-challenge batch vs 1700+: Nitronics 3W-13L, JKS 6W-11L, 1234 2W-10L, Sarvottam 6W-4L. Sweet spot: win vs ~1580, lose narrowly vs 1700+.
- pearl worker finding: BIG-map bleed on pearl4 was v110's wh2 (not the opening) — opening bit-inert on big maps, still 0/4 there. wh4 already replaced wh2 on v113.
- Built abyss_v114 = v113 + pearl gated opening (open_ engages nc<=700 non-maze OR startUnits>=5 && nc<=1300). Smoke vs v113: 66.7% (arena 75%, dilemma 100%, islands coin-flip). Metrics: +26% pearls r60, +47% splits r60, alive@r50 7.0 vs 1.0, queen deaths 0.58 vs 1.0/game.
- gate-v114-v104 (22 maps, 88g) running.

## 23:50 UTC — v114 gate result + v115 build + starvation root cause
- gate-v114-v104: 42.0% (SMALL 57.5%, BIG 29.2%). open_-IN maps (arena/Colosseum/default_small/dilemma/trophy) ~70%; BIG dip = noise on open_-out maps + marginal brood-clause maps (autarky/QoS/default).
- AUTOSCRIM ROOT CAUSE FOUND: swarm starvation. TD m997381: splits 3v20 extinct r148; stripes 1v54; weakhold 30v164; australia 59v395. Queen never reaches bud length — paths never cross pearl beds (no 'eat' action exists; growth is passive on tile entry).
- abyss_v115 = v114 with openMinUnits=99 (brood clause dead): open_ engages ONLY on <=700 non-maze maps (arena, Colosseum, default_small, dilemma, trophy). Outside-opponent gates vs cf+combat running on those + 4 inert controls.
- Outstanding: mid-game/big-map forage deficit = the real autoscrim killer (Australia/UNSW/Slithery all >1300 tiles, open_ inert). Needs a whole-game forage lane — starve/autarky workers.

## 00:15 UTC — guard census → v116 submitted; v115 gates done
- GUARD CENSUS (v113dbg, self-play, 10 games): selfguard fires 300-1231x/game, ALL rounds 320-489, ZERO queen firings; wallguard 0 firings anywhere. The guard was silently blocking ~1000 feed deaths/game on big maps — the r320+ consolidation mechanism. Steering's inference confirmed directly.
- v116 = v113 + guards scoped to (round<40 || champion). Smoke vs v113: 75% (9/12); longest dragon at end 24.0 vs 20.3 (feed partially restored); alive@r499 14 vs 41 (swarm consolidates); schooltime 4/4 queen alive. SUBMITTED as sub 16204 (processing).
- v115 (=v113 + map-gated pearl open, brood clause dead) outside gates: vs combat 63.9% (SMALL 80%), vs cf 50.0% (SMALL 80%, BIG 12.5% — cf corridor-map bias as usual). Both clear v104 baselines (38.9%/48.6%). Plan: layer as v117 = v116 + open_ once v116 ladders.
- Metrics pipeline tooling/upload_metrics.py built: per-game alive/maxlen/queen-death/hitSelf300 table by side.
- v117 = v116 + open_ (smoke vs v116: 75%, SMALL 83.3%; pearls r60 50.1 vs 43.3, alive@50 9.3 vs 6.8). SUBMITTED sub ~16210 (processing). v116 ACTIVE as of 00:4x; fired 4 ranked (837/919/501/7, 20 games m999545-m999564) + 3 benchmark-bot unranked (11/19/46, m999570/592/597) for its measurement.
- v117 ACTIVE (sub 16206). v116 first batch (as active): 8W-12L vs 1650+ — JKS 3-2 (v113 was 6-11), Nitronics 2-3, 1234 2-3, Quaker 1-4. Wins: Australia, TD x2, Trauma, Portals, Autarky, Schooltime, Maze. Losses: Devil x2, QoS, Default x2, Slithery x2, Stripes, +0-3 benchmark bots (Bot/test4/Sabotage single unranked).
- v118 smoke1 = DISASTER on contested big maps: feedMinUnits=3 let the r100 feed suicide the whole swarm (alive@499 5 vs 29). longest dragon did rise 34.8 vs 27.2. Fix: feedBigMinUnits=20 — feed only surplus.
- v118 early-feed DEADEND after 5 smokes (33/43.8/37.5/43.8/31.2 vs v117): feed timing can't beat r320 all-in feed; unsw 4/4 was the only bright spot (calm maps) but calm-gate regressed it. Logged in deadends.md. Champion growth rides swarm size now.
- v116 ladder-game metrics (20 ranked, 1650+): our champ hits 3-13 len @r300 vs opp 41@300 (m999547 maze vs 1234) — gap is real but feeding earlier locally fails vs our own base. Revisit after swarm size grows via pearl.
- Queen deaths in v116 batch: all hitHeadToHead/hitOtherBody (rams) — qsiege lane owns. hitWall is generic corridor death for all dragons, not queen-specific in this window.
- v117 = LIVE (sub 16206, activated ~01:05). Challenge quota: 2 games left this hour (battle needs 5) — refills ~01:30.
- v119 = v117 + queen ram screen (queen_: tiles inside seen/heard enemy sprint reach priced fatal; heard=2 ghost-hint). Self-play 50% (neutral); vs combat queen-death-maps: score-neutral but non-ram queen deaths 0.083 vs 0.458 (-82%), in-reach opps 2 vs 9. SUBMITTED. wQueenRam=30/wQueenRamHeard=2.
- v117 vs combat full board (87g): 57.5% (BIG 68.1%, SMALL 45%): losses stripes/weakhold 0/4 (starvation), QoS/devil/schooltime/default_small 25%.
- v117 20 ranked games fired vs 1650+ (m1002893-1002922) + 10 vs top-3 earlier.

## v120 deadend + weakhold repro + wh4check (Oct 4 ~01:00 UTC)
- v120 (openMaxTiles=1200 + enemy-arrival gate): 32.5% vs v117 on 5 medium maps — logged
  deadends. The pearl opening stays <=700 non-maze. Per-dragon open_ flicker broke swarm.
- weakhold repro vs combat 0/8: we OUT-EAT to r60 (11.5v1.5 pearls, 5.5v2.5 splits) then
  flatline to 1 alive vs their 27. Post-opening pocket-exit is the missing mechanism.
  Integrator's hotFar pull attempts: 25%/37.5% self-play — deadend. Pocket worker lane
  spawned (5d3c6001) with full diagnosis.
- wh4check (v119 vs v104, devil/stripes/TD 24g): 50% overall, devil 25% (worst map),
  TD 75%. splits@r60 5.1 vs 9.6 — early econ halved since v104; we win by attrition
  not tempo. earlyecon worker spawned (381c0534) to bisect wh4/open_/guard-scope.
- qsiege lane closed (honest negative, dead code). starve session terminated.
- Ladder: v117 final self-challenge band 7-13 vs 1650+ (Nitronics 2-3, Quaker 1-4,
  1234 2-3, IW 2-3). v119 ACTIVE (sub 16258, queen-ram screen).

## Code review r1 applied (Oct 4 ~04:50 UTC)
- F1: v121 was measuring the feed move WRONG — queenFeedRound alone. Real feed
  start = min(feedRound,queenFeedRound); live=320 (queenHide=1). Rebuilt v121 =
  feed bundle: feedRound/qFeedRound/champFallback→400, queenRelayFrom→370,
  queenHideUntil→390 (was 320 — 80r exposed grower otherwise). feedgate2 running.
- F2 HIGH: dead-end veto never set c.score → vetoed queen move can't win →
  trapped fallback → reverse split → len-2 stub (the queen-self-kill mechanism).
- F3 HIGH: viaReverse skips queen trap scan entirely post-320.
- v122 = v120 + {c.score=c.stepTerm, !queen_ in viaReverse} — vetofix gate running.
- Sticky review forwarded to earlyecon (drop kind-x assassin, feedMaxLen cap on
  holds, swarmRank on re-add, flags out of common.hpp). Autarky got F8/F9.
- v120: live sub 16296. Remaining-maps gate 52.1% (96g) → total ~52.4%/160g.
- v119 challenge record: Nitronics 3-2, 1234 1-4, unranked top3 3-4. Elo 1440.
- vetofix (v122 F2+F3, 48g 6-map): 50.0% — neutral; queen-death rate unchanged.
  Correctness kept in branch; F12/F13/F15 added after gate start — re-gate with
  the full pack on queen-death maps before any ship decision.
- v122full (v122 pack F2,F3,F12,F13,F15 on queen-death maps, 30g): 53.3% /
  55.6% unlocked — mild positive, queen-death rate unmoved (0.80 vs 0.77);
  crash deaths ~equal. Safe to merge into winners; combo at S2 only.
- v120 live: Elo 1440->1535 (pre-v120 window); v120 autoscrim record pending.
- battles feed found: api/v1/battles?teamId=351 — per-upload tables now feasible.
- feedgate2 halfway (24/48): 66.7% — schooltime 4/4, islands 3/4, slithery 2/2.
  alive@r499 24.2 vs 11.9 (swarm survives to feed), qlen 1.8 vs 1.2, longest
  26.5 vs 27.5 (midEnd=400 danger-doubling at feed start may cost ~1 len — F16).
- feedgate2 FINAL (48g): 50.0% — MECHANISM real (alive@499 25.0 vs 11.4) but
  champion pays for it: longest@end 26.3 vs 31.7 (-5.4). Win pattern: islands/
  australia/slithery/schooltime 66.7%; maze 16.7%, stronghold/unsw 33.3%.
  Read: 90r of feed can't rebuild the 30+ champion — need either earlier feed
  time or less feeder shyness (midEnd=400 doubles danger at feed start, F16).
  Next: v124 = bundle + midEnd450.
- feedprobe (replays, 12g stronghold/unsw): v121 feed suicides DO fire —
  r400-490 deaths ~2-3x base (stronghold 88/100 vs 27/45; unsw 219 vs 67).
  Conversion bug found: locateChamp starts at min-40=360 while queen still
  hidden to 390 → feeders die beside a len-2 hidden queen who re-buds the
  drops into workers (churn). Then she unhides, dies 77% anyway, fallback
  champion gets 90r. v125 = don't crown a hidden queen (queenReady gate).
  Design note: for queen-as-champion she must unhide ~340 (grow to ~15 by
  400), not 390 — feed can't build 30+ from len-2 in 90r.
- midend450 final (32g, driver killed): v124 56.2% vs v121, longest +1.6 —
  midEnd=450 is a small keeper (feeders less shy), not the main lever.
- Feed-bundle refinement queue: v125 (no-crown-hidden) gating; v126
  (hideUntil 340, queen grows to ~len-15 by 400) next. Main lever =
  feed turns + a champion that exists to feed (queen dies 77% post-unhide).
- hidqueen final (24g): 50.0%, identical metrics — churn theory FALSIFIED (hidden
  queen never crowned anyway). v126/v128 keep the no-crown guard anyway (harmless).
  Queen-as-champ path needs escort (5b) — she dies 77% post-unhide regardless.
- feed360 final (24g): v127 feed@360 = 66.7% vs v121. longest@end 29.1 vs 25.6 (+3.5),
  queen dead IDENTICAL 0.75 (no added exposure — unhide stayed 390), alive@499 20.0 vs 25.7.
  unsw 6/6. FEED-TIME IS THE LEVER: 139 feed turns > 90.
- feedstack (20g so far): v128 feed@400 stack 60%, +1.75 longest — weaker than feed@360.
  hideUntil340 adds queen exposure w/o payoff (per Akorite flag) — DROPPED from stack.
- v129 = feed@360 + midEnd450 + no-crown-hidden, unhide@390 — gating vs v127 (stack360).
- feedstack final (24g): v128 58.3% vs v121 — confirms feed@360 > feed@400 stack.
- stack360 (20g so far): v129 (feed@360+midEnd450+nocrown) 55% vs v127 — longest@end
  36.0 vs 35.5, queen dead 0.60 vs 0.65. v129 = FEED CANDIDATE.
- qdeathprobe: queen deaths SEAT/MAP-LOCKED not unhide-timing-locked (seat A dies
  ~same round regardless of bot/hideUntil). Escort/5b is the real queen fix.
- v129screen: S1 kill-check vs v120 all 17 maps both seats 88g LAUNCHED.
- v129screen final (88g): v129 47.7% vs v120 — S1 KILL on corridors:
  maze/slithery 0/4, trauma/portals/weakhold 1/4. Small maps 55% fine.
  Swarm mechanism works (alive@499 18.6 vs 11.4) but corridors bleed.
- ROOT CAUSE: queenHideUntil 390 in v129 vs v120's 320 — queen stays swarm-worker
  +70r instead of growing. On corridors queen-as-champion works (maze: queen len 26
  won). Feed@360 for worker-champ fine; delayed unhide is the bleed.
- v130 = v129 + queenHideUntil 320 — corridorfix gate vs v120 (6 maps x2 seeds x2 seats).
- corridorfix (24g): v130 (v129+hideUntil320) 16.7% vs v120 — WORSE. Queen timing
  NOT the corridor cause. Feed bundle itself bleeds corridors.
- Decomposing on 6 corridor maps: v131 = v120 + feed@360 ONLY (timing), v132 = +midEnd450.
  If v131 bleeds too → feed-timing is corridor-toxic → feature-gate feed by map class.
- corr360 (24g): v131 (feed@360 timing ONLY) 20.8% vs v120 corridors — maze/trauma/
  weakhold still 0/4. CORRIDOR BLEED = FEED TIMING ITSELF, not midEnd/hideUntil.
- Corridors want EARLY consolidation; open maps want LATE feed. Split: <=2000 tiles
  = corridor class (maze1152/trauma1152/weakhold600/portals512/slithery1701);
  >2000 = open class (islands2240/schooltime2400/unsw+aus+bigempty4096).
- v133 = v129 + eff_-gate: corridor-class reverts all 7 feed params to v120 values.
  v133screen (88g all maps vs v120) launched.
- v133screen final (88g): v133 50.0% vs v120 — ZERO bleed. corridors 50% exact
  (gate restores v120 behavior), schooltime 75%, slithery 1/4 boundary.
  alive@499 +54%, longest +0.9, queen len +0.7. No r0-5 queen deaths.
- v133combat (12g): 83.3% — swarm converts vs real opp (longest 31.9 vs 24.2).
- v120 vs top-4 benchmark: 0W-25L pulled from battles feed — total wipeout.
- v133 SUBMITTED (sub 16457, v110) + S2 challenges fired: FtM/Vibing++/Sponge
  ranked, SSS unranked. SPRT p0~0; check per 10g, cap 80g.
- S2 reality check: v133 vs top4 = 0-17 first wave (same floor as v120's 0-25).
  Replays: THEIR champions hit 51-94, ours cap 40-47; ~1/3 games = pre-r200 elim.
  Top-4 SPRT floored (both ~0%) — discrimination impossible at that tier.
- Our band record (1580-1750): meowest 10-30%, 1234 20%, WaterCandle 35-50%.
  Reframing: we're mid-pack; +400 Elo needs beating 1600-1750 at 60%+.
- Discrimination set fired: meowest(529)+WaterCandle(782) unranked, 1234(919) ranked.
- v133-local: feed@360 on opens + corridor-gate = mechanism up, no regression.
| v134econ | S1 | v134=v133+ee_fix120 dual-scan (econ lane candidate) | 6-map elim set x8s vs v133 | started | — | combo test per method (different mechanisms: feed gate vs trap-scan) |
| v134econ | S1 result | v134 vs v133 | 6-map elim x8s 96g | **56.2% ALL / 54.7% unlocked** | splits60 8.19vs5.66 (+45%), pearls60 +41%, devil 68.8% stripes 75% qOS/aut/default mirrors; qNonRam 0.31vs0.22 (accepted trade) | PASS→submitted v111 |
| v133-band | ladder obs | v133 vs 1600-1750 band (self-challenges) | ~19g so far | ~47% (9W-10L) vs v120 ~25-30% | wins incl 1234(1708) on TD+Australia 3-2 each; losses = pre-r200 swarm collapse | trending |
| v135pocket | S1 | v135=v134+pocket bait-fix | weakhold+dilemma+maze+stripes x8s 64g | **46.9% — FAIL** | maze 31.2%: starving_/baitEat ungated on anyBait_ → pulls+wedge-deaths on no-bait-cell-class maps (maze has 94 deg-1 cells) | iterate v135b |
| v135b | S1 | pocket gate tightened: pocketMap_=anyBait_&&NC<=700 | same 4-map set x8s | running | maze should bit-mirror v134 (all pocket mechs off) | — |
| v134-ladder | S2 obs | v134 live (sub v111) band challenges | 13 games fired (919x10R, 782/529/475 unranked) | — | — | accumulating |
| v135b | S1 result | v135 vs v134 | 4-map x8s 63g | 42.9% (maze 20%) | residual per-node cost still flipped saturated games | hoisted loops → v135c |
| v135c | S1 result | v135(hoisted) vs v134 | 4-map x8s 64g | 46.9% (maze 31.2%, all pair-S elsewhere) | maze skew = wasm depth-clip noise — several games bit-identical to mirror; vs cf 81.2% = v134's 81.2% (maze 87.5>75) | real-opp parity |
| v135combat | S1 conv | v135 vs abyss_combat | weakhold+stripes x4s 16g | 43.8%; **weakhold 0/8 → 50%** | seat-A flatline broken (27 elim, 24-21 len); alive499 3.9 vs 15.7 | mechanism converts |
| v135 | S3 | v134+v135 submitted | — | sub v112 "v135-pocket-bait" | per method: combo passed real-opp checks | LIVE |
| STEERING-3 (07:45) | — | new order | — | — | A: early growth elim maps (r25 6.7d/16.4L, r50 10.3d/25.5L, r100 20d/50L); B: feed-window champion-pearls (self-hit spike = intended feed deaths, not guard gap); C: review fixes before uploads; D: 17-map both-seat vs 5 teams ≥100g | v135 has A1 defect live (dilemma+portals lose both seats via F2 worker-scan trapped) → v137 fix path |
| STOP | — | — | — | — | — | feed-date moves; map-name tables (w*h, W==40); queen-risk trades; <100g verdicts; one-seat drills |
| KEPT | — | — | — | — | — | schooltime fix, scoped guards, wh4 small maps, map-gated pearl opening, feed@360 opens, corridor revert (feature-gated TBD), 1650+ matched challenges, round-keyed sonar, explore lane as-is |
| v137fix | S1 | abyss_v135+v137 pack | 41.4 | 128 | FAIL | F2+F3+F13+A2sealed: dilemma/portals seat-locked (fixed) BUT schooltime 18.8% 5-both-losses; alive@r499 5.3 vs 17.8 — sealed queen left her room via scored veto |
| v137qos | S1 | same | 43.8 | 16 | neutral | qOS unchanged (7/8 splits) — r36 mutual-elim not touched by pack |
| v136ak | S1 | v135+autarky election fix | 50.9 | 112 | hold | autarky 54.2% (3-1 pairs) all else inert; champMargin=3+relayFrom=280+tradeSlack=0 |
| v137b | S1 | v137-sealed-queen keeps trapped | — | 144 | running | F2 score gated !queen_||queenReach>=20 |

## Steering-4 (4 Oct) — queen self-kills, openings, champions, Computers diff
- Self-kills: 73/212 ladder queen deaths own-fault (hitWall 30, hitOtherBody 23, hitSelf 20); 46 pre-r200. Queen alive@499 -> 88% win; dead -> 34%. Targets: self-deaths <5/34 native, N/A <10% own-fault.
- x3 measured prototype: queen keepBase cap 2 (<=700 tiles, r<100) -> Stripes 7->18/20 wins. Ship behind bud_+r<100.
- Openings: portal transits r25 = dominant gap (winners 1.3-3.1 on QoS/Trophy/Default, ours 0.0). Cause: portals bug (unknown partner nb=-1) + blind penalty. Winner scripts per map recorded. Pearl benchmarks r25/r50: Devil 12/54, Trophy 10/44, Stripes 8/24, QoS 6/20, Default 6/18, PD 20/35.
- Champions: channelling not fragmentation — feeders die IN PLACE at champion head (noValidAction ~50/game) vs our hitSelf (~42, scattered). Lock champion ~r330; leaders start r360 at len 24 vs our 14. Gate: longest@r450 >=40 open maps.
- Queen killers: 96% mover-vs-stationary; side/front strikes never behind; in vision >=2 round-starts 65%; killers len2-3 age 13-21; dies median 14 tiles from start. Evasion step + front-arc escort 2-3 tiles + leash ~8 tiles <r100 (per map class).
- Computers +130: front-loaded feed (12.9 recycles r360-379 vs 5.3) + champion +1.6@r300 -> bell games 26->67% (both dead), 30->52% (both alive). Counter: feed ONE champion; their queen dies r71 median (hunt her: 0/39 when dead vs ours alive).
- Queen hunt: enemy queen start = 180-degree rotation of ours on 13/17 maps; x-mirror on Devil/Islands/Schooltime/Trophy. Send len-3 pairs from r25; slayQueen finishes in view.
- STOP list adds: param-only tweaks, feed-date moves.
- Order next 48h: (1a-1c)+(2) one candidate -> S0 native sweep (self-deaths <5/34, Stripes tl@50>12) -> S1 17 maps -> ladder 1234/meowest/WaterCandle+top4. Then portal fix + hunt.
- Test band adds: 1234 (919), meowest (529), WaterCandle (782), YueciLi (475) + Computers (112).

## v138 build + weakhold r37 diagnosis
- v138 = v137 pack + self-kill fixes (ally-walls deadend scan, <2-exit queen veto, worker exit-reservation <=2, doomed-fallback queen-exit last) + x3 queen bud (keepBase<=2, bud_&&r<100).
- v137b gate (9 maps x8 seeds): 47.2%; dilemma/portals both-seat losses CLEARED (0/8/0, 0/7/0+1). schooltime 31.2% = seat-lock (queens sealed both sides, attrition race). weakhold NEW deterministic self-kill: cand seat-A queen hitWall@r37 every seed — walked a fog corridor into a pocket nook; base's same-seat queen took the open east route, died ~r123-353.
- Root cause: F2's score=stepTerm made a vetoed pocket step pickable at -1999 — a scared queen with open-but-dangerous moves got routed into the pocket anyway.
- v138.1 fix: for queen_, vetoed 'deadend' choices demote to -1e18 whenever any non-deadend choice exists (all-vetoed still picks least-bad). Workers keep F2 ordering.
- v138smoke (schooltime/islands/maze x3s): 50%, maze 66.7%, queen non-ram deaths 0.444->0.389; schooltime seat-locked, queens stay sealed len 3.
- S0 native sweep v138s0c running: 17 maps x 2 seeds vs v135. Gate: queen self-deaths <5/34, Stripes tl@50>12 (tl50/tl100 metric added to replay_metrics).

## v138 iteration 2 — heads-only ally-walls
- S0 v138s0c (ally-body-walls, 68g): 51.5%, queen non-ram 0.250 vs 0.382 — BUT weakhold 0/4 (queen rerouted off the east food route into a south loop: over-walling all ally cells within 2) and stripes tl50 7.5 < 12 gate.
- Tightened 1a to spec-literal: teammate HEADS only (was every ally cell).
- v138fix1 recheck (weakhold/stripes/islands/dilemma x3s): weakhold seat-A restored 3/3 wins; stripes seat-B 3/3; seat-locks held; self-kills 7/24 vs base 12 (remaining are mostly the deterministic dilemma seat-A hitSelf@25 which exists identically in base).
- Full S0 re-sweep running (v138s0d).

## v138 S0 verdict (v138s0d, 68g vs v135) + submit
- Board 58.8% (SMALL 57.1, BIG 60.0); trauma/qOS/slithery 100%, autarky 75%.
- Mechanisms: queen non-ram 0.206 vs 0.382 (-46%); alive@end 0.488 vs 0.293; len@end 4.49 vs 1.24; longest@end 34.2 vs 30.0; queen-kept-after-theirs-died 39% vs 13%.
- Self-kills 14/68 (~7/34) vs literal gate <5/34 — user approved promotion anyway: mechanism moved hard; residual classes are fog-walk hitWalls + edge-wrap hitSelf + queen-onto-unseen-ally hitOtherBody.
- Stripes tl@50 8.5 mean (seat-B 13/9, seat-A 6/6) — below >12 bar; seat-lock noise.
- v138 SUBMITTED = sub 16660 "v138-selfkill-x3" (live). S1 challenges fired vs FtM/Vibing++ (6g ea ranked); 91/213/112/919/529/782 queued behind 60g/hr cap, background retry loop.

## v139 build = v138 + two-way + fog (portal experiments dropped)
- wQueenAlly=4.0: queen penalizes landing on/beside seen ally heads (queens move first; unseen-ally hitOtherBody residual).
- wQueenFog=2.0: queen penalizes landing on non-visible dest (seen-safe > unseen bonus).
- Portal attempts FAILED twice: (a) symmetric-guess nb for unpaired portals — queen evaluates wrong dest cell, crosses blind, dies (portals+QoS 0/8, self-kills x5). (b) all-map lip scout pull — parks workers off food, dilemma both seats wiped by r80. Reverted both; portal routing stays with earlyecon lane.
- v139 bisect smoke (4 maps x2s): 50%, identical seat board; queen dead 0.562 vs 0.750, pearls@r60 +30%.
- Full S0 v139s0full running vs v138.

## v139 full S0 verdict + v140 (qsafe port)
- v139 (two-way ally-adjacency + fog preference): 45.6% vs v138 — NET LOSS. BIG 42.5%, unsw 0/4, longest@end -4.6. Queen metrics improved (alive@end +11%) but rerouting costs games. DROPPED both; logged as honest negative (mechanism loses more in reroute/forage than the rare hitOtherBody saves).
- v140 = v138 + pocket qsafe port (qAdj adjacency screen, threat-escort, qVetoReach kill-tier, qEnemyLenMin len-floor, huntMirror B1). Smoke vs v138: 55% (5 maps x2s), queen dead 0.60 vs 0.95, kept-after-theirs 61% vs 14%.
- Full S0 v140s0full vs v138 running.
- v138 LIVE (sub 16660). S1 challenges: 0/10 vs FtM/Vibing++ (top-4 wall as expected); SSS/Sponge/Computers + band 919/529/782 queued behind 60g/hr cap.
- Lane status: earlyecon allocator iterating (sticky holds look net-loss); autarky shipped champMargin+relay+trade block (54x18 gate — to integrate); explore SPSA delivered vectors (feed330, sd2 revert — feed moves on STOP list, sd2 conflicts v120 ship — parked).

## ~11:00 UTC ladder obs (v138 live ~50 min)
- Elo 1637 (+61 since submit). vs top-4: Vibing++ 3W-22L, FtM 3W-27L ≈ 10-12% (v120 was 0-25, v133 1-26) — wall softening.
- Band: WaterCandle 4-6u (worse than v134's record — watch), nsw seng 0-5R (real loss, mid-band), meowest mixed 2-3/3-2R.
- v140 = v138 + qsafe + autarky_ak (folded into S0; gate 54x18). Sweep v140s0full2 running.

## ~11:40 UTC — steering-5/r3 folded
- Mirror-hunt bleed proven: huntMirror=0 → td/qOS/trophy 12/12 splits (was ~33% on). Review C8 explains: aims at rotation of hunter's own start = enemy worker spawn. Correct target = mirror of OUR queen's start; x-mirror on Devil/Islands/Schooltime/Trophy.
- v141a = v139 + C0 (scout portal unblocked at depth loop, move picker, trapped fallback, safeFirst). Smoke: pearls/turn 0.138 vs 0.001 on portals — mechanism fires. Full S0 running.
- v141 = v141a + C1 (unproven veto || path) + C2 (queen hide-bud needs 2 roomy exits, exempt r<50) + C3 (!queen_ on reverse split). Staged, gates after v141a.
- Local engine = official judge wasm (unswbc pkg) — no free-step cost mismatch on our side.
- Review says do NOT ship v140 over v139 (their sweep: 53.3 vs 56.6, Default 1-7, Maze 2-6, PD 3-5) — consistent with local 51.5%.
- Ladder ask: queen evasion vs front-arc rams (66% of v138 games) + portal transits r25 (0.01 vs 1.5) + feed queen r200-225 (FtM recipe 2→13 by r300).

## 2026-10-04 ~12:55 UTC — v142 bisect findings + lanes re-armed
- **v142 root-cause #1 (fixed):** `if (c.terminal) { t[d] = c.score; continue; }` dropped from the first[] depth loop during port → deadend-vetoed moves got phantom continuation scores → deterministic queen hitSelf@r26 weakhold-A. Restored; weakhold-A now wins.
- **v142 root-cause #2 (fixed):** portalOpen_ fired on ZERO-portal maps (weakhold 600 tiles ∈ (512,900], 0 portal ends ≤ 2) → phantom s0scout mission + blindGrace. Gate now requires ≥1 portal end seen.
- **v142 root-cause #3 (scoped):** C1's `|| unproven` inversion vetoes unproven regions even with loopRoom → workers can't enter fog pockets. Scoped to queen-only per v2 rule.
- **Residual:** stack still ~35-45% vs v139's 55% baseline on 5-map smoke. C2 bud-gate (`hiding && r≥50 && parentRoomy<2`) confirmed partial bleed on weakhold-B (flatline c2) but not sole cause — queen rams @225-280 remain.
- **Method fix:** incremental integration (v143=v139+p10 alone) replaces big-bang stack; lanes now gate each piece in parallel on v143.
- **Lane tasking:** pocket→v143+feed; explore→C1/C2/C3 attribution; earlyecon→v143+qsafe port; autarky→corrected mirror-hunt.
- **Ladder:** Elo 1646 (peak 1696). Last 80: band(1500-2000) 9/20=45%, top(2000+) 10/60=17%. Standing: lanes parallel, adversarial review pre-submit, battle log checked often (user).
- **v143 S0 vs v138 (68g): 50.0%** — dead-even (3W/28S/3L pairs). Mechanism metrics lean cand: alive@end +3.2, longest@end +2.8, qKeptAfterTheirs 34.5% vs 28%, qDead 0.647 vs 0.691. Weakhold 3/4, maze/slithery 3/4; td/stronghold/autarky 1/4 pair-losses. v143 = new integration base.
- **Ladder ~13:20:** Elo 1650. WC dropped to 1653 — we just won 2 Islands games off them.
- **Standing (user):** lanes parallel per-piece gating; adversarial review pre-submit; check battles often.
