# starve — weakhold/low-food swarm starvation fix

Bot: `workspace/abyss_starve` (copy of the reconstructed v109 base = abyss_v107 + wh2
deltas + pearl deltas, both applied with `patch -p1`). Flag: `Params::swarmTrap`
(default 1; no kParams override needed) + `swarmTrapCost` (2000).

v109 note: remote branches top out at `abyss_v107` — v108/v109 were never pushed and
the parent session was unreachable, so `workspace/abyss_v109` was reconstructed locally
from the documented deltas (wh2: `trapSeenOnly=1`, `trapFrontier=2`; pearl: openUntil=48,
openQueenKeep=3, openQueenDanger=1.8 + pearl Params block; v107 main.cpp selfguard kept —
pearl's main.cpp revert was a copy-from-v104 artifact). `abyss_svdbg` / `abyss_sdbg` =
diagnostic builds (same policy + BC_DEBUG); exclude from submissions.

## Diagnosis

Reproduced the starvation: v109 vs abyss_cf on weakhold (seeds 3–6, 8 games): 25%,
alive@499 1.67 vs 18.17. Openings are identical (eaten60 ~11, splits60 ~5.4, alive50 ~4);
the divergence is post-r150 population: splits 19–41 vs 103–113.

The mechanism (BC_DEBUG dragonLog + replay parsing):

1. **Pocket-death conveyor.** Worker dragons cycle `forage → cramped → reverse-split →
   trapped (N:kelp E:neck S:kelp W:kelp) → hitWall` at the SAME pocket cells — 15–39
   deaths at `(24,0)` / mirror `(15,14)` alone. weakhold's beds sit at the ends of
   ~4-cell 1-wide kelp cul-de-sacs: `(24,0)` is degree-1 behind the `(27,0)→(25,0)`
   corridor; `(15,14)` degree-1 behind `(12,14)→(14,14)`.
2. **The space check cannot see it.** `nav_.flood` is time-aware: our neck cell frees
   after ~L−1 moves, so the flood "escapes" the pocket through the neck and
   `space >= need` — entry is legal. In reality the head can NEVER retreat through
   its neck: a 1-wide corridor is a one-way ratchet. `viaReverse` then "rescues" it
   (a reverse-split escape exists on paper), but the entered stub still dies at the
   dead end.
3. **Self-baiting.** Each dead dragon drops pearls in/around the pocket → the next
   forager comes for them → dies → drops more. A conveyor running ~1 death / 9 r —
   replays show every victim marching the identical path `(29,0)→…→(25,0)→(24,0)→die`
   in ~9-round cycles.
4. **cf pays the same tax and wins anyway.** cf loses 8–48 dragons/game to the same
   pockets but eats ~300 pearls through them; at 20–25 units it out-produces the
   attrition ~4:1. Our swarm caps at ~5 — every conveyor death removes ~20% of the
   workforce, so the population never ignites.
5. Queen-side: our hiding queen lives to ~r300 (grows to len 31–39 on feeder deaths);
   cf's queen dies `hitWall` r52–72 every game.

## Fix history — three versions, one kept

`swarmTrap`: non-queen dragons on `maze_` maps (kelpFraction > 0.22: arena, devil,
islands, maze, portals, stripes, tower_defense, trauma, weakhold) run a pocket scan
at each candidate dest and pay a −`swarmTrapCost` toll when the dest opens onto a
**baited trap**. `c.terminal = true` still lets a plan take the mouth but never the
trap; when every move is pocket the ranking still prefers food — habitat forage is
preserved.

- **v1 — geometric hard veto.** `deadEnd(seenOnly=false)`; flag `exhausted && !cycle
  && cells <= trapSafeCells` → `stepTerm=-2000`. Worked on the lane gate (weakhold
  +33 vs v104) but the integrator's honest 22-map gate showed 36.9% vs v104
  (v108 = 47.7%): islands/slithery/autarky/big_empty collapsed — pockets ARE the
  habitat there and a hard veto blinds forage.
- **v2 — soft toll.** Same flag, `score -= swarmTrapCost` instead of a veto. Restored
  pocket economy BUT the weakhold conveyor returned untouched: replays + scan dumps
  showed the flag NEVER fired — every dir scanned `cells=32 cycle=1 exhausted=0`
  (the cap). Root cause: `b.nb` only respects *seen* kelp — unseen edges read as open
  — so `seenOnly=false` sees phantom space everywhere. The queen's scan works
  because `seenOnly=true` walls fog.
- **v3 — fog-aware + food discriminator (current).** `deadEnd(seenOnly=true)`;
  flag iff `exhausted && !cycle && cells <= trapSafeCells && frontier <= trapFrontier`
  AND the region (left in `nav_.queue[0..cells)`) contains food
  (`b.bed[c]==1 || w_.seenPearl[c]`). The conveyor's defining feature is a small
  closed pocket *with food* — weakhold's dead ends hold beds and prior victims'
  pearls; an empty dead end is harmless and a large/loopy/unproven region is
  survivable habitat.

## Results — v3, FULL 22-map gate vs abyss_v104 (seeds 3–4, both sides, 88 games)

| map | v109 vs v104 | v3 vs v104 | Δ |
|---|---|---|---|
| **weakhold** | 2/4 | **4/4** | **+2** |
| islands | 3/4 | 1/4 | −2 |
| stripes | 3/4 | 2/4 | −1 |
| australia | 2/4 | 1/4 | −1 |
| slithery_fight | 2/4 | 0/4 | −2 |
| autarky | 2/4 | 3/4 | +1 |
| all others | identical (incl. eight shared 0/4: default, maze, portals, schooltime, stronghold, trauma, unsw, big_empty @0–1/4) | | |
| **ALL** | **30/88 = 34.1%** | **27/88 = 30.7%** | −3.4pp |

Confirmation batch (seeds 5–6, n=8/map): islands v109 6/8 → v3 4/8; stripes 4/8 → 3/8;
slithery_fight 3/8 → 0/8.

alive@499 (r500 games): v3 36.3 vs v104 11.5; v109 36.8 vs 10.9.
small-map eaten60: v3 23.1 vs 28.0; v109 24.9 vs 28.0. wall+self+body deaths: v3 76.5,
v109 90.9, v104 ~72 — v3 dies LESS than v109 despite bigger populations.

## Honest assessment — targeted win, not a gate pass

- **The conveyor is dead.** weakhold 2/4 → 4/4 vs v104 (v109 baseline loses B-side);
  pocket hitWall deaths ~28/game → ~0–4 spread across cells; alive@499 on weakhold
  ~16 vs ~2. The seenOnly+food flag fires exactly where it should — flagged corridors
  show `N:489/−2000/deadend` while the habitat-pocket neighbors stay `forage`.
- **…but the integrator's bar (≥50% vs v104, no 0/4 map) is not met** — and cannot be
  met in this lane: the v109 baseline itself is 34.1% with the same eight 0/4 maps.
  v104 dominates the BIG-map half of the pool; nothing in the starvation mechanism
  touches that.
- **Cost is at noise level outside the conveyor maps.** Net maze_-map delta vs v109:
  −1 game (weakhold +2, islands −2, stripes −1). slithery_fight/australia/autarky
  deltas (−2,+1) are provably not the flag — kelpFraction < 0.22, `swarmTrap` never
  executes, the code path is identical to v109.
- The remaining −2 on islands sits at the noise edge (n=8) but is plausible-costly
  forage: islands' ≤12-cell food pockets pay the toll too. If the integrator wants to
  squeeze it, options ranked: (a) raise `trapSafeCells` floor → flag only ≤6-cell
  pockets (the integrator's bound idea — weakhold's are ≤4); (b) drop the food
  requirement and instead require the region to be a pure path (corridor, not room) —
  but a branched tree traps just as well, so shape is a weaker discriminator than
  bait; (c) gate the flag on unit count (feed the conveyor when rich like cf does).
- Recommendation: transplant `swarmTrap` v3 as-is onto v108 if the integrator accepts
  "weakhold fixed, elsewhere within noise" — the v1 regression is gone; don't expect
  it to move the all-map number while v104 owns the BIG maps.

Replays/runs: `results/v3-gate-all` (22-map v3 vs v104), `results/v109-base-all`
(same-fixture baseline), `results/v3-confirm`/`v109-confirm` (seeds 5–6),
`results/sdbg4-v3` (weakhold replays + scan dumps), `results/sdbg3-scan` (the
`s32c1e0` proof that seenOnly=false never fires).
