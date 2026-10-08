# Elim-class opening melee — what winners do in r0-80 that we don't (autarky lane)

Data: 9 small-map ladder losses with replays — vs 😹 (1826: Trophy, Portals,
Devil, Trauma), Z-A (1678: Trophy m1443065 elim@r74, Autarky m1443064),
Git Gud (1543: Autarky), Average Individuals (1628: Trauma), Quantify (1563:
weakhold). Analyzer: analysis/elim_opening.py. Windows: r0-80.

## The recipe: a pawn-donation loop, not melee skill

**1. Production gap is the whole story — they make 3.5× the children.**

splits in r0-80, per-bucket totals across the 9 games:

| bucket | WINNER | US |
|--------|--------|-----|
| r0-19  | 33  | 31 |
| r20-39 | 72  | 16 |
| r40-59 | 97  | 26 |
| r60-80 | 107 | 15 |

Same start (33 v 31 in r0-19), then we stall while they accelerate — children
per game med 34.3 vs our 9.8. Their workers resplit repeatedly; the swarm
self-refuels (below).

**2. Winners' children are suicide pawns — via hitWall/hitSelf, NOT h2h.**

Winner death reasons r0-80 (per-game means): hitWall 18.6, hitSelf 7.8,
h2h 6.9, other 2.8. The wall/self deaths are deterministic on-demand kills:

| game (winner) | suicides r0-80 | own-adj med | ≤2 | same-team drop eats |
|---------------|----------------|-------------|----|---------------------|
| Z-A Autarky | 38 hitWall | **1.0** | 100% | 151 cells |
| 😹 Portals | 30 (27 wall + 3 self) | 3.0 | 40% | 42 |
| AI Trauma | 20 | 3.0 | 35% | 63 |
| 😹 Trauma | 20 | 3.0 | 35% | 63 |
| Quantify weakhold | 13 hitSelf | 3.0 | 31% | 31 |
| 😹 Devil | 6 hitWall | 1.0 | 100% | 6 |

A shed-2 child walks into a wall (or U-turns into its own body where walls
are absent — weakhold) at adjacency 1-3 to allies: its 1-2 pearls land inside
the swarm and are eaten same-team immediately (every same-team eat ≥1 drop
cell per suicide; Z-A converted 151 pearl-cells). Cost of a pawn: −2 length on
the parent, +1 pearl dropped… net-zero on paper BUT the pawn's death ALSO
feeds the resplit cadence — drops land ON allies, eaten by the queen/mid
dragons, who resplit again. It's a pearl pump driven by on-demand death.
Our suicides: ~2/game (accidental).

**3. Our children die the wrong way — into enemy teeth.**

Children dying ≤15r after birth by h2h (ramming an enemy head):

| game | our h2h≤15r share | winner h2h≤15r share |
|------|-------------------|----------------------|
| Trophy vs 😹 | 47% (7/15) | 7% (3/43) |
| Trophy vs Z-A | 67% (6/9) | 21% (10/42) |
| Devil vs 😹 | 29% (2/7) | 9% (3/33) |

Our pawns get eaten by the enemy (our death-adjacency: med 1 to ENEMY) —
their drops feed the opponent's melee. Winners die adjacent to their OWN
units (own-adj med 2-3) — enemy can't collect those drops.

**4. Intake follows production — eaten 4×.**

Pearls eaten per bucket (attributed by acting turn), medians per game:
W r20-39: 20, r40-59: 20, r60-80: 24 — sustained 1 pearl/round. US: 6, 5, 4 —
decaying. (Most tileChange pearl-offs are NATURAL DESPAWN on beds — no head
on cell; real eats are the inside-turn offs.)

**5. Queen cadence:** winners' queens split at r0 (4/9) then ~9-17r spacing
(Z-A Trophy: 22,31,38); ours similar count but later spacing and she never
becomes a production engine (18,21,40 — then dead at ~r60 in elims).

**6. Two losses had ZERO our-deaths r0-80** (Trauma NC1152, weakhold NC600) —
not melee at all: the winner made 19-27 children while we made 2-3 and the
game was out-scaled, not out-fought. On these maps the elim "loss" is a slow
production deficit.

## Concrete mechanics to port

1. **Pawn-donation opening**: on elim-class boards, shed-2 children whose job
   is to die by hitWall (or hitSelf U-turn) at adjacency ≤2 of the swarm/
   queen within ~15r. This is strictly better than our current h2h pawn deaths
   (same death, pearls go to US not THEM). On-demand wall deaths are the
   primitive — no nva-boxing needed, works r0 onward, maps with interior
   walls only; hitSelf is the fallback on wall-poor boards.
2. **Never h2h-seek with fresh children**: our children engage immediately and
   47-67% die h2h inside enemy reach. Their children don't fight at all
   (h2h≤15r 3-21%) — they die to walls, not heads.
3. **Queen r0 bud + resplit pressure**: winners' queens keep splitting
   (~9-17r spacing through r80). Ours buds once then stalls/dies.
4. **Production is the elim bottleneck** — 3.5× child count by r60-80 is the
   whole gap; the melee outcome follows from numbers, not positioning
   (their death-adjacency isn't better, just denser).

## Caveats
- 😹 games went to r499 (Portals/Trauma were decided by length, not elim) —
  the pattern holds on the true elims (Trophy r74/104, Devil r130).
- "Suicide" is inferred from systematic wall/self deaths at own-adjacency ≤3
  with instant same-team pickup — could theoretically be extreme pathing
  incompetence that happens to be perfectly recyclable, but 38/game at
  adj-1 with 151-cell conversion is deliberate.
- NC≤700 filter: Trauma (1152) and Autarky (972) exceed it but were in the
  loss set anyway; kept for breadth.
