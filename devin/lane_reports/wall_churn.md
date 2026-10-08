# Wall-churn forensics — the bed-cycle conveyor (explore lane)

Trigger: `replays/v134b/m1443064.replay` (Autarky, Z-A). Winner B: 247 hitWall / 258 deaths,
256 splits, 601 eaten, ends queenEnd=52 vs our 31. Hypothesis under test: top bots suicide
units on walls near the champ as a drop-recycling conveyor. **Verdict: conveyor confirmed,
but the drop is a BED RESPAWN, not corpse pearls — bodies drop nothing.**

## 1. The mechanism, replay-verified (m1443064, winner side B)

Every one of the 247 hitWall deaths fits the exact same 4-step production line:

| Step | Evidence |
|---|---|
| split a fresh bud | **247/247 budded within 5r of death** — champ churns ~1 bud per 2 rounds all game |
| bud walks onto an empty bed cell | all 247 corpse cells are prior-bed tiles (0 fresh); the cell's pearl was consumed ~2r before death |
| bud suicides (hitWall) | all dead units are **len exactly 2.0** — they ate nothing, they are single-use |
| bed respawns, champ eats | pearl regrows at **death+4r in 243/247**; a teammate eats it in **242/247** — eater median len **18** = the champ |

The champ is an anchored feed station sitting on a bed cluster; buds are peeled off it,
each serves exactly one bed-cycle adjacent to the champ, then dies into a wall. The
"conveyor" runs at a constant ~50 deaths/100r from round ~30 to 499 — it is the main
economy, not a phase. Result: champ farms regrown pearls without moving → queenEnd 52,
longest 52, while we hold queenEnd 31.

**Deaths are not the drop — the vacancy is.** Cross-check on our own v131 losses:
corpse cells that never held a pearl regrow one in only 2.7% of cases; bodies donate
nothing. What the bud's death buys is (a) guaranteed vacancy of the bed cell at a precise
time and (b) unit turnover — a spent bud exits the unit economy instantly instead of
congesting the station. Whether occupancy actually pauses the respawn timer or the bud
is just cleanup, the operational fact stands: **the pearl income comes from beds being
eaten-and-regrown on a ~4-6r cadence by a dragon that never leaves.**

## 2. Generalization — 234 top-10 replays (aAah/FtM/chad/55/545/larp/Cultery/horse/87/SSS)

Strict cycle detector (bud ≤5r before death, len ≤4, died on a bed, regain ≤+4r, eaten ≤+3r):

| | sides with ≥15 hitWall | hitWall deaths | conveyor-verified |
|---|---|---|---|
| roundLimit winners | 20 | 2694 | **483 (~24 cycles/side-game)** |
| roundLimit losers | 25 | 3410 | 203 |

Losers actually die MORE by hitWall (3410) but almost none of it is the cycle — their wall
deaths are congestion/attrition. The verified cycle is a **winner signature**: ~24
conveyor deliveries per winning side, near zero in losses. (Undercount likely — strict
filters; the m1443064 exemplar scored 242/247.)

## 3. The gap vs our conveyor (abyss_v447 read; v449 not pushed yet)

| | Theirs (verified) | Ours (v447 `policy.hpp`) |
|---|---|---|
| champ position | **anchored ON a bed cluster** from ~r30 | plants wherever `regionReach ≥ 12` at `feedRound−champPlantLead` (r360) |
| feeder source | fresh len-2 buds split beside the champ | any short worker within `feedRadius=12` *walks* to the champ |
| delivery | bud dies ON the empty bed; champ eats the **bed respawn** | feeder dies by nva illegal-split (`"chfeed"`) beside the champ's head, "the body drops" |
| what dies | exactly len-2, one bed-cycle lifetime ~4r | len ≤ feedMaxLen, walks up to 12 cells of gauntlet |
| cadence | ~50 cycles/100r, all game | `midFeedRound=100` centroid recycle + `feedRound=400` window |

**Mechanism gap, concretely:**

1. **Our delivery is physically wrong.** `chfeed` nva-deaths dump the body beside the
   champ's head expecting a drop — but bodies drop no pearls (2.7% on never-bed cells,
   and those are unobserved-bed artifacts). Unless the feeder dies ON a bed, our whole
   `chfeed`/`feedFallback`/midFeed-conveyor donates **zero length**. The donation code
   is a corpse-feed model in an engine that has bed-respawn, not corpse-drops.
2. **Our champ anchors blind.** `regionReach ≥ 12` doesn't select for beds — the whole
   point of planting is to sit on 3-5 bed tiles and farm respawns. Their champ's income
   is bed-cycling; ours is waiting for corpses that never arrive.
3. **Our feeders walk.** `feedRadius=12` sends workers across contested space to die;
   their feeder is born 2 cells from its death cell. Their design has no gauntlet by
   construction — it also explains why their feed fires r0-499 at constant rate while
   ours is a 360-499 window that stalls on stale anchors.
4. **Unit turnover.** Their swarm stays lean because every bud is single-use (die after
   one cycle); ours accumulates feed-bound walkers. This is ALSO the "late-swarm
   drawdown" signature — the bed-cycle IS the funnel mechanic: one dragon eats, everyone
   else is disposable throughput.

## 4. Counter-build sketch (for integrator)

Replace "walk to champ and die beside it" with "champ plants on densest bed cluster
(≥3 beds within ~4 cells); local buds: land on an empty bed cell → suicide (hitWall
works, nva-split works) → champ eats the +4r regrow". The feeders never leave the
station radius; the champ never moves; the whole loop is local so it can't feed-window
h2h. If any variant tries this, the acceptance metric is simple: count bud-deaths whose
empty bed cell regrows and is champ-eaten — the verified cycle signature above.
