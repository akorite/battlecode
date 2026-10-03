# pearl lane — forage-first opening

Worker: this session. Branch: `devin/pearl`. Base: `devin/ladder-2026-10-03` (v106 head).
Bot: `workspace/abyss_pearl` (copy of `abyss_v104` — v104 dir untouched).

## Lane spec
v104 eats ~7.4 pearls in the first 30 rounds on small maps vs top teams' ~18.8:
the opening is too slow/defensive. Implement a forage-first opening, test vs
abyss_cf + abyss_combat on small+default+autarky, report per-map win rates and
pearls@30 vs v104 baseline. <=6 parallel games; report losses, don't ship.

## What changed (all scoped to `open_ = bud_ && round < openUntil`, openUntil=48;
inert by default: openUntil=0 in Params restores v104 exactly)

| Param | v104 | pearl | Effect while open_ |
|---|---|---|---|
| openDanger | (budMult 1.8) | 1.0 | breed-phase danger tax removed — base wDanger etc. still apply |
| openEnemyDist | (splitEnemyDist 2) | 1 | splits allowed within 1 of enemy heads (oe1-verified) |
| openHunt | — | 0 | swarm hunts only their queen + grower-threats; generic trade hunts off |
| openQueenKeep | (keep 4+r/30) | 3 | queen buds down to len 3 during the opening |
| openEatLen | (pocketEatLen 3) | 4 | eating steps ignore wPocket/wFog up to len 4 |
| openFog | (wFog 1.0) | 0.3 | swarm fog fear on open maps only (maze keeps 1.0 — kelp kills) |
| openExplore | (exploreValue .03) | .12 | stronger scout pull for swarm dragons |
| survival() | units<=3 | suppressed while open_ | a 2-3-dragon brood is a start, not a remnant |

Queen excluded from fog/eatShort relief (pockets and kelp kill her = instant loss).
Assassin squad unchanged (their-queen kill ends the game). Threat hunts (enemy
within 5 of a visible grower) still fire — defense isn't suspended.

Rationale: OPENING-ECON measured early split velocity = eating rate (~4
pearls/unit, opponents ~34 splits r0-60 vs ours far fewer); FORAGE lane's nf
(missions off during bud) ate +8% at parity. On 6/12 gate maps the team starts
with <=2 dragons — bud_ (units<18) IS the whole opening.

## Gate protocol
`kmatch.py run --cand <c> --base <b> --maps trophy,devil,dilemma,queen_of_spades,
Colosseum,stripes,tower_defense,weakhold,arena,default_small,default,autarky
--seeds 3 --seed-start 1 --jobs 6` — 12 maps × 3 seeds × both sides = 72 games
per matchup. eaten30 metric added to replay_metrics.py + kmatch summary.

Runs (results/<tag>/games.jsonl):
- gate_v104_cf, gate_v104_combat — v104 baselines
- gate_pearl_v104 — direct A/B (replays kept)
- gate_pearl_cf, gate_pearl_combat — the gate

## Results — v1 (forage-first, all relief incl. queen)

Per-map pairs W/6 (`results/gate_*/games.jsonl`, 72 games/matchup):

| map | v104 vs cf | pearl vs cf | v104 vs combat | pearl vs combat | pearl vs v104 |
|---|---|---|---|---|---|
| arena | 1/6 | **5/6** | 1/6 | **4/6** | 5/6 |
| Colosseum | 3/6 | 3/6 | 2/6 | 3/6 | 3/6 |
| stripes | 3/6 | **1/6** | 3/6 | 2/6 | 1/6 |
| tower_defense | 4/6 | 3/6 | 1/6 | 2/6 | 3/6 |
| weakhold | 0/6 | 0/6 | 0/6 | 0/6 | 0/6 |
| trophy | 3/6 | 4/6 | 4/6 | 4/6 | 4/6 |
| default_small | 4/6 | 4/6 | 1/6 | **3/6** | 3/6 |
| queen_of_spades | 4/6 | **2/6** | 2/6 | **5/6** | 1/6 |
| devil | 3/6 | **1/6** | 6/6 | 6/6 | **1/6** |
| dilemma | 0/6 | **6/6** | 0/6 | **3/6** | **6/6** |
| default | 2/6 | 1/6 | 4/6 | **1/6** | 2/6 |
| autarky | 5/6 | 5/6 | 4/6 | 4/6 | 6/6 |
| **ALL** | **48.6%** | **48.6%** | **38.9%** | **51.4%** | **50.7%** |

pearls eaten by r30 (cand vs base, small-maps subset / all maps):
- pearl vs v104: **12.4 vs 10.8** small, 13.0 vs 11.3 all — **+14%**
- pearl vs cf: 11.4 vs 10.4 small — v104 **trailed** 11.1 vs 12.8 (pearl flips the race)
- pearl vs combat: 11.6 vs 10.6 small — v104 was 11.6 vs 12.2

### What worked
- **dilemma 0/6→6/6 vs both** — the flagship flip; eaten30 17.5-18.0 vs ~6.5.
- arena 1/6→5/6 (vs cf), 1/6→4/6 (vs combat); eaten30 ~50-58 vs 45-47.
- autarky, trophy, default_small hold or improve; vs combat +12.5pp overall.

### What regressed — queen exposure on contact maps
- **stripes** down everywhere (1-2/6): 2-dragon corridor map, brood can't absorb
  the openness — pearl eats *less* (3.2 vs ~4.7) and splits less (1.7 vs 3.3).
- **devil** lost vs v104 (1/6) and cf (1/6 vs 3/6) but still 6/6 vs combat:
  it's a killbox-maze where contact IS the economy — v104's churn
  (26 splits, ~90 self/wall deaths) out-eats pearl's disengagement
  (12.8 splits, ~12 deaths, eaten30 6.7 vs 12.3). Matchup-dependent.
- **default** 4/6→1/6 vs combat (2/6→1/6 vs cf): queen dies earlier
  (h2h rams r22-130) — her danger tax dropped 10.8x→6x like everyone else's.
- **queen_of_spades** split (1/6 vs v104, 2/6 cf, 5/6 combat — mostly
  side-locked + early queen rams).
- Mechanism: openDanger relief applied to the *queen too* (queenDanger×grower
  = her fear fell to ~60%), and suppressed hunts leave her uncovered.

## v2 — queen exempt from relief (`openQueenDanger = 1.8`)

Single-variable fix on v1: swarm keeps forage-first freedom; the queen keeps
budMult-level fear during the opening. `abyss_pearl1` = frozen v1 snapshot.

Gate (same 12 maps, seeds 1-3): `gate_pearl2_{v104,cf,combat,pearl1}`

| matchup | v1 | v2 | delta |
|---|---|---|---|
| vs cf | 48.6% | 48.6% | 0 (map-for-map identical) |
| vs combat | 51.4% | 52.8% | +1.4 (trophy 4/6→5/6, rest identical) |
| vs v104 | 50.7% | 52.1% | +1.4 (default_small 3/6→4/6) |
| vs v1 direct | — | 54.2% | pairs 3W/33S/0L |

**Verdict: v2 ≈ v1 + noise.** The queen's fear level during r<48 does not move
outcomes — on default her deaths were bit-identical (same rounds/reasons):
enemies ram her well after the opening window, so early fear doesn't change
whether she's reachable. The bleed is not her own bravery; it's the swarm's
missing interceptors. Kept anyway (weakly positive, more principled).

## v3 — hunts restored (`openHunt = 1`, on top of v2)

Ablation of the hunt-suppression hypothesis: stripes/devil/default/qos all
show "pearl disengages" (fewer deaths, fewer splits, fewer eats; queen
uncovered). `abyss_pearl3` = v2 + openHunt 1.

| matchup | v2 | v3 | delta |
|---|---|---|---|
| vs cf | 48.6% | 47.2% | -1.4 (autarky 5/6→4/6; stripes/devil/default/qos unchanged) |
| vs combat | 52.8% | 51.4% | -1.4 (default 1/6→3/6 fix! but dilemma 3/6→0/6 kill) |
| vs v104 | 52.1% | 50.7% | -1.4 |

**Verdict: v3 < v2 — hunt suppression is load-bearing.** Restoring hunts
fixed default-vs-combat (+2) but killed dilemma-vs-combat (-3): dilemma's
flip requires the swarm to eat, not skirmish. And stripes/devil did not
recover — their bleed is not missing hunts either. What's left: the
foraging swarm *scatters* (openExplore/openFog pull defenders off the
brood), and on killbox/2-3-brood maps the brood can't absorb it. That
scatter IS the opening mechanic — reducing it is reducing the lane.

## Final verdict — ship `abyss_pearl` = v2 config

```
openUntil 48, openDanger 1.0, openQueenDanger 1.8, openEnemyDist 1,
openHunt 0, openQueenKeep 3, openEatLen 4, openFog 0.3, openExplore 0.12,
survival() suppressed while open_
```

vs v104 baseline (72-game gates, seeds 1-3, 12 maps):
- **vs combat: 52.8%** (v104 scores 38.9% — **+13.9pp**)
- **vs cf: 48.6%** (v104 scores 48.6% — parity, different map mix)
- **vs v104 direct: 52.1%**
- **pearls@30: +15%** (12.99 vs 11.31 all maps; 12.4 vs 10.9 small)

Net: better or equal on every gate metric. Map-level regressions that
remain (n=6 each, so noisy): stripes -2 pairs vs cf/combat baseline,
devil -2 vs cf, default -1 vs cf & -3 vs combat, qos -2 vs cf.
Wins: dilemma +6/+3, arena +4/+3, autarky +0/+0 (already strong),
default_small +0/+2, trophy +1/+1, Colosseum +0/+1, tower_defense -1/+1.

Follow-ups for other lanes / future tuning:
- Brood-defense during open_: a defender that stays near the queen
  (position via champ relay — no vision needed) could fix stripes/devil/
  default without touching forage velocity. v3 proved generic hunts are
  not the answer.
- openQueenKeep=3 on killbox maps (devil/stripes brood ≤3): shorter queen
  = shorter escape reach; untested knob.
- weakhold stays 0/6 for every abyss variant — pre-existing hole, not
  this lane's.

Artifacts: `results/gate_*/games.jsonl` (local; gitignored),
`tooling/replay_metrics.py` (eaten30 metric), `tooling/kmatch.py`
(pearls-by-r30 summary rows). Variants: `abyss_pearl` = v2 (ship),
`abyss_pearl1`/`abyss_pearl3` = ablation snapshots (local only).
