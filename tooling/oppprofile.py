#!/usr/bin/env python3
"""Opponent bracket forensics (explore lane) — per-team profile.

For each replay where the target team is on one side:
  - eats: per-side pearl takes (head lands on a pending/pearl tile), plus
    territory: dist from OWN spawn vs dist from ENEMY spawn at eat site
    (contested = eat site nearer enemy spawn / mid).
  - deaths: reason + distance from own spawn (home congestion vs field).
  - queen: ending len, buds, roam radius (dist from spawn at 100r buckets),
    death round/reason.
  - champ: longest@end dragon — how dominant (longest vs 2nd longest at end),
    and whether killing pattern suggests single-champ dependence.
"""
import sys, os, json, collections, statistics

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'handoff', 'tooling'))
sys.path.insert(0, HERE)
from parse_replay import parse
from replay_metrics import parse_map


def analyze(path, meta):
    mid = int(os.path.basename(path)[1:].split('.')[0])
    m = meta[str(mid)]
    tid = m['t']
    side = 'A' if m['a']['id'] == tid else 'B'
    opp_side = 'AB'[1 - 'AB'.index(side)]

    r = parse(path)
    res = r.get('result') or {}
    ev = r['events']
    W, H, dr, edges = parse_map(r['map'])

    def tdist(a, b):
        dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
        return min(dx, W - dx) + min(dy, H - dy)

    body, team = {}, {}
    for e in ev:
        if e['type'] == 'roundStart':
            break
        if e['type'] == 'dragonUpdate' and e['id'] < len(dr):
            t, b = dr[e['id']]
            team[e['id']] = 'AB'[t]
            body[e['id']] = collections.deque(tuple(x) for x in b)
    queen = {s: min((i for i in team if team[i] == s), default=-1) for s in 'AB'}
    spawn = {s: body[queen[s]][0] for s in 'AB' if queen[s] in body}

    rnd = 0
    pend = set(); pearls = set()
    eaten = {'A': 0, 'B': 0}
    eat_home = {'A': 0, 'B': 0}; eat_away = {'A': 0, 'B': 0}
    deaths = []
    qbuds = {'A': 0, 'B': 0}
    qroam = {'A': [], 'B': []}
    qd = {}
    endbody = {'A': [], 'B': []}
    for e in ev:
        t = e['type']
        if t == 'roundStart':
            rnd = e['round']
        elif t == 'tileChange':
            tl = tuple(e['tile'])
            if e['hasPearl']: pearls.add(tl)
            else: pearls.discard(tl); pend.add(tl)
        elif t == 'dragonUpdate':
            i = e['id']
            if i not in body: continue
            b = body[i]; h, tl = tuple(e['head']), tuple(e['tail'])
            if b[0] != h:
                b.appendleft(h)
                s = team[i]
                if h in pend:
                    eaten[s] += 1
                    dOwn = tdist(h, spawn[s])
                    dEn = tdist(h, spawn['AB'[1 - 'AB'.index(s)]])
                    (eat_home if dOwn <= dEn else eat_away)[s] += 1
                pend.discard(h)
                if i == queen.get(s) and rnd % 25 == 0:
                    qroam[s].append(tdist(h, spawn[s]))
            while len(b) > 1 and b[-1] != tl: b.pop()
        elif t == 'dragonSplit':
            s = e['team']
            if e['parentId'] == queen.get(s): qbuds[s] += 1
            body[e['parentId']] = collections.deque(tuple(x) for x in e['parentBody'])
            body[e['childId']] = collections.deque(tuple(x) for x in e['childBody'])
            team[e['childId']] = s
        elif t == 'dragonDeath':
            i = e['id']; s = team.get(i)
            if s is None or i not in body: continue
            dsp = tdist(body[i][0], spawn.get(s, body[i][0]))
            deaths.append((s, dsp, e['reason'], rnd))
            if i == queen.get(s): qd[s] = (rnd, e['reason'])
            body.pop(i, None)

    for s in 'AB':
        endbody[s] = sorted((len(bb) for j, bb in body.items() if team[j] == s), reverse=True)

    tr = res.get('team' + side) or {}
    tro = res.get('team' + opp_side) or {}
    return {
        'map': m['map'], 'side': side, 'won': res.get('winner') == side,
        'end': res.get('endReason'), 'rounds': rnd,
        'us': {
            'eaten': eaten[side], 'eatAway': eat_away[side],
            'deaths': [(d, why, rd) for s, d, why, rd in deaths if s == side],
            'qEnd': len(body.get(queen[side], [])) if queen[side] in body else 0,
            'qbuds': qbuds[side],
            'qroam': statistics.mean(qroam[side]) if qroam[side] else 0,
            'qdead': qd.get(side),
            'lens': endbody[side],
            'longest': tr.get('longestDragon', 0), 'total': tr.get('totalLength', 0),
            'alive': tr.get('dragonCount', 0),
        },
        'opp': {
            'eaten': eaten[opp_side], 'eatAway': eat_away[opp_side],
            'deaths': [(d, why, rd) for s, d, why, rd in deaths if s == opp_side],
            'qEnd': len(body.get(queen[opp_side], [])) if queen[opp_side] in body else 0,
            'qbuds': qbuds[opp_side],
            'qroam': statistics.mean(qroam[opp_side]) if qroam[opp_side] else 0,
            'qdead': qd.get(opp_side),
            'lens': endbody[opp_side],
            'longest': tro.get('longestDragon', 0), 'total': tro.get('totalLength', 0),
            'alive': tro.get('dragonCount', 0),
        },
    }


def main():
    meta = json.load(open('/tmp/opp_meta.json'))
    for t in (314, 46, 87):
        d = f'/home/ubuntu/bc/opp_{t}'
        rows = []
        for f in sorted(os.listdir(d)):
            if not f.endswith('.replay'): continue
            try: rows.append(analyze(os.path.join(d, f), meta))
            except Exception as ex: print('ERR', f, ex)
        w = sum(r['won'] for r in rows)
        print(f"\n===== team {t}: {w}-{len(rows)-w} in {len(rows)} replays =====")
        for tag, key in (('TEAM', 'us'), ('VS', 'opp')):
            e = [r[key]['eaten'] for r in rows]
            ea = [r[key]['eatAway']/r[key]['eaten'] for r in rows if r[key]['eaten']]
            ds = [x for r in rows for x in r[key]['deaths']]
            dsp = [x[0] for x in ds]
            why = collections.Counter(x[1] for x in ds)
            qe = [r[key]['qEnd'] for r in rows]
            qb = [r[key]['qbuds'] for r in rows]
            qr = [r[key]['qroam'] for r in rows]
            qd_ = [r[key]['qdead'] for r in rows if r[key]['qdead']]
            ln = [r[key]['longest'] for r in rows]
            l2 = [r[key]['lens'][1] if len(r[key]['lens'])>1 else 0 for r in rows]
            champdom = [l1/(l2v or 1) for l1, l2v in zip(ln, l2)]
            print(f"  {tag}: eats mean {statistics.mean(e):.0f} (away-frac {statistics.mean(ea):.2f})")
            print(f"      deaths n={len(ds)} reason {dict(why.most_common(5))}")
            if dsp: print(f"      death spawn-dist mean {statistics.mean(dsp):.0f} med {statistics.median(dsp)} "
                          f"<=10: {100*sum(1 for v in dsp if v<=10)/len(dsp):.0f}% >20: {100*sum(1 for v in dsp if v>20)/len(dsp):.0f}%")
            print(f"      qEnd mean {statistics.mean(qe):.1f} med {statistics.median(qe)}; "
                  f"qbuds {statistics.mean(qb):.1f}/g; qroam {statistics.mean(qr):.0f}; "
                  f"qdeaths {collections.Counter(x[1] for x in qd_).most_common()} rounds {[x[0] for x in qd_][:8]}")
            print(f"      longest@end mean {statistics.mean(ln):.0f}; champ-dominance L1/L2 mean {statistics.mean(champdom):.1f}")
        print("  per-game:")
        for r in rows:
            u = r['us']
            print(f"    {r['map'][:14]:14} {'W' if r['won'] else 'L'} {r['end'][:11]:11} "
                  f"e{u['eaten']:4} eaway{int(100*u['eatAway']/max(u['eaten'],1)):3}% "
                  f"qE{u['qEnd']:3} qb{u['qbuds']} d{len(u['deaths']):3} "
                  f"ln{u['longest']:3} tot{u['total']:4} al{u['alive']:2} qdead{u['qdead']}")


if __name__ == '__main__':
    main()
