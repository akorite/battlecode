"""Parked-unit census: fraction of each team's units stationary vs moving.

Per dragon: head each round (dragonUpdate/split; carry-forward when silent).
'Parked' at round r: every head in the trailing window [r-9, r] lies within
cheb-2 of the head at r-9 (fixed anchor). Natural pearl beds = cells with
>=3 hasPearl tileChange events. Torus cheb.

Per game per side: parked fraction per 25-round bin, parked units' cheb to
nearest bed, adjacent-to-bed share (<=1), winner flag. On 500-round games.
"""
import sys, os, glob, json, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
from parse_replay import parse
from pocket_metric import parse_map


def tcheb(W, H, a, b):
    dx = abs(a[0] - b[0]); dy = abs(a[1] - b[1])
    return max(min(dx, W - dx), min(dy, H - dy))


def analyze(path):
    r = parse(path)
    res = r.get('result') or {}
    rnd_events = [e for e in r['events'] if e['type'] == 'roundStart']
    maxr = len(rnd_events)
    if res.get('endReason') != 'roundLimit' and maxr < 499:
        return None
    W, H, dr, _ = parse_map(r['map'])
    team = {i: 'AB'[t] for i, (t, _b) in enumerate(dr)}
    beds = set()
    beds_n = collections.Counter()
    for e in r['events']:
        if e['type'] == 'tileChange' and e.get('hasPearl'):
            beds_n[tuple(e['tile'])] += 1
    beds = {c for c, n in beds_n.items() if n >= 3}

    # per-dragon round->head observations + alive windows
    hist = collections.defaultdict(dict)   # id -> {round: head}
    born, died = {}, {}
    rnd = 0
    for e in r['events']:
        ty = e['type']
        if ty == 'roundStart':
            rnd += 1
        elif ty == 'dragonUpdate':
            i = e['id']
            born.setdefault(i, 0)
            hist[i][rnd] = tuple(e['head'])
        elif ty == 'dragonSplit':
            team[e['childId']] = e['team']
            born[e['childId']] = rnd
            hist[e['childId']][rnd] = tuple(e['childBody'][0])
            hist[e['parentId']][rnd] = tuple(e['parentBody'][0])
        elif ty == 'dragonDeath':
            died[e['id']] = rnd

    # per-dragon head series indexed by round (carry-forward; None pre-spawn)
    harr = {}
    for i, h in hist.items():
        arr = [None] * (maxr + 1)
        last = None
        for rr in range(1, maxr + 1):
            if rr in h:
                last = h[rr]
            arr[rr] = last
        harr[i] = arr
    def head_at(i, rr):
        return harr[i][rr] if 0 <= rr <= maxr else None

    out = {'file': os.path.basename(path), 'winner': res.get('winner'),
           'sides': {}}
    for side in 'AB':
        ids = [i for i, t in team.items() if t == side]
        parked_frac = collections.defaultdict(list)  # bin -> [frac per round]
        d_bed_all = []
        d_bed_moving = []
        adj_rounds = 0
        parked_rounds = 0
        for rr in range(1, maxr + 1):
            cur = [i for i in ids if born.get(i, 1 << 30) <= rr < died.get(i, 1 << 30)
                   and head_at(i, rr) is not None]
            if not cur:
                continue
            npk = 0
            for i in cur:
                anch = head_at(i, rr - 9)
                if anch is None:
                    continue  # not yet 10 rounds old
                h = head_at(i, rr)
                ok = True
                for k in range(rr - 9, rr + 1):
                    hk = head_at(i, k)
                    if hk is None or tcheb(W, H, hk, anch) > 2:
                        ok = False; break
                if ok:
                    npk += 1
                    if beds:
                        d = min(tcheb(W, H, h, c) for c in beds)
                        d_bed_all.append(d)
                        adj_rounds += (d <= 1)
                    parked_rounds += 1
                elif beds:
                    d_bed_moving.append(min(tcheb(W, H, h, c) for c in beds))
            parked_frac[(rr - 1) // 25].append(npk / len(cur))
        out['sides'][side] = {
            'n_units_rounds': sum(len(v) for v in parked_frac.values()),
            'parked_frac': {b: round(sum(v) / len(v), 3) for b, v in parked_frac.items()},
            'parked_rounds': parked_rounds,
            'd_bed_med': (sorted(d_bed_all)[len(d_bed_all) // 2] if d_bed_all else None),
            'd_bed_moving_med': (sorted(d_bed_moving)[len(d_bed_moving) // 2] if d_bed_moving else None),
            'adj_share': (round(adj_rounds / parked_rounds, 3) if parked_rounds else None),
            'adj_share_moving': (round(sum(1 for d in d_bed_moving if d <= 1) / len(d_bed_moving), 3) if d_bed_moving else None),
        }
    return out


if __name__ == '__main__':
    for a in sys.argv[1:]:
        fs = sorted(glob.glob(os.path.join(a, '*.replay'))) if os.path.isdir(a) else [a]
        for f in fs:
            try:
                x = analyze(f)
                if x:
                    print(json.dumps(x))
            except Exception as ex:
                print('ERR', f, ex, file=sys.stderr)
