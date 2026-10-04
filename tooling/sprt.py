#!/usr/bin/env python3
"""SPRT for S2: is candidate better than current best on same opponents+seeds?
H0: p = p0 (current best's measured WR). H1: p = p0 + 0.08.
alpha=0.10, beta=0.20. Paired games -> per-game candidate win indicator vs
the reference WR is wrong; proper paired test uses pair outcomes.
Simpler robust version: treat each game as Bernoulli(p) under both bots'
historical rates is confounded; instead feed pair outcomes:
  pair W=1 / S=0.5 / L=0, score = sum/n.
SPRT on per-game wins: LLR += w*log(p1/p0) + (1-w)*log((1-p1)/(1-p0)).
Bounds: A = log((1-beta)/alpha), B = log(beta/(1-alpha)).
Usage: sprt.py <games.jsonl> --p0 0.524  (p0 = current best's S1 win rate)
"""
import json, math, sys, argparse

ap = argparse.ArgumentParser()
ap.add_argument('games')
ap.add_argument('--p0', type=float, required=True)
ap.add_argument('--lift', type=float, default=0.08)
args = ap.parse_args()

p0, p1 = args.p0, min(args.p0 + args.lift, 0.99)
A = math.log((1 - 0.20) / 0.10)   # ~2.08
B = math.log(0.20 / (1 - 0.10))   # ~-1.50

games = [json.loads(l) for l in open(args.games)]
llr, n, wsum = 0.0, 0, 0.0
decisions = []
for g in games:
    w = g.get('candWin')
    if w is None: continue
    n += 1; wsum += w
    llr += w * math.log(p1 / p0) + (1 - w) * math.log((1 - p1) / (1 - p0))
    if n % 10 == 0 or llr <= B or llr >= A:
        decisions.append((n, wsum / n, llr))

print(f"SPRT  p0={p0:.3f} p1={p1:.3f}  bounds B={B:.2f} A={A:.2f}")
for n, wr, llr in decisions:
    tag = 'ACCEPT H1' if llr >= A else ('REJECT' if llr <= B else '      ')
    print(f"  n={n:3d}  wr={wr:.3f}  llr={llr:+.2f}  {tag}")
print(f"final: n={len(games)} wr={wsum/max(len(games),1):.3f} llr={llr:+.2f}",
      'ACCEPT' if llr >= A else ('REJECT' if llr <= B else 'undecided'))
