# Top-team conveyor mechanics — exact numbers (autarky lane)

Data: 34 ladder replays, top-10-vs-top-10 (leaderboard 2026-10-03), 23 reaching
roundLimit (last_r ≥ 490). Pairings: SSS(91) × dev test 1 :P(545), chad gdp(70) ×
aAah(454), 𓎼𓃭𓅱𓂋𓇌(55) × Sponge(213) × forgot to mention(264), Cutlery(306),
fandagong(552). Replays: toptop_replays/. Analyzer: analysis/top_conveyor.py.
Distances = toroidal chebyshev to the winner's eventual-longest dragon's HEAD.

## 1) How the winner's longest dragon got long — two provenance modes

**(a) Spawn-lineage champ (16/22):** id0/id1 (queen or first worker) grows all
game. Trace shape: L@300 ≈ 3-21 → L@400 ≈ 12-68 → end 34-120 — ~60-75% of
final length arrives in the last 200 rounds (eaten_growth 27-113).

**(b) Late shed-all champ (6/22):** the eventual-longest is born at r452-490
as the shed tail of a near-total split — birthLen 28-53 while the parent
keeps len 2:

| map | champ | born | birthLen | parent keeps | eaten after |
|-----|-------|------|----------|--------------|-------------|
| Schooltime | id938 | r474 | 48 | 2 | +2 |
| weakhold | id301 | r456 | 28 | 2 | +1 |
| Islands | id1096 | r472 | 41 | 11 (the QUEEN shed) | +2 |
| Schooltime | id256 | r452 | 53 | 2 | +11 |
| Around UNSW | id1171 | r458 | 31 | 2 | +31 |
| Maze | id1168 | r490 | 44 | 2 | +6 |
| Schooltime | id383 | r481 | 12 | 2 | +7 |

A mechanism we do not have: the parent dives to len-2 and births a champ
carrying its whole body — instant re-concentration into a fresh, mobile id at
the bell. (Our cadence study: ~84-93% of everyone's resplits are keep-2/shed-2
stubs; top teams ALSO use keep-2/shed-all divestiture when consolidating.)

## 2) Feeder suicides — continuous churn, not a feed window

nva (noValidAction) deaths on the winner side:

- **Volume**: med 75/game, mean 172 (range 7-1065). Feeding never stops:
  first nva as early as r0-42 in churn-heavy games (Slithery 1065, Portals 462,
  Around UNSW 527), last at r495-499.
- **Not gated**: 30-60% of winner nva deaths happen before r350 — the feed
  isn't a scripted r360 event, it's ambient recycling all game.
- **Geometry** (winner nva deaths r300+, dist to champ head):

| band | share |
|------|-------|
| d=1 | 6% |
| d=2 | 17% |
| d=3-8 | 23% |
| d=9-12 | 16% |
| d=13-19 | 15% |
| d≥20 | 14% |

- The **d=2 spike (17%)** is the die-beside-head mechanism — same die-in-place
  our champFeedDist=2 implements. But the conveyor is broad: ~40% inside 8.
- **Capture is swarm-level, not point-to-champ**: for nva deaths within 12 —
  champ head reached a drop cell within 15r in ~10-70% (capByChamp), while ANY
  teammate reached one in ~60-95% (capByMate; Portals 318/340 mate vs 39/340
  champ; Trauma 59/67 vs 48/67). Drops are vacuumed by whoever is adjacent —
  the conveyor is "die inside the swarm", not "die at the champ's feet".
- Champ-grew-within-10r ~80-95% for within-12 deaths — proximity does convert.
- Losers show the same d=2 trick (r300+ med 2-3 when near) but their nva mass
  sits at d≥10 (med 9.5-16.5, n=372-975 diffuse starvation pools).

## 3) Champ roam vs plant + escorts

- **Champs ROAM — nobody plants.** Winner champs move ~1.0-1.3 cells/round,
  0-5% stationary, orbit radius (dist to own median position) 2-7 mid-game →
  3-9 in the bell era; 40-100 unique cells per 100 rounds. One bell-era
  outlier pair (Around UNSW/Schooltime 'born late' champs) orbited 14-18.
- **Escort cloud = feeder supply**: median teammates within cheb-3 of champ
  head is 2 (≤5: 5) in r300-399, collapsing to 0 (≤5: 1) at r400+ — the escorts
  die as feeders; the champ ends the game running through a thinning field.

## Diff vs our v424 (feedRadius 12 gate · die-at champFeedDist 2 ·
## heard≤30 · champOne · anchor plant at feedRound−40 ≈ r320 · feedRound 360)

| mechanism | top teams | v424 |
|-----------|-----------|------|
| feed timing | ambient churn r0→bell (first nva ~r0-42) | window-gated r360+ (midFeed pocket churn only on NC≥600, idle-only) |
| death geometry | die-at-2 spike (17%) + broad 3-12 funnel (39%) | die only at d≤2 of target |
| drop capture | SWARM vacuum — capByMate ≥ capByChamp usually | funnel to ONE champ head |
| champ mobility | roams ~1 cell/r, orbit 2-9, never still | PLANTS at champAnchor r320+ |
| concentration | late shed-all split births champ at r450-490 | none — champ persists as one id |
| feed radius | effective band ≤12 (matches) | feedRadius 12 (matches) |

## Mechanisms to port / hypotheses to test

1. **Champ should roam inside the donor cloud, not plant.** Their champs never
   sit still (0-5%) yet feeders still land med ~7. A plant is unnecessary when
   drops are vacuumed by the swarm — our anchor may be dead weight. Alternative
   read of our roam problem: our champ wanders ~19.5 from the swarm, theirs
   orbits ~2-9 INSIDE it. Port: replace anchor-plant with a mild pull toward
   the ally-density centroid (bounded roam), not a fixed pin.
2. **Ambient recycling > feed window.** Their churn runs all game — midFeed
   behavior should widen (drop the NC≥600 gate? lower the idleness bar), since
   even their dense maps recycle mid-game.
3. **Shed-all resplit = late concentration.** When a near-tied rival exists at
   r450+, splitting a long parent keeping len-2 mints a fresh champ carrying
   the whole body — cheap concentration with no funnel geometry required.
4. **The d≤2 die-in-place is confirmed real** (17% of their late nva deaths) —
   keep champFeedDist=2; the fix isn't the radius, it's champ-in-swarm.
5. Watch item: their ≥13 tail is still ~30% of late nva — even winners waste
   ~1/3 of suicides diffusely; our funnel's bar is their ≤12 share (~40-55%),
   not 90%.

## Caveats
- Winner = meta winner side; "champ" = that side's longest at last_r (for
  born-late ids the trace starts at birth).
- Capture = head enters a drop cell within 15r (pearl may have been taken by
  an enemy first — reachability proxy, not guaranteed pickup).
- Death cell = head snapshot at roundStart (sub-cell error).
- Loser-side nva med distances use games where loser survived to r300+.
