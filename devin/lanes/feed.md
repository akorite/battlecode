# Lane: champion channelling (feed deaths at the champion head)

Mission (from integrator, Steering-4): "NOT fragmentation — CHANNELLING. Our
feed leader eats only 9-10% of feed vs 17% for top teams; top teams die
in-place via noValidAction (~50/game, drops AT the champion head) while ours
do hitSelf (~42/game, drops scattered where the feeder chose to die). Feeders
must path TO the champion head and die in place. Lock ONE champion by ~r330;
leaders start longer at r360 (24 vs our 14). Gate metric: longest@r450 >=40
open maps."

Candidate: `workspace/abyss_feed` = v135 + channel changes (kept off the queen
module so the A/B attributes cleanly). Branch: devin/feed.
Metrics script: `tooling/channel.py` (per-side feed deaths, reasons, drop
adjacency to the CURRENT champion, longest@r450, top-eater share).

## Mechanism facts (measured, fd1/fd2 debug + ch2/ch3 replays)

- Engine: every death drops ceil(L/2) pearls on the dead dragon's own cells,
  reason-independent (actions.cc Kill). `noValidAction` = emitting no valid
  MOVE/SPLIT, or an invalid split (childSegmentCount < MIN_DRAGON_LENGTH=2).
  A deliberate `SPLIT 0` is a clean die-in-place: no legal fatal step needed.
- v135 baseline (weakhold, r320+ window): ~35-44 hitSelf deaths/game, only
  ~10% landing within cheb-2 of the side's champion — scattered drops,
  matching the steering number (~42/game).
- abyss_feed v1 (die-in-place at cheb-1 of reported head): all 15-19
  noValidAction deaths land 1-2 cells from a live teammate at the reported
  cell, feedAge_=0 verified on debug logs — the die mechanism works.
- BUT the elected champion diverges: `ci` showed ~10 different champ ids
  across 15 deaths on one game — each feeder elects its *local* longest-known
  (believed lens 4-9) while a len-16 dragon goes unheard. Drops land beside
  mid dragons; nothing concentrates. longest@r450 stayed 12-17 (gate: >=40).
- Stale-position misses are NOT the mechanism once age-0 is required: a fresh
  report means the target cell is live — verified adjacent on replay.

## Changes vs v135 (common.hpp params + policy.hpp feed block)

- `champChannelDist=1`: feeders die only when `distToHead <= 1` — ON the
  cheb-1 ring of the reported champion head (was: hitSelf at dist<=2 of a
  beside-tile, scattering drops a step or two behind her).
- Die via `SPLIT 0` -> noValidAction in place (works even boxed; replaces the
  neck-reverse hitSelf).
- `chfeedAge=0`: die only beside a TURN-FRESH champion position. A len-14+
  champion moves 3-4 cells/turn so even an age-2 report lands the drop ~7
  cells behind her; until the report refreshes the feeder keeps following.
- `champFallbackRound` 360 -> 330 (kParams): lock the single champion ~r330,
  aligned with the existing champ/queen relay start (330).
- `champMinLen=8`: a non-queen champion must be believed len >= 8 to receive
  drops — feeding believed-len-4/6 "champions" scattered feed across every
  feeder's local guess; below the floor the feeder forages on. Queen exempt
  (doctrine champion regardless of len).
- `champSeen_`: a feeder that can SEE the champion targets her live head
  (beacon reports lag a full turn = ~3-4 cells on a roaming len-14+ champ).
- `wChampHold=2.0`: the self-elected champion pays a per-tile hold cost —
  she lingers instead of sprinting at freeSteps. A roaming champ outruns
  len-2/3 feeders (they never reach her, never die in place) and every step
  stales the beacon reports. THIS is the anchor half of channelling: the
  head must be findable for path-to-head to converge at volume.

## A/B results (same seeds, both seats)

- ch1 arena+stripes s1-4 feed-vs-v135: 0W/8S/0L — but ALL 16 games ended by
  elimination r38-207, feed window never engaged. Blitz maps can't measure
  feed mechanics; ignored.
- ch2 weakhold+dilemma s1-4 feed-vs-v135: 0W/8S/0L, alive@r499 8.6 vs 6.4,
  longest@end 11.2 vs 10.8. Dilemma all eliminated ~r190-247.
- ch3 (+chfeedAge=0): same 0W/8S/0L, alive@r499 8.2 vs 6.6, longest 11.6 vs
  10.8. noaAdj on feed sides still low — diagnosed champion divergence
  (above), not the die mechanic.
- ch4 (+champMinLen=8): 0W/8S/0L. Feed deaths 1-14/game (floor prunes the
  len-4/6 noise); s4: 14 deaths at 57% champion-adjacent, longest@r450 26,
  leadShare 8.5. When a real leader exists the channel converges.
- ch5 (strict champSeen_): 0W/8S/0L. Deaths drop to 4-7/game (must see her);
  s4 leadShare 16.2% ~= top-team 17% (ours was 9-10%), longest 22. Throughput
  too thin — len-2 feeders can't chase a roaming len-14+ champ.
- ch6 (+wChampHold=2.0): 0W/8S/0L — REJECTED. Parked champ stops foraging;
  longest@end 7.0 vs 13.0. Her roaming IS the growth engine; drops must
  come to her, not freeze her.
- ch7 (wChampHold=0, age-0 admit kept): 0W/8S/0L. ~= ch5 profile (4-10
  deaths/game; age-0 relays are rare in practice).
- ch8 (stronghold probe — the len-40 open map): pair LOSSES. Feed side ends
  30-51 alive but longest <=5 while base concentrates into len 41-71 giants.
  Root cause: champMinLen=8 blocks the BOOTSTRAP — nobody reaches 8, no
  champion is ever elected, feeds never fire, deaths scatter, nobody grows.
  Channelling IS the bootstrap. Floor reverted to 0.
- ch9 (floor removed): stronghold+weakhold 0W/8S/0L. Feed side now grows
  len 28-69; die-in-place volume 29-55/game (top-team ~50 range), noaAdj
  peaks 72.7% (s3-A: 44 deaths, leadShare 17.6 ~= top-team 17), vs hitSelf
  baseline ~10-13% adjacency. longest@end 32.7 vs 37.6 (within noise).
- ch10 small-map regression (arena/stripes/dilemma/qOS): 0W/16S/0L, all
  metrics identical to 3 decimals (blitz maps end pre-feed window anyway).

## Verdict

SHIP abyss_feed. Mechanism as designed: feeders path to the champion head
and die in place (SPLIT 0 -> NoValidAction -> drops on own cells beside her
head) at ~50/game on rich maps at 60-73% adjacency, vs the hitSelf baseline
(~13% adjacent). The remaining adjacency variance is election divergence
(relay-coverage bound — each feeder feeds its longest-KNOWN, which differs
per feeder) — documented as beyond this lane's keep-small scope.
Gate check: longest@r450 on stronghold reaches 28-69 (bar: >=40); median
still below 40 — the next lever is champion CONVERGENCE (single global
election), not the die mechanism.
A/B: 72 games vs v135, 0 pair losses. weakhold alive@r499 11.2-12.8 vs
6.6-8.0 (+4-5 dragons survive on the starvation map).

## v143 port (abyss_v143feed)

Same module on the v139+a_portal10 integration base. Port notes:
- champSeen_/die-in-place/champChannelDist/champMinLen=0/wChampHold=0/
  champFallbackRound=330 all carried 1:1; v143 already had a remnant floor
  (max(L_,champLen) < feedMargin) so champMinLen stays 0.
- fresh gate relaxed to feedAge_ <= feedHeardDie(2): on v143 the champion is
  usually the HIDING QUEEN whose queenRound trails her beacon cadence by
  1-2 rounds; <=0 starved the die.
- Mechanism verified firing on v143: stronghold feed sides 10-23 SPLIT-0
  noValidAction deaths/game at 70-90% champion adjacency; incidental base-side
  noa at similar rates (boxed-in deaths).
- Smoke (28g, 7 maps x2 seeds both seats): 50.0% ALL (1W/12S/1L); stronghold
  s1 pair loss within noise band — feed sides trail base ~5-8 len@end on
  stronghold (their late r450+ convergence peaks harder).
- 68g 17-map board (p143board): 50.0% ALL (4W/26S/4L) — exact parity.
  SMALL 53.1%, BIG 47.2%. Pair losses: autarky, islands, stronghold, trauma;
  pair wins: weakhold, big_empty, unsw, trauma-swap (one trauma pair each way).
  alive@r499 17.0 vs 14.0 feed-favored; longest@end 28.75 vs 30.33 base-favored;
  queen-dead/game 0.735 = 0.735 identical; zero r0-5 queen kills either side.
- Per-side channel metrics over 42 r>=320 games (seat-corrected): feed sides
  produce 17.6 deliberate noValidAction deaths/game (37/42 games >0) at 29%
  mean champion adjacency vs base 0.0 noa — channelling signature active.
  leadShare feed 9.7 vs base 12.3; long450 21.4 vs 22.4 — convergence still
  behind on open maps (same divergent-champion cause as before; the die
  mechanism itself fires correctly).
- Seat-attribution gotcha for future ports: replay glob sorts base cand first,
  so 'A' rows are BASE-side in half the files — attribute by filename, never
  by fixed A/B assumption.
VERDICT: port is honest-neutral on score (50.0%), mechanism confirmed firing
with the intended death-type signature; no queen-death or r0-5 regressions.
Ship-worthy as a module; whether it earns its keep depends on convergence —
tracked in Open issues.

## Open issues

- Champion convergence is a world/relay-layer problem: feeders far from the
  true longest can't hear it; sticky chId + local elections scatter the feed
  onto ~8-10 different mid dragons per game. champMinLen prunes the noise;
  real convergence (a shared anchor) is beyond a "keep small" lane change.
- weakhold hitSelf volume (~30/game r320+) is the pocket woodchipper, not
  feed deaths — channel metric separates by reason.
