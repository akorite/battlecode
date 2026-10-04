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
