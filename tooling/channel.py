"""Feed-channel metrics from replays: are feeders dying AT the champion head?

Per side (A/B):
  feedDeaths   non-combat deaths in the feed window (round >= feedFrom, before last 15)
               hitSelf / noValidAction = self-sacrifice deaths
  hsDie/noaDie counts by reason
  adjDrop      of those, % whose head cell was within cheb-2 of the side's
               eventual longest dragon's head THAT round (drop at the champion)
  long450      longest body len at round 450 (gate: >=40 open maps)
  leadShare    pearls eaten by the final longest dragon / pearls eaten by the side
               (feed-leader share; steering: ours 9-10%, top teams 17%)

Usage: python3 tooling/channel.py <replay> [...]   # one JSON line per game
"""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
from parse_replay import parse  # noqa: E402

FEED_FROM = 320   # feed window: feeders wake ~r330 (queenFeedRound); earlier suicides are pocket/starve deaths
CHEB = 2


def tdist(a, b, W, H):
    dx = abs(a[0] - b[0])
    dy = abs(a[1] - b[1])
    return max(min(dx, W - dx), min(dy, H - dy))


def analyze(path):
    r = parse(path)
    ev = r['events']
    W = H = 0
    for line in r['map'].split('\n'):
        p = line.split()
        if p and p[0] == 'MAP':
            W, H = int(p[1]), int(p[2])
            break
    dr = {}
    for line in r['map'].split('\n'):
        p = line.split()
        if p and p[0] == 'DRAGON':
            t, n = int(p[1]), int(p[2])
            c = list(map(int, p[3:3 + 2 * n]))
            dr[len(dr)] = (t, collections.deque((c[2 * i], c[2 * i + 1]) for i in range(n)))

    body, team = {}, {}
    for e in ev:
        if e['type'] == 'roundStart':
            break
        if e['type'] == 'dragonUpdate' and e['id'] in dr:
            t, b = dr[e['id']]
            team[e['id']] = 'AB'[t]
            body[e['id']] = b
    queen = {s: min((i for i in team if team[i] == s), default=-1) for s in 'AB'}

    # first pass: reconstruct bodies so deaths/leaders can be located
    rnd = 0
    deaths = collections.defaultdict(list)   # side -> [(round, head_cell, reason, champ_dist)]
    eaten_by = collections.Counter()
    eaten_side = collections.Counter()
    pearls, pend = set(), set()
    len450 = {'A': 0, 'B': 0}
    heads_now = collections.defaultdict(dict)  # rnd -> id -> head cell
    champ_at = collections.defaultdict(dict)   # rnd -> side -> current longest dragon id
    for e in ev:
        ty = e['type']
        if ty == 'roundStart':
            rnd = e['round']
            for s in 'AB':
                cand = [i for i in body if team[i] == s]
                # bot's champion: our queen while she lives, else the longest body
                champ_at[rnd][s] = queen[s] if queen[s] in cand else max(cand, key=lambda i: len(body[i]), default=-1)
                if rnd == 450:
                    len450[s] = max((len(body[i]) for i in cand), default=0)
        elif ty == 'tileChange':
            t = tuple(e['tile'])
            if e['hasPearl']:
                pearls.add(t)
            else:
                pearls.discard(t)
                pend.add(t)
        elif ty == 'dragonUpdate':
            i = e['id']
            if i not in body:
                continue
            b = body[i]
            h, tl = tuple(e['head']), tuple(e['tail'])
            if b and b[0] != h:
                b.appendleft(h)
                if h in pend:
                    eaten_by[i] += 1
                    eaten_side[team[i]] += 1
            heads_now[rnd][i] = h
            if not b:
                b.appendleft(h)
            pend.discard(h)
            while len(b) > 1 and b[-1] != tl:
                b.pop()
        elif ty == 'dragonSplit':
            body[e['parentId']] = collections.deque(tuple(x) for x in e['parentBody'])
            c = e['childId']
            body[c] = collections.deque(tuple(x) for x in e['childBody'])
            team[c] = e['team']
            heads_now[rnd][c] = body[c][0] if body[c] else None
        elif ty == 'dragonDeath':
            i = e['id']
            s = team.get(i)
            if s is not None and rnd >= FEED_FROM:
                h = body[i][0] if body[i] else heads_now[rnd].get(i)
                ch = champ_at[rnd].get(s, -1)
                chh = heads_now[rnd].get(ch) if ch >= 0 else None
                cd = tdist(h, chh, W, H) if (h is not None and chh is not None) else 99
                deaths[s].append((rnd, h, e['reason'], cd))
            body.pop(i, None)

    out = {'map': r.get('map', '').split('\n')[0][:40], 'seed': r.get('seed'), 'result': r.get('result')}
    final_rnd = rnd
    for s in 'AB':
        dd = deaths[s]
        sac = [d for d in dd if d[2] in ('hitSelf', 'noValidAction') and d[0] < final_rnd - 15]
        hs = sum(1 for d in sac if d[2] == 'hitSelf')
        noa = sum(1 for d in sac if d[2] == 'noValidAction')
        adj = sum(1 for d in sac if d[3] <= CHEB)
        noa_adj = sum(1 for d in sac if d[2] == 'noValidAction' and d[3] <= CHEB)
        hs_adj = sum(1 for d in sac if d[2] == 'hitSelf' and d[3] <= CHEB)
        # top-eater share: pearls eaten by the side's single biggest eater / side total
        side_eaters = {i: n for i, n in eaten_by.items() if team.get(i) == s}
        lead_eat = max(side_eaters.values(), default=0)
        tot_eat = eaten_side[s] or 1
        ts = r.get('result', {}).get('team0' if s == 'A' else 'team1', {})
        out[s] = {
            'feedDeaths': len(sac),
            'hsDie': hs,
            'noaDie': noa,
            'adjDrop%': round(100.0 * adj / len(sac), 1) if sac else None,
            'noaAdj%': round(100.0 * noa_adj / noa, 1) if noa else None,
            'hsAdj%': round(100.0 * hs_adj / hs, 1) if hs else None,
            'long450': len450[s],
            'longEnd': ts.get('longestDragon', 0),
            'leadShare': round(100.0 * lead_eat / tot_eat, 1),
            'rounds': final_rnd,
        }
    return out


if __name__ == '__main__':
    for p in sys.argv[1:]:
        try:
            print(json.dumps(analyze(p)))
        except Exception as ex:
            print(json.dumps({'file': p, 'error': str(ex)}))
