"""Early-race mechanics census r0-60 on top-team ladder replays.

Per top-team side per game:
  - splits by round 15/30/60 (cumulative)
  - at each dragonSplit: parent pre-split len (= len(parentBody)+len(childBody)),
    parent post len, child len
  - distance-to-spawn over time: for each unit, tcheb(head, own_birth_cell)
    and tcheb(head, team_origin = nearest initial-dragon head) per round,
    bucketed r1-15/16-30/31-45/46-60

Manifest /tmp/topr/manifest.json maps match_id -> {a,b,map,winner,teams}.
Replays: /tmp/topr/<teamid>/m<id>.replay (dedup by match id).
"""
import sys, os, glob, json, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
from parse_replay import parse
from pocket_metric import parse_map


def tcheb(W, H, a, b):
    dx = abs(a[0] - b[0]); dy = abs(a[1] - b[1])
    return max(min(dx, W - dx), min(dy, H - dy))


def analyze(path, meta, want_teams):
    r = parse(path)
    res = r.get('result') or {}
    W, H, dr, _ = parse_map(r['map'])
    rnd_events = sum(1 for e in r['events'] if e['type'] == 'roundStart')
    team = {i: 'AB'[t] for i, (t, _b) in enumerate(dr)}
    init_head = collections.defaultdict(list)   # side -> [initial heads]
    for i, (t, body) in enumerate(dr):
        init_head['AB'[t]].append(tuple(body[0]))

    hist = collections.defaultdict(dict)
    born, died, own_spawn = {}, {}, {}
    rnd = 0
    splits = []
    for e in r['events']:
        ty = e['type']
        if ty == 'roundStart':
            rnd += 1
        elif ty == 'dragonUpdate':
            i = e['id']
            born.setdefault(i, 0)
            own_spawn.setdefault(i, tuple(e['head']) if rnd <= 1 else own_spawn.get(i))
            hist[i][rnd] = tuple(e['head'])
        elif ty == 'dragonSplit':
            team[e['childId']] = e['team']
            born[e['childId']] = rnd
            pb = e['parentBody']; cb = e['childBody']
            own_spawn[e['childId']] = tuple(cb[0])
            hist[e['childId']][rnd] = tuple(cb[0])
            hist[e['parentId']][rnd] = tuple(pb[0])
            splits.append({'round': rnd, 'team': e['team'],
                           'parent_pre': len(pb) + len(cb), 'parent_post': len(pb),
                           'child_len': len(cb)})
        elif ty == 'dragonDeath':
            died[e['id']] = rnd

    harr = {}
    for i, h in hist.items():
        arr = [None] * (rnd_events + 1)
        last = None
        for rr in range(1, rnd_events + 1):
            if rr in h:
                last = h[rr]
            arr[rr] = last
        harr[i] = arr

    out = []
    for side in 'AB':
        tid = meta.get('a' if side == 'A' else 'b')
        if tid not in want_teams:
            continue
        ids = [i for i, t in team.items() if t == side]
        sp = [s for s in splits if s['team'] == side and s['round'] <= 60]
        d_own = collections.defaultdict(list)   # bin -> [d]
        d_org = collections.defaultdict(list)
        for rr in range(1, min(60, rnd_events) + 1):
            b = (rr - 1) // 15
            for i in ids:
                if not (born.get(i, 1 << 30) <= rr < died.get(i, 1 << 30)):
                    continue
                h = harr[i][rr] if rr <= rnd_events else None
                if h is None:
                    continue
                if own_spawn.get(i):
                    d_own[b].append(tcheb(W, H, h, own_spawn[i]))
                if init_head[side]:
                    d_org[b].append(min(tcheb(W, H, h, c) for c in init_head[side]))
        out.append({
            'team_id': tid, 'side': side, 'won': res.get('winner') == side,
            'rounds': rnd_events, 'map': meta.get('map'),
            'splits_15': sum(1 for s in sp if s['round'] <= 15),
            'splits_30': sum(1 for s in sp if s['round'] <= 30),
            'splits_60': sum(1 for s in sp if s['round'] <= 60),
            'parent_pre': [s['parent_pre'] for s in sp],
            'child_len': [s['child_len'] for s in sp],
            'split_rounds': [s['round'] for s in sp],
            'd_own': {b: v for b, v in d_own.items()},
            'd_org': {b: v for b, v in d_org.items()},
            'units60': [i for i in ids if born.get(i, 1 << 30) <= 60],
        })
    return out


if __name__ == '__main__':
    meta = json.load(open('/tmp/topr/manifest.json'))
    top = {454, 157, 306, 545, 70, 55, 264, 213, 552, 91}
    names = {v.get('a'): v.get('an') for k, v in meta.items()}
    names.update({v.get('b'): v.get('bn') for k, v in meta.items()})
    names.update({454: 'aAah', 157: 'larp', 306: 'Cultery', 545: 'devtest', 70: 'chadgdp',
                  55: 'hieroglyph', 264: 'forgot', 213: 'Sponge', 552: 'fandagong', 91: 'SSS'})
    seen = set()
    for f in sorted(glob.glob('/tmp/topr/*/m*.replay')):
        mid = os.path.basename(f)[1:].split('.')[0]
        if mid in seen:
            continue
        seen.add(mid)
        m = meta.get(mid, {})
        try:
            for row in analyze(f, m, top):
                row['match'] = mid
                row['team_name'] = names.get(row['team_id'], str(row['team_id']))
                row['units60'] = len(row['units60'])
                print(json.dumps(row))
        except Exception as ex:
            print('ERR', f, ex, file=sys.stderr)
