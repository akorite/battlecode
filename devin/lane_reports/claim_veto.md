CLAIM-VETO COST FORENSICS (freeze task)
=======================================
Corpus: 30 fresh Cognoscenti ladder games (v134b-era live build —
abyss_v449 not pushed to devin/v120; newest branch ws is v447,
used for the code read) + 65 top-team replays (ciallo/cursey/
topreplays dirs; both sides tagged 'top' — 120 side-obs) + 28
opp side-obs from our games. Eats = hasPearl->False attributed to
nearest head (d<=1, validated 96.5% d0). Analyzer:
tooling/claim_veto.py (devin/pocket). Vision proxy VIS=8 cheb,
drop-adjacency cheb-1, conversion window k=5.

MEASUREMENTS (pooled, per side):

  (a) CONTESTED TAKES — pearl eaten while a same-team unit was
      closer-or-equal to the cell the round before:
        ours  2958/13050 = 22.7% of eats (med 44/game)
        opp   6883/24945 = 27.6%
        top  26414/96170 = 27.5%
      We collide LESS than everyone, not more — claims are not
      being over-violated; if anything we under-contest.

  (b) ORPHANED PEARLS — pearl instance alive >=3r with a friendly
      head within cheb-8 during life, never eaten by us:
        ours  5071/5549 seen = 91.4% untaken (~181/game)
        opp    (first-pass corpus) 34.2% of seen
        top    (first-pass corpus) 44.6% of seen
      Focused pass, damning subset: pearls with a friendly head
      within cheb-2 at some round — 981/1349 = 72.7% STILL never
      eaten. Three of every four pearls we stand next to for 3+
      rounds rot to the enemy or void. (Note: corpus set changed
      across passes — treat 91.4% as the current-build figure,
      direction confirmed on both.)

  (c) ADJACENT-DROP CONVERSION — pearl spawned within cheb-2 of a
      same-team death head, eaten by a teammate within 5 rounds:
        ours  2265/2746 = 82.5% (all drops incl non-adj: 48.7%)
        opp   5524/6693 = 82.5% (58.1%)
        top  21902/26855 = 81.6% (56.4%)
      THE Z-A 598/603 (99%) CLAIM DOES NOT REPRODUCE — everyone
      converts ~82% of adjacent drops inside 5 rounds. In the five
      actual Z-A games they ran 87-99% in wins — a game-level
      artifact (winner's swarm sits on the drop), not a separate
      mechanism. Our adjacent conversion is parity; the all-drops
      gap (~9pts under top) is volume/density, not veto.

THE RULE (policy.hpp, verified vs abyss_v447):
  friendDist_[cell] = min BFS dist from any visible teammate head
    (nearest maxRivalFields=12) PLUS heard teammates within
    heardFresh — claims extend past live vision.
  Per target per candidate destination (both loop bodies):
    m = dd + 1 + k   // our BFS dist to cell + steps already planned
    if (fd < m || (fd == m && friendId_ < our id)) v = 0;
    else if (enemyDist_[cell] < m) v *= enemyCloserFactor (0.85)
  i.e. a pearl a teammate is closer-or-equal to contributes ZERO
  pull for us — hard veto, not a price. ~policy.hpp:1542/:1569.

SUPPRESSION SHARE (code-level answer): the veto binds for every
non-closest unit on every shared cell — in an N-unit blob all
units but the single claimant get v=0 on interior pearls, so the
per-decision suppression rate approaches (N-1)/N on contested
cells (~90%+ inside the swarm). It applies to starving_ workers
too — no override; belief-0 scout targets are the only bypass
(:1056 comment).

WHY IT LEAKS (the absentee-claimant channel):
 1) No claim staleness/TTL: claim = pure distance. If the claimant
    is parked (~15% standing crop measured), on a mission
    (hunt/escort/feed), or dies en route, the pearl stays vetoed
    for every other unit indefinitely — it can sit <2 cells from
    friendly heads for 3+ rounds uneaten (measured 72.7%).
 2) Growers/champs claim too: friendDist_ includes non-worker
    roles — a parked grower on a bed reserves its whole halo from
    workers who are actually foraging.
 3) Heard-field claims: stale heard teammate positions veto pearls
    the hearer may have left; heardFresh bounds recency but the
    field still writes friendDist_.
 4) No backup-taker semantics: v=0 for everyone else means there
    is no second-in-line if the claimant stalls.

IMPLEMENTABLE DIFFS (ranked):
  A) CLAIM TTL — cheapest, biggest: pearls whose belief-cell has
     persisted T rounds (seenPearl age, or t.countdown-style age)
     are exempt from friend-claim. Effect: after a grace window the
     next-closest unit is free to take it; targets the orphan pool
     directly. One-line-ish guard in both loop bodies:
       if (v>0 && pearlAge[t.cell] < p_.claimTTL) { ...veto... }
  B) STARVING BYPASS: `if (!starving_ && fd<m) v=0` — a starving
     worker ignores friendly claims (it dies if it waits; the
     claimant is by definition better fed).
  C) ROLE FILTER: don't let growers' (and possibly feed-anchor)
     fields write friendDist_ — a unit that won't forage shouldn't
     reserve food. Careful: growers DO eat to grow — restrict to
     stationary growers if distinguishable, else accept some halo
     theft.
  D) Defer: adjacent-drop conversion is at parity (82%) — no diff.

CAVEATS: replays show outcomes, not decision internals — the
suppression share is a code-semantics bound, not an event count.
Orphan metric uses cheb vision proxy; walls make some cheb-2
pearls BFS-unreachable (inflates 'adjacent' orphans on corridor
maps). Z-A 99% figure not reproduced on my definition — if their
'adjacent' means drop-cells a teammate was ON (d=0), rate differs;
recommend re-measuring with their exact filter before discounting.
