# Lane: autarky (54x18, elimination-map class)

**Confirmed cause (one line):** our doctrine consolidates on a fixed clock (feed/split-stop ~r320) while the attrition war still runs — we freeze production, bleed ~19 length through r300-400, and the feed suicides scatter because the champion they die for is re-elected every few rounds; the winners keep producing (~39 dragons at r400) and consolidate one stable champion late.

Worker: session devin-13f9c33210b04125bd9da40bc7345e09, branch `devin/autarky`, bot `workspace/abyss_ak` (copy of `abyss_v113` + the single autarky-gated fix below).

## Diagnosis (mechanism, not just win%)

Autarky decides two ways:

1. **Bells (roundLimit ~80% of games): longest dragon at r499, then total length.** Both queens die early (~every game). The winner is whoever produces a *fallback champion* — v104-style opponents consolidate to ~30-55; we topped out ~15-25.
2. **Eliminations (~20%):** whoever survives the permanent attrition war in the mid-map. Winners at r50 have ~9.6 dragons vs 6.3.

Two measured loss modes, both real:

- **Champion churn.** From r320 (feed window) to r370 (`champRelayFrom`) *no* champion relays exist, so every dragon with `L_ >= feedMargin(4)` self-elects on local evidence. Instrumented on a lost bell game (akdbg vs v104, s6): **9 distinct dragons self-appointed champion over the game**, and the heard-champ target cell landed on **221 distinct cells**. Feed suicides (≈1.5k feed-targeted turns) scatter their drops across a moving, re-elected target — measured output was longest≈11 on a 30-dragon team vs v104's 35 on 10 dragons. `locateChamp()` re-elects on any `L_ > champLen_` takeover — a ±1 seesaw among ~3-8 peer candidates.
- **Bad trades in the attrition war.** ~55-60% of our head-to-head deaths are trades *we* initiate (`tradeSlack=1` allows `myLen <= enemyLen + 1`, i.e. trading down by 1). On autarky every trade leaves drops that feed *their* replacement engine — they farm the combat zone (e.g. v104 ate our pen-side v=10 bed ~30x in one game). Our swarm bled to ~19-26 alive while theirs stayed at 3-15 — but theirs *concentrated* all income on the champ while ours diffused across ~50 mouths (lost a game with total length 164 vs 33 — longest lost 26 vs 28).

## The fix (single autarky-gated change)

`policy.hpp::adjustByMap()` — fired only when `init.w==54 && init.h==18` (unique dims in the pool):

```cpp
eff_.champRelayFrom = 280;   // broadcast a champion before the r320 feed window opens
eff_.champMargin    = 3;     // NEW param: challenger needs +3 over the heard champ to take over
eff_.tradeSlack     = 0;     // only trades that do not lose length
eff_.tradeMinUnits  = 8;     // and only with a real army
```

`common.hpp`: new param `int champMargin = 0;` — default 0 makes `L_ > champLen_ + 0` identical to v113 on every other map (provably unchanged: all behavior differences live behind the 54×18 gate).

Mechanism: a stable single champion means feed suicides land on a *fixed, reachable* target (they die within `champFeedDist` of its head) and the drops consolidate instead of scattering. Trade discipline keeps enough feeders alive long enough to deliver ~200 rounds of income to it.

## Results vs abyss_v104 (local kmatch, reversed seats)

Autarky trajectory over experiments (16-game runs, seeds 1-8 both seats):

| variant | autarky win% | mechanism check |
|---|---|---|
| v113 baseline (ak3) | 37.5% | longest ~15-25 vs 30-50 |
| trades(0/8) only (ak5+ak5b) | 43.8% | alive 20-27 vs 4-6, longest still ~20 vs 30 — survival alone doesn't win bells |
| champ-hibernate + early feed (ak6) | 37.5% | static champ starved; regression |
| never-stop-producing + trades (ak7) | 31.2% | alive 49.8 vs 3.1 but longest 15 vs 31 — pure mass loses bells |
| champ-consensus only (ak8) | 43.8% | 6 elim wins + first consolidated champ (34) — consensus alone insufficient |
| **stacked: champ-consensus + trades (ak9)** | **56.2%** | **longest 28.9 vs 35.3 (was 22 vs 42); wins include bells c44/33, c40/12, c35/18, c55/18 + 2 elims** |

### Full 22-map gate vs abyss_v104 (`--maps all --seeds 4`, 176 games): 47.2%

| map | n | W | map | n | W | map | n | W |
|---|---|---|---|---|---|---|---|---|
| Colosseum | 8 | 62.5% | weakhold | 8 | 50.0% | islands | 8 | 87.5% |
| arena | 8 | 50.0% | australia | 8 | 37.5% | maze | 8 | 0.0% |
| default_small | 8 | 37.5% | **autarky** | 8 | **50.0%** | portals | 8 | 12.5% |
| devil | 8 | 50.0% | big_empty | 8 | 75.0% | schooltime | 8 | 100% |
| dilemma | 8 | 50.0% | default | 8 | 50.0% | slithery_fight | 8 | 25.0% |
| queen_of_spades | 8 | 50.0% | stronghold | 8 | 0.0% | trauma | 8 | 37.5% |
| stripes | 8 | 62.5% | tower_defense | 8 | 75.0% | unsw | 8 | 25.0% |
| trophy | 8 | 50.0% | | | | | | |

- **autarky 4/8 — not 0/4** (wins: c35/18, c40/12, c44/33, c55/18 — all bells with a consolidated champ).
- **No new 0/4**: maze and stronghold are 0/8, but the bot's code on non-autarky maps is *provably identical to v113* (full diff: one default-0 param, the one gated line using it, and the 54×18 block). Every off-autarky result is exactly what v113 does — deterministic engine, same decisions.
- **The ≥50% overall bar is not reachable inside this lane**: with autarky at 8/176 games, even 8/8 autarky wins yields 86/176 = 48.9% — v113's own baseline is ~46.6% (identical 168 games + 3/8 autarky from ak3). Lifting the gate past 50% needs the maze/stronghold/portals lanes, not autarky.

### abyss_cf sanity (autarky, default, default_small × 4 seeds): 50.0% overall (12/24)

- autarky 3/8 (bells c35/31, c44/31 + elim r308), default 3/8, default_small 6/8.

## Steering metric (r50 production)

- vs v104 locally: parity — ~13 vs 8-14 dragons, ~45-50 total length by r50 both sides. The opening is NOT the local loss mode.
- vs ladder mass-splitters: our r50 splits ~60-75% of theirs, diverging to ~40% by r150. Their edge is speed of replacement, and the combat-food flywheel (whoever controls the battle zone eats the drops) — the fix's trade discipline + consolidation attacks exactly that.

## Failed attempts (for the log)

- electedChamp reach-fear (champ flees all enemies): 12.5% — it starved; reverted.
- hiding-champ camps in swarm cover + feed params only: 25% — champ survived but stayed a moving, churning target.
- champ-suppressed-forage: same failure family — a static champ without delivered income starves.

## Notes

- v113's late-game "output guards" (r320+ feed-blocking, fixed in v116) distort local-vs-v104 results on non-autarky maps only in principle; autarky block is orthogonal.
- qsiege lane owns generic queen-encirclement; nothing here touches queen logic.
