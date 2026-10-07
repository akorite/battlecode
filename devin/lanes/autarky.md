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

---

# Adversarial review — abyss_v213 vs v209 (queen escape sprint)

Scope: escape mechanism only (94-line diff). Verified against engine truth at engine/engine/src/actions.cc (`Move()`/`Step()`).

## Kill defects, ranked

**K1 (high) — the path cap admits engine-illegal escapes for exactly the queens it serves (L≥5).** The cap `min(freeSteps(L)+L-2, qEscapeMax)` models "ceil(L/4) free steps + paid steps to len-2". The engine implements neither: `mustPayForStep = stepIndex > 0` — only step 0 is free; EVERY later step requires `body.size() > 2` and pops an extra segment. True max path = `1 + (L-2) = L-1`. Deviation = `freeSteps(L)-1`: L=5 → allows 5 vs legal 4; L=9 → allows 10 vs legal 8; L≥11 → qEscapeMax=10 binds below L-1 (safe). A path longer than L-1 dies mid-flight: at the paid step where body hits 2 the engine emits "can't pay for step N" → **NoValidAction kill** — the queen suicides mid-escape having bled ~L-2 segments, strictly worse than eating the ram (same death, body scattered along a corridor instead of dropped at the pin). Fix: `maxSteps = min(L_-1, p_.qEscapeMax)`.

**Corollary for the board — the "ceil(L/4) free moves" premise is wrong.** Rules doc (handoff/knowledge/01_rules.md) + engine agree: 1 free cell, each extra costs 1 segment. `freeSteps` is a codebase-wide fiction with asymmetric damage: `reachOf()` over-screens enemy reach by ceil(len/4)-1 (conservative, harmless); twoStep's `paid = freeSteps(L)<2` under-charges (len≥5 2-steps do pay 1); the slay-reach cap at :608 has the same over-allow suicide hole as this escape; my v158 champStep silently paid more than modeled. Recommend one sweep over every `freeSteps(...)+L-2` and `paid`-model site — the formula should be `steps-1` paid, `L-1` cap everywhere.

**K2 (medium) — `pathCost` under-models payment → bookkeeping drift → compounds K1.** `pathCost = max(0, len-freeSteps(L))` but the engine charges `len-1`. main.cpp pops `pathCost` segments for its own body model (`i>0 && pay-->0 && body.size()>2`) → the model lands `freeSteps(L)-1` segments too long → next turn's `L_`/markBody computed on a phantom tail → inflates the NEXT escape's affordability and blocks cells she no longer occupies. Fix: `pathCost = (int)pth.size() - 1`.

**K3 (medium) — phantom pins via heard ghosts.** `heardEnemies_` persist to `heardEnemyMemory=8` and `rammed()` weights them identically to seen enemies. An 8-round-stale relay's reach field can make all landings read "rammed" → the escape pays real body fleeing nothing. Soft-pricing conventions tolerate ghosts; a mechanism that spends body on the pin-test should use seen enemies (or `heardFresh<=3`) for the *trigger*, heard fields only for terminal safety.

**K4 (low-med) — terminal safety under-screens.** `e.dist` BFS walls her ENTIRE current body — enemies can't route through cells she is vacating this turn → a terminal reading `!rammed` may be reachable through her vacated trail (enemy moves after her action resolves). Same convention as the ~1730 screen but for destination choice it yields false-safe terminals: pays, lands, dies anyway. Bounded; acceptable as-is but worth knowing.

**K5 (low) — conservative under-triggers, benign.** `blk<=1` excludes the vacating tail (markBody stamps it 2 — matches the engine's still-body-at-step-time rule ✓) but also every teammate cell and teammate-exit reservation → `anyLegal`/`queenEscape` miss paths through cells vacating at step ≥2 or cells a teammate is leaving. Safe direction. hiding_ queen (len 2) → `maxSteps<2` → benign dead branch. grower_/lead_ queens can escape — correct.

## Verified correct (explicitly checked, no defect)

- **Mid-path interception is impossible**: the engine resolves each dragon's whole MOVE atomically — enemies can only hit her terminal head (or her body, which kills *them*). The comment's claim holds.
- **blk completeness**: ownBlk = base_ (all `w_.occ` occupied cells → INF, enemies AND teammates) + ownExtra + teammate-exit reservations + own body → the BFS cannot route through other dragons.
- **Trigger semantics**: `anyLegal && !anySafe` = "every legal landing is inside ram reach" — the right pin test. Placement after trySplit is correct (a blocking split preempts; a pinned queen's own split leaves her head on the cell anyway).
- **`rammed` ≡ the screen's formula**: per-enemy `e.dist` is a BFS field from the enemy head over `blk` (horizon-bounded, capped by maxRivalFields/maxHeardEnemyFields); `dist[cell] <= reachOf(visible)+reachBoost+bonus` with the same NC≥600 `qRamAdj` gate — equivalent to lines ~1730-1750.
- **`e.dest=-1` + path emit**: matches the established slay-reach convention (dest unused in the `!c.path.empty()` emit branch); safeFirst redirect is a benign fallback.
- **Portal hops are legal mid-path** (nb routes through paired portals) — the escape can genuinely teleport; upside, not a bug.
- **Pearls en route offset payment** (paid step onto pearl = net 0 in the engine) — the BFS ignores this; misses longer food-path escapes, conservative direction.

## Verdict

Fix K1+K2 before gating (both are one-expression changes; K1 can convert "rammed anyway" into a strictly worse suicide). K3 worth the seen-only trigger guard. Mechanism itself is sound: reachable, well-placed in decide(), and the engine semantics it relies on check out.

# Colony-blob hypothesis measurement (autarky lane) — FALSIFIED, no v225 build

Task: measure whether winners fight as a compact swarm while we spread; if yes, prototype cohesion pull (wCohere*dist/6) in abyss_v225 vs v209.

## Data

Corpus: 137 replays parsed (`analysis/blob_study.py`): top_replays 100, ladder_replays 7, our_replays 30; 117 decisive games carried paired stats (`analysis/blob_paired.py`). Per roundStart per team: median pairwise chebyshev (torus), mean dist to circular-mean centroid, per-dragon nearest-ally dist (nn), straggler frac (nn>8), deaths ≤10 vs >10 from own centroid (death loc = last dragonUpdate head; dragonDeath carries no position).

## Pooled distributions (non-351 games): winners are MORE spread, not less

| phase | medPair W/L | cenDist W/L | nn med/mean W | nn med/mean L | alive W/L |
|---|---|---|---|---|---|
| early (<120) | 13 / 13 | 9.1 / 8.9 | 4.0 / 4.4 | 4.0 / 5.1 | 17 / 14 |
| mid (120-330) | 15 / 14 | 12.6 / 10.4 | 3.0 / 3.2 | 3.0 / 4.0 | 40 / 28 |
| late (330+) | 16 / 14 | 12.9 / 10.5 | 4.0 / 4.3 | 4.0 / 4.6 | 30 / 24 |

Footprint (pairwise, centroid-dist) is LARGER on the winning side — losers get compressed into a pocket. The only tighter-winner signal is the nn MEAN (3.2 vs 4.0 mid): winners have fewer isolated stragglers, not more density.

## Paired per-game (the right comparison — controls map/matchup)

mid: W−L nn = **−0.48** mean (−0.23 med), W−L alive = **+12.6**. The nn edge is fully accounted for by army size:

- winner-fewer-alive games (n=25): winner tighter in **2 (8%)**
- winner-more-alive games (n=75): winner tighter in **61 (81%)**
- tighter>0.3: 44% of games; looser>0.3: 21%

late: W−L nn = −0.08 — coin flip (tighter 31% / looser 39%); alive still +5.6.
straggler frac: W−L = −0.023 mid — the only cohesion-adjacent edge, small and size-entangled.
Our corpus (n=23 decisive): same shape — nn −0.69 with alive +13.8; winner-fewer-alive n=5, tighter 0/5.

## Deaths vs own centroid

Winner side dies NEARER its centroid: 39% of deaths ≤10 cells vs 36% loser. Opposite of "losers die isolated" — consistent with die-in-place feeding (bodies dropped inside the swarm where the champ eats).

## Verdict: hypothesis not supported → skipped the v225 build

Condition for the prototype was "winners significantly more compact" — measured, they are not:

1. Cohesion (nn) is a **readout of army size, not an independent lever** — winners are tighter because they have 40 dragons in similar territory (8% tighter when they field fewer).
2. Winners' footprint is **larger** (+2.2 cenDist mid): they hold more territory. A centroid-pull `wCohere*dist/6` on idle workers would contract the swarm toward the losing configuration — wrong sign on the measured effect.
3. What the data DOES support is already our direction: numbers dominance (+12.6 alive mid) = feed efficiency / consolidation; straggler suppression (−0.023) is the only live cohesion signal and is better served by escort/not-dying-isolated than a global pull.

**Recommendation: don't build wCohere.** If a cohesion test is still wanted, the honest variant targets the nn TAIL (penalize targets when no ally within ~8), not centroid distance — but the effect size (−2.3pp stragglers) is small and entangled with survival.

Caveats: botA/botB are empty in this replay format — can't isolate our side; within-game W/L contrast in our 30 games reproduces the population pattern anyway. Deaths located at last-seen head (accurate to last move). Centroid uses circular mean on the torus (correct across wrap seams). Heads seeded from map dr spawns; splits assign child teams.

Note: origin/devin/v120 STATE.md already mentions a "v225 candidate" — if a build ever happens on this lane the name may need bumping.

# v237 ship-candidate review (autarky lane) — vs live v168

Scope: workspace/abyss_v237 on origin/devin/v120 @ daa44c4 vs abyss_v168. Diff = policy.hpp (15 hunks) + common.hpp; main.cpp is comment-only identical. Described composite (lateSplit release, keepEvery60, queenBudUntil450, v200-line anchor) verified present, PLUS two arms not in the description: the v213 queenEscape AND a tradeSlack tightening (tradeSlackSmall=0 on NC<=900 boards).

## Defects ranked

**1. HIGH — K1 unfixed: queenEscape's cap still admits engine-illegal paths for exactly the queens it serves (L in [5,10]).** policy.hpp `queenEscape`: `maxSteps = min(freeSteps(L_)+L_-2, qEscapeMax)`. The engine (actions.cc) gives only step 0 free — every later step needs body>2. True legal max = L-1. For L in [5,10] the cap exceeds L-1 (L=5: cap 5 vs legal 4; L=9: cap 10 vs legal 8). A queen whose only escape lands at the cap picks it (BFS takes nearest-safe), walks until the body can't pay, dies to NoValidAction mid-flight — strictly worse than eating the ram. Hidden queens are len 2-6: the kill window covers the common case. Fix: `maxSteps = std::min(L_-1, p_.qEscapeMax)`.

**2. MED — K2 unfixed: pathCost under-model.** `pathCost = max(0, pth.size() - freeSteps(L_))`; true paid cost is `size-1`. main.cpp's `pay` loop under-pops → bot's world.body keeps a phantom tail → next-turn own-blk/legality mis-evaluation. Same one-line fix family: `pathCost = size-1`.

**3. MED — the verify answer: lateSplitUnits=9999 IS a real release but bounded by a second gate — the feedRound total-split veto.** trySplit:1916 `if (w_.t.round >= p_.feedRound) return false` (pre-existing) kills ALL voluntary splits from feedRound. p_.feedRound = eff_.feedRound = 320 on corridor-class (w*h<=2000, most maps), 360 on big. So the release band is **[300,320) on corridor maps (20 rounds), [300,360) on open (60 rounds)** — "churn to the bell" overstates it; post-feedRound splits stay dead. (The die-in-place conveyor is unaffected — it's a separate `split,n=0` emit.) If the intent was pre-window mass-stocking it works; if it was release-to-499, the veto is in the way. Correctness clean otherwise: gate = `units>=9999` never fires; L_>=swarmSplitLen+roominess checks unchanged; unitLimit=64 (engine default, no map override) bounds total units; splits halve mass so no explosion past array bounds. Watch-item only: 64 dragons x per-dragon deadline — no timeout mechanism concern.

**4. MED — queenBudUntil=450 is partially dead.** Same feedRound veto caps ALL buds at 320/360, and the grower arm's `lateGame()` (midEnd=400 corridor/450 open) sits just behind. Effective extension: 250→320 corridor / 250→360 open (+70/+110r), not the +200 the param implies. The [feedRound,450] range is unreachable.

**5. MED — K3 unfixed: heard-ghost pins.** rammed() weights heardEnemies_ (<=8r stale relays) identically to seen enemies → a phantom can fake-pin the queen into burning body. Trigger on seen enemies only; heard for terminal safety is fine.

**6. MED — unadvertised arm: tradeSlackSmall.** `slack = NC<=900 ? 0 : 1` — on weakhold(600)/trophy(625)/qOS(875)/small-board class, trades tighten to net-zero-length (myLen<=enemyLen, no +1 slack). Mechanically fine, but it's a real melee rule change not in the described diff — if small-map splits move, attribute here alongside lateSplit/leash/midFeed.

**7. LOW — feedBurst sign.** `round - feedAt <= feedBurstRounds` is true for every round < feedAt (negative delta <= 20) → midFeed anchors carry a permanent x3 pull, not a 20-round front-load. Effect = midFeed is stronger than labeled; literal intent needs `0 <= round-feedAt <= 20`.

**8. LOW — corpse-site residual.** Anchor else-if correctly caps at min(champAnchorAge,feedHeardDie)=30r and adds `w_.visible(anchor) -> clear` (v182's known-empty fix shipped). Residual: a dead champ's anchor still feeds for up to 30r if nobody sees the corpse cell — bounded, much better than v182's leak.

**9. TRIVIAL — dead weight.** `p.feedRoundBrawl=300` write is dead (brawl block early-returns — pre-existing); `workerRegionNorm=0` disables the discount but regionSize_ still runs one BFS per dragon per game (harmless); `feedBurstDist=14 > feedRadius=12` is dead slack (radius aborts first). midFeedMinTiles=600 is still an area-gate not a shape-gate — fires on maze/trauma/slithery/qOS corridor boards (documented concern, inherited deliberately).

**10. LOW — escape ignores the counter-ram option.** Trigger legality uses blk<=1, which excludes enemy heads — a pinned queen that could trade head-to-head flees instead. Conservative direction; fine as shipped.

## Verified correct (explicitly checked)

- **Anchor machinery fires now**: `champAnchorId_ == w_.chId` (persists through staleness) OR the new `== w_.ourQueen && !queenDead` arm — a queen-champ can anchor. Evidence-round stamping kills the age-laundering. 30r clamp matches feedHeardDie — no zombie feeders. `w_.visible(anchor)` clear = fresh observation empties it. champAnchorId_ only stamped under `champHead_>=0` → never -1-vs--1 vacuous match.
- **feedHead_/feedAge_ reset per call** (:63,121) — the moved unconditional `if (feedHead_>=0)` block can't leak stale state; a dragon must pass a gate THIS turn to feed.
- **selfChamp_ can't self-feed**: selfChamp_ -> grower_ -> !worker_ -> exempt from midFeed and the window block. No champ-dies-at-own-position.
- **kParams block identical to v168** — no clobbers, champFallbackRound=330 confirmed in decl + kParams.
- **No new worker-split or opening-move vetoes** in the diff. trySplit's veto set is unchanged (eat/trade/defend/slay/attack-hunt/enemy-ban/roominess, all pre-existing). The escape is post-trySplit; chfeed is an emit not a veto.
- **Escape trigger**: `anyLegal && !anySafe` + placement after trySplit, before boxFeed — correct; dest=-1+path emit convention consistent; portal hops legal mid-path; pearl-landing payment offsets conservatively ignored.
- **Leash INF->64** fixed (unreachable pocket now max-penalized); leash correctly excludes hiding_/lead_ queens.
- **regionSize_ components** correct (wall-connected, portal-connected); bounded once-per-dragon.

## Verdict

Ship-risk concentrated in items 1-2: the escape's cap/cost model still assumes ceil(L/4) free steps that the engine never grants — for the len 5-6 queens most likely to trigger it, a max-range escape is certain death, worse than the pin it flees. One-expression fixes (`min(L_-1, qEscapeMax)`, `pathCost=len-1`). Item 3-4 are semantic: the release/bud extensions are real but truncated by the feedRound veto — if that's the intended design, correct the comments; if to-the-bell churn was the goal, the veto needs carving. Everything else is bounded or pre-existing.

---

## v310 champ-hunter forensics (mechanism verdict) — 2026-10-04

**Method:** v310_smoke replays aren't on this box and aren't in origin/devin/v120 (they live on the integrator's machine), so I replicated locally: built `workspace/abyss_v310dbg` = v310 + `#define BC_DEBUG` + two `out_.log` lines in buildSquadTargets (`chelig` fires per-dragon-round whenever a len>=8 non-queen enemy candidate exists, logging its len/seen-flag/myDist/swarmRank; `chassign` logs assignment with gain+mult). Ran `kmatch --cand abyss_v310dbg --base abyss_v263 --maps all --seeds 1 --jobs 2 --keep-replays` (44g, both seats), parsed all replays (`analysis/champhunt_audit.py`). Bot LOG lines land in replays as `dragonLog` events — cheap, exact instrumentation. Note the dbg build pays a logging overhead tax; pair score ~43% here vs their flat-50% — same read (every map pair seat-locked).

### Verdict: THE MECHANISM FIRES. The flat smoke is a map-set artifact, not a dead mechanism.

**(a) eligible-enemy frequency:** len>=8 non-queen enemy candidates exist in only ~30% of games (13/43 had any). On every small/elimination map — trophy, devil, Colosseum, queen_of_spades, stripes, tower_defense, dilemma, autarky, portals, schooltime, stronghold, trauma, weakhold, prisoners — **zero eligible dragon-rounds**: games end by elimination before any enemy reaches len 8 (also matches: enemies there die before len 8 — sonar reports show no len>=8 sightings at all). On open maps (big_empty, default, australia, around, slithery, maze, islands) eligibility is frequent once it starts (~2 eligible dragons/round in an eligible round). If the 34-game smoke ran `std`/`small`-weighted maps, ~0 hunts is the expected outcome — the flat 50%/34 and unchanged end-longest are *predicted* by map composition alone.

**(b) assignments + convergence:** gates pass when eligible — 1084/1344 eligible dragon-rounds passed both `myDist<=20` and `swarmRank<3`; 1238 assignments fired. The binding constraint is eligibility existing at all, not the gates. BUT convergence is mostly solo: median **1 distinct hunter per (target, 20r window)** (max 6) — rarely are 3 workers inside dist-20 of the same target. Hunters do converge: med dist at assign 5 → min 3 within 12r; 580/1230 reach cheb<=2 of the target cell; 216/1230 never got closer (target moved / hunter died / reassigned). Then they disengage (med dist back to 6 by +12r) — expected on negative-trade hunts: they come, ram or fail, and the assignment drops.

**(c) hunted vs unhunted death rate:** modest uplift — hunted len>=8 enemies died **30% (8/27)** vs unhunted len>=8 **25% (28/114)**. Within 15r of an assignment, hunted targets logged 193 hitHeadToHead deaths (+31 hitSelf = head-into-body ram attempts) — the kills DO happen. On big_empty specifically hunted 12/17 (71%) vs unhunted 59/79 (75%) — on brawl maps everything dies at that rate anyway, so the marginal effect there is nil. Small pools; the honest read is "fires and kills sometimes, no big delta".

### Code defects found (in buildSquadTargets/scoring — none block the mechanism)

1. **`champ-ram` cand is unreachable dead code** (policy.hpp ~1413). The champ target is always pushed into `hunts_` at assignment, so `huntAt(s.head)` in the occupied-dest branch above it always matches first → every ram of the hunt target is scored `100.0 + h->gain` with why="trade"/"defend", never reaching the `champHunt_ && s.id == champHuntId_` else-if. Consequence is observability only: the *intended* behavior (ram even at negative trade) still runs through the huntAt branch, which has no `tradeOk` guard — verified live: 0 champ-ram turns logged, yet 193 h2h kills on hunted targets. If the dedicated branch is wanted for the higher 70+visible bid or for visibility in logs, it must move ABOVE the `h &&` branch or set a flag why like `h->threat ? "defend" : (s.id==champHuntId_ ? "champ-ram" : "trade")`.

2. **Suspected negative-gain repulsion: FALSIFIED.** `gain = tgtSeen->visible - L_` (enemy minus hunter) — longer enemies give *larger* gain → `1.0+gain/4` multiplier is 1.25-6.0x ATTRACTION, never repulsion. Empirical: median gain +6, only 3/516 seen-assignments negative (hunters were len 3-6 vs targets len ~9). No bug here — I had the sign backwards.

3. **Real efficacy limiter (suspected, unverified): covered-victim veto.** scoreFrom occupied-dest branch: `cover>0 && !queen_ → return c` vetoes ANY head-ram when another enemy is within cheb-2 of the target's head. Winners' champs are escorted (queen study: escort ~5.6) → the exact targets this feature hunts are the ones rams can't touch. Likely binds harder than any other gate on open maps. If champ-hunt is meant to eat escorted champs, the veto needs a champHunt_ exemption (`if (cover>0 && !queen_ && !(champHunt_ && hid==champHuntId_))`).

4. **Stale-cell chasing:** heard-only hunters (champHuntId_<0) get +wChampHunt pull toward a last-heard position up to 20r old — 716/1230 assignments were heard-only, med dmin 4.0 vs 2.0 for seen — they converge on ghosts. Cap heard-target distance or use MsgChamp-style freshest-position relay for enemy champs.

5. Minor: swarmRank counts only `friends_` (visible teammates) — heard teammates don't vote, so two workers that can't see each other both self-assign as "nearest" — harmless (cap is soft anyway).

### Fix suggestion

Mechanism works; the smoke just needs a map set where len>=8 enemies exist: re-gate on `big` or open maps only (big_empty, default, australia, unsw, around, slithery, maze, islands ~x2 seeds) — ~16-20g shows the truth fast. If uplift still reads nil, the highest-leverage change is the covered-victim exemption (3): the feature's purpose is killing planted, escorted champs, and that single veto blocks most of those rams. champ-ram ordering fix (1) is free to fold in. Replays: `results/v310dbg_audit/replays/`; analyzer: `analysis/champhunt_audit.py`; instrumented copy: `workspace/abyss_v310dbg/` (local only, not pushed).

## v315 forensic — funnel composite loss classification + mechanism verification

Candidate: `workspace/abyss_v315` = v311 + `feedRound 340` + `feedMaxLen 7` + `queenChampMemory 999` (3-line diff vs v311 — queenChampMemory was already 999 in v311; effective delta = feedRound 360→340, feedMaxLen 6→7). Their smoke read 58%/81 (BIG 70%), queen-dead −9% — first funnel composite with a queen-survival gain.

Replays were not on this box or in origin/devin/v120 → replicated locally: **88g audit** (`--cand abyss_v315 --base abyss_v263 --maps all --seeds 2 --keep-replays`, tag `v315_audit`: **58.0% / BIG 66.7%** — matches their smoke) + **48g instrumented run** (`abyss_v315dbg` = v315 + `BC_DEBUG` → per-turn dragonLog telemetry, big maps only where the feed window engages, tag `v315_dbg`). Analyzer: `analysis/v315_funnel.py`.

### Loss classification (production rules: elim → longest → total LEXICOGRAPHIC — no queen term; verified engine scoring.cc)

37 cand losses: **18 ELIM / 17 LONGEST / 1 TOTAL / 1 DRAW**.

**ELIM — 18 (49%), proximate mechanism: pre-window swarm attrition, not funnel.** Our queen died in **18/18** (median r66, hitHeadToHead 13/18); theirs died in 13/18 (median r61). Median elimination r173 — all small maps + default/devil/weakhold corridor-adjacent. The feed window (r340+) never engaged; both sides trade queens early and our swarm loses the knife-fight. The −9% queen-dead arm can't help here — deaths are symmetric and early.

**LONGEST — 17 (46%), proximate mechanism: their champ out-consolidates ours post-queen-death.** Both queens died in 14/17 each side (ours med r345, theirs med r176 — queenChampMemory's queen-as-champ rarely survives to end: `queenEnd==longest` for us in only 2/17). Median gap 9 (mean 12.8, worst stronghold s1 A gap-60). **Their funnel recycled more bodies in 10/17** (nva med 58 vs our 35). But 4 losses break the volume story — we recycled *more* and still produced a shorter champ (queen_of_spades 35v3, stronghold 124v84, maze 121v115, australia 131v122) → **drop quality/lock precision differs, not just body count** (see funnel verification). big_empty s2 A was the opposite profile: minimal recycling both sides (18v15), their alive-60 swarm simply out-grew our champ.

**TOTAL — 1** (autarky s1 A: longest tied, total −6). **DRAW — 1** (portals s2 A).

### Funnel verification (instrumented, dbg side)

Production emit chain verified in code: `feedHead_` = queenCell (queenChampMemory≤999 stale) → MsgChamp fallback cell (≤champMemory) → champAnchor (≤30r, evidence-stamped, visible-clear) → emit requires `distToHead ≤ champFeedDist=2` where distToHead = BFS to the target's **neighbor cells** — emit-legal = manhattan ≤3 to the head (distToHead measures "distance to a cell adjacent to the target", not to the target — audit metric fixed accordingly).

Window-era emits (48g big-map instrumented run, dbg side): **100% of window nva deaths are `chfeed` emits on every map** (903/903) — zero can't-pay crashes in the feed window; the die-in-place is the ONLY nva source. 99.8% emit-legal (manh<=3 of locked feedHead_; the 2 outliers are log artifacts). Feeder lens 100% <= feedMaxLen=7 (med len 3; hist len2 364 / len3 273 / len4 128 / len5 66 / len6 44 / len7 28). Lock freshness: **87% locked a LIVE-seen champ (fa=0)**, 10% fa=1, 3% fa>=2 stale. Feed-locked dragon-rounds: 16,329 (18% live-sighting, 78% heard<=30, 4% stale>30); whys while locked: to-feed 16,065 (98%).

**Drop capture (ground truth, no sonar ambiguity): 847/903 (93.8%) of window drops had a teammate head within manh<=1 within 10 rounds.** The conveyor delivers — drops land where teammates are and get eaten. The raw "locked fh vs freshest team champ ping" distance reads med 17 (>6: 77%), but that is a *ping-consensus* artifact, not feeder error: MsgChamp pings on big maps report 2-21 distinct champ ids per round (split-brain election — each dragon pings ITS elected champ), so "the freshest ping" is usually about a different dragon than the feeder's lock. The feeder's own live sighting (fa=0, 87% of emits) is the real lock.

MidFeed era (r<340, NC>=600 boards): 3,604 chfeed emits across 48 games (~75/game) — the density-centroid recycling runs at volume and is also ~100% emit-legal (len<=5 99.6%).

Front-load confirmed by design (each side timed from its own feedRound — 340 vs 360): **54% of cand window nva inside the first 20r** vs base 33%; both med r+17. Base still recycles MORE overall (1,015 vs 903 — 12% more bodies) despite starting 20r later: our burst burns through the nearby-donor pool early then starves.

qlen@end (big maps, 48g): cand mean 3.79 / 10 nonzero of 48 vs base 3.17 / 6 of 48; queen-dead −5/48.

### qlen@end vs v263

Cand queenEnd mean 2.12 / med 0 (8/88 nonzero) vs base 1.58 / med 0 (6/88). On r500 games: queen alive at end **29.8% vs 17.5%**, queen len 3.11 vs 2.25, queen-dead/game 0.761 vs 0.830 (**−7pp**, matches their −9%). queenChampMemory works as designed while she's alive — she stays champ however stale her cell (pings reporting queen: cand 27% vs base 16% of all champ pings). But at ~76-83% queen mortality the effective funnel target is mostly the post-queen fallback champ — qlen@end is a thin tail statistic, not the funnel's main channel.

### Interpretation for the composite

- ELIM losses are funnel-independent — the 18 elim games are decided before r340 on small maps. The composite's BIG-map gains (66.7%) can't reach them.
- LONGEST losses are the funnel battleground: volume favors them (med nva 58 vs 35) and 4 losses show us out-recycling yet out-consolidated — precision is NOT the leak (94% capture); the lever is target-switch timing + donor allocation (see verdict).
- **Funnel verdict: WORKS AS DESIGNED — the loss channel is volume + target-switch timing, not drop precision.** (a) Emit machinery is airtight: every window death is a designed feed, 87% at a live-seen champ, 94% of drops eaten within 10r. (b) The LONGEST-loss mechanism is donor *volume* (their nva med 58 vs our 35) plus a **post-queen target switch**: in LONGEST losses our queen survives to med r345 (theirs dies med r176) — queenChampMemory keeps her champ-of-record until she dies right at window open, the anchor/election scrambles mid-window, and the burst has already spent the donor pool; their champ has been one stable feed target since ~r300. The 4 losses where we out-recycled yet still lost (maze 121v115, stronghold 124v84, australia 131v122, qOS 35v3) fit exactly that shape — mass went to a dying-then-dead queen and a late-elected champ instead of one consolidated target. (c) queenChampMemory's queen-survival arm is real but thin (alive@end 29.8% vs 17.5%) — it delays OUR queen's death into the window where it now costs a target switch.

Suggested levers, ranked: (1) when ourQueen dies, re-elect the champ from the FRESHEST teammate sighting and re-stamp champAnchorRound_ immediately (kill the ≤30r anchor drift at the switch); (2) let feeders who locked the dead queen convert her corpse-pile into the NEW champ's feed (they already die there — the drop is capturable by anyone within ≤1); (3) burst drain: 54% of feeds inside the first 20r of the window empties the radius-12 donor pool before the elected champ stabilizes — spread feedBurstRounds 20->40 or drop feedBurstMult 3->2 so donors arrive after the switch. None of these is a gating bug — the composite's gains are real; the LONGEST tail is a timing/donor-allocation inefficiency.

---

## v321 residual forensics (sub v124, gate replays)

Replays for `/home/ubuntu/bc/results/v321_gate/` were not on this box, so the gate was replicated locally at `--maps all --seeds 4 --jobs 2` with BOTH sides BC_DEBUG-instrumented (`workspace/abyss_v321dbg`, `abyss_v263dbg` — every alive dragon logs `L= id= fh= fa= sc= ch= hx= hy=` per turn). Analysis at partial run (~86/176 games, cand 58.1%, classes 18E/13L/4Q/1T — tracking their 53.5%/46-37-17 mix): `analysis/v321_residual.py`.

### Q1 — LONGEST class: concentration is real but the mechanism is conversion inefficiency, and it comes in three shapes

End-state top-3 + totals per loss (L = loss side, W = winner):

```
map        seed seat  our top3 (tot)      their top3 (tot)     longest-holders
australia  s1   A     [21,21,20] (308)    [22,20,17]  (72)     42v63
australia  s1   B     [21,21,20] (286)    [28,16,3]   (49)     65v73
australia  s2   A     [19,10,5]   (36)    [34,24,22]  (315)    87v33
australia  s2   B     [23,23,22]  (163)   [31,25,23]  (271)   120v103
maze       s1   A     [55,49,18]  (152)   [70,10,8]   (104)     5v6
stronghold s1   B     [47,27,21]  (98)    [50,10,5]   (70)     20v20
stronghold s2   A     [32,15,13]  (102)   [62]        (62)     56v44
big_empty  s1   B     [41,40,36]  (247)   [59,43,41] (1078)    45v29
big_empty  s2   A     [41,38,37]  (307)   [49,48,40] (1135)    42v22
big_empty  s2   B     [55,52,38]  (408)   [61,48,47] (1023)    48v35
autarky    s1   A     [35,5]      (40)    [52,16]     (68)     25v31
autarky    s1   B     [50,10]     (60)    [58,14,14] (100)     40v40
slithery   s2   B     [24,23,15]  (140)   [45,26,11] (128)     73v60
```

Three distinct loss shapes:

- **CONCENTRATION (australia s1, the cited shape):** we hold 4-6x their total mass but spread it over ~37 equal workers + three near-equal rivals ([21,21,20]); they condensed to a champ + escorts. Median end top-1 share in losses 0.17 vs winners 0.35; on australia specifically 0.07 vs 0.31.
- **VOLUME (big_empty x3):** they never consolidate — they keep 44-64 alive mid-dragons (total 1023-1135) and simply out-grow our champ (41-55 vs 59-61). Not a funnel race; a forage/survival scale gap.
- **KNIFE-EDGE (corridor maps):** symmetric funnels, 3-15 length gap.

Funnel-to-bell measurement (nva deaths per era, both sides, all 13 losses; feedAt=320 corridor/340 open):

```
era          nva W/L      near<=3      chfeed W/L    alive-pool W/L   med worker->longest dist W/L
era0         264/271      17%/18%      305/288       72/55            14/13
era1          58/26       19%/19%       88/54        29/16            16/14
era2          26/20       12%/30%       49/40        19/14            15/20
era3          20/23       20%/0%        39/44        12/16            18/17
```

**Neither funnel "runs to bell" — both fire the same era0 burst (identical 264v271 nva, near-adjacency rate identical ~18%).** The difference is what happens after: their pool collapses (72→12, feed conversions consume it), ours keeps ~16 residual donors drifting (medD rises to ~20) who emit a useless trickle far from the champ (era3 chfeed 44v39 — we emit MORE late, just too far to matter).

Where the concentration loss is born (australia s1 A, instrumented): our workers resolve a champ 86% of rounds (`ch+`) but lock a feed target only **1.0%** of eligible worker-rounds vs their 19.1% — the `feedRadius=12` abort kills us because our resolved targets sit med 19.5 away vs their 11.0 (only 28% of our resolved-target rounds are within 12 vs their 57%). Root cause is **target placement, not gate precision**: our champ-of-record free-ranges (traced id649: sc=1 continuously r420-499 while roaming 20+ cells/10r through all four map quadrants — the anchor pull `{champAnchor, 1.2, -1, 0.0}` decays `belief*gp(dist)` exactly like food, so once grazing carries it >~10 tiles off-anchor the pull can never recapture it). Their v263 champ anchors `=head` wherever it stands at plant time — inside the swarm by construction — so their workers resolve near targets and convert. Split-brain churn amplifies it: 14-19 distinct reported ch targets/round on our side at window open (multiple concurrent selfChamps because no dragon dominates — and no feeding because targets scatter — bistable failure).

**Q1 answer:** their post-death length concentrates in one champ parked inside the swarm remnant; ours distributes across 2-3 rival champs + a 30-50-strong foraging residue. Their funnel does NOT run to bell — it finishes in the first ~80 rounds by eating the whole pool; ours never engages the bulk of the pool because the feed target lives too far away (geometric starvation on big maps) or the body mass simply out-scales us (big_empty). Where our funnel does engage symmetrically (corridors), we lose knife-edge by 3-15.

### Q2 — ELIM class: hypothesis FALSIFIED — the queen does not starve; the swarm loses the melee first

18 elims, 15 replays analyzed. **Queen alive at elim round: 1/15.** Dead-queen timing: med **r67** (range r6-202), reasons **13x hitHeadToHead + 1x noValidAction** (weakhold — boxed, the dedie/pocket path). None die of starvation — noValidAction donations to her are ~0 both directions (nva 0-1/game; pre-window nva doesn't exist by design since the funnel targets the champ, never her).

Queen length trajectory r100→death: **flat L2-3** (L100 2-3, max 4; 4/15 never reached L>=4 so the `L>=hideLen+2` bud gate never even armed). Buds: 0-7 total (median 1). Team splits DO happen ([2-68/era in era0]) — the swarm grows by worker splits, not queen buds; her spawning contribution is ~0 by hide doctrine.

Causality runs the OTHER direction from the hypothesis: `cross` (first round our alive < theirs) lands r12-96, and at her death the swarm is already outnumbered 2v11 / 4v14 / 4v19 / 4v16 / 1v20 (or at parity 7v7/4v4 then bleeds out). Their queens die early too (med ~r100, mostly h2h) — but their swarm wins the opening melee, then their survivors mop up our len-2 queen.

**The elim mechanism: our swarm loses the r0-96 melee while the queen sits hidden at L2 contributing nothing (0-7 buds, zero combat power), then she's killed h2h as an exposed soft target.** "Starving queen" is wrong twice: (a) she doesn't starve, she's killed; (b) the donations that could feed her don't exist for either side pre-window. What the hide doctrine actually costs here is that our queen is a *pure liability* — no buds, no fight, can't even trade — so the effective early roster is workers-only vs their workers+queen.

### Combined read for v321

- ELIM (46%) is a pre-window melee problem, funnel-independent — queen-hide turns her into dead weight while the swarm bleeds out outnumbered. Lever: queen combat contribution before hideUntil, or bud-earlier doctrine (L3-4 buds) — the L>=4 gate starves her only function.
- LONGEST (37%) splits three ways: geometric conveyor starvation (anchor/pull + churn on open maps), volume out-scaling (big_empty — not a funnel problem), and corridor knife-edges (symmetric, small fixes). The single highest-leverage fix for the australia shape: **anchor-site or champ retention must keep the feed target inside the swarm** — e.g. score anchor candidates by own-swarm density/centroid distance, or make the anchor pull distance-flat (belief floor, not `bel*gp(dist)`) so a displaced champ actually returns.
- QUEENEND (17%, 4 here): theirs survive to end (qE 21/22 vs ours 0-18 on trauma) — same hide doctrine different outcome; worth a separate look but small class.
