"""hitSelf census: forced least-bad vs planner gap, + kamikaze availability.

Reconstructs ENGINE-truth occupancy at the moment of each hitSelf death
(sequential event scan: bodies tracked as deques from dragonUpdate head/tail,
splits set bodies explicitly). The death event stream shows
turnStart -> dragonAction(steps) -> dragonDeath with no update for the dead,
so the victim's head is its last update; the kill cell = head + chosen step
(portal steps resolved via edge partners).

Per death: which own-body segment index the head stepped onto (0=neck), is it
the tail cell (engine tail-vacate test), and per-dir option classes:
  open / tail / self / enemyHead / allyHead / otherBody / wall / portal
forced = no open dir (tail is fatal per no-vacate). kamikaze = enemyHead dir.

Usage: python3 hitself_census.py <replay_or_dir> [--cand NAME] -> JSONL/death
"""
import collections, glob, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
from parse_replay import parse
from pocket_metric import parse_map

D = {'N': (0, -1), 'S': (0, 1), 'E': (1, 0), 'W': (-1, 0)}
DCH = 'NESW'

def edge_kind(edges, W, H, x, y, d):
    if d == 'N': i = 2 * y * (W + 1) + x
    elif d == 'S': i = 2 * ((y + 1) % H) * (W + 1) + x
    elif d == 'W': i = (2 * y + 1) * (W + 1) + x
    else: i = (2 * y + 1) * (W + 1) + (x + 1) % W
    return edges.get(i, (0, -1))

def analyze(path, cand):
    r = parse(path)
    ev = r['events']
    W, H, dr, edges = parse_map(r['map'])
    base = os.path.basename(path).replace('.replay', '')
    parts = base.rsplit('-', 2)
    na = parts[-2] if len(parts) > 1 else ''
    cand_side = 'A' if na == cand else 'B'
    # portal id -> the two boundary indices sharing it
    pid2edges = collections.defaultdict(list)
    for ei, (k, p) in edges.items():
        if k == 2 and p >= 0: pid2edges[p].append(ei)
    def edge_index(x, y, d):
        if d == 'N': return 2 * y * (W + 1) + x
        if d == 'S': return 2 * ((y + 1) % H) * (W + 1) + x
        if d == 'W': return (2 * y + 1) * (W + 1) + x
        return (2 * y + 1) * (W + 1) + (x + 1) % W
    def portal_land(src_idx, d):
        """landing cell when crossing portal edge src_idx stepping dir d:
        the cell on the step-direction side of the partner boundary."""
        k, p = edges.get(src_idx, (0, -1))
        if k != 2 or p < 0: return None
        others = [ei for ei in pid2edges[p] if ei != src_idx]
        if len(others) != 1: return None
        pi = others[0]
        row, col = pi // (W + 1), pi % (W + 1)
        if row % 2 == 0:   # horizontal boundary: north (col,row/2-1) | south (col,row/2)
            by = row // 2
            return (col % W, ((by - 1) if d == 'N' else by) % H)
        by = row // 2      # vertical boundary: west (col-1) | east (col)
        return (((col - 1) if d == 'W' else col) % W, by % H)
    def step_cell(pos, d):
        x, y = pos
        kind, partner = edge_kind(edges, W, H, x, y, d)
        if kind == 1: return None, 'wall'
        if kind == 2:
            cell = portal_land(edge_index(x, y, d), d)
            return (cell, 'portal') if cell is not None else (None, 'portal?')
        dx, dy = D[d]
        return ((x + dx) % W, (y + dy) % H), 'open'
    body, team, heads, facing, born = {}, {}, {}, {}, {}
    recent_splits = []
    for e in ev:
        if e['type'] == 'roundStart': break
        if e['type'] == 'dragonUpdate' and e['id'] < len(dr):
            t, b = dr[e['id']]
            body[e['id']] = collections.deque(b)
            team[e['id']] = 'AB'[t]
            heads[e['id']] = tuple(b[0])
    out = []
    rnd = 0
    last_action = {}
    last_occ = {}   # cell -> (round, team) of last body occupancy seen
    def occ_map():
        """cell -> ('self'|id-of-dragon, is_head, is_enemy_relative?)"""
        m = {}
        for i, b in body.items():
            for j, c in enumerate(b):
                m[c] = (i, j == 0)
        return m
    for e in ev:
        ty = e['type']
        if ty == 'roundStart':
            rnd = e['round']
        elif ty == 'dragonAction':
            last_action[e['id']] = e['action']
        elif ty == 'dragonUpdate':
            i = e['id']
            if i not in body: continue
            b = body[i]; h, tl = tuple(e['head']), tuple(e['tail'])
            if b[0] != h: b.appendleft(h)
            while len(b) > 1 and b[-1] != tl: b.pop()
            heads[i] = h
            facing[i] = e['facing']
            last_occ[h] = (rnd, team.get(i))
        elif ty == 'dragonSplit':
            s = e['team']
            body[e['parentId']] = collections.deque(tuple(x) for x in e['parentBody'])
            body[e['childId']] = collections.deque(tuple(x) for x in e['childBody'])
            team[e['childId']] = s
            heads[e['parentId']] = tuple(e['parentBody'][0])
            heads[e['childId']] = tuple(e['childBody'][0])
            born[e['childId']] = (rnd, e['parentId'],
                                  tuple(e['childBody'][0]),
                                  tuple(e['childBody'][-1]))
            recent_splits.append((rnd, s,
                                  [tuple(x) for x in e['childBody']] +
                                  [tuple(x) for x in e['parentBody']]))
        elif ty == 'dragonDeath':
            i = e['id']
            if e['reason'] not in ('hitSelf', 'hitOtherBody', 'hitHeadToHead'):
                body.pop(i, None); heads.pop(i, None); facing.pop(i, None)
                continue
            s = team.get(i)
            if s is None: continue
            b = list(body.get(i, []))
            h = heads.get(i)
            act = last_action.get(i, {})
            steps = act.get('steps') or []
            kind = act.get('kind', '?')
            # full occupancy at this instant
            om = occ_map()
            own = set(b)
            tail = b[-1] if b else None
            rec = {'file': base, 'side': s, 'cand_death': s == cand_side,
                   'round': rnd, 'id': i, 'len': len(b), 'reason': e['reason'],
                   'action': kind, 'steps': steps}
            if h is None or not steps:
                rec['cls'] = 'no-state'
                out.append(rec); body.pop(i, None); heads.pop(i, None); continue
            # resolve the chosen path step by step (self collisions kill at first fatal)
            pos = h
            kill_cell = None; stepn = 0
            for sidx, sd in enumerate(steps):
                cell, ck = step_cell(pos, sd)
                stepn = sidx
                if cell is None:
                    kill_cell = None; break   # wall death shouldn't be hitSelf; flag
                if cell in own or (cell in om and om[cell][0] != i):
                    kill_cell = cell; break
                pos = cell
            rec['kill_cell'] = kill_cell
            rec['kill_step'] = stepn
            rec['steps_n'] = len(steps)
            f = facing.get(i)
            rec['facing'] = f
            rec['step0'] = steps[0] if steps else None
            if f and steps:
                rec['step_rel'] = ('fwd' if steps[0] == f else
                                   'rev' if steps[0] == DCH[DCH.index(f) ^ 2]
                                   else 'lat')
            if kill_cell is not None:
                rec['seg_idx'] = b.index(kill_cell) if kill_cell in b else -1
                rec['kill_is_tail'] = (kill_cell == tail)
                rec['kill_other'] = om[kill_cell][0] if kill_cell in om and kill_cell not in own else None
            # per-dir options at prev head
            opts = {}
            for d in 'NSWE':
                cell, ck = step_cell(h, d)
                if cell is None:
                    opts[d] = 'wall' if ck == 'wall' else 'portal'
                    continue
                if ck == 'portal': opts[d] = 'portal:' + ('open' if cell not in om else 'occ'); continue
                if cell in own:
                    opts[d] = 'tail' if cell == tail else 'self'
                elif cell in om:
                    oid, ishead = om[cell]
                    opts[d] = ('enemyHead' if team.get(oid) != s else 'allyHead') if ishead else 'otherBody'
                else:
                    opts[d] = 'open'
            rec['opts'] = opts
            # how long since each option cell was last occupied (replay truth)
            rec['opt_age'] = {d: (None if c is None else rnd - last_occ.get(c, (-99,))[0])
                              for d in 'NSWE'
                              for c in [step_cell(h, d)[0]]}
            # engine truth: own-tail step is fatal (no vacate rule) -> tail is NOT safe
            rec['open_dirs'] = sum(1 for v in opts.values() if v in ('open', 'portal:open'))
            rec['kam_dirs'] = sum(1 for v in opts.values() if v == 'enemyHead')
            rec['self_dirs'] = sum(1 for v in opts.values() if v == 'self')
            rec['ally_dirs'] = sum(1 for v in opts.values() if v == 'allyHead')
            rec['enemybody_dirs'] = sum(1 for v in opts.values()
                                      if v == 'otherBody')
            rec['is_queen'] = i in (0, 1)
            # was the victim a split child, and how old?
            if i in born:
                br, pid, chd0, chdT = born[i]
                rec['split_child'] = True
                rec['birth_round'] = br
                rec['age'] = rnd - br
            else:
                rec['split_child'] = False
                rec['age'] = rnd  # starter
            # any same-team split within cheb-2 of the kill cell, same/prior round?
            if kill_cell is not None:
                near = [sr for sr, st, cells in recent_splits
                        if st == s and rnd - sr <= 1
                        and min(max(abs(c[0]-kill_cell[0]), abs(c[1]-kill_cell[1]))
                                for c in cells) <= 2]
                rec['split_near'] = bool(near)
            recent_splits = [x for x in recent_splits if rnd - x[0] <= 2]
            ally_heads = [hh for j, hh in heads.items()
                          if j != i and team.get(j) == s]
            rec['d_ally'] = (min(max(abs(hh[0] - h[0]), abs(hh[1] - h[1]))
                                 for hh in ally_heads)
                             if ally_heads else None)
            # cheb dist from each open dir cell to own queen head (qRes probe)
            qid = 0 if s == 'A' else 1
            qh = heads.get(qid)
            if qh is not None:
                open_cells = [step_cell(h, d)[0] for d in 'NSWE'
                              if opts[d] in ('open', 'portal:open')]
                rec['qd_open'] = (min(max(abs(c[0] - qh[0]), abs(c[1] - qh[1]))
                                    for c in open_cells)
                                  if open_cells else None)
                rec['qd_kill'] = (max(abs(kill_cell[0] - qh[0]),
                                      abs(kill_cell[1] - qh[1]))
                                  if kill_cell is not None else None)
            rec['open_min_age'] = min(
                (v for d, v in rec['opt_age'].items() if opts[d] in ('open', 'portal:open') and v is not None),
                default=None)
            rec['end_cell'] = list(pos)
            eh = [hh for j, hh in heads.items()
                  if team.get(j) and team[j] != s]
            # per-open-dir: cheb to nearest enemy head pre-move (true-safe test)
            rec['opt_ehead'] = {
                d: min((max(abs(c[0] - hh[0]), abs(c[1] - hh[1])) for hh in eh),
                       default=None)
                for d in 'NSWE'
                for c in [step_cell(h, d)[0]]
                if c is not None and opts.get(d) in ('open', 'portal:open')}
            rec['safe_dirs'] = sum(1 for v in rec['opt_ehead'].values()
                                   if v is not None and v >= 2)
            if e['reason'] == 'hitHeadToHead':
                eh = [hh for j, hh in heads.items() if team.get(j) and team[j] != s]
                rec['end_d_enemyhead'] = (min(
                    max(abs(hh[0] - pos[0]), abs(hh[1] - pos[1])) for hh in eh)
                    if eh else None)
                rec['d_enemyhead'] = (min(
                    max(abs(hh[0] - h[0]), abs(hh[1] - h[1])) for hh in eh)
                    if eh else None)
            rec['cls'] = ('safe-existed' if rec['open_dirs'] > 0
                          else 'kamikaze-available' if rec['kam_dirs'] > 0
                          else 'truly-forced')
            out.append(rec)
            body.pop(i, None); heads.pop(i, None); facing.pop(i, None)
    return out

if __name__ == '__main__':
    args = sys.argv[1:]
    cand = 'abyss_v252'
    if '--cand' in args:
        i = args.index('--cand'); cand = args[i + 1]; del args[i:i + 2]
    files = []
    for a in args:
        if os.path.isdir(a): files += sorted(glob.glob(os.path.join(a, '*.replay')))
        else: files.append(a)
    for f in files:
        try:
            for rec in analyze(f, cand):
                print(json.dumps(rec))
        except Exception as ex:
            print(json.dumps({'file': f, 'error': str(ex)}), file=sys.stderr)
