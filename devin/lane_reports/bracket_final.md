# Bracket opponent forensics — π (314, ~2307) & Sabotage-d (46, ~2312)

Fresh ladder replays pulled 2026-10-04 (ranked games only, public /api/matches replay):
pi_replays n=15 (8W 7L), sab_replays n=16 (12W 4L). Analyzer: analysis/bracket_profile.py.

## 1. "3.14159265" (π) — team 314

### Engine: nva-stall churn (NOT wall-churn)
- Suicides almost exclusively by **noValidAction**: med **67**/game (up to 136), all clustered at
  adjacency ≤3 of own heads (**90% ≤3**, med 2) — dragons walk into dead pockets and stall, drops
  get vacuumed by the swarm. hitWall/hitSelf suicide ≈ **0** (median; only spikes when losing).
- nva deaths land ring **~9** from own longest (med 9, 48% ≤8) — a loose feed-funnel, not a tight one.
- Production: splits med 132 but **97% of splits keep-2 / shed small** — parents stall out next turn,
  children re-split. Pure churn compounding, similar gross volume to winners but lower conversion.
- Eaten med 291 vs opp 322 — they actually get OUT-EATEN on average.

### What kills their queen
Queen dies in **8/15** games: **7/8 hitHeadToHead** (med **r128**), 1 hitWall. She fights in the
mid-game melee and gets rammed. In 5/8 queen-death games it cost them the game (queenEnd or elim).

### Map W-L and loss modes (7 losses)
| map | end | mode | opp | tell |
|---|---|---|---|---|
| Stripes | r129 | ELIM | horse 2512 | swarm wiped; queen h2h r23 |
| weakhold | r413 | ELIM | horse | wiped late; queen h2h r68 |
| Maze | r499 | longest 31v36 | horse | opp wall-churned 426 suic → out-scaled 4v39 alive |
| Trauma | r499 | queenEnd | horse | longest 24v21 WON but queen dead r446 → loss |
| Schooltime | r499 | starved | horse | **splits 17v191** — total intake collapse, ended 1v30 |
| Default | r499 | queenEnd | laloyd 1985 | queen h2h r206, longest 19v20 |
| Australia | r499 | total 5v18 alive | Kamikaze 2112 | longest TIED 54v54; lost on swarm mass |

- Wins = eliminations on small open maps (Trophy r82, Devil r118, Autarky r147, qOS r215, PD r201):
  their nva-churn out-produces light opponents then swarm-wipes.
- "Self-jams in corridors" earlier claim: NOT their signature — they barely wall-die except when a
  churn-war is already lost (Maze 84 suic in the loss). **"Starves under contested-bed pressure":
  VERIFIED** — Schooltime collapse (17 splits) + they get out-eaten 291v322 globally.
- Loss deciders: **queen h2h death mid-late** (queenEnd/tiebreaks) and **being out-eaten +
  out-swarmed** in long churn wars vs wall-donation economies.

## 2. "Sabotage-d" — team 46

### Engine: densest wall-donation loop seen
- suic med **166.5**/game (up to 537 on Slithery), don15 (child dies ≤15r near own units) med **62**,
  nva literally **0** — every suicide is a placed hitWall/hitSelf donation.
- Volume: splits med 289 (up to 749); deaths match (churn ≈ balanced). h2h deaths med **69.5** —
  they fight constantly AND donate constantly.
- eaten med 808 — but **opponents eat 1059** — their donation drops get stolen near combat zones.
- Endgame: longest med **42** (75 Maze, 65 Slithery), alive ~10 — a real conveyor: churn → champ.

### What kills their queen
Queen dies in **11/16** games: **9 h2h + 2 hitWall**, med **r93** — she brawls early and often dies.
They usually win anyway (churn economy carries). But when she dies EARLY on a small map they get
eliminated (qOS loss: queen h2h r37 → elim r272; Autarky loss: queen r86 → wiped r489).

### Map W-L and loss modes (4 losses)
| map | end | mode | opp | tell |
|---|---|---|---|---|
| Islands | r499 | longest 42v48 | horse | mirror-churner out-fed them (opp suic 156) |
| Maze | r499 | longest 38v49 | chad gdp | opp ran nva-churn at **769 nva / 852 splits** — out-volumed |
| Autarky | r489 | ELIM late | chad gdp | swarm attrition, alive 0v5, queen r86 |
| qOS | r272 | ELIM | free trip sydney 2084 | queen h2h r37 → snowball |

- 12 wins incl. brutal churn wars (Slithery 749 splits W, Around UNSW 564). They lose ONLY to
  (a) heavier-volume churn engines and (b) early-queen-kill snowballs on small maps.

## 3. Ranked exploit recommendations (for v449-style bot)

**vs π:**
1. **Wall-donation economy out-converts their stall-churn** — every π loss came vs suic-loop
   opponents (don15 13-426). Our funnel already does this; just don't play their nva game.
2. **Kill their queen mid-game** — she's h2h-exposed r68-206. queenEnd/longest decides vs them;
   a queen-hunt or ram-pressure component has direct payoff (7/8 queen kills were h2h).
3. **Contest beds hard early** — verified starve susceptibility (17-split collapse). If we out-eat
   them r0-100, they never reach churn critical mass (small-map elims are their only win mode).
4. Survive to r499 on big maps — their alive@end collapses to 4-8 vs churners' 18-39; we win on
   total/alive even at tied longest (Australia precedent: 54v54, won on 5v18).

**vs Sab:**
1. **Early queen-kill window r0-100** — queen dies h2h med r93; on small maps her death snowballs
   to elim (their only fast losses). Aggressive melee + queen pressure on elim-class maps.
2. **Steal their donation drops** — opponents eat 1059 vs their 808. Their suicides drop pearls at
   adj≤3 to their OWN units — if our swarm sits on their churn zones we harvest their economy
   (that's exactly what chad gdp/horse do to them).
3. **Volume ceiling**: beating them in a pure churn war needs ~850+ splits (chad gdp Maze). Only
   worth racing if our funnel conversion matches; else play for queenEnd/elim.
4. Hide our queen (v449 universal hide already does): 9/11 of their queen kills are h2h rams —
   they can't ram what never exposes.

**Bottom line:** π = beat by out-eating early + queen-hunt mid-game (their queen is the tiebreak
that decides their r499 losses). Sab = much harder — only beaten by heavier churn volume or an
early queen snowball; prioritize early-queen pressure and drop-stealing on elim-class maps.

Data: pi_replays/, sab_replays/ (meta .json per match); per-game metrics /tmp/bracket_{314,46}.json.
