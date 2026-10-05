"""Drop capture study: where do feeder drops land relative to own dragons.

For each non-queen death r>=200: does an own-team head pass over the dead dragon's
cell within 12 rounds? And is that eater the longest own dragon? Tests the
'die in place on the champion's path' claim directly.
"""
import collections, glob, json, os, re, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../tooling'))
from parse_replay import parse  # noqa: E402
import replay_metrics as rm      # noqa: E402

OPEN = {'Autarky', 'Around UNSW', 'Big Empty', 'Schooltime', 'Islands', 'Australia'}


def tdist(a, b, W, H):
    dx = abs(a[0] - b[0]); dx = min(dx, W - dx)
    dy = abs(a[1] - b[1]); dy = min(dy, H - dy)
    return dx + dy


def analyze(path):
    r = parse(path)
    W, H, dr, edges = rm.parse_map(r['map'])
    team, body = {}, {}
    for i, (t, b) in enumerate(dr):
        team[i] = 'AB'[t]
        body[i] = collections.deque(tuple(x) for x in b)
    queen = {s: min((i for i in team if team[i] == s), default=-1) for s in 'AB'}

    # forward pass: collect per-round heads+lens, and death cells
    heads = collections.defaultdict(dict)
    lens = collections.defaultdict(dict)
    deaths = []  # (rnd, id, reason, cell, side, len)
    rnd = 0
    for e in r['events']:
        ty = e['type']
        if ty == 'roundStart':
            rnd = e['round']
            heads[rnd] = {i: body[i][0] for i in body}
            lens[rnd] = {i: len(body[i]) for i in body}
        elif ty == 'dragonUpdate':
            i = e['id']
            if i not in body:
                continue
            b = body[i]
            h, tl = tuple(e['head']), tuple(e['tail'])
            if b[0] != h:
                b.appendleft(h)
            while len(b) > 1 and b[-1] != tl:
                b.pop()
        elif ty == 'dragonSplit':
            body[e['parentId']] = collections.deque(tuple(x) for x in e['parentBody'])
            body[e['childId']] = collections.deque(tuple(x) for x in e['childBody'])
            team[e['childId']] = e['team']
        elif ty == 'dragonDeath':
            i = e['id']
            if i in body:
                deaths.append((rnd, i, e['reason'], list(body[i]), team.get(i)))
            body.pop(i, None)

    res = r['result'] or {}
    return {'W': W, 'H': H, 'team': team, 'queen': queen, 'heads': heads, 'lens': lens,
            'deaths': deaths, 'winner': res.get('winner'),
            'map': (re.search(r'MAP_NAME (.+)', r['map']).group(1) if re.search(r'MAP_NAME (.+)', r['map']) else '?')}


def main():
    sides = {}
    for t in [264, 306, 91, 213]:
        for line in open(f'/tmp/matches_{t}.jsonl'):
            m = json.loads(line)
            slot = 'A' if m['a']['id'] == t else 'B'
            sides[m['id']] = slot
    our = {}
    for line in open('/tmp/matches_351.jsonl'):
        m = json.loads(line)
        our[m['id']] = ('A' if m['a']['id'] == 351 else 'B', m['winner'].upper() == ('A' if m['a']['id'] == 351 else 'B'))

    C = {k: {'tot': 0, 'cap': 0, 'capLong': 0, 'capQueen': 0,
             'dist2': [], 'dreason': collections.Counter()} for k in ('top', 'our', 'ourw')}

    def record(key, a, s):
        W, H = a['W'], a['H']
        q = a['queen'][s]
        for (rnd, i, reason, cells, _t) in a['deaths']:
            s2 = a['team'].get(i)
            if s2 != s or i == q or rnd < 200:
                continue
            C[key]['tot'] += 1
            C[key]['dreason'][reason] += 1
            # who passes over the dead body's cells within 12 rounds
            eaters = set()
            for rr in range(rnd, min(rnd + 13, 500)):
                for j, h in a['heads'].get(rr, {}).items():
                    if a['team'].get(j) == s and h in cells:
                        eaters.add(j)
                        break
            if not eaters:
                continue
            C[key]['cap'] += 1
            L = a['lens'].get(rnd, {})
            own = sorted(((v, j) for j, v in L.items() if a['team'].get(j) == s), reverse=True)
            longest = own[0][1] if own else -1
            if longest in eaters:
                C[key]['capLong'] += 1
            if q in eaters:
                C[key]['capQueen'] += 1

    for f in sorted(glob.glob('top_replays/*.replay')):
        mid = int(re.search(r'm(\d+)\.replay', f).group(1))
        if mid not in sides:
            continue
        try:
            a = analyze(f)
        except Exception as ex:
            print('ERR', f, ex); continue
        if a['map'] not in OPEN:
            continue
        record('top', a, sides[mid])
    for f in sorted(glob.glob('our_replays/*.replay')):
        mid = int(re.search(r'm(\d+)\.replay', f).group(1))
        if mid not in our:
            continue
        try:
            a = analyze(f)
        except Exception as ex:
            print('ERR', f, ex); continue
        record('ourw' if our[mid][1] else 'our', a, our[mid][0])

    for k, c in C.items():
        tot = max(1, c['tot']); cap = max(1, c['cap'])
        print(f"== {k}: deaths r>=200={c['tot']} captured={c['cap']} ({c['cap']/tot:.0%})"
              f" byLongest={c['capLong']/cap:.0%} byQueen={c['capQueen']/cap:.0%}")
        print('   death reasons:', dict(c['dreason']))


if __name__ == '__main__':
    main()
