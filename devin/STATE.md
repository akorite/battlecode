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
