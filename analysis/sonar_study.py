"""Sonar-gossip forensics: ping cadence, burst->convergence, spatial clustering.

Q1: per-round ping count — constant/bursty/event-driven?
Q2: do receivers/teams converge spatially ~5-15r after bursts?
Q3: pings spatially clustered (hub cells) or uniform?

Extras: per-team ping rates (Ciallo 1064 / CURSEYOUBAYLE 784 / top teams vs
ladder-mid control), value-relay analysis (same u64 re-pinged by distinct
senders), hitKind mix, and value structure probe (low bits vs map coords).

Usage: python3 analysis/sonar_study.py
"""
import collections, glob, json, math, os, re, statistics, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../tooling'))
from parse_replay import parse  # noqa: E402
import replay_metrics as rm    # noqa: E402

META = json.load(open('/tmp/battles_meta_sonar.json'))
GOSSIP_TEAMS = {1064: 'ciallo', 784: 'cursey'}
D = {'N': (0, -1), 'E': (1, 0), 'S': (0, 1), 'W': (-1, 0)}


def analyze(path):
    mid = int(re.search(r'm(\d+)', path).group(1))
    meta = META[str(mid)]
    label = {}  # 'A'/'B' -> team id
    for s in 'ab':
        label[s.upper()] = meta[s]
    r = parse(path)
    ev = r['events']
    W, H, dr, edges = rm.parse_map(r['map'])
    team = {i: 'AB'[t] for i, (t, b) in enumerate(dr)}

    rnd = 0
    pos = {}                       # id -> head
    heads = {}                     # rnd -> {id: pos}
    pr = collections.defaultdict(lambda: collections.Counter())   # rnd -> team -> pings
    phit = collections.defaultdict(lambda: collections.Counter()) # rnd -> team -> hitKind
    recv = collections.defaultdict(set)    # rnd -> {ids that received a ping this round}
    recv_from = collections.defaultdict(dict)  # rnd -> recvId -> sender pos (first)
    sends_at = collections.Counter()       # (x,y) origin cells per team -> count
    sends_origin = collections.defaultdict(collections.Counter)
    senders = collections.defaultdict(set)     # team -> {id}
    pings_per_sender = collections.defaultdict(collections.Counter)
    val_senders = collections.defaultdict(set)   # value -> {senders}
    val_teams = collections.defaultdict(set)
    events_r = collections.defaultdict(list)     # rnd -> [('split'|'death'|'spawn')]
    directions = collections.defaultdict(collections.Counter)
    vals_by_team = collections.defaultdict(collections.Counter)

    for e in ev:
        if not isinstance(e, dict):
            continue
        ty = e['type']
        if ty == 'roundStart':
            rnd = e['round']
            heads[rnd] = dict(pos)
        elif ty == 'dragonUpdate':
            pos[e['id']] = tuple(e['head'])
        elif ty == 'dragonSplit':
            team[e['childId']] = e['team']
            pos[e['childId']] = tuple(e['childBody'][0])
            pos[e['parentId']] = tuple(e['parentBody'][0])
            events_r[rnd].append('split')
        elif ty == 'dragonDeath':
            pos.pop(e['id'], None)
            events_r[rnd].append('death')
        elif ty == 'tileChange' and e['hasPearl']:
            events_r[rnd].append('spawn')
        elif ty == 'sonarPing':
            st = team.get(e['senderId'])
            if st is None:
                continue
            gos = GOSSIP_TEAMS.get(label.get(st), 'other')
            pr[rnd][gos] += 1
            phit[rnd][(gos, e['hitKind'])] += 1
            directions[gos][e['direction']] += 1
            o = tuple(e['origin'])
            sends_origin[gos][o] += 1
            senders[gos].add(e['senderId'])
            pings_per_sender[gos][e['senderId']] += 1
            v = e.get('value')
            if v is not None:
                val_senders[v].add(e['senderId'])
                val_teams[v].add(st)
                vals_by_team[gos][v] += 1
            hid = e.get('hitId')
            if hid is not None:
                recv[rnd].add(hid)
                recv_from[rnd].setdefault(hid, o)

    maxr = max(heads) if heads else 0

    # --- Q2: receiver displacement + post-burst convergence ---
    # receivers: for each (rnd, id) in recv, displacement head(rnd) -> head(rnd+10)
    disp_recv, disp_ctrl = collections.defaultdict(list), collections.defaultdict(list)
    for rr, ids in recv.items():
        hs = heads.get(rr, {})
        for i in ids:
            if i not in hs:
                continue
            hh = heads.get(rr + 10, {}).get(i)
            if hh:
                gos = GOSSIP_TEAMS.get(label.get(team.get(i)), 'other')
                dx = min(abs(hh[0]-hs[i][0]), W-abs(hh[0]-hs[i][0]))
                dy = min(abs(hh[1]-hs[i][1]), H-abs(hh[1]-hs[i][1]))
                disp_recv[gos].append(dx + dy)
                # control: same-team non-receivers that round
                for j, pj in hs.items():
                    if j not in ids and team.get(j) == team.get(i):
                        hh2 = heads.get(rr + 10, {}).get(j)
                        if hh2:
                            dx2 = min(abs(hh2[0]-pj[0]), W-abs(hh2[0]-pj[0]))
                            dy2 = min(abs(hh2[1]-pj[1]), H-abs(hh2[1]-pj[1]))
                            disp_ctrl[gos].append(dx2 + dy2)

    # post-burst convergence: top-2% ping rounds; measure mean pairwise dist of
    # gossip-team heads at r vs r+L for L in 5..15 (does the swarm tighten?)
    def conv(gos):
        thr = sorted((pr[rr][gos] for rr in range(1, maxr+1))) if pr else []
        if not thr:
            return {}
        k = max(1, int(0.02 * len(thr)))
        burst = sorted(rr for rr in range(1, maxr+1) if pr[rr][gos] >= thr[-k] and pr[rr][gos] > 0)
        out = {}
        for L in (5, 10, 15):
            d0, dL = [], []
            for rr in burst:
                h0 = [heads[rr][i] for i in heads.get(rr, {}) if GOSSIP_TEAMS.get(label.get(team.get(i))) == gos]
                h1 = [heads.get(rr+L, {}).get(i) for i in heads.get(rr, {}) if GOSSIP_TEAMS.get(label.get(team.get(i))) == gos]
                h1 = [x for x in h1 if x]
                def mpd(hs):
                    if len(hs) < 2: return None
                    s = n = 0
                    for a in range(len(hs)):
                        for b in range(a+1, len(hs)):
                            s += min(abs(hs[a][0]-hs[b][0]), W-abs(hs[a][0]-hs[b][0])) + \
                                 min(abs(hs[a][1]-hs[b][1]), H-abs(hs[a][1]-hs[b][1]))
                            n += 1
                    return s / n
                m0, m1 = mpd(h0), mpd(h1)
                if m0 and m1:
                    d0.append(m0); dL.append(m1)
            if d0:
                out[L] = (statistics.mean(d0), statistics.mean(dL), len(burst))
        return out

    return {
        'mid': mid, 'W': W, 'H': H, 'rounds': maxr,
        'per_round': {g: [pr[rr][g] for rr in range(1, maxr+1)] for g in ('ciallo', 'cursey', 'other')},
        'hitkinds': {f'{g}_{k[1]}': v for g, d in phit.items() for k, v in d.items()},
        'directions': dict(directions),
        'senders': {g: len(s) for g, s in senders.items()},
        'alive_send_share': {g: sum(1 for i in senders[g]) for g in senders},
        'pps': {g: sorted(s.values(), reverse=True)[:10] for g, s in pings_per_sender.items()},
        'val_distinct': {g: len(c) for g, c in vals_by_team.items()},
        'val_top_repeat': {g: c.most_common(3) for g, c in vals_by_team.items()},
        'val_relayed': sum(1 for v, s in val_senders.items() if len(s) >= 3),
        'val_relayed_team': collections.Counter(tuple(sorted(t)) for t in val_teams.values()),
        'origins': {g: sorted(c.values(), reverse=True) for g, c in sends_origin.items()},
        'disp_recv': {g: (statistics.mean(v), statistics.median(v), len(v)) for g, v in disp_recv.items()},
        'disp_ctrl': {g: (statistics.mean(v), statistics.median(v), len(v)) for g, v in disp_ctrl.items()},
        'conv': {g: conv(g) for g in ('ciallo', 'cursey', 'other')},
        'events_r': dict(events_r),
        'result': r.get('result'),
    }


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
    json.dump({'n': len(games)}, open('/tmp/sonar_done.json', 'w'))

    # ---- aggregate ----
    def flat(key, g):
        return [x for gm in games for x in gm['per_round'][g]]

    print('\n== Q1 per-round ping rate (all rounds, per side) ==')
    for g in ('ciallo', 'cursey', 'other'):
        v = flat('per_round', g)
        games_with = sum(1 for gm in games if sum(gm['per_round'][g]) > 0)
        print(f'  {g:<7} sides_games={games_with}/{len(games)} med={statistics.median(v)} '
              f'mean={statistics.mean(v):.1f} p95={sorted(v)[int(.95*len(v))]}')

    print('\n== burstiness: per-game CV + spike analysis ==')
    for g in ('ciallo', 'cursey'):
        cvs, spike_share = [], []
        for gm in games:
            v = gm['per_round'][g]
            if sum(v) < 1000:
                continue
            m = statistics.mean(v)
            cvs.append(statistics.stdev(v) / m if m else 0)
            thr = m + 2 * statistics.stdev(v)
            spike_share.append(sum(1 for x in v if x > thr) / len(v))
        if cvs:
            print(f'  {g}: n={len(cvs)} games CV med={statistics.median(cvs):.2f} '
                  f'spike>2sd round share={statistics.median(spike_share):.3f}')

    print('\n== event-driven? pings within 2r of splits/deaths/pearl-spawns vs baseline ==')
    for g in ('ciallo', 'cursey'):
        near, far = [], []
        for gm in games:
            v = gm['per_round'][g]
            if sum(v) < 1000:
                continue
            evs = set()
            for rr, es in gm['events_r'].items():
                if any(e in ('split', 'death') for e in es):
                    evs.update(range(rr-1, rr+3))
            base = statistics.mean(v)
            near += [v[rr-1] for rr in evs if 1 <= rr <= len(v)]
            far += [v[rr-1] for rr in range(1, len(v)+1) if rr not in evs]
        if near and far:
            print(f'  {g}: near-events mean={statistics.mean(near):.1f} vs rest={statistics.mean(far):.1f}')

    print('\n== Q3 spatial clustering (origin cells) ==')
    for g in ('ciallo', 'cursey', 'other'):
        conc, tot_cells = [], 0
        for gm in games:
            o = gm['origins'].get(g)
            if o:
                conc.append(sum(o[:5]) / sum(o))
                tot_cells += len(o)
        if conc:
            print(f'  {g}: mean top-5-cell share={statistics.mean(conc):.3f} (uniform~={5/max(1,tot_cells//len(conc)):.4f})')

    print('\n== senders coverage ==')
    for g in ('ciallo', 'cursey'):
        n = [gm['senders'].get(g, 0) for gm in games]
        top = [x for gm in games for x in gm['pps'].get(g, [])]
        print(f'  {g}: senders/game med={statistics.median(n)} top-sender pings med={statistics.median(top) if top else 0}')

    print('\n== hitKind mix (share of team pings) ==')
    agg = collections.defaultdict(collections.Counter)
    for gm in games:
        for k, v in gm['hitkinds'].items():
            g, hk = k.split('_', 1)
            agg[g][hk] += v
    for g, c in agg.items():
        t = sum(c.values())
        print(f'  {g}: ' + ' '.join(f'{k}={v/t:.2f}' for k, v in c.most_common()))

    print('\n== values: distinct + relay structure ==')
    for g in ('ciallo', 'cursey'):
        d = [gm['val_distinct'].get(g, 0) for gm in games]
        reps = [x[1] for gm in games for x in gm['val_top_repeat'].get(g, [])]
        print(f'  {g}: distinct/game med={statistics.median(d)} top-value repeat med={statistics.median(reps)}')
    rel = [gm['val_relayed'] for gm in games]
    print(f'  values seen from >=3 distinct senders per game: med={statistics.median(rel)}')
    c = collections.Counter()
    for gm in games:
        for k, v in gm['val_relayed_team'].items():
            c[k] += v
    print('  team-mix of values:', c.most_common(5))

    print('\n== Q2 receiver displacement (10r, manhattan) ==')
    for g in ('ciallo', 'cursey', 'other'):
        dr_ = [gm['disp_recv'].get(g) for gm in games if gm['disp_recv'].get(g)]
        dc_ = [gm['disp_ctrl'].get(g) for gm in games if gm['disp_ctrl'].get(g)]
        if dr_:
            print(f'  {g}: receivers mean={statistics.mean(x[0] for x in dr_):.2f} '
                  f'vs non-receivers={statistics.mean(x[0] for x in dc_):.2f} (n games={len(dr_)})')

    print('\n== post-burst swarm spread (mean pairwise dist r vs r+L) ==')
    for g in ('ciallo', 'cursey'):
        for L in (5, 10, 15):
            m0, m1, nb = [], [], []
            for gm in games:
                if L in gm['conv'].get(g, {}):
                    a, b, n = gm['conv'][g][L]
                    m0.append(a); m1.append(b); nb.append(n)
            if m0:
                print(f'  {g} L={L}: spread {statistics.mean(m0):.1f} -> {statistics.mean(m1):.1f} (tightens {sum(1 for a,b in zip(m0,m1) if b<a)}/{len(m0)} games)')

    print('\n== direction mix ==')
    dd = collections.defaultdict(collections.Counter)
    for gm in games:
        for g, c in gm['directions'].items():
            dd[g].update(c)
    for g, c in dd.items():
        t = sum(c.values())
        print(f'  {g}: ' + ' '.join(f'{k}={v/t:.2f}' for k, v in c.most_common()))


if __name__ == '__main__':
    main()
