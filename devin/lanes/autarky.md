# Lane: autarky (54x18, elimination-map class)

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

---

# Adversarial review — v149→v151 (portal-scout), v151→v152 (C2/C3), C7 sealed-queen

Reviewed against devin/v120 @ c6c22ba. Read job, no gates.

## Diff 1: v149→v151 portal-scout — mechanics correct, ship-shape

**(a) scout → cand/two-step/split propagation: SAFE.**
- Two-step `cands` can never carry a scout: first-step filtered by `c1.dest < 0` (policy.hpp:201), second-leg filtered by `if (c2.dest < 0) continue`. So `cd.c.terminal`, `tc[]`, `ctot[]` never see dest=-1.
- `eaten.push_back(c.dest)` only runs in the `c.dest >= 0` branch — a scout's -1 never lands in `eaten`.
- `firstBody[d]` for a scout dir is unpopulated but also never read (dest<0 skips both `searchFrom` and the two-step pass).
- **trySplit CAN override a scout winner** — "scout" is not in its why-reject list (trade/defend/slay) and scout's `c.eat` stays false (the scout block returns before the `c.eat` line). The bud itself is safe: `out.split(c.n)` carries no direction (in-place), and portal edges read as nb=-1 → non-exits → `hasRoomyMove` is *conservative* at portal lips, not permissive. No bad-bud hole — the scout intent is just silently dropped that turn. If scouts should stick, add `bestMove.why == "scout"` to the trySplit reject list; as committed, legal buds outrank scouts (arguably fine — wScout is "exploration of last resort"). sprintTrade can also outbid a scout — defensible (a guaranteed kill > a blind cross).

**(b) `best.dest<0 && best.why!="scout"` skip: AIRTIGHT.**
- A scout is the only dest<0 choice that can win: other dest<0 `first[]` entries are skipped in the pick loop, cands always have dest≥0. When nothing wins, `best` stays default-constructed (`dest=-1`, `why=""`) → `why != "scout"` → trapped fallback still runs. Correct for all three cases (scout wins / cand wins / nothing wins).
- main.cpp safeFirst bypass is **load-bearing**: safeFirst's `dest >= 0` test rejects the portal-edge dir outright — without `c.why != "scout"` it would redirect every scout into an ordinary move and the feature would be dead code.
- Emit path is `out.move(c.dir)` — direction only; `dest` is internal bookkeeping. Engine teleports on the edge dir. Correct.
- Depth loop `if (c.dest<0) { if (why=="scout") t[d]=c.score; continue; }` keeps the terminal score at every depth — including timeout-before-first-depth (`total[d]` initialises to `first[d].score` = same value). Consistent. `c.terminal=true` on the scout is belt-and-suspenders (the dest<0 branch catches it first) — harmless.

**(c) queen exclusion covers all states.** `queen_` is id-based (`init.id == champId`); `hiding_` requires `queen_` (policy.hpp:59), grower is her other mode — hiding/grower/post-unhide queens all excluded by the one flag. The second `!queen_` inside the score expression is dead but harmless.

**(d) portals.map bud geometry:** covered in (a) — `hasRoomyMove` treats portal edges as non-exits → more conservative at portal lips, can't produce a portal-specific bad bud. Residual: a swarm dragon that keeps meeting split conditions at a portal lip will bud every turn instead of scouting — scout starvation, not a correctness bug.

## Diff 2: v151→v152 — C2/C3 sound; **wScout silently reverted to 6.0**

**wScout 2.0 → 6.0 (common.hpp:141)** — v151's own comment documented the reason ("6.0 streamed whole squads through portals into enemy territory: deaths 59 vs 42"). The revert is now *load-bearing* rather than cosmetic: with the v151 pick-loop fix scouts can actually win, and at 6.0 a blind cross scores ~5.4 (`6.0 − 0.3·(1+0.25·L)` for L≈4) — that outbids nearly every ordinary move, so the squad-streaming leak re-arms. The rest of v152's common.hpp is byte-identical and main/world/board/nav/io are untouched — this looks like an accidental clobber from a pre-v151 base, not a deliberate re-tune. If it IS deliberate, scout needs a value that only wins over dead options, not over real moves.

**C2 (hiding queen needs ≥2 roomy exits, r>2): consistent.**
- `blkP` is byte-for-byte the same construction as the parent's own roomy check six lines above (`base_` + child-INF + `markBody(parent, keep)`) — could literally reuse `blk`; the duplicated NC-copy + ≤4 floods are negligible CPU, so it's dead duplication not a bug.
- `blkP[nn] > 1` is the right idiom: markBody writes vacate-times (head→L+1, tail→2), `<=1` = free-now, matching buildBase's teammate-exit test; `flood`'s `blk[n] > nd` correctly lets vacating cells admit the wavefront.
- `keep` = parent's post-split len (= queenHideLen for a hiding queen) — same role as `len` in `hasRoomyMove(len)`. `parent.front()` = head cell = correct anchor (the parent holds position on the split turn). `b`, `nav_` in scope.
- r≤2 exemption matches the stated intent: `hiding_` can be true at r≤2 (`queenHide && queen_ && round<queenHideUntil && NC≥hideMinTiles`), and the scripted opening bud must not slip a round (unsw seat-A). Harmless no-op when it can't fire.
- Counting exits by independent floods is consistent: two dirs into the *same* small region both fail `≥need2` → `roomy<2` → no bud. Residual gap (document, don't block): it tests *this* turn's geometry — a child landing in her corridor next turn is unguarded, same limitation as all existing checks.

**C3 (`!queen_` on the score<-500 reverse): the cornered-queen fallback chain is complete.**
- When all moves are vetoed-but-legal she takes the least-bad — same as before minus the reverse option.
- She keeps normal splitting machinery: trySplit's grower/hiding paths have no score gate, so a legal bud still fires on a doomed-score turn.
- The trapped fallback remains reachable: it triggers on `best.dest<0 && why!="scout"`, queen-agnostic; a queen never produces `why=="scout"`.
- When truly illegal-moves-only (all dest<0), she still gets the ranked trapped fallback — no hang, no illegal emit.
- Removed case: all-vetoed + L≥4 → previously reversed into a facing-out 2-stub; now she takes the vetoed step. Both can die — the stub-vs-step tradeoff is your policy judgment (and your comment matches: stubs mutilate her on survivable boards); mechanically there is no hole in the chain.

## v150 pending deltas (feedFloor + unhide) — mechanism verdict for the washes

- **feedFloor**: correct but ~vacuous → explains the wash. `units>8` holds on >2000-tile maps for nearly the whole game, so the floor only binds after the swarm has already collapsed — but the pre-collapse feed turns are exactly the ones that scattered it. Under lexicographic scoring, plan-B longest can't be rebuilt from a sub-8 remnant either. Delete.
- **unhide** (`queenHideUntil=300`, `queenFeedRound=320` on >2000 tiles): live but backwards. An unhidden, mobile queen at r300 precedes the ~r330 anchor lock, so feeders die on a *moving* target — the scattered-drops anti-pattern — and her roaming exposure opens earlier under lexicographic scoring (queen dead = automatic tiebreak-1 loss). Under the verified scoring, she compounds by *being fed*, not by *waking early*. Delete both; if you want her earlier, make her the anchored feed target rather than mobile.

## C7 — sealed-queen test (implementable, head+len only)

The hole: `locateChamp`'s `queenReach() < 20` uses `regionReach()` — a 40-cell flood over `nb[]` that ignores occupancy. A queen sealed by her own body across a 1-tile neck floods *through her unseen body* → reads reachable → workers name a queen who can't be fed (31% of post-r390 schooltime turns).

Two hard facts available without knowing her body:

1. **Her neck is always one head-neighbor.** A snake's second segment occupies one of her ≤4 adjacent cells → real exits ≤ `openNb − 1`. `openNb ≤ 2` ⇒ at most one non-body exit ⇒ the 1-wide-mouth geometry = sealed for feeding purposes.
2. **Pocket capacity.** Her len−1 body must physically occupy cells in her connected open space. If that space holds ≤ `qlen + margin` cells, the body fills most of it — no free approach corridor can exist.

Drop-in (replace `queenReach() < 20` at policy.hpp:612):

```cpp
bool queenSealed(int qh, int qlen) {
    Board const& b = w_.board;
    if (qh < 0 || qh >= b.NC) return false;
    // A) head-degree bound — her neck is always one neighbor cell.
    int openNb = 0;
    for (int d = 0; d < 4; d++) {
        int n = b.nb[qh * 4 + d];
        if (n >= 0 && base_[n] < INF) openNb++;
    }
    if (openNb <= 2) return true;          // <=1 real exit: mouth-of-pocket geometry
    // B) pocket-capacity bound — her len-1 body can't leave a free corridor
    //    when the whole connected open space is this small.
    int cap = qlen + 8;                    // slack: head step + drop ring
    if (nav_.flood(b, qh, base_, cap + 1) <= cap) return true;
    return false;
}
// locateChamp: if (queenReady && ... && queenSealed(w_.queenCell, w_.queenLen)) queenReady = false;
```

Honest residual: (B) is still body-blind on the escape path — it catches *small-component* seals (the schooltime nooks, the actual failure) but not a queen self-coiled in open field (rare — bodies uncoil). It tightens for free as workers see her: any queen-body cell already marked in `w_.occ`/`ownExtra` is INF in `base_`. Cheap hardening option: run the flood on a seen-only map (fog = wall, the `deadEnd` convention) — false-sealed only costs a champ candidate, false-open costs 100 rounds of dead feeding, so the bias should be toward sealed. Related site: `regionReach(w_.head) >= 12` (policy.hpp:80) has the same blindness, but there the dragon's own body IS known — `blk = base_; markBody(blk, w_.body, L_);` makes that one exact.

---

# Feed-convergence lane — mechanism status (blocked item flagged to integrator)

`abyss_v152` (local, v149-based): die-in-place feeders walk to champ head + HOLD; `feedConvLead=40` hoists the gate to `feedAt-40`. Mechanism check on the dbg twin shows **zero fh≥0 turns before r360**: the feed target itself doesn't exist pre-window — `champHead_` stays -1 until `champFallbackRound` (360 under the live kParams shadow on v149; 330 fixed on v150+), and the queen branch is `queenReady`-gated at `queenHideUntil` (390 open / 320 corridor). Same reason `champPlantLead=40` is inert — `selfChamp_` can't exist before the election round. Front-loading recycles needs a pre-window target; convergence code is built and ready to gate once the target-timing question is answered (recommend: let the champ plant/anchor fire at `consolAt-40`, or relax the `queenReady` gate for TARGET purposes while keeping it for feed deaths).

---

# abyss_v157 board gate — correctness composite vs abyss_v149

**Build**: `workspace/abyss_v157` = v120-HEAD v149 + (a) portal-picker fix (scout candidate `!queen_`-gated, `wScout=2.0`, pick/depth/fallback/safeFirst wiring — verified mechanically in the earlier review) + (b) C5 (`s.id == ourQueen && exits <= 2` → `exits == 1`, keeping single-exit reservation only) + (c) `champFallbackRound=330` confirmed in both the decl and kParams on v120 HEAD — no 360 shadow. Compiles clean; `abyss_v149` synced to v120 HEAD first so the base is canonical (330 + `w_.champAnchor` World lock).

Gate: `kmatch run --cand abyss_v157 --base abyss_v149 --maps all --seeds 2 --jobs 2 --tag v157_board --keep-replays` — 22 maps × 2 seeds × both seats = 88 games (integrator est. 68; `all` resolves to the full SMALL+BIG set).

### Result: 58.0% overall (51/88) — composite is net-positive

| 75%+ | 50% | 25% |
|---|---|---|
| trauma **100%**, unsw **100%** | arena, devil, dilemma, qos, stripes, tower_defense, trophy, weakhold, default, portals, schooltime | islands, maze, slithery_fight |
| Colosseum, default_small, australia, autarky, big_empty, stronghold | | |

SMALL 55.0% / BIG 60.4% / ALL-unlocked 61.8%. Decisive pairs 10 W / 31 S / 3 L.

**Deltas (cand vs base):**
- longest@end (r500): **30.6 vs 28.9 (+1.7)** — the portal-scout conversion contributes on the far-half maps (unsw/trauma 100%).
- **queen dead /game: 0.750 vs 0.670 (+0.080)** — all non-ram (0.205 vs 0.125, ~1.6×): consistent with C5 releasing her second exit — workers now park cells she needed. queen alive@end 0.306 vs 0.429; **queen-kept-after-theirs 24.2% vs 38.5%** — the biggest regression in the composite, and it's tiebreak-1 currency under lexicographic scoring.
- alive@r499 14.1 vs 15.9; deaths/game flat (74.7 vs 74.9). Small-map opening improved: alive@r50 6.59 vs 5.84, splits@60 13.7 vs 12.1, pearls@60 37.2 vs 33.9.
- Map-level pattern: the three 25% maps (islands/maze/slithery) are exactly the pocket/corridor maps where queen exit-room matters most — the same geometry C2 was built for; C5 traded it away for devil (which stays 50% = seat-locked neutral here anyway).

**Read**: composite wins +8% — ship direction is right, but the C5 arm is plausibly net-negative inside it (islands/maze/slithery + queen-dead delta vs devil-neutral). If you split the composite, gate `v149 + portal-fix-only` against `v149 + portal-fix + C5` — I'd bet the portal arm alone scores ≥ this.

## C7 spec — body-aware sealed-queen test (design only)

Feedability, not mobility, is the question: a queen is feedable iff drops can reach her — in-place drops beside her head (she must be able to step) or drops on cells she can reach. Rank what blocks her head's exits by persistence: (1) map walls — permanent; (2) **her own body** — permanent *while* she can't move (self-consistent: a body that blocks all exits never vacates); (3) foreign bodies, ours and theirs — transient, they move off within rounds and a queen crowded only by foreign bodies is delayed, not sealed. So the spec's wall set is **map walls only** — every foreign body is treated as open — with the queen's own body bounded rather than guessed: (a) **head-degree bound** — her neck always occupies one adjacent cell, so real exits ≤ `openNb − 1` where `openNb` counts wall-open neighbors; `openNb ≤ 2` ⇒ at most one non-body exit ⇒ mouth-of-pocket geometry ⇒ sealed for feeding purposes in *any* body configuration; (b) **pocket-capacity bound** — flood her connected open space over map-walls-only, foreign bodies open, capped at `qlen + slack` (slack ≈ 8: a step + drop ring); if the region holds ≤ `qlen + slack` cells, her len−1 body fills most of it and no free approach corridor exists in any configuration ⇒ sealed; (c) both pass (`openNb ≥ 3`, region > `qlen + slack`) ⇒ unsealed — a region that large cannot be fully neck-plugged without the degree bound already firing, and any residual foreign-body crowd resolves itself. Residual: a false-negative when she self-coils in open field (rare — bodies uncoil on the move); the bias should be toward sealed anyway — a false-sealed costs one champ candidate, a false-open costs ~100 rounds of dead feeding. Implementation hook: `queenSealed(w_.queenCell, w_.queenLen)` replacing `queenReach() < 20` in locateChamp; keep `regionReach` for the self-anchor site where the body IS known (`markBody(blk, w_.body, L_)` makes that one exact).

---

# abyss_v158 — champion multi-step (v3 item 5) vs abyss_v157

**Build**: `workspace/abyss_v158` = v157 + champ path extension. Workers' twoStep caps at 2; the champ now extends the top `champStepSrc=8` (len−1)-step cands to `min(freeSteps(L), champStepMax=4)` via `scoreFrom` continuation (+`eatSum` for mid-path pearls, `pathEat` bitmask drives per-step `advanceBody`, `pathCost=0` since steps ≤ freeSteps). Emits `MOVE <dirs>` verbatim — engine accepts ≥4-step sequences (verified in replays: 678×3-step, 28×4-step, 1×5-step across 8 smoke games; no TLE/instruction-exceeded flags).

**v158a lesson (first cut, 12.5% on 4-map smoke)**: extension for `selfChamp_ || (queen_ && !hiding_)` with no safety/margin → (1) the queen zigzagged 4-step paths r341-373 (argmax churn — each turn re-picks a different long path, she oscillates instead of traveling) and died h2h r397; (2) mid-path cells got legality checks but zero threat pricing — 68-72 deaths ≤2r after a multi-step move on big_empty; (3) swarm starved: alive@r499 9.4 vs 30.9 — a chasing champ abandons the drop field and the feed engine dies with it.

**v158b fixes**: `selfChamp_` only (queen emits 0 multi-step in smoke2 — anchor/fragility outranks chase for her); every committed cell must have no enemy head within BFS `dist ≤ 1` (seen + heard fields); longer path must beat its own prefix by `champStepMargin=1.0` (kills jitter-commitment); `midEat` bit0 for wallguard fallback. Smoke2 recovered: **62.5%** (unsw 100%, autarky/big_empty/schooltime 50%).

## Board gate: `--cand abyss_v158 --base abyss_v157 --maps all --seeds 2 --jobs 2 --tag v158_board` (88g)

**Result: 51.1%** (45/88, CI 40.9-61.3) — vs v157's 58.0% gate vs v149, so net-neutral-to-slightly-worse as a full-board change. Split is the story:

| 100% | 75% | 50% | 25% |
|---|---|---|---|
| **unsw** | weakhold | arena, big_empty, Colosseum, default, default_small, devil, dilemma, islands, portals, qos, schooltime, slithery_fight, stripes, stronghold, tower_defense, trauma, australia | **autarky**, **maze** |

SMALL 52.5% / BIG 50.0% / ALL-unlocked 51.5%. Decisive pairs 4W/37S/3L.

**Deltas (cand vs base, r500 n=52 / all n=88):**
- longest@end **29.8 vs 28.4 (+1.35)** — the champ does convert speed into length.
- qlen@end 1.35 vs 1.75 (−0.40); queen alive@end 0.25 vs 0.29; queen-dead/game +0.02 (0.784 vs 0.761); queen-kept-after-theirs 25.6% vs 30.0%.
- alive@r499 14.75 vs 15.75; deaths flat (h2h 61.5 vs 61.6, wall+self+body 70.5 vs 72.2).
- Post-multi-step deaths are all `hitHeadToHead` (trades, the map's normal kill mode) — no wall/self crash signature; the v158a mid-path crashes are gone.

**Read**: mechanism confirmed (champ emits 3-4 steps, +1.35 longest@end, queen untouched). The payoff concentrates on big open boards (unsw 4/4 — both seeds both seats) where chasing converges; it costs on corridor/consolidation maps (autarky 75→25, maze →25) where champ position — staying planted over the drop field — beats pursuit speed, plus the small queen-side drag (−0.40 qlen@end). Neutral overall as shipped.

**Options if you want the upside without the corridor tax**: gate `champStepMax>2` on open-class — cheapest honest axis is `!maze_` (kelp frac ≤ 0.22, already computed per-map) though autarky isn't maze-class so the better axis may be `w*h` large-open like unsw/schooltime/australia/big_empty, or a seen-topology openness measure. One param + a re-gate.

Replays kept under `results/v158_board/`; smoke tags `v158_smoke` (pre-fix) / `v158_smoke2` (current build).

---

# abyss_v158d — champStep ported onto v168 (flagship queue) vs abyss_v168

**Build**: `workspace/abyss_v158d` = v168 + champStep, verbatim port of v158b: `selfChamp_` dragons extend top-8 (len−1)-step cands to `min(freeSteps,4)` via scoreFrom continuations, pathEat bitmask emit, mid-path cells rejected when any enemy head (seen or heard) is at BFS dist ≤1, extension must beat its own prefix by `champStepMargin=1.0`. One v168-specific addition: **anchored champs excluded** (`w_.champAnchor < 0`) — chasing while planted over the drop field was the corridor tax on the v157-based gate; an anchored champ now always holds. v168's EnemyField.reachBoost/qRamAdj untouched.

Gate: `--cand abyss_v158d --base abyss_v168 --maps autarky,australia,unsw,big_empty,Colosseum,maze --seeds 2 --jobs 2 --tag v158d_bell --keep-replays` = 24g.

### Result: 50.0% — all 12 pairs split W/L, below the 55% merge bar

Every map 50%; every metric flat to the decimal: longest@end **33.3 vs 33.2** (+0.1), qlen@end 0.15 = 0.15, queen-dead 0.875 = 0.875, h2h 125.625 = 125.625 (identical), alive@r499 23.65 vs 23.75. Pure seat-lock everywhere — australia pairs went c5/b28 then c28/b5, unsw c51/b22 then c21/b52.

**Mechanism check**: fires but rarely — 427×3-step + 5×4-step emits total; per-game ~65 on big_empty, ~20 unsw, ~5 autarky/maze (vs ~110/75+/30+ on the v157-based build — anchor exclusion + margin restrict it to genuinely-better unplanted chases). No TLE/instruction-exceeded flags; one anomalous 6-step action is the kill-move normalization artifact seen before, not an emit. CPU per game 67-194s wall = same distribution as the v168 base rows in prior gates.

**Read**: on v168 the piece is a true coin-flip — safe (no metric regression anywhere, the v158a failure modes stayed fixed) but earns nothing measurable on this set. The chase window it helps (pre-window, unplanted, clear field) is narrow because the champAnchor plant already owns the high-value window. If merged it'd be for the rare games where it fires, not this gate's evidence. Recommendation: **don't merge at 50%** — unless you want it as a free option; if you do, keep `champStepMargin=1.0` and the anchor exclusion (they're what made it safe).

Replays: `results/v158d_bell/`.

---

# Queen-behavior study — top teams vs Cognoscenti (351), ladder replays

Data: `top_replays/` = 100 ladder replays (teams 264/306/91/213, 25 each), `our_replays/` = 30 (team 351). Analysis restricted to open/decision maps (Autarky, UNSW, Big Empty, Schooltime, Islands, Australia) — 26 top / 12 our-losses / 16 our-wins. Per round per queen: head, movement, dist to nearest own head (escort), enemy-head proximity, cell open-degree, open-edge flood region. Scripts: `analysis/queen_study.py`, `analysis/champ_anchor_study.py`, `analysis/drop_capture_study.py`.

## Q: Do winning queens camp or move? — They move, always

**Everyone's queen moves ~97-100% of rounds, all game phases, all cohorts. Nobody camps.** The difference is entirely WHERE they move:

| cohort | escort mid→late | enemy≤3 mid→late | deg late | region late | queen alive@end |
|---|---|---|---|---|---|
| top teams | 5.6 → 5.6 | 17% → 12% | 3.2 | ~29 | **17/26 (65%)** |
| ours (wins) | 3.9 → 6.5 | 10% → 3% | 3.1 | ~29 | 10/16 |
| ours (losses) | 9.3 → **13.7** | **34%** → 24% | **2.0** | **~4** | **3/12** |

- Top queens orbit at **~5.6 tiles from the nearest own head**, constant from mid to end. Ours in losses drift to 9.3→13.7 — the queen ends up separated from her swarm. In wins we hold the same 3.9-6.5 profile — **escort distance is the single clearest win/loss variable**.
- Exposure: our losing queen has an enemy head within 3 in **34% of mid rounds** (top: 17%) and within 5 in **76% of late rounds** (top: 42%). edMean 4.7 vs their 7.2.
- Geometry collapse: our losing queen's open-degree falls to 2.0 and her flood region to ~4 cells (sealed pocket); top queens hold deg 3.2 / region ~29 throughout.

## Q: How do they survive rams that kill ours? — Prevention, not evasion

- **Top queens never crash: zero hitWall/hitSelf in 26 games.** Their only deaths: 5 noValidAction (sealed — engine kills an immobilized dragon), 4 hitHeadToHead. Median "death round" = 499.
- Ours: 9/12 dead by median r149 — h2h 6, **hitWall 2 + hitSelf 3** (cornered-flee crashes), hitOtherBody.
- Mechanism: their queen sits inside the swarm perimeter (escort ~5.6), so a rammer must clear own-body escorts to reach her; the roomy region (deg≥3, region~30) means an exit always exists — they survive by never being cornered, not by out-dodging a sprint. It's a *positioning* property that holds every round, not a per-turn dodge.
- They also kill the other queen: top opponents' queens die h2h 15/26, median r162 — the escorted queen IS the ram threat.

## Champion anchoring (steering metric) — planted, midfield, not home-anchored

- Top non-queen champ end-length median **47** vs ours 30 (losses) / 23 (wins). Queen-is-champ 19% top.
- Anchor (median head, r330+): spread median **5 tiles** — genuinely planted/tight orbit, not a roamer.
- BUT anchor is **not** near the queen's start: anch→ownQstart median 26 ≈ anch→center 24 ≈ anch→enemyQstart 29 ≈ anch→queen's-late-position 25. The champ plants at a territory-forward point, roughly midfield/equidistant — not beside the queen and not home.
- **Feeder die-radius claim does NOT replicate as a distance signature.** Deaths r≥200 are ~median 20-23 tiles from the anchor / current-longest head in ALL cohorts (top 21-23, ours 20-21) — feeders die distributed across the field, not within a radius-N halo of the champ. (`feedRadius=12` in v184 sits well inside the empirical median ~21 — expect it to cut the majority of recycling unless feeders first converge.)
- What DOES differ is the death-reason mix: top **noValidAction = 45%** of r200+ deaths (2994/6604, die-in-place) vs ours **17%** (351/2121); ours crash instead — hitSelf 24% + h2h 34%. Top teams run ~254 own-deaths/game vs our ~177 — they recycle ~1.4× harder, everywhere on the map.
- Drop capture: ~99% of dead-dragon cells get re-visited by an own dragon within 12r in all cohorts; captured-by-longest ~8-10% everywhere — the 17-vs-10% split doesn't reproduce under head-visit capture.

## Concrete diffs for the flagship

1. **Escort/anchor geometry is the queen-safety lever**: top queens survive by orbiting ~5 tiles inside the swarm on deg≥3 cells. Ours drifts (escort 13.7 late) into pockets (region~4) then crashes. A "queen-leash" — penalize queen dests with own-centroid dist > ~8 or open-degree <3 — directly targets the loss signature. (Consistent with qRamAdj: prevention via positioning.)
2. **Death-mix gap is the conveyor gap**: nva 45% vs 17% — the mechanism to close is not die-radius but converting hitSelf/h2h transit deaths into planned in-place deaths.
3. **Champ plants midfield-forward** (dist ~25 from own queen start, spread ~5) — our champAnchor already does this shape; the gap is champLen 30 vs 47, i.e. feed throughput, not anchor placement.

Replays: `top_replays/`, `our_replays/` on this box. All open-map cohort; corridor-class maps excluded (queen geometry differs by map class).

---

# Adversarial review — abyss_v182 vs v168 (champAnchor_ + feedHeardDie=30 + extras)

Diff inspected: `common.hpp`, `policy.hpp` (9 hunks). The landed diff is wider than the stated "persistent champAnchor + feedHeardDie 2→30": it also contains **feedBurst** (wFeed×3 for feeders within BFS-14 of feedHead_ during the first 20r of the feed window), **regionSize_ component labeling** (workerRegionNorm=0 — dead code, one wasted BFS per drone), and an **unstated qRamAdj scope change** (the `W==40 && H==15` gate dropped — weakhold-only fatal-reach queen pricing now applies on ALL maps; probably a deliberate de-gating since dims-gates are banned style, but it conflates the gate result: a pass/fail won't isolate which arm moved it).

## (a) feedHead_ at a stale cell — yes, and worse than stated

Anchor semantics: `champAnchor_ = champHead_` refreshes every round `champHead_>=0`, i.e. it records the last *estimate*, not a confirmed sighting — `champHead_` itself may already be `champAge_≤40` stale. When the estimate expires, `feedAge_ = round - champAnchorRound_` **resets to ~0**, re-arming `heardNear` (≤feedHeardDie=30) at a position that may already be ~40 rounds old. **Age laundering: true position staleness at die-time can reach ~40 (report edge) + ~30 (anchor window) ≈ 69 rounds** — the 30-round die gate does not bound real staleness. Fix: stamp the anchor with position-age not evidence-age — `champAnchorAge_ = champAge_` at refresh, `feedAge_ = champAnchorAge_ + (round - champAnchorRound_)`.

Sharper version: world.hpp:265 clears `chRound` when `chCell` is visible-and-vacated — i.e. the moment the team *confirms* the champ left, `champHead_` drops to -1 and anchor mode engages on the **known-empty cell**. No `visible(champAnchor_)` check exists in the else-if, so a feeder will converge on and die at a cell its own team just verified empty. Fix: mirror the vacate check — skip/clear anchor when `w_.board.visible(champAnchor_)` and champ not seen there.

Mitigant: for a *planted* champ (spread ~5 per the queen study) the stale anchor lands inside the patrol orbit — drops still get re-collected. The ghost-feeding risk concentrates in mobile-champ phases (queen-as-champ before anchor lock, pre-fallback).

## (b) Dead-champ poisoning — partial, ~30r blast radius

On champ death: sightings stop → `champHead_` expires at champMemory=40 → anchor holds the corpse site and `heardNear` stays armed ~30 more rounds. Feeders die at the corpse cell dropping THEIR pearls there — if the enemy swept the site, that's feeding pearls into enemy-held ground. A new elected champ re-arms `champHead_` → anchor re-targets, so not permanent. Net: bounded leak, ~30r × local feeder density per champ death. Worth one line: clear `champAnchor_` when the champ's death is observed or when a *different* champ id takes over `champHead_`.

## (c) champAnchorAge=40 vs feedHeardDie=30 — inconsistent, makes zombie feeders

Anchor serves `feedHead_` for anchor ages ≤40, but `heardNear` dies only ≤30. For anchor ages 30-40 feeders keep the to-feed pull, converge to `champFeedDist≤2` of the anchor, and **cannot die** — they hover at the ghost ring as non-productive drones for 10 rounds each. Either clamp the anchor branch to `champAnchorAge = min(champAnchorAge, feedHeardDie)` or raise `feedHeardDie` to 40 — the two constants must bound the same window.

## Extra holes found

- **selfChamp_ can feed itself to death**: the else-if isn't `!selfChamp_`-guarded. A freshly elected champ with `L_ ≤ feedMaxLen(6)` (small champ at election, e.g. remnant games) takes `feedHead_ = own stale anchor` and can die-in-place at its own remembered cell. One-token fix: `else if (!selfChamp_ && champAnchor_ >= 0 && ...)`.
- **feedBurst_ amplifies ghosts**: burst requires `feedAge_ ≤ champMemory(40)` — a 39-stale anchor still gets wFeed×3 pulling feeders harder toward dead cells. Consider `feedAge_ ≤ feedHeardDie` as the burst freshness gate so only die-eligible targets get the pull.
- Minor: `feedBurstRounds`/`feedBurstDist`/`feedBurstMult` new params — first 20r burst ≈ the front-load recipe from steering-4 (13+ recycles in window-open). Mechanism target for telemetry: nva feeds inside r360-380 should jump vs v168.

## Conveyor telemetry — v184 (feedRadius=12) vs v182, local 24g gate

Their gate replays aren't on this box, so this is a local paired gate: `--cand abyss_v184 --base abyss_v182 --maps autarky,australia,unsw,big_empty,schooltime,islands --seeds 2 --jobs 2 --tag v184_rad24 --keep-replays` (24g). Result: **45.8%** (pairs 2W/7S/3L) — below break-even; schooltime is pure B-seat-lock (B won all 4 regardless of bot).

**Feed-window (r360-499) deaths per game, v184 vs v182:**

| map | nva feeds | h2h | hitSelf | longest@end | wins |
|---|---|---|---|---|---|
| unsw | 28.5 / 53.2 | 20.5 / 20.0 | **61.5 / 38.0** | 24.2 / 25.0 | 1/3 |
| australia | **10.5 / 37.0** | 11.2 / 11.2 | 0.8 / 19.8 | 26.5 / 38.8 | 0/4 |
| autarky | 1.5 / 1.0 | 1.2 / 1.2 | 4.0 / 1.2 | 38.0 / 36.5 | 1/3 |
| big_empty | 7.0 / 10.0 | 33.8 / 33.8 | 7.2 / 7.2 | 52.2 / 50.2 | 2/2 |
| islands | 32.0 / 18.5 | 5.5 / 4.0 | 14.2 / 13.8 | 32.8 / 33.2 | 3/1 |
| schooltime | 35.8 / 26.8 | 9.5 / 11.0 | 54.0 / 29.5 | 38.2 / 22.8 | 0/4* |
| **ALL** | **19.2 / 24.4** | **13.6 / 13.5** | **23.6 / 18.2** | **35.3 / 34.4** | **7/17** |

**Answer to the radius question — it fails the trade:** feedRadius=12 suppresses nva feeds **−21%** (19.2→24.4 lost; −47% on unsw, −72% on australia) while h2h transit deaths stay **flat** (13.6 vs 13.5) — the "feeders die walking to the anchor" theory doesn't hold: those h2h deaths are combat attrition that happens anyway. Displaced feeders don't survive either — **hitSelf +30%** (23.6 vs 18.2): a feeder barred from recycling finds a worse way to die. longest@end flat (+0.9, noise). Consistent with the queen-study measurement that feeder deaths distribute at ~median 21 tiles from the anchor: a 12-tile radius excludes >half of all recycling structurally. If a radius gate is wanted at all, the empirical median suggests ~20-25, not 12 — or gate on *path-exposure* (enemies along the walk) rather than raw distance.

Replays: `results/v184_rad24/replays/`.

---

# Adversarial review — abyss_v198 vs v168 (v192 conveyor + mid-feed NC gate)

Scope: full diff `workspace/abyss_v198` vs `abyss_v168` on origin/devin/v120. The v192 composite = champAnchor_ + feedRadius=12 + feedBurst + qRamAdj-global + queenLeash + midFeed (+ regionSize_ dead code). All 6 staleness fixes from my v182 review landed correctly: evidence-round stamping, !selfChamp_ guard, min(anchorAge,heardDie) clamp, visible-empty clear, champ-id check, burst freshness gate.

## Ranked defects

**1. `champAnchorId_ == champId_` makes the anchor dead code in the exact state it exists for.** `locateChamp()` resets `champId_ = -1` alongside `champHead_` — when the champ's report ages past `champMemory=40`, `champHead_<0` AND `champId_=-1` → the stored anchor id can never equal it → the else-if never fires during normal off-vision play. The ONLY reachable case is the `std::max(L_,champLen_) < feedMargin` early-return (champId_ survives that path): small-remnant games only. The intended window — champ alive but unreported — is unreachable. Fix: compare `champAnchorId_` against `w_.chId` (world-level record, persists through staleness, ousted on new election/death) not the per-dragon `champId_` that dies with the report. **This may mean the anchor was never actually live in the v192 gate — BIG-map gains likely came from midFeed/leash/radius alone.**

**2. `midFeedMinTiles=600` doesn't exclude corridor class — fires on 16/22 maps.** NC is an area metric, not a shape metric. Corridor-class maps pass trivially: maze/trauma/stronghold (1152), slithery_fight (1701), queen_of_spades (875), trophy (625), autarky (972), default (1024), and **weakhold at exactly 600** (`>=` admits it). Excluded are only the 6 tiniest (arena 121, Colosseum/default_small 256, stripes 288, devil/dilemma/portals/tower_defense 512). If mid-feed recycling-at-r120 is the v192 SMALL-map loss driver, **v198's gate leaves it live on trophy/qOS/weakhold** (3 small maps, all ≥600). Correct axis: the corridor/open classifier or open-tile fraction, same one steering-3 mandated.

**3. qRamAdj-global is still in the composite (from v182/v192) and is the best structural suspect for remaining SMALL-map losses.** `wQueenRam=30 × newL × mult` additive danger on every cell inside `reachOf+boost+1` of ANY seen enemy, `floor_=0` → dist-1 included. On 256-600-cell maps an enemy BFS covers most of the board → the queen is fenced by overlapping fatal-priced reach rings → cowers/forages less → smaller qlen@end → lexicographic auto-losses (qlen is tiebreak 1). Designed for weakhold-600 corridors; on Colosseum/arena-size boards it's much heavier. On big maps the reach rings tile thinly — consistent with BIG-gain/SMALL-loss split.

**4. Torus-wrap centroid bug in midFeed.** `feedHead_ = b.id(sx/n, sy/n)` — arithmetic mean of ally head coords on a wrapped map: a swarm straddling the x-seam (heads at x=2 and x=W-2) yields centroid x≈W/2 — the far side, empty. The feedRadius=12 abort catches some cases (INF/>12 → drop target) but on 32-wide maps the wrong side is within 12 → workers converge and die at empty mid-map. Fix: wrapped circular mean, or anchor the centroid to the densest ally cluster / nearest-ally cell.

**5. Queen-leash edge cases.** `friendDist_` = BFS to nearest own head (seen or fresh-heard), no ally-state weighting: (i) a feeder walking to die at the anchor or a ram-squad pushing into enemies anchors the leash toward the kill zone — she follows doomed allies; (ii) `fd==INF` cells get ZERO penalty — unreachable pockets outrank merely-distant open cells → can tuck her solo into a sealed pocket, the isolation failure the leash exists to prevent (penalize INF as max-dist, not exempt); (iii) swarm-fleeing is benign (uniform penalty, follows swarm); (iv) hiding_ correctly exempt, but grower_ queens are leashed from r0 — mild early-forage constraint; (v) wQueenLeash=0.8/tile is soft — overridden by any real target pull past ~10-15 tiles → effectively advisory ≥leash+~7, still strictly better than v168's unbounded drift.

**6. Minor.** (i) `grower_=false; hunts_.clear(); escortOf_=-1` run BEFORE the feedRadius abort — a worker sheds assignments for a feed it then abandons (1-turn churn, re-picked next turn); (ii) midFeed centroid counts seen queen/champ in `n` but heard only role-0 — asymmetric; (iii) `feedBurstDist=14 > feedRadius=12` — burst window d≤12 effectively, the 14 is dead margin; (iv) anchor visible-clear only runs inside the feed block — non-feeding dragons lag one state behind (harmless).

## (d) SMALL-map loss attribution beyond mid-feed

Composite suspect ranking for SMALL 42.9%: **qRamAdj-global** (queen fenced on dense boards, qlen@end shrinks → lexicographic losses) > **midFeed on trophy/qOS/weakhold** (r120 recycling mid-combat) > **anchor-visible-clear + small-map omniscience** (everything visible → anchor cleared fast → conveyor reverts to live sightings; note this COSTS feeds on small maps while helping big — another split-consistent mechanism) > feedRadius=12 (mostly inert on small boards — everything's ≤12; can't explain small losses but still active on big).

Suggested isolation: midFeed off entirely (`midFeedRound=0`) × small preset only — 20g decides whether mid-feed was the small-map driver; then qRamAdj back to weakhold-dims or reach-scaled (`bonus *= min(1, NC/1152)`) — 20g. Both are one-line param/param-expression changes behind no new mechanism.

---

# Adversarial review — abyss_v200 / v201 / v202 vs v168 (origin/devin/v120)

Scope: v200 = my v198 defects' fix bundle (anchor w_.chId, density-centroid, qRamAdjMinTiles=600, leash INF→64, feedRadius ordering). v201 = v200 + deadEnd branch map (dedie). v202 = v200 + queen plant (w_.queenAnchor). Full diffs read; engine legality verified against engine/src/actions.cc.

## Headline — v202's feed target is dead code, TWO independent ways

**1. `w_.queenAnchor` never reaches feeders.** World objects are per-dragon. The plant writes `w_.queenAnchor` only inside the `queen_ &&` gate on the queen's own world (policy.hpp:127-129); it is never serialized into any beacon/heard/MsgChamp path (world.hpp:302-319 — no anchor field anywhere). On every worker's world `w_.queenAnchor` stays −1 forever → the feed-preference branch (policy.hpp:175 `!selfChamp_ && w_.queenAnchor >= 0 && ...`) is unreachable on the only dragons it exists for. The ONLY live v202 delta vs v200 is `targets_.push_back({w_.queenAnchor, 1.2, ...})` on the queen's own forage list — she self-orbits a post. The "stationary feed target, no staleness" mechanism is vapor. **Any v202-vs-v200 gate delta is noise + queen-orbit alone.**

**2. `w_.chId == w_.ourQueen` is unsatisfiable anyway.** Even with the anchor broadcast, noteChamp early-returns `id == ourQueen` into queenCell (world.hpp:331-334) — the queen is never recorded in chId; chId is written only at world.hpp:338 for non-queen dragons. The gate can never pass. The intended condition is `w_.ourQueen >= 0 && !w_.queenDead(w_.ourQueen)` (the alive-check queenReady already uses).

Fix sketch (no protocol change needed): workers already receive fresh queenCell via her beacons — derive "planted" client-side from queenCell stability (e.g. anchor = queenCell while cheb(queenCell_now, queenCell_from_5r_ago) ≤ 2). Or extend her own beacon with a plant flag+cell — every teammate already parses it. Secondary nits: plant gate `regionReach >= 12` uses the nb[]-flooding body-blind metric (the C7 issue) — a ≥12-cell pocket passes; `friendDist_<=6` bounds the damage but the metric is the known-weak one.

## v200 — verified: the anchor now fires

**Reachable states confirmed.** `champAnchorId_ == w_.chId` (policy.hpp:187-189): when the champ's report goes stale, locateChamp resets `champId_=champHead_=-1` but `w_.chId` persists — noteChamp only ousts it on a fresher/better report (world.hpp:335-338), never on age. So the else-if matches through the stale window → the intended off-vision conveyor is LIVE now (vs the dead code I flagged in v198). Also carries the v182 fixes correctly: evidence-round stamping (`champAnchorRound_ = round - champAge_` — no age laundering), `min(champAnchorAge, feedHeardDie)` = 30-window, `w_.visible(champAnchor_)` known-empty clear.

**Residual issues, ranked:**

- **(a) Queen-champ can never anchor through this path (medium-low).** When champId_=ourQueen (queen-branch), champAnchorId_=ourQueen ≠ w_.chId → during queen-alive games no anchor accumulates; on queen-report staleness the feed stream drops straight to fallback election, losing up to ~30r of convergence. Consistent with "anchor = worker-champ" scope — but v202 tried to fill exactly this hole and failed differently, so the hole is real: decide explicitly whether stale-queen feed continuity is wanted.
- **(b) `qRamAdjMinTiles=600` is the same shape-blindness as midFeedMinTiles (medium).** NC is area, not topology: the gate admits qOS(875), trophy(625), weakhold(600), plus all corridor-class maps (maze/trauma 1152, slithery 1701). It only removes arena/Colosseum/default_small/stripes/devil/dilemma/portals/TD — i.e., exactly the maps where the fence was least costly anyway. If SMALL-map queen-fencing was the motive, qOS/trophy/weakhold stay exposed.
- **(c) Verified fixes:** density-centroid picks the cheb-6-densest beacon (a real occupied cell — fixes both the torus-seam midpoint and the mid-air centroid); feedRadius ordering moved role-stripping inside the post-radius else (out-of-radius abort no longer churns grower_/hunts_/escortOf_); leash `fd==INF → 64` closes the free-pocket hole.
- **(d) Nit:** `feedBurstDist=14 > feedRadius=12` — the 12-14 band is dead slack (radius abort kills feedHead_ first).

## v201 (deadEnd) — mechanically sound, premise engine-verified

**The U-turn premise is TRUE, not assumed:** `Step()` (engine/engine/src/actions.cc:41-43) tests `destination ∈ mBody` BEFORE `push_front` — the vacating tail is still in the body → any move into own body incl. the just-vacating tail = HitSelf. A len≥2 head inside a deg≤2 chain cannot retreat; the tip is certain death. dedie drops at the current cell vs at the tip — correct and earlier.

**Map construction verified:** deg from nb[] counts portal edges as exits (nb≥0 routes through portals — correct, they are real escapes); only tip→junction chains marked (walk breaks on deg≥3, marking tip through mouth); tip-to-tip unmarked — correct AND moot, tip-to-tip corridors are closed components unreachable from open space; `deadEnd_[dest]` entry penalty (30×L_) is fatal-priced but finite → cornered dragons still pick least-bad; dedie trigger is worker_-scoped (queen excluded — she has her own nav_.deadEnd trap scan; champ is worker_-flagged and included — acceptable, doomed anyway).

**Edges, ranked (all low):**
- **(a) Unpaired-portal over-mark:** nb=-1 (unpaired, unguessed) counts as wall → a chain containing an unpaired portal is marked; dedie fires before move eval, preempting the scout escape the worker could take. Rare — needs an unpaired portal inside a corridor.
- **(b) Coverage hole, not a bug:** lollipop deg-2 loops (cycle attached to a junction at one cell) have no tip → unmarked; a dragon longer than the loop circumference tail-bites walking the ring. Real trap class the map doesn't cover.
- **(c) Escorts/hunters dedie on duty** — consistent (same doom), but the die-in-place drop lands inside the chain where nobody can safely retrieve it. Mitigation is upstream (entry penalty), not the trigger.

## Ranked verdict

1. **v202: fix before gating** — the anchor-propagation + `chId==ourQueen` gate make the intended mechanism unreachable; a v202-vs-v200 gate currently measures only "queen self-orbits a post". Two-line-ish fix via client-side queenCell stability derivation.
2. **v201: gate-ready** — no reachable-states or legality defects; edges are low-impact.
3. **v200: gate-ready** — anchor verified live; the NC≥600 gates carry the recurring area-vs-shape caveat on qOS/trophy/weakhold.
