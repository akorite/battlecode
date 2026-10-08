OPENING DOCTRINE r0-80 — top-8 vs our live build
=================================================
Corpus: 40 top-8 ladder replays (46 top side-obs: aAah/larp/Cultery/
devtest/chadgdp/hieroglyph/forgot/Sponge), 20 Cognoscenti ladder
games (our live flagship — "v424" not on any box/branch; newest on
devin/v120 is v341, ladder replays ARE the live build), 52 opp
side-obs. Eats = hasPearl->False nearest-head attribution.
Analyzer: tooling/opening_doctrine.py.

1) SPLIT TIMING
   first-split (med):  top 1   ours 7   opp 1
   per-map matched (same maps): top ≈ ours everywhere starters
   allow it (r1 both sides on Autarky/Maze/Trauma/weakhold/Australia/
   Around UNSW/Schooltime). Pooled med-7 was MAP-MIX, not a defect —
   our r1 opener already fires when starters are len>=4.
   splits by r80 (med):        top 29   ours 6   opp 19
   same-map splits80 (top vs ours):
     Australia 53/5 Portals 80/6 Stripes 26/4 Trauma 24/3.5
     weakhold 15/2 Trophy 13/6 Autarky 42/25 Maze 31/19
     Around UNSW 82/56  (Schooltime 11/16, TD 2/1 — elim maps)
   => the gap is POST-OPENER cadence, not the opener: they re-split
   2-4x faster on every economy map. Same conclusion as the intake
   census: cycle time = time-to-eat-back-to-L4.

2) ROAM FROM BIRTH r0-40 (per unit-round, tcheb to own birth cell)
                 med      p75       p90
   top   3->6->6->6   4->8->10->10  6->11->13->15
   ours  3->7->8->8   5->9->10->11  6->11->13->15
   opp   3->5->5->5   4->9->10->10  6->11->14->14
   OUR WORKERS ROAM FARTHER (r21-40 med 8 vs their 6). Not a
   p90 difference — we have a few deep roamers like them — but a
   25-50% median shift: our whole forage class walks farther.

3) CONTESTED BEDS (enemy head <=3 of pearl cell at eat round)
              eats80  contested-wins  enemy_d@eat  opp-near-losses
   top        4083      28.0%           med 6        31.7%
   ours        516      26.6%           med 6        22.8%
   opp        3944      31.5%           med 5        29.0%
   NO CONTEST ASYMMETRY: ~27-32% of everyone's eats happen within 3
   of an enemy head — top teams do NOT yield beds and do NOT take a
   worse contest rate than us. enemyCloserFactor 0.85 produces the
   same contest share as the field; the deficit is VOLUME (516 vs
   4083 eats80), not contest avoidance. No diff needed on the
   contest axis itself.

4) DEEP FOOD vs CRUMBS (eat depth = birth-cell -> eat-cell)
   eat-depth med (r1-20/21-40/41-60/61-80):
   top   3 / 4 / 3 / 3   p75 ~6-9   (~75% of eats within 6 of birth)
   ours  5 / 7.5 / 5 / 6 p75 ~9-12  (~50% within 6)
   opp   3 / 3 / 3 / 3   p75 ~7-8
   WE EAT DEEP, THEY EAT LOCAL. Top teams' stubs stay in a ~6-cell
   halo and convert the nearest crumbs; ours walk 2x farther per
   eat. Deep-foraging = travel tax = the starvation@60 gap (58% vs
   42%) measured in the intake census.

IMPLEMENTABLE DIFFS (v424 context: leash-free r<150,
enemyCloserFactor .85, open_ off maze):

 A) CRUMB RADIUS on early forage scoring: for r<~80 (or while
    unit age<40), multiply target value by decay on
    tcheb(birthCell,cell) beyond ~6 — e.g.
      if (r_<80 && age_<40) score *= min(1.0, 8.0/max(dBirth,8));
    Cheap alternative: hard radius — only consider pearls with
    dBirth<=10 unless none exist. Targets our med-8 roam / med-6
    eat-depth down toward their 6/3. Expected: higher eats80
    throughput per unit (their 89/side-game vs our 26).

 B) RE-SPLIT cadence audit, not a code diff: same-map splits80
    2-4x short (Portals 6 vs 80!). Before touching split policy,
    verify no population/round gate throttles re-splits in r0-80
    (any maxUnits/alive-cap style check, enemy-veto on open maps,
    or trySplit preconditions that delay past L=4 contact). The
    measured recipe allows a re-split EVERY time a unit re-hits
    L=4 — their bins ramp [211,103,168,197,224,244,271,300]
    (46 side-obs) vs ours flat [36,12,20,20,25,40,33,35] (20).
    If policy is clean, this is downstream of forage depth (A).

 C) Do NOT build a contest-diff: contest shares match (26.6% vs
    28.0%), and enemyCloserFactor already yields parity. Spend
    the effort on A+B.

CAVEATS: roam/depth numbers are pooled (map mixes differ) —
direction is robust but magnitudes approximate. 'contested'
defined by enemy distance at eat round, not approach-time
equidistance; close enough for the yield/contest question asked.
