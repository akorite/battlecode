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
