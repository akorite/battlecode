"""Sonar-gossip forensics v2 — per-side normalized analysis.

Side-level: each (replay, side) is a sample, classified 'gossip' when its
pings/alive-dragon-round rate is high. Metrics:
 Q1 ping rate over rounds (alive-conditioned), burstiness vs army size,
    rate near split/death rounds vs baseline.
 Q2 receiver pull: after a dragon RECEIVES an ally ping, does its dist-to-food
    drop faster than non-receivers' over 10r? And post-burst swarm spread.
 Q3 spatial clustering of ping origins.
"""
import collections, glob, json, os, re, statistics, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../tooling'))
from parse_replay import parse  # noqa: E402
import replay_metrics as rm    # noqa: E402

META = json.load(open('/tmp/battles_meta_sonar.json'))
D = {'N': (0, -1), 'E': (1, 0), 'S': (0, 1), 'W': (-1, 0)}


def analyze(path):
    mid = int(re.search(r'm(\d+)', path).group(1))
    meta = META[str(mid)]
    r = parse(path)
    ev = r['events']
    W, H, dr, edges = rm.parse_map(r['map'])
    team = {i: 'AB'[t] for i, (t, b) in enumerate(dr)}
    queen = {s: min(i for i in team if team[i] == s) for s in 'AB'}

    rnd = 0
    pos = {}
    heads = {}
    alive = collections.defaultdict(lambda: collections.Counter())
    pearls = set()
    pearl_h = {}
    pings = collections.defaultdict(list)          # rnd -> [(side, sender, origin, hitId, hitKind, value, dir)]
    events_r = collections.defaultdict(list)
    side_round_alive = collections.defaultdict(set)  # rnd -> {side heads ids}
    for e in ev:
        if not isinstance(e, dict):
            continue
        ty = e['type']
        if ty == 'roundStart':
            rnd = e['round']
            heads[rnd] = dict(pos)
            pearl_h[rnd] = frozenset(pearls)
            for i in pos:
                side_round_alive[rnd].add(i)
        elif ty == 'dragonUpdate':
            pos[e['id']] = tuple(e['head'])
        elif ty == 'tileChange':
            t = tuple(e['tile'])
            if e['hasPearl']:
                pearls.add(t)
            else:
                pearls.discard(t)
        elif ty == 'dragonSplit':
            team[e['childId']] = e['team']
            pos[e['childId']] = tuple(e['childBody'][0])
            pos[e['parentId']] = tuple(e['parentBody'][0])
            events_r[rnd].append('split')
        elif ty == 'dragonDeath':
            pos.pop(e['id'], None)
            events_r[rnd].append('death')
        elif ty == 'sonarPing':
            s = team.get(e['senderId'])
            if s is None:
                continue
            pings[rnd].append((s, e['senderId'], tuple(e['origin']), e.get('hitId'),
                               e['hitKind'], e.get('value'), e['direction']))
    maxr = rnd

    def tmanh(a, b):
        return min(abs(a[0]-b[0]), W-abs(a[0]-b[0])) + min(abs(a[1]-b[1]), H-abs(a[1]-b[1]))

    sides = {}
    for s in 'AB':
        tid = meta[s.lower()]
        rounds_alive = [rr for rr in range(1, maxr+1)
                        if any(team.get(i) == s for i in heads.get(rr, {}))]
        np = sum(1 for rr in pings for p in pings[rr] if p[0] == s)
        rate_num = sum(len(pings[rr]) and 1 for rr in pings)  # unused
        # ping rate per alive dragon
        rates = []
        for rr in rounds_alive:
            n_al = sum(1 for i in heads[rr] if team.get(i) == s)
            n_p = sum(1 for p in pings.get(rr, ()) if p[0] == s)
            if n_al:
                rates.append(n_p / n_al)
        senders = {p[1] for rr in pings for p in pings[rr] if p[0] == s}
        n_alive_units = len({i for rr in rounds_alive for i in heads[rr] if team.get(i) == s})
        origins = collections.Counter(p[2] for rr in pings for p in pings[rr] if p[0] == s)
        hits = collections.Counter(p[4] for rr in pings for p in pings[rr] if p[0] == s)
        vals = collections.Counter(p[5] for rr in pings for p in pings[rr] if p[0] == s)
        v_senders = collections.defaultdict(set)
        for rr in pings:
            for p in pings[rr]:
                if p[0] == s:
                    v_senders[p[5]].add(p[1])
        dirs = collections.Counter(p[6] for rr in pings for p in pings[rr] if p[0] == s)
        # queen vs worker ping share
        qp = sum(1 for rr in pings for p in pings[rr] if p[0] == s and p[1] == queen[s])

        # Q2: receivers (ally hits only) -> dFood delta over +10r vs non-receivers
        drecv, dctrl = [], []
        for rr in range(1, maxr - 9):
            hits_r = {p[3] for p in pings.get(rr, ()) if p[0] == s and p[3] is not None
                      and p[4] in ('ally', 'allyHead') and team.get(p[3]) == s}
            if not hits_r:
                continue
            ps0 = pearl_h.get(rr, ())
            ps1 = pearl_h.get(rr + 10, ())
            for i in (heads.get(rr) or {}):
                if team.get(i) != s:
                    continue
                h0 = heads[rr][i]
                h1 = heads.get(rr + 10, {}).get(i)
                if h1 is None or not ps0 or not ps1:
                    continue
                d0 = min(tmanh(h0, q) for q in ps0)
                d1 = min(tmanh(h1, q) for q in ps1)
                (drecv if i in hits_r else dctrl).append(d1 - d0)
        sides[s] = {
            'tid': tid, 'name': meta[s.lower() + 'Name'], 'pings': np,
            'rounds_alive': len(rounds_alive),
            'rate_med': statistics.median(rates) if rates else 0,
            'rate_mean': statistics.mean(rates) if rates else 0,
            'rate_cv': (statistics.stdev(rates) / statistics.mean(rates)) if rates and statistics.mean(rates) else 0,
            'senders': len(senders), 'alive_ever': n_alive_units,
            'coverage': len(senders) / max(1, n_alive_units),
            'origins': sorted(origins.values(), reverse=True),
            'hits': dict(hits), 'distinct_vals': len(vals),
            'top_val': vals.most_common(1)[0][1] if vals else 0,
            'relayed': sum(1 for v, ss in v_senders.items() if len(ss) >= 3),
            'dirs': dict(dirs), 'queen_ping_share': qp / max(1, np),
            'drecv': (statistics.mean(drecv), len(drecv)) if drecv else None,
            'dctrl': (statistics.mean(dctrl), len(dctrl)) if dctrl else None,
        }
        # near-event rate (per alive dragon) within 2r of splits/deaths
        evs = set()
        for rr, es in events_r.items():
            if any(e in ('split', 'death') for e in es):
                evs.update(range(rr - 1, rr + 3))
        near, far = [], []
        for rr in rounds_alive:
            n_al = sum(1 for i in heads[rr] if team.get(i) == s)
            if not n_al:
                continue
            rate = sum(1 for p in pings.get(rr, ()) if p[0] == s) / n_al
            (near if rr in evs else far).append(rate)
        sides[s]['rate_near'] = statistics.mean(near) if near else 0
        sides[s]['rate_far'] = statistics.mean(far) if far else 0
        # intra-round sender distinctness: pings/sender/round cap check
        sides[s]['ppr'] = np / max(1, len(rounds_alive))
    return {'mid': mid, 'map': re.search(r'MAP_NAME (\S+)', r['map']).group(1) if 'MAP_NAME' in r['map'] else '?',
            'rounds': maxr, 'sides': sides, 'result': r.get('result')}


def main():
    files = sorted(glob.glob('ciallo_replays/*.replay')) + sorted(glob.glob('cursey_replays/*.replay'))
    games = []
    for i, f in enumerate(files):
        try:
            games.append(analyze(f))
        except Exception as ex:
            print(f, 'FAIL', repr(ex)[:120])
        if i % 10 == 0:
            print('...', i, file=sys.stderr)

    sides = []
    for gm in games:
        for s in 'AB':
            d = dict(gm['sides'][s])
            d['mid'] = gm['mid']; d['map'] = gm['map']
            d['won'] = gm['result'].get('winner', '').lower() == s.lower()
            sides.append(d)
    sides.sort(key=lambda x: -x['rate_med'])
    print(f'{"team":<28} {"map":<14} {"pings":>6} {"rate":>6} {"cv":>5} {"cov":>5} {"send":>5} {"qshr":>5} {"dRecv":>7} {"dCtrl":>7} {"won":>4}')
    for d in sides:
        dr = f"{d['drecv'][0]:+.2f}" if d['drecv'] else '  -'
        dc = f"{d['dctrl'][0]:+.2f}" if d['dctrl'] else '  -'
        print(f"{d['name'][:27]:<28} {d['map'][:13]:<14} {d['pings']:>6} {d['rate_med']:>6.2f} {d['rate_cv']:>5.2f} "
              f"{d['coverage']:>5.2f} {d['senders']:>5} {d['queen_ping_share']:>5.2f} {dr:>7} {dc:>7} {str(d['won'])[:1]:>4}")

    gos = [d for d in sides if d['rate_med'] >= 1.5 and d['pings'] > 5000]
    quiet = [d for d in sides if d['rate_med'] < 0.5 and d['pings'] > 300]
    print(f'\ngossip sides (rate>=1.5, pings>5k): {len(gos)} | quiet sides (<0.5): {len(quiet)}')
    print('gossip teams:', sorted({(d['tid'], d['name']) for d in gos}))
    print('quiet teams:', sorted({(d['tid'], d['name']) for d in quiet}))

    for grp, name in ((gos, 'GOSSIP'), (quiet, 'QUIET')):
        if not grp:
            continue
        print(f'\n== {name} aggregate ==')
        print(f'  rate med={statistics.median(d["rate_med"] for d in grp):.2f} '
              f'cv={statistics.median(d["rate_cv"] for d in grp):.2f} '
              f'coverage={statistics.median(d["coverage"] for d in grp):.2f} '
              f'queen share={statistics.median(d["queen_ping_share"] for d in grp):.3f}')
        print(f'  rate near split/death rounds={statistics.mean(d["rate_near"] for d in grp):.2f} '
              f'vs baseline={statistics.mean(d["rate_far"] for d in grp):.2f}')
        dr = [d['drecv'][0] for d in grp if d['drecv']]
        dc = [d['dctrl'][0] for d in grp if d['dctrl']]
        print(f'  dFood(+10r) receivers={statistics.mean(dr):+.2f} vs non-receivers={statistics.mean(dc):+.2f}')
        t5 = [sum(d['origins'][:5]) / sum(d['origins']) for d in grp if d['origins']]
        print(f'  top-5 origin-cell share={statistics.mean(t5):.3f}')
        hits = collections.Counter()
        for d in grp:
            hits.update(d['hits'])
        t = sum(hits.values())
        print('  hitKind:', ' '.join(f'{k}={v/t:.2f}' for k, v in hits.most_common()))
        print(f'  distinct vals/game med={statistics.median(d["distinct_vals"] for d in grp)} '
              f'top-val repeat med={statistics.median(d["top_val"] for d in grp)} '
              f'relayed(>=3 senders) med={statistics.median(d["relayed"] for d in grp)}')
        w = sum(1 for d in grp if d['won'])
        print(f'  win share={w}/{len(grp)}')


if __name__ == '__main__':
    main()
