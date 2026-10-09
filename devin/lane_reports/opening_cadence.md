# Opening cadence bisect — elim maps, r0-90

Corpus: 17 small-map ladder replays (replays144/: Trophy×3, Devil×2, PD×4,
weakhold×3, TD×2, qOS×1, Stripes×1) — 10 seat-A + 7 seat-B, incl. the cited
m1443065 (Trophy vs Z-A 1678, loss). Record: 6W-11L. Live bot = abyss_v449
(= v447 gates + universal queen hide). Analyzer: devin/lanes/opcad.py.

## Where the gap opens

Every loss shows splits@60 deficit; no win does (us → them):

| result | splits@60 us | splits@60 them |
|---|---|---|
| 11 losses | 0,0,0,2,4,4,7,7,7,9,11 (med ~4-7) | 5,11,13,20,20,21,22,24,24,25,30 (med ~21) |
| 6 wins | 4,6,8,14,15,28 | 0,2,6,8,17,0 |

Quoted Trophy number confirmed: m1443065 = 9v30 by r60; m1440441 = 11v24.

Per-10r buckets (all 17g summed, us / them):

| bucket | alive us | alive th | splits us | splits th | eaten us | eaten th |
|---|---|---|---|---|---|---|
| r0-9   | 347 | 335 | 23 | 22 | 15 | 13 |
| r10-19 | 415 | 379 |  9 |  9 | 22 | 25 |
| r20-29 | 507 | 467 | 16 | 21 | 45 | 55 |
| r30-39 | 609 | 558 | 14 | 26 | 58 | 45 |
| r40-49 | 710 | 674 | 20 | 30 | 55 | 57 |
| r50-59 | 789 | 760 | 21 | 35 | 88 | 59 |
| r60-69 | 868 | 895 | 22 | 38 | 69 | 83 |
| r70-79 | 922 | 936 | 22 | 33 | 64 | 76 |
| r80-89 | 895 | 960 | 17 | 33 | 50 | 65 |

r0-20 is symmetric (queen bud phase, 23v22 and 9v9). **The gap opens r20-60** —
their worker generation kicks in (21+26+30+35 = 112 vs our 16+14+20+21 = 71)
and never closes. Alive counts stay near-parity: our extra units die as fast as
theirs arrive (they churn ammunition; we lose producers).

## Mechanism counters

- Per-unit intake r0-90: **7.57 vs 7.88 eats/100 unit-rounds — parity**. Food is not it.
- Map coverage: mean unique tiles **267 vs 261** — not exploration.
- Queen bud cadence (rounds between queen splits): **us median 1.0, them 2.0** —
  our queen buds MORE often (keepBase=min(.,2) while bud_&&r<100 already maxed).
- Worker first-split: median r18 vs r19 (mean 20.1 vs 13.7) — near parity.
- Children born split-ready (len≥4 at birth): us 9/164 (5%), them 5/248 (2%) —
  we bud more quality, they produce 1.5× more children.
- Deaths ≤90: us 118 {h2h 68, hitSelf 28, body 17, wall 5};
  them 110 {h2h 66, self 28, wall 13, **body 3**}.
  Our friendly-geometry deaths (self+body) = 45 vs their 31 (+45%); on elim
  maps our own swarm kills us ~6× more via hitOtherBody (17 vs 3).
- Dead-unit lifetimes ≤60: in losses ours die at median ~7-15r vs theirs 18-29r —
  they kill our young workers; our kills land on their older units.
- splitEnemyDist exposure proxy: enemy head within cheb-1 of a unit head on
  **6.7% (us) vs 7.0% (them) of unit-rounds r0-60 — symmetric**.

## Resplit cadence (r0-90, observed parent→next-split intervals)

The quoted "winners resplit 16-17r vs our 22-24r" does NOT replicate on this
corpus — measured medians are far tighter and near-parity:

| metric (r0-90) | us | them |
|---|---|---|
| queen resplit interval | 6 (n=33) | 10 (n=33) |
| worker resplit interval | 6 (n=65) | 7 (n=115) |
| worker age at FIRST split | 9 (n=87) | 7 (n=218) |
| workers reaching first split | **87** | **218** |

Mechanism: per-surviving-parent cadence is equal (6-7r). The volume gap is
**first-split eligibility — 218 vs 87 workers ever reach len-4**. Ours die at
len 2-3 before their first split; theirs survive the first threshold, then
resplit at the same pace we do. It is one flywheel, not two rates: more
len-4 survivors → more splits → more children → more future parents.

## open_ correction (v457 test result)

The earlier openUntil=0 finding does NOT carry to this lineage: abyss_v457
(open_ disabled on v449) lost to real opponents — 53% vs the 62.7% v376
control. The forage-first opening is net-positive on elim maps on the v449
lineage; keep openUntil=48 (map-gated). Recorded as a do-not-retest in the
reverse direction.

## The v449 split gates (read from workspace/abyss_v447 = v449's gates)

- worker: `L<swarmSplitLen(4)` reject; `L>=swarmBudLen(6)` → bud len-4 child
  (parent keeps 2), else halve.
- grower/queen: `keep = keepBase + round/60`, keepBase 4→min(2) while
  bud_&&r<100; `n = growerChild(2)`; champ stops budding at queenBudUntil 450.
- `splitEnemyDist=1` veto; `budAlive=18` breed phase; unitLimit/feedRound
  irrelevant r0-90.

## Verdict: which gate delays us most on a 625-tile map

**None — the delay is upstream of every gate.** Our queen already buds at
median cadence 1.0 (their 2.0): keepBase-min-2 is fully open. Worker
first-split is r18-19 both sides: swarmSplitLen=4 is reached on schedule the
FIRST time. splitEnemyDist=1 vetoes both sides identically (6.7% vs 7.0%).
growerChild=2 matches their len-2-churn child profile.

What actually delays us: the SECOND and later splits. Parents that survive to
len-4 split fine; the deficit is that after r20 our workers die at len 2-3
(h2h 68 + body 17 of 118 deaths) before reaching len-4 again, while theirs
live to resplit — their children are ammunition that dies AT the front, ours
are producers that die BEFORE it. Child quality is inverted (we bud 5% len-4
vs their 2%) and still lose volume — identical to the whole-line finding:
mass retention to len-4, not any gate, is the binding constraint.

If a gate must be named closest to the delay, it's `swarmSplitLen=4` — not
because it rejects (parents die before reaching it) but because len-4 is the
exact threshold our len-2/3 dead never cross. A len-3 split rule wouldn't fix
it: children would be len-1/2 fodder and the dead-parent pool would shrink
faster. The fixable surface remains parent survival past len-3 in the
contested corridor (closed: in-reach dodge, pre-contact ring, spawn timing —
all falsified) or a production form that doesn't route through len-4 workers
(e.g. direct queen throughput — her cadence is already maxed, so no headroom
there either).

The one asymmetric number worth chasing: **hitOtherBody 17 vs 3**. On elim
maps our bodies kill our workers ~6× more than theirs do — scrum density
kills us, not the enemy's economy. That's geometry of OUR swarm, not a split
gate.
