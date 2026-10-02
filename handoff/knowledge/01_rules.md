# Rules of Abyss — what the rulebook produces at scale

*Evidence base: 59,544 analyzed games (team-side observations = 2×) from a 80,940-replay corpus, Sep 21 → Oct 1, 2026.*

## The rules, one by one, with what they caused

### MOVE — 1 cell free per turn; each extra cell costs 1 body segment ("sprint")

Measured: sprint is ~0.25% of all moves across the entire season. Of 59k games, essentially nobody burns body for speed — because a segment spent is a segment that can't hold territory, can't split, and can't drop pearls on death.

The one exception is instructive: **cheji bt** sprints 1.2% of moves, ~5× the field — and it's the team whose suicide cycle *produces* the situation sprint is good for (a dragon at the edge of a fresh corpse-field grabbing pearls before re-saturation). Sprint isn't weak; it's expensive, and only an economy that banks body → food can amortize it.

**Corollary:** any design relying on sprint as routine tech is throwing away length. If you sprint, it should be inside a feeding loop.

### SPLIT — rear ≥2 segments bud a new dragon; parent keeps the front

Measured: ~240 splits/team/game at elite level, concentrated in the first 40% of the game (1.57M splits in the 30–35% progress bucket alone across the corpus). Every elite splits within ~24 rounds of game start.

Splitting is simultaneously the growth engine, the territory tool (a new dragon claims its own cell), and the death engine (more bodies = more exposure). Teams differ hugely on pace: SSS at 170/game vs Cutlery at 464 — and both are top-10. The binding constraint isn't the rules; it's *space* — after ~60% progress there's nothing to split into without colliding, so splits fall off a cliff while deaths stay high.

**Corollary:** split early and relentlessly. Late-game splitting is negative-ev — it adds targets, not board control.

### SUICIDE — dragon dies deliberately; corpse drops ⌈L/2⌉ pearls on its tiles

Measured: the single biggest strategic fork on the ladder. forgot to mention: 206/game. cheji bt: 123. Six of the top ten: ~0. It is not a fringe trick — it is the second-best elo's whole identity.

Why it works: length on a dead dragon pays half its body as *food on the ground where it died*. In a self-saturated web, a boxed-in dragon dying anyway is a sunk cost; suicide upgrades the corpse into resources the champion eats. The eval model confirms the exchange rate — the winner's mid-game signature is *higher* lost-to-deaths length (+11.8 at 50%) alongside bigger territory.

**Corollary:** suicide is a conversion mechanic, not a death. Suiciding without collection (low-elo teams do this) is just feeding the map. The differentiator is the loop: suicide at the right place (inside your swarm, near the champion's patrol), not merely often.

### Sonar — ≤4 directional rays per action; ray stops at first kelp or body; wraps around edges; crosses portals; every dragon it hits (including enemies) receives the value

Measured: 58% of all pings die on kelp, 39% hit allies, 3.5% ever touch an enemy. Sonar is almost never used to see the enemy — it's used to see the *world* and to talk to *yourself*.

Because there's no shared memory between your own dragons, sonar is the only state channel — and it's broadcast: anything your dragons hear, enemies on the ray hear too. Elite teams treat it as a signed protocol (the documented Loong format carries a tag + dragon id + role + length + position, explicitly because eavesdropping is free).

Usage is a hard tier gate: 0.77 pings/action at Shrimp → 2.77 at Shark → 3.9 saturation for the information-maximalists (Stockfish, calc, Sabotage-d). And yet Cache me outside holds 2038 elo at 0.40 — mass can substitute for communication, just not as efficiently.

**Corollary:** protocol, not presence. The value is a self-coherent message format all your dragons can read, not the ray count.

### Kelp walls — impassable; kill on contact; stop sonar rays

Measured: kelp is the #1 dragon killer at ~30% of all deaths — more than every combat mechanic combined. It's the map's only static hazard and it does strategic work: walls split the board into defensible regions, and a dragon hugging kelp can only be attacked from ≤3 sides.

Two elite families die to it deliberately-adjacent: 3.14159265 (61% hitWall) and calc (58%) — both play the edge. Their kills-per-cost calculus is that a dragon operating on kelp is safer *per position*, even if some fraction dies on the wall; the other teams (Cutlery, forgot, cheji) sit at ~0% wall deaths because their web saturates interior space and never touches edges.

**Corollary:** wall-deaths are a style marker, not incompetence. ~0% and ~55% both win; what fails is the middle (teams that accidentally hit walls).

### Head-to-head — two heads collide; BOTH die, regardless of length

Measured: ~21% of all deaths are mutual kills — the second-largest combat cause. On Trophy it's 65%.

This rule manufactures kamikazes: a 2-segment dragon trading for a 40-segment champion is the most lopsided exchange available, so elites deliberately keep cheap expendable bodies for interdiction. It's also why escort spacing matters — two dragons approaching head-on is a guaranteed kill for the defender.

**Corollary:** h2h is asymmetric value — the shorter dragon always profits. Long dragons must route around; short dragons should be encouraged to push.

### The 500-round cap — winner = longest living dragon, tie-broken by total length

Measured: ~58% of games reach the cap (a fraction that rose through the season — early meta eliminated more). Every single game that ends before the cap is an elimination — there is no other early end.

This rule writes the endgame: dispersion beats concentration until the bell, then only your single longest dragon counts. It's the reason the corpse-economy doctrine exists at all — it's a mechanism for *concentrating* length before the bell (swarm dies → pearls → one dragon eats them all). cheji bt's champion-at-bell is the cleanest expression; Sponge is the degenerate case (it plays the whole game as a bell strategy and still wins 59%).

**Corollary:** if you're not feeding a champion by ~80% of the game, the bell judge will score for whoever did.

### The 64-dragon cap — ≤64 alive simultaneously

Measured: non-binding. Season max sustained peak is calc at 48.2; even the most rabid splitters plateau ~40. The actual ceiling is spatial — the map fills before the rule fires.

### No shared memory between dragons; nothing carries between turns except the board

Measured/produced: this is *the* rule that creates the game. Every team reinvents the same structure: a champion that reads state, workers/kamikazes that act on announcements, all speaking over the interceptable sonar channel. Role systems (Loong's 64-bit packet; Cat's paradise common.hpp constants) are the entirely of "coordination" — there is no other way to pass information.

### 100M CPU points per dragon per turn — overuse = timeout death

Measured: the language meta is decided. 49 of the top 50 teams are C++ (the lone Python top-50 is an artifact of early ladder). Timeout deaths are rare (<1%) but real — a handful of teams have measurable `tle` rates.

### Pearl spawn schedule — pearls appear on tiles; schedules were fixed per map until Sep 25, then randomized

Measured: a mid-season rules earthquake. 20+ teams had hardcoded spawn timing; randomization deleted that tech tree overnight and it shows in the E1→E2 era jump (split activity +21%, deaths +20% in one week — teams that lost their schedule advantage had to fight for space instead).

### Turn order — A acts before B each round

Measured: moving second is a real edge. Side-B wins 65% of Shark-tier games (47–50% at lower tiers) even though the eval model *penalizes* side-B by −0.12 logits. Reading A's committed moves before choosing yours beats initiative once coordination quality is high enough to exploit it.

---

## The shape the rules force

The rules funnel all real strategy into one loop:

```
SPLIT hard → occupy tiles → die in waves (walls/trades/crowding) →
SUISCIDE turns corpses into pearls → pearls feed a champion →
at round 500 the champion's length decides
```

Every top team is a point on this loop. The rankings are the answer to "how efficiently does your iteration of the loop convert mass into territory into a fed champion."
