# Map analysis — the board picks the doctrine

*10 maps in the ranked pool, ~12k team-games each. Rates are per-team per-game; "elim" = share ending before round 500.*

## The map table

| Map | Peak alive | Rounds | Elim% | Deaths/g | Sui/g | Sonar/act | Shape it forces |
|---|---|---|---|---|---|---|---|
| Slithery Fight | 60.4 | 497 | 2% | 790 | 97.0 | 2.50 | the farming marathon — huge open field |
| Schooltime | 47.8 | 468 | 19% | 249 | 25.4 | 2.48 | big structured board, long grind |
| Portals | 33.7 | 487 | 4% | 384 | 37.2 | 2.52 | wrapping lanes, grind-heavy |
| Trauma | 34.5 | 490 | 7% | 177 | 23.9 | 2.48 | open chaos, low interaction per dragon |
| Autarky | 35.3 | 417 | 40% | 163 | 13.8 | 2.54 | mid-size, balanced |
| Default | 32.5 | 405 | 47% | 97 | 7.0 | 2.30 | the reference map |
| Devil | 28.7 | 269 | 80% | 156 | 15.8 | 2.28 | small violent sprint |
| Queen Of Spades | 18.6 | 341 | 66% | 62 | 4.6 | 2.30 | tight lanes, forced collision |
| Trophy | 33.0 | 263 | 85% | 82 | 4.6 | 2.21 | kamikaze coliseum |
| Prisoners Dilemma | 14.5 | 247 | 70% | 76 | 6.9 | 2.26 | the corridor — smallest swarms |

## Three map archetypes

**Marathon boards** (Slithery, Portals, Trauma, Schooltime): >460 avg rounds, <20% elim. Slithery Fight is the extreme — 60-dragon swarms, ~790 deaths/team, games virtually never end early. This is where feeding economies print (97 sui/g — the only map where the suicide doctrine is *uncontested correct*). eval is decided by the bell every time.

**Reference boards** (Autarky, Default): ~405-417 rounds, ~40-47% elim. The doctrine-neutral maps — every style is viable, no map gimmick to exploit.

**Sprint boards** (Devil, Trophy, Queen Of Spades, Prisoners Dilemma): <341 rounds, 66-85% elim, smallest swarms. These are eliminations by design — the board is too small for a sustainable swarm. Trophy's 65% h2h-death share (vs 21% global) says it all: it's a head-on coliseum.

## Death-mix fingerprints by map

| Map | hitWall | hitSelf | hitBody | h2h | boxed-in |
|---|---|---|---|---|---|
| Trophy | 8% | 10% | 9% | **65%** | 8% |
| Default | 8% | 13% | 15% | **55%** | 9% |
| Schooltime | 17% | 19% | 13% | 38% | 13% |
| Queen Of Spades | 23% | 19% | 11% | 37% | 10% |
| Prisoners Dilemma | **41%** | 27% | 5% | 13% | 14% |
| Trauma | 38% | 24% | 8% | 13% | 18% |
| Devil | 21% | 25% | 13% | 26% | 15% |
| Autarky | 34% | 19% | 5% | 29% | 13% |
| Portals | 34% | 27% | 13% | 14% | 12% |
| Slithery Fight | 33% | 28% | 11% | 11% | 17% |

The map writes the cause of death: open combat maps → h2h dominates (Trophy 65%); corridor maps → walls dominate (Prisoners 41%, Trauma 38%); dense maps → self-collisions rise (Portals 27%, Slithery 28%).

## Sonar by map

Enemy hit-rates vary 30× — **Default 8.9% vs Portals 0%**: on Portals the rays wrap through portals and never touch enemies (they hit kelp at 64% — the channel becomes pure mapping). Schooltime has the densest self-traffic by ally hits (31%).

## Who's good where

Per-team map WR (from profiles):

- **Cutlery** — best: Autarky 84%, Schooltime 80%. Worst: Devil 54%, Prisoners 60%. (Web needs space.)
- **forgot** — best: Schooltime 79%, Devil 75%. Worst: Portals 48%. (Portal lanes break saturation.)
- **cheji bt** — best: Devil 86%, Trauma 84%. Worst: Portals 48%, Slithery 48%. (Lockdown needs borders.)
- **calc** — best: Devil 87%, Trauma 84%. Worst: Slithery 51%. (Mass leaves bodies on kelp marathons.)
- **Stockfish** — best: Portals 87%, Queen 83%. Worst: Prisoners 55%. (Sonar-through-portals is its edge.)
- **Sponge** — best: Devil 82%, Schooltime 72%. Worst: Portals 46%. (Compact defense loves tight maps.)
- **3.14159265** — best: Default 78%, Trauma 71%. Worst: Schooltime 44%. (Needs walls to push.)
- **Cache me outside** — best: Schooltime 84%, Devil 79%. Worst: Trauma 60%, Prisoners 55%.
- **PPP** — best: Trauma 90%, Autarky 79%. Worst: Devil 27%! (Boom-bust dies on small boards.)
- **SSS** — best: Devil 85%, Trauma 73%. Worst: Autarky 46%.

**Pattern:** portals and marathons punish every doctrine except Stockfish's information play; tight maps reward compact/defensive styles and punish over-extension (PPP's 27% on Devil is the season's clearest map counter).
