# pocket lane — weakhold pocket-starvation

## Verdict: SHIP candidate `abyss_pocket` (branch devin/pocket)

vs abyss_combat on weakhold — the actual #1 loss signature — **4/8 (1W/2S/1L
pairs), up from v119's 0/8.** cand-A reached alive 15–21 at r499 where v119
flatlined to 1 alive vs 27; cand-B won one outright. vs v119 pair-set:
weakhold 0W/4S/0L, dilemma 0W/4S/0L, stripes 1W/3S/0L — **zero pair losses on
all three mission maps** (arena+devil sanity: 43.8%, 1 pair-loss on devil s4;
devil is spawn-side-locked — v119 self-play is the identical A-sweep/B-lose
signature, ours flipped one thin A-side seed).

## S0 diagnosis (confirmed, with evidence)

**weakhold flatline is a bait-pocket woodchipper, not fog-starvation.**

- ~24–33 dragons/side/game die `hitWall` at ONE cell each — A: (15,14),
  B: (24,0): 1-exit appendage beds (open-degree 1) down 1-wide corridors.
- weakhold's food engine is concentrated bait: the cd=1 beds live inside the
  pockets. In v119 self-play, 93/98 of side-A pearls came from its own trap
  cells; each eat respawns a pearl that pulls the next newborn in. Babies
  (len 2–3) enter head-first, exit is through their own neck → `hitWall` ~9
  rounds later. `viaReverse` needs len>=4.
- Combat eats 433 pearls across ~30 cells (field beds cd=100–500), never camps
  bait. We eat only our own bait pocket → feed the woodchipper, never roam.
- Residual symptom after trap fix: *safe-paralysis* — workers froze in 2×2
  orbits at corridor mouths, all dirs scored 1–7, nearest belief 14+ steps out,
  per-tile explore pull ~0.001 at that range.

## Mechanism (abyss_pocket = v119 + 3 gated changes, all worker-scoped)

1. **Worker deadEnd scan at k==0** (`workerScan`, was queen-only): wedge is a
   first-step blunder. Exception `baitEat`: a *starving* worker may still take
   the informed suicide-eat (enter, bank the pearls, wedge-die) — cheap suicide
   out-values orbiting a food desert in v119's swarm economy.
2. **Bait exclusion** (`baitLen=4`): a bed with 3 seen-blocked edges isn't food
   for len<4 unless starving; kills the belief anchor at the pocket lip.
3. **Fog approach** (`wFogPull=6 · fp(ndu)`, `fp` = long-range discount 0.93^k):
   pull toward the *nearest* unseen tile by BFS distance (routes through fog,
   not walls; count is flat, manhattan was the failed integrator approach).
   `wPersist=0.5` heading hysteresis while starving stops mouth-orbitting;
   `wFrontier=0.004 · nu` unseen-reach preference.
   Gate: `worker_ && starving_ && (anyBait_ || round>=60)`. `anyBait_` (a
   3-wall cell in targets_) is the load-bearing guard: on no-bait maps the
   whole block is off and behavior is exactly v119 — that is what keeps
   dilemma's knife-edge queen lane (any early worker perturbation = r47 flip)
   clean at 4W/4L.

## Results matrix (A/B, same seeds both seats)

| run | cand | base | map | score | pairs W/S/L |
|-----|------|------|-----|-------|-------------|
| pocketrepro | v119 | combat | weakhold | 0/8 | 0/0/4 — the signature |
| pvc2 | pocket | combat | weakhold | **4/8** | 1/2/1 — flatline broken |
| pocket21 | pocket | v119 | weakhold | 50% | 0/4/0 — alive A 17–26 vs B 3 |
| pdil13 | pocket | v119 | dilemma | 50% | 0/4/0 — clean seat-lock |
| pstr3 | pocket | v119 | stripes | 62.5% | 1/3/0 |
| pgen | pocket | v119 | arena+devil | 43.8% | 0/7/1 — devil s4 flip |
| devbase | v119 | v119 | devil | 50% | 0/4/0 — same seat-lock |

Explored and REJECTED (seat-flip whack-a-mole — every interior/frontier pull
variant that helped one weakhold side broke the other or flipped dilemma):
frontier-masked pulls (≥2 seen-open neighbors), baitOpt_ pull suppression,
foodNow_/poorFood_ escort release, age-clock starvation (Policy is rebuilt per
turn — member state can't persist). These stay in git history on devin/pocket.

Residual risks: `hitSelf` deaths ~50/game (bigger swarm, corridor pileups);
the two pvc2 losses and devil s4 are queen-death endings — that is module 5b's
signature, not a navigation defect.

## 5b queen-safety module — findings (partial, folded into this branch)

Replay forensics on pvc2 s3-A (queen r222): a **lone len-3 ram sprinted W 2 tiles
and died head-to-head with her** — both died at adjacent heads, nearest ally ~5
tiles. Exact 5b signature. Two real defects found in v119's ram screen
(`queen_ && !lead_`, policy.hpp):

1. head-to-head kills at ADJACENCY — the screen's `reachOf(v)=freeSteps+v-2`
   is one short of the lead-branch's `+v-1`, and the kill actually lands
   *beside* her head.
2. `e.dist` is BFS over `ownBlk` — her own body blocks the field, so rams
   attacking along her body line read INF and score "safe".

Shipped: `qRamAdj=1` + min-dist over dest's 4 neighbors, **gated to weakhold
dims (W40×H15)** — the map where the hole demonstrably killed her. pvc4/pvc6 =
4/8 vs combat (queen survived the r222 pattern; the remaining s3 loss is a
late-game swarm collapse — 7 enemies inside cheb 4, not interceptable).

REJECTED (all hurt econ or flip seats):
- `qEscortHeard` (idle workers converge on her role-2 beacon ≤14 tiles): weakhold
  s3-A pair-loss — escort pull drains forage.
- `wQueenAlone` (queen drifts toward allies when none within 3): POISON — pulls
  the hiding queen toward the swarm = into fights; mirror-flipped BOTH seats on
  weakhold+dilemma (B swept, A collapsed 11 vs 59 eaten).
- adjacency screen ungated or gated on `anyBait_`: stripes s4-B pair-loss +
  arena/stripes regressions (37.5%). The wider fear net is only safe where the
  geometry hole was proven.

Escort side of 5b NOT shipped — converging workers on a hidden queen keeps
costing econ; the right form probably wants escorts to form only once an enemy
is *near* the queen's reported cell, not continuously.

## v150 = abyss_v149 + channelling feed merge (gate-runner task)

Merged v143feed's three pieces onto the v149 base (v143+C4+champ-plant+fallback330):
champSeen_ live-head targeting, die-in-place SPLIT-0 (noValidAction), fresh gate
feedAge_<=feedHeardDie(2) || champSeen_. champChannelDist=1 replaces champFeedDist
for champOne feeders; champMinLen kept at 0 (documented rejection). wChampHold NOT
ported — champAnchor_ is the same idea done right (planted hover, not parked roam).
C4 corridor veto + c.terminal early-outs untouched.

Gate vs abyss_v149 — autarky,stronghold,default,unsw,islands x2 seeds both seats (20g):
- win%: 45.0% ALL (1W/7S/2L); autarky/default/unsw 0/2/0 pairs, islands 1/0/1,
  stronghold 0/1/1 (s1 double-loss, s2 split). CI [25.8,65.8] — noise band.
- longest@end (r500 n=17): 26.5 vs 31.7 — delta driven by 2-3 monster games on
  base side (54,48,39,37 vs cand max 41); per-map medians much closer. unsw cand
  actually ahead (28.75 vs 27.0).
- Feed capture (channel.py, 20 r>=320 games, seat-corrected): chfeed fires as
  designed — 22.2 noValidAction/game ALL SPLIT-0 verified vs base 0.1. Feed
  deaths 45.6 at 23% adj vs base 47.6 at 18% adj — die-in-place is the MORE
  accurate drop mechanism. leadShare 8.2 vs 9.2 (no conversion gain), l450 19.4
  vs 24.8.
- Queen deaths 0.700=0.700; wall+self+body deaths 107 vs 132 (the ~25 shifted
  into noValidAction = the chfeed volume). No r0-5 queen kills either side.
- Map-shape finding: unsw/islands show 50-63 deliberate SPLIT-0/game at 3-10%
  adjacency — those games keep the QUEEN as champion (roams, never plants):
  feeders die beside a <=2-round-stale reported head. Same stale-target waste
  v149 has there, just with a different death type. The plant only covers
  worker-champs; queen-champ targeting is the shared gap.

VERDICT: mechanisms are compatible — die-in-place out-precisions the neck-step
(23% vs 18%) and scores within noise (45%±20); no evidence it helps or hurts
the monster-champ upside at n=20. If a ship/die call needs power, run a bigger
board; if longest@end is the gate metric, the signal is slightly negative but
inside per-map variance.

### scoring-reframe addendum (2026-10-04): bells score LEXICOGRAPHICALLY

Integrator's discovery, verified 17/17 on the v150 games.jsonl: queen-alive ->
queen end-length -> longest -> total. This changes two v150 reads:
- stronghold s1-B loss is NOT noise — it is the qlen signature: our queen ended
  len-10 while a planted worker-champ grew to 36; their fed queen ended 31 and
  won the first tiebreak outright. Feed-the-worker is score-blind whenever both
  queens live; feed-the-queen is the primary key. The election's sealed-queen
  exemption (queenReach<20 -> queenReady=false) therefore costs BELLS, not just
  feed — a marginally-reachable queen who could still eat should probably keep
  the feed ahead of a worker-champ fallback.
- autarky s1-A win (queen 3 vs dead, longest 31 vs 54) is the dead-queen
  autolose — escort/hunt work is directly on-score.
