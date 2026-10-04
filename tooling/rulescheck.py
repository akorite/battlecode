#!/usr/bin/env python3
"""Rules-checker: portal exits, freeze bug, ram-reach cost model — all replay-derived.

Q1: for every teleport (portal transit) verify actual landing == TileAfterCrossing
    (partner edge, same heading) computed from the map's EDGE partner table.
Q2: transits per game + milling (head static runs, small-region pacing).
Q3: multi-step MOVEs; simulate bodies under engine rules (step0 free, later steps
    pay 1 tail segment; pearl keeps tail) and check predicted tail == event tail.
"""
import sys, collections
sys.path.insert(0, 'handoff/tooling')
from parse_replay import parse

DIR = {'N': (0, -1), 'S': (0, 1), 'E': (1, 0), 'W': (-1, 0)}

def load_map(text):
    W = H = None
    edges, dragons, pearls = {}, {}, set()
    did = 0
    for line in text.splitlines():
        t = line.split()
        if not t or t[0].startswith('#'):
            continue
        if t[0] == 'MAP': W, H = int(t[1]), int(t[2])
        elif t[0] == 'EDGE' and int(t[2]) == 2:
            edges[int(t[1])] = int(t[3])          # edgeIdx -> portalId
        elif t[0] == 'DRAGON':
            team = int(t[1]); n = int(t[2])
            body = [(int(t[3 + 2*i]), int(t[4 + 2*i])) for i in range(n)]
            dragons[did] = (team, body); did += 1
        elif t[0] == 'TILE' and int(t[4]) > 0:
            pass  # pearl SPAWNER (min/max respawn gap) — pearls arrive via tileChange
    return W, H, edges, dragons, pearls

def decode_edge(idx, W):
    row, x = idx // (W + 1), idx % (W + 1)
    if row % 2 == 0:
        return ('H', x, row // 2)      # between (x,y-1) and (x,y)
    return ('V', x, (row - 1) // 2)    # between (x-1,y) and (x,y)

def side_edge(x, y, d, W):
    dx, dy = DIR[d]; nx, ny = x + dx, y + dy
    if d in 'NS':
        return (2 * max(y, ny)) * (W + 1) + x
    return (2 * y + 1) * (W + 1) + max(x, nx)

def landing(partner, d):
    o, x, y = partner
    if o == 'H':
        return (x, y) if d == 'S' else (x, y - 1)
    return (x, y) if d == 'E' else (x - 1, y)

def wrap(p, W, H):
    return (p[0] % W, p[1] % H)

def run(path):
    r = parse(path)
    W, H, edges, starters, pearls0 = load_map(r['map'])
    partners = collections.defaultdict(list)
    for ei, pid in edges.items():
        partners[pid].append(decode_edge(ei, W))
    pearls = set(pearls0)
    body = {i: collections.deque(b) for i, (t, b) in starters.items()}
    team = {i: t for i, (t, b) in starters.items()}
    cur_steps, step_k = [], 0
    pending_eat = set()
    rnd = 0
    heads = collections.defaultdict(dict)
    seen_action = set()
    stats = collections.Counter()
    mismatches, transits, multistep = [], [], collections.Counter()

    for e in r['events']:
        t = e['type']
        if t == 'roundStart':
            rnd = e.get('round', rnd + 1)
        elif t == 'tileChange':
            p = tuple(e['tile'])
            if e['hasPearl']: pearls.add(p)
            else:
                pearls.discard(p)
                pending_eat.add(p)   # removal emits BEFORE the eater's dragonUpdate
        elif t == 'dragonSplit':
            body[e['parentId']] = collections.deque(tuple(p) for p in e['parentBody'])
            body[e['childId']] = collections.deque(tuple(p) for p in e['childBody'])
            team[e['childId']] = e['team']
            cur_steps, step_k = [], 0
        elif t == 'dragonDeath':
            body.pop(e['id'], None)
        elif t == 'dragonAction':
            cur_steps = e['action'].get('steps', []) if e['action']['kind'] == 'move' else []
            step_k = 0
            seen_action.add(e['id'])
            if len(cur_steps) > 1:
                multistep[len(cur_steps)] += 1
                stats['multistep_moves'] += 1
        elif t == 'dragonUpdate':
            did, head, facing = e['id'], tuple(e['head']), e['facing']
            b = body.get(did)
            if b:
                old = b[0]
                if did not in seen_action and head == old and tuple(e['tail']) == b[-1]:
                    heads[did][rnd] = head
                    continue  # initial position-sync update, not a step
                mdist = min((head[0]-old[0]) % W, (old[0]-head[0]) % W) + \
                        min((head[1]-old[1]) % H, (old[1]-head[1]) % H)
                if mdist != 1 and head != old:
                    stats['teleport'] += 1
                    ei = side_edge(old[0], old[1], facing, W)
                    pid = edges.get(ei)
                    if pid is not None:
                        exp = [p for p in partners[pid] if p != decode_edge(ei, W)]
                        ok = exp and wrap(landing(exp[0], facing), W, H) == wrap(head, W, H)
                        transits.append((rnd, did, old, facing, head,
                                         'OK' if ok else f'LAND-MISMATCH exp={landing(exp[0], facing) if exp else None}'))
                        stats['q1_ok' if ok else 'q1_bad'] += 1
                    else:
                        transits.append((rnd, did, old, facing, head, f'NO-PORTAL-EDGE ei={ei}'))
                        stats['q1_noedge'] += 1
                # deployed engine (replay-verified): EVERY step pops 1 tail unless the
                # head lands on a pearl — no extra multi-step payment
                b.appendleft(head)
                if head in pearls or head in pending_eat:
                    pearls.discard(head); pending_eat.discard(head); stats['ate'] += 1
                elif b: b.pop()
                if len(b) > 1 and tuple(b[-1]) != tuple(e['tail']):
                    mismatches.append((rnd, did, step_k, list(b), e['tail']))
                step_k += 1
            heads[did][rnd] = head

    for did, hh in heads.items():
        rounds = sorted(hh)
        run_, best = 1, 1
        for a, bb in zip(rounds, rounds[1:]):
            run_ = run_ + 1 if bb == a + 1 and hh[bb] == hh[a] else 1
            best = max(best, run_)
        stats[f'maxstatic_{min(best, 99)}'] += 1
        stats['dragons'] += 1
    return stats, transits, multistep, mismatches

if __name__ == '__main__':
    for path in sys.argv[1:]:
        try:
            stats, transits, multistep, mismatches = run(path)
            name = path.split('/')[-1].replace('.replay', '')
            print(f'\n== {name}')
            print(' ', dict(stats))
            print('  multistep:', dict(multistep))
            for tr in transits[:10]:
                print('  transit', tr)
            if mismatches[:3]:
                print('  TAIL-MISMATCH', mismatches[:3])
        except Exception as ex:
            import traceback; traceback.print_exc()
