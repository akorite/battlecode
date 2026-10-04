"""Classify h2h deaths as seam-adjacent (wrapped) or normal in a replay."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'handoff', 'tooling'))
from parse_replay import parse

DIMS = {'queen_of_spades': (25,35), 'weakhold': (40,15), 'devil': (32,16),
        'stripes': (24,12), 'dilemma': (32,16), 'tower_defense': (32,16),
        'default': (32,32), 'autarky': (54,18), 'stronghold': (48,24),
        'islands': (48,24), 'unsw': (64,24), 'trophy': (32,20), 'portals': (48,24),
        'maze': (48,24), 'schooltime': (40,30), 'trauma': (40,20), 'slithery_fight': (40,30)}

def seam_adj(a, b, W, H):
    if a is None or b is None: return False, False
    dx, dy = abs(a[0]-b[0]), abs(a[1]-b[1])
    normal = dx <= 1 and dy <= 1 and (dx or dy)
    seam = ((dx == W-1 and dy <= 1) or (dy == H-1 and dx <= 1)) and not normal
    # also cheb wrapped distance
    wdx, wdy = min(dx, W-dx), min(dy, H-dy)
    wrapped = wdx <= 1 and wdy <= 1 and (wdx or wdy) and not normal
    return seam or wrapped, normal

def analyze(path):
    p = parse(path)
    name = os.path.basename(path).split('-')[0]
    W, H = DIMS.get(name, (None, None))
    events = p['events']
    rnd = 0
    heads = {}   # id -> [x,y]
    team = {}    # id -> 'A'/'B'
    deaths = []
    for e in events:
        if e['type'] == 'roundStart': rnd = e['round']
        elif e['type'] == 'dragonUpdate':
            heads[e['id']] = e['head']
        elif e['type'] == 'dragonSplit':
            team[e['childId']] = e['team']; team.setdefault(e['parentId'], e['team'])
        elif e['type'] == 'dragonDeath':
            deaths.append((rnd, e['id'], e['reason'], heads.get(e['id'])))
    # default team from id parity (A even, B odd) where unknown
    for i in heads:
        team.setdefault(i, 'A' if i % 2 == 0 else 'B')
    out = {'map': name, 'botA': p['botA'], 'botB': p['botB'],
           'winner': p['result']['winner'] if p['result'] else None, 'deaths': []}
    dead_ids = set()
    for i, (r, did, reason, cell) in enumerate(deaths):
        dead_ids.add(did)
        if reason != 'hitHeadToHead': continue
        # find the enemy counterpart: enemy dragon that also died h2h in same round,
        # else nearest enemy head
        myt = team.get(did, 'A' if did % 2 == 0 else 'B')
        mate = None
        for r2, did2, reason2, cell2 in deaths:
            if did2 != did and r2 == r and reason2 == 'hitHeadToHead' and team.get(did2) != myt:
                mate = (did2, cell2); break
        ecell = mate[1] if mate else None
        if ecell is None:
            # nearest enemy head
            best = None
            for oid, oc in heads.items():
                if team.get(oid) == myt or oc is None: continue
                dx, dy = abs(oc[0]-cell[0]), abs(oc[1]-cell[1])
                if W: dx, dy = min(dx, W-dx), min(dy, H-dy)
                d = max(dx, dy)
                if best is None or d < best[0]: best = (d, oc)
            if best and best[0] <= 2: ecell = best[1]
        seam, normal = seam_adj(cell, ecell, W or 10**9, H or 10**9)
        out['deaths'].append({'round': r, 'id': did, 'team': myt, 'cell': cell,
                              'enemy_cell': ecell, 'seam': seam,
                              'queen': did in (0, 1)})
    return out

if __name__ == '__main__':
    res = []
    for path in sys.argv[1:]:
        try:
            res.append(analyze(path))
        except Exception as ex:
            print(f'{path}: {ex}', file=sys.stderr)
    import collections
    agg = collections.defaultdict(lambda: collections.Counter())
    qagg = collections.defaultdict(lambda: collections.Counter())
    for r in res:
        our = 'A' if r['botA'] and 'v149' in r['botA'] else 'B'
        for d in r['deaths']:
            side = 'ours' if d['team'] == our else 'theirs'
            agg[r['map']][f"{side}_h2h"] += 1
            if d['seam']: agg[r['map']][f"{side}_seam"] += 1
            if d['queen']:
                qagg[r['map']][f"{side}_q"] += 1
                if d['seam']: qagg[r['map']][f"{side}_qseam"] += 1
    print(f"{'map':<16} {'our_h2h':>8} {'our_seam':>8} {'their_h2h':>9} {'their_seam':>10} | {'our_qh2h':>8} {'our_qseam':>9} {'their_qh2h':>10} {'their_qseam':>11}")
    for m in sorted(set(list(agg)+list(qagg))):
        a, q = agg[m], qagg[m]
        print(f"{m:<16} {a['ours_h2h']:>8} {a['ours_seam']:>8} {a['theirs_h2h']:>9} {a['theirs_seam']:>10} | {q['ours_q']:>8} {q['ours_qseam']:>9} {q['theirs_q']:>10} {q['theirs_qseam']:>11}")
