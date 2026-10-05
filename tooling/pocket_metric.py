"""Pocket-occupancy metrics from a .replay: do a team's workers forage dead-end pockets?

Per side: dragon-rounds with head in pocket cells (static region<40 / <120 via
walls-only BFS), pearls eaten while in pocket, deaths by reason, deaths with
head in pocket<40, plus opening-race context.

Usage: python3 tooling/pocket_metric.py <replay> [...]
"""
import collections, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
from parse_replay import parse

D = {'N': (0, -1), 'E': (1, 0), 'S': (0, 1), 'W': (-1, 0)}
POCKET, POCKETISH = 40, 120

def parse_map(txt):
    W = H = 0
    dr, edges = [], {}
    for line in txt.split('\n'):
        p = line.split()
        if not p: continue
        if p[0] == 'MAP': W, H = int(p[1]), int(p[2])
        elif p[0] == 'DRAGON':
            t, n = int(p[1]), int(p[2])
            c = list(map(int, p[3:3 + 2 * n]))
            dr.append((t, [(c[2 * i], c[2 * i + 1]) for i in range(n)]))
        elif p[0] == 'EDGE':
            edges[int(p[1])] = (int(p[2]), int(p[3]))
    return W, H, dr, edges

def edge_kind(edges, W, H, x, y, d):
    if d == 'N': i = 2 * y * (W + 1) + x
    elif d == 'S': i = 2 * ((y + 1) % H) * (W + 1) + x
    elif d == 'W': i = (2 * y + 1) * (W + 1) + x
    else: i = (2 * y + 1) * (W + 1) + (x + 1) % W
    return edges.get(i, (0, -1))[0]

def region_sizes(W, H, edges, cap):
    """per-cell walls-only reachable count, capped."""
    out = [0] * (W * H)
    for y in range(H):
        for x in range(W):
            i0 = y * W + x
            if out[i0]: continue
            seen = {i0: 0}
            q = [i0]
            for c in q:
                cx, cy = c % W, c // W
                for d, (dx, dy) in D.items():
                    if edge_kind(edges, W, H, cx, cy, d) != 0: continue
                    t = ((cx + dx) % W, (cy + dy) % H)
                    ti = t[1] * W + t[0]
                    if ti not in seen:
                        seen[ti] = 0
                        q.append(ti)
                if len(q) >= cap: break
            for c in q: out[c] = min(len(q), cap)
    return out

def cell_deg(W, H, edges, x, y):
    n = 0
    for d in D:
        if edge_kind(edges, W, H, x, y, d) == 0: n += 1
    return n

def main(path):
    r = parse(path)
    ev = r['events']
    W, H, dr, edges = parse_map(r['map'])
    rsize = region_sizes(W, H, edges, POCKETISH)
    deg = [cell_deg(W, H, edges, x, y) for y in range(H) for x in range(W)]
    body, team = {}, {}
    queen = {}
    for e in ev:
        if e['type'] == 'roundStart': break
        if e['type'] == 'dragonUpdate' and e['id'] < len(dr):
            t, b = dr[e['id']]
            body[e['id']] = collections.deque(tuple(x) for x in b)
            team[e['id']] = 'AB'[t]
    qid = {s: min(i for i, t in team.items() if t == s) for s in 'AB'}
    for i in qid.values(): queen[i] = True
    T = {s: collections.Counter() for s in 'AB'}
    pearls, pend = set(), set()
    rnd = 0
    heads = {}
    for e in ev:
        ty = e['type']
        if ty == 'roundStart':
            rnd = e['round']
            for i, h in heads.items():
                s = team.get(i)
                if s is None: continue
                rs = rsize[h[1] * W + h[0]]
                if rs < POCKET: T[s]['turnsPocket'] += 1
                if rs < POCKETISH: T[s]['turnsPocketish'] += 1
                if deg[h[1] * W + h[0]] <= 2: T[s]['turnsNarrow'] += 1
                T[s]['turnsN'] += 1
        elif ty == 'tileChange':
            t = tuple(e['tile'])
            if e['hasPearl']: pearls.add(t)
            else:
                pearls.discard(t); pend.add(t)
        elif ty == 'dragonUpdate':
            i = e['id']
            if i not in body: continue
            b = body[i]
            h, tl = tuple(e['head']), tuple(e['tail'])
            if b[0] != h:
                b.appendleft(h)
                if h in pend:
                    T[team[i]]['eaten'] += 1
                    if rsize[h[1] * W + h[0]] < POCKET: T[team[i]]['eatenPocket'] += 1
            pend.discard(h)
            while len(b) > 1 and b[-1] != tl: b.pop()
            heads[i] = h
        elif ty == 'dragonSplit':
            s = e['team']
            body[e['parentId']] = collections.deque(tuple(x) for x in e['parentBody'])
            c = e['childId']
            body[c] = collections.deque(tuple(x) for x in e['childBody'])
            team[c] = s
            heads[e['parentId']] = e['parentBody'][0]
            heads[c] = e['childBody'][0]
        elif ty == 'dragonDeath':
            i = e['id']
            s = team.get(i)
            if s is None: continue
            T[s]['deaths'] += 1
            T[s]['d_' + e['reason']] += 1
            if queen.get(i): T[s]['dQueen'] += 1
            # round buckets: early <100, mid 100-359, late 360+ (feed/transit window)
            rb = 'E' if rnd < 100 else ('M' if rnd < 360 else 'L')
            T[s]['dr%s_%s' % (rb, e['reason'])] += 1
            T[s]['drr%s' % rb] += 1
            h = heads.get(i)
            if h:
                ci = h[1] * W + h[0]
                rs = rsize[ci]
                if rs < POCKET:
                    T[s]['deathsPocket'] += 1
                    T[s]['dp_' + e['reason']] += 1
                elif rs < POCKETISH:
                    T[s]['deathsPocketish'] += 1
                else:
                    T[s]['deathsOpen'] += 1
                dg = deg[ci]
                T[s]['dn%d_%s' % (min(dg, 3), e['reason'])] += 1
            body.pop(i, None)
            heads.pop(i, None)
    return {'file': os.path.basename(path), 'rounds': rnd,
            'A': dict(T['A']), 'B': dict(T['B'])}

if __name__ == '__main__':
    for p in sys.argv[1:]:
        try:
            print(json.dumps(main(p)))
        except Exception as ex:
            print(json.dumps({'file': os.path.basename(p), 'error': str(ex)}))
