# 15. Portals economy bug (confirmed local + ladder)

Symptom: on Portals (512 tiles, xy symmetry) our entire team does 1-9 splits and
eats 1-9 pearls over 500 rounds — peak alive ~4-7, dragons just pace. Reproduced
locally (m3_queen portals-s0: A 1 split/1 pearl, B 4/9) and on ladder vs real
teams (m821965, m821968 vs calc: 4-9 splits/10-24 pearls; m821982 vs Sponge who
did 483 splits/1330 pearls — the food IS there, we just can't reach it).

Diagnosis hypothesis: portal-paired halves of the map are unreachable in our
fields — nb[c*4+d] = -1 for portals whose partner is unseen, so BFS targets
never route through. wPortalLoiter keeps dragons off portal-side tiles unless
crossing, and blind-portal danger (wBlind) discourages first crossings. Result:
we never learn portal partners, never reach half the map's pearl beds, starve
at ~4 alive. Coincidentally WINS vs suicide-meta opponents because our len-3
queen hides while their queen dies fighting.

Fix candidates (untested): (a) treat unknown-portal nb as passable-with-penalty
for BFS routing so targets resolve; (b) an early scout rule — send 1 unit through
each seen portal to learn the partner; (c) drop wBlindQuiet enough that blind
crossings aren't vetoed. Test vs local portals first, then challenge-battle on it.
