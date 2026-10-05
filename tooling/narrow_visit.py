"""Narrow-cell visit outcomes: do workers enter deg<=2 / region<40 cells, and
what ends each visit — exit to open cell, death (by reason), or split inside.

Usage: python3 tooling/narrow_visit.py <replay> [...]
Prints JSONL per replay: per-side counts of visits, exits, deaths-in-narrow
by reason, dwell turns, plus pearl eats by region-size band.
"""
import collections, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
from parse_replay import parse
from pocket_metric import parse_map, edge_kind, region_sizes, cell_deg, D, POCKET

def main(path):
    r = parse(path)
    ev = r['events']
    W, H, dr, edges = parse_map(r['map'])
    rsize = region_sizes(W, H, edges, 120)
    deg = [cell_deg(W, H, edges, x, y) for y in range(H) for x in range(W)]

    def narrow(c):
        return deg[c[1] * W + c[0]] <= 2 or rsize[c[1] * W + c[0]] < POCKET

    body, team = {}, {}
    for e in ev:
        if e['type'] == 'roundStart': break
        if e['type'] == 'dragonUpdate' and e['id'] < len(dr):
            t, b = dr[e['id']]
            body[e['id']] = collections.deque(b)
            team[e['id']] = 'AB'[t]
    T = {s: collections.Counter() for s in 'AB'}
    innarrow = {}   # id -> dwell length of current visit
    heads = {}
    pend = set()

    def end_visit(i, s, outcome):
        if i in innarrow:
            T[s]['visits'] += 1
            T[s]['v_' + outcome] += 1
            T[s]['dwell'] += innarrow[i]
            del innarrow[i]

    for e in ev:
        ty = e['type']
        if ty == 'tileChange':
            if not e['hasPearl']: pend.add(tuple(e['tile']))
        elif ty == 'dragonUpdate':
            i = e['id']
            if i not in body: continue
            b = body[i]
            h, tl = tuple(e['head']), tuple(e['tail'])
            s = team[i]
            if b[0] != h:
                b.appendleft(h)
                if h in pend:
                    T[s]['eaten'] += 1
                    rs = rsize[h[1] * W + h[0]]
                    T[s]['eaten_r%d' % (40 if rs < 40 else (120 if rs < 120 else 121))] += 1
            pend.discard(h)
            while len(b) > 1 and b[-1] != tl: b.pop()
            heads[i] = h
            # visit bookkeeping on the NEW head position
            if narrow(h):
                innarrow[i] = innarrow.get(i, 0) + 1
            else:
                end_visit(i, s, 'exit')
        elif ty == 'dragonSplit':
            s = e['team']
            body[e['parentId']] = collections.deque(tuple(x) for x in e['parentBody'])
            c = e['childId']
            body[c] = collections.deque(tuple(x) for x in e['childBody'])
            team[c] = s
            heads[e['parentId']] = tuple(e['parentBody'][0])
            heads[c] = tuple(e['childBody'][0])
            if e['parentId'] in innarrow:
                end_visit(e['parentId'], s, 'split')
            if narrow(heads[c]): innarrow[c] = 1
            if narrow(heads[e['parentId']]): innarrow[e['parentId']] = 1
        elif ty == 'dragonDeath':
            i = e['id']
            s = team.get(i)
            if s is None: continue
            if i in innarrow:
                end_visit(i, s, 'die_' + e['reason'])
            body.pop(i, None)
            heads.pop(i, None)
    for i, s in list(team.items()):
        if i in innarrow: end_visit(i, s, 'open_at_end')
    return {'file': os.path.basename(path), 'A': dict(T['A']), 'B': dict(T['B'])}

if __name__ == '__main__':
    for p in sys.argv[1:]:
        try:
            print(json.dumps(main(p)))
        except Exception as ex:
            print(json.dumps({'file': os.path.basename(p), 'error': str(ex)}))
