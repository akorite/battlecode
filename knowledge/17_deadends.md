# 17. Post-v98 tuning dead ends (Oct 1) — all vs abyss_hd2, local A/B

v98 = sc + hide-feed queen (gated >=600t) + portal-lip-gate. Every single-change A/B
since has landed at the ~50% noise floor or regressed. The param/policy surface is
at a local optimum; only doctrine-level changes have moved it (v96 doctrine 65%,
v98 hide+lip 71%).

| variant | change | score | verdict |
|---|---|---|---|
| abyss_hk | wHuntHeard 0->0.5 (stalk heard enemies incl. queen flags) | 12-11 | floor, dead |
| abyss_qe | escortRing 3->2, escortCount 3->4, wHeardEnemy 1->1.6, reach 3->5 | 10-10 | floor |
| abyss_qf | queenFeedRound 350->300, feedMaxLen 6->8 | 10-10 | floor |
| abyss_hx | hideMinTiles 600->500 (hide on 512t maps) | 8-15 | REGRESSION - gate is correct |
| abyss_ls | lateSplitUnits 20->48 (swarm keeps splitting post-r300) | ~5-5 | floor |
| abyss_t7 | hideMinTiles 600->700 (queen grows on Trophy instead of hiding) | 7-9 | slight regression - hide still better on Trophy |
| abyss_sn2 | 2 beacon dirs/turn + 2 enemy-report dirs | 17-13 small maps, 8-10 big | ~51% net, not a ship |
| abyss_nf | wFog 1.0->0.25 (less fog fear) | 15-15 | floor |
| abyss_hc | hiding queen also pulls AWAY from enemies (wHideEnemy*ed) | 3-21 | REGRESSION - corner trap |
| abyss_sd | beacon aimed at most-unseen dir instead of rotation | 14-16 | floor/dead |
| abyss_b2 | swarm splits n=L/2 -> n=2 (bud-2 spam, meta style) | 15-30 | REGRESSION |
| abyss_sw | post-r350 unexplored pull x8 when enemy queen unseen (sweep) | ~9-20 | regression trend |
| abyss_ca | no non-queen head-trades during bud_ (<18 units) | ~10-16 | regression trend |

Verified facts mined from ranked replays (v98, ~28 games):
- elo trajectory 1206 -> 1552 in ~4h of autoscrims; ranked W-L 16-12, but 1-9 vs >=1900.
- vs top-3: 8/11 losses are EARLY ELIMINATIONS r44-275, not tiebreaks. Trophy 0-4
  (wiped r44-108 at 4-5 alive); Autarky queens die r4-5 both sides (spawn adjacency,
  map-intrinsic); openings: their splits ~34/60r vs our ~4-8 (pearl intake, not gates).
- On Schooltime (2400t) hide+feed works mechanically: queen len40 ate36 by r433
  (lost because she died 67r short); a win had 413 splits/2296 pearls/64 alive.
- Their sonar ~3.9/act vs our ~1.0 (top-3 emit every dir per dragon). Emit-side
  changes don't measurably help us locally; read-side is saturated too.
- Queens die ~100% of games for EVERYONE (arch study); tiebreak usually = longest
  dragon -> sustained swarm mass matters even under queen rules.
- The correct queen-hide model: pull toward friends, NOT away from enemies
  (hc's corner-pull trapped her). On <600t she plays grower; on Trophy (625t) hiding
  still beat un-hiding despite open terrain.

## Control + metric re-verification (session cont.)
- **Byte-identical control (abyss vs abyss_ctrl, 60 games): 34/60 = 57%** — confirms the ~40-57% noise band; ship bar stands at >=65%.
- **Throughput-metric rescue FAILED**: sw 124.7sp/433.7pe vs hd2 144.6/523 (LOWER); b2 ~equal; sn2 slightly lower. Flat-line variants are dead on metrics too, not just W/L.
- **Trauma/Sponge loss anatomy**: they win by flooding the maze accepting 267 hitWall+130 noValidAction deaths; feed queen to len-36; we starve at pe99 (wPocket already off; next suspect wFog — mf test).
- **Sponge plays ~0 sonar and still wins** — sonar is not their edge; swarm mass is.
- **KILLBOX lane VERIFIED**: kbTiles=1000 gate on non-maze smalls -> wPocket 0.8 + tradeSlack 0. QoS 15-5 replicated, devil exempted (side-locked ~97%), autarky queens suicide r5 = structural nav dead-end (tail-following ILLEGAL — boxed queen can't ping-pong). Merge candidate for v99.

- **abyss_kb REJECTED on orchestrator box**: kb vs hd2 = 10-30 (QoS 0-10 with r33-r131 eliminations, dilemma 0-10, arena 5-5, Colosseum 5-5). Lane-reported QoS 15-5 does not reproduce here — child-box wasm/baseline drift suspected; hd2 beats sc 6-4 on QoS locally so the map is playable for the tip. tradeSlack=0 on non-maze smalls = spawn-phase wipe.
- hd2 vs sc on QoS 6-4 (map winnable, lane claimed 3-7 — env divergence again).


- abyss_cg DEAD 1-5: champion-grower (longest stops budding r350+) lost every slithery — economy crash; heard-coverage gaps make multiple growers self-elect.
- abyss_mf DEAD 20-15 combined (57% floor): maze wFog 0.4x does not lift trauma/devil.
- kb REJECTED (see above) — total 17+ dead lanes/changes.


## Side-lock + same-side-metric methodology (VERIFIED, important)
- **Schooltime/slithery/autarky/QoS seeds 0-4 are side-locked locally**: side-B won 9/9 mirrors in cv2 batch and ~90% across bu/sp batches. Spawn-econ asymmetry ~10x on schooltime (starved side maxes ~23sp/56pe regardless of bot — IDENTICAL stats across bu/sp/hd2). W/L on symmetric A/B batches is side-draw noise; use SAME-SIDE metric deltas (chal-as-X vs hd2-as-X across the seed's two replays) as the honest comparator.
- Ladder schooltime inverted sides (they feasted as A, we starved as B): ladder seeds differ — the map is a spawn lottery either way.
- abyss_cv INERT: dsp/dpe/dlongest +0 across 26 games — receiver_ flag unreachable (feed block only runs for L<=6; receivers are longer). The '36' slithery win was luck.
- abyss_bu (budAlive40 on >=2000t): schooltime sp +54/pe +81 but longest -26 and W/L 4-5 — churn without wins. DEAD.
- abyss_sp (paid 3rd transit step >=1500t): fires (spr254-1655) but schooltime dpe -1029, longest -77, 3-7 — sprinting spends tiebreak length (mechanism behind 'Cutlery sprint-spam loses mass'). DEAD.
- abyss_ss (starved-side center rush): starved-A pe 40-68 vs hd2's 31-43 — marginal; rushers die in the enemy-held center. DEAD.
- Long-growers already can't initiate h2h (all trade branches require !grower_) — 'longest 3' losses = swarm decimation, not keep-policy. Champion-keep is a dead class.
| ax/ax2 (deadend-lookahead nav) | 10-10 both variants on trauma+autarky | trauma 7-3 edge did not reproduce under queen-only scoping = run variance | REJECT |
| gstats queenLen | simulation (pearl/sprint/split deltas) — drifts; Trauma showed q16v9 but engine B-won | queenLen unreliable on B-side close games |
| se (2nd enemy report/turn) | 15-17 on default/portals/stronghold/trauma | read-side heard coverage already sufficient; emit only reached 1.15/act | REJECT |
| ranked-loss taxonomy (5 losses pulled) | all losses = swarm-mass collapse (alive 17-27 vs 42-64), both-queens-dead endgames decided by mass, opp sonar ~3.85/act constant | queen mechanics NOT the differentiator at our level; mass sustain is |
| qf2 (queenFeedRound 350->240) | 10-10 on big maps (schooltime side-locked) | early queen feed wake neutral | REJECT |
- **oe1 (splitEnemyDist=1)** — OE lane 17/24 vs hd2 on their box, but vs v99-st: 9-15 (autarky 1-7, stronghold 4-4, portals 4-4 side-locked). REJECTED vs v99; also lane-env divergence again.

- p2 paid-step gate (L4 dragons paying 1 seg for non-eating 2nd steps): PERFECTLY INERT — 15-15 vs v99 over 30 games (autarky 5-5, trauma 5-5, slithery 5-5; every seed side-locked). L4 paid 2-steps were already rare or not outcome-relevant. 2026-10-02.

- tail-veto split (veto on enemy-dist to child head instead of parent head): REGRESSION — eliminated r123 vs v99 self-play on devil (2 vs 42 alive). Children born into scrum + halved parents mid-fight. The splitEnemyDist veto isn't the killbox bottleneck. 2026-10-02.

- early-breed veto skip (ignore splitEnemyDist for r<25): NO DELTA — devil s0 trace byte-identical to v99 self-play; veto never engages before r25 (spawns too far). Killbox stall is mid-game contact, not opener. 2026-10-02.

- abyss_qd queen-dead consolidation (stop splits + arm feeding when own-queen beacon stale, gated to r300+): INERT — 8-8 vs v99 (autarky 4-4, schooltime 4-4). Fires correctly but self-play can't price it; parked. 2026-10-02.

## 2026-10-02 (session end state)

- **cf (feedRound 400→260) — LOCAL WIN, LADDER FAIL.** 21-11 vs v99 locally (autarky 6-2, stronghold 7-1, champion 29v21) → submitted as v100 → went 1-9 vs meowest(1676)/err404(1661), elo 1550→1480 → REVERTED (v101 = resubmitted v99). Lesson: local self-play A/B cannot price feed-vs-real-opponent dynamics; only ship on real-ladder evidence.
- **nf (bud_ → skip squad missions, FORAGE lane) — ambiguous.** 13-11 vs st locally; +161% eats as weak-side B on devil but −49% as strong-side A. Asymmetric — helps the side we lose from but costs the side we win. Parked, unmerged.
- **v101_vs_cf stacked test killed at 32/64** (devil 5-3, trophy 4-3, portals 2-2 — was trending inconclusive).
- **Loss taxonomy (ranked, confirmed):** (a) killbox devil/trophy = economy exclusion (peak ~10 vs 40-60, h2h attrition, per-dragon eat parity — population flywheel); (b) big maps = accidental boxing deaths 340/game vs elite 0 (Slithery m850139) + no champion (Default m850142: we 29 dragons/longest14 vs their 2/longest20); (c) elite pattern = sustained ~0.9 feed-suicides/round into one champion.
- **LIVE STATE: v101-revert (=v99-stalk code) active on ladder.** Local tip = abyss_st. Variants kept: abyss_cf (feed260), abyss_nf, abyss_qd, abyss_v101(cf+nf).

## SURVIVAL lane report (landed post-stop) — knowledge/18_survival_lane.md
- Boxing deaths are trapped-fallback suicides: ~75% of fatal dir-blockers are ALLY bodies (4175 vs 47 enemy).
- KEEPERS for next session to verify: abyss_crowd (wCrowd ally-occupied penalty, 19-11=63%) and abyss_combat (same penalty exempt at contact, 20-10=67%) — staged in workspace/. Both vs abyss_st base — rebase onto v99/current tip before A/B.
- Deadend: f1 roomy-flood veto 12-18; f4 tighter gate inconclusive.
- Suffocation feasibility: reachable via exit-count denial on enemy-adjacent dests (fights f2's anti-clustering for same cells).
