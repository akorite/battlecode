#!/usr/bin/env python3
"""Quantify frontier pacing loops: fraction of head positions in r[a,b] that are
revisits of a cell the same dragon headed within the last `mem` rounds, plus
counts of dragons with >=half their positions revisits (the pacing population).
Usage: loophist.py <replay> [a b mem]"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'handoff', 'tooling'))
from collections import defaultdict, deque
from parse_replay import parse

def main():
    path = sys.argv[1]
    a, b, mem = (int(sys.argv[2]) if len(sys.argv) > 2 else 100,
                 int(sys.argv[3]) if len(sys.argv) > 3 else 200,
                 int(sys.argv[4]) if len(sys.argv) > 4 else 10)
    r = parse(path)
    heads = defaultdict(list)   # id -> [(round, (x,y))]
    rnd = -1
    for e in r['events']:
        if e.get('type') == 'roundStart':
            rnd = e.get('round', rnd + 1)
        elif e.get('type') == 'dragonUpdate':
            if a <= rnd <= b and 'head' in e:
                heads[e['id']].append((rnd, tuple(e['head'])))
    pace, tot, revisit_pos, total_pos = 0, 0, 0, 0
    loopers = []
    for did, hs in heads.items():
        if len(hs) < 5:
            continue
        tot += 1
        seen = {}
        rev = 0
        for rnd_i, cell in hs:
            if cell in seen and rnd_i - seen[cell] <= mem:
                rev += 1
            seen[cell] = rnd_i
        revisit_pos += rev
        total_pos += len(hs)
        if rev >= len(hs) * 0.5:
            pace += 1
            cells = {c for _, c in hs}
            loopers.append((did, len(hs), rev, len(cells)))
    print(f"{os.path.basename(path)}: dragons>=5pos={tot} pacers={pace} "
          f"revisit_frac={revisit_pos/max(1,total_pos):.3f} "
          f"(window r{a}-{b}, mem={mem})")
    for did, n, rev, nc in sorted(loopers, key=lambda x: -x[2])[:8]:
        print(f"  id{did}: {rev}/{n} positions revisits, {nc} unique cells")

# dragonUpdate carries no team; replay filename is '<map>-s<seed>-<A>-<B>.replay'
# and even ids are side A, odd side B on the standard harness (queen = min id).
# Report per-side by splitting id parity when --split is passed.

if __name__ == '__main__':
    main()
