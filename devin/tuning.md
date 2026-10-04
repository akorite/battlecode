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
