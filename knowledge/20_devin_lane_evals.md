# Devin lane-eval campaign (2026-10-02/03) — results, verdicts, lessons

Ship candidate: **abyss_v104** (commit 232c080). Flagship abyss_v102 measured 63.6% vs live
abyss_st (176 games, keyed sonar, clean). v104 = 59.4% vs st vs v102's 58.3% on identical
9600-seed fixtures (paired, 96 games each) — marginally ahead, carries every mechanism that
verified good. Below the 65% bar; j0019 (all-maps ×4 fresh seeds vs v102+st, 352 games) is the
formal benchmark.

## Lane results vs flagship (clean keyed evals)

| lane | diff | verdict | mechanism |
|---|---|---|---|
| eat | eatBonus 1.0→2.0 | 47.4% DROP | adj-eat rate flat 0.760→0.759 — skips aren't weight-bound |
| cf | feedRound 400→320, brawl 380→300 | 50.0% MERGE | longest 32.6v28.9 — works mechanically, W/L flat |
| open | eat-then-split + budMult gate | 50.0% DROP | elimination variance not opening-bound; arena flipped 0-6 both ways |
| ts | tail-strike queen fear tax | 45.8% wash | paired: 10 queen saves ↔ 11 new deaths — fear displaces, doesn't prevent |
| seal | ally-body exit-denial via danger price | 48.3% DROP | wall+self+body deaths flat 23.3v23.9 — priced danger where legality was needed |
| qk | slayQueen+protectLead+stamped sonar, minus U-turn escape | 47.3% split | slay converts 100% dist-2 kills (58%→100%, 13 saves→13 wins) BUT escape-removal threw 20 games (hitSelf+6,h2h+5) |
| adj | queen never parks enemy-adjacent | inert DROP | byte-identical — baseline already never parks; h2h deaths are enemy-initiated sprints |
| v103 = cf+ts | combination test | 47.9% vs v102 | stacking marginal mechanisms still washes |
| v104 = cherry-picked qk+cf+ts | ship candidate | 59.4% vs st (paired seeds) | kept slay/lead/veto/sonar; restored U-turn escapes |
| v105 = v104+dead-queen early consolidation | 41.7% vs v104, 44.4% vs st | REGRESS/DROP | deadQ helped weakhold 4-2, cost autarky+schooltime; silence false-positives → premature consolidation |

## Verified mechanisms (keep)

- **slayQueen**: converts ~100% of in-reach queen kills (was ~58%). Queen-fate is ~100%
  decisive both directions — this is the only lane that measurably produced wins.
- **protectLead**: survival mode once their queen dies.
- **deadEnd veto**: queen never enters closed corridors (wall deaths 20→23 worked).
- **Round-stamped keyed sonar**: anti-replay (WaterCandle forges pings).
- **cf consolidation timing**: feedRound/fallback 320 produces longest 32.6 vs 28.9.

## Postmortems (approach vs implementation)

- **qk**: approach good, implementation split — removing her U-turn escape *created* trapped
  suicides. Lesson: "remove a dangerous escape" ≠ "add safety". Cherry-picked, kept the rest.
- **ts**: approach doubtful — the tax worked exactly as coded but deaths relocate (10↔11).
  Fear without an escape-improving mechanism nets zero.
- **seal**: mechanism untested — priced danger where legality was required. Idea (ally-aware
  exit preservation) may still be right, implementation wrong.
- **v105 deadQ**: approach (early consolidation after queen death) sound — it worked on
  weakhold (4-2 vs v104) — but silence-presumption fires false positives on open maps where
  queen is alive-but-silent → premature consolidation starves the swarm. Third failed
  implementation of "early consolidation"; cf timing was the only version that didn't regress.
- **weakhold**: structural map loss — sonar reach ~2.4 cells (kelp eats ~50% of pings),
  queens die r48-78 *unwitnessed* in corridors, gossip can't span corridors, no convergence
  mechanism can form. Don't iterate there; it's a physics wall, not a policy bug.

## Loss decomposition (flagship vs st, 27 r500 losses)

- ~55% elimination races (small-map early brawls — every lane touching this was neutral)
- ~28% consolidation (longest-dragon gaps — cf/v105 targeted, both washed or regressed)
- ~17% queen-fate (our queen dies, theirs lives — slay/protectLead in v104)

## Why params are inert

Knobs move the choice *margin*; our losses are discrete structural events (queen into a
dead-end, tail-strike spawn, side-locked spawn races). eatBonus doubling didn't change the
adjacent-eat rate at all (0.760→0.759): dragons already eat what they safely can; skips are
danger/mission-driven. Combinations of marginal mechanisms also wash (v103). Only mechanisms
that change discrete outcomes (kill the queen, keep her out of corridors) move W/L.

## Eval protocol (what "clean" means)

- Team-keyed sonar (`sonarKey(m,round,team)` + round-stamped tags) — without it the flagship's
  pings cross-talk between the two identical bots and evals are contaminated (~+10% phantom).
- Paired explicit seed sets; tuning seeds 1000s / eval seeds 8500-9700 disjoint (overfit guard).
- Maps side-locked (devil, portals, queen_of_spades, schooltime, slithery_fight are ~50%
  lock) — read ALL-unlocked too; per-map n=6 is noise-level, look for mechanism metrics.
- Mechanism metrics matter more than W/L at n<50: queen deaths, longest@r499, eaten@r60,
  adj-eat rate, dist-2 kill rate.

## Open threads

- j0019 (v104 formal benchmark vs v102+st, 352 games @9500-9503): decides 65% ship bar.
- Small-map elimination variance: biggest loss bucket, every approach neutral so far.
- Escorted queen-hunt (assassin role exists): their queen dies ~symmetric timing to ours;
  killing hers *earlier* flips queen-fate games before ours falls. Untried structurally.
- Salvage candidates: caged-queen detection (schooltime feeders waste ~1800 turns; only pays
  there), ally-aware exit legality (seal done right).
