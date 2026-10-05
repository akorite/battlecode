#!/usr/bin/env python3
"""Per-round team trajectories from a replay: alive, total len, queen len,
splits, eaten, h2h deaths. For structural comparison across bots.
Usage: trajectory.py <replay> [...] -> JSON per file: {A:{rounds:[...]}, B:{...}}"""
import collections, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
from parse_replay import parse


def analyze(path):
    r = parse(path)
    # id -> team (starters: even=A odd=B; splits carry team)
    team = {0: 'A', 1: 'B', 2: 'A', 3: 'B'}
    rnd = -1
    # per round: per team set of (id, len), splits, eaten(approx via len delta>0?), deaths
    cur = {}         # id -> {'team','len'}
    per_round = collections.defaultdict(lambda: {'A': collections.Counter(), 'B': collections.Counter()})
    # simpler: reconstruct body length per dragon per round from head/tail span? engine
    # emits dragonUpdate per STEP with head/tail — len not explicit. Track len via
    # deaths/splits; approximate len from growth events is unreliable.
    # Instead: alive count + splits + deaths per round are exact; length via
    # result summary only. Queen len via queen's own updates? not in events.
    # Compromise: per-round alive + splits + h2h/other deaths + per-dragon alive-span.
    alive = collections.defaultdict(set)
    splits_r = collections.defaultdict(lambda: collections.Counter())
    deaths_r = collections.defaultdict(lambda: collections.Counter())
    death_reason = collections.defaultdict(collections.Counter)
    first_spawn = {}
    for e in r['events']:
        t = e.get('type')
        if t == 'roundStart':
            rnd = e.get('round', rnd + 1)
        elif t == 'dragonSplit':
            did = e['childId']
            par = e['parentId']
            tm = e.get('team') or team.get(par, 'A' if par % 2 == 0 else 'B')
            team[did] = tm
            first_spawn.setdefault(did, rnd)
            splits_r[rnd][tm] += 1
        elif t == 'dragonDeath':
            did = e['id']
            tm = team.get(did, 'A' if did % 2 == 0 else 'B')
            deaths_r[rnd][tm] += 1
            death_reason[tm][e.get('reason')] += 1
        elif t == 'dragonUpdate':
            did = e['id']
            if did not in team:
                team[did] = 'A' if did % 2 == 0 else 'B'
            alive[rnd].add(did)
    n_rounds = max(alive) + 1 if alive else 0
    out = {'rounds': n_rounds, 'map': r.get('map', '').split('\n')[2].replace('MAP_NAME ', '') if r.get('map') else '',
           'result': r.get('result'), 'A': {}, 'B': {}}
    for tm in 'AB':
        ids = [d for d, s in team.items() if s == tm]
        out[tm] = {
            'alive_r': [sum(1 for d in alive.get(rr, ()) if team[d] == tm) for rr in range(n_rounds)],
            'splits_r': [splits_r[rr][tm] for rr in range(n_rounds)],
            'deaths_r': [deaths_r[rr][tm] for rr in range(n_rounds)],
            'death_reason': dict(death_reason[tm]),
            'n_dragons': len(ids),
            'queen_first_dead_r': min((rr for rr, i, why in
                                       [(rr, i, w) for rr in range(n_rounds) for i, w in
                                        [(i, w) for i, w in []]]), default=None),
        }
    # queen death round: lowest id per team death
    for tm in 'AB':
        q = min([d for d, s in team.items() if s == tm], default=None)
        out[tm]['queen_id'] = q
        for rr in range(n_rounds):
            if q is not None and deaths_r[rr][tm] and q in alive.get(rr - 1, ()):
                pass
        # simpler: scan events again not needed — deaths_r has counts not ids.
    # redo: per-dragon last alive round
    last_alive = {}
    for rr, ids in alive.items():
        for d in ids:
            last_alive[d] = rr
    out['last_alive'] = {str(k): v for k, v in last_alive.items()}
    out['first_spawn'] = {str(k): v for k, v in first_spawn.items()}
    return out


def summarize(a):
    """Compact fingerprint: key milestones for comparison."""
    res = {}
    for tm in 'AB':
        al = a[tm]['alive_r']; sp = a[tm]['splits_r']
        res[tm] = {
            'alive@50': al[50] if len(al) > 50 else None,
            'alive@100': al[100] if len(al) > 100 else None,
            'alive@200': al[200] if len(al) > 200 else None,
            'alive@300': al[300] if len(al) > 300 else None,
            'alive@end': al[-1] if al else 0,
            'peak_alive': max(al) if al else 0,
            'peak_round': al.index(max(al)) if al else 0,
            'splits<50': sum(sp[:50]), 'splits50-150': sum(sp[50:150]),
            'splits150-300': sum(sp[150:300]), 'splits300+': sum(sp[300:]),
            'deaths': dict(a[tm]['death_reason']),
            'q_last_alive': a['last_alive'].get(str(a[tm]['queen_id'])),
        }
    res['end'] = a['result']
    res['rounds'] = a['rounds']
    return res


if __name__ == '__main__':
    for p in sys.argv[1:]:
        a = analyze(p)
        print(json.dumps({'file': os.path.basename(p), **summarize(a)}))
