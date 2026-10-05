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
