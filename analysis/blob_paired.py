"""Paired per-game winner-vs-loser cohesion comparison (blob hypothesis).

For each decisive replay: within the SAME game, compare winner-side vs
loser-side mean nearest-ally distance (nn), straggler fraction (nn>8),
and alive count, per phase bucket. Pairing controls for map and matchup;
the alive-delta column exposes the army-size confound.

Usage: source ~/.bc-env && $BC_PY analysis/blob_paired.py
"""
import sys, glob, collections, statistics
sys.path.insert(0, 'handoff/tooling'); sys.path.insert(0, 'tooling')
from parse_replay import parse
import replay_metrics as rm

def tdist(a, b, W, H):
    dx = abs(a[0] - b[0]); dx = min(dx, W - dx)
    dy = abs(a[1] - b[1]); dy = min(dy, H - dy)
    return max(dx, dy)

def per_game(path):
    r = parse(path)
    win = r['result'].get('winner')
    if win not in ('A', 'B'):
        return None
    W, H, dr, edges = rm.parse_map(r['map'])
    team = {i: ('B' if t else 'A') for i, (t, b) in enumerate(dr)}
    heads = {i: tuple(b[0]) for i, (t, b) in enumerate(dr)}
    per = {'A': collections.defaultdict(list), 'B': collections.defaultdict(list)}
    for e in r['events']:
        ty = e['type']
        if ty == 'roundStart':
            rnd = e['round']
            if rnd % 10 == 0 and rnd >= 100:
                b = 'mid' if rnd < 330 else 'late'
                for s in 'AB':
                    pts = [heads[i] for i in heads if team.get(i) == s]
                    if len(pts) >= 4:
                        nn = sorted(min(tdist(p, q, W, H) for q in pts if q != p)
                                    for p in pts)
                        per[s]['nn_' + b].append(sum(nn) / len(nn))
                        per[s]['strag_' + b].append(
                            sum(1 for x in nn if x > 8) / len(nn))
                        per[s]['alive_' + b].append(len(pts))
        elif ty == 'dragonUpdate':
            heads[e['id']] = tuple(e['head'])
        elif ty == 'dragonSplit':
            team[e['childId']] = e['team']
            heads[e['childId']] = tuple(e['childBody'][0])
            heads[e['parentId']] = tuple(e['parentBody'][0])
        elif ty == 'dragonDeath':
            heads.pop(e['id'], None)
    lose = 'A' if win == 'B' else 'B'
    row = {}
    for b in ('mid', 'late'):
        if per[win]['nn_' + b] and per[lose]['nn_' + b]:
            m = lambda s, k: sum(per[s][k + '_' + b]) / len(per[s][k + '_' + b])
            row[b + '_dnn'] = m(win, 'nn') - m(lose, 'nn')
            row[b + '_dst'] = m(win, 'strag') - m(lose, 'strag')
            row[b + '_dal'] = m(win, 'alive') - m(lose, 'alive')
    return row or None

if __name__ == '__main__':
    files = (glob.glob('top_replays/*.replay') + glob.glob('ladder_replays/*.replay')
             + glob.glob('our_replays/*.replay'))
    rows = []
    for f in files:
        try:
            row = per_game(f)
        except Exception:
            continue
        if row:
            rows.append(row)
    print('games with paired data:', len(rows))
    for b in ('mid', 'late'):
        d = [r[b + '_dnn'] for r in rows if b + '_dnn' in r]
        s = [r[b + '_dst'] for r in rows if b + '_dst' in r]
        a = [r[b + '_dal'] for r in rows if b + '_dal' in r]
        if not d:
            continue
        print(f'{b}: W-L nn mean={sum(d)/len(d):+.2f} med={statistics.median(d):+.2f} '
              f'| straggler={sum(s)/len(s):+.3f} | alive={sum(a)/len(a):+.1f}')
        tight = sum(1 for x in d if x < -0.3)
        loose = sum(1 for x in d if x > 0.3)
        print(f'   tighter>0.3: {tight} ({100*tight/len(d):.0f}%)  '
              f'looser>0.3: {loose} ({100*loose/len(d):.0f}%)')
        smallw = [r for r in rows if b + '_dal' in r and r[b + '_dal'] < -3]
        bigw = [r for r in rows if b + '_dal' in r and r[b + '_dal'] > 3]
        if smallw:
            t = sum(1 for r in smallw if r[b + '_dnn'] < 0)
            print(f'   winner-fewer-alive (n={len(smallw)}): tighter {t} ({100*t/len(smallw):.0f}%)')
        if bigw:
            t = sum(1 for r in bigw if r[b + '_dnn'] < 0)
            print(f'   winner-more-alive (n={len(bigw)}): tighter {t} ({100*t/len(bigw):.0f}%)')
