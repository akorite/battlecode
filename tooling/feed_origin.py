"""Feeder origin profile: how do dragons get adjacent to the champion —
path to it, or spawned/budded next to it?

Per side per death: dist(spawnCell -> deathCell), dist(deathCell -> champHead
at that round), split reason. Spawn cell = child's head at dragonSplit (or
initial DRAGON head for starters). Champ proxy = side's longest live dragon
at that round (head cell).

Usage: python3 tooling/feed_origin.py <replay> [...] -> JSONL
"""
import collections, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
from parse_replay import parse
from pocket_metric import parse_map

def main(path):
    r = parse(path)
    ev = r['events']
    W, H, dr, edges = parse_map(r['map'])
    body, team, spawn = {}, {}, {}
    for e in ev:
        if e['type'] == 'roundStart': break
        if e['type'] == 'dragonUpdate' and e['id'] < len(dr):
            t, b = dr[e['id']]
            body[e['id']] = collections.deque(b)
            team[e['id']] = 'AB'[t]
            spawn[e['id']] = b[0]
    out = {s: collections.Counter() for s in 'AB'}
    dists = {s: [] for s in 'AB'}   # (spawn->death, death->champ, len) per deliberate death
    heads = {}
    rnd = 0
    def cheb(a, b):
        return max(abs(a[0] - b[0]), abs(a[1] - b[1]))
    def torus_cheb(a, b):
        dx = abs(a[0] - b[0]); dy = abs(a[1] - b[1])
        return max(min(dx, W - dx), min(dy, H - dy))
    for e in ev:
        ty = e['type']
        if ty == 'roundStart':
            rnd = e['round']
        elif ty == 'dragonUpdate':
            i = e['id']
            if i not in body: continue
            b = body[i]; h, tl = tuple(e['head']), tuple(e['tail'])
            if b[0] != h: b.appendleft(h)
            while len(b) > 1 and b[-1] != tl: b.pop()
            heads[i] = h
        elif ty == 'dragonSplit':
            s = e['team']
            body[e['parentId']] = collections.deque(tuple(x) for x in e['parentBody'])
            c = e['childId']
            body[c] = collections.deque(tuple(x) for x in e['childBody'])
            team[c] = s
            ph = tuple(e['parentBody'][0]); ch = tuple(e['childBody'][0])
            heads[e['parentId']] = ph; heads[c] = ch
            spawn[c] = ch
            out[s]['splits'] += 1
        elif ty == 'dragonDeath':
            i = e['id']
            s = team.get(i)
            if s is None: continue
            # champ = longest OTHER live dragon of this side (exclude dying)
            champ, chlen = None, 0
            for j, b2 in body.items():
                if j == i or team.get(j) != s: continue
                if len(b2) > chlen: chlen, champ = len(b2), j
            h = heads.get(i)
            sp = spawn.get(i, h)
            if h:
                out[s]['deaths'] += 1
                deliberate = e['reason'] in ('hitSelf', 'noValidAction')
                if deliberate: out[s]['delib'] += 1
                sd = torus_cheb(sp, h)
                dc = torus_cheb(h, heads[champ]) if champ else -1
                if deliberate:
                    dists[s].append((sd, dc, len(body[i])))
                    if dc >= 0 and dc <= 2: out[s]['delibNearChamp'] += 1
                    out[s]['sd_sum'] += sd; out[s]['dc_sum'] += max(dc, 0)
                if dc >= 0 and dc <= 2: out[s]['nearChamp'] += 1
            body.pop(i, None); heads.pop(i, None)
    res = {'file': os.path.basename(path)}
    for s in 'AB':
        d = dict(out[s])
        if dists[s]:
            s2 = sorted(x[0] for x in dists[s]); d['sd_med'] = s2[len(s2) // 2]
            s2 = sorted(x[1] for x in dists[s]); d['dc_med'] = s2[len(s2) // 2]
        res[s] = d
    return res

if __name__ == '__main__':
    for p in sys.argv[1:]:
        try:
            print(json.dumps(main(p)))
        except Exception as ex:
            print(json.dumps({'file': os.path.basename(p), 'error': str(ex)}))
