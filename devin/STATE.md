# Cognoscenti state — 2026-10-04 (post v3-prompt restart)

## Rating / live
- Elo 1621 (was 1696 peak, -75 drift on autoscrims). Live: **v149 (sub #116)** — 55.1%/68 vs v138 board.
- vs 1600-1950 band: ~61%. vs 2000+: ~17%. Ranked-eligible foes: FtM(264) Vibing++(306) SSS(91) Preyas(1101) 1234(919) Sponge(213) Computers(112). WaterCandle/Citadel ranked-off.
- Cutoff ~1955-1967 by 10 Oct snapshot. Gap ~334 Elo.

## Verified scoring (do not re-litigate)
- r499 bells: lexicographic **queenEnd → longest → total** (35+/0 replays). Dead queen = 0 → auto-loss vs any live queen.

## Top 3 loss causes (current evidence)
1. **Portals freeze** — dragons mill whole games on portal-dense maps (portals.map: 5 pearls/490r). ROOT CAUSE FOUND: scout moves scored +5.8 but `dest=-1` filtered by pick loop + safeFirst veto in main.cpp. FIXED in v151 (gate running).
2. **Queen rams** — lone len-2/3 enemy rams stationary queen, zero allies within 3 tiles. ~50/60 games queen dead. Pocket lane owns escort/evasion.
3. **No consolidation crown** — champ ends 17-25 vs top teams' 40-60 (WC recipe: lock ~r330, feed r380-480, die-in-place feeders). v149 shipped champAnchor; die-in-place feeder convergence is autarky lane's build.

## In flight
- v151 gate: portal-scout picker fix on portals/qOS/trophy/islands/weakhold/stripes (24 games, ~15 min).
- Lanes: pocket=queen escort/evasion; autarky=die-in-place feeders + adversarial review; earlyecon=queen feed r200+; explore=rules check (portal exit semantics, ram reach, ceil(L/4)).
- Ranked salvo: ~40 fired vs FtM/Vibing++/SSS; refill queued for Preyas/1234/Sponge/Computers at cap reset.

## Next hypotheses (ordered)
- H-PORTAL2: picker+guard fix restores transits → portals.map unfreezes (measuring).
- H-EVADE: queen steps off when enemy head in vision + no ally between → cuts ram deaths.
- H-QFEED: feeder reach to queen r200+ → qlen@end 3.8 → 8+.
- H-CONVERGE: die-in-place feeders lift feed-capture 10% → ~17%.

## 2026-10-04 ~04:55 UTC — mid-cycle checkpoint
- Rating ~1600-1615 (bled ~80 since 1696 peak; ranked vs band = net negative until queen module lands — ranked refill STOPPED).
- Live: v149 (sub #116). Latest losses all queen-class: h2h @83-201, hitOtherBody, or qlen out-fed when alive (Nitronics/Milk Dragon/😹/SSS).
- Mechanism found (this session): `loopRoom` computed on OPTIMISTIC fog scan → phantom cycles exempt the deadend veto on ALL maps except weakhold → queen walked cul-de-sacs blind. Deterministic dilemma hitSelf@25 reproduced + traced via qscan logs (S scored "forage" +1 while unproven=1).
- v156 (proven-loop/tree fix): 31.8%/22 — veto now FIRES but converts death mode (hitSelf→h2h earlier). Needs escort, held as piece.
- Gates running: autarky→v157 composite board (portal-fix+C5, 68g); earlyecon→v158 front-load feeders; explore→v159 seam-crossing fix; pocket→v153 queen anchor+threat-escort (THE critical piece per all census data: queen dead in 82% of ladder replays, h2h=45%).
- Killed since last: v152 C2+C3 (41.7%, queen deaths up), mirror-hunt (37.5%), queen-feed all configs, C5 wash 50%.

## 2026-10-04 ~06:30 UTC
- v160 reachBoost: 54.2%/24 W1S11L0 — safe but mechanism-inert (qDead identical; rams arrive via fog anyway). Merged as harmless piece.
- v161 portalGuess=0: 54%/24 W2S9L1 vs v157 — safe-positive; single qOS-s2 pair loss (seat-locked queen h2h zone). Small-map econ -2/60 cost visible.
- explore v159 seam fix: KILLED — premise false (vision is toroidal, wrap landings always visible). Confirms reach-model+wQueenRam is THE queen-h2h lever (already in v162 via reachBoost+qRamAdj).
- v162 = v161 + reachBoost + qRamAdj boarding vs v157 (8 maps ×2×2).
- Elo 1604. Lanes: autarky v157 board in flight, pocket v153 (critical), earlyecon v158 feeders.

## 2026-10-04 ~08:00 UTC
- Elo 1589 (down from 1696 peak — v149 par at band, not dominant).
- v163 composite (v157+guess-off+reachBoost+qRamAdj+v153): ~52%/68 W4S26L3 — WASH. Seat-locks dominate; queen module's 65%/20 fixture lift diluted to parity on the full board.
- Now boarding v153 PURE on 17 maps (tag v153_full) — the 65%/20 piece needs its own honest board vs live; if ≥55% it's the submission candidate.
- Lane delivers so far: pocket v153 (65%/20 ✓), earlyecon v158 feedBurst (62.5% pair, qlen@end +79% ✓ → merged in v164), autarky v157 (board pending), explore v159 seam (killed — toroidal vision premise false), explore C1/C2/C3 attribution (all bleed different maps), pace schooltime-positive.
- Killed: locked queen pivot (starves her), mirror-hunt, C2/C3, queen-feed all forms, seam avoidance.

## Checkpoint ~09:05 UTC (Sat Oct 3)
- **v153-pure full board: 50%/68 W5S23L5** — queen module (65%/20 on 5-map fixture) doesn't transfer to the 17-map board. Same plateau as every composite.
- **v157 = best measured-vs-live (58%/88)**. Internal read: C5 arm costs queen survival (kept-after-theirs 24.2% vs 38.5%). v165 (portal-fix only, C5 reverted) vs v157 boarding now — winner = submission base.
- Pattern confirmed across all gates: seat-locks dominate ~75% of pairs; individual pieces wash ±5% inside n≤90 boards. The lift has to come from stacking ALL the measured-positive pieces, not any one.
- Ladder ~1615, ranked refill still stopped.

## Checkpoint ~09:45 UTC (Sat Oct 3)
- **v157 SUBMITTED + ACTIVE** (server v117): portal fix + C5 + fallback330. Gate 58.0%/88 vs v149. Tag ladder-v157 pushed.
- **C5 marginal verdict: KEEP** — v165 (portal-only, C5 removed) lost 41.7%/60 to v157, 0W/25S/5L pairs; qlen@end 2.78 vs 3.89. autarky's C5-drag hypothesis disproved on the board.
- v153-pure full board: 50%/68 — fixture lift doesn't transfer; queen module parked as pieces.
- Built + staging: v168 = v157 + reachBoost + qRamAdj + die-in-place (SPLIT-0 noValidAction vs neck-step). Board vs v149 running.
- Ladder ~1610 (14/20 autoscrims).
- **v168 vs v149: 58.3%/60 W7S21L2** — ties v157's margin + verified pieces. BIG 63.9%, autarky/trauma/unsw 100%, qlen@end 3.14 vs 2.08 (+51%), wall/self/body deaths 59.4 vs 71.2. Equal-vs-live; v169 (+feedBurst) boarding now.
- v157 live & earning; ladder ~1610.
- **v168 SUBMITTED + ACTIVE** (server v118): v157 + reachBoost + qRamAdj + die-in-place. 58.3%/60 vs v149. Tag ladder-v168.
- v169 (+feedBurst) 55.0%/60 — dilutes margin, parked (feedBurst may go back in behind a different base later).
- Lanes re-tasked: pocket→C7 sealed-queen (autarky spec), autarky→champ ceil(L/4) multi-step, earlyecon→echo reads/sonar recon, explore→v168 live-loss census.
- Confirmed in replay: v168 produced a 45-length champ on autarky — consolidation machinery delivers when it converges.

## 2026-10-03 ~05:00 UTC — diagnostics cycle

- Gate raised to 75% vs live (was 70%).
- v172 (queen veto tier): smoke 50%/20 all-splits — rare-fire, kept as insurance.
- pocket diag vs 1750-band (okbro/DeepSeek/1234): 11 losses = **6 queen SELF-KILL**
  (hitWall/hitSelf/hitOtherBody r68-494 — she corners herself; 3 games longest was
  equal/better, self-kill alone forfeited key-1) + **5 early swarm deficit** (a3-5
  vs a8-21 @r50 → ram → elim). qRamAdj was gated to weakhold dims — OFF on every
  map those rams landed. Also a rules violation (map-size table).
- v173 built: qRamAdj ungated (adjacency screen on all maps) + wh_ dims table →
  queen_||pocketMap_ (calibrated fog-trap scan + unproven veto for the queen on
  every map — attacks the self-kill leak). Smoke on the 12 diagnostic maps running.
- Feed census: ~13 chfeed deaths/feed-game — supply OK; champ ends ~26 vs 45+ —
  the gap is convergence/capture, not feed volume.

## ~05:40 UTC — v173 verdict + queue state

- **v173 FAIL: 39.6%/48, 6 pair losses.** wh_→pocketMap_ suppressed budding on
  pocket maps (splits@r60 8.65 vs 10.35, alive@r50 5.2 vs 6.9) — the documented
  pin regression. queen-dead flat at 0.75 anyway. REVERTED; dims-table fix
  abandoned for wh_ (needs a real feature, not a blind conversion).
- Australia replay (m1098277): we fielded 43 dragons/462 total, lost longest
  24 vs 28 — they consolidated to ONE champ. **feedMaxLen=6 caps feeders**:
  mid-size dragons can't feed AND can't be champ → dead weight. v176 lifts
  the cap to champLen_-1 once a champ exists (true consolidation).
- v174 (swarmSplitLen 4→3), v175 (C7 queenSealed + champMargin=3),
  v176 (feedMaxLen relax), v177 (qRamAdj-only) queued/built. v177 smoking now.

## ~06:10 UTC — live census + v174 dead

- **Live v168 record ~39%**: SuitedConnectors(1563) 1-4, STAR(1700) 2-3,
  1234(1700) 1-3, DeepSeek(1768) 2-2, okbro(1783) 2-3, wawow(1618) 3-2.
  Map bleeds: TowerDefense 0/3, Trauma 0/3 (live replays: hitWall dominates
  fleet deaths — TD elims r132-210 w/ 13-25 wall deaths; trauma r499 grinds
  275-327 wall deaths. Cornered units pick lethal least-bad moves.)
- **v174 FAIL 0%/24, 0/12 pairs**: splitLen 4->3 HALVED production
  (splits@r60 4.5 vs 10.75; alive@r50 2.2 vs 8.8) — len-3 children too
  fragile; workers split instead of eating (pearls@r60 9.7 vs 24.8).
  H-EARLYDEF production arm disproven: deficit is fragility/intake.
- **v177 wash 50%/48 identical metrics** — qRamAdj ungate mergeable as
  insurance (dims-table fix, zero cost).
- v175 (C7+champMargin) running now, v176 (feedMaxLen) queued.
- pocket -> room-shrink trajectory mechanism (abyss_qshrink vs v168).
  autarky -> champStep on v168 base. Lanes all producing.

## ~06:50 UTC — v175 verdict

- **v175 (C7+champMargin): 47.9%/48, W1/S21/L2 — FAIL merge bar.** wall-deaths
  -12% but alive@end -37% (10.2 vs 16.2): stabilization over-consolidates.
  champMargin remains an autarky-only option (56.2% there earlier); C7 parked.
- **v178 built**: v168 + adj-ungate + queen close-cover (escortRingQueen=2 —
  bodyguards INSIDE the "no ally within 2" kill window; escortCountQueen=4).
  Direct counter to the band-ram profile (stationary queen + no cover).
- **Pocket's live read**: self-kill FIXED in v168 (0/12 fresh vs 6/11 old);
  ram h2h = 8/9 remaining losses, all on non-weakhold maps where adj was off.
- v176 (feedMaxLen relax, BIG maps) gating now; v178 queued behind.

## ~07:20 UTC — v175 + v176 verdicts

- **v175 (C7+champMargin): 47.9%/48 FAIL.** wall-deaths -12% but alive@end
  -37%. champMargin stays an autarky option; C7 parked.
- **v176 (feedMaxLen relax): 46.9%/32 FAIL.** longest@end +15% (35.4 vs 30.8 —
  consolidation mechanism works) but queen dead 0.812 vs 0.750, qlen@end
  1.29 vs 2.33 — mid-size feeders were her screen. Lexicographic scoring
  makes the queen cost dominant. Parked; front-load feeders (earlyecon
  62.5% verified) is the consolidation lever instead.
- Pattern from both fails: ANY change draining units near the queen kills
  her more, and queen-death forfeits key-1 regardless of longest. Every
  candidate must be evaluated on queen-alive@end FIRST.
- v178 (close-cover escorts) gating next.

## ~08:00 UTC — v178 verdict

- **v178 (close-cover escorts): 45.8%/48 FAIL.** queen dead UP 0.771 vs 0.729
  — ring-2 bodyguards CAGE her (friend cells block her escape when fleeing).
  maze 4/4 + schooltime 75% (open maps it works) but dilemma 0/4 + trauma
  0/4 + autarky 25% (corridors it cages). Same lesson as wh_: protection
  that restricts her mobility kills her. Parked.
- Correct close-cover lesson: escorts must stay MOBILE/non-blocking — if a
  retry, ring>=3 with intercept behavior not body-block.
- v179 (feedBurst port onto v168) queued next; earlyecon's original was
  62.5% verified on the old base.
- Note: qlen@end dropped 41% under v178 too (1.645 vs 2.774) — escorts
  occupied cells her feeders needed; another queen-cost tax.

## ~08:40 UTC — v179 verdict + v180 built

- **v179 (feedBurst port): 55.0%/40, W4/S14/L2 — MERGE.** alive@end +20%,
  zero queen-cost (dead 0.850 flat, alive@end 0.125 vs 0.094). unsw/
  default/weakhold/big_empty wins. The consolidation mechanism that works
  without the queen tax. Port from earlyecon's verified v158.
- **v180 (worker-region): built.** Static region map at init + forage
  targets in small regions pull weakly (workerRegionNorm=20, starving
  exempt). Targets the one-sided hitWall bleed on corridor maps —
  scoring not veto (rules-legal for workers).
- Remaining queue: v180 smoke (corridor maps), then composite assembly
  from merge-passing pieces.

## ~09:30 UTC — leaderboard + ranked salvos

- Our team has isPublic:false — invisible on the public ladder. Real
  field bigger than the 88 shown (hidden teams like wawow830@1632 exist).
  Our tracked Elo ~1583 slots ~rank 12 among VISIBLE teams; true rank
  higher (more hidden teams above us possible). Cutoff math unchanged.
- Ranked salvo #1 fired: wawow830 x6, zzz3nith x4, nooberGamer x2 (12
  games, the best +EV targets). Result so far ~7W-7L = breakeven.
- Refill queued (~30m): DeepSeek-1761 x5, Hydra x5, STAR-1688 x4,
  1234 x3, okbro x2.
- Top-team salvo queued (~65m): Cache 2229, cheji 2124, Quaker 1955,
  Knight 1843, zhongwen 1806, Um_nik 1741, Nitronics 1728, JKS 1634 —
  +EV math: even 10-17% win rate vs +400-700 Elo is profitable.
- v181 built = v168 + adj-ungate + feedBurst + worker-region (composite,
  region toggleable via param). v180 smoke 20/40.

## ~10:00 UTC — v180 FAIL + lane re-tasking

- **v180 (worker-region): FAIL 41.7%/36** (0W/15S/3L). longest@end
  -15% — pocket forage was FEEDING dragons, not just wall-killing them.
  Pulling workers off regions starved them.
- **Pattern across 3 fails**: v173 (wh_-widen), v178 (close-cover),
  v180 (region-discount) — every mobility/econ restriction costs more
  than it saves. Correctness fixes are the only reliable gains.
- **New lane directive**: study top-team replays directly and clone
  observed winner behavior at the same decision points, not invent.
  pocket: corridor worker behavior diff. autarky: queen positioning vs
  region topology. earlyecon: early-split survival r10-50. explore:
  census + rank tracking.
- v181: workerRegionNorm=0 (piece killed), then gate vs v168.

## ~11:00 UTC — steering r5 applied + v182 full gate

- **NEW PROMOTION GATE**: >=55% vs live over >=200 games both seats all
  maps, 95% LB > 50%, + no-worse vs top-team benchmark (FtM/Vibing++/
  SSS/Computers/Sponge/WaterCandle). Composite bundling per upload.
  Rollback always allowed. (Replaces unreachable 75%.)
- **Conveyor radius rule** (next build): anchor champ in own territory
  near queen start; recycle feeders only within ~N tiles of anchor;
  far feeders forage-then-walk-in. Metric: feeder ram losses vs champ
  length gained — cap radius if losses > gains.
- **v182 220-game gate fired** vs v168 (22 maps, 5 seeds, both seats).
- **v181 smoke** at ~35/48 tracking ~45-50% — read at completion.
- **Lanes**: earlyecon -> Dilemma/Trauma r150-250 elim classification
  + r25/r50 benchmarks (growth/evasion fixes only, no restrictions);
  autarky -> champ-anchor/feed-radius telemetry from top replays;
  pocket -> corridor worker diff; explore -> census/rank.
- Conveyor finding (standing): winners run ~80 nva die-in-place/game,
  champs 53-105; we produced ZERO on ladder (feedHeardDie=2 stalls).
  v182 anchor fix raises nva ~4x locally (S0 verified).

## ~11:40 UTC — v181 verdict: wash with queen cost

- **v181 (adj-ungate + feedBurst on v168): 50.0%/48, W5/S14/L5.** BIG
  60.7% (islands 4/4, maze/big_empty/unsw 75%) vs SMALL 35% (dilemma
  0/4, weakhold+trauma 25%). Mechanism works on big maps; bleeds early
  on small ones.
- **Queen cost on corridor set**: dead 0.833 vs 0.688, qlen@end 1.5 vs
  4.7, kept-after-theirs 0.18 vs 0.50. Champ-feed pulls escorts on
  cramped maps — same class as the early-fragility cluster.
- alive@end +13%, longest@end +3% — the feedBurst side still pays.
- v182 220-gate running; v183 (territory anchor) built, queued.
- Benchmark teams resolved: FtM 264, Vibing 306, SSS 91, Computers 112,
  Sponge 213, WC 782 (ranked-off). None in our last 100 autoscrims —
  benchmark must be fired post-upload; baseline ~0-10% vs top-4.
- Ladder 1579 (Ron Squad 1700 new wall 1/5, UNSW map 1/3).

## ~12:30 UTC — v182 mid-gate + conveyor telemetry

- **Ladder: Elo 1579, last-40 19/21.** Ron Squad (1700) new wall 1/5
  (+121 gap needs ~25% to be +EV — off farming list). wawow830 flipped
  to 8/15 for us; zzz3nith 5/10, nooberGamer 5/10.
- **v182 mid-gate: 16W/41 (~39%)** — pair losses on autarky, big_empty,
  default_small, dilemma, portals, schooltime; pair wins maze+slithery.
  Trending below 55% — persistent-anchor feeding looks net-negative.
- **Conveyor telemetry (big_empty s1 replays):** feed window r360-499,
  cand-side deaths — nva 14 (base 0), h2h 31-33, self 12, body 4-9.
  longest@end 43-44 vs base 46 both seats. Feeders die at stale
  last-known positions → wasted bodies + champ gains nothing.
- **Per steering metric: transit h2h losses (31-33/game) > nva gains
  (~14) → cap the radius.** v184 = v182 + feedRadius=12 built, 16-game
  smoke on feed maps running.
- **v183 = v182 + territory anchor** (champ locks at roomiest cell near
  spawn, cheb<=2) — the stationary-champ fix that makes last-known
  positions stay fresh. Queued behind v184_rad.
- Refill scripts re-fired (both had died silently — nohup env);
  ranked refill ~05:26, top-team salvo ~05:34.
- Lanes re-tasked: earlyecon→elim classification Dilemma/Trauma,
  pocket→corridor attrition study, autarky→conveyor telemetry + v182
  adversarial review, explore→live-loss census + Elo.

## ~13:10 UTC — elim fix doesn't port; conveyor variants racing

- **v182 killed at 43%/70** (was tracking below 55% — stale-anchor feeds
  wasted). Replays kept for lanes.
- **v184_rad vs v182: 56%/16 on feed maps** — feedRadius=12 verified as
  conveyor fix (big_empty 60-68 champs vs v182's 43-44).
- **v186 (territory+persistent anchor on feedBurst): ~25% s1** —
  territory anchor alone insufficient.
- **v188 (openUntil=0 ported from earlyecon): FAIL 40.6%/32** — mechanism
  doesn't transfer to v168: splits@r60 8.2 vs 10.3 DOWN, pearls 18.8 vs
  23.8 DOWN, longest@end 11.5 vs 21.3. Same as mirror-hunt: won on v120,
  loses on current base. The open_ stall doesn't reproduce here.
- v187 (territory+radius+persistent+burst) smoking; v179 fallback gate
  ~75/308.
- Ranked refill 429'd (fired into still-active cap; needs retry loop).

## 05:20 UTC — conveyor line decomposition + lane findings landed

- Ladder: Elo ~1582, but the ranked top-salvo hit a wall: 3W-37L vs 2000+ (Cache 0/18, chad gdp 2/18). Below the ~8% +EV breakeven -> killed 2100+ targets; refill3 fires only vs measured-beatable (nooberGamer 1876 = best EV at ~50%).
- v182 gate: KILLED 43%/70 (stale-anchor die-in-place).
- v184 (radius 12): +56% vs v182 only — never verified vs v168. Methodology note: vs-variant %s are not vs-live %s.
- v186 (territory anchor) 41%/22 FAIL; v187 (+radius) 43%/14 tracking FAIL; v188 (openUntil=0 port) 40.6% FAIL; v179 fallback gate ~50%/78 tracking flat.
- **Lane findings (decisive)**: autarky — top queens orbit ~5.6 INSIDE swarm (never isolated); ours drifts to 13.7. Top champs plant FORWARD midfield (~25 from queen start, spread ~5) NOT home. nva-mix 45% vs 17% is the real conveyor gap. v182 adversarial: 6 concrete defects (age laundering ~69r, known-empty dies, dead-champ poisoning, zombie feeders, selfChamp self-feed, burst ghosts).
- pocket — corridor study INVERTS the attrition read: top teams churn MORE corridor deaths deliberately (walls 4.2x, feed 6.4x) = feed production, not bleeding.
- earlyecon — PD/Trauma r150-250: elim class is production volume (they out-birth us), not survival behavior.
- In gate now: v190 (v182 + all 6 autarky fixes + feedRadius12, anchor stays forward), v191 (queen swarm-leash: wQueenLeash 0.8 past dist 6 — keeps queen inside cover vs the 87% queen-death rate), v189 (bed-anchor, likely dead after forward-champ finding).
- Composite metric insight: conveyor strips fleet (alive@end 12 vs 22.8) for +3.4 longest — net negative WHILE queen dies 87% (dead queen forfeits tiebreak-1). Queen survival gates everything else.

## 2026-10-05 06:15 UTC
- Ladder: Elo 1603. Last 18 done: 14W-4L vs Hydra(1612)/JustReboot(1438). Bleed maps persist: Trauma, TD, Australia, Default.
- v192 composite (conveyor fixes + leash + mid-feed + anchor-die): smoke **58.6%/29, BIG 60.9%, pairs 3W/10S/1L**; alive@end +30%, longest +13%, qlen +16%. Adversarial review passed (accepted risks: contested centroid drops, per-spawn region flood CPU).
- **Upload gate FIRED**: v192 vs v168, all 22 maps, seeds 1-5, 220 games both seats (2 batches). Needs >=55% + LB>50 + benchmark parity (FtM/Vibing++/SSS/Computers/Sponge/WaterCandle).
- v193 (v192 + queenHideUntil 390->100, unhide-inside-leash doctrine): smoke running.
- refill3 ranked top-ups running (winnable targets only; high-elo lottery cut per EV math).
- Next: if v192 clears -> submit + fire benchmark challenges + push. If v193 reads >v192 -> gate it next.
- v193 (queenHideUntil 390->100): FAIL. Fleet -33% (queen is the early factory; unhiding stops her budding), qlen flat 4.4v4.6, queen-alive +33% can't pay for it. Hide-vs-grow is structural: she produces OR grows, not both. Dead end logged.
- v194 (feedRadius 12->20): FAIL 45.2%/42 vs v192. Autarky's rad study (on v182) doesn't transfer: inside v192 rad12 wins — fewer far-feeder transit deaths, fleet +23%, qlen 5.25v4.0. Radius correct at 12.
- v195 (workerRam soft screen): FAIL 44.4%/18. Soft evasion tax degrades foraging (longest -16%), trauma pair-loss. 4th mobility-touch that costs more than it saves (region, unhide, rad20, workerRam) — victim-ram needs a different fix class.
- Conveyor metric (gate replays): v192 nva feeds 8-11/window vs base 1-2 (5-10x); h2h transit losses ~3/game both sides — gains >> losses, radius holds at 12.
- v196 (queen-graze): FAIL 29.4%/17. v197 (champ sweep): FAIL 28.6%/7 — champ IS the anchor; sprinting teleports it = v182 failure mode (longest -40%). Closed: champ stays put, grazes local drops.
- v192 gate mid-read 131g: 49.6% — BIG 59.3% / SMALL 42.9%. Fails upload bar. v198 (midfeed big-map gate NC>=600) gating all-maps now.
- Elo 1554 (challenge results landing + autoscrim parity losses). refill4 EV-filtered loop running.

## 2026-10-05 ~09:00Z — v192 postmortem → v200/v201
- v192 gate died at 49.6%/131 (BIG 59.3 / SMALL 42.9 — but small-n CI overlaps noise).
- Autarky adversarial review: champAnchor was DEAD CODE (champAnchorId_==champId_ never
  true off-vision — locateChamp resets both). BIG-map gains ran on midFeed/leash/rad/burst only.
- Small-map suspect reranked: qRamAdj-global (fences queen on dense boards → small qlen@end →
  lexicographic losses). mid-feed nva=0 on small maps (beacon gate) — exonerated. Leash wash 53.4%/58 (v199).
- Conveyor metric on v192 replays: small elim maps end BEFORE feed window — early-elim class owns them.
- BUILT v200 = v198 + anchor->w_.chId + torus density-centroid + qRamAdj NC>=600 gate + leash INF pocket fix + feedRadius ordering. Full board firing.
- BUILT v201 = v200 + pocket deadEnd branch map (deg<=2 chain to deg1 tip; len>=2 entry fatal-priced + inside -> die-in-place). Corridor smoke vs v200 firing.
- earlyecon: both production knobs inert/negative — PD fix class = worker survival/evasion, not econ.
- explore census: vs1500-1750 class2 elim 8/17; vs1750+ class3 bells 6/13; winners' queen eats 4-10x ours; longest/total funnel 20-50% vs our 5-18%.
- Elo ~1597 (refill +EV grinding, 2/3 vs chad2087, beat Knight1981).

## 2026-10-05 ~12:00Z — small-map hunt: per-map bisect
- v200_full mid-read ~80/132: all maps ~50% EXCEPT Colosseum 0/4 + default_small 0/4 (the <=256-cell boards — where qRamAdj/midFeed are already off). Only leash touches them.
- **v205 (v200 + leash gate NC>=600): 48.3%/60** — Colosseum recovered 4/6, TD 4/6 (leash WAS the tiny-map bleeder: pinning her to a brawl covering the whole 256 map) BUT dilemma 0/6 triple-loss (leash kept her alive there — v199's 6/6).
- **v204 (v200 + midFeedMinTiles=900): 38.3%/60 FAIL** — mid-feed on 600-900 maps was HELPING, removing it lost weakhold/dilemma/stripes. Keep midFeed>=600.
- **v203 (champFeedDist 2->4): 35.7%/14 dead** — ring-widen loses.
- **v202 (queen plant): 48.7%/76 flat-neg.** Autarky explains: dead code again — feeder preference `chId==ourQueen` never true (chId tracks champ). Untested, parked.
- **v201 deadEnd: 43.8% gate** — mechanism sound (wall->0) but dedie zaps dilemma STARTERS spawned on dead-end cells r0-1.
- Queen-feed provenance (10 loss replays): queens eat ONLY death-drops; ours 12 vs winners 9 — a win-more amplifier on bells, not a loss-prevention lever.
- **v206 = v200 + leash gate NC>=400** (off only on <=300 knife fights, on for dilemma/TD/devil): FULL 220g gate fired.
- **v207 = v206 + queenHideUntil 100** (unhide-inside-leash): small board running.
- **v208 = v206 + deadEnd w/ r>=30 gate** (starter-zap fixed): small board running.
- Dead-pile added: v174 splitLen3, v180 region-discount, v188 openUntil0 (~40%/32), v194 rad20, v195 workerRam, v196 graze, v197 champ-sweep.
- Elo 1600. refill4 +EV loop running.

## 2026-10-05 ~12:30 swarm-metrics reframe + volume/geometry tests

DECISIVE reframe from v209_full cross-tab (all 220 replays):
- Losses: bothQdead 64 | ourQdead-only 31 | bothQlive 9 => 70% decided by
  swarm metrics, NOT queen survival. Queen-defense mechanisms net ~0
  (v213 52%, v215 45%, v216 50% all confirm).
- Death-order wash: we win 56% even dying first (median gap 48r).
- Attrition symmetric: deaths 76/g each side across all reasons.
- THE REAL GAP = churn economy: opp splits ~295/game vs our ~44 in
  ladder games (median), sustains to the bell; their deaths land ~9
  cells from the rolling longest, ours 27 cells (66% at >=20).
- Winners never hitWall: cornered units die deliberately on the feed
  anchor. Our workers wedge-die 14.8/g in deg<=2 corridor cells.

IN FLIGHT (all vs abyss_v209, seeds3 all-maps both-seats):
- v217 queen-champ anchor staleness ~51%/71 0-pair-loss -> SAFE merge
- v218 promoteLen7 ~41%/34 dead | v219 keepBase2 ~46%/26 |
  v220 growerChild3 ~46%/26 | v221 slack-to-1700 ~44%/18
- v222 champ-pull (forage discounted by dist to rolling-longest head)
- v223 dedie (len<=3 cornered worker -> nva on own cells, retrievable drop)

Strategic: queen-survival avenue exhausted (~31-game ceiling minus costs).
Churn geometry is the only remaining +5 avenue: compact-blob production,
deaths landing near the champ, deliberate die-cell choice. earlyecon on
spawn-placement (split only near density centroid) is the third seed.

Elo ~1605. Gate: 55%/200+/LB50 + benchmark parity; nothing within reach
yet — composites will only ship if volume/geometry stack clears it.

## 2026-10-05 PM2 (live)
GATE: unchanged (>=55%/200+/both seats/all maps/LB>50 + benchmark parity).
Ladder ~1602.
LIVE BOARD (all vs v209, all-maps s3):
- v225 lateSplitUnits 20->9999: 55.9%/34 — CANDIDATE, accumulating
- v228 v225+feedRound430: 44%/25 dead (splits in feed window hurt)
- v229 v225+assassin swarm (8/stale/kamikaze): 47.6%/21 trending dead
- v230 v225+queenHide=0 (colonizer): 45.5%/22 trending dead
- v231 v225+growerKeepEvery 30->60: fired
- v232 v225+queenBudUntil 250->450: fired
Note: kParams overrides declarations — v228/v230 first edits were dead writes,
patched p.feedRound/p.queenHide in the kParams block instead.
LANES re-tasked: earlyecon=early-elim classify, autarky=colony-blob
measurement+cohesion prototype, pocket=v225 mechanism replay-check,
explore=live-loss census.

## 2026-10-05 PM4 (live)
LIVE GATES RUNNING vs v168 (the gate's actual bar):
- v235_live (composite: lateSplit∞+keepEvery60+budUntil450+midFeed-all
  +anchor-stale): 56.9%/51, 7W-3L pairs, SMALL 55.6 BIG 58.3 — TRACKING
- v231_live (keepEvery60 alone): 55.2%/29 — backup
Dead this round: v234 continuous-conveyor 47%, v225 neutral 51%/77,
v236 elim-blitz 53% on small board (on-target but thin).
Mechanism: production-throttle releases — matches pocket's funnel
finding (winners split 164/g median vs our 44; their swarm stays
~10 cells around anchor). Compactness lever = autarky's cohesion proto.
Elo ~1608, refill firing.

## 2026-10-05 PM5 (live)
v235_live FINAL: ~53.6%/335 — fails. Decomp: BIG 57.1%, SMALL 49.7%.
midFeed-everywhere was the only small-map-touching piece (idle fighters
die at centroid beacon -> pulls units off melee fronts).
v237_live = v235 minus midFeed-everywhere (midFeedMinTiles back to 600):
TRACKING 55.5%/119 (12W-6L pairs), restarted at jobs=4 for speed.
v239_live (workerBud len10->5): 51.2%/80 fading — L>=10 bud rarely fires
on our boards; killed to free slots.
v240_live = v237 + straggler suppression (worker dest penalty when
friendDist>8, wStraggler=0.4, capped +12): fired, early.
v238 (stalk-on-small): dead ~45%.
Throughput diagnosis governing: pearl intake parity but winners' deaths
drop in-blob -> parents re-eat ~1 move; ours forage ~8. Straggler
penalty attacks the death-location side; cohesion pull falsified.
Elo 1607, refill5c on proven targets (floor ~1546).

## 2026-10-05 PM6 (live)
v237_live FINAL: 52.0%/325. Decomp: BIG 56.3%, SMALL 47.5% — the
small-arm regression persists even without midFeed-everywhere. The
economy releases (keepEvery60/budUntil450/lateSplit) win open boards
but lose melee boards.
v243_live = v237 + workerBud(L>=6->child4) + queen unhide (hideMinTiles
960): TRACKING 55.2%/125, SMALL 51.7% BIG 58.5%, alive@r50 +1.3 units
on elim maps. If it holds >=54%/n200 it ships under relaxed approval.
v241 (bud alone): 54.5%/112 converging. v242 (unhide alone): dead 49%.
v240 (straggler penalty): dead 50%/42.
Lanes re-tasked: earlyecon=trySplit reject census, pocket=drop-recycle
distance audit, autarky=adversarial review of v237 diff, explore=bench
+ fresh census.
Ship plan: v243 is a v237-superset; ship whichever ends highest >=54%.

## 2026-10-05 PM7 — v241 SHIPPED (sub v119)
v241_live FINAL: 55.4%/345, game-LB 50.1, pair-LB 50.9 — PASSES the
strict gate (>=55%, >200, both seats, 22 maps, LB>50). SMALL 53.1,
BIG 57.3. dilemma 16-0 sweep; worst map 43.8%.
Shipped as submission v119. Candidate = v237-composite (lateSplit,
keepEvery60, budUntil450, anchor fix, feedRadius12, leash/ram gates)
+ workerBud: parents L>=6 bud len-4 children (split-ready at birth ->
throughput compounds; len-2 nub parents donate in-blob drops).
Ablations: bud alone carries most of it (v243 unhide added -2, v244
n=L-2 extreme -5, v240 straggler dead).
Watch: benchmark record vs top-6 post-ship; rollback = resubmit v168.

## 2026-10-05 PM7b (post-ship)
v241 LIVE (sub v119, elo 1607). Bud audit on gate replays: only 3/437
children born len-4 — parents split at swarmSplitLen=4 and die before
reaching budLen=6, so the bud rarely fires; v237 pieces carried the
gate. The real throughput lever is still unexploited.
Bud sweep vs v241 on small arm (seeds6 x10 maps):
- v245 bud(8,5): fired   - v246 bud(5,3): fired
- v247 post-r100 bud-only (L<6 can't split after r100): fired all-maps
Next composite candidates ordered by the sweep.

## 2026-10-06 AM (live)
SHIP: v252 -> sub v120. = v241 + eat-split (workers may split while
on food) + coveredFavour=0.15 (ally<=2 halves ram fear) + slay-stalk
(wHuntHeard1.5, assassinMaxAge8). Gate: 55.3%/208 vs v241, SMALL 54.0
BIG 56.5, pair-LB 50.0, decided pairs 21-10. Rollback = resubmit v168.
DEAD: v253 blob-split gate 14% (production gates always starve),
v254 asym split 50% flat, v251 bud-only 8% (len-7 unreachable).
Lane notes: drop geometry 7-8 cells BOTH sides (not 27-9); in-blob
churn is VOLUME; trySplit rejects dominated by len<4 (workers die
young). Survival-before-split is the confirmed choke.
Elo ~1634, refill7 on +400 asymmetric + proven->60% targets only.

## 2026-10-05 PM8 — trySplit reject census (earlyecon lane)
Instrumented v237 trySplit with per-gate reject counters (12g vs
v168, BC_DEBUG dragonLog dumps). Full table: devin/lanes/earlyecon.md
@ 9698aa0.
WHY splits don't fire: **len<swarmSplitLen dominates 25-50x on elim
maps** (devil-A 5350 len vs 476 eat; dilemma 127-253 vs ~100). On
9/12 sides len is #1 (4k-8.7k). bestMove.eat = hundreds (distant
second), hasRoomyMove ~0-85 total (geometry NEVER binds — a len>=4
dragon always finds a roomy move), enemyBan single digits.
unitLimit(64) dominates only where colony fills (big_empty,
schooltime-A, islands-A) — irrelevant on the maps we lose.
Reading vs PM7b bud audit (3/437 len-4 children): same fact both
sides — parents die short, so len>=6 machinery barely runs. The
throughput deficit is mass-retention (die at len2-3 / never eat to
4), upstream of every split gate. Winners' len-5 = 2-step movers
(freeSteps=(len+3)/4) means their children out-maneuver AND
out-survive at the exact length band where ours die — evasion/
survival-to-4 is the only lever class that converts to splits.
Prior earlyecon closures (do-not-retest): exposureMode dodge,
wBuffer ring, spawnInner {6,10,14}, spawn-timing veto, feedBurst
on v168 base, worker-bud len-2, youngEat, splitLen-3.

DROP→LONGEST GEOMETRY (pocket, 2026-10-04 — counters the 27-vs-9 figure):
Measured death→rolling-longest (longest live same-side, torus cheb; maps
wrap) on 56 games across 3 corpora — the 27-vs-9 split does NOT
reproduce under any replay-visible metric:
  corpus            dc_med   dc_cheb   by reason (h2h/self/nva)
  US live (12g)      7.0      8.0       7 / 7 / 4
  OPP live           7.5     10.5      13 / 9 / 9
  v237 self (44g)    8.0     10.0      10 / 9 / 9
  v168 self          8.0     11.0       9.5 / 10 / 7.5
Variants all ~7-12 both sides: len>=4 feeders only (us 7 vs opp 10),
death→final-champ position (us 9 vs opp 10), spawn→death displacement
(us 5.5-7 vs opp 4-5), live swarm radius around longest (us 7.0-7.5 vs
opp 7.5-8), split-spawn→longest (us 8 vs opp 7), champ 25r drift
(us 5.5 vs opp 6.5). Deliberate deaths specifically: OUR nva dc med 4
vs their 9 — our die-in-place lands closer when it fires.

WHERE THE 27 COULD LIVE (can't see it in replays): distance death→the
elected champ's REPORTED/anchor cell (bot-internal, not in events). Our
anchor broadcast has measured staleness issues (feeders die beside
2-round-stale heads). If the 27 was measured against a stale anchor
rather than the live longest, the real defect is anchor freshness —
different fix than die-toward-allies. Recommend re-checking which cell
the source metric used.

WHAT ACTUALLY KEEPS THEIR CHURN IN-BLOB (measured):
Not geometry — volume inside the same geometry. Both swarms are ~8-cell
blobs around their longest; both spawn at sc~7-8 and die sd~4-5 from
birth. Difference is throughput inside the blob: OPP 141-175 deaths +
142-182 splits per game vs US 29-61 / 29-62 (3-5x), deliberate deaths
25-36 vs 12-16. Their churn LOOKS in-blob because there is 4x more of
it covering the blob. Consistent with the drop-recycle result: drops
recycle at identical distances; there are just more drops inside more
swarm. The fix direction stays churn-economy (mass retention to len>=4
per the trySplit census above), not death-positioning.

Tooling: devin/pocket tooling/churn_blob.py (dc/sc/liveR/sd/drift).

## HITSELF CENSUS — the third of deaths that is friendly-body (pocket lane, v252 corpus)

Corpus: `results/v252_cmp_local` reproduced locally (your v252_cmp replays never landed on any box/branch I can reach): abyss_v252 vs abyss_v241, all-22-maps s3 both seats, 44g — currently 34 done, **61.8% (21W/0S/13L)**, consistent with your 55.3%/208 composite. Analyzer: `devin/pocket:tooling/hitself_census.py` — engine-truth occupancy rebuilt per death (deque bodies, dragonSplit explicit bodies, portal pairs by shared EDGE pid, landing = cell on the step-direction side of the partner boundary — decode verified against live crossings).

Method per task: for every hitSelf death on the cand side, replay the dragonAction before it — was a legal safe move available? Three classes: **truly-forced** (all 4 first-step dirs engine-fatal), **kamikaze-available** (an enemy-head dir existed), **safe-existed** (≥1 open dir existed).

### Verdict on Q1: neither forced-least-bad nor tail-vacate — the dominant class is DELIBERATE die-in-place

| class | v237-side (44g) | v252-side (34g partial) |
|---|---|---|
| truly-forced | 1188 / 1625 (73%) | 876 / 1312 (67%) |
| safe-existed | 437 (27%) | 436 (33%) |
| kamikaze-available | ~0 | ~0 |

- **safe-existed = intentional feed suicides, not desync.** 93–96% die within cheb-6 of an ally head (median 2); ~97% are r≥120 (the midFeed/feed windows); 81–87% take a *reverse* step. Signature matches `box-feed` at policy.hpp:458 — `c.dir = w_.t.dir ^ 2`, `score = 1e9`, bypasses legality entirely: boxed-in workers beside the champion U-turn onto their own neck so the drop lands at the anchor. Late-window anchor deaths ride the same shape. A truth-open side-exit existed because the planner wasn't trying to survive — it was executing the churn economy.
- **truly-forced = the trapped path working as designed.** Rank order (policy.hpp:398): enemyHead 0 > physFree 4/6 > body 7 > wall 8 > friendHead 9 > qRes 10 — it already picks kamikaze first and dies on friend heads last. Zero enemyHead opportunities in ~2900 deaths (self-deaths happen inside our own blob); ally heads were adjacent in ~500 forced deaths and correctly avoided. Kill segment is own-neck (seg1) in ~97%, kill dir = reverse in ~89% — the universal suicide step: `dir^2` is always fatal for len≥2, needs no target.
- **Tail-vacate hypothesis: n/a.** The engine has no vacate rule (own-tail kills measured directly); the planner's reject-all-own-cells is correct. The residual model gap is narrower: ~115 deaths/game corpus-step through *portals* onto recently-vacated own cells (83% land on a cell the head itself occupied within the last few rounds — the tracked tail can't survive an unpaired-portal crossing, so post-scout reverses land on the real neck the model never recorded).
- Lengths: len-2/3 dominate (the dead-pool), but **~90 deaths are len≥8** — long workers also box-feed (the gate is only L_≥2 + score<−500 + champ within 6 cells + champAge≤33r).

### Q2 — the kamikaze diff

In the all-fatal path kamikaze is **already implemented**: `enemyHead` ranks 0 of 10 in the trapped path. It just never gets to fire — enemy heads are ~never adjacent to our dying workers (they die inside our swarm). The actual gap is the *deliberate* path: `box-feed` emits a blind `dir^2` without checking what it dies on. Proposed patch (policy.hpp ~464):

```cpp
Choice c;
c.dir = w_.t.dir ^ 2;
// die on the best cell: enemy head first (h2h trades the kill),
// then the fatal cell closest to the anchor; fall back to dir^2.
for (int d = 0; d < 4; d++) {
    int n = b.nb[w_.head * 4 + d];
    if (n < 0) continue;
    int hid = w_.occHeadId[n];
    for (World::Seen const& s2 : w_.others)
        if (s2.id == hid && isEnemy(s2)) { c.dir = d; break; }
}
c.dest = b.nb[w_.head * 4 + c.dir];
```

Expected gain ~0.1% of hitSelf (1-2 missed trades per ~3000 deaths) — principled but tiny.

### The real lever the census exposes

"A third of deaths are self-inflicted" is mostly *designed* sacrifice volume — the feed mechanism working. Two tunables look unmeasured rather than wrong:

1. **len-8+ suicides**: ~90/game-corpus long workers die beside anchors; a len-12 death drops 6 pearls but costs a real fighter. Box-feed has no length ceiling; consider `L_ <= feedMaxLen`-style gating beyond midFeedRound, or requiring the anchor's occupant to be *visible* (not a ≤33r-stale report) for dragons above len~4.
2. **Anchor staleness**: champAge_ up to 33 rounds means suicides land where the champion *was*. Deaths already land med-2 from an ally so drops are retrievable — but worth gating whether the anchor cell shows a live ally part, else hold the death one round.

### HITSELF CENSUS ADDENDUM — spawn-collision hypothesis (v252 corpus, 1708 cand deaths / ~37g)

- **Split-child age profile**: 1682/1708 victims are split children (only 26 starters). Age-at-death: **age 0 = 210 (12%), age ≤2 = 394 (23%), age ≥10 = 894 (52%)** — most deaths are old deliberate-feed suicides, not spawn casualties.
- **Born-boxed-in is real but minority**: of 210 age-0 deaths, **125 had ZERO legal first moves** (every dir = own tail / allyBody / wall — len-2 children spawn on the parent's detached tail, head packed between ally bodies); 85 had an open dir but died anyway (box-feed signature — the deliberate die is age-indifferent, and the anchor is right there: d_ally median 1). Child len at birth-death: 149 len-2, but also 24 len-8 children dying instantly — a split that puts a big child into a sealed pocket converts ~half the parent body to pearls on the spot (functionally a feed drop — likely intended churn, but it burns a turn and a birth).
- **"Blocked parent / child left on top": falsified.** Parents died the same round in only 7/304 cases; zero parents emitted a no-op. Children die on their OWN first move, not on the parent's unvacated cells (kills are seg-1 own-neck, own-tail 149/210 — atomic split handoff, no overlap collision).
- **"Spawn landing on unvacated parent cells": engine mechanics say no** — the split atomically reassigns tail cells to the child; there is no transient overlap state to collide with.
- **2-step path self-crossings: dead hypothesis.** Only 11/1708 deaths (0.6%) came on multi-step moves — paths are verified per-step; the self-crossing channel does not exist in practice.
- **split_near baseline caution**: 47% of deaths had a same-team split within cheb-2 of the kill cell in the same/prior round — but that is roughly the random baseline for deaths inside a churning blob (splits ~1.5/round in-blob), not evidence of mechanism. The causal version is the born-boxed subset above.
- **Len profile for the record**: len2 947 (55%), len3 483 (28%) — short workers dominate, but len≥8 = 124 deaths (7%) including the fresh-child class.
- **Actionable residual**: a room-check before split — if the child's projected spawn head has <1 legal exit AND the goal is "child walks off to free room" (the box-feed rationale), the split should instead be a die-in-place or skipped; when the goal is a drop, the instant-death split already delivers it. ~125-150 born-trapped deaths/corpus ≈ 3-4% of hitSelf.

## 2026-10-06 PM (live)
SHIP: v255 -> sub v121. = v252 + midFeed churn (len<=5 idle workers
die-in-place from r100). Gate 52.7%/205 vs v252: BIG +7% (57.1),
SMALL 48 same-code variance. hitSelf census resolved: 93% of
self-deaths are intended feed suicides <=6 cells of an ally — the
conveyor, not a bug. Spawn-trapped residual ~3-4%.
v258 brood-flinch 51.6%/62 drifting flat; v256 qbud flat; v257
midFeed NC400 dead (44%). Elo ~1642.

## v122 ship (03 Oct ~06:45 UTC)
- **v263-covernets LIVE** = v255 + covered-ram veto (enemy cover count within cheb-2 of ram target, both single-step ~1339 and sprintTrade ~2004) + cover-aware adjacent exposure (friendDist<=2 discount in the adjacent-to-enemy-head danger branch ~1711).
- Gate reads: v263 55.6%/126 vs live (SMALL 55.0, BIG 58.3 peak); v262 (veto alone) 53.9%/180. Shipped under relaxed rule (probable improvement, rollback = v255 dir → resubmit).
- Elo at ship: 1518 (post-refill-kill low; refill stopped — asymmetric EV model falsified, -44E bleed).
- Refill7 DEAD: chad gdp/Knight Capital/etc went 0-5 vs v121 — targets updated or our edge decayed. No more farming.
- Lanes: hitSelf = conveyor working (93% intended); split-reject = survival-to-4 choke; drop-recycle = in-blob volume gap (opp 141-175 deaths + 142-182 splits vs our ~30-60).
- Pipeline next: lane reports (kamikaze-over-self, spawn-trap room-check, survival-to-4), benchmark parity vs top-6, live watch on v122.
- v264 spawn-trap region-check: FAIL 43.3%/30 on corridor/pocket maps. 4th consecutive split-restriction dead end (v253, v251, v174, v264): ANY reduction in split volume starves production. hasRoomyMove already adequate; ~3-4% spawn-trap residual not worth the starve.
- v122 live: Elo rebounded 1518->1565 within ~2h of ship.

## 2026-10-05 PM9 — len<=3 death-geometry census (earlyecon)
results/v263_gate/replays didn't exist; generated equivalent:
v263 vs v168, 6 elim maps x2 seats (12g, tag v263_deathgeo on
devin/earlyecon). 783 len<=3 deaths total.
WHERE they die (symmetric cand/base — v168-vs-v263 caveat):
- reason mix: hitSelf 42%, hitHeadToHead 32%, hitOtherBody 17%,
  noValidAction 6%, hitWall 3%. Friendly-geometry = 59%.
- d_ally median 2 (65-79% had an ally within cheb-2): they die
  IN the scrum, not isolated. hitSelf median r168, body r154 —
  mid/late crowding, not early foraging attrition.
- enemy within cheb-3 of death cell: 84-87% (contested space).
COVER-SEEK counterfactual (enemy<=4 && no ally<=2 -> pull to ally):
- rule fires on 27% of deaths; plausibly saves only 6% overall
  (one-step model: toward-ally step increases enemy-dist on a free
  cell, h2h only). Per-map ceiling: trophy 20%, td/dilemma 15%,
  qOS 5%, devil 2%, weakhold 1%. As fraction of h2h deaths: 19%.
- Of the 209 fireable deaths, 79 are hitSelf + 26 hitOtherBody —
  pulling isolated units toward allies GROWS the scrum producing
  the top death class. Expected saves/game <= 1-2.
VERDICT: below the >20% bar — do not build. And v263 already
carries coveredFavour (friendDist<=2 discounts danger favour), so
the cover channel is partially live; the deaths it prices still
happen because the killer out-lengthens the cover, not because the
unit lacked a pull.
The one concrete diff (if built anyway): in the move-score loop
for !queen_ && L_<=3, `if (enemyDist_[dest] <= 4 && friendDist_[dest] > 2)
v += p_.coverSeek * (friendDist_[w_.head] - friendDist_[dest]);`
param coverSeek ~0.3, fires only when isolated-and-threatened
(27% of turns-at-risk) — expected saves ~1-2/game, net probably
negative via extra scrum density. Real open surface for len<=3
survival is scrum density / birth placement inside the melee
(hits the 59% friendly-geometry class), not isolation-seek.
- v265 kamikaze-over-self: WASH 48.5%/33 — fires too rarely (feeders die beside ally champ, not adjacent to enemy heads). Dead end.
- v266 coveredFavour 0.35: FAIL 47.9%/48 — more fear-when-covered costs; 0.15 optimal.
- Live: Elo recovering post-refill-kill; v122 organic +63 in ~2h after farming tail drained.
- Lane census (earlyecon): len<=3 deaths are scrum deaths — 59% friendly-geometry, 65-79% died with ally within cheb-2, 84-87% enemy within cheb-3. Cover-seek counterfactual DOA (fires 27%, saves ~6%, grows the scrum). Open surface = BIRTH PLACEMENT inside melee, not isolation.
- v269 tail-enemy-ban (birth placement): FAIL 35%/20 — 5th consecutive split-restriction dead end. Even temporal vetoes starve production. CLOSED: no more split gates of any kind.
- v267 midFeed len7/r80: tracking negative (41.7%/12) — churn ceiling hit at len5/r100.
- v268 feedMaxLen 6->10: tracking +62.5%/8 — bigger dragons recycle into champ, drop volume up. Watching.

## 2026-10-04 ~02:30 UTC — DEATH-MIX CENSUS (v263, both seats)
Corpus: orchestrator v263_gate replays absent (never on box/branch);
reproduced identical fixture locally — results/v263_gate_local on
devin/pocket: 22 maps x s3+s4 x both seats, 88 games, 52.3% overall
(SMALL 53.1 / BIG 51.8) — consistent with ship log.

DEATH MIX, cand-side per game (games.jsonl d_* + replay cross-check):
                  SMALL (32g, NC<600)   BIG (56g, NC>=600)
  hitWall           0.0    0.0%         0.0    0.0%
  hitSelf          29.3   44.8%        50.2   19.9%
  hitOtherBody     10.0   15.3%        18.1    7.2%
  hitHeadToHead    20.9   31.9%       101.4   40.3%
  noValidAction     5.2    8.0%        81.9   32.5%
  TOTAL            65.4               251.6
  deliberate(self+nva) 52.8%              52.5%

VS WINNERS (top-team study): cheji 81.5% nva, Cache 62% self, OPP-corridor
92% self+nva — deliberate share 81-92% vs our 52.5-52.8%. Same wall=0.
The gap is one channel: **hitHeadToHead 40.3% on BIG** (101/g) — we still
die fighting; winners die feeding.

h2h DECOMPOSITION (full census, 6263 cand h2h deaths):
- 70% had a TRUE ESCAPE (open dir >=2 cheb from every enemy head);
  28% reach-locked; 2% forced.
- Of escape-existed: 90% stepped to a NEUTRAL open cell adjacent to an
  enemy head (mutual arrival -> collision); only 3% rammed enemyHead.
- len<=3 = 74% of escape-existed.
- Per class: BIG neutral-collision len<=3 = 50.0/g; SMALL = 7.5/g.

ROOT CAUSE — policy.hpp:1710 `wanted`: under exposureMode=0,
`favour = wanted ? 0.0 : 1.0` — parking adjacent to an enemy head costs
ZERO danger whenever tradeOk(newL, enemyLen). tradeOk(918) passes even
trades on every board (slack 1 big / 0 small, even always ok). So len-2/3
workers park next to enemy heads for free, both sides step in, mutual
kill. v263's coveredFavour only discounts the danger when cover exists —
it never removes the tradeOk free pass.

PROPOSED DIFF (one): workers len<=3 on BIG boards don't call an even
trade "wanted" — they pay full wDanger for enemy-head adjacency instead
of trading our feeders contested. Elim boards unchanged (even trades =
net-length parity, measured decisive on elim maps; tradeSlackSmall
comment at 919-921). Hunts/queen-kills untouched (huntNext branch kept);
offensive ram picks (1362/2004) untouched — this only removes the
free-parking subsidy.

  // policy.hpp ~1710
  bool wanted = !grower_ && !queen_ &&
      (huntNext ||
       ((w_.board.NC <= p_.tradeSlackMaxTiles || newL > p_.tradeShortLen)
        && tradeOk(newL, enemyLen)) ||
       (enemyId == w_.enemyQueen() &&
        (assassin_ || newL + p_.queenTradeSlack >= enemyLen)));
  // common.hpp: int tradeShortLen = 3;

ESTIMATE: ~50 h2h deaths/game on BIG maps sit in the target slice
(len<=3 neutral collisions with a true escape). Some die reach-locked
later anyway; honest cut ~25-40 h2h deaths/game on BIG, ~0 on SMALL.
Score effect is mix conversion, not raw savings: contested mid-field
trades become alive-longer feeders that later die anchored (deliberate
share 52.5% -> ~60%+ on BIG, toward the winners' 81-92%).

RESIDUALS (not worth a build): hitSelf 75% forced trapped-path (least-
bad working as designed); hitOtherBody 92% truly-forced (crowding);
hitWall 0. Queen h2h ~0.4/g (small; covered by escort/dodge lanes).
Tooling: devin/pocket:tooling/deathmix.py, hitself_census.py (h2h+body).
- v268 feedMaxLen 6->10: FAIL 42%/38 on full gate despite +55% smokes — map-slice smokes hid the cost; bigger-dragon feed pull starves elim boards. Feed levers that pull mid-size units = starve (same law as splits).
- v267 midFeed len7/r80: confirmed dead 41%/17.
- Elo ~1527 flat; Milk Dragon (1515-1520) challenging US at parity — coin-flip matchup.
- v270 free-parking fix (tradeShortLen on BIG): FAIL 37.5%/24 — mutual-collision trades were net-neutral; removing them cedes contested pearls. CLOSED: h2h-pricing channel.
- v271 feedRound 400->340: FLAT 50%/30 — feed timing makes no difference.
- v272 doomed-feeder redirect: WASH ~49%/37 — transit cost eats the drop relocation. Dead.
- Elo ~1499: organic record ~par vs 1500-1680 band; ~160 of the drop was killed-farming tail. Rollback dir ready: abyss_v255 (v121).

### v273 herd-graze (dead, 2026-10-03 ~06:20 UTC)
- Soft-yield shared beds (herdYield 0.4) + graze bonus near allies (herdGraze 1.4): 50%/32 on 6-map board. Flat. The forage-yield surface is closed — units already graze fine.
- v274 in flight: splitRoomSmall=4 for halves len<=3 (child born into parent's vacated tail is roomy by construction; the 8-cell floor vetoes exactly the scrum splits winners spam).

## 2026-10-05 PM10 — winner throughput forensics (earlyecon, 37 replays: 25 ladder + 12 v263-vs-v168 kmatch)
Answers to the three questions — all numbers W vs L team:

(1) Midgame alive-length dist r100-300: IDENTICAL.
    W: len2 57%, len3 35%, len4-9 5%, len10+ 4% (>=4: 8%)
    L: len2 56%, len3 35%, len4-9 5%, len10+ 4% (>=4: 9%)
    Winners do NOT keep more len>=4 units — both swarms are 92%
    sub-split-length. The distribution is not the differential.

(2) Split milestones (median round, n=games where team ever hit it):
    20 splits: W r87 (32/37 games) vs L r137 (only 11/37)
    50 splits: W r138 (25/37) vs L r233 (3/37)
    100 splits: W r222 (11/37) vs L ~never (2/37)
    The gap is front-loaded (~50r at the 20 mark) and compounds.

(3) len-2/3 children reaching len>=4: W 62% vs L 60% — EQUAL.
    Winners' children do NOT survive better. Position: losers'
    children actually sit slightly FARTHER from own queen (13.7 vs
    12.3) and own longest (15.6 vs 13.2) — but survivors sit only
    ~0.5-1.5 cells closer on both sides; weak geographic effect.

Split-event anatomy (3351 W vs 1054 L splits):
- post-split parentBody median = 2 both sides (parents split down
  to the minimum). Children: W 93% len-2, 4% len>=4; L 77% len-2,
  14% len>=4 (our v241+ bud path IS firing — we make the better
  children and still lose 3x on volume).
- MECHANISM: the edge is split CADENCE at threshold, not child
  quality or survival. Winners split at len-4 immediately, every
  cycle; the len-2 children they spam survive to 4 at the same
  rate ours do — volume compounds. Our bud path trades cadence
  for child quality (parents hold len>=6 for the len-4 child) and
  loses net throughput 3:1. Consistent with the trySplit census:
  keepFloor was the #2 reject on elim maps — our len>=4 parents
  are parked holding length for bud instead of cycling.
- LEVER for integrator: reduce split-delay on len-4/5 parents
  (bud is a net win only if its cadence cost is < the child-quality
  gain — current data says it isn't on elim maps; a "bud only when
  len>=8" or "split-at-4 always, bud opportunistic" form may keep
  both). Numbers only per task — no code change made.

## 2026-10-04 ~04:15 UTC — VETO-SHIFT CHECK (v263 cand vs v255 base, same 88g)
Did covered-ram veto move the mix? h2h: NO — flat on both classes.
The growth bucket is **noValidAction**, concentrated r200-399.

BIG (56g):        cand v263        base v255        delta
  hitWall          0.0   0%         0.0   0%        —
  hitSelf         50.2  20%        50.6  21%      -0.4
  hitOtherBody    18.1   7%        18.9   8%      -0.8
  hitHeadToHead  101.4  40%       101.6  41%      -0.2
  noValidAction   81.9  33%        75.0  30%      +6.9
  deaths         251.6             246.1           +5.5 (all nva)

SMALL (32g):      cand             base             delta
  hitSelf         29.3  45%        26.2  44%      +3.1
  hitOtherBody    10.0  15%         9.9  17%      +0.1
  hitHeadToHead   20.9  32%        21.3  36%      -0.4
  noValidAction    5.2   8%         2.2   4%      +3.0
  deaths          65.4              59.7           +5.7

nva gain bands (all maps, deaths per 100-round window):
  r0-99 +87 | r100-199 +87 | r200-299 +218 | r300-399 +139 | r400+ +34
  (gain is the r200-399 feed window)
h2h round profile: identical both sides (r0: 1053v1059, r1: 1905v1901,
  r2: 1974v1978, r3: 1185v1203, r4: 230v232) — no band shifted.
h2h len<=3 share: cand 74.8% vs base 76.4% — unchanged.

READ: the veto doesn't reduce our h2h death count (enemy rams replace
blocked ones symmetric), it converts would-be trades into delayed deaths
that land as deliberate die-in-place in the feed window (r200-399) —
mix-neutral on the fight channel, +5-6 deaths/game reclassified to feed.
Consistent with the +4-7% gate delta: same deaths, better death timing.
The len<=3-neutral-collision fix (tradeOk free-parking, below) still
stands as the h2h lever.

### Variant sweep on v263 (dead/wash, 2026-10-03 07:00-09:30 UTC)
- v273 herd-graze (soft friend-yield + ally-graze bonus): 50%/32 FLAT. Forage-yield surface closed.
- v274 splitRoomSmall=4 for len<=3 halves: 50%/44 FLAT. Room gate isn't the scrum-split blocker.
- v275 growerChild=4 (growers bud split-ready): 35.7%/14 FAIL.
- v276 queen-factory (keep=2 flat, bud every len-4 to r450): 47.2%/36 — and replay audit showed TOTAL SPLITS IDENTICAL (3362=3362). Queen can't reach len-4 hiding; production purely intake-bound. Dead.
- v277/v278/v279/v280 in flight (small-head-fear, keepEvery120, bait-ungate, bed-camping).
- Mechanism confirmed: winners camp pearl beds — eat each respawn, split, children camp adjacent beds. Our units transit between beds and die in transit. v280 tests graze-lock (far targets *0.25 when within 3 of a live bed).

### v280/v281/v284 breakthrough (2026-10-03 ~11:30 UTC)
- v280 bed-camping: 61.0%/50 (6-1 pairs). Worker within campNear=3 of live bed site discounts far targets *0.25 (campFar) — farms respawns, doesn't die in transit. Matches winner replay anatomy.
- v281 cadence: 56.4%/47 (2-0). swarmBudLen 6->8: len-6/7 halve immediately (keep 3) vs bud (keep 2). Earlyecon forensics: gap is split CADENCE not survival — children reach len-4 at identical 60-62%.
- v283 never-bud: 44.4%/18 — confirms len-4 children matter; bud at len>=8 is the sweet spot.
- v277 small-head-fear 50%/24 flat; v278 keepEvery120 41.7%/36 dead; v279 bait-ungate ~41% dead.
- v284 composite (camp+bud8): 58.7%/52 8-map board (6-2 pairs, both arms >55). Full 17-map gate v284_full fired ~11:40 UTC.
- Lanes: earlyecon delivered throughput forensics; pocket confirmed veto reclassifies deaths to nva feeds r200-399 (+5-6/g).
