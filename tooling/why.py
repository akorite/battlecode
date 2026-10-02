"""Decision/death analyzer for replays with BC_DEBUG LOG lines.

Usage: python3 why.py <replay> [<replay> ...]
Prints JSON: per game, histogram of `why` decisions, and last-why x death-cause.
"""
import sys, os, json, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
from parse_replay import parse
import importlib.util
_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    'bc_mapdata', os.path.join(_HERE, '../handoff/tooling/battlecode-eval/bceval/mapdata.py'))
_mapdata = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_mapdata)

WHY = re.compile(r'^r(\d+) (\S+)')


def analyze(path):
    rep = parse(path)
    board = _mapdata.map_data(rep['map'])
    start_pos = {d['body'][0]: d['team'] for d in board['dragons']}
    team_of = {}
    for e in rep['events']:
        if e['type'] == 'roundStart':
            break
        if e['type'] == 'dragonUpdate' and tuple(e['head']) in start_pos:
            team_of[e['id']] = start_pos[tuple(e['head'])]

    why_hist = {'A': {}, 'B': {}}
    last_why = {}      # dragon id -> (round, why)
    death_x_why = {'A': {}, 'B': {}}
    depth_hist = {'A': [], 'B': []}
    for e in rep['events']:
        ty = e['type']
        if ty == 'dragonSplit':
            team_of[e['childId']] = e['team']
            team_of[e['parentId']] = e['team']
        elif ty == 'dragonLog':
            m = WHY.match(e['text'])
            if not m:
                continue
            rnd, why = int(m.group(1)), m.group(2)
            d = team_of.get(e['id'])
            if not d:
                continue
            base = why.split(':')[0]
            why_hist[d][base] = why_hist[d].get(base, 0) + 1
            last_why[e['id']] = (rnd, base)
            dm = re.search(r'depth=(\d+)', e['text'])
            if dm:
                depth_hist[d].append(int(dm.group(1)))
        elif ty == 'dragonDeath':
            d = team_of.get(e['id'])
            if not d:
                continue
            rnd, why = last_why.get(e['id'], (-1, 'nolog'))
            # bucket: died within 2 rounds of its last logged decision
            key = f"{e['reason']}|{why}"
            death_x_why[d][key] = death_x_why[d].get(key, 0) + 1
    return {
        'map': board['name'], 'why': why_hist, 'death_x_why': death_x_why,
        'depth': {s: round(sum(v) / max(1, len(v)), 1) for s, v in depth_hist.items()},
    }


if __name__ == '__main__':
    agg_why, agg_dx = {'A': {}, 'B': {}}, {'A': {}, 'B': {}}
    depths = {'A': [], 'B': []}
    for p in sys.argv[1:]:
        r = analyze(p)
        for s in 'AB':
            for k, v in r['why'][s].items():
                agg_why[s][k] = agg_why[s].get(k, 0) + v
            for k, v in r['death_x_why'][s].items():
                agg_dx[s][k] = agg_dx[s].get(k, 0) + v
            if r['depth'][s]:
                depths[s].append(r['depth'][s])
    print('WHY histogram:', json.dumps(agg_why, indent=1, sort_keys=True))
    print('DEATH x last-why:', json.dumps(agg_dx, indent=1, sort_keys=True))
    print('mean depth:', {s: round(sum(v) / max(1, len(v)), 1) for s, v in depths.items()})
