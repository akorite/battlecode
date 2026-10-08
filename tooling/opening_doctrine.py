"""Opening-doctrine census r0-80 on ladder replays.

Per side per game:
  1) split timing: first-split round, splits per 10r bin r0-80
  2) roam distance r0-40: per unit-round, tcheb(head, own_birth_cell)
     and tcheb(head, team_origin) -> percentiles
  3) contested eats r0-80: for each pearl removal attributed to an
     eater (nearest head, validated), enemy distance to that cell at
     the eat round; contested = enemy head within cheb-3. Also the
     reverse: enemy eats where OUR unit was within 3 (lost contests).
  4) eat depth: distance from eater's own birth cell to the eat cell
     (deep food vs spawn-adjacent crumbs) r0-80.

Tag: 'ours' (351), 'top' (top-8 ids), 'opp'.
"""
import sys, os, glob, json, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
from parse_replay import parse
from pocket_metric import parse_map

TOP = {454, 157, 306, 545, 70, 55, 264, 213}
OURS = 351


def tcheb(W, H, a, b):
    dx = abs(a[0] - b[0]); dy = abs(a[1] - b[1])
    return max(min(dx, W - dx), min(dy, H - dy))


def analyze(path, meta):
    r = parse(path)
    res = r.get('result') or {}
    W, H, dr, _ = parse_map(r['map'])
    team = {i: 'AB'[t] for i, (t, _b) in enumerate(dr)}
    init_head = collections.defaultdict(list)
    for i, (t, body) in enumerate(dr):
        init_head['AB'[t]].append(tuple(body[0]))

    hist = collections.defaultdict(dict)
    born, died, own_spawn = {}, {}, {}
    rnd = 0
    removals = []
    splits = []
    for e in r['events']:
        ty = e['type']
        if ty == 'roundStart':
            rnd += 1
        elif ty == 'dragonUpdate':
            born.setdefault(e['id'], 0)
            hist[e['id']][rnd] = tuple(e['head'])
            own_spawn.setdefault(e['id'], tuple(e['head']) if rnd <= 1 else own_spawn.get(e['id']))
        elif ty == 'dragonSplit':
            team[e['childId']] = e['team']
            born[e['childId']] = rnd
            pb, cb = e['parentBody'], e['childBody']
            own_spawn[e['childId']] = tuple(cb[0])
            hist[e['childId']][rnd] = tuple(cb[0])
            hist[e['parentId']][rnd] = tuple(pb[0])
            splits.append({'round': rnd, 'team': e['team']})
        elif ty == 'dragonDeath':
            died[e['id']] = rnd
        elif ty == 'tileChange' and e.get('hasPearl') is False:
            removals.append((rnd, tuple(e['tile'])))
    maxr = rnd
    harr = {}
    for i, h in hist.items():
        arr = [None] * (maxr + 1)
        last = None
        for rr in range(1, maxr + 1):
            if rr in h:
                last = h[rr]
            arr[rr] = last
        harr[i] = arr
    alive_ids = list(hist.keys())

    # eat attribution (removal -> nearest alive head, d<=1)
    eats = []  # (round, cell, unit)
    for rr, c in removals:
        best = None; bd = 99
        for i in alive_ids:
            if not (born.get(i, 1 << 30) <= rr < died.get(i, 1 << 30)):
                continue
            h = harr[i][rr]
            if h is None:
                continue
            d = tcheb(W, H, h, c)
            if d < bd:
                bd = d; best = i
        if bd <= 1:
            eats.append((rr, c, best))

    out = []
    for side in 'AB':
        tid = meta.get('a' if side == 'A' else 'b')
        enemy = 'B' if side == 'A' else 'A'
        ids = set(i for i, t in team.items() if t == side)
        eids = set(i for i, t in team.items() if t == enemy)

        sp = [s['round'] for s in splits if s['team'] == side and s['round'] <= 80]
        bins = [0] * 8
        for rr in sp:
            bins[(rr - 1) // 10] += 1

        roam = collections.defaultdict(list)   # bin r0-10/11-20/21-30/31-40
        for rr in range(1, min(40, maxr) + 1):
            b = (rr - 1) // 10
            for i in ids:
                if not (born.get(i, 1 << 30) <= rr < died.get(i, 1 << 30)):
                    continue
                h = harr[i][rr]
                spc = own_spawn.get(i)
                if h and spc:
                    roam[b].append(tcheb(W, H, h, spc))

        # contested: my eats where enemy head within 3 of cell at eat round
        my_eats = [(rr, c) for rr, c, u in eats if u in ids and rr <= 80]
        their_eats = [(rr, c) for rr, c, u in eats if u in eids and rr <= 80]
        cont_win = 0; cont_n = 0
        enemy_d_all = []
        for rr, c in my_eats:
            de = min((tcheb(W, H, harr[j][rr], c) for j in eids
                      if harr[j][rr] and born.get(j, 1 << 30) <= rr < died.get(j, 1 << 30)), default=99)
            enemy_d_all.append(de)
            if de <= 3:
                cont_win += 1
            cont_n += 1
        # lost contests: their eats where OUR head within 3
        lost_close = 0
        for rr, c in their_eats:
            dm = min((tcheb(W, H, harr[j][rr], c) for j in ids
                      if harr[j][rr] and born.get(j, 1 << 30) <= rr < died.get(j, 1 << 30)), default=99)
            if dm <= 3:
                lost_close += 1

        # eat depth: distance from eater birth cell to eat cell
        depth = collections.defaultdict(list)
        for rr, c, u in eats:
            if u in ids and rr <= 80:
                spc = own_spawn.get(u)
                if spc:
                    depth[(rr - 1) // 20].append(tcheb(W, H, spc, c))

        out.append({
            'match': meta.get('id'), 'team_id': tid, 'side': side,
            'tag': 'ours' if tid == OURS else ('top' if tid in TOP else 'opp'),
            'won': res.get('winner') == side, 'map': meta.get('map'), 'rounds': maxr,
            'first_split': min(sp) if sp else None,
            'split_bins': bins, 'splits80': len(sp),
            'roam': {b: v for b, v in roam.items()},
            'eats80': cont_n,
            'contested_wins': cont_win,
            'enemy_d_eats': enemy_d_all,
            'their_eats80': len(their_eats),
            'lost_close': lost_close,
            'depth': {b: v for b, v in depth.items()},
        })
    return out


if __name__ == '__main__':
    meta = json.load(open('/tmp/open_manifest.json'))
    seen = set()
    fs = sorted(glob.glob('/tmp/topr/*/m*.replay') + glob.glob('/tmp/ours/*.replay'))
    for f in fs:
        mid = os.path.basename(f)[1:].split('.')[0]
        if mid in seen or mid not in meta:
            continue
        seen.add(mid)
        m = dict(meta[mid]); m['id'] = mid
        try:
            for row in analyze(f, m):
                print(json.dumps(row))
        except Exception as ex:
            print('ERR', f, ex, file=sys.stderr)
