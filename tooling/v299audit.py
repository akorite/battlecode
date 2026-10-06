#!/usr/bin/env python3
"""v299 roam-leash mechanism audit (explore lane).

Per replay in a kmatch dir (files {map}-s{seed}-{na}-{nb}.replay, cand =
abyss_v299 whichever seat it sat):
  (a) distance from each of OUR dragon deaths to the team's CURRENT longest
      dragon (min tdist over its body cells) — the drop-recycle claim.
  (b) queen outcome split by whether she was the team's longest at the end /
      at her death, plus allied head density within Chebyshev 4 of her head at
      death (or r450 when she lives) — worker-density vs her-own-positioning.
  (c) loss class under the verified (queenEnd -> longest -> total) keys + elim.

Usage: v299audit.py <results_dir>   (default results/v299_audit)
"""
import sys, os, json, collections, statistics

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'handoff', 'tooling'))
sys.path.insert(0, HERE)
from parse_replay import parse
from replay_metrics import parse_map, edge_kind, D
CAND = 'abyss_v299'


def near4(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1])) <= 4


def analyze(path, fname):
    parts = fname[:-len('.replay')].split('-')
    cand_side = 'A' if parts[-2] == CAND else 'B'
    r = parse(path)
    res = r.get('result') or {}
    ev = r['events']
    W, H, dr, edges = parse_map(r['map'])

    def tdist(a, b):
        dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
        return min(dx, W - dx) + min(dy, H - dy)

    body, team = {}, {}
    for e in ev:
        if e['type'] == 'roundStart':
            break
        if e['type'] == 'dragonUpdate' and e['id'] < len(dr):
            t, b = dr[e['id']]
            body[e['id']] = collections.deque(tuple(x) for x in b)
            team[e['id']] = 'AB'[t]
    queen = {s: min((i for i in team if team[i] == s), default=-1) for s in 'AB'}

    rnd = 0
    deaths_dist = {'A': [], 'B': []}          # (dist to own longest body, len)
    queen_death = {}                           # s -> (round, reason, was_longest, allies4)
    q_cover = {'A': [], 'B': []}               # allies within 4 of queen head @r450 (or death)
    q_alive_end = {}
    q_is_longest_end = {}

    for e in ev:
        t = e['type']
        if t == 'roundStart':
            rnd = e['round']
        elif t == 'dragonUpdate':
            i = e['id']
            if i not in body:
                continue
            b = body[i]
            h, tl = tuple(e['head']), tuple(e['tail'])
            if b[0] != h:
                b.appendleft(h)
            while len(b) > 1 and b[-1] != tl:
                b.pop()
            if rnd == 450 and i == queen.get(team[i]):
                q_cover[team[i]].append(
                    sum(1 for j, bb in body.items()
                        if team[j] == team[i] and j != i and near4(bb[0], b[0])))
        elif t == 'dragonSplit':
            s = e['team']
            body[e['parentId']] = collections.deque(tuple(x) for x in e['parentBody'])
            body[e['childId']] = collections.deque(tuple(x) for x in e['childBody'])
            team[e['childId']] = s
        elif t == 'dragonDeath':
            i = e['id']
            s = team.get(i)
            if s is None or i not in body:
                continue
            head = body[i][0]
            mates = [(j, bb) for j, bb in body.items() if team[j] == s and j != i]
            if mates:
                lj, lb = max(mates, key=lambda x: len(x[1]))
                d = min(tdist(head, c) for c in lb)
                dn = min(tdist(head, bb[0]) for _, bb in mates)
                deaths_dist[s].append((d, len(body[i]), dn))
            if i == queen.get(s):
                was_long = mates and len(body[i]) >= max(len(bb) for _, bb in mates)
                allies4 = sum(1 for j, bb in mates if near4(bb[0], head))
                queen_death[s] = (rnd, e.get('reason'), bool(was_long), allies4)
                q_cover[s].append(allies4)
            body.pop(i, None)

    def qstate(s):
        q = queen.get(s, -1)
        if q in body:
            mates = [len(bb) for j, bb in body.items() if team[j] == s and j != q]
            return True, (not mates) or len(body[q]) >= max(mates), len(body[q])
        return False, False, 0

    row = {'file': fname, 'map': parts[0], 'seed': parts[1],
           'candSide': cand_side, 'end': res.get('endReason'),
           'winner': res.get('winner'), 'rounds': rnd}
    for s in 'AB':
        tr = res.get('team' + s) or {}
        alive, is_long, qlen = qstate(s)
        row[s] = {
            'qEnd': qlen if alive else 0,
            'qAlive': alive, 'qWasLongestEnd': is_long,
            'longest': tr.get('longestDragon', 0), 'total': tr.get('totalLength', 0),
            'alive': tr.get('dragonCount', 0),
            'ddist': deaths_dist[s],
            'qdeath': queen_death.get(s),
            'qCover450': (q_cover[s][-1] if q_cover[s] else None),
        }
    return row


def classify(row, s):
    o = 'AB'[1 - 'AB'.index(s)]
    if row['end'] == 'teamEliminated':
        return 'elim'
    me, th = row[s], row[o]
    for k, name in (('qEnd', 'key0-queenEnd'), ('longest', 'key1-longest'), ('total', 'key2-total')):
        if me[k] != th[k]:
            return name
    return 'draw-ish'


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'results', 'v299_audit')
    rows = []
    for f in sorted(os.listdir(os.path.join(d, 'replays'))):
        if f.endswith('.replay'):
            rows.append(analyze(os.path.join(d, 'replays', f), f))

    def agg(side_rows, key):
        vals = [x for r in side_rows for x in r[key]['ddist']]
        return vals

    cand_rows = [(r, r['candSide']) for r in rows]
    base_rows = [(r, 'AB'[1 - 'AB'.index(r['candSide'])]) for r in rows]

    print(f"games: {len(rows)}")
    cw = sum(1 for r, s in cand_rows if r['winner'] == s)
    cd = sum(1 for r, s in cand_rows if r['winner'] in (None, '', 'draw'))
    print(f"cand {cw}-{len(rows)-cw-cd}-{cd}")

    # (a) death distance to own longest body
    for label, keysel in (('cand', lambda r: r['candSide']),
                          ('base', lambda r: 'AB'[1 - 'AB'.index(r['candSide'])])):
        vals = [x[0] for r in rows for x in r[keysel(r)]['ddist']]
        lens = [x[1] for r in rows for x in r[keysel(r)]['ddist']]
        dn = [x[2] for r in rows for x in r[keysel(r)]['ddist']]
        if vals:
            print(f"(a) {label}: deaths {len(vals)}, dist-to-longest mean {statistics.mean(vals):.2f} "
                  f"med {statistics.median(vals):.1f}  <=4: {100*sum(1 for v in vals if v<=4)/len(vals):.0f}%"
                  f"  dead-len mean {statistics.mean(lens):.2f}"
                  f"  nearest-ally mean {statistics.mean(dn):.2f} med {statistics.median(dn):.1f}"
                  f" <=4: {100*sum(1 for v in dn if v<=4)/len(dn):.0f}%")

    # (b) queen survival when not longest
    for label, keysel in (('cand', lambda r: r['candSide']),
                          ('base', lambda r: 'AB'[1 - 'AB'.index(r['candSide'])])):
        nl = [r[keysel(r)] for r in rows if not r[keysel(r)]['qWasLongestEnd']]
        lv = [q for q in nl if q['qAlive']]
        dd = [q['qdeath'] for q in nl if q['qdeath']]
        cov_live = [q['qCover450'] for q in lv if q['qCover450'] is not None]
        cov_dead = [q[3] for q in dd]
        print(f"(b) {label}: queen-not-longest games {len(nl)}, survived {len(lv)}"
              f"  cover@450 live {statistics.mean(cov_live):.1f}" if cov_live else f"(b) {label}: nl {len(nl)}")
        if cov_dead:
            print(f"    cover@death dead {statistics.mean(cov_dead):.1f}  "
                  f"deaths: " + ", ".join(f"{q[0]}:{q[1]}{'L' if q[2] else ''}/a{q[3]}" for q in dd))

    # (c) residual loss classes
    cls = collections.Counter()
    for r, s in cand_rows:
        if r['winner'] != s and r['winner'] not in (None, '', 'draw'):
            cls[(classify(r, s), r['map'])] += 1
    print("(c) cand loss classes:", dict(collections.Counter(k for k, _ in cls)))
    print("    by map:", dict(cls))
    for r, s in cand_rows:
        if r['winner'] != s and r['winner'] not in (None, '', 'draw'):
            me, th = r[s], r['AB'[1 - 'AB'.index(s)]]
            print(f"    L {r['map']} {r['seed']} side{s} {r['end']}@{r['rounds']} "
                  f"qE {me['qEnd']}v{th['qEnd']} ln {me['longest']}v{th['longest']} "
                  f"tot {me['total']}v{th['total']} qdead={me['qdeath']}")


if __name__ == '__main__':
    main()
