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
