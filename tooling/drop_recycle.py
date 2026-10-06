#!/usr/bin/env python3
"""Drop-recycle audit: when a dragon dies, ceil(L/2) pearls drop on its own
body cells (verified: True flips land on the dragon's last head positions).
Measure (a) death-cell -> nearest ALLY head distance at the death round,
(b) whether dropped pearls get re-eaten within ~5 rounds, and by which side
(us / them / decayed).

Usage: python3 tooling/drop_recycle.py --cand abyss_v237 <replays...|dir>
"""
import sys, os, json, glob, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.expanduser('~/bc/handoff/tooling'))
from parse_replay import parse

WINDOW = 5


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def analyze(path, cand, side_map=None, force_side=None):
    r = parse(path)
    base = os.path.basename(path).replace('.replay', '')
    parts = base.rsplit('-', 2)
    if side_map and base.lstrip('m') in side_map:
        cand_side = side_map[base.lstrip('m')]
        na = cand
    elif side_map and base in side_map:
        cand_side = side_map[base]
        na = cand
    else:
        na = parts[-2] if len(parts) > 1 else base
        cand_side = 'A' if na == cand else 'B'
    if force_side:
        cand_side = force_side
    winner = (r.get('result') or {}).get('winner')
    mp = parts[0].rsplit('-s', 1)

    team = {}
    heads = collections.defaultdict(dict)      # side -> id -> head
    hist = collections.defaultdict(list)       # id -> [head cells in order]
    lens = {}
    flips = collections.defaultdict(list)      # cell -> [(round, hasPearl)]
    head_at = collections.defaultdict(dict)    # rnd -> cell -> side
    id_at = collections.defaultdict(dict)      # rnd -> cell -> dragon id
    pos_at = collections.defaultdict(dict)     # rnd -> id -> head cell
    parents = {}                               # child id -> parent id
    deaths = []
    rnd = -1

    for e in r['events']:
        t = e.get('type')
        if t == 'roundStart':
            rnd = e['round']
            continue
        if t == 'dragonUpdate':
            i = e['id']
            s = e.get('team') or ('A' if i % 2 == 0 else 'B')
            team[i] = s
            h = tuple(e['head'])
            heads[s][i] = h
            hist[i].append(h)
            head_at[rnd][h] = s
            id_at[rnd][h] = i
            pos_at[rnd][i] = h
            continue
        if t == 'dragonSplit':
            s = e['team']
            team[e['childId']] = s
            team[e['parentId']] = s
            heads[s][e['childId']] = tuple(e['childBody'][0])
            hist[e['childId']] = [tuple(c) for c in e['childBody']]
            lens[e['childId']] = len(e.get('childBody', [1]))
            lens[e['parentId']] = len(e.get('parentBody', [1]))
            hist[e['parentId']] = [tuple(c) for c in e['parentBody']]
            head_at[rnd][tuple(e['childBody'][0])] = s
            head_at[rnd][tuple(e['parentBody'][-1])] = s
            id_at[rnd][tuple(e['childBody'][0])] = e['childId']
            id_at[rnd][tuple(e['parentBody'][-1])] = e['parentId']
            pos_at[rnd][e['childId']] = tuple(e['childBody'][0])
            pos_at[rnd][e['parentId']] = tuple(e['parentBody'][-1])
            parents[e['childId']] = e['parentId']
            continue
        if t == 'tileChange':
            flips[tuple(e['tile'])].append((rnd, e['hasPearl']))
            continue
        if t == 'dragonDeath':
            i = e['id']
            s = team.get(i, 'A' if i % 2 == 0 else 'B')
            dcell = heads[s].get(i)
            # body = last distinct head positions (snake rule); len estimate:
            # distinct path cells capped — pearls drop on own cells and we
            # detect via True flips on the path anyway
            path = hist.get(i, [])
            body = []
            for c in reversed(path[-30:]):
                if c not in body:
                    body.append(c)
            if dcell and dcell not in body:
                body.insert(0, dcell)
            ally_d = None
            for j, hj in heads[s].items():
                if j == i or dcell is None:
                    continue
                d = cheb(dcell, hj)
                ally_d = d if ally_d is None else min(ally_d, d)
            foe = 'B' if s == 'A' else 'A'
            enemy_d = None
            for j, hj in heads[foe].items():
                if dcell is None:
                    continue
                d = cheb(dcell, hj)
                enemy_d = d if enemy_d is None else min(enemy_d, d)
            deaths.append({
                'file': base, 'map': mp[0], 'round': rnd, 'id': i, 'side': s,
                'cand_death': s == cand_side, 'reason': e.get('reason'),
                'len_est': len(body), 'death_cell': dcell, 'path': body,
                'ally_d': ally_d, 'enemy_d': enemy_d,
                'winner': winner, 'cand_won': winner == cand_side,
                'parent': parents.get(i),
            })
            heads[s].pop(i, None)
            continue

    out = []
    for d in deaths:
        dr = d['round']
        pathset = set(d['path'])
        drops = []
        for c in pathset:
            seq = flips.get(c, [])
            gain = [rr for rr, hp in seq if hp and dr <= rr <= dr + 2]
            if gain:
                drops.append(c)
        eaten_us = eaten_them = eaten_unk = decayed = 0
        fates = []
        for c in drops:
            nxt = [rr for rr, hp in flips.get(c, [])
                   if (not hp) and rr > dr]
            consumed_r = nxt[0] if nxt else None
            if consumed_r is not None and consumed_r - dr <= WINDOW:
                who = head_at[consumed_r].get(c)
                if who is None:
                    who = head_at[consumed_r - 1].get(c) or \
                          head_at[consumed_r + 1].get(c)
                eater_id = id_at[consumed_r].get(c) or \
                    id_at[consumed_r - 1].get(c) or id_at[consumed_r + 1].get(c)
                travel = None; is_parent = False
                if eater_id is not None:
                    epos = pos_at[dr].get(eater_id) or \
                        pos_at[max(0, dr - 1)].get(eater_id)
                    if epos is not None:
                        travel = cheb(c, epos)
                    is_parent = (eater_id == d.get('parent'))
                fates.append(('eaten', who, consumed_r - dr, travel, bool(is_parent)))
                if who == d['side']:
                    eaten_us += 1
                elif who is not None:
                    eaten_them += 1
                else:
                    eaten_unk += 1
            else:
                fates.append(('decayed', None, None))
                decayed += 1
        rec = {k: v for k, v in d.items() if k != 'path'}
        rec['drop_n'] = len(drops)
        rec['eaten_us'] = eaten_us
        rec['eaten_them'] = eaten_them
        rec['eaten_unk'] = eaten_unk
        rec['decayed'] = decayed
        rec['fates'] = fates[:6]
        out.append(rec)
    return out


def main():
    cand = 'abyss_v237'
    args = sys.argv[1:]
    side_map = None
    if '--cand' in args:
        i = args.index('--cand')
        cand = args[i + 1]
        del args[i:i + 2]
    if '--sides' in args:
        i = args.index('--sides')
        raw = json.load(open(args[i + 1]))
        side_map = {k: v[0] for k, v in raw.items()}
        del args[i:i + 2]
    force = None
    if '--force-side' in args:
        i = args.index('--force-side')
        force = args[i + 1]
        del args[i:i + 2]
        side_map = {}
    files = []
    for a in args:
        if os.path.isdir(a):
            files += sorted(glob.glob(os.path.join(a, '*.replay')))
        else:
            files.append(a)
    for f in files:
        try:
            for rec in analyze(f, cand, side_map, force):
                print(json.dumps(rec))
        except Exception as ex:
            print(json.dumps({'file': f, 'error': str(ex)}), file=sys.stderr)


if __name__ == '__main__':
    main()
