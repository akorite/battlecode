#!/usr/bin/env python3
"""earlyecon bisect table: per-map cand-vs-base splits60/eaten60/alive50 + pair score.

usage: python3 devin/lanes/ee_table.py results/ee_*  (run from ~/bc)
"""
import json, sys, glob, collections

MAPS = ['devil', 'stripes', 'tower_defense', 'queen_of_spades', 'default', 'autarky']

def agg(d):
    rows = collections.defaultdict(list)
    for line in open(f'{d}/games.jsonl'):
        g = json.loads(line)
        rows[g['map']].append(g)
    out = {}
    for m, gs in rows.items():
        # dedupe killed-run duplicates: same (seed,candSide) -> keep last
        ded = {}
        for g in gs:
            ded[(g['seed'], g['candSide'])] = g
        gs = list(ded.values())
        n = len(gs)
        wins = sum(g['candWin'] for g in gs)
        def mean(key):
            v = [g['c'][key] for g in gs if g['c'].get(key) is not None]
            w = [g['b'][key] for g in gs if g['b'].get(key) is not None]
            return (sum(v)/max(1,len(v)), sum(w)/max(1,len(w)))
        cs, bs = mean('splits60')
        ce, be = mean('eaten60')
        ca, ba = mean('alive50')
        cq, bq = mean('qNonRam')
        cd = sum(g['c'].get('d_hitWall',0)+g['c'].get('d_hitSelf',0)+g['c'].get('d_hitOtherBody',0) for g in gs)/n
        bd = sum(g['b'].get('d_hitWall',0)+g['b'].get('d_hitSelf',0)+g['b'].get('d_hitOtherBody',0) for g in gs)/n
        extra = {k: mean(k) for k in ('tl50', 'tl100', 'tl200', 'eat25', 'eat100', 'eat200')}
        out[m] = (n, wins, cs, bs, ce, be, ca, ba, cq, bq, cd, bd, extra)
    return out

dirs = sys.argv[1:]
allm = {}
for d in dirs:
    allm[d] = agg(d)

print(f"{'run':16} {'map':15} {'n':>3} {'pairW':>6} {'spl60 c/b':>10} {'eat60 c/b':>10} {'alv50 c/b':>10} {'qNonRam':>9} {'wallish c/b':>10}")
for d in dirs:
    tot_n = tot_w = 0
    for m in MAPS + [m for m in allm[d] if m not in MAPS]:
        if m not in allm[d]: continue
        n, w, cs, bs, ce, be, ca, ba, cq, bq, cd, bd, extra = allm[d][m]
        tot_n += n; tot_w += w
        print(f"{d.split('/')[-1]:16} {m:15} {n:>3} {w:5.1f} {cs:5.1f}/{bs:<4.1f} {ce:5.1f}/{be:<4.1f} {ca:5.1f}/{ba:<4.1f} {cq:.2f}/{bq:.2f} {cd:5.1f}/{bd:<4.1f}")
    print(f"{d.split('/')[-1]:16} {'ALL':15} {tot_n:>3} {tot_w:5.1f} ({100*tot_w/max(1,tot_n):.1f}%)")
    print()
    # S0 economy checkpoints (only when the metrics exist in this run's games)
    if any(extra.get('tl100', (0, 0))[0] or extra.get('tl100', (0, 0))[1] for m, (*_, extra) in allm[d].items()):
        print(f"{'':16} {'map':15} {'tl50 c/b':>10} {'tl100 c/b':>11} {'tl200 c/b':>11} {'eat25 c/b':>10} {'eat100 c/b':>11} {'eat200 c/b':>11}")
        for m in MAPS + [m for m in allm[d] if m not in MAPS]:
            if m not in allm[d]: continue
            e = allm[d][m][-1]
            print(f"{d.split('/')[-1]:16} {m:15} {e['tl50'][0]:5.1f}/{e['tl50'][1]:<5.1f} {e['tl100'][0]:6.1f}/{e['tl100'][1]:<5.1f} {e['tl200'][0]:6.1f}/{e['tl200'][1]:<5.1f} {e['eat25'][0]:5.1f}/{e['eat25'][1]:<5.1f} {e['eat100'][0]:6.1f}/{e['eat100'][1]:<5.1f} {e['eat200'][0]:6.1f}/{e['eat200'][1]:<5.1f}")
        print()
