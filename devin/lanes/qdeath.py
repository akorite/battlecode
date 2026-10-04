"""Queen-death deltas from a kmatch results dir: per-map candWin + queen deaths
(cand side vs base side), plus death-reason histograms."""
import json, sys, collections, pathlib
for d in sys.argv[1:]:
    G = [json.loads(l) for l in open(pathlib.Path(d)/'games.jsonl')]
    per_map = collections.defaultdict(lambda: [0,0,0,0,0,0])
    rsn = {'c': collections.Counter(), 'b': collections.Counter()}
    qr = {'c': [], 'b': []}
    for g in G:
        c, b = g['c'], g['b']
        pm = per_map[g['map']]
        pm[0] += g['candWin']; pm[1] += 1
        if c.get('qDeadRound') is not None:
            pm[2] += 1; rsn['c'][c.get('qDeadReason')] += 1; qr['c'].append(c['qDeadRound'])
        if b.get('qDeadRound') is not None:
            pm[3] += 1; rsn['b'][b.get('qDeadReason')] += 1; qr['b'].append(b['qDeadRound'])
        pm[4] += c.get('queenEnd', 0) or 0; pm[5] += b.get('queenEnd', 0) or 0
    print(f'== {d}  ({len(G)} games)')
    print(f'{"map":>16} {"score":>5} {"n":>3} {"qDeadC":>6} {"qDeadB":>6} {"qEndC":>6} {"qEndB":>6}')
    for m in sorted(per_map):
        w,n,dc,db,ec,eb = per_map[m]
        print(f'{m:>16} {w:5.1f} {n:3} {dc:6} {db:6} {ec/n:6.2f} {eb/n:6.2f}')
    def mid(xs): return sorted(xs)[len(xs)//2] if xs else None
    print(' cand q deaths:', dict(rsn['c']), 'median round', mid(qr['c']))
    print(' base q deaths:', dict(rsn['b']), 'median round', mid(qr['b']))
