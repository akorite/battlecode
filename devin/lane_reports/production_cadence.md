# Production cadence forensics — top-8 vs Cognoscenti (v424-era ladder)

Corpus: `ladder_top/` 30 seated replays vs top-8 (aAah 2555,
forgot-to-mention 2479, horse 2458, Cutlery 2440, larp-stock 2435,
dev-test 2386, SSS 2335, chad gdp 2385, 𓎼𓃭𓅱𓂋 2292, WeHaveQuizzes ~2294)
vs `ladder_us424/` 20 seated replays (team 351 current live build).
Tooling: `devin/lanes/prodcad.py`. Sides identified via match API seats.

## (1) Parent regrowth — rounds until the same parent splits again

| era | top-8 | their opponents | us (v424) | our opponents |
|---|---|---|---|---|
| r0-120  | 6  (p25 3, p75 14) | 6  | **7**  | 7  |
| r120-300| 10 (p25 4, p75 26) | 9  | **15** | 9  |
| r300+   | **8** (p25 4, p75 25) | 8 | **25** | 8  |

The decisive row: era2 resplit median **8 vs 25 — we take 3x longer**
to cycle a parent back to split length late-game. Every opponent in
both corpora runs ~8r in era2; we alone sit at 25r. Mechanism: their
parents regrow by eating conveyor drops in-blob (drop-recycling); ours
re-forage pearls over distance. Our budAlive=18 floor also parks
parents holding length for bud instead of splitting at threshold.

## (2) Child birth length + first-split delay

| child len | top-8 (n=~10k) | us (n=~2.2k) |
|---|---|---|
| 2  | 64% | 84% |
| 3  | 13% | 2%  |
| >=4| **22%** | **10%** |
| >=8 (deep tail) | ~4% (400+) | ~1% |

Their splits halve LONG parents (len 8-15 -> len 4-7 children, split-
ready at birth); ours are len-2 dominated — the bud path produces only
~10% len>=4 despite being designed for exactly that.

## (3) Split location — inside the fight, not the territory

| metric | top-8 | us |
|---|---|---|
| d(child spawn, parent birth cell) | 3.0 | 5.0 |
| d(child spawn, own centroid) | 11.0 | 13.0 |
| d(child spawn, nearest enemy head) | **0.0** (mean 1.2) | **0.0** (mean 1.3) |

Both sides split inside the scrum (median enemy distance = 0 — the
child literally spawns adjacent to enemies). Not a differential, but
confirms children-as-ammunition is the standard regime; ours split
slightly farther out (5 vs 3 from parent birth — consistent with our
spread-out forage style).

## (4) Unit-count trajectory (alive dragon-rounds per 50r bucket, summed)

| bucket | top-8 | us |
|---|---|---|
| r0-50   | 13414 | 5475 |
| r50-100 | 27056 | 10821 |
| r100-150| 36600 | 15324 |
| r150-200| 41072 | 16430 |
| r200-250| 42892 (peak) | 17417 |
| r250-300| 40420 | 18367 (peak) |
| r300+   | ~35k  | ~17k |

Saturation at ~90% of peak: them r150-200 bucket, us r200-250+ — and
their plateau is **2.4x our volume**. Their swarm fills to engine cap
by mid-game; ours never gets close.

## Gate recommendations (relax/tighten)

1. RELAX keepFloor/budAlive-hold in era2+: our parents idle at
   keep-length holding for bud while theirs re-split every ~8r.
   Bud opportunistic only (len>=10?), never block a len-4+ split.
2. RELAX the late-game feed ban / harvest gates that stop splits —
   their cadence continues to the cap; ours throttles at exactly the
   era the conveyor should be cycling parents.
3. TIGHTEN nothing on split cadence itself: len-2 children are the
   standard unit on both sides; the lever is cycle speed + in-blob
   drop intake, not child size or spawn position.
4. Child-size upside comes free: if parents split at len>=8 instead
   of holding for an explicit bud, the len>=4-children share rises
   toward their 22% naturally — same gate as #1.
