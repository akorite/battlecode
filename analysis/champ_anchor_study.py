"""Champion anchoring study: where do winners' champs sit + where do feeders die.

Per replay+side: champ = longest-bodied dragon at end (queen excluded, reported
separately when queen IS the longest). Anchor = median head cell over r330+.
Territory = dist(anchor, own queen start) vs dist(anchor, enemy queen start) vs
dist to map center. Die-in-place radius = dist(dead head, anchor) per non-queen
death, split by reason.
"""
import collections, glob, json, os, re, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../tooling'))
from parse_replay import parse  # noqa: E402
import replay_metrics as rm      # noqa: E402


def tdist(a, b, W, H):
    dx = abs(a[0] - b[0]); dx = min(dx, W - dx)
    dy = abs(a[1] - b[1]); dy = min(dy, H - dy)
    return dx + dy


def med(points):
    xs = sorted(p[0] for p in points); ys = sorted(p[1] for p in points)
    n = len(points)
    return (xs[n // 2], ys[n // 2]) if n else None


def quant(v, qs):
    v = sorted(v)
    if not v:
        return {q: None for q in qs}
    return {q: v[min(len(v) - 1, int(q * len(v)))] for q in qs}


def analyze(path):
    r = parse(path)
    W, H, dr, edges = rm.parse_map(r['map'])
    team, body = {}, {}
    for i, (t, b) in enumerate(dr):
        team[i] = 'AB'[t]
        body[i] = collections.deque(tuple(x) for x in b)
    queen = {s: min((i for i in team if team[i] == s), default=-1) for s in 'AB'}
    qstart = {s: tuple(dr[queen[s]][1][0]) if queen[s] >= 0 else None for s in 'AB'}

    heads_at = collections.defaultdict(dict)      # rnd -> {id: head}
    lens_at = collections.defaultdict(dict)       # rnd -> {id: len}
    deaths = []                                    # (rnd, id, reason, cell)
    rnd = 0
    for e in r['events']:
        ty = e['type']
        if ty == 'roundStart':
            rnd = e['round']
            heads_at[rnd] = {i: body[i][0] for i in body}
            lens_at[rnd] = {i: len(body[i]) for i in body}
        elif ty == 'dragonUpdate':
            i = e['id']
            if i not in body:
                continue
            b = body[i]
            h, tl = tuple(e['head']), tuple(e['tail'])
            if b[0] != h:
                b.appendleft(h)
            while len(b) > 1 and b[-1] != tl:
                b.pop()
        elif ty == 'dragonSplit':
            body[e['parentId']] = collections.deque(tuple(x) for x in e['parentBody'])
            body[e['childId']] = collections.deque(tuple(x) for x in e['childBody'])
            team[e['childId']] = e['team']
        elif ty == 'dragonDeath':
            i = e['id']
            if i in body:
                deaths.append((rnd, i, e['reason'], body[i][0], team.get(i)))
            body.pop(i, None)

    res = r['result'] or {}
    out = {}
    out['_lens'] = lens_at; out['_heads'] = heads_at
    for s in 'AB':
        # champ = longest non-queen dragon alive at end; if none, longest seen late
        cand = [(len(body[i]), i) for i in body if team.get(i) == s and i != queen[s]]
        qend = len(body[queen[s]]) if queen[s] in body and queen[s] >= 0 else 0
        if cand:
            L, champ = max(cand)
        else:
            champ, L = -1, 0
        # anchor = median head over r>=330 (use last seen rounds if dead early)
        cpos = {rr: heads_at[rr][champ] for rr in sorted(heads_at) if champ in heads_at[rr]}
        pts = [p for rr, p in cpos.items() if rr >= 330]
        anchor = med(pts)
        # fallback: median over all rounds seen
        if anchor is None and champ >= 0:
            pts = list(cpos.values())
            anchor = med(pts)
        out[s] = {'champ': champ, 'champLen': L, 'queenEndLen': qend,
                  'queenIsChamp': qend >= L, 'anchor': anchor, 'anchorRounds': len(pts),
                  'deaths': [d for d in deaths if d[4] == s],
                  'cpos': cpos, 'cpts': pts,
                  'qpos': {rr: heads_at[rr].get(queen[s]) for rr in sorted(heads_at)},
                  '_qid': queen[s],
                  'lens': lens_at, 'heads': heads_at,
                  'team': s}
    out['_team'] = team
    return {'W': W, 'H': H, 'out': out, 'winner': res.get('winner'), 'map':
            (re.search(r'MAP_NAME (.+)', r['map']).group(1) if re.search(r'MAP_NAME (.+)', r['map']) else '?'),
            'qstart': qstart}


def main():
    sides = {}
    for t in [264, 306, 91, 213]:
        for line in open(f'/tmp/matches_{t}.jsonl'):
            m = json.loads(line)
            slot = 'A' if m['a']['id'] == t else 'B'
            sides[m['id']] = (slot, m['winner'].upper() == slot)
    our = {}
    for line in open('/tmp/matches_351.jsonl'):
        m = json.loads(line)
        slot = 'A' if m['a']['id'] == 351 else 'B'
        our[m['id']] = (slot, m['winner'].upper() == slot)

    C = {'top': collections.defaultdict(list), 'our': collections.defaultdict(list),
         'ourw': collections.defaultdict(list)}

    def record(key, a, s):
        o = a['out'][s]
        if o['anchor'] is None:
            return
        W, H = a['W'], a['H']
        anchor = o['anchor']
        qs, eq = a['qstart'][s], a['qstart']['AB'[1 - 'AB'.index(s)]]
        # queen's late position vs anchor
        qpts = [p for rr, p in o['qpos'].items() if p and rr >= 330]
        if qpts:
            qmed = med(qpts)
            C[key]['anch_qmed'].append(tdist(anchor, qmed, W, H))
        C[key]['anch_qs'].append(tdist(anchor, qs, W, H) if qs else None)
        C[key]['anch_eqs'].append(tdist(anchor, eq, W, H) if eq else None)
        C[key]['anch_ctr'].append(tdist(anchor, (W // 2, H // 2), W, H))
        C[key]['champLen'].append(o['champLen'])
        C[key]['qIsChamp'].append(1 if o['queenIsChamp'] else 0)
        # champ roaming spread: median dist of its head samples to the anchor
        if o['cpts']:
            C[key]['spread'].append(sorted(tdist(p, anchor, W, H) for p in o['cpts'])[len(o['cpts'])//2])
        for (rnd, i, reason, cell, _t) in o['deaths']:
            if i == o['champ'] or rnd < 200:
                continue
            C[key]['die_' + reason].append(tdist(cell, anchor, W, H))
            C[key]['die_all'].append(tdist(cell, anchor, W, H))
            # distance to champ's head AT the death round, and to its path window +-4
            ch = o['cpos'].get(rnd)
            if ch is not None:
                C[key]['dhead_' + reason].append(tdist(cell, ch, W, H))
                C[key]['dhead_all'].append(tdist(cell, ch, W, H))
            near = min((tdist(cell, p, W, H) for rr, p in o['cpos'].items() if abs(rr - rnd) <= 4), default=None)
            if near is not None:
                C[key]['dpath_' + reason].append(near)
                C[key]['dpath_all'].append(near)
            # distance to CURRENT longest non-queen dragon's head at death round
            L = a['out']['_lens'].get(rnd, {})
            H2 = a['out']['_heads'].get(rnd, {})
            tm = a['out']['_team']
            ownL = [(v, i) for i, v in L.items() if tm.get(i) == s and i != o.get('_qid', -99)]
            if ownL:
                tgt = max(ownL)[1]
                if tgt in H2:
                    C[key]['dtgt_' + reason].append(tdist(cell, H2[tgt], W, H))
            # own-team head centroid at death round
            own = [p for i, p in H2.items() if tm.get(i) == s]
            if own:
                cx = sum(p[0] for p in own) / len(own); cy = sum(p[1] for p in own) / len(own)
                C[key]['dctr_' + reason].append(tdist(cell, (round(cx), round(cy)), W, H))

    for f in sorted(glob.glob('top_replays/*.replay')):
        mid = int(re.search(r'm(\d+)\.replay', f).group(1))
        if mid not in sides:
            continue
        try:
            a = analyze(f)
        except Exception as ex:
            print('ERR', f, ex); continue
        if a['map'] not in ('Autarky', 'Around UNSW', 'Big Empty', 'Schooltime', 'Islands', 'Australia'):
            continue
        record('top', a, sides[mid][0])
    for f in sorted(glob.glob('our_replays/*.replay')):
        mid = int(re.search(r'm(\d+)\.replay', f).group(1))
        if mid not in our:
            continue
        try:
            a = analyze(f)
        except Exception as ex:
            print('ERR', f, ex); continue
        record('ourw' if our[mid][1] else 'our', a, our[mid][0])

    for k in C:
        c = C[k]
        print(f'== {k} ({len(c["champLen"])} games) ==')
        print('  champLen  p25/p50/p75:', quant(c['champLen'], [.25, .5, .75]))
        print('  queenIsChamp frac:', round(sum(c['qIsChamp']) / max(1, len(c['qIsChamp'])), 2))
        print('  anchor->ownQstart:', quant(c['anch_qs'], [.25, .5, .75]))
        print('  anchor->enemyQstart:', quant(c['anch_eqs'], [.5]))
        print('  anchor->center:', quant(c['anch_ctr'], [.25, .5, .75]))
        print('  champ spread (r330+ head vs anchor):', quant(c['spread'], [.25, .5, .75]))
        print('  anchor->queenLateMedian:', quant(c['anch_qmed'], [.25, .5, .75]))
        for reason in ['noValidAction', 'hitSelf', 'hitHeadToHead', 'all']:
            v = c['die_' + reason]
            print(f'  die r>=200 {reason} ->anchor: n={len(v)}', quant(v, [.5, .9]))
            v = c['dhead_' + reason]
            print(f'    same-round ->champHead: n={len(v)}', quant(v, [.25, .5, .9]))
            v = c['dpath_' + reason]
            print(f'    +-4r window ->champPath: n={len(v)}', quant(v, [.25, .5, .9]))
            v = c['dtgt_' + reason]
            print(f'    ->currentLongest@round: n={len(v)}', quant(v, [.25, .5, .9]))
            v = c['dctr_' + reason]
            print(f'    ->ownCentroid@round: n={len(v)}', quant(v, [.25, .5, .9]))


if __name__ == '__main__':
    main()
