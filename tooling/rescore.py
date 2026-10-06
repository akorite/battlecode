"""Rescore a kmatch board under production rules: elim -> (queenEnd, longest, total).
Usage: python3 tooling/rescore.py <dir> [...]
"""
import json, sys

for d in sys.argv[1:]:
    wins = eng = flips = 0
    n = 0
    flip_list = []
    for line in open(f'{d}/games.jsonl'):
        g = json.loads(line)
        c, b = g['c'], g['b']
        n += 1
        eng += g['candWin']
        # production ranking
        if c['alive'] == 0 or b['alive'] == 0:
            prod = 1.0 if c['alive'] > b['alive'] else 0.0 if b['alive'] > c['alive'] else 0.5
        else:
            ck = (c['queenEnd'], c['longest'], c['total'])
            bk = (b['queenEnd'], b['longest'], b['total'])
            prod = 1.0 if ck > bk else 0.0 if bk > ck else 0.5
        if prod != g['candWin']:
            flips += 1
            flip_list.append((g['map'], g['seed'], g['candSide'], g['candWin'], prod,
                              c['queenEnd'], b['queenEnd'], c['longest'], b['longest']))
        wins += prod
    if n:
        print(f"{d}: engine {eng/n*100:.1f}% -> production {wins/n*100:.1f}%  (n={n}, flips={flips})")
        for f in flip_list[:12]:
            print('   flip', f)
