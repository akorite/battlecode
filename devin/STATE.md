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
