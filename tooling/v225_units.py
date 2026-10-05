#!/usr/bin/env python3
"""v225 mechanism audit: does releasing lateSplitUnits (20->9999, post-r300
worker splits) lift alive@end / unit count, where do the extra splits land,
does the champion still consolidate (longest@end), and what's the cost
(h2h donations)?

Usage: python3 tooling/v225_units.py --cand abyss_v225 <replays dir-or-files>

Per replay, per side:
  splits_total, splits_post300 (count, rounds, cells), splits_post300_parents
  alive@300/400/499 (or last round), longest@end, deaths by reason
  (h2h/self/wall/body/nva/eaten split <=300 vs >300), queen end len.
"""
import sys, os, json, collections, glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.expanduser('~/bc/handoff/tooling'))
from parse_replay import parse


def side_of(dragon_id, splits, updates_team):
    if dragon_id in updates_team:
        return updates_team[dragon_id]
    if dragon_id in splits:
        return splits[dragon_id]
    return 'A' if dragon_id % 2 == 0 else 'B'


def analyze(path, cand):
    r = parse(path)
    base = os.path.basename(path).replace('.replay', '')
    parts = base.rsplit('-', 2)
    na = parts[-2]
    cand_side = 'A' if na == cand else 'B'

    T = {'A': collections.Counter(), 'B': collections.Counter()}
    rnd = -1
    team = {}          # id -> 'A'/'B'
    heads = {}         # id -> head cell (latest)
    lens = {}          # id -> body len (latest)
    alive = set()
    splits_post300 = {'A': [], 'B': []}   # (round, cell, parentLen)
    alive_at = {'A': {}, 'B': {}}
    queen = {'A': 0, 'B': 1}
    qlen_end = {'A': 0, 'B': 0}

    for e in r['events']:
        t = e.get('type')
        if t == 'roundStart':
            rnd = e['round']
            for s in 'AB':
                alive_at[s][rnd] = sum(1 for i in alive if team.get(i) == s)
            continue
        if t == 'dragonUpdate':
            i = e['id']
            alive.add(i)
            heads[i] = tuple(e['head'])
            lens[i] = len(e.get('tail', [])) + 1
            if 'team' in e:
                team[i] = e['team']
            elif i not in team:
                team[i] = 'A' if i % 2 == 0 else 'B'
            continue
        if t == 'dragonSplit':
            s = e.get('team') or ('A' if e['parentId'] % 2 == 0 else 'B')
            team[e['childId']] = s
            team[e['parentId']] = s
            alive.add(e['childId'])
            plen = len(e.get('parentBody', []))
            heads[e['childId']] = tuple(e['childBody'][0])
            lens[e['childId']] = len(e.get('childBody', []))
            T[s]['splits'] += 1
            if rnd > 300:
                T[s]['splits_post300'] += 1
                splits_post300[s].append((rnd, tuple(e['childBody'][0]), plen))
            continue
        if t == 'dragonDeath':
            i = e['id']
            s = team.get(i, 'A' if i % 2 == 0 else 'B')
            reason = e.get('reason', '?')
            T[s]['d_' + reason] += 1
            if rnd > 300:
                T[s]['d_' + reason + '_post300'] += 1
            alive.discard(i)
            continue

    for s in 'AB':
        alive_ids = [i for i in alive if team.get(i) == s]
        if alive_ids:
            q = min(alive_ids)
            qlen_end[s] = lens.get(q, 0)
        else:
            qlen_end[s] = 0

    ms = parts[0].rsplit('-s', 1)
    out = {'file': base, 'map': ms[0], 'seed': 's' + ms[1] if len(ms) > 1 else '?',
           'cand_side': cand_side}
    res = r.get('result', {})
    for s in 'AB':
        o = {}
        for k in ('splits', 'splits_post300'):
            o[k] = T[s][k]
        for reason in ('hitHeadToHead', 'hitSelf', 'hitOtherBody', 'hitWall',
                       'noValidAction', 'eaten'):
            o['d_' + reason] = T[s]['d_' + reason]
            o['d_' + reason + '_p300'] = T[s]['d_' + reason + '_post300']
        rounds = sorted(alive_at[s])
        for mark in (300, 400, 499):
            past = [x for x in rounds if x <= mark]
            o[f'alive{mark}'] = alive_at[s][past[-1]] if past else None
        o['qlen_end'] = qlen_end[s]
        o['splits_p300_detail'] = splits_post300[s]
        out[s] = o
    out['result'] = res
    return out


def main():
    cand = 'abyss_v225'
    args = sys.argv[1:]
    if '--cand' in args:
        i = args.index('--cand')
        cand = args[i + 1]
        del args[i:i + 2]
    files = []
    for a in args:
        if os.path.isdir(a):
            files += sorted(glob.glob(os.path.join(a, '*.replay')))
        else:
            files.append(a)
    for f in files:
        try:
            print(json.dumps(analyze(f, cand)))
        except Exception as ex:
            print(json.dumps({'file': f, 'error': str(ex)}))


if __name__ == '__main__':
    main()
