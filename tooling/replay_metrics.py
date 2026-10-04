"""Per-game metrics from a replay, for local A/B evaluation.

Usage: python3 tooling/replay_metrics.py <replay> [...]   # one JSON line per game

Metrics per side (A/B), tied to the blockers in analysis/our-games/report.md:
  win, end, rounds                      outcome
  alive499, longest, total, queenEnd    round-500 consolidation (blocker 1)
  eaten, turns, ppt                     pearls per dragon-turn (blocker 2)
  adjN, adjAte, adjQuietN, adjQuietAte  free pearl adjacent to head -> eaten that turn (blocker 2)
  qDeadRound, qDeadReason, qNonRam      queen deaths, non-ram = not hitHeadToHead (blocker 3)
  slayOpp1/2/3, slayKill1/2/3           dragon-turns with the enemy queen in vision and a free path
                                        within reach ceil(L/4)+L-2 (by path length, 3 = 3+),
                                        and how many ended with her dead that turn
  eaten60, splits60, alive50            opening race (blocker 4)
Replay parsing follows analysis/our-games/scripts/an.py and forage2.py.
"""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
from parse_replay import parse  # noqa: E402

D = {'N': (0, -1), 'E': (1, 0), 'S': (0, 1), 'W': (-1, 0)}


def parse_map(txt):
    W = H = 0
    dr = []
    edges = {}
    for line in txt.split('\n'):
        p = line.split()
        if not p:
            continue
        if p[0] == 'MAP':
            W, H = int(p[1]), int(p[2])
        elif p[0] == 'DRAGON':
            t, n = int(p[1]), int(p[2])
            c = list(map(int, p[3:3 + 2 * n]))
            dr.append((t, [(c[2 * i], c[2 * i + 1]) for i in range(n)]))
        elif p[0] == 'EDGE':
            edges[int(p[1])] = (int(p[2]), int(p[3]))
    return W, H, dr, edges


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


def analyze(path):
    r = parse(path)
    ev = r['events']
    W, H, dr, edges = parse_map(r['map'])

    def tdist(a, b):
        dx = abs(a[0] - b[0])
        dy = abs(a[1] - b[1])
        return min(dx, W - dx) + min(dy, H - dy)

    body, team = {}, {}
    for e in ev:
        if e['type'] == 'roundStart':
            break
        if e['type'] == 'dragonUpdate' and e['id'] < len(dr):
            t, b = dr[e['id']]
            body[e['id']] = collections.deque(tuple(x) for x in b)
            team[e['id']] = 'AB'[t]
    queen = {s: min((i for i in team if team[i] == s), default=-1) for s in 'AB'}
    T = {s: collections.Counter() for s in 'AB'}
    qdead = {s: None for s in 'AB'}
    alive_at = {s: {} for s in 'AB'}
    tot_at = {s: {} for s in 'AB'}
    pearls, pend = set(), set()
    occ = set()
    rnd = 0
    st = None  # (id, side, adjacent?, quiet?, ate)
    slay = None  # (dragon id, side, distance bucket) while that dragon has an in-reach enemy queen

    def path_dist(src, dst, limit):
        # BFS over free tiles (no kelp, no portal edges, no bodies except the target head)
        seen = {src: 0}
        q = [src]
        for c in q:
            if seen[c] >= limit:
                continue
            for d, (dx, dy) in D.items():
                if edge_kind(edges, W, H, c[0], c[1], d) != 0:
                    continue
                t = ((c[0] + dx) % W, (c[1] + dy) % H)
                if t in seen:
                    continue
                if t == dst:
                    return seen[c] + 1
                if t in occ:
                    continue
                seen[t] = seen[c] + 1
                q.append(t)
        return None

    def close():
        nonlocal st
        if st is None:
            return
        i, s, adj, quiet, ate = st
        if adj:
            T[s]['adjN'] += 1
            T[s]['adjAte'] += ate > 0
            if quiet:
                T[s]['adjQuietN'] += 1
                T[s]['adjQuietAte'] += ate > 0
        st = None

    for e in ev:
        ty = e['type']
        if ty == 'roundStart':
            close()
            rnd = e['round']
            for s in 'AB':
                alive_at[s][rnd] = sum(1 for j in body if team[j] == s)
                tot_at[s][rnd] = sum(len(body[j]) for j in body if team[j] == s)
            occ = set()
            for b in body.values():
                occ.update(b)
        elif ty == 'tileChange':
            t = tuple(e['tile'])
            if e['hasPearl']:
                pearls.add(t)
            else:
                pearls.discard(t)
                pend.add(t)
        elif ty == 'turnStart':
            close()
            slay = None
            i = e['id']
            if i not in body:
                continue
            s = team[i]
            h = body[i][0]
            eq = queen['B' if s == 'A' else 'A']
            if i > 1 and eq in body:
                qh = body[eq][0]
                dx, dy = abs(qh[0] - h[0]), abs(qh[1] - h[1])
                if max(min(dx, W - dx), min(dy, H - dy)) <= 3:  # in 7x7 vision
                    L = len(body[i])
                    reach = -(-L // 4) + L - 2
                    pd = path_dist(h, qh, reach)
                    if pd is not None:
                        b = str(min(pd, 3))
                        T[s]['slayOpp' + b] += 1
                        slay = (i, s, b)
            adj = False
            for d, (dx, dy) in D.items():
                if edge_kind(edges, W, H, h[0], h[1], d) == 1:
                    continue
                t = ((h[0] + dx) % W, (h[1] + dy) % H)
                if t in pearls and t not in occ:
                    adj = True
                    break
            quiet = True
            if adj:
                quiet = not any(tdist(h, body[j][0]) <= 3 for j in body if team[j] != s)
            st = [i, s, adj, quiet, 0]
        elif ty == 'dragonAction':
            s = team.get(e['id'])
            if s is not None:
                T[s]['turns'] += 1
        elif ty == 'dragonUpdate':
            i = e['id']
            if i not in body:
                continue
            b = body[i]
            h, tl = tuple(e['head']), tuple(e['tail'])
            if b[0] != h:
                b.appendleft(h)
                occ.add(h)
                if h in pend:
                    T[team[i]]['eaten'] += 1
                    if rnd <= 60:
                        T[team[i]]['eaten60'] += 1
                    if i == queen[team[i]]:
                        T[team[i]]['qEaten'] += 1
                    if st and st[0] == i:
                        st[4] += 1
            pend.discard(h)
            while len(b) > 1 and b[-1] != tl:
                b.pop()
        elif ty == 'dragonSplit':
            s = e['team']
            body[e['parentId']] = collections.deque(tuple(x) for x in e['parentBody'])
            c = e['childId']
            body[c] = collections.deque(tuple(x) for x in e['childBody'])
            team[c] = s
            T[s]['splits'] += 1
            if rnd <= 60:
                T[s]['splits60'] += 1
        elif ty == 'dragonDeath':
            i = e['id']
            s = team.get(i)
            if s is None:
                continue
            T[s]['deaths'] += 1
            T[s]['d_' + e['reason']] += 1
            if i == queen[s]:
                qdead[s] = (rnd, e['reason'])
                if slay and slay[1] != s:
                    T[slay[1]]['slayKill' + slay[2]] += 1
                    slay = None
            body.pop(i, None)
    close()

    res = r['result']
    out = {'file': os.path.basename(path), 'map': None, 'botA': r.get('botA'), 'botB': r.get('botB'),
           'seed': r.get('seed'), 'end': res.get('endReason'), 'rounds': rnd, 'winner': res.get('winner')}
    for s in 'AB':
        tr = res.get('team' + s) or {}
        c = T[s]
        o = dict(c)
        o['win'] = 1.0 if res.get('winner') == s else 0.5 if res.get('winner') in (None, '', 'draw') else 0.0
        o['alive'] = tr.get('dragonCount', 0)
        o['alive499'] = alive_at[s].get(499)
        o['alive50'] = alive_at[s].get(50)
        o['tl50'] = tot_at[s].get(50)
        o['tl100'] = tot_at[s].get(100)
        o['longest'] = tr.get('longestDragon', 0)
        o['total'] = tr.get('totalLength', 0)
        q = queen[s]
        o['queenEnd'] = len(body[q]) if q in body else 0
        o['qDeadRound'] = qdead[s][0] if qdead[s] else None
        o['qDeadReason'] = qdead[s][1] if qdead[s] else None
        o['qNonRam'] = int(bool(qdead[s]) and qdead[s][1] != 'hitHeadToHead')
        o['ppt'] = c['eaten'] / max(1, c['turns'])
        out[s] = o
    return out


if __name__ == '__main__':
    for p in sys.argv[1:]:
        print(json.dumps(analyze(p)))
