"""Conveyor geometry on top-10 replays.

Per dragonDeath in each game, for the dead dragon's team:
  (a) toroidal-chebyshev dist from its last head cell to that team's
      rolling-longest dragon's head that round
  (b) dist to nearest other alive teammate head
  (c) death reason
Reported per side (winner vs loser contrast), split by reason + era.

Plus: median round of each dragon's first split (per team), team's first-ever
split round, and queen distance-to-ally-centroid time series (eras).

Usage: python3 analysis/conveyor_geom.py
"""
import collections, glob, json, os, re, statistics, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../tooling'))
from parse_replay import parse  # noqa: E402
import replay_metrics as rm    # noqa: E402


def analyze(path, meta):
    r = parse(path)
    ev = r['events']
    W, H, dr, edges = rm.parse_map(r['map'])
    team = {i: 'AB'[t] for i, (t, b) in enumerate(dr)}
    queen = {s: min(i for i in team if team[i] == s) for s in 'AB'}

    body = {i: collections.deque(tuple(x) for x in b) for i, (t, b) in enumerate(dr)}

    def tcheb(a, b):
        dx = min(abs(a[0] - b[0]), W - abs(a[0] - b[0]))
        dy = min(abs(a[1] - b[1]), H - abs(a[1] - b[1]))
        return max(dx, dy)

    rnd = 0
    deaths = []              # (round, id, reason, team)
    first_split = {}         # parentId -> round of its first split
    team_first = {}          # team -> first split round in game
    qorbit = collections.defaultdict(list)   # team -> [(round, queen->centroid dist)]
    alive_snap = collections.defaultdict(dict)  # round -> {id: head}
    len_snap = collections.defaultdict(dict)    # round -> {id: len}

    pos = {i: body[i][0] for i in body}
    for e in ev:
        if not isinstance(e, dict):
            continue
        ty = e['type']
        if ty == 'roundStart':
            rnd = e['round']
            alive_snap[rnd] = {i: b[0] for i, b in body.items()}
            len_snap[rnd] = {i: len(b) for i, b in body.items()}
            # queen->centroid
            for s in 'AB':
                q = queen.get(s)
                hs = [b[0] for i, b in body.items() if team[i] == s]
                if q in body and hs:
                    cx = sum(h[0] for h in hs) / len(hs)
                    cy = sum(h[1] for h in hs) / len(hs)
                    qorbit[s].append((rnd, tcheb(body[q][0], (cx, cy))))
            continue
        if ty == 'dragonUpdate':
            i = e['id']
            if i not in body:
                continue
            b = body[i]
            h, tl = tuple(e['head']), tuple(e['tail'])
            if b[0] != h:
                b.appendleft(h)
                while len(b) > 1 and b[-1] != tl:
                    b.pop()
            continue
        if ty == 'dragonSplit':
            team[e['childId']] = e['team']
            body[e['parentId']] = collections.deque(tuple(x) for x in e['parentBody'])
            body[e['childId']] = collections.deque(tuple(x) for x in e['childBody'])
            p = e['parentId']
            if p not in first_split:
                first_split[p] = rnd
            team_first.setdefault(team[p], rnd)
            continue
        if ty == 'dragonDeath':
            i = e['id']
            deaths.append((rnd, i, e['reason'], team.get(i)))
            body.pop(i, None)

    # longest-dragon-per-round lookup: per round, id of team's max-length dragon
    longest = {}  # (round, team) -> (id, len)
    for rr, ls in len_snap.items():
        per = collections.defaultdict(list)
        for i, L in ls.items():
            per[team[i]].append((L, i))
        for s, xs in per.items():
            xs.sort(reverse=True)
            longest[(rr, s)] = xs[0]

    rows = []
    for (rr, i, reason, s) in deaths:
        if s is None:
            continue
        # death cell: last seen head at death round (head snapshot at roundStart;
        # better: body tracked to the moment of death isn't kept — use roundStart snapshot)
        dc = alive_snap.get(rr, {}).get(i)
        if dc is None:
            # died before first snapshot of this round: use prev round's
            dc = alive_snap.get(rr - 1, {}).get(i)
        if dc is None:
            continue
        ch = longest.get((rr, s))
        dchamp = None
        if ch and ch[1] != i and ch[1] in alive_snap.get(rr, {}):
            dchamp = tcheb(dc, alive_snap[rr][ch[1]])
        dnear = None
        for j, hj in alive_snap.get(rr, {}).items():
            if j != i and team.get(j) == s:
                d = tcheb(dc, hj)
                dnear = d if dnear is None else min(dnear, d)
        rows.append({'mid': re.search(r'm(\d+)', path).group(1), 'rnd': rr, 'id': i,
                     'team': s, 'reason': reason, 'dChamp': dchamp, 'dAlly': dnear,
                     'won': meta['winner'].lower() == s.lower(),
                     'champLen': ch[0] if ch else None})
    return {'rows': rows, 'first_split': first_split, 'team': team,
            'team_first': team_first, 'qorbit': dict(qorbit),
            'map': meta['map'], 'winner': meta['winner'], 'aName': meta['a']['name'], 'bName': meta['b']['name']}


def era(rr):
    return 'r0-99' if rr < 100 else 'r100-199' if rr < 200 else 'r200-299' if rr < 300 else 'r300-399' if rr < 400 else 'r400+'


def ring(d):
    if d is None:
        return '?'
    return 'ring<=2' if d <= 2 else 'ring3-5' if d <= 5 else 'far6-10' if d <= 10 else 'diffuse>10'


def main():
    games = []
    for f in sorted(glob.glob('toptop_replays/*.replay')):
        mp = f.replace('.replay', '.json')
        meta = json.load(open(mp))
        meta.setdefault('winner', meta.get('winner', ''))
        try:
            games.append(analyze(f, meta))
        except Exception as ex:
            print(f, 'FAIL', repr(ex)[:120])

    allrows = [r for g in games for r in g['rows']]
    print(f'games={len(games)} deaths={len(allrows)}')
    for g in games[:20]:
        print(f"  {g['map']:<14} {g['aName']} v {g['bName']} w:{g['winner']}")

    print('\n== death distance to CHAMP head (winner side vs loser side) ==')
    for won in (True, False):
        sel = [r['dChamp'] for r in allrows if r['won'] == won and r['dChamp'] is not None]
        if not sel:
            continue
        rings = collections.Counter(ring(d) for d in sel)
        n = len(sel)
        print(f"  {'WINNER' if won else 'LOSER'}: n={n} med={statistics.median(sel)} mean={statistics.mean(sel):.1f} | "
              + ' '.join(f'{k}={v/n:.2f}' for k, v in rings.most_common()))

    print('\n== by era (winner side) ==')
    for e_ in ('r0-99', 'r100-199', 'r200-299', 'r300-399', 'r400+'):
        sel = [r['dChamp'] for r in allrows if r['won'] and era(r['rnd']) == e_ and r['dChamp'] is not None]
        if sel:
            rings = collections.Counter(ring(d) for d in sel)
            n = len(sel)
            print(f'  {e_}: n={n} med={statistics.median(sel)} | ' + ' '.join(f'{k}={v/n:.2f}' for k, v in rings.most_common()))

    print('\n== by reason x side ==')
    for won in (True, False):
        for rs in ('noValidAction', 'hitHeadToHead', 'hitOtherBody', 'hitWall', 'hitSelf'):
            sel = [r for r in allrows if r['won'] == won and r['reason'] == rs and r['dChamp'] is not None]
            if len(sel) >= 10:
                dc = [r['dChamp'] for r in sel]
                da = [r['dAlly'] for r in sel if r['dAlly'] is not None]
                print(f"  {'W' if won else 'L'} {rs:<15} n={len(sel):<4} dChamp med={statistics.median(dc):>4} | dAlly med={statistics.median(da):>4}")

    print('\n== distance to nearest ally (all deaths) ==')
    for won in (True, False):
        sel = [r['dAlly'] for r in allrows if r['won'] == won and r['dAlly'] is not None]
        if sel:
            print(f"  {'W' if won else 'L'}: n={len(sel)} med={statistics.median(sel)} mean={statistics.mean(sel):.1f} "
                  f"<=2: {sum(1 for d in sel if d<=2)/len(sel):.2f} <=5: {sum(1 for d in sel if d<=5)/len(sel):.2f}")

    print('\n== first split ==')
    per_side = collections.defaultdict(list)
    teamfirst = collections.defaultdict(dict)
    for gi, g in enumerate(games):
        for pid, rr in g['first_split'].items():
            s = g['team'][pid]
            won = g['winner'].lower() == s.lower()
            per_side[won].append(rr)
        for s, rr in g['team_first'].items():
            won = g['winner'].lower() == s.lower()
            teamfirst[won].setdefault(gi, rr)
    for won in (True, False):
        v = per_side[won]
        if v:
            print(f"  {'W' if won else 'L'}: median first-split round per dragon={statistics.median(v)} (n={len(v)})")
        tf = teamfirst[won]
        if tf:
            print(f"  {'W' if won else 'L'}: median team's first split in game={statistics.median(tf.values())} (n={len(tf)})")

    print('\n== queen -> ally centroid distance by era (winner vs loser sides) ==')
    qagg = collections.defaultdict(list)
    for g in games:
        for s, traj in g['qorbit'].items():
            won = g['winner'].lower() == s.lower()
            for rr, d in traj:
                qagg[(won, era(rr))].append(d)
    for won in (True, False):
        for e_ in ('r0-99', 'r100-199', 'r200-299', 'r300-399', 'r400+'):
            v = qagg.get((won, e_))
            if v:
                print(f"  {'W' if won else 'L'} {e_}: n={len(v)} med={statistics.median(v):.1f} mean={statistics.mean(v):.1f}")


if __name__ == '__main__':
    main()
