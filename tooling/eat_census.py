"""Intake-side census: pearls eaten per unit-round + starvation share.

Eats: tileChange hasPearl->False attributed to the unit whose carried-forward
head is nearest the cell (validated: 96.5% d0, 3% d1 same-round ordering;
d>1 events ignored as noise ~0.4%).

Per side per game:
  eaten / unit_rounds (full game), eaten120 / ur120 (r0-120 ramp),
  starve@60/@120 = share of alive units whose last attributed eat (or birth)
  was >10 rounds ago.
Tag: 'ours' (team 351), 'top' (top-10 ids), 'opp' (everyone else).
"""
import sys, os, glob, json, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
from parse_replay import parse
from pocket_metric import parse_map

TOP = {454, 157, 306, 545, 70, 55, 264, 213, 552, 91}
OURS = 351


def tcheb(W, H, a, b):
    dx = abs(a[0] - b[0]); dy = abs(a[1] - b[1])
    return max(min(dx, W - dx), min(dy, H - dy))


def analyze(path, meta):
    r = parse(path)
    res = r.get('result') or {}
    W, H, dr, _ = parse_map(r['map'])
    team = {i: 'AB'[t] for i, (t, _b) in enumerate(dr)}
    hist = collections.defaultdict(dict)
    born, died = {}, {}
    rnd = 0
    removals = []  # (round, cell)
    for e in r['events']:
        ty = e['type']
        if ty == 'roundStart':
            rnd += 1
        elif ty == 'dragonUpdate':
            born.setdefault(e['id'], 0)
            hist[e['id']][rnd] = tuple(e['head'])
        elif ty == 'dragonSplit':
            team[e['childId']] = e['team']
            born[e['childId']] = rnd
            hist[e['childId']][rnd] = tuple(e['childBody'][0])
            hist[e['parentId']][rnd] = tuple(e['parentBody'][0])
        elif ty == 'dragonDeath':
            died[e['id']] = rnd
        elif ty == 'tileChange' and e.get('hasPearl') is False:
            removals.append((rnd, tuple(e['tile'])))
    maxr = rnd
    harr = {}
    for i, h in hist.items():
        arr = [None] * (maxr + 1)
        last = None
        for rr in range(1, maxr + 1):
            if rr in h:
                last = h[rr]
            arr[rr] = last
        harr[i] = arr

    # single attribution pass: removal -> nearest alive unit (d<=1)
    unit_eats = collections.defaultdict(list)
    unatt = 0
    alive_ids = list(hist.keys())
    for rr, c in removals:
        best = None; bd = 99
        for i in alive_ids:
            if not (born.get(i, 1 << 30) <= rr < died.get(i, 1 << 30)):
                continue
            h = harr[i][rr]
            if h is None:
                continue
            d = tcheb(W, H, h, c)
            if d < bd:
                bd = d; best = i
        if bd <= 1:
            unit_eats[best].append(rr)
        else:
            unatt += 1

    out = []
    for side in 'AB':
        tid = meta.get('a' if side == 'A' else 'b')
        ids = set(i for i, t in team.items() if t == side)
        ur_tot = 0; ur120 = 0
        for rr in range(1, maxr + 1):
            n = sum(1 for i in ids if born.get(i, 1 << 30) <= rr < died.get(i, 1 << 30))
            ur_tot += n
            if rr <= 120:
                ur120 += n
        tot_eat = sum(len(unit_eats.get(i, ())) for i in ids)
        eat120 = sum(1 for i in ids for rr in unit_eats.get(i, ()) if rr <= 120)

        def starve_at(rr):
            alive = [i for i in ids if born.get(i, 1 << 30) <= rr < died.get(i, 1 << 30)]
            if not alive:
                return None
            st = 0
            for i in alive:
                le = max((e for e in unit_eats.get(i, ()) if e <= rr), default=0)
                ref = le if le else born.get(i, 0)
                if rr - ref > 10:
                    st += 1
            return [round(st / len(alive), 3), len(alive)]

        s60 = starve_at(60) if maxr >= 60 else None
        s120 = starve_at(120) if maxr >= 120 else None
        tag = 'ours' if tid == OURS else ('top' if tid in TOP else 'opp')
        out.append({
            'match': meta.get('id'), 'team_id': tid, 'tag': tag, 'side': side,
            'won': res.get('winner') == side, 'map': meta.get('map'),
            'rounds': maxr,
            'eaten': tot_eat, 'urounds': ur_tot,
            'eff': round(tot_eat / ur_tot, 4) if ur_tot else None,
            'eaten120': eat120, 'ur120': ur120,
            'eff120': round(eat120 / ur120, 4) if ur120 else None,
            'starve60': s60, 'starve120': s120, 'unatt': unatt,
        })
    return out


if __name__ == '__main__':
    meta = json.load(open('/tmp/eat_manifest.json'))
    seen = set()
    fs = sorted(glob.glob('/tmp/topr/*/m*.replay') + glob.glob('/tmp/ours/*.replay'))
    for f in fs:
        mid = os.path.basename(f)[1:].split('.')[0]
        if mid in seen or mid not in meta:
            continue
        seen.add(mid)
        m = dict(meta[mid]); m['id'] = mid
        try:
            for row in analyze(f, m):
                print(json.dumps(row))
        except Exception as ex:
            print('ERR', f, ex, file=sys.stderr)
