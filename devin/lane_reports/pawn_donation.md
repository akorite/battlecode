PAWN-DONATION RECIPE vs ENGINE (feeds abyss_v463 design)
======================================================
Corpus: ciallo+cursey replays (60 games, winner/loser sides) +
15 fresh Cognoscenti ladder games (our live build vs tozoman /
Spearhead / shark++ / waddledee / No Idea). Analyzer:
devin/pocket:tooling/pawn_donation.py. Pawn = len-2 dead unit.
Drop = hasPearl add on a dead unit's body segment cell.

ENGINE RULE — VERIFIED EXACT on replay data:
dead dragons drop pearls same-round on body segments 0,2,4,...
(len-2 -> head cell only; len-3 -> head + seg[2], observed
directly: len3 death r65 adds at (10,13)=seg0 and (11,12)=seg2).
ceil(len/2) pearls confirmed by counts.

(a) WHO EATS WINNERS' PAWN DROPS — not the champ, not the queen.
    Winner pawn drops (5254 in ciallo alone): ally 55% / enemy 5%
    / decay>5r 17% / eaten 5-20r 23%. Of ally-eaten drops the
    EATER's length distribution (60g):
      ->2: 19%   ->3: 40%   ->4: 25%   ->5+: 16%
    eater is team-LONGEST only 13%, queen 1%.
    Read: donations feed OTHER STUBS, circulating mass through the
    len 2-4 pool — a quarter of ally-eats promote a len-3 to len-4
    (split-eligible). The recipe is "keep the stub pool topped up
    at the split threshold", not "feed the champion".
    Hyper-local: 79% of ally-eaters were already <=2 cells from
    the drop cell at the death round.

(b) WINNERS' PAWN DEATH MIX (win side, 175/game):
      hitWall 41% | hitSelf 16% | hitOtherBody 16% | h2h 14% | nva 13%
    88% die within cheb-1 of a pearl-bed cell — they die AT the
    fountains, actively ramming walls/necks, not clean die-in-place.
    Age at death med 13r; 31% dead within 5r of birth (fast bud
    recycling). Loser side similar mix (61% wall+body), on-bed 89%.
    OURS (47/game): nva 41%, h2h 26%, hitSelf 24%, hitOtherBody 9%,
      hitWall 0% — our pawns NEVER die on walls; we die passively
      (trapped/starve/contested) not by deliberate ramming, and
      only 60% on beds.

(c) UNIT-COUNT THRESHOLDS — winners run the loop once the swarm
    is large: pawn-death rate ~0.29/r at alive<50 -> ~1.07/r at
    alive 50-100. alive@pawn-death med 79 (p25 53). Ours: med 63
    but only 47 deaths/g vs their 175 — the gate isn't count, it's
    that our swarm rarely reaches/sustains the size + our pawns
    don't die on-site.

v463 GATE CHECK ("suicide len-2 buds within cheb-2 of len>=4 ally"):
    Only 35% of winner pawn deaths are within cheb-2 of a len>=4
    ally (med d=4); our current deaths: 20% within2, med 5. The
    winners' effective gate is "on a bed, in a dense ally
    neighborhood, consumer = nearest stub" — NOT "adjacent to a
    long ally". A len>=4-proximity requirement is ~3x narrower
    than winner geometry; an "on-bed AND any-ally<=2" gate matches
    88% of their deaths better. Also their pawn churn fires ~4x
    harder past alive>=50 — throttle the variant off below that
    (it can't recycle what the swarm can't re-eat).

DELTA TO WINNERS (what v463 must buy): 3.7x pawn-death volume,
site discipline (88% on-bed vs our 60%), and active ramming as
the death channel (hitWall+hitSelf+hitOtherBody = 73% of winner
pawn deaths; our wall-channel is literally 0%).
