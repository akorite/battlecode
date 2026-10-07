#!/usr/bin/env python3
"""Top-team queen forensics (explore lane).

Per replay: queen = min starter id per team (verified convention). Extracts:
  (1) splits where parent is a starter (id < len(dr)) — queen-bud events +
      parent length at bud; queen splits (parent == team queen) separately.
  (2) queen head distance from her spawn cell per 100-round bucket.
  (3) queen ending length (0 if dead) by game outcome.
  (4) queen death (round, reason).
  (5) non-queen split parent-length histogram.

Usage: qforensics.py <replay_dir> [--top-ids id1,id2,...]
"""
import sys, os, json, collections, statistics, re

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'handoff', 'tooling'))
sys.path.insert(0, HERE)
from parse_replay import parse
from replay_metrics import parse_map

BUCKET = 100


def analyze(path):
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
            body[e['id']] = collections.deque(tuple(x) for x in b)
            team[e['id']] = 'AB'[t]
    queen = {s: min((i for i in team if team[i] == s), default=-1) for s in 'AB'}
    spawn = {i: body[i][0] for i in body}

    rnd = 0
    qd = {}
    qend = {}
    qdist = {s: collections.defaultdict(list) for s in 'AB'}
    q_buds = {s: [] for s in 'AB'}          # (round, parentLen)
    starter_buds = {s: [] for s in 'AB'}    # parent is starter but not queen
    worker_bud_lens = {s: [] for s in 'AB'}
    bot_names = {'A': r.get('botA'), 'B': r.get('botB')}

    for e in ev:
        t = e['type']
        if t == 'roundStart':
            rnd = e['round']
        elif t == 'dragonUpdate':
            i = e['id']
            if i not in body:
                continue
            b = body[i]
            h, tl = tuple(e['head']), tuple(e['tail'])
            if b[0] != h:
                b.appendleft(h)
            while len(b) > 1 and b[-1] != tl:
                b.pop()
            if i == queen.get(team[i]) and rnd % 25 == 0:
                qdist[team[i]][rnd // BUCKET].append(tdist(b[0], spawn[i]))
        elif t == 'dragonSplit':
            s = e['team']
            plen = len(e['parentBody'])
            if e['parentId'] == queen.get(s):
                q_buds[s].append((rnd, plen))
            elif e['parentId'] in body and e['parentId'] < len(dr):
                starter_buds[s].append((rnd, plen))
            else:
                worker_bud_lens[s].append(plen)
            body[e['parentId']] = collections.deque(tuple(x) for x in e['parentBody'])
            body[e['childId']] = collections.deque(tuple(x) for x in e['childBody'])
            team[e['childId']] = s
        elif t == 'dragonDeath':
            i = e['id']
            s = team.get(i)
            if s is None or i not in body:
                continue
            if i == queen.get(s):
                qd[s] = (rnd, e.get('reason'))
            body.pop(i, None)

    for s in 'AB':
        q = queen.get(s, -1)
        qend[s] = len(body[q]) if q in body else 0

    return {
        'file': os.path.basename(path), 'map': r.get('map'), 'bots': bot_names,
        'winner': res.get('winner'), 'end': res.get('endReason'), 'rounds': rnd,
        'sides': {s: {'queen': queen[s], 'qEnd': qend[s], 'qDeath': qd.get(s),
                      'qBuds': q_buds[s], 'starterBuds': starter_buds[s],
                      'workerBuds': worker_bud_lens[s],
                      'qDist': {k: round(statistics.mean(v), 1) for k, v in sorted(qdist[s].items())}}
                  for s in 'AB'},
    }


def main():
    d = sys.argv[1]
    tops = set()
    if len(sys.argv) > 2 and sys.argv[2] == '--top-ids':
        tops = set(int(x) for x in sys.argv[3].split(','))
    rows = [analyze(os.path.join(d, f)) for f in sorted(os.listdir(d)) if f.endswith('.replay')]
    print(f'games: {len(rows)}')

    # need team ids — botA/botB names in replay; match to known top names
    allnames = collections.Counter()
    for r in rows:
        for s in 'AB':
            allnames[r['bots'][s]] += 1
    print('teams seen:', allnames.most_common(20))

    for label, sel in (('ALL', lambda r, s: True),):
        qsplits = [r['sides'][s]['qBuds'] for r in rows for s in 'AB']
        nq = sum(1 for q in qsplits if q)
        plens = [pl for q in qsplits for _, pl in q]
        wpl = [pl for r in rows for s in 'AB' for pl in r['sides'][s]['workerBuds']]
        sb = [pl for r in rows for s in 'AB' for _, pl in r['sides'][s]['starterBuds']]
        print(f"\n[{label}] queen-buds: {nq} queens budded / {len(qsplits)} sides; "
              f"parentLens {sorted(plens)[:20]}")
        if plens:
            print(f"  queen bud parentLen: mean {statistics.mean(plens):.1f} "
                  f"median {statistics.median(plens)} n={len(plens)}")
        print(f"  other-starter buds: {len(sb)}, lens {collections.Counter(sb).most_common(8)}")
        if wpl:
            hist = collections.Counter(min(pl // 5, 12) * 5 for pl in wpl)
            print(f"  worker-bud parentLen mean {statistics.mean(wpl):.1f} "
                  f"median {statistics.median(wpl)} n={len(wpl)}  hist5: {dict(sorted(hist.items()))}")

        qends_w = [r['sides'][s]['qEnd'] for r in rows for s in 'AB' if r['winner'] == s]
        qends_l = [r['sides'][s]['qEnd'] for r in rows for s in 'AB' if r['winner'] not in (None, '', 'draw') and r['winner'] != s]
        print(f"  qEnd winners: mean {statistics.mean(qends_w):.1f} median {statistics.median(qends_w)} "
              f"dist {collections.Counter(min(q//5,10)*5 for q in qends_w).most_common()}")
        print(f"  qEnd losers:  mean {statistics.mean(qends_l):.1f} median {statistics.median(qends_l)} "
              f"dist {collections.Counter(min(q//5,10)*5 for q in qends_l).most_common()}")

        deaths = [r['sides'][s]['qDeath'] for r in rows for s in 'AB' if r['sides'][s]['qDeath']]
        print(f"  queen deaths: {len(deaths)}  reasons {collections.Counter(d[1] for d in deaths).most_common()}")
        rb = collections.Counter(min(d[0] // 100, 6) * 100 for d in deaths)
        print(f"  death rounds: {dict(sorted(rb.items()))}")

        # roam: mean dist-from-spawn per bucket across queens (winners vs losers)
        for tag, cond in (('W', lambda r, s: r['winner'] == s),
                          ('L', lambda r, s: r['winner'] not in (None, '', 'draw') and r['winner'] != s)):
            agg = collections.defaultdict(list)
            for r in rows:
                for s in 'AB':
                    if cond(r, s):
                        for b, v in r['sides'][s]['qDist'].items():
                            agg[b].append(v)
            print(f"  qDist-from-spawn ({tag}): " +
                  '  '.join(f'r{b*100}+:{statistics.mean(v):.0f}' for b, v in sorted(agg.items())))

    # winners only deep table for the top performers
    print('\nper-game queen table (winner side only, qEnd desc):')
    wrows = [(r['sides'][s], r['bots'][s], r['file']) for r in rows for s in 'AB' if r['winner'] == s]
    wrows.sort(key=lambda x: -x[0]['qEnd'])
    for sd, bot, f in wrows[:15]:
        print(f"  {f[:24]} {str(bot)[:20]:20} qEnd {sd['qEnd']:3} buds {len(sd['qBuds'])} "
              f"death {sd['qDeath']} roam " +
              ' '.join(f'{b}:{v}' for b, v in list(sd['qDist'].items())[:6]))


if __name__ == '__main__':
    main()
