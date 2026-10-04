#!/usr/bin/env python3
"""Action-A gate table: tl@25/50/100, n@25/50/100, eat@25/50/100, elim<r200,
queen deaths <r50 — cand side (c) vs base side (b), per map + overall.

usage: python3 devin/lanes/gate_stats.py results/<tag> [...]
"""
import json, sys, collections

def agg(d):
    rows = {}
    for line in open(f'{d}/games.jsonl'):
        g = json.loads(line)
        rows[(g['map'], g['seed'], g['candSide'])] = g  # dedupe rerun dups: keep last
    gs = collections.defaultdict(list)
    for g in rows.values():
        gs[g['map']].append(g)
    out = {}
    for m, gg in gs.items():
        n = len(gg)
        w = sum(g['candWin'] for g in gg)
        def mean(k):
            c = [g['c'].get(k) for g in gg]
            b = [g['b'].get(k) for g in gg]
            c = [x for x in c if x is not None]
            b = [x for x in b if x is not None]
            return (sum(c) / max(1, len(c)), sum(b) / max(1, len(b)))
        mrow = {'n': n, 'w': w}
        for k in ('tl25', 'tl50', 'tl100', 'n25', 'n50', 'n100', 'eat25', 'eat50', 'eat100', 'alive50'):
            mrow[k] = mean(k)
        # eliminations <r200 suffered by each side
        ce = be = 0
        cq = bq = 0
        for g in gg:
            if g['end'] == 'teamEliminated' and g['rounds'] < 200:
                if g['winner'] == g['candSide']:
                    be += 1   # base side was eliminated
                else:
                    ce += 1   # cand side eliminated
            for side, cnt in (('c', 'ce'), ('b', 'be')):
                pass
            cq += 1 if (g['c'].get('qDeadRound') is not None and g['c']['qDeadRound'] < 50) else 0
            bq += 1 if (g['b'].get('qDeadRound') is not None and g['b']['qDeadRound'] < 50) else 0
        mrow['celim'] = ce; mrow['belim'] = be; mrow['cqd'] = cq; mrow['bqd'] = bq
        out[m] = mrow
    return out

MAPS = ['devil', 'dilemma', 'trophy', 'default', 'stripes', 'tower_defense', 'queen_of_spades']

for d in sys.argv[1:]:
    A = agg(d)
    print(f"== {d}")
    print(f"{'map':15} {'n':>3} {'pairW':>5} {'tl25':>11} {'tl50':>11} {'tl100':>12} {'n25':>9} {'n50':>9} {'n100':>10} {'eat25':>10} {'eat50':>10} {'elim<200':>9} {'qd<50':>7}")
    T = collections.Counter()
    for m in MAPS + [x for x in A if x not in MAPS]:
        if m not in A: continue
        r = A[m]
        for k in ('n', 'w', 'celim', 'belim', 'cqd', 'bqd'): T[k] += r[k]
        for k in ('tl25', 'tl50', 'tl100', 'n25', 'n50', 'n100', 'eat25', 'eat50'):
            T['c' + k] += r[k][0] * r['n']; T['b' + k] += r[k][1] * r['n']
        print(f"{m:15} {r['n']:>3} {r['w']:5.1f} {r['tl25'][0]:5.1f}/{r['tl25'][1]:<5.1f} {r['tl50'][0]:5.1f}/{r['tl50'][1]:<5.1f} {r['tl100'][0]:6.1f}/{r['tl100'][1]:<5.1f} "
              f"{r['n25'][0]:4.1f}/{r['n25'][1]:<4.1f} {r['n50'][0]:4.1f}/{r['n50'][1]:<4.1f} {r['n100'][0]:5.1f}/{r['n100'][1]:<5.1f} "
              f"{r['eat25'][0]:5.1f}/{r['eat25'][1]:<5.1f} {r['eat50'][0]:5.1f}/{r['eat50'][1]:<5.1f} {r['celim']:>4}/{r['belim']:<4} {r['cqd']:>3}/{r['bqd']:<3}")
    n = max(1, T['n'])
    print(f"{'ALL':15} {int(T['n']):>3} {T['w']:5.1f} ({100*T['w']/n:.1f}%) "
          f"{T['ctl25']/n:5.1f}/{T['btl25']/n:<5.1f} {T['ctl50']/n:5.1f}/{T['btl50']/n:<5.1f} {T['ctl100']/n:6.1f}/{T['btl100']/n:<5.1f} "
          f"{T['cn25']/n:4.1f}/{T['bn25']/n:<4.1f} {T['cn50']/n:4.1f}/{T['bn50']/n:<4.1f} {T['cn100']/n:5.1f}/{T['bn100']/n:<5.1f} "
          f"{T['ceat25']/n:5.1f}/{T['beat25']/n:<5.1f} {T['ceat50']/n:5.1f}/{T['beat50']/n:<5.1f} {int(T['celim']):>4}/{int(T['belim']):<4} {int(T['cqd']):>3}/{int(T['bqd']):<3}")
    print()
