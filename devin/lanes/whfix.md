# whfix — weakhold / tower_defense / trauma queen-trap fix

Bot: `workspace/abyss_wh1` (copy of abyss_v104 + fix). Flag: `Params::trapSeenOnly` (default on via kParams), `trapSafeCells=12`.

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

## Results (local, kmatch; cand=wh1 unless noted)

| run | cand | base | maps/seeds | score | notes |
|---|---|---|---|---|---|
| whfix-repro | abyss_v104 | abyss_cf | weakhold,td,trauma ×4 | 41.7% | weakhold 0/8; all queen deaths = pocket hitWall |
| whfix-v1 | wh1 | abyss_cf | weakhold ×4 | 12.5% | pocket deaths 0/8; queen non-ram 1.0→0.125/g |
| whfix-gate1 | wh1 | abyss_v104 | weakhold,td,trauma ×4 | 50.0% | weakhold 4/4 splits; td 37.5%, trauma 62.5%; queen non-ram 0.458→0.250/g; queen alive@end 0.562 vs 0.375 |
| whfix-gate2 | wh1 | abyss_cf | all maps ×1 | 46.4% | **0 r0–5 queen deaths, 0 timeouts**; weakhold split 1/1 |

vs abyss_cf on weakhold the queen-trap loss mode is gone, but games still lose to swarm
starvation (alive@499 1.7 vs 21.0) — a different failure class (forage/economy), for a
different lane. vs v104 head-to-head weakhold is side-determined (every seed pair split).

## Verdict

Ship: the fix removes a deterministic self-inflicted death mode with zero new early deaths
or timeouts on all maps. It does not move weakhold win rate vs strong opponents — the map's
remaining losses are starvation, not queen traps.
