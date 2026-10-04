# QSIEGE lane — mid-game queen-siege defense

Lane: mid-game queen encirclement deaths (h2h/hitWall r50–450, all-4-exits-blocked).
Bot: `workspace/abyss_qsiege`, rebased onto `abyss_v113` mid-lane per coordinator
(v112 for the first two gates, v113 after).

## Verdict: NEGATIVE — nothing ships

Every formulation of "exit-freedom scoring" was evaluated and either lost the
gate or proved behavior-inert. The lane hypothesis — that local per-move scoring
can prevent these deaths — is falsified inside this architecture: the seal/ram
develops faster than scoring reacts, the swarm already covers what it can, and
any queen-side penalty costs more fights than it saves. Details below so the
next lane doesn't repeat the dead ends.

## Diagnosis (29 ladder replays, 22 our-queen deaths, 19 mid-game)

Tool: `devin/lanes/qsiege_diag.py` (tracks bodies round-by-round, classifies the
death cell's blockers and the queen's free-exit history).

| class | n | signature |
|---|---|---|
| encircled | 8 | exits ≤1 for ≥3 of last 6 rounds + enemy within 6 |
| pocketed | 6 | same geometry, no enemy within 6 |
| rammed | 7 | straight h2h, exits fine until the end |
| fade | 1 | slow bleed |

Blockers of her final cell: kelp 1–4, **own body 1–3, friendly bodies 0–3, enemy
≈0**. Enemies press from 2–6 out but almost never seal directly — the proximate
seal is kelp + her own coil + *her own escort*. Reachable region stays ~200 cells
until 1–2 rounds before death, so the seal is sudden/local: invisible to `trapOn`
(static walls) and the `space<need` cliff (fires too late by construction —
survival-lane found ~85% of fatal positions were entered with it already true).

Coordinator steering intel (426 top-team replays): 94% of queen deaths are a
len2-3 enemy steering into her with ZERO allies within 3 tiles; she initiates
~6% of fatal contacts. Median ram round ~131.

## Variants evaluated (all same lane item: exit-freedom / cover scoring)

### F3 — queen pays for fragile exits, ungated — gate 39.8% ❌
`danger += wQSiege * max(0, 2 - (exits - fragile))`, fragile = exit already
touching a foreign head (either team). Gate vs v104 (22 maps × s0-1 × both seats):

- 35/88. New 0/4s vs v108's known zeros: devil, stripes, tower_defense, unsw.
- Queen-side metric did improve (median death r143 vs v104 r96; non-ram 0.341 vs
  0.398/g) but wins moved the wrong way.
- Fail mechanism: the charge fires while her escort surrounds her — it can't
  tell protection from seal, so it pulls her off the screen on combat maps and
  she gets rammed alone. Small-map econ also sagged (splits r60: 10.6 vs 13.3).

### F4 — F3 gated by `enemyDist_[dest] <= 4` — gate 43.2% ❌
Only charge when an enemy head can actually exploit the plug. Recovered
devil/stripes/tower/autarky to seat-splits, but slithery/islands/australia went
back to v112-baseline losses (the term is inert wherever no siege geometry
exists). BIG maps 16/48 = 33% — v112's own baseline weakness, not the diff.

### G1 — swarm-side exit reservation — smoke only, inert
Teammates pay to step into one of the queen's last-2 exits (extends the existing
"never take a teammate's last exit" INF to threshold 2 for her). Smoke: identical
to F4's results everywhere it could fire (islands bit-identical; only weakhold
lens moved, still won). The condition — queen's exits ≤2 while a teammate wants
one — is rarer than the kill geometry.

### R1 — queen avoids uncovered+reachable tiles — smoke 16.7% ❌ (v113 base)
Per coordinator intel: `enemyDist_[dest]<=1 && friendDist_[dest]>3 → +wQSiege`.
At the front every tile is reachable and uncovered when she leads, so she just
retreats; devil/stripes/tower all went 0/2 (worse than seat-splits).

### R2 — threat-triggered ally cover bonus — inert (final shipped code)
Escorts get `-wQSiege` for ending within cheb `qSiegeCover` of our queen when an
enemy (visible `enemies_` or relayed `heardEnemies_`) is within BFS 3 of her and
≤1 ally already covers her. At wQSiege=1 and 3, cover 3 and 4: **bit-identical
replays to v113 in every smoke game** — the trigger never occurs. When she's
threatened the swarm is already there; when she's alone there's nobody close
enough to answer. Even the "don't plug her exits" geometry doesn't arise:
the escort is at ring-3, not inside.

## Baseline-attribution caveat (important for the integrator)

`abyss_v113` itself goes **0/6 vs abyss_v104 on devil, stripes, tower_defense**
(bit-identical losses to every qsiege run — verified). wh4's trap-scan fires only
on small maps (`trapMaxTiles`) and pins the queen: splits by r60 collapse
2.8 vs 12.3. v113's small-map regression makes the "vs v104" gate structurally
unwinnable for any v113-descendant; qsiege-vs-v113 is the honest comparator.

Same phenomenon on v112 lineage: unsw/trauma losses are bit-identical between
qsiege and v112 — inherited, not introduced.

## Full gates

| cand | base | score | notes |
|---|---|---|---|
| F3 (v112 base) | v104 | 35/88 = 39.8% | escort-pull, new 0/4s devil/stripes/tower/unsw |
| F4 (v112 base) | v104 | 38/88 = 43.2% | inert where no siege; BIG 33% = v112 baseline |
| R2c (v113 base) | v113 | RUNNING (gate3) | expected ≈inert per 3 inert smokes |

## Queen-death-rate deltas

| batch | cand qDead/game | base qDead/game | cand median death r | base median |
|---|---|---|---|---|
| F3 gate vs v104 (88g) | 0.864 | 0.875 | 143 | 96 |
| F4 gate vs v104 (88g) | 0.864 | 0.795 | — | — |
| R2 vs v113 (12g attrib) | 0.750 | 0.750 | identical metrics | |

## What would actually help (for whoever takes this next)

- The kill is positional and decided 1-3 rounds out, but per-move scoring only
  sees this turn. Options with real depth: plan-level reservation (mark tiles
  that keep her ≥2 exits into HER multi-step plan, not one move), or a relayed
  "queen under threat" beacon that pulls escorts from beyond vision — my cover
  term can't see her unless a teammate already can.
- The wh4/small-map regression in v113 is worth its own look independent of
  this lane — it costs more games than queen-siege does.
