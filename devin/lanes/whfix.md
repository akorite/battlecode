# whfix — weakhold / tower_defense / trauma queen-trap fix

Bot: `workspace/abyss_wh4` (wh3 + map-size gate). Flags via kParams: `trapSeenOnly=1`,
`trapSafeCells=8`, `trapFrontier=1`, `trapMaxTiles=700`.

`workspace/abyss_wh1..wh3` are kept as the failed iterations (see below); **wh4 is the
ship candidate**.

## Diagnosis

Live-ladder abyss_v104 loses on weakhold because the queen walks into the map's cul-de-sac
pockets (x∈[24,27] on y=0; mirror near x∈[12,15] on y=14) and dies `hitWall`.

Root cause: `nav::deadEnd` (the trap scan behind the queen's pocket veto) treated **unseen
edges as open**. The pocket's far kelp wall sits outside her 7×7 vision when she evaluates
entry, so the BFS "escaped" through fog (scan showed ~32 cells + a cycle) and the veto never
fired. One step later the walls were observed (scan: 3 cells, exhausted) and the veto fired,
but her new body now plugged the pocket's only exit — every move illegal → trapped fallback
picks direction 0 → `hitWall`. Deterministic: reproduced in 8/8 local games on weakhold
(replays: `results/whfix-dbg*/replays`), always on the same pocket cells.

Secondary loss modes on these maps (unchanged, out of scope for this lane):
swarm starvation on weakhold (alive@499 ~2 vs ~21 for abyss_cf) and
`hitHeadToHead` queen combat deaths r200–400.

## Fix

`deadEnd(b, start, wall, limit, seenOnly)`: with `seenOnly=true` the BFS only crosses edges
that have actually been observed (`Edge.seen`); cells with an unseen edge count toward a new
`Scan::frontier` field instead of being traversed. The veto now fires when

- `tiny`/`tree`/`loopRoom` as before (with `frontier == 0` so a scan blocked only by fog is
  not mistaken for a dead end), or
- `unproven`: `trapSeenOnly` on, no cycle, `cells <= trapSafeCells` — the queen demands
  proof of room; an unexplored pocket is a trap risk, not an escape.

Cheap: seenOnly BFS visits strictly fewer cells than before (stops at fog walls).

## wh1 → wh2: the open-map pin

wh1's `unproven` veto fired whenever the confirmed-open region was small — on open maps
the seen region is partitioned by fog and her own body, so small `cells` happened
everywhere, all four moves got vetoed, and the queen starved pinned. Integrator gate:
v107 (wh1 merged) 31% vs v104's 44% on the same fixture (big_empty 4→0, default 2→0,
devil 2→0, trauma 4→2).

wh2 discriminates a pocket **mouth** from open vision via `Scan::frontier` (scanned cells
having at least one unseen edge). A cul-de-sac's fog boundary is ~1–2 cells (one-cell-wide
aperture); open space's boundary is ~all scanned cells.

`unproven = trapSeenOnly && !cycle && cells <= trapSafeCells && frontier <= trapFrontier`

## wh2 → wh3 → wh4: corridors are pockets until proven otherwise

wh3 tightened the mouth signature (`cells<=8 && frontier<=1`) — still a net regression on
the honest 22-map gate (34% at the 53-game mark, abandoned): a thin corridor ending in fog
has *exactly* that signature, so the veto still fired on maze/trauma/stronghold-type maps.

wh4 gives up on geometric discrimination entirely: the whole `seenOnly` scan (and with it
`unproven`) runs **only when `NC <= trapMaxTiles` (700)** — all 10 small ladder maps
(weakhold 600, td/dilemma/devil/portals 512, trophy 625, stripes 288, Colosseum/
default_small 256, arena 121) get the fix; every big map gets byte-identical v104 scans,
so the pin regression cannot exist there by construction.

## Results (local, kmatch; cand=wh1/wh2 unless noted)

| run | cand | base | maps/seeds | score | notes |
|---|---|---|---|---|---|
| whfix-repro | abyss_v104 | abyss_cf | weakhold,td,trauma ×4 | 41.7% | weakhold 0/8; all queen deaths = pocket hitWall |
| whfix-v1 | wh1 | abyss_cf | weakhold ×4 | 12.5% | pocket deaths 0/8; queen non-ram 1.0→0.125/g |
| whfix-gate1 | wh1 | abyss_v104 | weakhold,td,trauma ×4 | 50.0% | weakhold 4/4 splits; td 37.5%, trauma 62.5%; queen non-ram 0.458→0.250/g; queen alive@end 0.562 vs 0.375 |
| whfix-gate2 | wh1 | abyss_cf | all maps ×1 | 46.4% | **0 r0–5 queen deaths, 0 timeouts**; weakhold split 1/1 |
| wh2-weakhold | wh2 | abyss_cf | weakhold ×4 | 12.5% | identical to wh1: 0 own wall deaths; cf queen still dies hitWall in pocket every game |
| wh2-open | wh2 | abyss_cf | big_empty,default,trauma ×2 | 50.0% | big_empty 3/4 (alive@499 61–64 — no pin), default 2/4, trauma 1/4; queen deaths all combat r65–430; **0 r0–5 deaths, 0 timeouts** |
| wh2-gate1 | wh2 | abyss_v104 | weakhold,td,trauma ×4 | 54.2% | weakhold 4/4 splits; td 50% (wh1 was 37.5%), trauma 62.5%; queen non-ram 0.25 vs 0.458; queen alive@end 0.562 vs 0.375 |
| wh3-all (abandoned) | wh3 | abyss_v104 | all 22 ×2 | ~34% | same corridor-pin signature; killed at 53/88 |
| **wh4-all (HONEST GATE)** | wh4 | abyss_v104 | all 22 ×2 | **50.0%** | PASS: ≥50%, no map at 0/4 (worst 25%); td 4/4, weakhold/trauma 2/4 splits; 0 timeouts; schooltime r1 hitSelf is a v104 baseline quirk (both queens die identically — other lane owns it) |
| wh4-cf | wh4 | abyss_cf | weakhold,td,trauma ×2 | 41.7% | weakhold 25% (veto intact: 0 own wall deaths, cf queen dies in pocket every game); td 50%; trauma 50%; queen non-ram 0.167 vs 0.583 |

vs abyss_cf on weakhold the queen-trap loss mode is gone, but games still lose to swarm
starvation (alive@499 1.7 vs 21.0) — a different failure class (forage/economy), for a
different lane. vs v104 head-to-head weakhold is side-determined (every seed pair split).

## Verdict

Ship **abyss_wh4**: the pocket veto works exactly where it was needed (weakhold: 0 own
wall deaths; cf's queen still dies in the pocket every game) and cannot fire on big maps
at all (`NC>700` → v104-identical decisions). Honest 22-map gate: 50.0% vs v104, no 0/4
map, no timeouts. It does not move weakhold win rate vs strong opponents — the map's
remaining losses are starvation, not queen traps.
