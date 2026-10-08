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
- explore: qOS r36 mutual-elim = torus wrap-seam invisible head-on (crossing check can't see wrap steps); fix: price seam crossings + boundary occupancy — devin/lanes/explore.md
- explore: v143 C-pack attribution — C1 bleeds dilemma 0-4, C2 clean (no weakhold-B flatline), C3 queen-death bleed stronghold/qOS — devin/lanes/explore.md
- explore: v149 audit — losses cluster on queenEnd bell: autarky queen-h2h exposure, td queen-wall@40, islands/stronghold queen-feed race (qEat 2-11 vs 23-83) — devin/lanes/explore.md
- explore: rules-check — portal exits heading-preserved (96/96 replays), dir^2 neck bug world.hpp:215; portals freeze=starvation-loops; move cost=uniform slither shed, freeSteps wrong — devin/lanes/explore.md
- explore: pace149 gate 12-8 (60%) vs v149 — wins on queen columns (alive 55v40, qNonRam halved) not pacing (v149 already low revisit); bleeds islands 1-3 post-queen longest race — devin/lanes/explore.md
- explore: v159 seam gate 10-10 no-op — vision is TOROIDAL (wraps never blind); mutual-elims = pursuit/trade geometry; queen dies to enemy-initiated trades — lever = reach model (freeSteps) not avoidance — devin/lanes/explore.md
- v157 live loss census: 17-13; losses = both-dead-longest 6, queen-dead-solo 4 (maze cluster 3), elim 2, feed-race 1; portal fix verified live (520-710 transits/game vs 0 in audit); queen-alive@end -> 15/16 wins
- v168 live census: 9-14 (down from 57%); queen survival collapsed to 17% (h2h x8, hitSelf x3 NEW); losses queen-dead 7, elim 3, both-dead-race 3, feed-race 1; transits still healthy
- v168/last60 census in pocket taxonomy: vs1500-1750 CLASS2(8/17), vs1750+ CLASS3 bells(6/13); elims are small-map only (devil/trophy/trauma/stripes/td); diagnostics 4-8
- census+structure study: elo 1572->1601 rank 122; vs1750+ wall 4-9; top bots = tiny funnel swarm (dr 2-14), longest/tot 20-50% (ours 5-18%), queen fed 4-10x, escort-density accepted
- v168 last60: 29-31, classes bell-qdead 10/late-elim 10/longest 6/bothdead 3; TD->elim x4, maze->qdead x3, schooltime->longest x3; 1700+ losses = r150-300 split/econ collapse (portals 0-split flatline); elo 1601
- census3 22-38 vs elite band: bothdead 12 (islands/autarky/unsw), late-elim 11 (autarky x5), early-elim RESURGENT 9 (stripes x4); queen selfkill solo=0 (fix held); our conveyor nva ~0-4/game NOT firing, elites run 23-204
- census4 19-21: bothdead 10/elim 6/qdead 4; queen own-fault x10 (hitSelf BACK x2); elite queen feed=escorted ROAM 97pct, 68pct at r200+, feed=win-spoils not plan; v202 plant cant match feed-rate
- rank30 census 11-19: bothdead 10/elim 5/live-q 3; UNSW x4 bothdead; chad@2049 sweeps via econ+dead-queen swarm; own-fault qd 8/19 (hitSelf persists)
- v168-15g: 6-9, ALL 9 losses queen-dead, 8/9 h2h ram; no live-q losses; chad nva 175-241 vs our 11-52; v237 builds, bench needs activation (blocked)
- v168-20g: 12-8 improving; queen-h2h 7/8 losses; mutual-death swarm fight 6/8; chad nva churn 211-354; schooltime live-q econ loss
explore lane: v299 mechanism audit — -21% congestion deaths real, recycle+cover falsified; funnel bleed persists
explore lane: top-team queen forensics 234g — queens bud len-2 children, hover ~10 cells, 72% die<r200 by h2h; qEnd>=17 banks only 38% of bells wins
explore lane: opening-split forensics — winners split at len4->2 same shape as us but 77 vs our 43/side r<=120; the lever is rate+cadence not child size
explore lane: combat mechanics forensics — winners' 3+-step moves 2.4x ours, hunt-when-winning +58%; h2h len gate + wraps already match
