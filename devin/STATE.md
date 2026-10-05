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
