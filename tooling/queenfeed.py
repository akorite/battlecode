#!/usr/bin/env python3
"""Queen feed-rate anatomy: when/how do elite queens eat vs ours.

Per side per replay:
  qEaten, eat-round histogram (per 100), stationarity at eat time
  (queen head displacement over prior 10 rounds), escort profile
  (same-team dragons within Chebyshev 3, est. lengths), queen
  roaming coverage (unique cells / 100r).

Length estimator: exact at dragonSplit (childBody/parentBody),
then +1 per attributed eat, starters seeded len=4 pre-first-split.
"""
import sys, os, json, collections

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'handoff', 'tooling'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_replay import parse


def analyze(path):
    r = parse(path)
    events = r['events']

    # --- team assignment: union-find over ally relations + split team field
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
            team[e['parentId']] = e['team']
            team[e['childId']] = e['team']
            union(e['parentId'], e['childId'])
        elif e['type'] == 'sonarPing':
            if e.get('hitKind') in ('ally', 'allyHead') and e.get('hitId') is not None:
                union(e['senderId'], e['hitId'])
    # propagate team through unions
    for e in events:
        if e['type'] == 'dragonSplit':
            team[find(e['parentId'])] = e['team']
    # assign unresolved starters by root
    for did in list(team):
        team.setdefault(find(did), team[did])
    # fallback parity for never-seen ids
    def tmof(did):
        t = team.get(did, team.get(find(did)))
        return t

    # --- walk events
    rnd = -1
    head = {}          # id -> [x,y] latest
    qlen = {}          # id -> est length
    eaten = collections.Counter()
    dq = collections.defaultdict(list)   # id -> [(rnd, head)]
    queen_eats = collections.defaultdict(list)  # team -> [(rnd, tile)]
    escort = collections.defaultdict(list)      # team -> [(rnd, [(id,len,dist)])]
    upd_queue = []   # dragonUpdates this round (id, head)
    pending_eats = []  # (rnd, tile) awaiting attribution
    eat_attr = {}    # (rnd,tile) -> id
    cur_round_upds = []
    alive = collections.defaultdict(set)

    def flush_round():
        # attribute eats: first upd in round whose head==tile
        for (rr, t) in pending_eats:
            t = tuple(t)
            for (did, h) in cur_round_upds:
                if h == t or h == list(t):
                    eat_attr[(rr, t)] = did
                    eaten[did] += 1
                    qlen[did] = qlen.get(did, 4) + 1
                    break
        pending_eats.clear()
        cur_round_upds.clear()

    queen_ids = set()
    # determine queens after team propagation: starters = lowest 4 ids, queen = min id per team
    starter_teams = {}
    for e in events:
        if e['type'] == 'dragonSplit' and e['parentId'] in (0, 1, 2, 3):
            starter_teams.setdefault(e['parentId'], e['team'])
    # second pass for team of each starter via sonar unions
    teams_of = {}
    for did in (0, 1, 2, 3):
        teams_of[did] = team.get(did) or team.get(find(did))
    qs = {}
    for did in (0, 1, 2, 3):
        t = teams_of.get(did)
        if t and (t not in qs or did < qs[t]):
            qs[t] = did

    for e in events:
        t = e['type']
        if t == 'roundStart':
            flush_round()
            rnd = e['round']
        elif t == 'dragonUpdate':
            did = e['id']; head[did] = e['head']
            cur_round_upds.append((did, e['head']))
            alive[rnd].add(did)
            dq[did].append((rnd, e['head']))
            qlen.setdefault(did, 4)
        elif t == 'tileChange':
            if e['hasPearl'] is False:
                pending_eats.append((rnd, e['tile']))
        elif t == 'dragonSplit':
            qlen[e['childId']] = len(e.get('childBody') or []) or 4
            qlen[e['parentId']] = len(e.get('parentBody') or []) or qlen.get(e['parentId'], 4)
        elif t == 'dragonDeath':
            qlen.pop(e['id'], None)
    flush_round()

    # --- per queen: eats, stationarity, escorts
    out = {}
    qhead_r = {}
    for tm, q in qs.items():
        hist = [h for (rr, h) in dq.get(q, [])]
        rounds = [rr for (rr, h) in dq.get(q, [])]
        # last head per round
        last = {}
        for rr, h in dq.get(q, []):
            last[rr] = h
        qhead_r[tm] = last
        eats = [(rr, t) for (rr, t), did in eat_attr.items() if did == q]
        rec = {'queen': q, 'qEaten': len(eats), 'eats': [],
               'planted_eats': 0, 'roam_eats': 0,
               'escort_lens': [], 'escort_n': [],
               'cells_per_100': []}
        for (rr, tile) in eats:
            # stationarity: positions in last[last] rounds
            span = [last.get(x) for x in range(max(0, rr - 10), rr + 1)]
            span = [s for s in span if s]
            disp = len(set(map(tuple, span)))
            planted = (rr >= 10 and last.get(rr - 5) == last.get(rr))
            rec['eats'].append(rr)
            if planted:
                rec['planted_eats'] += 1
            else:
                rec['roam_eats'] += 1
            # escorts: same-team heads within Chebyshev 3 of queen head at rr
            allies = []
            for did in alive.get(rr, ()):
                if did == q or tmof(did) != tm:
                    continue
                h = None
                for (r2, h2) in reversed(dq.get(did, [])):
                    if r2 <= rr:
                        h = h2; break
                if h is None:
                    continue
                d = max(abs(h[0] - tile[0]), abs(h[1] - tile[1]))
                if d <= 3:
                    allies.append((did, qlen.get(did, 4), d))
            rec['escort_lens'].append([a[1] for a in allies])
            rec['escort_n'].append(len(allies))
        # roaming coverage per 100 rounds
        for lo in range(0, 500, 100):
            cells = set()
            for rr in range(lo, min(lo + 100, 500)):
                if last.get(rr): cells.add(tuple(last[rr]))
            rec['cells_per_100'].append(len(cells))
        out[tm] = rec
    return {'map': (r.get('map') or '').split('MAP_NAME ')[-1].split('\n')[0] if r.get('map') else '',
            'result': r.get('result'), 'sides': out}


def fmt(path):
    a = analyze(path)
    print(f"== {os.path.basename(path)} map={a['map']}")
    for tm in 'AB':
        s = a['sides'].get(tm)
        if not s:
            continue
        hist = collections.Counter(e // 100 for e in s['eats'])
        import statistics
        el = [l for lst in s['escort_lens'] for l in lst]
        print(f"  {tm}: qEaten={s['qEaten']} planted={s['planted_eats']} roam={s['roam_eats']} "
              f"hist={dict(hist)} escortN_avg={statistics.mean(s['escort_n']) if s['escort_n'] else 0:.1f} "
              f"escortLen_med={statistics.median(el) if el else '-'} cells/100={s['cells_per_100']}")


if __name__ == '__main__':
    for p in sys.argv[1:]:
        fmt(p)
