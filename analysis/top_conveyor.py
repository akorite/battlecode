"""Top-team conveyor forensics (roundLimit games only).

For the winner side (loser for contrast):
 1. Eventual-longest dragon ("champ"): per-round length trace + head trace.
 2. Every teammate death: drop cells (even body indices per engine Kill()),
    dist champ-head -> nearest drop cell at death round; does champ head enter
    a drop cell within 15r (capture); does champ len grow within 10r; reason;
    dist to champ TAIL-side too.
 3. Feeder suicides = nva deaths: count/game, first/last round, era histogram.
 4. Champ roam vs plant: unique head cells + mean step dist + orbit radius
    (median-position distance), eras r300-399 / r400-500; % rounds stationary.
 5. Escorts: teammates within cheb-3 / cheb-5 of champ head per round.

Usage: python3 analysis/top_conveyor.py [glob]
"""
import collections, glob, json, os, statistics, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../tooling'))
from parse_replay import parse  # noqa: E402
import replay_metrics as rm    # noqa: E402


def tcheb(W, H):
    def f(a, b):
        dx = min(abs(a[0] - b[0]), W - abs(a[0] - b[0]))
        dy = min(abs(a[1] - b[1]), H - abs(a[1] - b[1]))
        return max(dx, dy)
    return f


def analyze(path, meta):
    r = parse(path)
    ev = r['events']
    W, H, dr, edges = rm.parse_map(r['map'])
    d = tcheb(W, H)
    team = {i: 'AB'[t] for i, (t, b) in enumerate(dr)}
    body = {i: collections.deque(tuple(x) for x in b) for i, (t, b) in enumerate(dr)}

    snaps = {}   # rnd -> {id: (head, len, body_tuple)}   — head+len+body
    heads = {}   # rnd -> {id: head}  (same info, faster capture lookups)
    bodies = {}  # rnd -> {id: body tuple}
    deaths = []  # (rnd, id, reason, team, drops tuple)
    rnd = 0
    last_r = 0

    for e in ev:
        if not isinstance(e, dict):
            continue
        ty = e['type']
        if ty == 'roundStart':
            rnd = e['round']
            last_r = max(last_r, rnd)
            heads[rnd] = {i: b[0] for i, b in body.items()}
            bodies[rnd] = {i: tuple(b) for i, b in body.items()}
            continue
        if ty == 'dragonUpdate':
            i = e['id']
            if i in body:
                b = body[i]
                h, tl = tuple(e['head']), tuple(e['tail'])
                if b[0] != h:
                    b.appendleft(h)
                    while len(b) > 1 and b[-1] != tl:
                        b.pop()
            continue
        if ty == 'dragonSplit':
            team[e['childId']] = e['team']
            body[e['parentId']] = collections.deque(tuple(x) for x in e['parentBody'])
            body[e['childId']] = collections.deque(tuple(x) for x in e['childBody'])
            continue
        if ty == 'dragonDeath':
            i = e['id']
            if i in body:
                bb = list(body[i])
                drops = tuple(bb[k] for k in range(0, len(bb), 2))
                deaths.append((rnd, i, e['reason'], team.get(i), drops))
            body.pop(i, None)

    # capture lookups need heads beyond last_r
    return {'deaths': deaths, 'heads': heads, 'bodies': bodies,
            'team': team, 'last_r': last_r, 'map': meta['map'], 'WH': (W, H),
            'a': meta['a']['name'], 'b': meta['b']['name'], 'winner': meta['winner']}


def per_side(g, side):
    """All conveyor metrics for one side of one game."""
    team, heads, bodies, deaths, last_r = g['team'], g['heads'], g['bodies'], g['deaths'], g['last_r']
    W = H = None
    d = None
    # reconstruct distance fn lazily (W,H stored in g)
    W, H = g['WH']
    d = tcheb(W, H)

    # eventual longest on this side at last_r
    end = bodies.get(last_r, {})
    end_ids = [i for i in end if team[i] == side]
    if not end_ids:
        return None
    champ = max(end_ids, key=lambda i: len(end[i]))
    champ_len_at_end = len(end[champ])

    # champ trace: rounds where champ alive
    trace = [(rr, len(bodies[rr][champ]), bodies[rr][champ][0])
             for rr in sorted(bodies) if champ in bodies[rr]]

    # roam metrics per era on champ head
    def era_stats(lo, hi):
        hs = [h for rr, L, h in trace if lo <= rr < hi]
        if len(hs) < 10:
            return None
        steps = [d(hs[k], hs[k + 1]) for k in range(len(hs) - 1)]
        mx = statistics.median(h[0] for h in hs)
        my = statistics.median(h[1] for h in hs)
        orbit = statistics.mean(d(h, (mx, my)) for h in hs)
        return {'uniq': len(set(hs)), 'step': statistics.mean(steps),
                'still': sum(1 for s in steps if s == 0) / len(steps), 'orbit': orbit}
    roam = {e: era_stats(lo, hi) for e, (lo, hi) in
            {'mid': (200, 300), 'feed': (300, 400), 'bell': (400, last_r + 1)}.items()}

    # escorts per round
    esc3, esc5 = collections.defaultdict(list), collections.defaultdict(list)
    for rr, L, ch in trace:
        mates = [i for i in heads.get(rr, {}) if i != champ and team[i] == side]
        n3 = sum(1 for i in mates if d(heads[rr][i], ch) <= 3)
        n5 = sum(1 for i in mates if d(heads[rr][i], ch) <= 5)
        esc3[rr].append(n3); esc5[rr].append(n5)

    # feeder deaths: all deaths of this side, geometry vs champ
    fed = []
    for (rr, i, reason, s, drops) in deaths:
        if s != side or i == champ or not drops:
            continue
        # champ head position at death round (may not exist if champ born later)
        ch = bodies.get(rr, {}).get(champ, (None,))[0] if champ in bodies.get(rr, {}) else None
        dd = None
        if ch:
            dd = min(d(c, ch) for c in drops)
        # capture: champ head enters a drop cell within 15r
        captured_by_champ = False
        captured_by_mate = False
        for rr2 in range(rr, min(rr + 16, last_r + 1)):
            hh = heads.get(rr2, {})
            if champ in hh and hh[champ] in drops:
                captured_by_champ = True
            if any(j != i and team[j] == side and hh[j] in drops for j in hh):
                captured_by_mate = True
            if captured_by_champ:
                break
        grew = False
        if champ in bodies.get(rr, {}):
            l0 = len(bodies[rr][champ])
            for rr2 in range(rr, min(rr + 11, last_r + 1)):
                if champ in bodies.get(rr2, {}) and len(bodies[rr2][champ]) > l0:
                    grew = True
                    break
        fed.append({'rnd': rr, 'reason': reason, 'd': dd, 'len': len(drops) * 2 - 1,
                    'capChamp': captured_by_champ, 'capMate': captured_by_mate, 'grew': grew})

    return {'champ': champ, 'end_len': champ_len_at_end, 'trace': trace,
            'roam': roam, 'fed': fed, 'esc3': esc3, 'esc5': esc5}


def main():
    games = []
    for f in sorted(glob.glob(sys.argv[1] if len(sys.argv) > 1 else 'toptop_replays/*.replay')):
        meta = json.load(open(f.replace('.replay', '.json')))
        try:
            g = analyze(f, meta)
            games.append(g)
        except Exception as ex:
            print(f, 'FAIL', repr(ex)[:120])

    rl = [g for g in games if g['last_r'] >= 490]
    print(f'games={len(games)} roundLimit={len(rl)}')

    print('\n== champ end length + growth trace (winner side) ==')
    alltr = []
    for g in rl:
        side = g['winner'].upper()
        ps = per_side(g, side)
        if not ps:
            continue
        alltr.append((g, side, ps))
        tr = ps['trace']
        # length at era boundaries
        def lat(rr):
            xs = [L for r_, L, h in tr if r_ <= rr]
            return xs[-1] if xs else None
        print(f"  {g['map']:<14} {g['a']} v {g['b']} w:{side} | champ id{ps['champ']} endLen={ps['end_len']} "
              f"L@200={lat(200)} L@300={lat(300)} L@400={lat(400)} L@end={lat(g['last_r'])} "
              f"born_r{tr[0][0]}")

    print('\n== feeder deaths per game (winner side) — count, timing, d-to-champ-head, capture ==')
    agg = collections.defaultdict(list)
    for g, side, ps in alltr:
        fed = ps['fed']
        nva = [f for f in fed if f['reason'] == 'noValidAction']
        agg['nva_ct'].append(len(nva))
        close = [f for f in nva if f['d'] is not None and f['d'] <= 12]
        agg['nva_close'].append(len(close))
        cap_c = [f['capChamp'] for f in close]
        cap_m = [f['capMate'] for f in close]
        grew = [f['grew'] for f in close]
        if close:
            print(f"  {g['map']:<14} w:{side} nva={len(nva)} within12={len(close)} "
                  f"capByChamp={sum(cap_c)}/{len(close)} capByMate={sum(cap_m)}/{len(close)} champGrew={sum(grew)}/{len(close)}")

    def stat(name, vals):
        v = list(vals)
        return f"{name}: n={len(v)} med={statistics.median(v)} mean={statistics.mean(v):.1f}"
    print('  ' + stat('nva/game W', agg['nva_ct']))
    print('  ' + stat('nva<=12/game W', agg['nva_close']))

    print('\n== nva timing (winner side): first/last round + era share ==')
    for g, side, ps in alltr:
        nva = [f for f in ps['fed'] if f['reason'] == 'noValidAction']
        if not nva:
            continue
        rs = [f['rnd'] for f in nva]
        late = sum(1 for r_ in rs if r_ >= 350)
        print(f"  {g['map']:<14} w:{side} n={len(nva)} first={min(rs)} last={max(rs)} >=350:{late}/{len(rs)}")

    print('\n== nva distance-to-champ-head distribution (winner side, r300+) ==')
    bins = collections.Counter()
    for g, side, ps in alltr:
        for f in ps['fed']:
            if f['reason'] == 'noValidAction' and f['rnd'] >= 300 and f['d'] is not None:
                bins[min(f['d'], 20)] += 1
    tot = sum(bins.values())
    print('  d: ' + ' '.join(f'{k}:{v}({v/tot:.2f})' for k, v in sorted(bins.items())))

    print('\n== champ roam vs plant (winner side) ==')
    print('  era | uniq cells | mean step | % stationary | orbit radius')
    for g, side, ps in alltr:
        for e, s in ps['roam'].items():
            if s:
                print(f"  {g['map']:<14} {e:<5} uniq={s['uniq']:<4} step={s['step']:.2f} still={s['still']:.2f} orbit={s['orbit']:.1f}")

    print('\n== escorts: teammates within cheb-3 / cheb-5 of champ head (winner side) ==')
    for era_lo, era_hi, nm in [(300, 400, 'r300-399'), (400, 500, 'r400+')]:
        e3, e5 = [], []
        for g, side, ps in alltr:
            for rr in range(era_lo, min(era_hi, g['last_r'] + 1)):
                if rr in ps['esc3']:
                    e3.extend(ps['esc3'][rr]); e5.extend(ps['esc5'][rr])
        if e3:
            print(f"  {nm}: med escort<=3 {statistics.median(e3)} | med escort<=5 {statistics.median(e5)}")

    # loser side quick contrast on fed distance
    print('\n== loser side: nva med d-to-champ-head (r300+) ==')
    for g in rl:
        side = 'B' if g['winner'] == 'a' else 'A'
        ps = per_side(g, side)
        if not ps:
            continue
        dd = [f['d'] for f in ps['fed'] if f['reason'] == 'noValidAction' and f['rnd'] >= 300 and f['d'] is not None]
        nva = [f for f in ps['fed'] if f['reason'] == 'noValidAction']
        if dd:
            print(f"  {g['map']:<14} l:{side} nva={len(nva)} r300+ med dChamp={statistics.median(dd)} n={len(dd)}")


if __name__ == '__main__':
    main()
