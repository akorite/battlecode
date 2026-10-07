"""Suicide geography: per noValidAction death, geometry at the death round.

(a) cheb to LONGEST same-team dragon's head (excl. victim unless it is longest)
(b) cheb to nearest pearl-bed cell (cells that ever show hasPearl in tileChange)
(c) ally head density within cheb-4 of the death cell
(d) dead unit's length
+ queen head dist (consumer check)

Boards wrap (torus cheb). Winner from result.winner.
"""
import sys, os, glob, json, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
from parse_replay import parse
from pocket_metric import parse_map


def tcheb(W, H, a, b):
    dx = abs(a[0] - b[0]); dy = abs(a[1] - b[1])
    return max(min(dx, W - dx), min(dy, H - dy))


def analyze(path, us_side=None):
    r = parse(path)
    W, H, dr, _ = parse_map(r['map'])
    team = {i: 'AB'[t] for i, (t, _b) in enumerate(dr)}
    body = {}
    heads = {}
    rnd = 0
    winner = (r.get('result') or {}).get('winner')
    pearls = set()   # live pearl cells at the current instant
    out = []
    for e in r['events']:
        ty = e['type']
        if ty == 'roundStart':
            rnd += 1
        elif ty == 'tileChange':
            t = tuple(e['tile'])
            (pearls.add if e.get('hasPearl') else pearls.discard)(t)
        elif ty == 'dragonUpdate':
            i = e['id']
            if i not in body:
                body[i] = collections.deque()
            b = body[i]; h, tl = tuple(e['head']), tuple(e['tail'])
            if not b or b[0] != h:
                b.appendleft(h)
            while len(b) > 1 and b[-1] != tl:
                b.pop()
            heads[i] = h
        elif ty == 'dragonSplit':
            body[e['parentId']] = collections.deque(tuple(x) for x in e['parentBody'])
            body[e['childId']] = collections.deque(tuple(x) for x in e['childBody'])
            team[e['childId']] = e['team']
            heads[e['parentId']] = tuple(e['parentBody'][0])
            heads[e['childId']] = tuple(e['childBody'][0])
        elif ty == 'dragonDeath' and e['reason'] == 'noValidAction':
            i = e['id']; s = team.get(i)
            if s is None or i not in body:
                body.pop(i, None); heads.pop(i, None)
                continue
            b = list(body[i]); h = heads.get(i)
            if h is None:
                body.pop(i, None); heads.pop(i, None)
                continue
            # longest ally dragon (by current body length) and its head
            longest_id, longest_len = -1, -1
            for j, bj in body.items():
                if team.get(j) != s or j == i:
                    continue
                if len(bj) > longest_len:
                    longest_len, longest_id = len(bj), j
            d_long = (tcheb(W, H, h, heads[longest_id])
                      if longest_id >= 0 else None)
            # queen head (id 0=A,1=B) alive?
            qid = 0 if s == 'A' else 1
            d_queen = (tcheb(W, H, h, heads[qid])
                       if qid in heads and qid in body else None)
            d_bed = min((tcheb(W, H, h, c) for c in pearls), default=None)
            ally4 = sum(1 for j, hh in heads.items()
                        if j != i and team.get(j) == s and tcheb(W, H, h, hh) <= 4)
            out.append({'file': os.path.basename(path), 'round': rnd, 'side': s,
                        'winner_side': winner, 'won': s == winner,
                        'us': (s == us_side) if us_side else None,
                        'len': len(b), 'd_long': d_long, 'd_queen': d_queen,
                        'd_bed': d_bed, 'ally4': ally4,
                        'is_longest': len(b) >= longest_len})
            body.pop(i, None); heads.pop(i, None)
        elif ty == 'dragonDeath':
            i = e['id']; body.pop(i, None); heads.pop(i, None)
    return out


if __name__ == '__main__':
    dirs = sys.argv[1:]
    recs = []
    for a in dirs:
        fs = sorted(glob.glob(os.path.join(a, '*.replay'))) if os.path.isdir(a) else [a]
        for f in fs:
            try:
                recs += analyze(f)
            except Exception as ex:
                print('ERR', f, ex, file=sys.stderr)
    for x in recs:
        print(json.dumps(x))
