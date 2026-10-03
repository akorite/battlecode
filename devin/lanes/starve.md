# starve — weakhold/low-food swarm starvation fix

Bot: `workspace/abyss_starve` (copy of the reconstructed v109 base = abyss_v107 + wh2
deltas + pearl deltas, both applied with `patch -p1`). Flag: `Params::swarmTrap`
(default 1; no kParams override needed).

v109 note: remote branches top out at `abyss_v107` — v108/v109 were never pushed and
the parent session was unreachable, so `workspace/abyss_v109` was reconstructed locally
from the documented deltas (wh2: `trapSeenOnly=1`, `trapFrontier=2`; pearl: openUntil=48,
openQueenKeep=3, openQueenDanger=1.8 + pearl Params block; v107 main.cpp selfguard kept —
pearl's main.cpp revert was a copy-from-v104 artifact). `abyss_svdbg` = same + BC_DEBUG.

## Diagnosis

Reproduced the starvation: v109 vs abyss_cf on weakhold (seeds 3–6, 8 games): 25%,
alive@499 1.67 vs 18.17. Openings are identical (eaten60 ~11, splits60 ~5.4, alive50 ~4);
the divergence is post-r150 population: splits 19–41 vs 103–113.

The mechanism (BC_DEBUG dragonLog + replay parsing, `results/starve-diag-v109/`,
`results/starve-dbg/`):

1. **Pocket-death conveyor.** Worker dragons cycle `forage → cramped → reverse-split →
   trapped (N:kelp E:neck S:kelp W:kelp) → hitWall` at the SAME pocket cells — 15–39
   deaths at `(24,0)` / mirror `(15,14)` alone. weakhold's beds sit at the ends of
   ~5-cell 1-wide kelp cul-de-sacs (entry only via `(28,0)←(28,1)←(28,2)` corridor).
2. **The space check cannot see it.** `nav_.flood` is time-aware: our neck cell frees
   after ~L−1 moves, so the flood "escapes" the pocket through the neck and
   `space >= need` — entry is legal. In reality the head can NEVER retreat through
   its neck: a 1-wide corridor is a one-way ratchet. `viaReverse` then "rescues" it
   (a reverse-split escape exists on paper), but the entered stub still dies at the
   dead end.
3. **Self-baiting.** Each dead dragon drops pearls in/around the pocket → the next
   forager comes for them → dies → drops more. A conveyor running ~1 death / 10 r.
4. **cf pays the same tax and wins anyway.** cf loses 8–48 dragons/game to the same
   pockets but eats ~300 pearls through them; at 20–25 units it out-produces the
   attrition ~4:1. Our swarm caps at ~5 — every conveyor death removes ~20% of the
   workforce, so the population never ignites.
5. Queen-side: our hiding queen lives to ~r300 (grows to len 31–39 on feeder deaths);
   cf's queen dies `hitWall` r52–72 every game.

## Fix (one change)

`swarmTrap`: non-queen dragons on `maze_` maps get the queen's `nav_.deadEnd` scan
(`seenOnly=false` — optimistic fog, only veto what is *proven* closed) and veto

    sc.exhausted && !sc.cycle && sc.cells <= trapSafeCells

i.e. a confirmed-small closed tree — a pocket the dragon only leaves by dying.
`wall = nb2 + ownExtra`, same as the queen's scan. Runs even when `viaReverse` holds:
the stub still dies in there. Fountain corridors survive (bigger regions / loops).
~20 lines + 1 param; BC_DEBUG off.

## Results (kmatch, seeds 3–5, both sides; gate maps weakhold, tower_defense, trauma,
arena, dilemma, default_small)

### score per map (wins/6)

| map | v109 vs cf | starve vs cf | Δ | v109 vs v104 | starve vs v104 | Δ |
|---|---|---|---|---|---|---|
| arena | 33.3% | 33.3% | 0 | 66.7% | 66.7% | 0 |
| default_small | 33.3% | 33.3% | 0 | 33.3% | 33.3% | 0 |
| dilemma | 100% | 100% | 0 | 100% | 100% | 0 |
| tower_defense | 50.0% | 33.3% | −16.7 | 33.3% | 33.3% | 0 |
| **weakhold** | **16.7%** | **33.3%** | **+16.7** | **66.7%** | **100%** | **+33.3** |
| trauma | 0% | 0% | 0 | 0% | 0% | 0 |
| **ALL** | **38.9%** | **38.9%** | **0** | **50.0%** | **55.6%** | **+5.6** |

### alive@499 (r500 games) and eaten60 (small-map pearls by r60), cand vs base

| run | alive@499 | eaten60 |
|---|---|---|
| v109 vs cf | 5.85 vs 13.6 | 25.1 vs 27.8 |
| starve vs cf | 7.18 vs 13.3 | 22.7 vs 27.8 |
| v109 vs v104 | 7.43 vs 5.29 | 22.3 vs 18.5 |
| starve vs v104 | 6.39 vs 4.31 | 19.3 vs 17.5 |

wall+self+body deaths/game: vs cf 13.7→11.7; vs v104 12.4→7.2.

Weakhold detail (`starve-fix-diag`, s3–5 vs cf): 33.3%; our pocket deaths ~1–2/game
(was 15–39); cf still pays 8–48. Two wins at r499 via hidden-queen survival.

## Honest assessment / caveats

- **Not a loss on the gate**: overall 38.9→38.9 (cf) and 50.0→55.6 (v104). Weakhold,
  the lane's target map, improves on both gates (+16.7 / +33.3). tower_defense dips
  one game vs cf — inside CI noise, worth re-checking if iterated.
- **Cost**: eaten60 −2–3. On weakhold our dragons now eat almost no pocket food
  (eats ~0–13/game in kept replays) — the map's beds are corridor-baited and we let
  them rot rather than feeding the conveyor. Wins come from attrition + hide-and-feed
  queen, not from matching cf's economy.
- If a future lane wants the pocket economy, the profitable play is a *timed*
  reverse-split harvest (enter with L≥4, eat, shed the child out before the dead end)
  or a unit-count-gated veto (feed the conveyor only when rich like cf does) — not a
  blanket veto. `swarmTrap` is intentionally conservative; a `swarmTrapUnits` threshold
  was considered but not shipped (one-change rule).
- trauma 0% and the tower_defense wobble are pre-existing/off-lane (v109 baselines
  identical).

Replays: `results/starve-fix-diag/replays` (post-fix), `results/starve-diag-v109/` +
`results/starve-dbg/` (pre-fix, BC_DEBUG). Analysis scripts: /tmp/starve/{pop,where,walls,regions}.py
(session-local; the mechanism + commands are reproduced above).
