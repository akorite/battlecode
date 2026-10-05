"""Colony-blob hypothesis: do winners fight as a more compact swarm?

Per replay, per round, per team: median pairwise chebyshev (torus) between
alive same-team dragons, mean distance to team centroid (torus circular mean),
and death locations split by distance to own centroid (<=10 vs >10).

Cohorts: winner-side vs loser-side (result.winner). Buckets: early <120,
mid 120-330, late 330+.

Usage: python3 analysis/blob_study.py [glob ...]
"""
import collections, glob, json, math, os, random, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../tooling'))
from parse_replay import parse  # noqa: E402
import replay_metrics as rm      # noqa: E402

random.seed(7)


def tdist(a, b, W, H):
    dx = abs(a[0] - b[0]); dx = min(dx, W - dx)
    dy = abs(a[1] - b[1]); dy = min(dy, H - dy)
    return dx + dy


def torus_centroid(pts, W, H):
    sx = sy = cx = cy = 0.0
    for x, y in pts:
        tx = 2 * math.pi * x / W
        ty = 2 * math.pi * y / H
        sx += math.cos(tx); cx += math.sin(tx)
        sy += math.cos(ty); cy += math.sin(ty)
    n = max(1, len(pts))
    ax = (math.atan2(cx / n, sx / n) % (2 * math.pi)) * W / (2 * math.pi)
    ay = (math.atan2(cy / n, sy / n) % (2 * math.pi)) * H / (2 * math.pi)
    return (ax, ay)


def bucket(rnd):
    return 'early' if rnd < 120 else ('mid' if rnd < 330 else 'late')


def analyze(path):
    """-> {side -> {'med': {bucket: [vals]}, 'cen': {bucket: [vals]},
                    'near': int, 'far': int, 'alive': {bucket: [n]}}}"""
    r = parse(path)
    W, H, dr, edges = rm.parse_map(r['map'])
    team = {}
    heads = {}
    for i, (t, body) in enumerate(dr):
        team[i] = 'AB'[t]
        heads[i] = tuple(body[0])
    rnd = -1
    last_head = dict(heads)
    out = {s: {'med': collections.defaultdict(list),
               'cen': collections.defaultdict(list),
               'alive': collections.defaultdict(list),
               'nn': collections.defaultdict(list),
               'near': 0, 'far': 0} for s in 'AB'}
    cen = {s: None for s in 'AB'}
    for e in r['events']:
        ty = e['type']
        if ty == 'roundStart':
            rnd = e['round']
            b = bucket(rnd)
            for s in 'AB':
                pts = [heads[i] for i in heads if team.get(i) == s]
                if len(pts) < 2:
                    continue
                cen[s] = torus_centroid(pts, W, H)
                # pairwise: full if small, sample if large
                pairs = []
                if len(pts) <= 22:
                    for i in range(len(pts)):
                        for j in range(i + 1, len(pts)):
                            pairs.append(tdist(pts[i], pts[j], W, H))
                else:
                    for _ in range(400):
                        a, c = random.sample(pts, 2)
                        pairs.append(tdist(a, c, W, H))
                pairs.sort()
                out[s]['med'][b].append(pairs[len(pairs) // 2])
                out[s]['cen'][b].append(sum(tdist(p, cen[s], W, H) for p in pts) / len(pts))
                nn = sorted(min(tdist(p, q, W, H) for q in pts if q != p) for p in pts)
                out[s]['nn'][b].append(nn[len(nn) // 2])
                out[s]['alive'][b].append(len(pts))
        elif ty == 'dragonUpdate':
            heads[e['id']] = tuple(e['head'])
            last_head[e['id']] = tuple(e['head'])
        elif ty == 'dragonSplit':
            team[e['childId']] = e['team']
            heads[e['childId']] = tuple(e['childBody'][0])
            last_head[e['childId']] = tuple(e['childBody'][0])
            heads[e['parentId']] = tuple(e['parentBody'][0])
        elif ty == 'dragonDeath':
            s = team.get(e['id'])
            heads.pop(e['id'], None)
            if s and cen.get(s) is not None and e['id'] in last_head:
                d = tdist(last_head[e['id']], cen[s], W, H)
                if d <= 10:
                    out[s]['near'] += 1
                else:
                    out[s]['far'] += 1
    return out, (r['result'] or {}).get('winner'), r.get('botA'), r.get('botB')


def merge(acc, per):
    for s, d in per.items():
        for k in ('med', 'cen', 'alive'):
            for b, vals in d[k].items():
                acc[s][k][b].extend(vals)
        acc[s]['near'] += d['near']
        acc[s]['far'] += d['far']


def report(name, acc):
    print(f'\n=== {name} ===')
    for b in ('early', 'mid', 'late'):
        for s in ('W', 'L'):
            key = 'winner' if s == 'W' else 'loser'
            med = acc[key]['med'][b]; cen = acc[key]['cen'][b]; alv = acc[key]['alive'][b]
            nn = acc[key]['nn'][b]
            if not med:
                continue
            med.sort(); cen.sort(); nn.sort()
            print(f'  {b:5s} {key}: medPair={med[len(med)//2]:.1f} cenDist={cen[len(cen)//2]:.1f} '
                  f'nn={nn[len(nn)//2]:.1f}/{sum(nn)/len(nn):.1f} alive~{sum(alv)/len(alv):.0f} (n={len(med)})')
    for s, key in (('W', 'winner'), ('L', 'loser')):
        n = acc[key]['near']; f = acc[key]['far']
        if n + f:
            print(f'  deaths near-centroid(<=10): {key} {n}/{n+f} = {100*n/(n+f):.0f}%  far={f}')


def blank():
    return {'med': collections.defaultdict(list), 'cen': collections.defaultdict(list),
            'alive': collections.defaultdict(list), 'nn': collections.defaultdict(list),
            'near': 0, 'far': 0}


def main():
    W_ = {'winner': blank(), 'loser': blank()}
    ours = {'winner': blank(), 'loser': blank()}
    n = draws = 0
    for f in sorted(glob.glob('top_replays/*.replay') + glob.glob('ladder_replays/*.replay') + glob.glob('our_replays/*.replay')):
        try:
            per, win, ba, bb = analyze(f)
        except Exception as ex:
            print('ERR', f, ex)
            continue
        n += 1
        if win not in 'AB':
            draws += 1
            continue
        dst = ours if ('351' in (ba or '') or '351' in (bb or '')) else W_
        for s in 'AB':
            key = 'winner' if s == win else 'loser'
            for k in ('med', 'cen', 'nn', 'alive'):
                for b, vals in per[s][k].items():
                    dst[key][k][b].extend(vals)
            dst[key]['near'] += per[s]['near']
            dst[key]['far'] += per[s]['far']
    print(f'games={n} draws={draws}')
    report('non-351 games: winner-side vs loser-side', W_)
    report('team-351 games: winner vs loser side', ours)


if __name__ == '__main__':
    main()
