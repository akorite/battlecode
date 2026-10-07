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

## v149q — queen-survival module on v149 (evasion + threat escort + leash): REJECTED 41.7%

Spec (integrator, resuming task): (a) queen evasion — step away when an enemy
head enters vision with no ally between, (b) escort 2-3 tiles out on her front
arc, (c) keep her near start r<100. Built on synced abyss_v149 (devin/v120 HEAD,
champAnchor in World):

- Evasion veto tier: dest inside `freeSteps(ev)+ev-1` of a seen enemy →
  `wQueenVeto(500)*newL*mult − dd` (near-veto, keeps escape gradient);
  `qEnemyLenMin=3` floor in BOTH the queen screen and the lead screen
  (edge-seen len under-read — visible counts segments).
- Threat escort with front-arc post: escortOf_=queenCell_ (seen else freshest
  role-2 beacon), qThreat_ = enemy (seen or heard) within qEscortThreat=8 cheb,
  volunteers within qEscortDist=14 + swarmRank<escortCount; arc pull wQueenArc=0.8
  toward the cheb-2..3 ring cell nearest the threat.
- Leash: wQueenLeash=1.0 overshoot penalty past leashDist=10 of startCell,
  r<leashUntil=100, gated NC<=2000 && portalEnds.empty() (lifts on portal
  sighting — the band-8 version fought scripted portal walks and regressed qOS).

GATE abyss_v149q vs abyss_v149, tag q149, weakhold/stronghold/autarky/
queen_of_spades/dilemma/arena ×2 seeds both seats (24g):
- Score 41.7% (0W/10S/2L), CI [24.5,61.2]; pair losses arena + stronghold,
  pair splits everywhere else.
- QUEEN METRICS MOVED WRONG WAY: queen-dead 0.667 vs 0.542, queen-alive@end
  0.455 vs 0.636, qlen@end 4.9 vs 9.6, queen non-ram deaths 0.125 vs 0.042.
- Small-map pearls-eaten@r60 33.3 vs 40.9 — the queen starves. This is the
  same signature both prior leash rejections showed (v135 band-8: qOS 0/2/2 +
  stripes; the starvation is strongest on small maps where she must range to
  eat). Band-10 + portal-lift did NOT fix it — third rejection; the comfort
  zone is not a radius constraint, it's wherever food is.
- Cannot cleanly attribute the 3 adds among themselves (no per-piece ablation
  run); the leash is the overwhelming suspect by signature. Evasion veto and
  front-arc escort individually verified-good on v135 bases (qOS r32 dodge,
  escort 5/8 weakhold) — the bundle regression pattern is leash's.

VERDICT: dead on arrival as a bundle; spec superseded by v153 anyway (anchor +
threat-escort + die-in-place, no leash). The escort/arc block ports to v153
unchanged; leash rejected 3x — do not retry without a food-aware trigger.

## v153 — queen-champ anchor + threat-conditional escort + die-in-place (IN PROGRESS)

Spec (integrator): queen-champ plant (she anchors when champIsQueen_ at
feedRound-champPlantLead, roomy pivot >=12, hover ~1-2 cells) + threat-
conditional escort (guard post 2-3 on her front arc, ONLY while an enemy head
is within ~8 of her reported cell) + keep die-in-place feed convergence.

BUILD: abyss_v153 = v149 + World::queenAnchor latch (queen-only set/clear) +
wQueenAnchor=3.0 pull + threat escort (qEscortThreat=8, qEscortDist=14,
qArcDist=3 front-arc cell, wQueenArc=0.8) + v150's die-in-place feed
(champSeen_ live-head, champChannelDist=1, SPLIT-0 -> noValidAction,
feedAge_<=feedHeardDie(2)||champSeen_). No leash (3x-rejected), no evasion-veto
bundle (kept base ram screen for clean attribution of spec items).

GATE-1 (shared-latch version, tag v153): abyss_v153 vs abyss_v149,
unsw/islands/stronghold/autarky/default x2 both seats (20g):
- 65.0% (4W/5S/1L) CI [43.3,81.9]; islands 4/4 (the queen-champ pathology),
  autarky 3/4, unsw 1W/0S/1L, stronghold+default splits.
- qlen@end 2.875 vs 2.125 UP; queen-dead 0.750 vs 0.800 DOWN; longest@end
  29.6 vs 32.4 DOWN (stronghold s2-B 28-vs-58 monster outlier); wall+self+body
  deaths 108 vs 130 (stale-target feed waste converted away).
- Channel (cand vs base side, seat-corrected): noaDie cand 18-113/g vs base 0
  (v149 neck-steps, no SPLIT-0); adjacency default 49%, stronghold 71%,
  unsw 32%, islands 9%, autarky 2%.
- ANCHOR POST-MORTEM: the queen never planted. unsw/islands queens die
  r205-345 — before the r360 window. autarky s1 queen lived to 499 but post-360
  span 29 (roamed): the shared w_.champAnchor latch is wiped by every
  non-planter decide, so she re-locked at her DRIFTED head each turn — the
  v149a deceleration-pull failure, reproduced on the queen. Worker-champs pin
  anyway (their post-feed pulls are weak; the drops are their food), the
  queen's forage targets outbid the 1.2 pull.
- FIX (v153b): dedicated World::queenAnchor — set/cleared by the queen's own
  decide only, locks ONCE at the first roomy cell in-window, wQueenAnchor=3.0
  (beats forage). Re-gating same 20g.

GATE-2 (locked-pivot version, tag v153b): same 20g —
- 50.0% (3W/4S/3L) CI [29.9,70.1]. unsw 0/4 = TWO pair losses (gate-1 was
  1W/0S/1L); islands 3/4 (was 4/4); stronghold 1W/0S/1L (was split).
- qlen@end 2.444 vs 2.778 — FLIPPED negative; queen-dead 0.750 = 0.750;
  longest@end 31.6 vs 32.4 still down; feed-waste reduction held (108 vs 135).
- READ: a pinned r360+ queen starves where she must range to keep eating —
  unsw is the harshest case (0/4). The anchor is REJECTED on mechanism
  evidence: fixed pivot converts a roaming champ into a starving one; the
  drops are not enough local food. Worker-champ pin works because its whole
  job is hoovering drops; the queen has a forage/survival scoring layer.
- STRIPPED: anchor block + pull removed. abyss_v153 = v149 + threat escort +
  die-in-place only. Re-gating same 20g as v153c to confirm the ~65% was the
  escort+feed pair and not the (weak) anchor pull.

GATE-3 (stripped — escort + die-in-place ONLY, tag v153c): same 20g —
- 40.0% (1W/6S/3L) CI [21.9,61.3]. unsw 0/4 again; islands 3/4; stronghold 1/4;
  autarky 2/4. qlen@end 3.389 vs 3.222 (≈flat); queen-dead 0.75 vs 0.80;
  longest@end 30.7 vs 32.6.

THREE-GATE ORDERING (identical 20g protocol, same seeds both seats):
  weak latch hover (v153)   65%  4W/5S/1L  qlen@end 2.9 vs 2.1  islands 4/4
  locked pivot      (v153b) 50%  3W/4S/3L  qlen@end 2.4 vs 2.8  islands 3/4
  no localization   (v153c) 40%  1W/6S/3L  qlen@end 3.4 vs 3.2  islands 3/4

The "deceleration pull" is not a bug to fix — it is the mechanism. The queen
re-locks the shared champAnchor at her own head each decide (every non-planter
wipes it, so it never holds a real pivot); the resulting 1.2 pull toward where
she IS slows her enough that relayed positions stay convergent for die-in-place
drops, while she still ranges to eat. Harder (locked pivot at w3.0) starves
her; nothing lets her outrun her own relays. unsw: she dies pre-window in
every build (queen-dead ~0.75 there) — the s2 flip gate-1->later is the only
map whose result moved, consistent with the localization being active.

FINAL BUILD: restored the gate-1 block verbatim (byte-identical semantics —
only comments differ; kvmrun replays are deterministic, so its 65%/4W/5S/1L
holds; world.hpp identical to v149). abyss_v153 =
  abyss_v149 + queen soft-localization via shared champAnchor latch (above)
            + threat-conditional escort (enemy head within 8 of her reported
              cell -> worker takes the front-arc post 2-3 out, qArcDist=3,
              wQueenArc=0.8, swarmRank<escortCount, qEscortDist<=14 volunteer)
            + v150 die-in-place feed (champSeen_ live head, champChannelDist=1,
              SPLIT-0 noValidAction die, feedAge_<=2 || champSeen_).
Spec metrics on the shipped build (gate-1): qlen@end 2.875 vs 2.125 UP,
queen-dead 0.750 vs 0.800 DOWN, longest@end 29.6 vs 32.4 DOWN (stronghold
s2-B 28-vs-58 monster outlier; medians closer). VERDICT: SHIP escort +
localization + die-in-place; REJECT locked queen pivot; leash stays 3x-rejected.

== v153c7 — C7 sealed-queen (autarky spec), on abyss_v153 ==

SPEC: queenSealed(queenCell, queenLen) replaces `queenReach() < 20` in
locateChamp. Map-walls-only flood, foreign bodies treated open (b.nb is the
static graph so bodies are open by construction). Three clauses:
(a) head-degree bound — openNb <= 2 at her cell => sealed;
(b) pocket-capacity bound — flood capped at qlen + queenSealSlack(8), region
    <= cap => sealed (early exit as soon as q.size() > cap);
(c) else unsealed. Unknown cell (cell<0) => NOT sealed (election wants evidence).

Site changes vs v153 (only two call points):
- locateChamp: queenReady && queenSealed(w_.queenCell, w_.queenLen) => unready
  (was queenReach() < 20 — a raw region-size <20 test at the reported cell).
- queen soft-anchor gate: `!queenSealed(w_.head, L_)` replaces `queenReach() >= 20`
  — same eligibility question, evaluated at her live head; an elected-but-sealed
  queen keeps roaming instead of anchoring (the latch is still the WEAK chase-
  the-head hover from v153, do not re-lock it).
queenReach() left defined (unused now).

GATE (v153c7-g1): cand=v153c7 vs base=v153, unsw/islands/stronghold/autarky/
default x2 seeds both seats, 20g — isolates C7 against the shipped build.

Score: 55.0% (1W/9S/0L), CI [34.2,74.2]; pairs [50,65]. stronghold the only
non-split map: 1W/1S/0L (s1 cand won both seats). Zero pair losses.

Metrics cand vs base: longest@end 27.6 vs 26.4 UP (spec: not down);
queen-dead 0.700 vs 0.750 DOWN; qlen@end 2.0 = 2.0 (unchanged — she still
dies pre-window on the heavy maps); alive@r499 13.7 vs 14.0;
h2h deaths 62.9 = 62.9 literally identical; all blitz metrics to 3 decimals.

VERDICT: parity-or-better, ship-safe. C7 doesn't move the score on this fixture
because the two tests overlap in effect where it matters: reach<20 sealed a
<20-cell room; C7 seals <=2-exit heads (missed by reach) and rooms <= qlen+8
(len2->10, len5->13, len10->18 — comparable magnitudes). The boundary shifted,
the volume didn't. Real value is correctness, not score: a head-pinched queen
(openNb 2 in a big open room) now reads sealed — reach saw the room, not the
pinch — and a len-12 queen in a 19-cell room now reads unsealed instead of
excluded. Election changes are rare because most fixture queens die r205-345,
before the r360 anchor window where the test gates.

== Ladder diagnostics — vs 1750-2000 band (last-60 window) ==

15 games found: okbro(id 22) 1-4, 1234(id 919) 2-3, DeepSeek-V4.1-Flash(id 776) 1-4.
Our queen died in 11/15; EVERY loss includes her death; 3/4 wins she survived
(4th = mutual death, won longest 33v29 vs 1234 unsw). The 1750-band reads are
below — queen lens at r50/200/400 and death mechanism per game.

CLASS 1 — QUEEN SELF-KILL -> dead-queen auto-loss (6/11 losses, THE LEAK)
  m1098357 unsw    okbro    hitWall      r204  qE 0/33  lg 32/41 a499 7/32
  m1098353 autarky okbro    hitSelf      r291  qE 0/26  lg 47/26 <- won longest, lost bell
  m1098354 maze    okbro    hitSelf      r195  qE 0/50  lg 35/50 a499 6/20
  m1093774 maze    DeepSeek hitWall      r198  qE 0/30  lg 38/30 <- won longest, lost bell
  m1096032 austral 1234     hitOtherBody r494  qE 0/0   lg 27/28 <- self-kill 5 rounds before bells, lost longest by ONE
  m1096034 stripes 1234     hitOtherBody r68 -> teamEliminated (a2 vs a5 @r50)
  hitWall x2, hitSelf x2, hitOtherBody x2. In 3 games our longest was equal or
  better — the self-kill alone forfeited the first key. v138 owns the self-kill
  items (exit-reservation, <=2-exit veto) — confirm coverage for r195-291
  mid-game deaths, not just the early cases; r494 hitOtherBody is a
  bells-eve suicide that flipped a won game.

CLASS 2 — EARLY SWARM DEFICIT -> queen ram -> elim (5/11)
  m1098355 trophy  okbro    h2h r142 -> elim   a3 vs a8  @r50
  m1096035 trophy  1234     h2h r49  -> elim   a4 vs a14 @r50
  m1093775 devil   DeepSeek h2h r70  -> elim   a5 vs a21 @r50
  m1093777 austral DeepSeek h2h r150          -> both dead -> lg 22/27
                     (we led a64 vs a35 @r200 — swarm didn't matter, queen did)
  m1093778 default DeepSeek h2h r203          -> lg 15/26
  On elim maps we field 2-5 dragons at r50 vs their 5-21. The killer profile
  matches steering-4 (mover, len small, no ally near). NOTE: qRamAdj is gated
  W==40&&H==15 (weakhold dims) — the adjacency screen is OFF on trophy/devil/
  stripes/australia where these rams land. Coverage gap is concrete.

CLASS 3 — QUEEN-FEED DEFICIT (contributing, not primary)
  okbro queen trajectory: q3@r50 -> q5-6@r200 -> q26-50@end (the FtM recipe —
  len~2 till r200 then fed to 26+). Our queens die before the r360 feed window.
  DeepSeek wins with WORKER swarms (queens die early both sides: qE 0/0 in
  3 of 4 losses — they out-attrit us after mutual queen death).
  1234 wins by early swarm mass (a14-21 @r50), queens irrelevant.

Net: we lose the band not on econ (we out-swarm mid-game: unsw a64v35,
austral a64v35 @r200) but on the FIRST lexicographic key. Fix order by
measured cost: (1) queen self-kill coverage for r195-494 deaths = ~55% of
losses, (2) early-split economy on blitz maps = ~45%, (3) feed timing only
matters once (1) and (2) stop pre-empting it.

UNRANKED diagnostic challenges fired (never ranked): vs okbro battles
1098973-76, vs DeepSeek 1098977-80, vs 1234 1099009/10/16/17 (first post
502'd, retried clean). Replays pending ladder run.

CHALLENGE SET (12 unranked diagnostics, current live build): 3-9
  okbro 1-3, DeepSeek 2-2, 1234 1-3. Replays in ladder_replays/.

  LOST  PrisDil    okbro    h2h r446 -> elim        qE 0/14
  LOST  Autarky    okbro    h2h r257   qE 0/15  lg 47/20 <- won longest AGAIN
  LOST  Schooltime okbro    BOTH ALIVE qE 3/3   lg 3/33 <- only non-queen-death loss
  LOST  Stripes    DeepSeek h2h r173   qE 0/10
  LOST  Trauma     DeepSeek h2h r393   qE 0/20
  LOST  Trauma     1234     h2h r349   both dead -> lg 15/19
  LOST  TowerDef   1234     h2h r132 -> elim
  LOST  Australia  1234     h2h r170   both dead -> lg 26/36
  WON   PrisDil    okbro    qE 6/0 (queen alive)
  WON   Stripes    DeepSeek elim (our queen hitSelf r184 late, wiped them first)
  WON   Default    DeepSeek both dead -> lg 16/13
  WON   weakhold   1234     qE 7/0 (queen alive — the mission map converts)

COMBINED (27 games, 20 losses): queen died in 19/20 losses; the ONLY loss with
our queen alive at bells was Schooltime's champ rout (a499 1v30, lg 3v33).
Ram h2h dominates fresh data 8/9; self-kill count ZERO in the 12 fresh games
vs 6 in the older window — consistent with v138's self-kill protections now
being live (verify: live build version between the two windows). Remaining
leak is ~100% RAM, and it lands on trophy/devil/stripes/australia/trauma/
prisdil where qRamAdj's W40xH15 gate does NOT cover — the escort/kill-veto
module (devin/queen, currently weakhold-gated) is the missing coverage.
Autarky flipped twice on 'won longest lost bell' (lg 47 vs live qE 15/26) —
feeding worker-champs while our queen dies is structurally wrong under
lexicographic scoring; queen survival must outrank worker feed.

== abyss_qshrink — room-shrink trajectory (queen self-kill mechanism), on v168 ==

SPEC: track her reachable-region size each decide (BFS from head, walls +
foreign bodies block, own body open); on shrink (>30% vs 5 rounds ago, or 3
rounds running) AND below threshold -> relocate pull toward the deepest cell
of the largest exit subtree (head-neighbour root with most cells). Queen-only,
p_.qShrinkOn flag, history ring in World (Policy rebuilt per turn).

TWO GATES vs abyss_v168, weakhold,devil,trophy,stripes,australia,autarky,maze
x2 seeds both seats (28g each):

qshrink-g1 (trajectory arms only):    50.0% (0W/14S/0L)  every map split
qshrink-g2 (+ lostRoom drift-in arm): 50.0% (0W/14S/0L)  identical

Metrics cand vs base (g2): queen-dead 0.893 vs 0.929; non-ram (self-kill class)
0.321 vs 0.286 UP slightly; alive@r499 12.9 vs 13.6; all blitz metrics identical
to 3 decimals (swarm untouched — the pull never perturbs workers, correct-by-
construction).

VERDICT: REJECT — inert on this fixture in both arms. Root-cause read: the
self-kill class is only ~0.3 of a 0.9/game queen-death rate locally; the
fixture's queen deaths are mostly h2h rams + elims where the region-shrink
window either never existed (spawned into flat-low pockets: hmax8 arm added
for exactly this, still silent) or the shrink happens inside the kill round
itself (body-seals in <3 rounds — trajectory has no gradient to ride). The
1750-band cornering pathology (queen self-kill r195-494) lives in games vs
bots that block corridors with bodies; self-play mirrors don't produce it.
Caveat: no per-decide trigger instrumentation — can't separate 'fired and
failed' from 'never fired', but two identical 50% mirrors bound the effect
to ~0 either way. Params parked: qShrinkOn=1, qShrinkMin=48, qShrinkDrop=0.30,
wQShrink=2.5 in abyss_qshrink/common.hpp if a different trigger (e.g. enemy-
body-frontier proximity rather than region-size trajectory) is wanted later.

== Top-team corridor replay study (teams 952/70/501/226 + ours) ==

39 corridor replays (maze/trauma/stripes/weakhold/portals/slithery) via
ladder.py + tooling/pocket_metric.py (new: per-cell walls-only region size;
pocket = region<40 cells; measures turns/eats/deaths by pocket band).
OURS = 15 ladder + 12 challenge + 40 self-play corridor replays.

ANSWER 1 — do they forage dead-end pockets? YES, MORE than us.
  pocket-turns:  cheji 6.4% | Knight 3.3% | Cache 2.4% | Quaker 0.9% | OURS 1.0-1.1%
  pocket intake: cheji 209/1058 (19.8% of all eaten!) | Knight 223/2535 (8.8%)
                 Cache 52/368 (14.3%) | Quaker 35/1295 (2.7%) | OURS 14.5/600 (2.4%)
  Pocket forage is FOOD INCOME. v180's premise inverted — blocking pocket
  forage cut intake, hence 41.7%. The defect was never pocket ENTRY, it is
  that some of ours can't get OUT (see wall deaths).

ANSWER 2 — wall-death rates (the real diff):
  cheji + Cache: ZERO hitWall. Not low — zero, across 19 replays, ~400 deaths.
  Quaker 191.8/game (41%), Knight 522.5/game (58%) — wall deaths don't
  disqualify when the econ runs hot, but the zero-wall cohort shows a perfect
  wall discipline is achievable on the same maps.
  OURS: 26.5 wall/game vs 1700s (18%), 15.2 self-play — we choose wall moves
  as cornered least-bad ~10-27x/game. Pocket-wall subset is small (~0.7/g) —
  our walls are corridor-open, not pocket-wedge.

ANSWER 3 — where they send workers: everywhere, with a churn economy.
  deaths/game: Knight 902.8 | Quaker 462.5 | cheji 263.5 | Cache 144 | OURS 60-148
  eaten/game:  Knight 2535   | Quaker 1295   | cheji 1058  | Cache 368 | OURS 224-600
  Top teams run 3-6x our death volume — turnover IS the corridor engine.
  Death-mix flip: cheji 81.5% noValidAction + Cache 62% hitSelf = deliberate
  feeding-kills (die-in-place at ~10-25x our rate: their pkDeaths 74/game in
  pockets are nva/h2h feed-drops, never wedge). OURS: h2h 42-54% of deaths —
  we die FIGHTING, they die FEEDING.

BEHAVIORAL DELTAS to clone (ranked by measured gap):
  1. die-in-place feed volume: cheji ~215 nva/game, ours ~8 — the champ-feed
     channel is real but running at ~4% of their rate. (v150 merge showed the
     mechanism works; volume is the gap — feed earlier/more of the swarm.)
  2. wall-move discipline: cheji/Cache never produce a wall move. Ours leak
     ~18% of deaths to least-bad wall picks — cornered-eval needs a non-
     suicidal least-bad (idle/suicide-to-feed beats hitWall if it's dying anyway:
     a wall death drops ceil(L/2) pearls where it stands — deliberately
     splitting first (hitSelf) or noValidAction preserves the drop value).
  3. pocket extraction, not pocket fear: raise pocket forage to ~5-15% of
     intake like winners — gated so workers exit when the pocket's pearls
     are cleared (they leave, we wedge).
  4. swarm throughput: their eaten/game is 4-10x ours on the same maps —
     split-rate/econ, not positioning, is the corridor gap.

REPLAY EVIDENCE on file: workspace/topreplays/t{952,70,501,226}/ + sides.json,
pm_*.json aggregates. Analyzer: tooling/pocket_metric.py.

== Corridor/transit attrition study (45 ladder games, corridor maps) ==

Corpus: 45 corridor-map ladder games (whole 5-game sets pulled around recent
losses vs nooberGamer/wawow830/zzz3nith/Ron Squad, elo 1590-1700): Maze,
Tower Defense, Trauma, weakhold, Slithery Fight. us=A in every set.
Metrics via extended tooling/pocket_metric.py (region bands + cell-degree
bands + round buckets + queen flag + len-at-death).

TASK 1 — per-game death mix, our losses (23) vs our wins (22):

              our LOSSES (23g)          our WINS (22g)
  deaths   US 96.1   OPP 263.1       US 78.5   OPP 65.3
  wall     US 17.4   OPP 4.1         US 11.2   OPP 0.8
  self     US 21.4   OPP 146.8       US 18.5   OPP 34.6
  body     US 7.7    OPP 4.6         US 10.8   OPP 0.8
  h2h      US 36.9   OPP 36.9        US 26.4   OPP 28.2
  nva      US 12.7   OPP 70.7        US 11.6   OPP 1.0
  eaten    US 337    OPP 792         US 360    OPP 188
  queenD   US 0.78   OPP 0.17        US 0.36   OPP 0.91

ONE-SIDED RATIOS in losses: eaten OPP 2.35x US; deliberate deaths
(self+nva) OPP 217.5 vs US 34.1 = 6.4x; walls US 4.2x OPP; h2h 1.0x = WASH;
hitOtherBody US 1.7x. Region: our deaths 93% OPEN cells, only 7.1/g in
pockets — pocket-wedge is not the leak; OPP pocket deaths 21.2/g are feed
drops. Narrow-cell deaths: our wall deaths 72% in deg<=2 cells; opponents
die deg<=2 too but via self/nva (feed), never wedge.

STEERING CLAIM CHECK — "31-33 feeders die h2h r360-499 in feed transit":
NOT reproduced. Our late-window (r360+) h2h = 2.4/g in losses; h2h dead are
len2-3 (31/36.9 per g) in the r100-359 melee, not long feeders walking to
an anchor. The transit leak is not h2h; it is WHAT we die by: 14.8/g mid
wall + 6.5/g mid body + 14.3/g mid self of mostly len2-3 dragons dying
unproductively while OPP churns 143/g mid as deliberate feed.

TASK 2 — how do winners avoid pocket traps:
They do NOT avoid narrow cells (narrow-cell turn share 13.3-14.1% vs our
11.9%). They never pick the wall death: m1106190 OPP wall=0 while
self=833 + nva=275 (=1108 deliberate deaths/1206 total); m1106138 OPP
wall=0, self=370. cheji/Cache corpus (earlier study): literal ZERO hitWall
across ~400 deaths. Cornered -> die deliberately ON the feed anchor, not
against the wall.

TASK 3 — proposed mechanism (one, no mobility/econ restriction):
MID-GAME DIE-IN-PLACE: relax the feed channel's eligibility from the
r330+/converged-champ/cheb-1 gate to: round>=~120, worker len<=3, no pearl
target within reach and no hunt -> path to champion reported cell and
SPLIT-0 there (noValidAction drop on own cells). Rationale: (a) the dead
population already exists — our 45/g mid deaths of len2-3 workers die for
nothing; converting even 1/3 into anchor drops doubles feed volume;
(b) measured OPP volume 143/g mid deliberate deaths is exactly their
econ edge (eaten 792 vs 337); (c) zero movement restriction — it gives
idle workers a destination, matching shipped die-in-place semantics
(23% adjacency proven in v150). Cheap adjunct: when ALL candidate moves
are lethal (cornered), score the death cell by ally-adjacency/pearl value
instead of equal -inf — die where the drop is retrievable, never hitWall.

EVIDENCE: workspace/transit_corridor.json (45 games), transit_metric.json,
topreplays/, worst cases m1106138 (US wall 101 vs OPP 0), m1106190
(US wall 98 vs OPP 0, OPP self 833).

== Worker routing study (task: pocket-trap avoidance mechanism) ==

Corpora: our 45 corridor-map ladder games + top-team replays
(952 Cache/5g, 70 cheji/15g, 501 Quaker/8g, 226 Knight/11g).
New tooling: narrow_visit.py — per-side narrow-cell (deg<=2 or region<40)
VISIT outcomes: exit / split / die-by-reason, dwell, eats by region band.

ANSWER — neither pure hypothesis; the trap is decided at ENTRY:

(1) Target-selection ruled OUT. Winners enter narrow cells 1.4-8.6x our
    rate (visits/g: ours 342, OPP-ladder 505, cheji 1067, Cache 466,
    Quaker 1400, Knight 2955) and forage inside them heavily (cheji ~20%
    of intake from region<40). No min-region-size filter on their targets.

(2) Move-legality ruled out at death time: 219/219 sampled US hitWall
    deaths had ZERO empty neighbors (e0) — once cornered, every option is
    lethal; there is no "pick the exit" left. Exit share: US 81%, OPP 64%,
    cheji 67%, Cache 64% — we actually exit the MOST.

(3) The real geometry: our wall-dead are len2-3 (89%), in regions >=120
    (92%) — NOT pockets — at deg<=2 cells: 1-wide dead-end BRANCHES
    (deg1 tip + deg2 chain). Plug owners: own body ~48%, ally body ~45%,
    enemy ~1.5%. A len>=2 dragon entering a 1-wide dead-end path can never
    U-turn (retreat = hitSelf through own body): entering is a one-way
    trip. len-1 unaffected (no body to plug).

(4) Winners' narrow visits end deliberately, not on walls: Cache/cheji
    hitWall=0 with die-in-narrow hitSelf 63/g and nva 156/g — they dive in
    TO feed-die or pass through. Ours forage in and get self-plugged:
    US 12.8 wall + 12.3 self/g in-narrow vs OPP 2.3 wall + 57.1 self +
    18.9 nva/g. Knight/Quaker DO wall-die (174-494/g) — they win on churn
    volume instead; zero-wall discipline exists and is reachable.

PROPOSED MECHANISM — deadEnd_ branch map (one flag):
precompute per cell `deadEnd` = cell lies on a maximal deg<=2 path ending
at a deg1 tip (1-wide dead-end branch, not a loop — same BFS sweep as
regionSize_, once per map). Then:
  (a) forage/target/step value := 0 for any len>=2 worker whose move
      would enter a deadEnd cell (one-way trip — can't retreat);
  (b) dragons already inside (spawn/split there): die-in-place pull —
      drop the body deliberately (suicide/SPLIT-0) instead of grinding
      to the tip for a wall death. Same drop, deliberate positioning.
Gated on corridor maps (anyDeadEnd_ flag). Predicted effect: our 12.8/g
narrow wall deaths convert to ~0 (pathing never enters) + the trapped
residual becomes feed drops like OPP's 57/g hitSelf.

== C7 sealed-queen port status ==
STILL UNPORTED in flagship. abyss_v192/policy.hpp:676 still gates
`queenReach() < 20` in locateChamp; no queenSealed anywhere. NOTE: v192
now computes `regionSize_` (wall-component size per cell, once per map,
for workerRegionNorm) — C7 becomes a 4-line port:
  sealed := openNb(cell) <= 2 || regionSize_[cell] <= qlen + 8
exactly the autarky spec (head-degree bound + pocket-capacity bound),
foreign bodies open by construction.

== v201 deadEnd gate (v201_corr_local, 16g: trauma/slithery/weakhold/dilemma x2 seeds, both seats, vs abyss_v200) ==
Ran locally (gate not pushed when tasked): **43.8% ALL** — 2W/3S/3L.
weakhold + trauma 75% each (1W/1S/0L), slithery 25% (0/1S/1L),
**dilemma 0/4 — all four games IDENTICAL r97 teamEliminated c0/b3**,
both seeds both seats = deterministic, not noise. ALL-unlocked 50%.

VERIFICATION vs the three checks:
(1) walls ->0 on deg<=2 branches: VACUOUS — this fixture produces ZERO
    hitWall on both sides (corridor hitWall bleed needs ladder/live-opp
    replays; self-play gives hitSelf not hitWall). What IS measurable:
    dn1_hitSelf (deaths at dead-end TIPS): **0.94/g vs 15.81/g on base**
    — the tip-grind class is eliminated. dn2_hitSelf 20.8 vs 27.1.
(2) dedie nva fires: dn2_nva 10.4/g vs 4.5, dn1_nva 1.6 vs 0 — the
    inside->die-in-place triggers ~12/g on narrow cells. Total nva flat
    (66.6 vs 68.1) since base churns more overall. Total hitSelf
    34.1/g vs 55.4 (-21/g converted). slithery: 385 vs 783 over 4g.
    Counter-signal: weakhold hitSelf 150 vs 61 — v201 self-plugs MORE
    on weakhold (forage denial pushes workers into open-cell suicides?).
(3) freeze/starve pathology: CONFIRMED + FATAL on dilemma — see below.

DILEMMA FORENSICS (the 0/4): map marks only 3% cells deadEnd (16/512;
4 chains: tips at (14,0),(17,0),(14,15),(17,15) -> junctions y4/y11 on
x=14,17 columns). But BOTH len-11 starters' bodies span those columns:
B id=3 head (17,13) sits inside the y12-15 chain; its r0 split throws
child id=7 at (17,3) inside the y0-3 chain. dedie kills the child at
r0 (nva) and the parent at r1 — **spawned-on-deadEnd starters and fresh
split children suicide instantly**. The len-11 is geometrically doomed
either way (facing the tips, no U-turn — v200's mirror dies hitSelf at
the tips too, e.g. r4@(14,0)), but v200's slow death produces 3-4
split generations that keep the early swarm alive; v201's instant nvas
strip the reproductive runway: B side total 114 dragon-turns vs A 853,
wiped r97.

Mechanism verdict: entry-price + dedie is GEOMETRICALLY CORRECT (the
doomed dragons it kills really are doomed) but STRATEGICALLY BLIND —
it cannot distinguish "entered a trap" from "born in a trap". Fixes,
ranked:
  (a) dedie only when the dragon has no legal path to a junction
      (escape check — fires only when certain; still wouldn't save
      id=3 but is the correct semantic);
  (b) per-dragon enteredDeadEnd flag set on stepping onto deadEnd_
      from outside — spawned-inside dragons never dedie (lets doomed
      starters run their productive endgame like v200's);
  (c) dedie grace window (skip r<K) — cheap but weaker than (b).
  (b) is the honest fix: the pathology we measured is forage ENTRY,
  not spawn position. Entry price (a) stays as-is.
Also note: dilemma x=14/17 len-11 starters are inherently doomed — a
map-level fact both bots pay; it only decides the game because dedie
front-runs the death and forfeits the splits.

Side metrics worth keeping: qlen@end 8.1 vs 4.6 UP, queen alive@end
0.583 vs 0.417 UP, longest@end 21.9 vs 19.4 UP, alive@r499 5.9 vs 7.7
DOWN, adjacent free pearl taken 0.540 vs 0.661 DOWN, eaten/g 443 vs
527 (-16%), small-map pearls@r60 2.9 vs 13.1 (4.6x down — forage
denial costs real intake on small maps), alive@r50 3.0 vs 6.75 DOWN.

VERDICT: REJECT as built — fix (b) first (spawned-inside exemption),
then re-gate with dilemma included; off-dilemma board is ~58% and the
tip-grind elimination is the real win.

== FUNNEL COLLAPSE STUDY: how winners' feeders get adjacent ==
Corpus: 51 replays (topreplays t70/t226/t501/t952 + 12 okbro/dseek/1234
ladder). tooling/feed_origin.py: per deliberate death ->
sd=spawn->death cheb, dc=death->rolling-longest-head cheb. 36/102
sides produced a champ >=30.

ANSWER: NEITHER path-to-champ NOR spawn-adjacent budding — it's
CHURN-COMPACTNESS. Feeders die where they spawn, inside the swarm blob:
  - sd_med = 3-4 cells (all sides, monster and non-monster games alike)
    — feeders do NOT travel to the champ; even in monster games the
    median feeder dies 4 cells from where it was budded.
  - dc_med = 8-10 cells — deaths land ~10 cells from the rolling
    longest, i.e. inside the swarm blob, not at its head. Deliberate
    deaths literally adjacent (<=2 of longest): only 7-12%.
  - NOT champ-budded (prior finding holds): children land 12-23 cells
    from the current longest; parent==longest only 0-15% late.
  - Path-to-anchor DOES occur but only in the minority deep-funnel
    games: 1234 m1099017 sd=18/dc=22 (champ 36); okbro m1098976
    sd=9 (champ 33 with n=32 swarm — mass-churn mode). Median mode is
    die-in-blob.
  - The real discriminator is VOLUME: monster-game sides split 426-591
    /game vs 84 for loser sides without a monster. okbro/dseek/1234
    median splits 164 vs our ~44 (3-5x). Deliberate deaths up to 93/g
    vs our ~40 cap.
  - Winners end en=5-25 (some exceptions: okbro n=32); the funnel is a
    side-effect of a swarm that stays within ~10 cells of its anchor
    and replaces itself constantly — pearls drop in the blob, the
    champ grazes the field.

IMPLICATION (mechanism direction): bud-placement and per-feeder routing
are BOTH wrong targets. The funnel = (a) high split volume +
(b) compact swarm around the anchor + (c) deliberate death-in-blob.
Our midFeedRound=120 die-at-centroid already implements (c) correctly
(die in the blob == die near rolling longest when swarm is compact).
The residual gap is (a)+(b): they bud 3-5x more and stay tighter.
Constraint on (a) is food intake (they eat 2-4x more — churn economy),
so the funnel fix is upstream: swarm density near the anchor +
forage throughput, not the death mechanism.

== CORRIDOR ENTRY-AVOIDANCE: inverted again (deadend_visit.py, 39 top-team + 12 ladder replays) ==
Steering hypothesis: winners don't enter dead-end corridors at all.
VERDICT: **winners enter deadEnd branches 5-34x more than us. Entry
avoidance is a fabricated discipline — nobody does it.**

Per-side rates on deadEnd-marked cells (v201 marking: deg1-tip ->
deg<=2 chain -> junction):
| team        | enter/g | dwell/g | exit/g | wall | self | nva  | h2h |
|-------------|---------|---------|--------|------|------|------|-----|
| cheji       |   124.1 |   552.7 |   97.7 |  0.0 |  0.4 | 45.3 | 1.8 |
| Knight      |   481.6 |  1911.7 |  254.1 |266.3 | 20.9 |  0.5 |15.3 |
| Quaker      |   156.4 |   590.5 |   71.2 | 89.5 | 16.0 |  0.4 | 5.1 |
| Cache       |    33.8 |   126.8 |    6.5 |  0.0 | 33.0 |  0.0 | 0.0 |
| their-opp   |    87.0 |   348.7 |   32.8 | 13.8 | 26.4 | 35.4 | 2.5 |
| US (ladder) |     6.6 |    40.2 |    5.7 |  2.2 |  2.2 |  0.0 | 0.5 |

Secondary facts:
- len@entry is le2-dominated EVERYWHERE (dead-end entries and deaths
  are a len-2 phenomenon — the swarm's default worker size), le3 next.
  len@death inside: 95%+ ld2.
- Tip-distance of in-deadEnd deaths: **~90% at td0 (the tip itself)**,
  all teams — winners included. They walk the whole branch to the tip
  and die there; the ONLY difference is death reason: cheji 561 nva,
  Cache 132 hitSelf, Knight 2929 hitWall, Quaker 716 hitWall at td0.
- cheji "exit" 98% of entries = len-1s darting in/out (U-turn legal
  at len-1). len>=2 entry is a one-way trip ending at the tip for
  every team.

REREAD OF THE MECHANISM LINE:
(a) v201 entry-fatal-price: backwards — we already enter dead-ends
    least of all (6.6/g vs winners 34-482/g). We banned ourselves from
    a forage channel winners exploit; eaten/g -16% on the v201 gate is
    the mechanism eating real income, not noise.
(b) v208 dedie r>=30: kills dragons at the MOUTH for a death winners
    take at the TIP — same pearl position either way (own-cell drop),
    so dedie saves nothing positionally and forfeits the corridor's
    pearls en route. Its 45%/20 fits.
(c) What winners actually do in corridors = treat them as one-way
    forage channels: len-2 walks in eating pearls, dies at the tip,
    len-1s sweep the drops (only len-1 can U-turn out). The corridor
    economy is income + churn, not a trap to avoid.
(d) Our corridor deficit is entry VOLUME and overall churn, not
    death-geometry. Dead-end branch cells should be forage-valued
    (they're the last untouched income on corridor maps) with the
    tip-death accepted as the cost — the Knight profile.

RECOMMENDATION: retire the deadEnd family (3 gates, all dead/negative:
v201 43.8, v208 45, plus the 16-cell dilemma spawn zap). If anything
remains, it's a *tip-death conversion* (hitWall->nva) worth ~0 since
pearl position is identical. Corridor attrition's real lever is the
churn economy — eat more, die deliberately, repeat.

=== QUEEN-DEATH CENSUS: v209_full (220g locally reproduced, abyss_v209 vs abyss_v168, --maps all --seeds 5) ===
Corpus note: the orchestrator's v209_full replays were never committed; I
reproduced the identical fixture on this box (results/v209_full_local,
220/220 replays). Final score 52.7% — matches the ~53% composite, so the
corpus is representative.

HEADLINE: 93/104 losses include our queen dying (89.4%). She is alive in
ALL 116 wins — survival is a perfect bell gate on this corpus. Zero
elim-cascade losses; zero h2h-initiated cases identifiable from events
(move order not exposed; both parties die same round).

CLASS COUNTS (of 104 losses / of 93 queen-death losses):
  a-ram-isolated    49  (47% / 53%)  h2h, no ally within 2 tiles
  b-ram-escorted    22  (21% / 24%)  h2h WITH ally at 0-2 tiles
  d-self-wall-body  22  (21% / 24%)  hitSelf 16 + hitOtherBody 6, med r209
  e-elim-cascade     0
  queen-alive-loss  11  schooltime x4, trauma x4, stronghold-s2,
                        slithery_fight-s5 (second/third-key losses)

CLASS (a) — rammed isolated, n=49 (med kill r137, range 14-464):
  Killer distance at k-5: med 4 cells, 1-7 in 38/49 cases. The rammer is
  VISIBLE 5 rounds out — approaching from inside vision range, not
  materializing from fog. Only 2/49 beyond 8 cells (big_empty-s5 @29,
  default-s1 @10).
  11/49 killers were NEWBORN SPLITS (absent at k-5, born age 0-4):
  Colosseum-s2 (split@24 kill@28), arena-s1/s2/s4/s5 (children born r8-13
  kill r12-16), devil-s4 (born@153 kill@157), default-s5 + dilemma-s3 +
  slithery_fight-s5 (born and killed same/adjacent round). The enemy
  births a len-2 child adjacent to her and it rams immediately — no
  travel, no warning window, only body-geometry prevents it.
  Queen drift over the last 5 rounds: med 3 cells — she is wandering, not
  sprinting away. Spawn-dist med 8: mid-map roaming, not leash-pinned.
  Refs: Colosseum-s1 r35, arena-s2 r14, australia-s5 r173, autarky-s4
  r138, big_empty-s1 r146, weakhold-s3 r405.

CLASS (b) — rammed WITH escort, n=22 (med kill r113):
  ally_d 0-2 by construction; killer@k5 med 5 (3-6 typical). She is
  INSIDE the swarm and the rammer still connects — escort PRESENCE does
  not stop the dive; nobody was interposed on the approach lane. drift
  med 3, spawndist med 8 — she was wandering with the pack, not evading,
  not leash-pinned. h2h trades the rammer too — a len-2 child diving her
  inside our own pack is a net-positive trade for the attacker (auto-
  bell under lexicographic scoring).
  Refs: arena-s1 r12 (ally_d 1!), tower_defense-s3/s4/s5 r174-278,
  big_empty-s2..s4 r60-120 (4 kills — open map, escort can't screen all
  arcs), unsw-s4 r222, devil-s2 r90 (ally_d 2, enemy_d 0 — adjacent kill).

CLASS (d) — self/wall/body, n=22 (med kill r209, range 67-351):
  All hitSelf/hitOtherBody, mid-map with allies nearby (ally_d med 2) —
  she collides with her own swarm while roaming, not cornered in fog.
  DETERMINISTIC BUG: weakhold A-side queen dies hitSelf @r132 cell
  [15,14] in ALL THREE cand-A losses (s1,s2,s4) — same round, same cell,
  different seeds. A scripted self-collision in v209's policy on the
  weakhold A-side path — worth a direct replay-stepped fix. Other refs:
  schooltime-s1 r316 [3,1] (top-row edge), schooltime-s3 r132 [56,1],
  islands-s4/s5 both r238, portals-s2/s3/s5 r225-243 (portal-map
  clustering suggests a portal-exit self-crossing pattern too).

ANSWER TO THE BUILD QUESTION:
  Post-v209 queen deaths are "isolated and doomed ~5 rounds out", NOT
  sudden pins from fog, NOT leash-pinning. Evidence: rammer at med 4
  cells at k-5 and visible in 38/49 class-a cases; queen drift med 3
  (no evasion attempted); spawndist med 8 (roaming free). The v213
  fog-escape sprint addresses a failure mode that barely exists here
  (2/49 killers genuinely far at k-5). What the corpus actually shows:
    1. A len-2/3 rammer (incl. NEWBORN splits, 11 cases born 0-4 rounds)
       walks up to an unescorted queen over 4-6 visible rounds and she
       does not react — there is no dodge/evade trigger on approach.
    2. Escorts that merely stand near her fail 22 times: presence !=
       geometry. The screen needs to interpose on the threat arc, or
       she needs to retreat behind the swarm when a head closes.
    3. Fix class = approach-reaction + escort geometry (body on the
       lane), not vision extension. The killer is already seen; the
       queen just keeps wandering.
    4. Secondary, cheap: the weakhold r132 [15,14] deterministic
       hitSelf is one scripted bug — fixing it erases ~3% of losses by
       itself; portals/islands self-crossings (r225-243) look like a
       second scripted pattern.
  Corpus: /tmp census jsonl + 220 replays under results/v209_full_local/
  on branch; analyzer tooling/queen_forensics.py (committed).

CORRIDOR SIDEBAR (per your ask): winners' workers on trauma/PD do NOT
avoid dead-end entries — measured last report: they ENTER dead-end
corridors 5-34x more than us (entry avoidance inverted). The deadEnd
family is retired on 3 gates (v201 43.8%, v208 45%/20 + dilemma zap);
corridor answer is the churn economy (forage-in, deliberate tip-death,
len-1 sweeps), not routing. No new work needed here unless you want the
tip-death conversion (~0 value, same drop cell).

=== v225 MECHANISM AUDIT (locally reproduced: abyss_v225 = v209 + lateSplitUnits 20->9999, gate --maps all --seeds 1 --seed-start 3, 44g vs v209, results/v225_smoke_local) ===
Your v225_smoke replays aren't on any branch/box I can reach, so I rebuilt
the candidate (one-line param on v209, verified diff = common.hpp:270
lateSplitUnits 20->9999) and reran the same fixture. Local read 52.3%/44
vs your 55.9%/34 — same mechanism under test.

MECHANISM CONFIRMED — post-r300 worker-split release raises late churn:
  post-300 splits:   cand mean 35.8 (med 6.5)  vs  base mean 29.2 (med 5.5)
                     burst concentrated r300-350 (703 vs 467 splits)
  alive@end:         15.61 vs 14.41  (+8%); alive499 13.65 vs 11.58 (+18%)
  total@end:         122.2 vs 96.7  (+26%); r499-only 169.8 vs 126.2 (+35%)
  longest@end:       20.7 vs 19.4; r499-only 33.2 vs 31.0  (consolidation
                     NOT harmed — champ still grows on the bigger swarm)
  eaten:             635.7 vs 596.7 (+7%)

WHERE THE EXTRA SPLITS HAPPEN: swarm-wide frontier churn, NOT bud-adjacent
feed — only 13% land within cheb-6 of the longest head (schooltime 2%,
big_empty 5%, unsw 16%, islands 42% [funnel map], slithery 9%). Parent
len med 2 — small len-4->2 splits keeping population topped up. The feed
phase still consolidates via the death side instead: post-300 nva feeds
19.6 vs 14.1 (+39% — more units alive to walk into the anchor).

COST SIGNATURE: none on h2h — dead even 58.15 vs 58.2 total, 10.1 = 10.1
post-300. hitSelf/hitOtherBody even. The only negative read: queenEnd
1.05 vs 1.68 mean — but queen-death RATE is near-even (36 vs 34 dead@end,
qDeadRound med 113 vs 107 — ours dies slightly LATER), so it's length-mix
noise not a survival regression. Bell flips (dead-vs-live): cand lost 5,
won 3 — roughly balanced.

PAIR RECORD: autarky 0/2 + weakhold 0/2 pair losses (both seeds); wins on
default_small, islands, maze (all 2/2). 44-game CI is wide (~±15pts), so
read as mechanism-verified + score-positive, not gate-proven.

VERDICT: mechanism does what it claims — late churn volume up, champion
consolidation preserved, no h2h donation tax. The +26-35% total-length
lift is where the bell gains live (key-3), and nva-feed supply rising
+39% is the key-2 helper. Watch item: queenEnd means sit lower on cand
side despite flat death rate — worth one more board before shipping if
the composite margin is thin. Analyzer: tooling/v225_units.py.

=== DROP-RECYCLE AUDIT (v237_live replays absent from all branches — locally reproduced gate v237 vs v168 all-maps s3, FULL 44g = 52.3% (4W/15S/3L) matching live tracking; + top-team corpus 103g; + ladder_replays 12g live vs foreign) ===
Analyzer tooling/drop_recycle.py: per dragonDeath -> drop cells = own-cell
True pearl flips within r+2 (verified against head-path positions), fate =
next False flip <=5r attributed to the side+id whose head was on the cell.
Travel = drop-cell to eventual eater's head at death round (the "~1 vs ~8
moves" quantity). Parent-recycle = literal split-parent eats the drop.

VERDICT: the donation claim is FALSIFIED on every axis, in all 3 corpora.
  corpus            ally_d med | eater-travel med | us/them/decay(5r)
  TOP (103g)          1            2            29 / 30 / 41
  TOP-opps            1            2            29 / 30 / 41
  v237 self-play(44g) 1            2            29 / 29 / 42
  v168 self-play(44g) 1            2            28 / 28 / 44
  US live ladder      2            2            25 / 25 / 49
  OPP live ladder     1            2            30 / 28 / 41

- Winners' drops are eaten at med travel 2 (not ~1); ours at 2 (not ~8).
  Far-travel tail (>=8): us ~5%, opponents ~7%. No donation asymmetry.
- Live ladder specifically: our drops 25% self-recycled vs 25% donated —
  a dead-even mirror, not a midfield giveaway. Unlimited window: 49/43/9
  vs their 48/46/6 — still symmetric.
- Parent-recycle: TOP 9.6%, v237 7.7%, us-live 7.5%, opp-live 4.7% —
  ours slightly ABOVE opponents, not broken.
- ally_d (death->nearest ally head): med 1-2 everywhere; opponents die at
  med 1 vs our 2 on the ladder — they die marginally nearer friends.

THE REAL (SMALL) RESIDUAL: our live-ladder decay rate is 49% vs their 41%
— our drops rot ~8pts more because they land in thinner neighborhoods
(same ally-density cause as everything else: volume, not geometry). The
dominant gap remains death VOLUME (~87-140 deaths/game ours vs ~300
top-team) — not where drops land or who retrieves them.

IMPLICATION FOR die-toward-allies: the imagined mechanism targets a leak
that measures ~zero. Best case it shifts the ~8pt decay gap — worth a
fraction of a bell at most. Recommend NOT building it as specced; if the
decay residual matters, the lever is swarm density at death sites (same
churn-economy fix as everywhere), not death-cell selection.

Wins-vs-losses (task item a): v237-death ally_d histogram identical in
won vs lost games — med 1 both, shape near-identical (win n=2403 med 1;
loss n=4170 med 1). Losses simply contain MORE deaths; the recycle
geometry doesn't change. Replays: results/v237_live_local/ (all 44).
Tooling committed.

=== DROP→LONGEST GEOMETRY (orchestrator's 27-vs-9 claim) ===
Full report appended to devin/STATE.md on origin/devin/v120 @84e31d6.
Does NOT reproduce on 56 games / 8 metric variants: dc ~7-8 med for all
sides. Ours die CLOSER to the longest when deliberate (nva dc 4 vs 9).
In-blob churn = volume inside same geometry, not death positioning.
Only unreproducible axis: distance to the elected champ's REPORTED cell
(bot-internal anchor staleness — flagged to orchestrator as likely
metric source; different fix if confirmed).
Tooling: tooling/churn_blob.py.

== Suicide geography (nva death-cell census) — 2026-10-04 ==
Corpus: workspace/topreplays t{70,226,501,952} (39g, 8739 nva deaths)
+ ladder_replays (12g, 80 nva). Per death: cheb to longest-ally head,
queen head, nearest LIVE pearl (tileChange-tracked), ally heads <=4,
dead unit len. Analyzer: tooling/suicide_geo.py.

MEDIANS (torus cheb):
                TOP-win (n5135)  TOP-lose (3604)  US ladder (80)
 d_long         9                11                4
 d_queen        14               16                9-10
 d_pearl        2                2                 2
 ally4          5 (97%>0)        4 (95%>0)         2-4 (100%>0)
 len med        2                2                 3
 len hist       1:7 2:67% 3:24% 4+:9%   similar    2:39% 3:40% 4+:21%
 isLongest      3%               6%                10%

ANSWER 1 — consumer: NO single consumer. Winners' suicides land ~9
cells from the longest head and ~14 from the queen — NOT beside the
champ. They die INSIDE the swarm blob (5 ally heads within 4 cells)
beside a live pearl (d=2). "Densest patch" is closest to true, but
the site is swarm-relative, not anchor-specific. (Drop-recycle audit:
the actual eater is ~2 cells away — whoever's adjacent in the blob.)
Ours land TIGHTER on the longest (d=4) — die-at-centroid already
overshoots their geometry.

ANSWER 2 — length signature: REAL. Winners' dead are len-2 stubs
(67%; med 2). Ours med 3 (len2 39%, len3 40%). They recycle a unit
the moment it's jobless, while it's still a 1-pearl stub; we hold
to len-3+ before the die-in-place fires. Combined with 25x rate gap
(250/g vs our ~10/g): the discriminator is LIFECYCLE, not site —
they churn stubs early and often in-blob; we suicide rarely and late.

IMPLICATION: midFeed's len<=3+centroid is pointed at the wrong axis.
Winners' version is closer to "len-2 unit in the dense blob with no
job -> die now beside the nearest pearl". If a next build relaxes
eligibility, the measured targets are: fire at len==2 (not len<=3),
site = near swarm density+pearl (not necessarily the centroid anchor).

================================================================
PARKED-UNIT CENSUS — big-map unit geometry, top teams
================================================================
Corpus: ~/bc/ciallo_replays + ~/bc/cursey_replays (pulled 30+30 via
ladder.py, teams 1064 Ciallo / 784 CURSEYOUBAYLE). 41/60 games ran
the full 500 rounds (19 ended early — excluded per spec). fv2,
botA/botB fields empty so sides reported as winner vs loser.
Parked def: head within cheb-2 of its position 10 rounds earlier
for all 10 trailing rounds. Beds: cells with >=3 hasPearl
tileChange events. Torus cheb. Analyzer: tooling/parked_census.py.

PARKED FRACTION OVER TIME (median per 25-round bin):

 bin (r)   0   1    2    3    4    5    6    7    8    9
 winner   .03 .11  .12  .13  .15  .14  .15  .15  .15  .16
 loser    .04 .14  .14  .11  .13  .15  .13  .13  .13  .14

 bin (r)   10   11   12   13   14   15   16   17   18   19
 winner   .15  .15  .16  .14  .15  .14  .14  .10  .10  .11
 loser    .16  .16  .14  .17  .15  .12  .13  .12  .12  .11

Profile: ramp to ~13-16% by r50-75 (new units can't be parked for
their first 10 rounds), plateau through r450, tail-off ~10-12% in
the final 50. Winners and losers park at the SAME rate — the
fraction is not a discriminator (win 22.3% of unit-rounds vs
lose 21.2% overall).

BED GEOMETRY (per-game medians):
                 win (41)   lose (41)
 d_bed parked     1          1
 d_bed moving     1          2
 adj<=1 parked    .697       .651
 adj<=1 moving    .513       .478
 parked unit-rnd  2125       1264  (winners field more units)

ANSWER — camp on fountains: CONFIRMED for both sides. ~70% of
parked unit-rounds sit adjacent (cheb<=1) to a natural pearl bed
vs ~51% of moving unit-rounds; parked median d_bed = 1 vs moving
1-2. Parked units are not scattered mid-map — they hold position
next to a pearl spawn cell. Residual ~30-35% of parked rounds are
off-bed (d>1): med 2-3, i.e. still within one step of a bed —
perimeter/body-plug camping rather than remote stalls.

WINNER vs LOSER differences are small and consistent: winners'
parked units sit slightly tighter on beds (adj 0.70 vs 0.65) and
winners generate ~70% more parked unit-rounds (2125 vs 1264) —
but the parked SHARE is equal, so the driver is unit volume, not
parking behavior. Losers die off — fewer units to park.

IMPLICATION for our build: on big maps the top teams run a
~15%-of-units standing crop sitting on beds — a feed/guard layer
that eats pearls as they spawn. Combined with the funnel census
(feeders die where they spawn inside a ~10-cell blob) the model
is: bed-adjacent residents + churning stubs, not roaming foragers.
Parking itself is not a win lever (losers match the rate); the
lever stays volume + where the parked crop sits relative to beds.

================================================================
INTAKE CENSUS — pearls eaten per unit-round + starvation
================================================================
Corpus: top-10 ladder replays re-pulled (42 top side-obs, 36
games) + 30 Cognoscenti ladder replays (our live flagship —
"our v376" replays don't exist on any box/branch; newest on
devin/v120 is v341; ladder replays ARE the current live build).
60 opp side-obs as mid-ladder reference.
Eats: tileChange hasPearl->False, attributed to nearest alive
head (validated 96.5% d0, 3% d1 ordering, 0.4% noise).
Analyzer: tooling/eat_census.py.

                     top(42)   ours(30)   opp(60)
 eaten/game            762       354        257
 eaten r0-120          150        54         64
 unit-rounds         10574      4631       4515
 unit-rounds r0-120   1788      1081        934
 EFF (eaten/ur)       .0719     .0576      .0602
 EFF120              .0788     .0455      .0621
 starve@60           .417      .578       .471
 starve@120          .496      .482       .604
 alive@60            ~21       ~11        ~13
 alive@120           ~36       ~18        ~21

(a) ARE THEIR UNITS BETTER FED? YES — +25% per unit-round over the
full game (.074 vs .060 mean) and +73% in the ramp (.079 vs .0455).
Not a denominator artifact: vs our own ladder opponents we're dead
even (paired eff120 diff -0.0006, 30 pairs) — our per-unit forage
is mid-ladder par, top-10 is a genuinely better class.

(b) THE RAMP WINDOW is where the gap concentrates: eaten120 top
150 vs ours 54 (2.8x). Decomposed: ~1.65x unit-rounds (1788 vs
1081) x ~1.7x per-unit efficiency. BOTH effects real, roughly
equal weight — swarm coverage AND forage efficiency.

(c) STARVATION: @60 we starve 58% of alive units vs their 42%
(opp 47%) — 4-in-7 of our early units go 10+ rounds unfed. @120
converges ~50% everywhere (churn makes the alive-pool young;
residual diffs are survivorship noise — ours .482 < opp .604
because our units die before they can starve).

VERDICT: forage targeting IS a broken piece — specifically in
r0-120. Top teams' per-unit intake is +73% in the ramp while
holding the same len-2-peel split recipe. The mechanism to copy
isn't child size or split policy — it's early forage throughput:
each of their units converts ~2x the pearls ours does in the
window where split cadence is decided. Second factor is unit
count (~1.65x unit-rounds) — which itself is downstream of
intake (eat more -> resplit faster). Fix forage in r0-120 and
the unit-count half follows.
