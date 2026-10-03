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
