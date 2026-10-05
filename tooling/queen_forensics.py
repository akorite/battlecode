"""Queen-death forensics for gate replays (fv2 format, seats by dragon id 0/1).

For each replay: locate the cand side's QUEEN death event (queen = lowest-id
dragon of each parity; ids 0,1 are the initial queens — parity = team).
Report round, reason, cell, distance to nearest ALLY head and nearest ENEMY
head at the death round, the killer's head 5 rounds before the kill, and a
rough class:
  (a) ram-isolated   h2h victim, no ally head within cheb 2
  (b) ram-escorted   h2h victim, ally within 2 (screen failed)
  (c) h2h-initiated  queen died hitHeadToHead as the AGGRESSOR? (can't see
                     aggressor in events; approximated: killer len <= queen)
  (d) self/wall/body hitSelf/hitWall/hitOtherBody
  (e) elim-cascade   death at/after first mass-elimination round (heuristic:
                     reason teamEliminated context — flagged when >60% of the
                     side's dragons die same round)

Also emits distance profile of the enemy killer head at rounds kill-5..kill.

Usage: python3 tooling/queen_forensics.py <replay-or-dir> [--cand NAME]
--cand selects which bot name is the candidate (default abyss_v209); side is
resolved from the replay's name-a/name-b header ordering: filenames are
{map}-s{seed}-{na}-{nb}.replay where na = side A.
"""
import collections, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
from parse_replay import parse
from pocket_metric import parse_map


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def tcheb(a, b, W, H):
    dx = abs(a[0] - b[0]); dy = abs(a[1] - b[1])
    return max(min(dx, W - dx), min(dy, H - dy))


def forensics(path, cand):
    base = os.path.basename(path)
    parts = base[:-7].rsplit('-', 2)   # strip .replay
    mseed, na, nb = parts[0], parts[1], parts[2]
    cand_side = 'A' if na == cand else ('B' if nb == cand else None)
    if cand_side is None:
        return {'file': base, 'error': 'cand not in names'}
    queen_id = 0 if cand_side == 'A' else 1
    r = parse(path)
    ev = r['events']
    W, H, dr, edges = parse_map(r['map'])
    res = r.get('result', {})
    winner = res.get('winner')
    loss = winner is not None and winner != cand_side
    out = {'file': base, 'map': mseed, 'cand_side': cand_side,
           'winner': winner, 'loss': bool(loss)}
    if not loss:
        out['class'] = 'no-loss'
        return out
    # Track heads, lens, team through events. Initial ids: parity = side.
    team, heads, lens = {}, {}, {}
    rnd = 0
    headhist = collections.defaultdict(dict)  # id -> {round: head}
    deaths = []
    for e in ev:
        ty = e['type']
        if ty == 'roundStart':
            rnd = e['round']
        elif ty == 'dragonUpdate':
            i = e['id']
            if i not in team:
                team[i] = 'AB'[i % 2]
            h = tuple(e['head'])
            heads[i] = h
            headhist[i][rnd] = h
        elif ty == 'dragonSplit':
            s = e['team']
            team[e['childId']] = s
            heads[e['childId']] = tuple(e['childBody'][0])
            lens[e['childId']] = len(e['childBody'])
            heads[e['parentId']] = tuple(e['parentBody'][0])
            lens[e['parentId']] = len(e['parentBody'])
        elif ty == 'dragonDeath':
            deaths.append({'rnd': rnd, 'id': e['id'], 'reason': e['reason'],
                           'side': team.get(e['id']), 'head': heads.get(e['id'])})
            heads.pop(e['id'], None)
    qspawn = None
    if queen_id in headhist:
        qspawn = headhist[queen_id][min(headhist[queen_id])]
    qd = next((d for d in deaths if d['id'] == queen_id), None)
    if not qd:
        out['class'] = 'queen-alive-loss'
        return out
    out['queen_death'] = qd
    # Snapshot ally/enemy distances at death round: heads dict was mutated;
    # rebuild head positions AT qd['rnd'] from headhist (latest <= rnd).
    ally_d = enemy_d = None
    allies = enemies = 0
    killer_head = None
    for i, hh in headhist.items():
        if i == queen_id:
            continue
        if team.get(i) is None:
            continue
        cand_rounds = [rr for rr in hh if rr <= qd['rnd']]
        if not cand_rounds:
            continue
        last = hh[max(cand_rounds)]
        # alive check: died before/at qd round?
        dd = next((d for d in deaths if d['id'] == i and d['rnd'] <= qd['rnd']), None)
        if dd:
            continue
        d = tcheb(qd['head'], last, W, H)
        if team[i] == cand_side:
            allies += 1
            ally_d = d if ally_d is None else min(ally_d, d)
        else:
            enemies += 1
            enemy_d = d if enemy_d is None else min(enemy_d, d)
            if d == enemy_d:
                killer_head = i
    out['ally_d'] = ally_d
    out['enemy_d'] = enemy_d
    out['allies_alive'] = allies
    out['enemies_alive'] = enemies
    # class
    reason = qd['reason']
    initiated = None
    if reason == 'hitHeadToHead':
        # h2h counterpart: enemy dragon that died h2h the same round — the
        # initiator is whoever MOVED onto the other's previous head cell.
        cp = next((d for d in deaths
                   if d['rnd'] == qd['rnd'] and d['reason'] == 'hitHeadToHead'
                   and d['side'] != cand_side), None)
        if cp is not None:
            qprev = headhist[queen_id].get(qd['rnd'] - 1)
            eprev = headhist[cp['id']].get(qd['rnd'] - 1)
            if eprev is not None and qd['head'] == eprev:
                initiated = True          # she moved onto his cell
            elif qprev is not None and cp['head'] == qprev:
                initiated = False         # he moved onto hers = rammed
        if ally_d is None or ally_d > 2:
            cls = 'a-ram-isolated'
        else:
            cls = 'b-ram-escorted'
        if initiated is True:
            cls += '+initiated'
        elif initiated is False:
            cls += '+rammed'
    elif reason in ('hitSelf', 'hitWall', 'hitOtherBody'):
        cls = 'd-self-wall-body'
    else:
        cls = f'e-other-{reason}'
    # elim cascade: >60% of side dragons die same round
    same = sum(1 for d in deaths if d['side'] == cand_side and d['rnd'] == qd['rnd'])
    side_total = sum(1 for i in team if team[i] == cand_side)
    if side_total and same / max(1, side_total) > 0.6:
        cls = 'e-elim-cascade'
    out['class'] = cls
    # killer approach: h2h counterpart when identifiable, else nearest enemy
    kill_src = killer_head
    if reason == 'hitHeadToHead':
        cp2 = next((d for d in deaths
                    if d['rnd'] == qd['rnd'] and d['reason'] == 'hitHeadToHead'
                    and d['side'] != cand_side), None)
        if cp2 is not None:
            kill_src = cp2['id']
            out['killer_id'] = cp2['id']
    if kill_src is not None:
        hh = headhist[kill_src]
        tr = qd['rnd'] - 5
        cand_rounds = [rr for rr in hh if rr <= tr]
        if cand_rounds:
            out['killer_dist_at_k5'] = tcheb(qd['head'], hh[max(cand_rounds)], W, H)
        else:
            out['killer_dist_at_k5'] = -1
    # queen behavior before death: drift over last 5 rounds + spawn distance
    qh = headhist.get(queen_id, {})
    rs = sorted(rr for rr in qh if rr <= qd['rnd'])
    if len(rs) >= 2:
        lo = max(0, qd['rnd'] - 5)
        older = [rr for rr in rs if rr <= lo]
        if older:
            out['q_drift5'] = tcheb(qh[max(older)], qd['head'], W, H)
    if qspawn is not None:
        out['q_spawn_dist'] = tcheb(qspawn, qd['head'], W, H)
    return out


if __name__ == '__main__':
    cand = 'abyss_v209'
    args = sys.argv[1:]
    if '--cand' in args:
        i = args.index('--cand')
        cand = args[i + 1]
        del args[i:i + 2]
    files = []
    for a in args:
        if os.path.isdir(a):
            files += sorted(os.path.join(a, f) for f in os.listdir(a) if f.endswith('.replay'))
        else:
            files.append(a)
    for p in files:
        try:
            print(json.dumps(forensics(p, cand)))
        except Exception as ex:
            print(json.dumps({'file': os.path.basename(p), 'error': str(ex)}))
