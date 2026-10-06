"""Death-mix census: per-map-class dragonDeath reason counts for the cand side.

Reuses hitself_census.parse_map + team tracking (init dragons from map dr,
split children via dragonSplit team field). Tile class: TILE_COUNT >= 600 = BIG
(midFeedMinTiles convention), else SMALL.

Usage: python3 deathmix.py <replay_dir> [--cand NAME] -> JSONL per replay
"""
import glob, json, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
from parse_replay import parse
from pocket_metric import parse_map

REASONS = ['hitWall', 'hitSelf', 'hitOtherBody', 'hitHeadToHead', 'noValidAction']


def side_of(path, cand):
    base = os.path.basename(path).replace('.replay', '')
    parts = base.rsplit('-', 2)
    return 'A' if (len(parts) > 1 and parts[-2] == cand) else 'B'


def analyze(path, cand):
    r = parse(path)
    m = re.search(r'TILE_COUNT (\d+)', r['map'])
    nc = int(m.group(1)) if m else -1
    mapname = os.path.basename(path).split('-s')[0]
    _, _, dr, _ = parse_map(r['map'])
    team = {i: 'AB'[t] for i, (t, _b) in enumerate(dr)}
    cand_side = side_of(path, cand)
    counts = {x: 0 for x in REASONS}
    other = 0
    queen_death = None
    for e in r['events']:
        ty = e['type']
        if ty == 'dragonSplit':
            team[e['childId']] = e['team']
        elif ty == 'dragonDeath':
            i = e['id']
            t = team.get(i)
            if t is not None and t == cand_side:
                if e['reason'] in counts:
                    counts[e['reason']] += 1
                else:
                    other += 1
                if i in (0, 1):
                    queen_death = e['reason']
    return {'file': os.path.basename(path), 'map': mapname, 'nc': nc,
            'cls': 'BIG' if nc >= 600 else 'SMALL',
            'counts': counts, 'other': other, 'queen_death': queen_death}


if __name__ == '__main__':
    args = sys.argv[1:]
    cand = 'abyss_v263'
    if '--cand' in args:
        i = args.index('--cand'); cand = args[i + 1]; del args[i:i + 2]
    files = []
    for a in args:
        if os.path.isdir(a):
            files += sorted(glob.glob(os.path.join(a, '*.replay')))
        else:
            files.append(a)
    for f in files:
        try:
            print(json.dumps(analyze(f, cand)))
        except Exception as ex:
            print(json.dumps({'file': f, 'error': str(ex)}), file=sys.stderr)
