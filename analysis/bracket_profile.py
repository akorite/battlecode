"""Bracket opponent profiler: pi (314) and Sabotage-d (46).

Per game, per side: death causes (early/late), churn economy (splits, nva
donations near own units vs starvation far), queen fate, endgame longest/total,
suicide-pawn share, starve waves. Aggregates per opponent: map W/L, what kills
their queen, which mechanism decides their losses.

Usage: python3 analysis/bracket_profile.py <dir> <target_team_id>
"""
import collections, glob, json, os, statistics, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../tooling'))
from parse_replay import parse   # noqa: E402
import replay_metrics as rm      # noqa: E402


def med(v):
    return round(statistics.median(v), 1) if v else 0


def analyze(path, meta, target):
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
    head_of = {i: body[i][0] for i in body}
    child_birth = {}

    T = 'A' if meta['A'] == target else 'B'
    out = {'map': meta['map'], 'T': T, 'NC': NC,
           'win': None, 'rounds': 0,
           'splits': collections.Counter(), 'deaths': collections.Counter(),
           'reasons': {T: collections.Counter(), 'AB'[1 - 'AB'.index(T)]: collections.Counter()},
           'reasons_early': {T: collections.Counter(), 'AB'[1 - 'AB'.index(T)]: collections.Counter()},
           'nva_adj': {s: [] for s in 'AB'}, 'nva_dchamp': {s: [] for s in 'AB'},
           'suic': collections.Counter(), 'don15': collections.Counter(),
           'eaten': collections.Counter(),
           'q_died': {}, 'q_endlen': {}, 'q_len100': {},
           'alive_end': collections.Counter(), 'tot_end': collections.Counter(),
           'long_end': collections.Counter(),
           'nva_per_r': {s: collections.Counter() for s in 'AB'},
           'end_top': {s: [] for s in 'AB'}}
    O = 'AB'[1 - 'AB'.index(T)]
    rnd = 0
    actor = None
    champ = {s: None for s in 'AB'}   # rolling longest id

    def maxlen(s):
        return max((len(b) for i, b in body.items() if team.get(i) == s), default=0)

    for e in ev:
        ty = e['type']
        if ty == 'roundStart':
            rnd = e['round']
            out['rounds'] = max(out['rounds'], rnd)
            if rnd == 99:
                for s in 'AB':
                    q = queen[s]
                    out['q_len100'][s] = len(body[q]) if q in body else 0
            continue
        if ty == 'turnStart':
            actor = e['id']
            continue
        if ty == 'tileChange':
            if not e.get('hasPearl') and actor is not None and team.get(actor):
                out['eaten'][team[actor]] += 1
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
            out['splits'][s] += 1
            continue
        if ty == 'dragonDeath':
            i = e['id']
            s = team.get(i)
            if s:
                out['deaths'][s] += 1
                out['reasons'][s][e['reason']] += 1
                if rnd <= 100:
                    out['reasons_early'][s][e['reason']] += 1
                if i == queen[s]:
                    out['q_died'][s] = (rnd, e['reason'])
                dc = head_of.get(i)
                if dc and e['reason'] == 'noValidAction':
                    own = [tcheb(dc, h) for j, h in head_of.items() if j != i and team.get(j) == s]
                    out['nva_adj'][s].append(min(own) if own else 99)
                    # dist to own longest dragon head
                    li, ll = None, -1
                    for j, b in body.items():
                        if team.get(j) == s and j != i and len(b) > ll:
                            li, ll = j, len(b)
                    if li is not None:
                        out['nva_dchamp'][s].append(tcheb(dc, head_of[li]))
                    out['nva_per_r'][s][rnd // 10] += 1
                if e['reason'] in ('hitWall', 'hitSelf'):
                    out['suic'][s] += 1
                    if i in child_birth and rnd - child_birth[i] <= 15:
                        out['don15'][s] += 1
            body.pop(i, None)
            head_of.pop(i, None)

    for s in 'AB':
        alive = [i for i in body if team.get(i) == s]
        out['alive_end'][s] = len(alive)
        out['tot_end'][s] = sum(len(body[i]) for i in alive)
        out['long_end'][s] = max((len(body[i]) for i in alive), default=0)
        out['end_top'][s] = sorted((len(body[i]) for i in alive), reverse=True)[:3]
        if queen[s] in body:
            out['q_endlen'][s] = len(body[queen[s]])
    w = meta.get('w')
    out['win'] = (w == 'a' and T == 'A') or (w == 'b' and T == 'B')
    return out


def fmt_reasons(c, tot):
    return ' '.join(f'{k}:{v}({v * 100 // max(1, tot)}%)' for k, v in c.most_common())


def main():
    d, target = sys.argv[1], int(sys.argv[2])
    games = []
    for f in sorted(glob.glob(os.path.join(d, '*.replay'))):
        meta = json.load(open(f.replace('.replay', '.json')))
        try:
            games.append(analyze(f, meta, target))
        except Exception as ex:
            print('FAIL', f, ex)
    T = None
    agg = collections.defaultdict(list)
    mapwl = collections.defaultdict(lambda: [0, 0])
    print(f'\n=== {len(games)} games for team {target} ===')
    for g in games:
        T = g['T']; O = 'AB'[1 - 'AB'.index(T)]
        wl = 'W' if g['win'] else 'L'
        mapwl[g['map']][0 if g['win'] else 1] += 1
        elim = g['rounds'] < 450
        qT = g['q_died'].get(T)
        print(f"{wl} {g['map'][:20]:<21} r{g['rounds']:<3} {'ELIM' if elim else 'lim '}"
              f" spl {g['splits'][T]:>3}v{g['splits'][O]:>3}"
              f" dth {g['deaths'][T]:>3}v{g['deaths'][O]:>3}"
              f" nva {g['reasons'][T]['noValidAction']:>3}v{g['reasons'][O]['noValidAction']:>3}"
              f" suic {g['suic'][T]:>2}v{g['suic'][O]:>2}"
              f" long {g['long_end'][T]:>3}v{g['long_end'][O]:>3}"
              f" alive {g['alive_end'][T]:>2}v{g['alive_end'][O]:>2}"
              f" q:{qT if qT else 'alive' + str(g['q_endlen'].get(T, 0))}")
        for k in ('splits', 'deaths', 'suic', 'don15', 'eaten'):
            agg['T_' + k].append(g[k][T])
            agg['O_' + k].append(g[k][O])
        agg['T_nva'].append(g['reasons'][T]['noValidAction'])
        agg['O_nva'].append(g['reasons'][O]['noValidAction'])
        agg['T_h2h'].append(g['reasons'][T]['hitHeadToHead'])
        agg['T_long'].append(g['long_end'][T])
        agg['O_long'].append(g['long_end'][O])
        agg['T_alive'].append(g['alive_end'][T])
        agg['nva_adj_T'] += g['nva_adj'][T]
        agg['nva_dchamp_T'] += g['nva_dchamp'][T]
        if g['win']:
            agg['W_T_nva'].append(g['reasons'][T]['noValidAction'])
        else:
            agg['L_T_nva'].append(g['reasons'][T]['noValidAction'])
            agg['L_map'].append(g['map'])
            agg['L_rounds'].append(g['rounds'])
    print('\n=== map W-L ===')
    for mp, (w, l) in sorted(mapwl.items()):
        print(f'  {mp:<24} {w}W {l}L')
    print('\n=== medians T (target) vs O (opponents) ===')
    for k in ('splits', 'deaths', 'suic', 'don15', 'eaten'):
        print(f'  {k:<10} T {med(agg["T_" + k]):>6}   O {med(agg["O_" + k]):>6}')
    print(f'  nva        T {med(agg["T_nva"]):>6}   O {med(agg["O_nva"]):>6}   (W games T:{med(agg["W_T_nva"])} L games T:{med(agg["L_T_nva"])})')
    print(f'  h2h        T {med(agg["T_h2h"]):>6}')
    print(f'  long@end   T {med(agg["T_long"]):>6}   O {med(agg["O_long"]):>6}')
    print(f'  alive@end  T {med(agg["T_alive"]):>6}')
    print(f'  nva_adj    T med {med(agg["nva_adj_T"])}  share<=3: {sum(1 for x in agg["nva_adj_T"] if x <= 3) * 100 // max(1, len(agg["nva_adj_T"]))}%')
    print(f'  nva_dchamp T med {med(agg["nva_dchamp_T"])}  share<=8: {sum(1 for x in agg["nva_dchamp_T"] if x <= 8) * 100 // max(1, len(agg["nva_dchamp_T"]))}%')
    qd = [g for g in games if g['q_died'].get(g['T'])]
    print(f'\nqueen died in {len(qd)}/{len(games)} games;',
          'reasons:', collections.Counter(q['q_died'][q['T']][1] for q in qd).most_common(),
          'med round:', med([q['q_died'][q['T']][0] for q in qd]))
    print('losses:', collections.Counter(agg['L_map']).most_common(), 'med end round:', med(agg['L_rounds']))
    json_out = {'games': [{k: (dict(v) if isinstance(v, collections.Counter) else v) for k, v in g.items() if k not in ('nva_adj', 'nva_dchamp', 'nva_per_r', 'end_top')} for g in games]}
    json.dump(json_out, open(f'/tmp/bracket_{target}.json', 'w'), default=str)


if __name__ == '__main__':
    main()
