"""Cadence forensic: per-parent birth->resplit interval + correlates.

For each dragon id, intervals between consecutive dragonSplit events with that
parentId. Per interval, on the parent's tracked head:
  (a) median toroidal-manhattan dist to nearest unconsumed pearl
  (b) fraction of rounds head sits ON a pearl bed (blocks respawn)
  (c) median ally-head count within cheb<=5
Plus: stub len after split, pre-split len at resplit, eaten/round growth rate,
censored intervals (parent dies before resplit), queen vs worker splits.

Cohorts: 'top' = both sides of top_replays; 'our' = team-351 side of
our_replays/ladder_replays; 'ouropp' = opponents of ours (mid-tier control).

Usage: python3 analysis/cadence_study.py
"""
import collections, glob, json, os, re, statistics, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../tooling'))
from parse_replay import parse  # noqa: E402
import replay_metrics as rm    # noqa: E402

META = json.load(open('/tmp/battles_meta.json'))
DIRS = [(0, -1), (1, 0), (0, 1), (-1, 0)]
ALLY_R = 5


def beds_of(map_txt):
    beds = set()
    for line in map_txt.split('\n'):
        p = line.split()
        if len(p) == 5 and p[0] == 'TILE' and int(p[4]) > 0:
            beds.add((int(p[1]), int(p[2])))
    return beds


def analyze(path, cohorts):
    """cohorts: {'a': name|'teamid', 'b': ...} mapping replay side -> cohort label."""
    r = parse(path)
    ev = r['events']
    W, H, dr, edges = rm.parse_map(r['map'])
    beds = beds_of(r['map'])

    body, team = {}, {}
    for i, (t, b) in enumerate(dr):
        team[i] = 'AB'[t]
    queen = {s: min(i for i in team if team[i] == s) for s in 'AB'}

    def tmanh(a, b):
        dx = min(abs(a[0] - b[0]), W - abs(a[0] - b[0]))
        dy = min(abs(a[1] - b[1]), H - abs(a[1] - b[1]))
        return dx + dy

    # pass 1: per-round head snapshot + pearl set + split/death events
    heads = {}          # round -> {id: (x,y)}
    lens = {}           # round -> {id: len} (approx via body sim)
    pearls = set()
    pearl_hist = {}     # round -> frozenset copy reference
    splits = []         # (round, parentId, childId, parentLenAfter, childLen)
    died = {}           # id -> round
    pos = {}            # id -> current head
    ln = {}             # id -> current len
    rnd = 0
    for e in ev:
        ty = e['type']
        if ty == 'roundStart':
            rnd = e['round']
            heads[rnd] = dict(pos)
            lens[rnd] = dict(ln)
            pearl_hist[rnd] = frozenset(pearls)
            continue
        if ty == 'dragonUpdate':
            pos[e['id']] = tuple(e['head'])
            # keep body sim: len unknown from event; track via split/death/head-tail? tail is tail CELL not len.
            continue
        if ty == 'tileChange':
            t = tuple(e['tile'])
            if e['hasPearl']:
                pearls.add(t)
            else:
                pearls.discard(t)
            continue
        if ty == 'dragonSplit':
            p, c = e['parentId'], e['childId']
            splits.append((rnd, p, c, len(e['parentBody']), len(e['childBody'])))
            team[c] = team[p]
            pos[c] = tuple(e['childBody'][0])
            pos[p] = tuple(e['parentBody'][0])
            continue
        if ty == 'dragonDeath':
            died[e['id']] = rnd
            pos.pop(e['id'], None)
            continue
    maxr = rnd

    # pass 2: per-id split lists -> intervals -> correlate
    by_id = collections.defaultdict(list)
    for (rr, p, c, plen, clen) in splits:
        by_id[p].append((rr, c, plen, clen))

    out = []
    for pid, ss in by_id.items():
        ss.sort()
        for k in range(1, len(ss)):
            r1, c1, stub1, _ = ss[k - 1]
            r2, c2, plen2, clen2 = ss[k]
            if r2 <= r1:
                continue
            ds, onb, dens, p5s, moved = [], [], [], [], 0
            prevh = None
            for rr in range(r1 + 1, r2 + 1):
                h = (heads.get(rr) or {}).get(pid)
                if h is None:
                    continue
                ps = pearl_hist.get(rr)
                dmin = min((tmanh(h, q) for q in ps), default=None)
                if dmin is not None:
                    ds.append(dmin)
                onb.append(1 if h in beds else 0)
                my = team[pid]
                n, p5 = 0, 0
                for q in ps:
                    if max(min(abs(q[0]-h[0]), W-abs(q[0]-h[0])),
                           min(abs(q[1]-h[1]), H-abs(q[1]-h[1]))) <= ALLY_R:
                        p5 += 1
                for j, hj in heads[rr].items():
                    if j != pid and team.get(j) == my and \
                            max(min(abs(hj[0]-h[0]), W-abs(hj[0]-h[0])),
                                min(abs(hj[1]-h[1]), H-abs(hj[1]-h[1]))) <= ALLY_R:
                        n += 1
                dens.append(n)
                p5s.append(p5)
                if prevh is not None and h != prevh:
                    moved += 1
                prevh = h
            out.append({
                'team': team[pid], 'pid': pid, 'r1': r1, 'r2': r2, 'iv': r2 - r1,
                'queen': pid == queen[team[pid]],
                'stubAfter': stub1, 'lenAtResplit': plen2 + clen2, 'shed': clen2,
                'growth': (plen2 + clen2 - stub1) / (r2 - r1),
                'dFood': statistics.median(ds) if ds else None,
                'onBed': sum(onb) / len(onb) if onb else None,
                'allyDens': statistics.median(dens) if dens else None,
                'p5': statistics.median(p5s) if p5s else None,
                'moveFrac': moved / max(1, len(p5s)),
            })
        # censored: last split -> death/end
        last_r, _, last_stub, _ = ss[-1]
        end = died.get(pid, maxr)
        if end > last_r + 4:
            out.append({'team': team[pid], 'pid': pid, 'r1': last_r, 'r2': end,
                        'iv': end - last_r, 'censored': True, 'queen': pid == queen[team[pid]],
                        'stubAfter': last_stub, 'deathRound': died.get(pid)})

    # birth->first-split for child ids
    first = {}
    for (rr, p, c, plen, clen) in splits:
        first.setdefault(c, rr)
    births = []  # (round, id, team, len)
    for (rr, p, c, plen, clen) in splits:
        births.append((rr, c, clen))
    for (rr, c, clen) in births:
        if c in by_id:
            iv = by_id[c][0][0] - rr
            if iv > 0:
                out.append({'team': team[c], 'pid': c, 'r1': rr, 'r2': by_id[c][0][0],
                            'iv': iv, 'birthIv': True, 'queen': False,
                            'birthLen': clen, 'lenAtResplit': by_id[c][0][2] + by_id[c][0][3]})

    # attach cohort labels
    for o in out:
        o['cohort'] = cohorts.get(o['team'], '?')
    return out


def agg(rows, key, label=''):
    iv = [r['iv'] for r in rows if not r.get('censored')]
    if not iv:
        return f'  {label:<22} n=0'
    d = [r['dFood'] for r in rows if r.get('dFood') is not None and not r.get('censored')]
    b = [r['onBed'] for r in rows if r.get('onBed') is not None and not r.get('censored')]
    a = [r['allyDens'] for r in rows if r.get('allyDens') is not None and not r.get('censored')]
    g = [r['growth'] for r in rows if r.get('growth') is not None and not r.get('censored')]
    return (f'  {label:<22} n={len(iv):<4} iv med={statistics.median(iv):>4} mean={statistics.mean(iv):5.1f} '
            f'p25={sorted(iv)[len(iv)//4]:>3} p75={sorted(iv)[3*len(iv)//4]:>3} | '
            f'dFood med={statistics.median(d) if d else -1:>4} onBed={statistics.mean(b) if b else 0:.2f} '
            f'ally={statistics.median(a) if a else -1:>4} grow={statistics.mean(g) if g else 0:.3f}/r')


def main():
    files = []
    for f in sorted(glob.glob('top_replays/*.replay')):
        mid = re.search(r'm(\d+)', f).group(1)
        v = META[mid]
        files.append((f, {'A': 'top', 'B': 'top'}))
    for f in sorted(glob.glob('our_replays/*.replay')) + sorted(glob.glob('ladder_replays/*.replay')):
        mid = re.search(r'm(\d+)', f).group(1)
        v = META[mid]
        if v.get('a') == 351:
            files.append((f, {'A': 'our', 'B': 'ouropp'}))
        elif v.get('b') == 351:
            files.append((f, {'A': 'ouropp', 'B': 'our'}))
        else:
            files.append((f, {'A': '?', 'B': '?'}))

    allrows = []
    for i, (f, co) in enumerate(files):
        try:
            rows = analyze(f, co)
            for r_ in rows:
                r_['file'] = os.path.basename(f)
            allrows += rows
        except Exception as ex:
            print(f, 'FAIL', repr(ex)[:120])
        if i % 30 == 0:
            print(f'... {i}', file=sys.stderr)
    json.dump(allrows, open('/tmp/cadence_rows.json', 'w'))

    print(f'total intervals: {sum(1 for r in allrows if not r.get("censored") and not r.get("birthIv"))}, '
          f'censored: {sum(1 for r in allrows if r.get("censored"))}, '
          f'birth->first: {sum(1 for r in allrows if r.get("birthIv"))}')

    print('\n== RESPLIT intervals by cohort (all parents) ==')
    for co in ('top', 'our', 'ouropp'):
        print(agg([r for r in allrows if r['cohort'] == co], None, co))

    print('\n== RESPLIT intervals, queens excluded ==')
    for co in ('top', 'our', 'ouropp'):
        print(agg([r for r in allrows if r['cohort'] == co and not r['queen']], None, co))

    print('\n== queens only ==')
    for co in ('top', 'our', 'ouropp'):
        print(agg([r for r in allrows if r['cohort'] == co and r['queen']], None, co))

    print('\n== birth->first-split intervals ==')
    for co in ('top', 'our', 'ouropp'):
        bi = [r['iv'] for r in allrows if r['cohort'] == co and r.get('birthIv')]
        if bi:
            print(f'  {co:<22} n={len(bi)} med={statistics.median(bi)} mean={statistics.mean(bi):.1f}')

    print('\n== censored (split -> died/end without resplit) ==')
    for co in ('top', 'our', 'ouropp'):
        cz = [r for r in allrows if r['cohort'] == co and r.get('censored')]
        dth = [r for r in cz if r.get('deathRound') is not None]
        if cz:
            surv = [r['iv'] for r in cz]
            print(f'  {co:<22} censored={len(cz)} died={len(dth)} '
                  f'medWait={statistics.median(surv)} deathShare={len(dth)/len(cz):.2f}')

    # correlate: which factor separates fast vs slow within cohort
    print('\n== within-cohort: interval vs dFood bucket ==')
    for co in ('top', 'our'):
        rows = [r for r in allrows if r['cohort'] == co and r.get('dFood') is not None and not r.get('censored')]
        for lo, hi in ((0, 2), (2, 4), (4, 7), (7, 12), (12, 99)):
            sel = [r for r in rows if lo <= r['dFood'] < hi]
            if len(sel) >= 8:
                print(f'  {co} dFood[{lo},{hi}): n={len(sel):<4} iv med={statistics.median(r["iv"] for r in sel)}')

    print('\n== within-cohort: interval vs onBed ==')
    for co in ('top', 'our'):
        rows = [r for r in allrows if r['cohort'] == co and r.get('onBed') is not None and not r.get('censored')]
        for lo, hi in ((0, 0.05), (0.05, 0.3), (0.3, 1.01)):
            sel = [r for r in rows if lo <= r['onBed'] < hi]
            if len(sel) >= 8:
                print(f'  {co} onBed[{lo},{hi}): n={len(sel):<4} iv med={statistics.median(r["iv"] for r in sel)}')

    print('\n== within-cohort: interval vs ally density ==')
    for co in ('top', 'our'):
        rows = [r for r in allrows if r['cohort'] == co and r.get('allyDens') is not None and not r.get('censored')]
        for lo, hi in ((0, 1), (1, 3), (3, 6), (6, 30)):
            sel = [r for r in rows if lo <= r['allyDens'] < hi]
            if len(sel) >= 8:
                print(f'  {co} ally[{lo},{hi}): n={len(sel):<4} iv med={statistics.median(r["iv"] for r in sel)}')


if __name__ == '__main__':
    main()
