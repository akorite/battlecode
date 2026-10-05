"""Queen/champ trajectory at r50/200/400 from a .replay file.

Usage: python3 tooling/traj.py <replay> [...]
Prints one JSON line per replay: per-side marks.
"""
import collections, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
from parse_replay import parse

MARKS = (50, 200, 400)

def parse_map(txt):
    dr = []
    for line in txt.split('\n'):
        p = line.split()
        if p and p[0] == 'DRAGON':
            t, n = int(p[1]), int(p[2])
            c = list(map(int, p[3:3 + 2 * n]))
            dr.append((t, [(c[i], c[i + 1]) for i in range(0, 2 * n, 2)]))
    return dr

def main(path):
    r = parse(path)
    ev = r['events']
    dr = parse_map(r['map'])
    body, team = {}, {}
    for e in ev:
        if e['type'] == 'roundStart':
            break
        if e['type'] == 'dragonUpdate' and e['id'] < len(dr):
            t, b = dr[e['id']]
            body[e['id']] = collections.deque(tuple(x) for x in b)
            team[e['id']] = 'AB'[t]
    queen = {s: min((i for i in team if team[i] == s), default=-1) for s in 'AB'}
    marks = {s: {} for s in 'AB'}
    rnd = 0
    for e in ev:
        ty = e['type']
        if ty == 'roundStart':
            rnd = e['round']
            if rnd in MARKS:
                for s in 'AB':
                    ids = [i for i in body if team.get(i) == s]
                    q = queen[s]
                    marks[s][rnd] = {
                        'qlen': len(body[q]) if q in body else 0,
                        'alive': len(ids),
                        'longest': max((len(body[i]) for i in ids), default=0),
                        'total': sum(len(body[i]) for i in ids),
                    }
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
            body.pop(e['id'], None)
    return {'file': os.path.basename(path), 'marks': marks, 'rounds': rnd}

if __name__ == '__main__':
    for p in sys.argv[1:]:
        try:
            print(json.dumps(main(p)))
        except Exception as ex:
            print(json.dumps({'file': os.path.basename(p), 'error': str(ex)}))
