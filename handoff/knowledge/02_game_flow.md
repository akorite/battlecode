# Game flow — the four phases of an Abyss match

*Evidence: per-round event histograms + dragon-history curves across 59,544 games; eval trajectories on 25k+ scored games.*

## The universal arc

Every game follows the same curve: `explode → collide → consolidate → crown`. The phases are separated not by time but by **what limits each one** — and each phase has a distinct killer question.

```
Progress:   0%        25%          50%          75%        100%
            |---------|------------|------------|----------|
Phase:      Expansion  Collision    Consolidation  The bell
Question:   "how big   "who owns     "whose swarm   "who is
             can we     the middle"   converts"     longest"
             get?"
```

## Phase-by-phase with data

### Phase 1 — Expansion (0–30%)

Split volume rises monotonically through this phase, peaking at ~35% progress (1.57M splits per 5%-bucket globally). Deaths are at their lowest *rate* relative to dragons-alive — each team is mostly playing against empty board, not each other. Sonar traffic is already heavy (~40–116M pings/bucket) because the swarm is mapping, not fighting.

**Winner-loser divergence starts at 10%:** winner's swarm is +0.8 dragons by 10% progress and +2.9 by 20%. That sounds small; the bceval model reads it as a win-probability edge of 51% → 60%. By the end of this phase the eventual winner has already built a statistically meaningful lead — the first-30% split pattern effectively decides the board.

### Phase 2 — Collision (30–60%)

The hinge. Free space runs out mid-way through this phase; splits plateau then decline (1.57M → 1.48M/bucket), deaths peak at ~45–55% (1.44M/bucket — the corpse production maximum), sonar reaches its absolute maximum (~146M pings/bucket at 55–60%) as the swarm is densest and fighting hardest.

**This is where the game is won:** the winner-loser gap explodes from +5.4 to +12.8 alive dragons between 30% and 60% progress. By 50% the eval model already prices winners at 67%. Mid-game territory differential is the cleanest signal in the whole dataset (+250 tiles for winners at 50%).

Median first blood is ~round 16 — but first blood predicts nothing (51% of first-dead teams still win). It's *sustained* attrition that kills, not losing a dragon.

### Phase 3 — Consolidation (60–85%)

Both swarms shrink — splits drop by half, deaths stay high. The swarms are deliberately dying off: this is where suicide-economy teams cash in (mass → pearls → champion eats). Winners plateau ~32 alive; losers collapse steadily from 17 → 11.

Eval spread doubles (0.23 → 0.34): the outcome becomes legible to the model. Practical threshold: a swarm below ~15 alive at 80% progress is almost never coming back.

### Phase 4 — The bell (85–100%)

~58% of games reach ~round 500. Everything before was scoring for one number: your single longest dragon. Deaths drop off (both sides have less swarm left to kill), winners' eval P hits 88.8%.

Comebacks exist — 16% of winners were below 30% P at some point — but late reversals are exceptional. The biggest recorded eval swing in a single 50-round interval is around +0.4 P.

## The curves, side by side

| Progress | Winner alive | Loser alive | Gap | Winner P | Splits/bucket | Deaths/bucket | Sonar (M) |
|---|---|---|---|---|---|---|---|
| 0% | 3.6 | 3.6 | 0.0 | 51% | 0.93M | 0.45M | 38 |
| 10% | 11.6 | 10.8 | +0.8 | 56% | 1.12M | 0.73M | 60 |
| 20% | 18.5 | 15.6 | +2.9 | 60% | 1.40M | 1.01M | 82 |
| 30% | 23.7 | 18.3 | +5.4 | 63% | 1.57M | 1.33M | 116 |
| 40% | 27.6 | 19.7 | +7.9 | 65% | 1.57M | 1.44M | 131 |
| 50% | 30.6 | 20.0 | +10.6 | 67% | 1.48M | 1.43M | 139 |
| 60% | 32.2 | 19.4 | +12.8 | 69% | 1.37M | 1.38M | 146 |
| 70% | 31.8 | 17.2 | +14.6 | 72% | 1.05M | 1.12M | 112 |
| 80% | 29.0 | 13.6 | +15.4 | 77% | 0.60M | 0.80M | 68 |
| 90% | 26.0 | 10.7 | +15.3 | 89% | 0.43M | 0.51M | 45 |
| 100% | 23.2 | 7.5 | +15.7 | — | — | — | — |

## What "flow" means at elite level

Elite teams shape the phases deliberately:

- **forgot to mention** compresses Phase 1–2 — suicides spike earlier than the field's, banking the corpse economy while everyone else is still expanding.
- **cheji bt** runs a two-generation swarm — first wave farms and dies (alive dips at 65%), second wave eats and finishes (regrows to 26 by end).
- **PPP** overshoots Phase 1 — peaks 30 alive at 50%, then crashes to 19 (over-extension), riding the crash into a fed champion.
- **Sponge** flattens the whole arc — keeps a modest swarm alive the whole game, concedes Phases 2–3, wins at the bell.
- **Cache me outside** never leaves Phase 1 — flat ~31 alive from 55% onward; perpetual expansion, no consolidation.
