"""Queen-siege diagnosis: classify our queen's mid-game deaths in replays.

For each replay, reconstruct dragon bodies each round. When a tracked side's
queen (lowest starting id on that team) dies, record a snapshot of the 12
rounds before death: free exits at her head, enemies/friendlies nearby, her
length — and classify the death:

  encircled   exits stayed <=1 for >=3 of the last 6 rounds AND an enemy head
              was within cheb 6 at some point in the last 8 rounds
  pocketed    exits <=1 sustained but NO enemy near (she sealed herself in)
  rammed      exits were >=2 within 2 rounds of death (sudden H2H / sprint)
  fade        anything else (long starvation / unclear)

Usage:
  qsiege_diag.py --side A|B|both replay [...]
  qsiege_diag.py --ladder <matches.jsonl> replay_dir   # side from match id
"""
import argparse, collections, json, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../handoff/tooling'))
from parse_replay import parse

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


def analyze(path, sides=('A', 'B')):
    r = parse(path)
    ev = r['events']
    W, H, dr, edges = parse_map(r['map'])
    body, team = {}, {}
    for e in ev:
        if e['type'] == 'roundStart':
            break
        if e['type'] == 'dragonUpdate' and e['id'] < len(dr):
            t, b = dr[e['id']]
            body[e['id']] = collections.deque(tuple(x) for x in b)
            team[e['id']] = 'AB'[t]
    queen = {s: min((i for i in team if team[i] == s), default=-1) for s in 'AB'}

    def cheb(a, b):
        dx = abs(a[0] - b[0])
        dy = abs(a[1] - b[1])
        return max(min(dx, W - dx), min(dy, H - dy))

    hist = {s: collections.deque(maxlen=13) for s in 'AB'}   # per-round queen state
    deaths = []
    occ = set()
    rnd = 0
    for e in ev:
        ty = e['type']
        if ty == 'roundStart':
            rnd = e['round']
            occ = set()
            for b in body.values():
                occ.update(b)
            for s in sides:
                q = queen[s]
                if q not in body:
                    continue
                h = body[q][0]
                ex = 0
                for d, (dx, dy) in D.items():
                    if edge_kind(edges, W, H, h[0], h[1], d) != 0:
                        continue
                    t = ((h[0] + dx) % W, (h[1] + dy) % H)
                    if t not in occ:
                        ex += 1
                en6 = sum(1 for j in body if team[j] != s and cheb(h, body[j][0]) <= 6)
                en3 = sum(1 for j in body if team[j] != s and cheb(h, body[j][0]) <= 3)
                fr4 = sum(1 for j in body if team[j] == s and j != q and cheb(h, body[j][0]) <= 4)
                hist[s].append((rnd, ex, en6, en3, fr4, len(body[q]), h))
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
            s = e['team']
            body[e['parentId']] = collections.deque(tuple(x) for x in e['parentBody'])
            c = e['childId']
            body[c] = collections.deque(tuple(x) for x in e['childBody'])
            team[c] = s
        elif ty == 'dragonDeath':
            i = e['id']
            s = team.get(i)
            if s is None:
                continue
            if i == queen[s] and s in sides:
                snap = list(hist[s])
                last6 = [x[1] for x in snap[-6:]] or [9]
                en_near = any(x[2] > 0 for x in snap[-8:])
                if (sum(1 for x in last6 if x <= 1) >= 3 or (last6 and last6[-1] == 0)):
                    cls = 'encircled' if en_near else 'pocketed'
                elif len(last6) >= 2 and last6[-2] >= 2:
                    cls = 'rammed'
                else:
                    cls = 'fade'
                deaths.append({
                    'side': s, 'round': rnd, 'reason': e['reason'], 'cls': cls,
                    'len': len(body[i]), 'trail': [
                        {'r': x[0], 'ex': x[1], 'en6': x[2], 'en3': x[3],
                         'fr4': x[4], 'len': x[5], 'h': x[6]} for x in snap],
                })
            body.pop(i, None)
    res = r['result']
    return {'file': os.path.basename(path), 'rounds': rnd, 'winner': res.get('winner'),
            'end': res.get('endReason'), 'deaths': deaths}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('replays', nargs='+')
    ap.add_argument('--side', default='both')
    ap.add_argument('--ladder', default='', help='matches.jsonl: side = the Cognoscenti seat')
    a = ap.parse_args()
    side_of = {}
    if a.ladder:
        for line in open(a.ladder):
            m = json.loads(line)
            ours = 'A' if m['a']['id'] == 351 else 'B' if m['b']['id'] == 351 else None
            if ours:
                side_of[f"m{m['id']}.replay"] = (ours, m['map'], m['a'], m['b'], m['winner'])
    out = []
    for p in a.replays:
        sides = ('A', 'B') if a.side == 'both' else (a.side,)
        meta = side_of.get(os.path.basename(p))
        if meta:
            sides = (meta[0],)
        try:
            rec = analyze(p, sides)
        except Exception as ex:
            print(f'ERR {p}: {ex}', file=sys.stderr)
            continue
        if meta:
            rec['ladder'] = {'map': meta[1], 'opp': meta[2]['name'] if meta[0] == 'B' else meta[3]['name'],
                             'ourSide': meta[0], 'matchWinner': meta[4]}
        out.append(rec)
        print(json.dumps(rec))
    agg = collections.Counter()
    mid = collections.Counter()
    for rec in out:
        for d in rec['deaths']:
            agg[d['cls']] += 1
            if 50 <= d['round'] <= 450:
                mid[d['cls']] += 1
    print(f'## deaths: {dict(agg)}  mid-game(50-450): {dict(mid)}', file=sys.stderr)


if __name__ == '__main__':
    main()
