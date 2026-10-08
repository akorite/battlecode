#!/usr/bin/env python3
"""Combat mechanics forensics (explore lane) — top-team replays.

Per replay:
 (1) h2h engagements: initiator (the mover whose action path ends on an enemy
     head), initiator len vs victim len, round, initiator survives? (engine
     kills both on head-collision — verified per event stream), who wins game.
 (2) escort formations: every 25r, allies within Chebyshev 3 of queen head and
     of longest dragon's head: count + relative offset histogram.
 (3) multi-step actions: move steps >=2, classified by terminal outcome —
     ends on enemy head (hunt kill), ends on pearl tile (forage), starts
     adjacent to enemy head moving away (escape), else transit.
 (4) torus wraps: |raw dx|>1 or |dy|>1 between consecutive head updates per
     step; wrap-involved kills.

Usage: combatforensics.py <replay_dir> [--ours-side file-with-side-map]
"""
import sys, os, collections, statistics

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'handoff', 'tooling'))
sys.path.insert(0, HERE)
from parse_replay import parse
from replay_metrics import parse_map, edge_kind, D

DIRV = {'N': (0, -1), 'E': (1, 0), 'S': (0, 1), 'W': (-1, 0)}


def analyze(path):
    r = parse(path)
    res = r.get('result') or {}
    ev = r['events']
    W, H, dr, edges = parse_map(r['map'])

    def cheb(a, b):
        dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
        return max(min(dx, W - dx), min(dy, H - dy))

    body, team = {}, {}
    for e in ev:
        if e['type'] == 'roundStart':
            break
        if e['type'] == 'dragonUpdate' and e['id'] < len(dr):
            t, b = dr[e['id']]
            team[e['id']] = 'AB'[t]
            body[e['id']] = collections.deque(tuple(x) for x in b)
    queen = {s: min((i for i in team if team[i] == s), default=-1) for s in 'AB'}

    rnd = 0
    heads_snap = {}          # heads at roundStart
    action_of = {}           # id -> action this turn
    h2h = []                 # (init side, init len, victim len, rnd, bothDie, initWrap)
    multistep = collections.Counter()
    wraps = {'A': 0, 'B': 0, 'kill': 0, 'mswrap': 0}
    esc_queen = {'A': [], 'B': []}
    esc_long = {'A': [], 'B': []}
    esc_shape = {'A': collections.Counter(), 'B': collections.Counter()}
    winner = res.get('winner')

    def classify_ms(i, path_end, start, s, heads0):
        # heads0 = heads at roundStart {id: (cell, len)}
        if path_end is None:
            return 'other'
        if any(cheb(path_end, hh) == 0 and team.get(j, '') != s
               for j, hh in heads0.items()):
            return 'hunt'
        adj0 = any(cheb(start, hh) <= 1 and team.get(j, '') != s
                   for j, hh in heads0.items())
        if adj0 and not any(cheb(path_end, hh) <= 1 and team.get(j, '') != s
                            for j, hh in heads0.items()):
            return 'escape'
        return 'transit'

    for e in ev:
        t = e['type']
        if t == 'roundStart':
            rnd = e['round']
            heads_snap = {i: body[i][0] for i in body}
            # escort sampling
            if rnd % 25 == 0:
                for s in 'AB':
                    q = queen.get(s, -1)
                    if q in body:
                        al = [(j, bb[0]) for j, bb in body.items() if team[j] == s and j != q]
                        near = [h for _, h in al if cheb(h, body[q][0]) <= 3]
                        esc_queen[s].append(len(near))
                        for h in near:
                            dx = h[0] - body[q][0][0]
                            dy = h[1] - body[q][0][1]
                            if dx > W // 2: dx -= W
                            if dx < -W // 2: dx += W
                            if dy > H // 2: dy -= H
                            if dy < -H // 2: dy += H
                            esc_shape[s][(max(-1, min(1, dx)), max(-1, min(1, dy)))] += 1
                    mates = [(j, bb) for j, bb in body.items() if team[j] == s]
                    if mates:
                        lj, lb = max(mates, key=lambda x: len(x[1]))
                        esc_long[s].append(sum(1 for j, bb in mates
                                               if j != lj and cheb(bb[0], lb[0]) <= 3))
        elif t == 'dragonAction':
            i = e['id']
            if e.get('action', {}).get('kind') == 'move':
                steps = e['action']['steps']
                if len(steps) >= 2:
                    s = team.get(i)
                    start = heads_snap.get(i, body[i][0] if i in body else None)
                    # compute path end with wrap math
                    c = start
                    wrapped = False
                    for st in steps:
                        dx, dy = DIRV[st]
                        nx, ny = c[0] + dx, c[1] + dy
                        if nx < 0 or nx >= W or ny < 0 or ny >= H:
                            wrapped = True
                        c = (nx % W, ny % H)
                    k = classify_ms(i, c, start, s, heads_snap)
                    multistep[(s == winner, k)] += 1
                    if wrapped:
                        wraps['mswrap'] += 1
                    action_of[i] = ('move', steps, wrapped, c)
                else:
                    action_of[i] = ('move', e['action']['steps'], False, None)
            elif e.get('action'):
                action_of[i] = (e['action']['kind'], None, False, None)
        elif t == 'dragonUpdate':
            i = e['id']
            if i not in body:
                continue
            b = body[i]
            h, tl = tuple(e['head']), tuple(e['tail'])
            prev = heads_snap.get(i)
            if prev is not None:
                raw = (h[0] - prev[0], h[1] - prev[1])
                if abs(raw[0]) > 1 or abs(raw[1]) > 1:
                    s = team.get(i)
                    if s:
                        wraps[s] += 1
            if b[0] != h:
                b.appendleft(h)
            while len(b) > 1 and b[-1] != tl:
                b.pop()
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
            if e['reason'] == 'hitHeadToHead':
                # initiator = the dead one who moved onto an enemy head this turn;
                # victim = enemy whose head sat on the same cell at roundStart
                myh = heads_snap.get(i, body[i][0])
                act = action_of.get(i)
                init, vic = i, None
                # if I didn't move, the OTHER dead dragon initiated into me
                if act is None or act[0] != 'move':
                    # find enemy dead/moved into my head
                    for j, hh in heads_snap.items():
                        if team.get(j) != s:
                            a2 = action_of.get(j)
                            if a2 and a2[0] == 'move' and a2[3] == myh:
                                init, vic = j, i
                                break
                else:
                    for j, hh in heads_snap.items():
                        if team.get(j) != s and hh == (act[3] if act[3] else myh):
                            vic = j
                            break
                il = len(body[init]) if init in body else -1
                vl = len(body[vic]) if vic in body else -1
                h2h.append((team.get(init), il, vl, rnd,
                            act and act[2] if init == i else None))
                if vic is not None and vic in body and vic != i:
                    pass  # victim death event arrives separately
            body.pop(i, None)

    return {'file': os.path.basename(path), 'winner': winner, 'h2h': h2h,
            'multistep': multistep, 'wraps': wraps, 'escQueen': esc_queen,
            'escLong': esc_long, 'escShape': esc_shape, 'end': res.get('endReason')}


def main():
    d = sys.argv[1]
    rows = []
    for f in sorted(os.listdir(d)):
        if f.endswith('.replay'):
            try:
                rows.append(analyze(os.path.join(d, f)))
            except Exception as ex:
                print('ERR', f, ex)
    print('games:', len(rows))

    # (1) h2h
    allh = [h for r in rows for h in r['h2h']]
    lw = [h for r in rows for h in r['h2h'] if h[0] == r['winner']]
    ll = [h for r in rows for h in r['h2h'] if r['winner'] in ('A', 'B') and h[0] != r['winner']]
    def ratio(h):
        i, v = h[1], h[2]
        return round(i / v, 2) if v > 0 else -1
    for tag, hs in (('winner-side', lw), ('loser-side', ll)):
        if not hs: continue
        rs = [ratio(h) for h in hs if h[2] > 0]
        print(f"(1) {tag} h2h initiations {len(hs)}: init/vic len ratio "
              f"mean {statistics.mean(rs):.2f} med {statistics.median(rs)}; "
              f"init>=vic {100*sum(1 for x in rs if x>=1)/len(rs):.0f}%, "
              f"init<0.5*vic {100*sum(1 for x in rs if x<0.5)/len(rs):.0f}%")
    # (3) multistep
    ms = collections.Counter()
    for r in rows: ms.update(r['multistep'])
    print('(3) multistep (won?,class):', dict(ms))
    # (4) wraps
    wa, wb, wm = 0, 0, 0
    for r in rows:
        wa += r['wraps']['A']; wb += r['wraps']['B']; wm += r['wraps']['mswrap']
    wkills = sum(1 for r in rows for h in r['h2h'] if h[4])
    print(f"(4) wrap steps: A {wa} B {wb} (multistep-wraps {wm}), wrap-h2h-initiations {wkills}")
    # (2) escorts
    for name, key in (('queen', 'escQueen'), ('longest', 'escLong')):
        for s in 'AB':
            vals = [x for r in rows if r['winner'] == s for x in r[key][s]]
            valsL = [x for r in rows if r['winner'] in ('A', 'B') and r['winner'] != s for x in r[key][s]]
            if vals or valsL:
                print(f"(2) {name} side{s} escorts<=3: W {statistics.mean(vals):.1f} "
                      f"L {statistics.mean(valsL):.1f} (n {len(vals)}/{len(valsL)})")
    sh = collections.Counter()
    for r in rows:
        for s in 'AB':
            if r['winner'] == s: sh.update(r['escShape'][s])
    print('(2) winner queen-escort shape (dx,dy in -1..1):', sh.most_common(9))


if __name__ == '__main__':
    main()
