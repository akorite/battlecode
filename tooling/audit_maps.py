#!/usr/bin/env python3
"""Map-class audit: per-map pair outcomes + mechanism fields from games.jsonl.
Usage: audit_maps.py results/<tag>"""
import sys, json, os
from collections import defaultdict

d = sys.argv[1]
gj = os.path.join(d, 'games.jsonl') if os.path.isdir(d) else d
games = [json.loads(l) for l in open(gj)]
bymap = defaultdict(list)
for g in games:
    bymap[g['map']].append(g)

def fmtg(g):
    w = 'W' if g['candWin'] else 'L'
    end = g.get('end', '?')[:8]
    cq = g['c'].get('qDeadRound'); bq = g['b'].get('qDeadRound')
    cr = (g['c'].get('qDeadReason') or '')[:4]; br = (g['b'].get('qDeadReason') or '')[:4]
    q = f" cq={g['c'].get('queenEnd')}"
    if cq is not None: q += f"†{cq}{cr}"
    q += f" bq={g['b'].get('queenEnd')}"
    if bq is not None: q += f"†{bq}{br}"
    return (f"{g['seed']}:{g['candSide']}{w} r{g.get('rounds','?')} {end}"
            f" len{g['c']['longest']}/{g['b']['longest']} tot{g['c']['total']}/{g['b']['total']}{q}")

for m in sorted(bymap):
    gs = sorted(bymap[m], key=lambda g: (g['seed'], g['candSide']))
    wins = sum(g['candWin'] for g in gs)
    aside = [g for g in gs if g['candSide'] == 'A']
    bside = [g for g in gs if g['candSide'] == 'B']
    a_w = sum(g['candWin'] for g in aside); b_w = sum(g['candWin'] for g in bside)
    seat = ''
    if len(aside) == len(bside) == 2:
        if a_w == b_w == 2: seat = 'CAND-WINS-BOTH-SEATS'
        elif a_w == b_w == 0: seat = 'CAND-LOSES-BOTH-SEATS'
        elif (a_w == 0) == (b_w == 0): seat = 'SIDE-LOCKED(same seat wins both seeds)'
    r499 = [g for g in gs if g.get('rounds', 0) >= 499 or g.get('end') == 'roundLimit']
    cq_alive = sum(1 for g in r499 if g['c'].get('queenEnd', 0) > 0)
    bq_alive = sum(1 for g in r499 if g['b'].get('queenEnd', 0) > 0)
    qd_c = [g['c'].get('qDeadRound') for g in gs if g['c'].get('qDeadRound') is not None]
    qd_b = [g['b'].get('qDeadRound') for g in gs if g['b'].get('qDeadRound') is not None]
    print(f"\n{m}  cand {wins}-{len(gs)-wins}  {seat}  | queens@499 cand {cq_alive}/{len(r499)} base {bq_alive}/{len(r499)} | qDead c:{qd_c} b:{qd_b}")
    for g in gs:
        print('   ' + fmtg(g))
