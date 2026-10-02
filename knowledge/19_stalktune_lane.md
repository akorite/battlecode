# STALK-TUNE lane report — assassin-squad param sweep (bc_workspace5)

Date: 2026-10-02. Lane: tune the v99 assassin-squad params vs `abyss_st` (v99) and
`abyss_hd2` (v98). All batches: `match.py`, maps `trauma,slithery_fight,autarky`,
seeds 0–4 both sides, 30 games per A/B unless noted. Sandbox is deterministic;
"inert" below means bit-identical replays (all same-side deltas exactly 0).

## 0. Baseline sanity — REPRODUCED

`abyss_st` vs `abyss_hd2`, trauma+slithery_fight, seeds 0-4 both sides (20g):

| map | st W-L |
|---|---|
| trauma | 6-4 |
| slithery_fight | 7-3 |
| **total** | **13-7 (+6 net)** |

Matches the expected ~+5. Same-side deltas vs hd2: longestDragon +3.25,
totalLength +3.15, queenLength +1.05 — v99 wins on the champion/tiebreak axis.

## 1. One-at-a-time sweep vs abyss_st (30g each)

| param | value | autarky | slithery | trauma | **total** | verdict |
|---|---|---|---|---|---|---|
| assassinCount | 2 | 5-5 inert | 5-5 inert | 4-6 | **14-16 (46.7%)** | worse |
| assassinCount | **4** | 5-5 inert | 5-5 inert | 6-4 | **16-14 (53.3%)** | best (sub-60%) |
| assassinCount | 5 | 5-5 inert | 5-5 inert | 6-4 | **16-14 (53.3%)** | = K4 |
| assassinMaxDist | 10 | 5-5 | 5-5 | 5-5 | **15-15 inert** | inert |
| assassinMaxDist | 24 | 5-5 | 5-5 | 5-5 | **15-15 inert** | inert |
| assassinForce | 0.3 | 5-5 | 5-5 | 5-5 | **15-15 inert** | inert |
| assassinForce | 0.8 | — not run (session stopped) | | | | |
| assassinMaxAge | 3, 9 | — not run (session stopped) | | | | |

**Nothing reached the 60% bar.** No param change is a verified win; K=3 stays
the default by the rules of the sweep. `assassinCount=4` is the best-scoring
candidate (53.3%, tied with K=5) — worth a retest on more seeds before shipping;
it was NOT combo-tested (the combo run requires ≥60% winners, none existed).

Key same-side deltas (n=30):
- ac2 (K=2): queenDeathRound -6.6 (own queen dies sooner), queenLength -0.3 — a
  2-dragon squad is too weak to force h2h and costs screen mass.
- ac4/ac5 (K=4/5): queenDeathRound +10.5/+11.6, queenLength +0.83/+1.03,
  splits/steps slightly down — a 4th member protects the push better; identical
  score for K5 (4th+ members are the marginal squad, not the whole swarm).
- md10/md24/af03: every delta exactly 0.00 — genuinely inert. Squads that
  activate are always within cheb 10 of the report cell; the force gate
  (combined len ≥ rep.len×0.5) never binds at 0.3 either.

## 2. Failure-mode check — PASSED

"Squad strips the screen on report-free maps": **no**. On slithery_fight and
autarky (few/no queen reports in these seeds) EVERY variant produced
bit-identical replays vs abyss_st (identical win margins both directions —
e.g. autarky s4: A wins 24-14 in both orientations for every variant). The
squad is provably inert when no role-1 report exists; it cannot bleed mass.
Trauma is the only map in this set where the mechanism activates at all —
and it is also the only map where any variant moved W-L.

## 3. Sonar / steering findings (implemented, UNTESTED — session stopped)

Protocol read (`policy.hpp:emitSonar`, `world.hpp` inbox):
- Per dragon per turn: 1 beacon ping (rotating dir) + ≤1 enemy report aimed at
  the closest ally on a ray. Queen already preferred as report subject and
  carries `isQueen` flag → role-1 heardEnemies feed `assignAssassin()`.
- heardEnemies dedupe: same cell within 4 rounds keeps the FIRST report (no
  refresh) — a stationary queen's fix goes stale up to 4r; a moving queen lands
  a fresh entry per new cell.
- So a queen-flagged packet currently reaches only teammates on ONE ray; the
  fix cannot outrun vision range without a relay.

Built `abyss_stx` = `abyss_st` + generalized emit behind two new params
(defaults reproduce current behavior — VERIFIED bit-identical: stx-vs-stx
mirror on arena/seed0 == st-vs-st, 1389 events, same result):
- `queenPingDirs` (default 1): when the seen foe is the enemy queen, send the
  report on the N nearest ally rays instead of only the closest.
- `queenRelayAge` (default 0): when the queen isn't visible, re-emit the
  freshest role-1 heard report younger than N as our own enemy packet —
  multi-hops the fix past the vision edge.
Planned tests (not run): `queenPingDirs=4` and `queenRelayAge=2`, each 30g vs
abyss_st. Prior deadend note: a generic 2nd enemy report/turn (abyss_se) was
already rejected 15-17 — the qbump is worth testing only because it's
queen-scoped (fires only when she is seen/heard, not every turn).

Sonar density: ours ~1.1/act in gstats (sonarPerAction) vs elite ~3.85 — the
gap is emit-side (2 pings/dragon/turn max). No completed variant moved it.
Benchmarks context: end-queenLength on trauma ~9-15 for the winners in this
set; splits/60r not recomputed here (killed mid-run).

## 4. Deadends added (this lane)

- assassinMaxDist {10,24}: inert — candidates always inside 10 cells when a
  fresh report exists.
- assassinForce 0.3: inert — the combined-length gate doesn't bind downward.
- assassinCount 2: mild regression (46.7%) — squad too weak, queen dies sooner.
- assassinCount 4,5: 53.3% each — best candidate but below the 60% ship bar.

## 5. Commands used

```bash
# baseline
python3 tooling/match.py --bots abyss_st abyss_hd2 --maps trauma,slithery_fight \
    --seeds 5 --tag tune_base --jobs 8
# each variant
python3 tooling/sweep.py --base abyss_st --variant 'assassinCount=4' \
    --maps trauma,slithery_fight,autarky --seeds 5 --tag ac4 --jobs 8
# scoring (same-side deltas control for side-lock)
python3 tooling/tunestats.py <tag>
```

Tooling note: `handoff/tooling/parse_replay.py` + `battlecode-eval/bceval/
mapdata.py` were missing from this bundle — re-implemented here (the .replay
format is packed Cap'n Proto; schema recovered from the unswbc replay-viewer
bundle). `tooling/tunestats.py` (new) aggregates per-map W-L + same-side
metric deltas; `results/<tag>/gstats.jsonl` caches per-game stats.
Sonar-variant code lives in `workspace/abyss_stx` (untested).
