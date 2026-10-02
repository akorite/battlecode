# 16. Architecture feasibility — can abyss-v95 reach top-20? (Oct 1)

Lane: architecture-feasibility. Method: replay-only analysis, 15 replays / 30 team-games
(tooling/coord.py, force-balance and alive-curve scripts). Buckets: OURS_top (our ladder losses vs
Stockfish/calc/WHQ/Cache-me-outside), OURS_weak (vs bnb/DFS-tier), plus Stockfish/calc/WHQ's own
games. All numbers are per-team-game means unless noted.

## 16.0 TL;DR

The single-policy per-dragon architecture is **not itself the blocker** — no replay signature
suggests top teams run a fundamentally different decision loop. The blocker is (a) a **round-phase
doctrine** we don't have (they bud-out at r0 and race mass r0-80; we move/fight from r0), and
(b) **zero sonar intel** (we are the only sampled team at 0 pings/action; everyone ≥1100 elo runs
2-4 tagged pings/action). One structural change — a doctrine phase controller — attacks the
mechanism that actually kills us (elimination at r150-440 after losing the r40-80 mass race).
Honest ceiling for that alone: ~1450-1550, not 1940. Top-20 additionally needs sonar merge
(already built in abyss_dev, unverified) and later assassin/feed roles. No rewrite needed.

## 16.1 Gap-table verification (each 14.2 row vs replay evidence)

| 14.2 row | claim | measured | verdict |
|---|---|---|---|
| Queen survival | queen dies r5-74 unscreened; fix = escort ring ~9-10, enemies ≥20, ~2 exits | **FALSIFIED as protection model.** All 30 tracked queens die (100%). qd_mean (min enemy dist to queen) = 2.5-9.7 for EVERYONE incl. winners; qd_ge20 ≈ 0 all teams. ring_med: ours 7.2 / SF 7.0 / WHQ 10.8. allies<10: SF 6.5 vs ours 3.2 — that's swarm mass screening, not a designed ring. Nobody keeps enemies away from the queen; winners keep a *swarm* that outlasts. Our queen dies h2h fighting as a normal swarm unit (88 moves, 1 split, h2h @88 in m821977), not noValidAction | Real gap = champId bug + queen trades like a regular unit; escort-ring target is mythology |
| Tagged sonar | we have 0; meta runs tagged protocols | **VERIFIED, worse than doc says.** sonar/action: ours 0.00 vs SF 3.88, calc 1.30, WHQ 2.12, opp_top 2.91, opp_weak 3.91 — even ~1361-elo bnb runs ~3.9 tagged pings/action. Only sampled team at 0 is us (and 1119-elo DFS). Zero-sonar is literally a bottom-tier marker | Confirmed; abyss_dev protocol (kSonarTag/MsgBeacon/MsgEnemy) is the fix path; verification-only cost stands |
| Swarm scaling | "splits fine; wipe is brawl-positioning, tune params" | **PARTLY REFRAMED.** splits150: ours 34-44 vs opp_top 170 / SF 202. maxAlive: ours 21 vs opp 50 / SF 64. But the wipe mechanism is a **mass race lost r40-80**, not per-fight positioning: both sides ~6 alive at r40; winners go 8→27→56 while we flatline at 4-11 then bleed out (h2h = 54% of our deaths vs 9-14% theirs). Our deaths are outnumbered 92-100% (5.6-6.8 foes vs 2-2.5 allies within cheb-5); SF deaths outnumbered 1-6%. They field multiple map-wide clusters (medPairDist 11-17); we are one small knot (4.7-7.1) | Param tuning won't close a 5x split deficit; needs an explicit breed doctrine (below). Note OURS_weak maxAlive 24-64: vs ~1360 we scale fine — the deficit only appears vs top pressure |
| Corpse economy | WHQ 51 suicides/g feeds queen to len 34.7 | **VERIFIED but reframed.** WHQ explicit suicides = 56/g BUT all ≥r245 — it's an endgame queen-dump, not an all-game rail. SF/calc run ZERO suicides; their hitSelf deaths (SF 217, calc 125/game) are dense-pack collateral + corpse-pearl recycling at fight sites (everyone dies at mean len ~2.0). Our feed block (r400-490) is the right mechanism, gated correctly — it just never matters because we die before r450 | Deprioritize: pays off only in roundLimit games (~47%) we currently never reach |
| Sprint | sprintTrade = kill-dive only; meta sprints surgical ~150/g | **VERIFIED + a bug.** Our sprints 13-18/g vs SF 75 surgical, opp_weak 169, calc 582 spam. Root cause isn't just narrow policy — sprint-kill gating uses `s.id == w_.enemyQueen()` and enemyQueen() is broken by the same champId bug (below), so the surgical sprint path almost never fires | Fix gating (enemyQueen = the other id∈{0,1}) then widen to escape+surgical |
| Queen assassination | needs sonar flag + converged squad | **PARTIALLY VERIFIED.** Both queens die ~100% of games — but mostly to brawl attrition and r0-5 spawn collisions, not coordinated dives. Top teams' queens die r0-5 in most games (m821961: both queens dead r0; m821977: SF's queen dead r2 — they won anyway). Assassination isn't what wins; mass is what wins. (kill-window data: our hunts never assemble a squad at the enemy queen) | Deprioritize vs swarm mass; becomes relevant only once we survive to midgame |
| Map doctrine | extend adjustByMap | **UNVERIFIED** — sample too map-poor to score per-map (Default/Autarky/Schooltime dominate losses but top opponents also win on those). Low-priority either way | Park |
| noValidAction deaths | ~21% of deaths; our queen boxed-dead | **FALSIFIED for us.** Our dNoVal = 0.0 both buckets. High noval appears in dense-swarms (WHQ 58, calc 30/game) as boxing collateral when maxAlive ~50-64 — a symptom of mass, not the bug that kills us | Drop from gap list |

Additional finding not in 14.2 — **champId() is a verified coin-flip bug**: `world.hpp:51
int champId() { return init.team=='A'?0:1; }` assumes A↔id0, B↔id1. Replay shows queen-id per team
varies per game on the same map (Schooltime A-queen=0 then 1; Slithery 0 then 1; Default A=1 both).
In our 5-game top-loss sample A-queen ∈ {1,0,1,1,0} → **champ grower absent in 3/5 games**; the two
games where champId was right produced our best masses vs top (m821962 Schooltime: maxAlive 64 —
the only top-tier game where we matched mass, lost on queen/tiebreak at r500). Correct rule is
universal and free: `amQueen = (myId<=1)` — the ids 0/1 ARE the two queens, one per team; each
dragon knows its own team. enemyQueen() = the other one. ~5-line fix, no architecture.

## 16.2 Behavioral signatures of top teams (from SF/calc/WHQ replays)

1. **r0 split cascade.** SF's entire starting line splits on round 0 (m821977: ids 0,2-7 all SPLIT
   childSeg=2; 3-4 dragons → ~10 alive at r1). Our opening (same game): all moves, zero splits.
   Everyone buds mostly len-2 children all game (child=2 dominates all teams' split mix) — the
   meta is bud-2 spam, not big-body splits.
2. **Breed-before-brawl.** Winners' alive curve: flat ~6-8 until r40, then 8→27→56 by r80-150.
   Losers' curve: flat 4-11 forever. The game is decided in that window; elimination follows at
   ~r150-440 (our losses) or r500 roundLimit (~47% of sampled games).
3. **Multi-cluster spread, not a deathball.** Winner medPairDist 11-17, rogueFrac 0.28-0.75 —
   they hold several local packs covering the map. Each local fight finds them with 3-4+ heads
   present: at their death sites they average 6.3 allies vs 0.5 foes (cheb≤5); at ours, 2.0-2.5
   allies vs 5.6-6.8 foes. Local superiority is emergent from mass — you can't fake it with 8
   dragons.
4. **Pearl economy.** Income per game: SF 2154, opp_top 1167, ours 322-474. Growth feeds splits
   feeds growth — the compounding loop.
5. **Queen is expendable hardware.** Winners' queens die r0-5 in most games and they still win
   (m821977 SF queen @2 → won by elimination r439; m823881 both queens @4-5 → WHQ won r500 on
   longest-dragon). The queen only matters when the game reaches r500 undecided — then WHQ-style
   teams dump the swarm into her (suicides all ≥r245). **Succession model flag:** all sampled
   r500 games had BOTH original queens dead (tiebreak = longest dragon). Cannot distinguish
   "fixed queen dead=0" from "lowest-id-alive relay" from this sample — both fit; a game with
   asymmetric queen survival at r500 is needed to discriminate.
6. **Spawn-adjacent queen trades are real.** m821961 r0: our queen's first action was a 3-step
   sprint (paid 2 segs) that wrapped into the enemy queen — mutual h2h death. Opposing spawn
   edges are torus-adjacent on 32x32 maps; queens collide without "assassination" intent.
7. **Sprint = collateral engine.** Dense swarms pay constant self/wall deaths (SF: 217 self + 146
   wall per game, ~0.5% of actions; ours: 9 self + 31 wall per ~2200 actions = 1.4% — we hit
   walls 3× more per action with 1/10th the mass, i.e. worse sprint hygiene not less usage).

## 16.3 Verdict — the ONE structural change

**Round-phase doctrine controller** (breed → engage → endgame), additive to policy.hpp.

Rationale: every measurable signature of our losses traces to one mechanism — we fail the
r40-80 mass race and get eliminated. A doctrine layer is the smallest change that produces the
observed winner behavior: r0 bud-cascade + contact-averse growth (avoid enemy≤2 rather than
trade on sight), with a phase switch to the existing brawl policy once maxAlive ~15-20, and the
existing feed block as the endgame phase. It subsumes the "map doctrine" row and does NOT
require sonar to start (phase can be stateless on round/aliveCount).

- Effort: ~1 session (phase flag + score multipliers + breed-move scorer + split gating inside
  breed phase; champId fix included as freebie). Not a rewrite — it's a coordinator above
  `decide()`, not instead of it.
- Expected payoff: converts elimination losses into contested mid-games. If breed-phase doubles
  our r80 alive count we reach parity where the ~0% top-5 winrate becomes real coin-flips.
  Estimate +150-250 elo (to ~1450-1550) — the largest single jump available; it is NOT
  sufficient for top-20 alone.
- Ranked alternatives: **Sonar merge** (abyss_dev → main): ~0.5 session, mostly A/B verify —
  prerequisite for heard-danger/pack-hunt/assassin but doesn't itself fix the mass race; do it
  second (or concurrently — it's already built). **Queen-murder scripting**: ~1 session on top of
  sonar; queens die to brawl anyway so payoff is bounded. **Corpse-rail feeder**: ~1 session;
  only pays in roundLimit games (~47%) we don't currently survive to see.

Sequencing recommendation: champId/`id<=1` fix + doctrine controller → sonar merge+verify →
assassin squad → endgame feed tuning.

## 16.4 Cannot retrofit (would need rewrite)

1. **Joint multi-dragon planning**: each dragon is an independent process; the only shared
   channel is sonar ≈ 4×u64/turn (~256 bits/dragon/turn). True team-level search is impossible;
   tagged-message protocols are the ceiling.
2. **Persistent squad membership/leadership**: no durable ally identity across turns beyond
   positional echoes (heardMemory 14r cap in dev build); emergent roles only.
3. **Shared map-wide state** (influence maps, territory claims): each dragon re-derives fields
   from its own vision+heard; there is no shared world model to write to.
4. **Reliable queen-as-hub command tree**: queens die ~100% of sampled games; a command
   hierarchy rooted in a usually-dead node is architecturally fragile (relay chains lose
   fidelity; succession makes hub role handoff possible but lossy).
5. **Anything needing >~256 bits/dragon/turn bandwidth** (dense target maps, coordinated
   formation specs): bandwidth-capped by sonar protocol.

## 16.5 Method notes

- Analyzer: `tooling/coord.py` (per-replay per-team: queen tracking, local force balance at
  deaths, alive curves, sonar counts, split/death/action mixes).
- Force balance = count of alive ally/enemy heads within cheb-5 of victim's head at death round.
- Queen = map-start ids {0,1} per team (from map dragon order); succession model unverified (16.2.5).
- Sample: 15 replays (10 ours_top/weak + 5 top-team games), 30 team-games. Queen-mortality and
  sonar findings saturate quickly; mass/doctrine estimates carry ~±20% error bars at this n.
