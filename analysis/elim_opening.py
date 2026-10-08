"""Elim-class opening-melee forensics: what winners do in r0-80 that we don't.

Per side per game (us = team 351 side, opp = winner):
  - splits per round bucket (r0-19/20-39/40-59/60-80), split-out sizes
  - queen bud cadence (queen = min id): split rounds
  - pearls eaten per round bucket (tileChange pearl-off attributed to the
    dragon whose live head is on the cell)
  - unit lifetimes for dragons born r0-80 (death-birth or censored)
  - death adjacency: dist of death cell to nearest teammate head / enemy head
  - suicide-pawn signature: children split off who die h2h within 15r of birth
  - death reasons per side r0-80

Usage: python3 analysis/elim_opening.py
"""
import collections, glob, json, os, statistics, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../tooling'))
from parse_replay import parse  # noqa: E402
import replay_metrics as rm    # noqa: E402

BUCKETS = [(0, 20), (20, 40), (40, 60), (60, 81)]
BNAME = ['r0-19', 'r20-39', 'r40-59', 'r60-80']


def analyze(path, meta):
    r = parse(path)
    ev = r['events']
    W, H, dr, edges = rm.parse_map(r['map'])
    NC = W * H

    def tcheb(a, b):
        dx = min(abs(a[0] - b[0]), W - abs(a[0] - b[0]))
        dy = min(abs(a[1] - b[1]), H - abs(a[1] - b[1]))
        return max(dx, dy)

    team = {i: 'AB'[t] for i, (t, b) in enumerate(dr)}
    body = {i: collections.deque(tuple(x) for x in b) for i, (t, b) in enumerate(dr)}
    queen = {s: min(i for i in team if team[i] == s) for s in 'AB'}
    birth = {i: 0 for i in body}

    splits = collections.defaultdict(lambda: collections.Counter())   # side -> bucket -> n
    shed = collections.defaultdict(list)                               # side -> childLen at birth
    q_splits = collections.defaultdict(list)
    eaten = collections.defaultdict(lambda: collections.Counter())     # side -> bucket -> n
    life = collections.defaultdict(list)                               # side -> lifetimes (born<=80)
    deadr = collections.defaultdict(dict)                              # side -> id -> death rnd
    reasons = collections.defaultdict(collections.Counter)
    d_adj_own = collections.defaultdict(list)                          # dist to nearest teammate head
    d_adj_enemy = collections.defaultdict(list)
    pawn = collections.defaultdict(lambda: {'n': 0, 'h2h15': 0, 'h2h_all': 0, 'died15': 0})
    # h2h seek: children whose FIRST death event is h2h and <=15r from birth
    child_birth = {}  # id -> rnd

    pearls = set()   # live pearl cells
    rnd = 0
    last_r = 0
    head_of = {i: body[i][0] for i in body}
    last_eater = {}  # cell -> team of last dragon whose head sat on it (attribution fallback)

    for e in ev:
        if not isinstance(e, dict):
            continue
        ty = e['type']
        if ty == 'roundStart':
            rnd = e['round']
            last_r = max(last_r, rnd)
            actor = None
            continue
        if ty == 'turnStart':
            actor = e['id']
            continue
        if ty == 'tileChange':
            c = tuple(e['tile'])
            if e.get('hasPearl'):
                pearls.add(c)
            else:
                pearls.discard(c)
                if actor is not None and rnd <= 80 and team.get(actor):
                    eaten[team[actor]][min(rnd // 20, 3)] += 1
            continue
        if ty == 'dragonUpdate':
            i = e['id']
            if i in body:
                b = body[i]
                h, tl = tuple(e['head']), tuple(e['tail'])
                if b[0] != h:
                    b.appendleft(h)
                    while len(b) > 1 and b[-1] != tl:
                        b.pop()
                head_of[i] = b[0]
            continue
        if ty == 'dragonSplit':
            cid, pid = e['childId'], e['parentId']
            s = e['team'].upper() if isinstance(e['team'], str) else 'AB'[e['team']]
            team[cid] = s
            body[pid] = collections.deque(tuple(x) for x in e['parentBody'])
            body[cid] = collections.deque(tuple(x) for x in e['childBody'])
            head_of[cid] = body[cid][0]
            head_of[pid] = body[pid][0]
            birth[cid] = rnd
            child_birth[cid] = rnd
            if rnd <= 80:
                splits[s][min(rnd // 20, 3)] += 1
                shed[s].append(len(e['childBody']))
                if pid == queen.get(s):
                    q_splits[s].append(rnd)
                pawn[s]['n'] += 1
            continue
        if ty == 'dragonDeath':
            i = e['id']
            s = team.get(i)
            if s:
                deadr[s][i] = rnd
                if rnd <= 80:
                    reasons[s][e['reason']] += 1
                    if i in birth or i in body:
                        life[s].append(rnd - birth.get(i, 0))
                    if i in child_birth and e['reason'] == 'hitHeadToHead':
                        pawn[s]['h2h_all'] += 1
                        if rnd - child_birth[i] <= 15:
                            pawn[s]['h2h15'] += 1
                    if i in child_birth and rnd - child_birth[i] <= 15:
                        pawn[s]['died15'] += 1
                    # adjacency at death
                    dc = head_of.get(i)
                    if dc:
                        own = [tcheb(dc, h) for j, h in head_of.items() if j != i and team.get(j) == s]
                        en = [tcheb(dc, h) for j, h in head_of.items() if team.get(j) and team.get(j) != s]
                        if own:
                            d_adj_own[s].append(min(own))
                        if e['reason'] in ('hitWall','hitSelf'):
                            d_adj_own[s+'_suic'].append(min(own))
                        if en:
                            d_adj_enemy[s].append(min(en))
            body.pop(i, None)
            head_of.pop(i, None)

    # censored lifetimes for dragons born<=80 still alive at 80
    for i, b in birth.items():
        s = team.get(i)
        if b <= 80 and i in body and i not in deadr[s]:
            life[s].append(min(80, last_r) - b)  # censored at 80/game-end

    out = {'map': meta['map'], 'NC': NC, 'a': meta['a']['name'], 'b': meta['b']['name'],
           'winner': meta['winner'], 'last_r': last_r,
           'splits': {s: dict(splits[s]) for s in 'AB'},
           'shed': dict(shed), 'q_splits': dict(q_splits),
           'eaten': {s: dict(eaten[s]) for s in 'AB'},
           'life': dict(life), 'reasons': {s: dict(reasons[s]) for s in 'AB'},
           'd_own': dict(d_adj_own), 'd_enemy': dict(d_adj_enemy),
           'pawn': dict(pawn)}
    return out


def bline(c):
    return ' '.join(f"{BNAME[k]}:{c.get(k,0)}" for k in range(4))


def main():
    games = []
    for f in sorted(glob.glob('elim_replays/*.replay')):
        meta = json.load(open(f.replace('.replay', '.json')))
        try:
            games.append((f, analyze(f, meta)))
        except Exception as ex:
            print(f, 'FAIL', repr(ex)[:120])

    print(f'games={len(games)}')
    agg = collections.defaultdict(lambda: collections.defaultdict(list))
    for f, g in games:
        ws = g['winner'].upper()
        ls_ = 'B' if ws == 'A' else 'A'
        ours = 'A'  # we're side A in ladder replays
        print(f"\n== {g['map']} NC={g['NC']} {g['a']} v {g['b']} w:{ws} last_r={g['last_r']} ==")
        for s, tag in ((ws, 'WINNER'), (ours, 'US(A)')):
            b = g['splits'].get(s, {})
            print(f"  {tag:<7} splits {bline(b)} shed med={statistics.median(g['shed'].get(s, [0]))} "
                  f"q_splits@{g['q_splits'].get(s, [])} | eaten {bline(g['eaten'].get(s, {}))}")
            lf = g['life'].get(s, [])
            if lf:
                print(f"        lifetimes n={len(lf)} med={statistics.median(lf)} "
                      f"<=5r:{sum(1 for x in lf if x<=5)/len(lf):.2f} <=15r:{sum(1 for x in lf if x<=15)/len(lf):.2f}")
            p = g['pawn'].get(s, {'n': 0, 'h2h15': 0, 'died15': 0})
            if p['n']:
                print(f"        children: n={p['n']} died<=15r={p['died15']} ({p['died15']/p['n']:.2f}) "
                      f"h2h<=15r={p['h2h15']} ({p['h2h15']/p['n']:.2f})")
            do, de = g['d_own'].get(s, []), g['d_enemy'].get(s, [])
            if do:
                print(f"        death adjacency: own med={statistics.median(do)} enemy med={statistics.median(de)}")
            print(f"        reasons: {g['reasons'].get(s, {})}")
        # aggregate winner vs us across games
        for s, tag in ((ws, 'W'), (ours, 'U')):
            for k, v in g['splits'].get(s, {}).items():
                agg[tag]['splits' + str(k)].append(v)
            agg[tag]['shed'] += g['shed'].get(s, [])
            agg[tag]['qs'] += g['q_splits'].get(s, [])
            for k, v in g['eaten'].get(s, {}).items():
                agg[tag]['eaten' + str(k)].append(v)
            agg[tag]['life'] += g['life'].get(s, [])
            for r_, n in g['reasons'].get(s, {}).items():
                agg[tag]['r_' + r_].append(n)
            agg[tag]['d_own'] += g['d_own'].get(s, [])
            agg[tag]['d_enemy'] += g['d_enemy'].get(s, [])
            p = g['pawn'].get(s)
            if p:
                agg[tag]['pn'].append(p['n']); agg[tag]['pd15'].append(p['died15']); agg[tag]['ph15'].append(p['h2h15'])

    print('\n\n===== AGGREGATE winner-side vs our-side (all elim losses) =====')
    for tag in ('W', 'U'):
        a = agg[tag]
        print(f"\n--- {'WINNER' if tag=='W' else 'US'} ---")
        print('  splits/game by bucket:', {BNAME[k]: f"med {statistics.median(a['splits'+str(k)])} tot {sum(a['splits'+str(k)])}" for k in range(4)})
        if a['shed']:
            print(f"  shed child-len: med={statistics.median(a['shed'])} mean={statistics.mean(a['shed']):.1f} dist={collections.Counter(a['shed']).most_common(8)}")
        print(f"  queen splits/game: {statistics.mean([len(a['qs']) for _ in [0]])} tot qsplit rounds={sorted(a['qs'])[:20]}")
        print('  eaten/game by bucket:', {BNAME[k]: f"med {statistics.median(a['eaten'+str(k)]) if a['eaten'+str(k)] else 0}" for k in range(4)})
        lf = a['life']
        if lf:
            print(f"  lifetimes n={len(lf)} med={statistics.median(lf)} <=5:{sum(1 for x in lf if x<=5)/len(lf):.2f} <=15:{sum(1 for x in lf if x<=15)/len(lf):.2f} >=40:{sum(1 for x in lf if x>=40)/len(lf):.2f}")
        print('  death reasons/game:', {r_: f"{statistics.mean(v):.1f}" for r_, v in a.items() if r_.startswith('r_')})
        if a['d_own']:
            print(f"  death-adj own med={statistics.median(a['d_own'])} enemy med={statistics.median(a['d_enemy'])}")
        if a['pn']:
            print(f"  children/game n={statistics.mean(a['pn']):.1f} died<=15r={sum(a['pd15'])}/{sum(a['pn'])} h2h<=15r={sum(a['ph15'])}/{sum(a['pn'])}")


if __name__ == '__main__':
    main()
