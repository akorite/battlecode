#!/usr/bin/env python3
"""Field census: elim / key-1 (longest) / key-2 (total) loss decomposition.

Scoring at roundLimit (corrected): winner = (longestDragon, totalLength)
lexicographic — no queen key. For each replay:
  end reason, longest/total both sides (result block),
  dragonCount both sides at r450, splits in r360-500 both sides,
  queen (min starter id per side) death round+reason.

Usage: fieldcensus.py <matchlist.jsonl> <replay_dir>
"""
import sys, os, json, collections

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'handoff', 'tooling'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_replay import parse


def analyze(path):
    r = parse(path)
    res = r.get('result') or {}
    events = r['events']
    # team assignment via split team field + sonar allies
    parent = {}
    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb: parent[ra] = rb
    team = {}
    for e in events:
        if e['type'] == 'dragonSplit':
            team[e['parentId']] = e['team']; team[e['childId']] = e['team']
            union(e['parentId'], e['childId'])
        elif e['type'] == 'sonarPing' and e.get('hitKind') in ('ally', 'allyHead') and e.get('hitId') is not None:
            union(e['senderId'], e['hitId'])
    for e in events:
        if e['type'] == 'dragonSplit':
            team[find(e['parentId'])] = e['team']
    for did in list(team):
        team.setdefault(find(did), team[did])
    def tmof(did):
        return team.get(did, team.get(find(did)))

    rnd = -1
    alive = collections.defaultdict(set)
    splits = collections.defaultdict(lambda: collections.Counter())
    deaths = {}                      # id -> (round, reason)
    for e in events:
        t = e['type']
        if t == 'roundStart':
            rnd = e['round']
        elif t == 'dragonUpdate':
            alive[rnd].add(e['id'])
        elif t == 'dragonSplit':
            tm = tmof(e['parentId'])
            if tm: splits[rnd][tm] += 1
        elif t == 'dragonDeath':
            deaths[e['id']] = (rnd, e.get('reason'))
    n_rounds = (res.get('endReason') == 'roundLimit') and 499 or (max(alive) if alive else 0)

    out = {}
    for tm in 'AB':
        ids = [d for d in team if tmof(d) == tm]
        q = min((d for d in ids if d <= 3), default=min(ids) if ids else None)
        qd = deaths.get(q)
        dc450 = None
        if alive.get(450):
            dc450 = sum(1 for d in alive[450] if tmof(d) == tm)
        sp = sum(splits[rr][tm] for rr in range(360, 501))
        out[tm] = {
            'dc450': dc450,
            'splits360_500': sp,
            'qdead': qd,
        }
    return {
        'end': res.get('endReason'), 'winner': res.get('winner'),
        'rounds': res.get('endReason') == 'roundLimit' and 499 or (max(alive) if alive else 0),
        'A': {**out.get('A', {}), **(res.get('teamA') or {})},
        'B': {**out.get('B', {}), **(res.get('teamB') or {})},
    }


def main():
    matches = {}
    for l in open(sys.argv[1]):
        l = l.strip()
        if l.startswith('{'):
            m = json.loads(l); matches[m['id']] = m
    rows = []
    for f in sorted(os.listdir(sys.argv[2])):
        if not f.endswith('.replay'):
            continue
        mid = int(f[1:-7])
        m = matches.get(mid)
        if not m:
            continue
        ours = 'a' if m['a']['id'] == 351 else 'b'
        d = analyze(os.path.join(sys.argv[2], f))
        s = d.get(ours.upper()) or {}
        o = d.get('B' if ours == 'a' else 'A') or {}
        win = (d.get('winner') or '').lower() == ours
        ln, oln = s.get('longestDragon'), o.get('longestDragon')
        tot, otot = s.get('totalLength'), o.get('totalLength')
        if win:
            mode = 'win'
        elif d['end'] == 'teamEliminated':
            mode = 'elim'
        elif oln is not None and ln is not None and oln > ln:
            mode = 'key1-longest'
        elif oln == ln and (otot or 0) > (tot or 0):
            mode = 'key2-total'
        else:
            mode = 'roundLimit-other'
        rows.append(dict(id=mid, map=m['map'], opp=m['b' if ours == 'a' else 'a']['name'],
                         oelo=m['b' if ours == 'a' else 'a']['elo'],
                         win=win, mode=mode, end=d['end'], rounds=d['rounds'],
                         ln=ln, oln=oln, tot=tot, otot=otot,
                         dc=s.get('dc450'), odc=o.get('dc450'),
                         sp=s.get('splits360_500'), osp=o.get('splits360_500'),
                         qd=s.get('qdead'), oqd=o.get('qdead'),
                         dcA=(d.get('A') or {}).get('dragonCount'), dcB=(d.get('B') or {}).get('dragonCount')))
    c = collections.Counter(r['mode'] for r in rows)
    w = sum(1 for r in rows if r['win'])
    print(f"n={len(rows)} record {w}-{len(rows)-w}")
    print('modes:', dict(c))
    for r in rows:
        if not r['win']:
            print(f"* {r['id']} {r['map'][:14]:14s} {r['mode']:15s} r{r['rounds']} ln={r['ln']}v{r['oln']} "
                  f"tot={r['tot']}v{r['otot']} dc450={r['dc']}v{r['odc']} sp360={r['sp']}v{r['osp']} "
                  f"qd={r['qd']} oqd={r['oqd']} vs {r['opp'][:16]}({round(r['oelo'])})")
    # aggregates for losses
    ls = [r for r in rows if not r['win']]
    rl = [r for r in ls if r['mode'].startswith('key')]
    import statistics as st
    if rl:
        print(f"\nroundLimit losses n={len(rl)}: our splits360-500 mean {st.mean(r['sp'] for r in rl if r['sp'] is not None):.1f} "
              f"vs opp {st.mean(r['osp'] for r in rl if r['osp'] is not None):.1f}")
        print(f"  dc450 ours mean {st.mean(r['dc'] for r in rl if r['dc'] is not None):.1f} vs opp {st.mean(r['odc'] for r in rl if r['odc'] is not None):.1f}")
        print(f"  longest ours {st.mean(r['ln'] for r in rl):.1f} vs {st.mean(r['oln'] for r in rl):.1f}; total ours {st.mean(r['tot'] for r in rl):.1f} vs {st.mean(r['otot'] for r in rl):.1f}")
        frozen = sum(1 for r in rl if (r['sp'] or 0) <= 2)
        print(f"  our split-freeze (<=2 splits r360-500): {frozen}/{len(rl)}; opp frozen: {sum(1 for r in rl if (r['osp'] or 0)<=2)}/{len(rl)}")


if __name__ == '__main__':
    main()
