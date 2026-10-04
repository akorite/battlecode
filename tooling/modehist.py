"""Mode-histogram aggregator for abyss_x_modes debug-build replays.

Reads results/<tag>/games.jsonl + replays/*.replay, extracts the per-turn LOG
line's `m=<mode>` field (abyss_x_modes emits it via dbg(); the opponent emits
nothing), and prints mode-share tables per map per round band, plus the
mode x why cross-tab and flag rates (bud/lean/lead).

Usage: python3 tooling/modehist.py results/<tag> [--band N]
"""
import sys, os, json, re, collections, pathlib
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
from parse_replay import parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from replay_metrics import parse_map

TURN = re.compile(r'^r(\d+) (\S+).*? m=(\S+) bud=(\d) lean=(\d) lead=(\d) s=(-?\d+) wb=(\S+)@(-?\d+):(-?\d+)')
BANDS = [(0, 29), (30, 119), (120, 299), (300, 399), (400, 999)]
MODES = ['forage', 'attack', 'intercept', 'support', 'escort', 'feeder',
         'grower', 'champ', 'assassin', 'queen', 'qhide', 'qlead', 'lead']


def band_of(r):
    for lo, hi in BANDS:
        if lo <= r <= hi:
            return (lo, hi)
    return BANDS[-1]


def game_rows(path):
    """Yield (team, round, why, mode, bud, lean, lead) for every logged turn."""
    rep = parse(path)
    W, H, dr, edges = parse_map(rep['map'])
    team_of = {}
    for e in rep['events']:
        if e['type'] == 'roundStart':
            break
        if e['type'] == 'dragonUpdate' and e['id'] < len(dr):
            team_of[e['id']] = 'AB'[dr[e['id']][0]]
    for e in rep['events']:
        ty = e['type']
        if ty == 'dragonSplit':
            team_of[e['childId']] = e['team']
            team_of[e['parentId']] = e['team']
        elif ty == 'dragonLog':
            m = TURN.match(e['text'])
            if not m:
                continue
            d = team_of.get(e['id'])
            if d is None:
                continue
            yield (d, int(m.group(1)), m.group(2).split(':')[0], m.group(3),
                   int(m.group(4)), int(m.group(5)), int(m.group(6)),
                   int(m.group(7)), m.group(8), int(m.group(9)), int(m.group(10)))


def main():
    res = pathlib.Path(sys.argv[1] if '/' in sys.argv[1] else 'results/' + sys.argv[1])
    games = [json.loads(l) for l in (res / 'games.jsonl').read_text().splitlines()]
    # per (map, band, mode) dragon-turn counts, cand side only
    hist = collections.defaultdict(collections.Counter)
    why_x = collections.defaultdict(collections.Counter)   # (map, mode) -> why counts
    flags = collections.defaultdict(lambda: [0, 0, 0, 0])  # map -> [turns, bud, lean, lead]
    whys = collections.defaultdict(collections.Counter)    # map -> all whys (both pre-m builds too)
    margins = collections.defaultdict(list)                # map -> [score margin best-alt]
    alt_whys = collections.defaultdict(collections.Counter)  # (map, mode) -> runner-up why counts
    knife = collections.Counter()                          # (map, mode) -> turns with margin <= 2
    for g in games:
        rp = res / 'replays' / f"{g['map']}-s{g['seed']}-{g['cand'] if g['candSide']=='A' else g['base']}-{g['base'] if g['candSide']=='A' else g['cand']}.replay"
        # the replay file name is <map>-s<seed>-<nameA>-<nameB>
        cand = 'A' if g['candSide'] == 'A' else 'B'
        if not rp.exists():
            print('missing replay', rp.name, file=sys.stderr)
            continue
        for team, rnd, why, mode, bud, lean, lead, sc, wbwhy, wbdir, wbmar in game_rows(str(rp)):
            if team != cand:
                continue
            b = band_of(rnd)
            hist[(g['map'], b)][mode] += 1
            why_x[(g['map'], mode)][why] += 1
            whys[g['map']][why] += 1
            if wbmar >= 0:
                margins[g['map']].append(wbmar)
                alt_whys[(g['map'], mode)][wbwhy] += 1
                if mode != 'feeder' and wbmar <= 2:
                    knife[(g['map'], mode)] += 1
            f = flags[g['map']]
            f[0] += 1; f[1] += bud; f[2] += lean; f[3] += lead
    for m in sorted({k[0] for k in hist}):
        print(f'\n=== {m} ===')
        tot = sum(sum(c.values()) for k, c in hist.items() if k[0] == m)
        f = flags[m]
        print(f'dragon-turns {tot}  bud% {100*f[1]/max(1,f[0]):.0f}  lean% {100*f[2]/max(1,f[0]):.0f}  lead% {100*f[3]/max(1,f[0]):.0f}')
        print(f'{"band":>10} {"turns":>6}  ' + '  '.join(f'{md:>9}' for md in MODES))
        for lo, hi in BANDS:
            c = hist.get((m, (lo, hi)))
            if not c:
                continue
            n = sum(c.values())
            print(f'{lo:>4}-{hi:<5} {n:>6}  ' + '  '.join(f'{100*c.get(md,0)/n:8.1f}%' if c.get(md) else f'{".":>9}' for md in MODES))
        # top mode->why mismatches (mode says one job, outcome says another)
        print('  mode x top-whys:')
        for (mm, mode), c in sorted(why_x.items()):
            if mm != m:
                continue
            top = ', '.join(f'{w} {n}' for w, n in c.most_common(4))
            print(f'    {mode:>10}: {top}')
        ms = sorted(margins[m])
        if ms:
            q = lambda p: ms[int(p * (len(ms) - 1))]
            small = sum(1 for x in ms if x <= 2)
            print(f'  margins: p10 {q(.1)} p25 {q(.25)} p50 {q(.5)} p75 {q(.75)}  knife-edge(<=2) {100*small/len(ms):.1f}%')
            for (mm, mode), n in sorted(knife.items()):
                if mm != m:
                    continue
                top = ', '.join(f'{w} {c}' for w, c in alt_whys[(m, mode)].most_common(3))
                print(f'    knife {mode:>10}: {n} turns   top runner-ups: {top}')


if __name__ == '__main__':
    main()
