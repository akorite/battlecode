"""Queen behavior study: top teams vs Cognoscenti (351).

Per replay, per round: queen head, movement, escort distance (nearest own head),
enemy proximity, cell openness (degree), region size (flood over open edges),
death round/reason. Aggregates per cohort in buckets early<100, mid 100-330, late 330+.

Usage: python3 analysis/queen_study.py
"""
import collections, glob, json, os, sys, re

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../tooling'))
from parse_replay import parse  # noqa: E402
import replay_metrics as rm      # noqa: E402

D = {'N': (0, -1), 'E': (1, 0), 'S': (0, 1), 'W': (-1, 0)}


def edge_kind(edges, W, H, x, y, d):
    if d == 'N':
        i = 2 * y * (W + 1) + x
    elif d == 'S':
        i = 2 * ((y + 1) % H) * (W + 1) + x
    elif d == 'W':
        i = (2 * y + 1) * (W + 1) + x
    else:
        i = (2 * y + 1) * (W + 1) + (x + 1) % W
    return edges.get(i, (0, -1))[0]


def tdist(a, b, W, H):
    dx = abs(a[0] - b[0]); dx = min(dx, W - dx)
    dy = abs(a[1] - b[1]); dy = min(dy, H - dy)
    return dx + dy


def flood(open_nb, src, cap):
    seen = {src}
    q = [src]
    for c in q:
        if len(seen) >= cap:
            break
        for n in open_nb[c]:
            if n not in seen:
                seen.add(n)
                q.append(n)
    return len(seen)


def analyze(path):
    r = parse(path)
    W, H, dr, edges = rm.parse_map(r['map'])
    # open neighbors per cell (kind-0 edges only: no kelp walls, no portals)
    open_nb = {}
    for y in range(H):
        for x in range(W):
            c = []
            for d, (dx, dy) in D.items():
                if edge_kind(edges, W, H, x, y, d) == 0:
                    c.append(((x + dx) % W, (y + dy) % H))
            open_nb[(x, y)] = c
    # team assignment
    team = {}
    for e in r['events']:
        if e['type'] == 'roundStart':
            break
        if e['type'] == 'dragonUpdate' and e['id'] < len(dr):
            team[e['id']] = 'AB'[dr[e['id']][0]]
    queen = {s: min((i for i in team if team[i] == s), default=-1) for s in 'AB'}
    heads = {}  # id -> cell, updated on every dragonUpdate
    for i, (t, body) in enumerate(dr):
        heads[i] = tuple(body[0])

    out = {s: {'moves': [], 'escort': [], 'eProx3': 0, 'eProx5': 0, 'eRounds': 0,
               'deg': [], 'region': [], 'qDead': None, 'qDeadReason': None,
               'snap': collections.defaultdict(lambda: [0, 0, 0.0, 0.0, 0, 0, 0.0, 0.0, 0])}
           for s in 'AB'}
    rnd = 0
    prev_qhead = {}
    for e in r['events']:
        ty = e['type']
        if ty == 'roundStart':
            rnd = e['round']
            for s in 'AB':
                q = queen[s]
                if q < 0 or q not in heads:
                    continue
                qh = heads[q]
                o = out[s]
                own = [heads[i] for i in heads if team.get(i) == s and i != q]
                en = [heads[i] for i in heads if team.get(i) and team[i] != s]
                moved = prev_qhead.get(s) is not None and qh != prev_qhead[s]
                esc = min((tdist(qh, h, W, H) for h in own), default=99)
                ed = min((tdist(qh, h, W, H) for h in en), default=99)
                b = 'e' if rnd < 100 else ('m' if rnd < 330 else 'l')
                z = o['snap'][b]
                z[0] += 1                      # rounds alive
                z[1] += 1 if moved else 0      # moved
                z[2] += esc                    # escort dist
                z[3] += len(open_nb.get(qh, []))
                z[4] += 1 if ed <= 3 else 0    # enemy within 3
                z[5] += 1 if ed <= 5 else 0
                z[6] += ed
                if rnd % 5 == 0:
                    z[7] += flood(open_nb, qh, 40)
                    z[8] += 1
                prev_qhead[s] = qh
        elif ty == 'dragonUpdate':
            heads[e['id']] = tuple(e['head'])
        elif ty == 'dragonSplit':
            team[e['childId']] = e['team']
            heads[e['childId']] = tuple(e['childBody'][0])
            heads[e['parentId']] = tuple(e['parentBody'][0])
        elif ty == 'dragonDeath':
            if e['id'] == queen.get(team.get(e['id']), -1):
                s = team[e['id']]
                out[s]['qDead'] = rnd
                out[s]['qDeadReason'] = e['reason']
            heads.pop(e['id'], None)
    res = r.get('result') or {}
    return {'W': W, 'H': H, 'out': out, 'winner': res.get('winner'),
            'map': re.search(r'MAP_NAME (.+)', r['map']).group(1) if re.search(r'MAP_NAME (.+)', r['map']) else '?'}


def emit(name, agg):
    print(f'== {name} ==')
    for b, label in [('e', 'early<100'), ('m', 'mid 100-330'), ('l', 'late 330+')]:
        z = agg[b]
        n = z[0]
        if not n:
            print(f'  {label}: no data')
            continue
        nreg = z[8] or 1
        print(f'  {label}: rounds={int(z[0])} moveRate={z[1]/n:.2f} escort={z[2]/n:.1f} '
              f'deg={z[3]/n:.1f} enemy<=3:{z[4]/n:.2f} enemy<=5:{z[5]/n:.2f} edMean={z[6]/n:.1f} region={z[7]/nreg:.0f}')


def main():
    # build id -> (team side, team won) for top replays
    sides = {}
    for t in [264, 306, 91, 213]:
        for line in open(f'/tmp/matches_{t}.jsonl'):
            m = json.loads(line)
            slot = 'A' if m['a']['id'] == t else 'B'
            won = m['winner'].upper() == slot
            sides[m['id']] = (slot, won, t)
    our = {}
    for line in open('/tmp/matches_351.jsonl'):
        m = json.loads(line)
        slot = 'A' if m['a']['id'] == 351 else 'B'
        our[m['id']] = (slot, m['winner'].upper() == slot)

    TOP = collections.defaultdict(lambda: [0, 0, 0.0, 0.0, 0, 0, 0.0, 0.0, 0])
    TOPopp = collections.defaultdict(lambda: [0, 0, 0.0, 0.0, 0, 0, 0.0, 0.0, 0])
    OUR = collections.defaultdict(lambda: [0, 0, 0.0, 0.0, 0, 0, 0.0, 0.0, 0])
    OURw = collections.defaultdict(lambda: [0, 0, 0.0, 0.0, 0, 0, 0.0, 0.0, 0])
    dead = {'top': collections.Counter(), 'topopp': collections.Counter(),
            'our': collections.Counter(), 'ourw': collections.Counter()}
    qrounds = {'top': [], 'topopp': [], 'our': [], 'ourw': []}

    for f in sorted(glob.glob('top_replays/*.replay')):
        mid = int(re.search(r'm(\d+)\.replay', f).group(1))
        if mid not in sides:
            continue
        slot, won, t = sides[mid]
        try:
            a = analyze(f)
        except Exception as ex:
            print('ERR', f, ex)
            continue
        if a['map'] not in ('Autarky', 'Around UNSW', 'Big Empty', 'Schooltime', 'Islands', 'Australia'):
            continue  # open/decision maps only — queen behavior differs by class
        for s, key in [(slot, 'top'), ('AB'[1 - 'AB'.index(slot)], 'topopp')]:
            o = a['out'][s]
            G = TOP if key == 'top' else TOPopp
            for b in 'eml':
                z = o['snap'][b]
                for i in range(9):
                    G[b][i] += z[i]
            if o['qDead'] is not None:
                dead[key][o['qDeadReason']] += 1
                qrounds[key].append(o['qDead'])
            else:
                dead[key]['alive'] += 1
                qrounds[key].append(499)

    for f in sorted(glob.glob('our_replays/*.replay')):
        mid = int(re.search(r'm(\d+)\.replay', f).group(1))
        if mid not in our:
            continue
        slot, won = our[mid]
        try:
            a = analyze(f)
        except Exception as ex:
            print('ERR', f, ex)
            continue
        o = a['out'][slot]
        if not won:
            z = o['snap']['l'] if o['snap']['l'][0] else o['snap']['m']
            print('LOSS', a['map'], f, 'qDead', o['qDead'], o['qDeadReason'],
                  'lateEscort', round(z[2]/max(1,z[0]),1), 'lateDeg', round(z[3]/max(1,z[0]),1))
        G = OURw if won else OUR
        for b in 'eml':
            z = o['snap'][b]
            for i in range(9):
                G[b][i] += z[i]
        k = 'ourw' if won else 'our'
        if o['qDead'] is not None:
            dead[k][o['qDeadReason']] += 1
            qrounds[k].append(o['qDead'])
        else:
            dead[k]['alive'] += 1
            qrounds[k].append(499)

    emit('TOP teams (their side, open maps)', TOP)
    emit('TOP opponents (other side)', TOPopp)
    emit('OURS losses', OUR)
    emit('OURS wins', OURw)
    for k in dead:
        qr = qrounds[k]
        print(k, 'queen deaths:', dict(dead[k]),
              'median death round:', sorted(qr)[len(qr) // 2] if qr else '-')


if __name__ == '__main__':
    main()
