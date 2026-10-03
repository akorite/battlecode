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
