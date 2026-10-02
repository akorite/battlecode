# Prior competitions — what MIT/Cambridge/adjacent postmortems teach about Abyss

*Sources: MIT Battlecode postmortems 2019–2025 (battlecode.org), Cambridge Battlecode docs (battlecode.cam, 2025-26 Titan game), Halite 2/3 writeups, Battlesnake postmortems. This file is about what winners did and what it means for UNSW Abyss.*

## The other Battlecodes at a glance

| Comp | Game | Comms | Compute | Parallel to Abyss |
|---|---|---|---|---|
| MIT 2021 | muckrakers/politicians boxing ECs | shared array | bytecode budget | box-in ≈ noValidAction kills |
| MIT 2023 | carriers/launchers, sky islands, 3 resources | proximity-gated shared array + amplifiers | bytecode | resource triage = pearl economy |
| MIT 2024 | ducks, flags, bread, traps | 64×16-bit shared array | bytecode | flag-sniping ≈ champion hunting |
| MIT 2025 | paint 70% coverage, towers, SRP patterns | shared array | bytecode | territory % win = alive-at-bell |
| Cambridge '26 | Titan mining, conveyors, turrets | markers (placed tiles!) | 2ms/unit Python | supply-chain routes = pearl paths |
| Halite 2/3 | ships mine halite, dropoffs | none needed (single agent) | wall-clock | economy vs combat balance |
| Battlesnake | snakes, food, hazards | n/a (1 unit) | 500ms/move | body-as-resource, avoid walls |

## What MIT winners actually did (the recurring playbook)

**1. Steal from the open-source meta — deliberately.** Cout for Clout's defining move: "the one logical thing that anyone would do: rob XSquare's micro and turn it against him. It took approximately 20 minutes" (+100 elo, 1850→1950). 4 Musketeers lifted bug-nav from XSquare's 2022 repo. Just Woke Up stole XSquare's exploration code. The MIT meta has a single open-source load-bearing contributor (XSquare) everyone builds on. **Abyss parallel: Cat's paradise abyss-framework + the Loong diary play the same role — the shared baseline is the floor, differentiation is where elo lives.**

**2. Macro > micro, but micro decides close games.** Om Nom's biggest gains were micro fixes ("soldiers shouldn't go home early" — a *priority* bug, not a strategy change; paint-efficiency tiebreakers). Yet their macro insight — "money is all you need" — is that resource *type balance* beats resource *amount*: they discovered tower-nuking converts money→paint at a better rate than SRPs. **Abyss parallel: forgot/cheji's suicide→pearl→champion loop is the same mechanic — converting one resource (body mass) into another (fed length) at a rate the naive player doesn't know exists.**

**3. Communication architecture is a first-class subsystem.** 4 Musketeers built a formal "database": a sector system (map → ~128 sectors, sector id = 7 bits vs 12 for a location) plus a shared-memory reporter structure. 2023's twist: comms were proximity-gated unless you built amplifiers — so *infrastructure shaped information flow*. **Abyss parallel: sonar rays ARE the amplifiers — Loong's 64-bit tagged packet format is the same answer to the same problem, except Abyss's channel is broadcast-interceptable, which MIT never had to deal with.**

**4. Zerg-rush scales further than anyone models.** Cout for Clout: "47 vs 50 ducks → lost 90%" — the sitting-duck defense wasn't viable, so they went *full aggro*, +130 elo overnight. 3 Musketeers 2021: 50-influence muckrakers lost; 1-influence muckraker spam won — "increasing our number of muckrakers spawned would allow us to overwhelm." **Abyss parallel: our swarm-size data (peak alive, splits/g, bodies logit) is the same law — numbers beat unit quality; the suicide economy converts numbers into concentrated length at the bell.**

**5. Early-round budget discipline.** Om Nom: "every unit we spawned would allocate a massive array and then go over bytecode on the first turn — snowballing matters most early." **Abyss parallel: instruction budgets + the 0–30% divergence window (winner +2.9 dragons by 20%) — the teams that don't blow their opening CPU are the ones whose expansion curve starts clean.**

**6. Iteration speed is a weapon.** ReCurs3ve (Halite III, 3rd) built a "battlestation" — local replay tooling, version-benchmark harness, per-frame metrics — before the strategy. No thoughts head empty's retrospective lesson: top teams had A/B-test infrastructure and they didn't. **Abyss parallel: our whole loop (collect→download→analyze→bceval) is that battlestation for the meta itself; the Loong diary shows a top-60 team doing it by hand.**

**7. Symmetry exploitation.** Zhugeduck, Gone Fishin', 4 Musketeers all invested in fast symmetry checkers — assume rotational symmetry, infer enemy state from your own map half, save the entire scouting budget. **Abyss maps are symmetric tori — our best teams' wall-riding patterns (3.14159265's 61% hitWall) only make sense if their spawn-mirroring lets them infer enemy-facing walls they've never seen.**

**8. The waiting-game trap.** Big Red 2019: after a spec buff, the meta collapsed to "prophet ball" turtle-and-win-on-tiebreaker — defensive macro beat rushing only because the rules rewarded it. When the rules nerf defense, everyone rushes. **Abyss parallel: the 500-round bell rewards a *fed champion* — the defense-shaped meta (Sponge's 59% flat-curve wins) exists because the rules make attrition cheap.**

## Cambridge Battlecode — the closest structural cousin

Cambridge's 2026 game (Titan) differs mechanically — buildings, not swarms — but the *problems* are identical:

- **Conveyors = pearl paths.** Both games require routing a resource from where it's produced to where it scores. The top Cambridge teams' conveyor-network optimization is the spatial analog of forgot/cheji's corpse-field placement (suicide where the champion patrols).
- **Markers = sonar.** Cambridge gives free "marker" tiles as inter-unit comms — one-way, physical, eavesdroppable-by-design communication. Exactly the constraint sonar imposes.
- **Cost scaling.** Every entity raises the next's cost multiplier — the same price-signal as Abyss's "each split costs body, each body must earn tiles."
- **Python-only, 2ms/unit.** The opposite compute regime to Abyss's C++ arms race — a deliberate design choice to equalize. Notably, MIT's bytecode budget produced the same effect in Java.
- **2000-round cap + tiebreakers** — longest/economy tiebreaks reward the same consolidation arc Abyss's 500-round bell does.

## Halite — the economy-vs-combat masterclass

- **reCurs3ve (Halite III, 3rd):** the whole bot was a *planning layer* — every ship gets a role/goal/path via a greedy conflict-resolving assignment engine. Spawning was a *policy decision*, not a reflex ("eliminating variance helped my winrate"). **Abyss parallel: Cutlery's suffocation web and SSS's minimalism are the two poles of this — how much is emergent splitting vs deliberate assignment.**
- **Shummie (Halite 2):** harassment tactics ("send one ship, watch the enemy overcommit 10 to chase it") and the 4-player prisoner's-dilemma of rushing: rush wins 1v1 but loses the multiplayer table. **Abyss parallel: kamikaze trades are harassment-as-feature — a 2-segment dragon trading for a champion is the same "cheap unit taxes expensive unit" economics.**

## Battlesnake — when bodies are the whole game

- Hybrid RL + alpha-beta: policy plays generally, tree search vetoes obvious wins/losses. "Many strategies are viable — rule-based, tree-search, ML." **Abyss parallel: our data says the top tier is all hand-tuned heuristics + sonar protocols, zero visible ML — the search space is too big for per-turn tree search under 100M points/dragon.**
- Minimax + floodfill + decision-tree visualizers: the winning pattern is a scorer over candidate moves, not a planner. **Abyss's micro is the same shape (score-the-neighborhood movement).**

## The universal winning loop, across every comp

Every postmortem converges on the same meta-loop:

```
1. Get a working bot fast — iterate on the ladder, don't theorize
2. Build tooling before strategy — replay viewers, A/B harnesses
3. Exploit the economy's conversion edges — find what converts X→Y cheaply
4. Spam > finesse early; coordination > spam late
5. Steal published micro/frameworks, then out-iterate on top
6. Comms/state-sharing is a multiplier — invest once, reap all game
7. Play the tiebreak/edge rules — bells, bytecaps, walls decide margins
```

Applied to Abyss: our winners did exactly this — Cutlery's split-maximalism (rule 4+7, the swarm bell), forgot's corpse-economy (rule 3), the sonar-protocol teams (rule 6), Cat's-paradise derivatives (rule 5). The competition's real innovation was making communication *interceptable* — forcing protocol design as a strategy axis MIT never had.
