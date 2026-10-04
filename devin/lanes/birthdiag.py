"""Birth-divergence diagnostics: v104-level econ vs v120 on elim maps.

For each (map, seed): replay1 has A=v104,B=v120; replay2 has A=v120,B=v104.
Team A = even ids in both (queen = min id of the team's initial dragons).

Per side+seed we get one (v104 births) vs (v120 births) timeline from the
same starting side. For every v104 split we ask whether a v120 split lands
nearby (same round +-15, any parent) — else it's a "missing birth", and we
classify its parent (queen vs swarm) and the child-cell spread.
"""
import collections
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../handoff/tooling'))
from parse_replay import parse


def births(path):
    ev = parse(path)['events']
    cur = 0
    # id -> team from the initial dragonUpdates (first before any roundStart)
    team = {}
    started = False
    out = []
    for e in ev:
        if e['type'] == 'roundStart':
            cur = e['round']
            started = True
        elif e['type'] == 'dragonUpdate' and not started and 'team' not in e:
            pass
        elif e['type'] == 'dragonSplit':
            out.append({
                'round': cur, 'team': e['team'], 'parent': e['parentId'],
                'child': e['childId'], 'pLen': len(e['parentBody']),
                'cLen': len(e['childBody']), 'cell': e['childBody'][0],
            })
    # queen = lowest id seen splitting for each team (matches queen=min initial id)
    return out


def game_rows(tag_dir, mapname):
    rows = []
    for seed in range(1, 9):
        fs = sorted(glob.glob(f'{tag_dir}/replays/{mapname}-s{seed}-*.replay'))
        f1 = f2 = None
        for f in fs:
            if re.search(r'abyss_v104-abyss_', f):
                f1 = f
            elif re.search(r'abyss_(v120|econ120)-abyss_v104', f):
                f2 = f
        if not (f1 and f2):
            continue
        b1, b2 = births(f1), births(f2)
        # replay1: A=v104, B=v120; replay2: A=v120, B=v104
        for side in 'AB':
            v104 = [x for x in (b1 if side == 'A' else b2) if x['team'] == side] if side == 'A' else \
                   [x for x in b2 if x['team'] == 'B']
            v120 = [x for x in (b1 if side == 'B' else b2) if x['team'] == side] if side == 'A' else \
                   [x for x in b1 if x['team'] == 'B']
            rows.append((seed, side, v104, v120))
    return rows


def main(tag='results/diag_v104'):
    maps = ['devil', 'stripes', 'tower_defense']
    grand = collections.Counter()
    for m in maps:
        agg = collections.Counter()
        missing = []
        for seed, side, v104, v120 in game_rows(tag, m):
            agg['v104_splits60'] += sum(1 for x in v104 if x['round'] <= 60)
            agg['v120_splits60'] += sum(1 for x in v120 if x['round'] <= 60)
            agg['v104_q_splits60'] += sum(1 for x in v104 if x['round'] <= 60 and x['parent'] <= 1)
            agg['v120_q_splits60'] += sum(1 for x in v120 if x['round'] <= 60 and x['parent'] <= 1)
            agg['v104_splits_all'] += len(v104)
            agg['v120_splits_all'] += len(v120)
            r120 = [x['round'] for x in v120]
            for x in v104:
                if x['round'] > 100:
                    continue
                if not any(abs(x['round'] - r) <= 15 for r in r120):
                    missing.append((m, seed, side, x['round'], x['parent'] <= 1, x['pLen'], x['cell']))
                    agg['missing'] += 1
                    agg['missing_q' if x['parent'] <= 1 else 'missing_w'] += 1
                    agg[f'missing_r{x["round"]//20*20}'] += 1
        print(f'== {m}')
        for k in sorted(agg):
            print(f'   {k}: {agg[k]}')
        grand.update(agg)
        # where do missing-birth child cells sit vs the pair's birth cells?
    print('== TOTAL', dict(grand))
    # per-missing detail compactly: role x round-bucket histogram
    hist = collections.Counter((mm[4], mm[3] // 20 * 20) for mm in missing)
    print('missing births (queen?, round bucket):', dict(sorted(hist.items())))


if __name__ == '__main__':
    main(*sys.argv[1:])
