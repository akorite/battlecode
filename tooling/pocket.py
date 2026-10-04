"""Pocket-starvation analyzer for weakhold replays.

Per team: alive/dragons over time, eats (pearl pickups) over time, splits,
death reasons, and per-dragon `why` histograms bucketed by round phase.
Dragon teams: initial dragons from map DRAGON lines (team 0->A side as listed
in map file == botA slot), splits carry parent team.

Usage: python3 pocket.py <replay> [...] [--rounds N]
"""
import sys, os, json, re, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
from parse_replay import parse

WHY = re.compile(r'^r(\d+) (\S+)(?:.*?\bL=(\d+))?')
DBG = re.compile(r'\bhx=(\d+) hy=(\d+)')


def map_starts(mapname):
    """team letter -> list of head cells from the map's DRAGON lines."""
    import glob
    for d in [os.path.expanduser('~/bc/workspace/maps'),
              os.path.expanduser('~/.venv-bc/lib/python3.12/site-packages/unswbc/templates/maps'),
              os.path.expanduser('~/bc/engine/maps')]:
        p = os.path.join(d, mapname + '.map')
        if os.path.exists(p):
            heads = {'A': [], 'B': []}
            for l in open(p):
                t = l.split()
                if t and t[0] == 'DRAGON':
                    heads['AB'[int(t[1])]].append((int(t[3]), int(t[4])))
            return heads
    return {'A': [], 'B': []}


def analyze(path, phase_edge=(60, 200)):
    rep = parse(path)
    starts = map_starts(rep['map'])
    start_pos = {h: t for t, hs in starts.items() for h in hs}
    team_of = {}
    for e in rep['events']:
        if e['type'] == 'roundStart':
            break
        if e['type'] == 'dragonUpdate' and tuple(e['head']) in start_pos:
            team_of[e['id']] = start_pos[tuple(e['head'])]

    why_hist = {'A': collections.Counter(), 'B': collections.Counter()}
    why_phase = {'A': [collections.Counter() for _ in range(3)], 'B': [collections.Counter() for _ in range(3)]}
    last_why = {}
    death_x_why = {'A': collections.Counter(), 'B': collections.Counter()}
    deaths = {'A': [], 'B': []}
    splits = {'A': [], 'B': []}
    eats = {'A': [], 'B': []}       # (round, id) pearl pickups attributed via tileChange(false)
    alive = {'A': collections.Counter(), 'B': collections.Counter()}
    pending_eat = {}
    cur_round = 0
    last_id = None
    seen_ids = set()

    for e in rep['events']:
        ty = e['type']
        if ty == 'roundStart':
            cur_round = e['round']
            for t in 'AB':
                alive[t][cur_round] = sum(1 for i in seen_ids if team_of.get(i) == t)
        elif ty == 'turnStart':
            last_id = e['id']
        elif ty == 'dragonUpdate':
            if e['id'] not in seen_ids:
                seen_ids.add(e['id'])
        elif ty == 'dragonSplit':
            team_of[e['childId']] = e['team']
            team_of.setdefault(e['parentId'], e['team'])
            seen_ids.update([e['childId'], e['parentId']])
            splits[e['team']].append(cur_round)
        elif ty == 'tileChange' and not e['hasPearl']:
            t = team_of.get(last_id)
            if t in 'AB':
                eats[t].append(cur_round)
        elif ty == 'dragonLog':
            m = WHY.match(e['text'])
            if not m:
                continue
            rnd, why = int(m.group(1)), m.group(2)
            d = team_of.get(e['id'])
            if not d:
                continue
            base = why.split(':')[0]
            why_hist[d][base] += 1
            ph = 0 if rnd < phase_edge[0] else (1 if rnd < phase_edge[1] else 2)
            why_phase[d][ph][base] += 1
            last_why[e['id']] = (rnd, base)
        elif ty == 'dragonDeath':
            d = team_of.get(e['id'])
            if not d:
                continue
            seen_ids.discard(e['id'])
            deaths[d].append((cur_round, e['reason']))
            rnd, why = last_why.get(e['id'], (-1, 'nolog'))
            death_x_why[d][f"{e['reason']}|{why}"] += 1

    def hist_rounds(rs, step=50):
        out = collections.Counter()
        for r in rs:
            out[r // step * step] += 1
        return dict(sorted(out.items()))

    return {
        'file': os.path.basename(path), 'map': rep['map'], 'botA': rep['botA'], 'botB': rep['botB'],
        'result': rep['result'],
        'deaths': {t: collections.Counter(r for _, r in deaths[t]) for t in 'AB'},
        'death_x_why': death_x_why,
        'why_phase': {t: [dict(c.most_common(8)) for c in why_phase[t]] for t in 'AB'},
        'eats_by50': {t: hist_rounds(eats[t]) for t in 'AB'},
        'splits_by50': {t: hist_rounds(splits[t]) for t in 'AB'},
        'last_alive': {t: max(alive[t].values()) if alive[t] else 0 for t in 'AB'},
    }


if __name__ == '__main__':
    for p in [a for a in sys.argv[1:] if not a.startswith('--')]:
        print(json.dumps(analyze(p), indent=1, default=lambda o: dict(o)))
