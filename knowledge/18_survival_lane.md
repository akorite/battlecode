# CHILD-SURVIVAL lane — report

Baseline: `abyss_st` (v99 ladder tip). Workbench: `abyss_cs` (copy). Benchmark: schooltime + trauma + slithery_fight, seeds 0-4 both sides = 30 games per A/B. Schooltime & slithery are side-locked in this harness → W/L is a coarse signal; same-side metric deltas are the honest comparator.

## 1. Diagnosis — what wall/self deaths actually are

Instrumented variant `abyss_diag` (BC_DEBUG on; verified behavior-neutral: mirrored schooltime replays are bit-identical, 99,200 events). 30-game attribution via `tooling/deathx.py` (reconstructs every dragon's body from dragonUpdate/dragonSplit events, classifies each fatal destination cell, names the dir-blockers at trapped-fallback time, and replays the entry move 1-3 rounds earlier).

Deaths per side per game (all 3 maps, 30 games, ~9940 deaths total across both identical bots):

| map | hitWall | hitSelf | hitOtherBody | h2h | wall+self/game/bot |
|---|---|---|---|---|---|
| Slithery Fight | 3660 | 3524 | 1630 | 2544 | **359** |
| Schooltime | 1486 | 1112 | 606 | 1904 | **130** |
| Trauma | 64 | 94 | 22 | 0 | **8** |

Self-inflicted deaths are ~60% of all deaths, confirming the premise. BUT the composition kills the "accident" hypothesis:

- **hitSelf is 86% ownNeck** (reversal into the 2nd body segment) + feed suicide; zero accidental own-body hits logged. Every ownNeck death was a `why=trapped` (no-legal-move fallback pick) or `why=feed` (intentional euthanasia, L≤6, r400-490).
- **hitWall is 77% free_kelp** (stepping onto a kelp edge) — again 100% `why=trapped`: the dragon dies into kelp because every dir was already illegal. Near-zero "walked into an unseen wall" deaths: fog deaths don't appear in logs at all.
- The engine's trapped-fallback ranks `enemyHead < kelp/ownBody < friendHead` — it deliberately picks kelp over an ally head when everything is fatal, which is why hitWall dominates hitSelf.

So hitWall+hitSelf ≈ one phenomenon: **trapped suicides** (~61% of all diag-bot deaths; ~85% of fatal turns had ZERO free dirs). The kill cell (kelp vs neck) is cosmetic — entrapment is decided 1-3 moves upstream.

### The seal channel: allies, not enemies

Dir-blocker attribution at the trapped turn (843 annotated deaths): **~75% of fatal seals are ALLY bodies** (4175 ally vs 47 enemy vs 3 unknown blocking cells). Top patterns: `kelp2+drag1+neck` 380, `kelp3+neck` 160, `drag3+neck` 122, `kelp1+drag2+neck` 122. The swarm boxes itself.

Entry-move analysis (the move INTO the cell where it died 1-3 moves later): dests chosen had geometric exits 2→1004, 3→440, 4→436, 1→130 — dragons enter normal-looking cells that seal within a round as allies converge. ~85% of fatal positions already had `space<need` (the area-flood veto fires as -1000 but is taken anyway when nothing better exists — it's a last-resort ordering, not an avoidance mechanism).

### What the code does today (baseline reads)

- `scoreFrom` illegals: kelp edges, unpaired portals, own body, teammate-last-exit (`buildBase` line ~537: ally heads with exactly 1 exit have that exit INF'd), h2h trade branch.
- `blk[c]` timing: own segments vacate (seg i frees at L-i+1); **all other dragons' cells = INF permanent walls** — ally bodies are modeled as never moving, which systematically over-seals corridors the swarm actually shares.
- Space veto `space<need` = pure area flood — not turn-around-aware: a 1-wide cul-de-sac holding `need` cells passes.
- Trapped fallback orders death types only — no "delay death" objective among fatal picks.
- No crowding/anti-cluster term exists anywhere (friendDist_/enemyDist_ fields exist but only feed yield/hot/escort logic).
- `feed` suicides (r400-490, L≤6) are intentional champion-fueling — 679 in the batch — not a loss channel.

## 2. A/B results (each = 30 games vs abyss_st)

### f1 — roomy-flood veto (REJECTED, -6 = 12-18)

`nav.hpp`: added `floodRoomy` (counts reachable tiles with ≥3 neighbors usable next step — turn-around room); `policy.hpp`: veto `space<need` replaced by `roomy<need`, same -1000+terminal shape.

| map | cs | st |
|---|---|---|
| schooltime | -2 | +2 |
| trauma | -2 | +2 |
| slithery | -2 | +2 |

Same-side: slithery alive improved +5-8 (cs 62.8/58.2 vs st 57.4/50.6) — the veto DID cut cul-de-sac deaths; but schooltime-A collapsed 13.6→5.4 alive and tiebreak margins suffered. Mechanism of failure: `roomy<need` veto also forbids 1-wide pockets the hide/escort mechanics deliberately use (queen hiding = sit in a pocket), and marking such moves `terminal -1000` removes them from eval rescue exactly when space is scarce — the weak side dies faster, not slower.

### f2 — ally-crowd penalty (SHIPPED-CANDIDATE, +8 = 19-11 = 63.3%)

`common.hpp`: `wCrowd=1.0`. `policy.hpp` scoreFrom at k==0: `danger += wCrowd * (# dest neighbors occupied by an ally part)` — occ cells with id-parity == own team; own body absent from `occ` so the swarm, not our length, is priced.

| map | cs | st | verdict |
|---|---|---|---|
| schooltime | +4 | -4 | won both sides (+3 A, +1 B) |
| trauma | +8 | -8 | dominant (+5 A, +3 B) |
| slithery | -4 | +4 | lost tiebreaks |
| **total** | **+8** | **-8** | **63.3% — over the 60% bar** |

Same-side deltas (per game, both sides):

- schooltime A: alive 47.2 vs 31.8 (+15), totlen 222 vs 157 (+42%) — massive survival gain on the previously-doomed side.
- schooltime B: alive 50.0 vs 25.6, totlen 286 vs 154.
- trauma: queenLen 5.6/5.4 vs 1.4/0.6 — queens live ~4x longer; longest 11.4/6.6 vs 6.2/7.8.
- slithery: alive even-to-better (59.0/56.4 vs 60.0/52.2) but longest-dragon tiebreaks lost on B (15.4 vs 18.6).

Death mix (per bot per game): slithery own wall+self **301.4 vs 410.2 (-26%)** — the crowd penalty really did cut ally-seal suicides. Schooltime ~flat (138.2 vs 133.6 — the wins there came from faster pushes/eliminations, not fewer deaths: cs-as-A eliminated st at r146 on seed3). Trauma ~flat (8.5 vs 7.7).

Mechanism: dispersion penalty spreads the swarm so ally bodies stop converging into corridor mouths; queens and growers keep pockets but stop getting sealed by their own escort traffic. On slithery (dense combat arena) the same dispersion weakens mob packs — longest-dragon concentration drops. Note death-count confounding: schooltime-B shows deaths +134 AND alive +24.4 simultaneously — dispersion opened space for +158.8 splits/game, so a bigger population both dies and survives more. Alive@end, longestDragon and queenLen are the honest survival metrics; raw death counts track population churn.

### f3 — crowd penalty exempted in combat range (SHIP CANDIDATE, +10 = 20-10 = 66.7%)

Same as f2 but skip penalty when `enemyDist_[dest] <= 3` (an enemy head within 3 BFS steps) — restores mob cohesion at contact while keeping civilian dispersion. Hypothesis: recovers slithery longest-dragon margins while keeping the schooltime/trauma gains. Confirmed on slithery, half-confirmed overall:

| map | cs | st | vs f2 |
|---|---|---|---|
| schooltime | -2 | +2 | worse (+4 → -2) |
| trauma | +8 | -8 | same (+5 A, +3 B) |
| slithery | +4 | -4 | flipped (-4 → +4) |
| **total** | **+10** | **-10** | **66.7%** |

Same-side deltas (cs − st per game):

- slithery A: deaths **−166** (hitWall −94.6, hitSelf −46.0, otherBody −32.6), alive@end +2.4 — the survival fix and the win flip on one side.
- slithery B: deaths −64.8 (hitWall −31.6, hitSelf −23.8), longestDragon +3.2.
- trauma A: queenLength **+4.6** (6.0 vs 1.4); trauma B: **+3.8** (5.4 vs 1.6) — queens live ~4× longer; that's the +8.
- schooltime A: deaths −71.6 but longestDragon **−9.8** (13.8 vs 23.6), alive flat; schooltime B: alive +3.6 only (f2: +24.4) — the ≤3 exemption re-admits ally seals inside scrums, and schooltime's dense corridors mean most fatal seals ARE combat-adjacent. Not seed noise: same-side alive collapsed vs f2 (+0.0/+3.6 vs +15.4/+24.4) — mechanical, not random.
- Trauma-side story: dispersion keeps the queen's pocket reachable — splits & pearls roughly even, deaths flat; queens simply stop being sealed.

Verdict: f3 beats f2 on aggregate (+10 vs +8) by recovering the combat-mob penalty while keeping trauma, at the cost of schooltime's edge — which same-side metrics show is mechanical, not noise. Both clear the 60% bar; ship preference = f3 if slithery matters on the ladder, f2 if schooltime does.

### f4 — tighter combat gate, enemyDist ≤ 1 (killed at 10/30, inconclusive)

f3's ≤3 exemption covers a 37-cell BFS disc — broad enough to re-admit sealing deaths near any contact. f4 narrowed it to `enemyDist_[dest] <= 1` (only dests literally adjacent to an enemy head). Batch stopped mid-run per instruction; the 10 completed games were trending schooltime-positive but are too few to call. Natural next probe if these variants are iterated further.

## 3. Suffocation feasibility (steering data point)

In abyss self-play the enemy's deaths are 100% hitHeadToHead — zero noValidAction (table above). The opponents' 111/game noValidAction figure is produced by OUR bodies sealing THEIR exits incidentally — the same mechanism that traps us, aimed outward. Deliberate suffocation is architecturally expressible:

- Cheap version (no BFS): when `dest` is adjacent to an enemy head, count that head's still-open exits (4 neighbors minus kelp/unpaired-portal edges minus occupied cells). Bonus when our head lands on one of its exits (exits −1); large bonus when exits → 0 — the enemy's next turn has no legal action = guaranteed noValidAction death (it can't even suicidally trade h2h if we occupy, not adjacent-attackable).
- Existing machinery supports it: `enemies_`/`enemyDist_` fields already BFS each enemy head; `wDanger`/`localOk` already weight enemy-adjacent dests; a "choker" role can reuse the `assassin_` flag pattern. Cost is O(1) per enemy-adjacent candidate — well inside the 75ms turn budget.
- Direction of the term: currently `danger` PUNISHES parking next to enemy heads unless a trade is taken; a choke-reward flips that for exit-occluding dests where we DON'T trade (denial without exchange). Feasible, but fights the same anti-clustering force as f2 — the two compete for the same neighbor cells (f2 already demonstrates allies sealing; f3's combat exemption is exactly the gate a suffocation term would need).
- Caution: boxing requires bodies committed to exits — cells our dragons then occupy = they're immobile bait the enemy may trade through; and boxing a LONGER enemy near our short ones inverts the h2h odds. Map-scoped opportunity on killbox maps (trauma/portal-dense) where pockets abound; weak on open maps (schooltime) where exits re-form.

## 4. Exact commands

```bash
# workspace
mkdir -p ~/battlecode && tar -xzf ~/attachments/*/bc_workspace5.tgz -C ~/battlecode
uv tool install unswbc
cp -r ~/battlecode/workspace/abyss_st ~/battlecode/workspace/abyss_cs   # workbench
cp -r ~/battlecode/workspace/abyss_st ~/battlecode/workspace/abyss_diag # + BC_DEBUG edits

# diagnosis (30g instrumented mirror)
python3 tooling/match.py --bots abyss_diag abyss_st --maps schooltime,trauma,slithery_fight --seeds 5 --tag cs_diag --jobs 5
python3 tooling/deathx.py results/cs_diag/replays --csv /tmp/deaths30.jsonl

# A/B (per fix)
rm -f ~/.cache/unswbc/wasmbots/abyss_cs-*.wasm   # after editing headers
python3 tooling/match.py --bots abyss_cs abyss_st --maps schooltime,trauma,slithery_fight --seeds 5 --tag cs_fN --jobs 5
python3 tooling/wl.py cs_fN                     # per-map/side W-L
python3 tooling/sdiff.py cs_fN                  # same-side metric deltas
python3 tooling/deathx.py results/cs_fN/replays # death-mix deltas

# To re-verify a shipped variant (f3 shown):
cp -r workspace/abyss_combat workspace/abyss_cs
rm -f ~/.cache/unswbc/wasmbots/abyss_cs-*.wasm
python3 tooling/match.py --bots abyss_cs abyss_st --maps schooltime,trauma,slithery_fight --seeds 5 --tag verify_f3 --jobs 5
```

## 5. Deliverables (in cs_variants.tgz)

- `abyss_crowd/` — **f2**: crowd penalty, 19-11 (63.3%). Diff vs st: `wCrowd` param + 11-line block in scoreFrom.
- `abyss_combat/` — **f3**: crowd penalty + `enemyDist_>3` gate, 20-10 (66.7%). Best aggregate.
- `tooling/deathx.py`, `tooling/wl.py`, `tooling/sdiff.py` — death attribution, W-L, same-side metric tools.
- This report (CS_report.md).

Both shipped variants have BC_DEBUG off and are single-concern diffs against abyss_st.
