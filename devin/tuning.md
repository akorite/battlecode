# tuning lane — param vector search (SPSA-lite coordinate probes)

Round 1 base = v120 copy (devin/v120 @ f44a1da). Benchmark opponent `abyss_combat`.
CAVEAT: v120's live params come from a kParams lambda overriding struct defaults
(active: feedRound=320, champFallbackRound=320, queenHide=1, trapSafeCells=8).
`xt_fr320`/`xt_cf320` patched only the overridden default → no-op duplicates of
baseline. All other r1 probes hit the active site.
Fixture note: devil+trophy side-B eliminations vs combat are structurally lost for
the whole v-lineage → r1 ceiling 8-2 regardless of params; combat cannot
discriminate this vector. Round 2 switches benchmark to abyss_cf on the
v127-replica base (feed360 triple, relays330, unhide390 per integrator).
Each probe: 5 maps (stronghold,trauma,schooltime,devil,trophy) × 1 seed (s7) × both sides vs combat = 10 games.
score = cand win share; dlen = mean longest-at-end delta vs combat. ~10 games/probe.

| slug | variant | maps | W-L | dlen | time | note |
|---|---|---|---|---|---|---|
| xt_base | `feedRound=400` | stronghold,trauma,schooltime,devil,trophy | 8-2 (80%) | dlen +11.3 | 8m | BASELINE row (v120 default → no-op patch) |
| xt_fr320 | `feedRound=320` | stronghold,trauma,schooltime,devil,trophy | 8-2 (80%) | dlen +10.4 | 7m | feeds wake ~80r earlier; bigger champ on r500 maps |
| xt_cf320 | `champFallbackRound=320` | stronghold,trauma,schooltime,devil,trophy | 8-2 (80%) | dlen +9.2 | 7m | queen-less champion emerges earlier |
| xt_qf290 | `queenFeedRound=290` | stronghold,trauma,schooltime,devil,trophy | 8-2 (80%) | dlen +6.7 | 8m | queen gets fed earlier |
| xt_sd0 | `splitEnemyDist=0` | stronghold,trauma,schooltime,devil,trophy | 8-2 (80%) | dlen +9.2 | 9m | always split even adjacent to enemy head |
| xt_qts5 | `queenTradeSlack=5` | stronghold,trauma,schooltime,devil,trophy | 8-2 (80%) | dlen +10.4 | 8m | trade into their queen more readily |
| xt_sm4 | `sprintMax=4` | stronghold,trauma,schooltime,devil,trophy | 7-3 (70%) | dlen +9.2 | 8m | longer own sprints |
| xt_sm2 | `sprintMax=2` | stronghold,trauma,schooltime,devil,trophy | 7-3 (70%) | dlen +9.1 | 8m | shorter own sprints (safety) |
| xt_wx20 | `wExposed=2.0` | stronghold,trauma,schooltime,devil,trophy | 8-2 (80%) | dlen +10.4 | 8m | stronger reach-aversion |
| xt_wx06 | `wExposed=0.6` | stronghold,trauma,schooltime,devil,trophy | 8-2 (80%) | dlen +11.1 | 8m | weaker reach-aversion |
| x2b_cf | `feedRound=360` | stronghold,trauma,schooltime,devil,trophy | 5-5 (50%) | dlen +5.9 | 9m | BASELINE: v127-replica as-is vs cf |
| x2_f330 | `feedRound=330,queenFeedRound=330,champFallbackRound=330` | stronghold,trauma,schooltime,devil,trophy | 5-5 (50%) | dlen +15.8 | 9m | whole feed window earlier |
| x2_f390 | `feedRound=390,queenFeedRound=390,champFallbackRound=390` | stronghold,trauma,schooltime,devil,trophy | 5-5 (50%) | dlen +8.2 | 9m | whole feed window later |
| x2_qf340 | `queenFeedRound=340` | stronghold,trauma,schooltime,devil,trophy | 5-5 (50%) | dlen +7.1 | 9m | queen fed earlier only |
| x2_qf380 | `queenFeedRound=380` | stronghold,trauma,schooltime,devil,trophy | 5-5 (50%) | dlen +5.8 | 10m | queen fed later only |
| x2_me450 | `midEnd=450` | stronghold,trauma,schooltime,devil,trophy | 5-5 (50%) | dlen +6.7 | 10m | growers keep splitting 50r longer |
| x2_me360 | `midEnd=360` | stronghold,trauma,schooltime,devil,trophy | 5-5 (50%) | dlen +6.9 | 10m | late-game from 360 |
| x2_tsc12 | `trapSafeCells=12` | stronghold,trauma,schooltime,devil,trophy | 5-5 (50%) | dlen +6.7 | 8m | bigger veto margin (active 8) |
| x2_tsc4 | `trapSafeCells=4` | stronghold,trauma,schooltime,devil,trophy | 5-5 (50%) | dlen +6.7 | 8m | tighter veto |
| x2_sd0 | `splitEnemyDist=0` | stronghold,trauma,schooltime,devil,trophy | 5-5 (50%) | dlen +4.3 | 8m | always split vs heads |
| x2_sd2 | `splitEnemyDist=2` | stronghold,trauma,schooltime,devil,trophy | 6-4 (60%) | dlen +15.0 | 8m | back to pre-v120 |
| x2_sm4 | `sprintMax=4` | stronghold,trauma,schooltime,devil,trophy | 5-5 (50%) | dlen +9.1 | 6m | recheck on new base |
| x2_rel340 | `queenRelayFrom=340,champRelayFrom=340` | stronghold,trauma,schooltime,devil,trophy | 5-5 (50%) | dlen +4.3 | 7m | relays later |
| x2_rel300 | `queenRelayFrom=300,champRelayFrom=300` | stronghold,trauma,schooltime,devil,trophy | 5-5 (50%) | dlen +1.5 | 7m | relays earlier |
| x2_em1 | `exposureMode=1` | stronghold,trauma,schooltime,devil,trophy | 6-4 (60%) | dlen +6.2 | 9m | favour exposed w/ local numbers |
| x2_qd30 | `queenDanger=3.0` | stronghold,trauma,schooltime,devil,trophy | 5-5 (50%) | dlen +6.7 | 7m | queen more cautious |
| x2_sv45 | `survivalDanger=4.5` | stronghold,trauma,schooltime,devil,trophy | 5-5 (50%) | dlen +6.8 | 7m | survival-mode more cautious |
| x2_f300 | `feedRound=300,queenFeedRound=300,champFallbackRound=300` | stronghold,trauma,schooltime,devil,trophy | 6-4 (60%) | dlen +0.6 | 6m | extend earlier-gradient |
| x2_fr300 | `feedRound=300` | stronghold,trauma,schooltime,devil,trophy | 5-5 (50%) | dlen +8.9 | 6m | feed window only, queenFeed/champ stay |
| x2_cf300 | `champFallbackRound=300` | stronghold,trauma,schooltime,devil,trophy | 5-5 (50%) | dlen +5.9 | 6m | queenless champ only earlier |
| x3_sd2f330 | `splitEnemyDist=2,feedRound=330,queenFeedRound=330,champFallbackRound=330` | stronghold,trauma,schooltime,devil,trophy | 6-4 (60%) | dlen +12.3 | 7m | combo: revert + feed-early |
| x3_full | `splitEnemyDist=2,feedRound=330,queenFeedRound=330,champFallbackRound=330,exposureMode=1` | stronghold,trauma,schooltime,devil,trophy | 6-4 (60%) | dlen +8.5 | 9m | combo + em1 |

## Round 2/3 analysis (vs abyss_cf, base = v127-replica, baseline 5-5/+5.9)
Score movers (vs 5-5 base): sd2 6-4/+15.0, em1 6-4/+6.2, f300 6-4/+0.6, sd2f330 6-4/+12.3, full 6-4/+8.5.
Margin king: f330 5-5/+15.8 (stronghold 56-73 vs 33-56; st-B grew 27→59 but still L).
Per-map: all action is schooltime + trophy-B. sd2 fixes st-B; em1 rescues st-A; f300 fixes trauma-A+st-B but breaks trophy-B (39/60). em1 anti-stacks with feed330 (unfixes st-B, loses trauma-B, though flips devil-A).
Peaked params confirmed: relays 330 (300:+1.5, 340:+4.3), sprintMax 3 vs combat (2 & 4 both lose a game).
Flat vs cf: qf340/380, me360/450, tsc4/12, qd30, sv45, fr300, cf300, sd0(+4.3 worse).

### Vectors to integrator (ranked)
1. {splitEnemyDist=2} — revert of v120's ship: 6-4, dlen +15.0. Fixture-dependent? needs re-gate on internal base.
2. {feed triple 330} — same landed direction, one more step earlier: margin +15.8 at score parity. 300 overshoots (margin collapse).
3. {sd2 + feed330} — stacks: 6-4, +12.3. Single-vector option if landing one change.
(exposureMode=1: solo 6-4 but incompatible with feed330 — alternative only if feed stays ≥360.)
All evidence n=10/probe single-seed s7 vs abyss_cf — directional, needs integrator gate validation.

## Round 4 (steering-3): relays->370+, fear radius (heardEnemyReach), em2, qts/sm recheck, danger weights
New eval axes per probe (eval_probe.py over kept replays): elim maps dev/dil/tro/def
r25/r50/r100 (dragons,totalLength) minus winner-targets (6.7/16.4, 10.3/25.5, 20/50);
open maps longest@499>33 & total>=260; REJECT flags: cand queen dead <r50 on elim
maps, any elim game ending <r200.
