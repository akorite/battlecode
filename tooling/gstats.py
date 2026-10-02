"""Per-game stats extractor for local/ladder replays.

Usage: python3 gstats.py <replay> [<replay> ...]
Prints one JSON line per game: counters per team plus per-round alive history.
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
from parse_replay import parse
import importlib.util
_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    'bc_mapdata', os.path.join(_HERE, '../handoff/tooling/battlecode-eval/bceval/mapdata.py'))
_mapdata = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_mapdata)


def game_stats(path):
    rep = parse(path)
    board = _mapdata.map_data(rep['map'])
    # map starting dragons to ids in creation order by matching head positions
    start_pos = {d['body'][0]: d['team'] for d in board['dragons']}
    team_of = {}          # dragon id -> 'A'/'B'
    n_start = {'A': 0, 'B': 0}
    for e in rep['events']:
        if e['type'] == 'roundStart':
            break
        if e['type'] == 'dragonUpdate' and tuple(e['head']) in start_pos:
            team_of[e['id']] = start_pos[tuple(e['head'])]
            n_start[team_of[e['id']]] += 1
    T = {s: dict(actions=0, moves=0, steps=0, sprints=0, sprintCost=0, splits=0,
                 suicides=0, badSplits=0, badSteps=0, deaths=0,
                 death_hitWall=0, death_hitSelf=0, death_hitOtherBody=0,
                 death_hitHeadToHead=0, death_noValidAction=0,
                 sonar=0, sonar_kelp=0, sonar_ally=0, sonar_allyHead=0,
                 sonar_enemy=0, sonar_enemyHead=0, sonar_empty=0,
                 pearlsEaten=0, tle=0, instrMax=0, instrExceeded=0)
         for s in 'AB'}
    alive = {'A': n_start['A'], 'B': n_start['B']}
    hist = {'A': [], 'B': []}
    last_action = {}
    cur = None
    rnd = 0
    max_alive = {'A': n_start['A'], 'B': n_start['B']}
    # Slay Queen: each team's queen is its lowest-id dragon.
    queen_id = {}
    for _id, _t in team_of.items():
        if _t not in queen_id or _id < queen_id[_t]:
            queen_id[_t] = _id
    # Queen's starting length: dragons are listed in creation order (ids 0,1,...).
    qlen = {s: len(board['dragons'][queen_id[s]]['body']) if s in queen_id and queen_id[s] < len(board['dragons']) else 2
            for s in 'AB'}
    qmax = {s: qlen[s] for s in 'AB'}
    qdead = {'A': None, 'B': None}                     # round the queen died
    qate = {'A': 0, 'B': 0}                            # pearls eaten BY the queen
    qhead = {'A': None, 'B': None}                     # last known queen head
    def _qside(_id):
        for _s in 'AB':
            if queen_id.get(_s) == _id:
                return _s
        return None
    for e in rep['events']:
        ty = e['type']
        if ty == 'roundStart':
            rnd = e['round']
            hist['A'].append(alive['A']); hist['B'].append(alive['B'])
        elif ty == 'turnStart':
            cur = e['id']
        elif ty == 'dragonAction':
            d = team_of.get(e['id'])
            if d is None:
                continue
            t = T[d]
            t['actions'] += 1
            a = e.get('action') or {}
            k = a.get('kind')
            last_action[e['id']] = k
            if k == 'move':
                t['moves'] += 1
                st = len(a.get('steps', []))
                t['steps'] += st
                if st > 1:
                    t['sprints'] += 1
                    t['sprintCost'] += st - 1
                qs = _qside(e['id'])
                if qs and qdead[qs] is None:
                    paid = max(0, st - (qlen[qs] + 3) // 4)
                    qlen[qs] = max(0, qlen[qs] - paid)
            elif k == 'split':
                t['splits'] += 1
            elif k == 'suicide':
                pass  # counted at death
            ins = e.get('instructions')
            if ins:
                t['instrMax'] = max(t['instrMax'], ins.get('count', 0))
                if ins.get('exceeded'):
                    t['instrExceeded'] += 1
            if e.get('tle'):
                t['tle'] += 1
        elif ty == 'dragonSplit':
            d = e['team']
            team_of[e['childId']] = d
            team_of[e['parentId']] = d
            alive[d] += 1
            max_alive[d] = max(max_alive[d], alive[d])
            qs = _qside(e['parentId'])
            if qs and qdead[qs] is None:
                qlen[qs] = max(0, qlen[qs] - e.get('childSegmentCount', 0))
        elif ty == 'dragonDeath':
            d = team_of.get(e['id'])
            if d is None:
                # victim id we never saw act (h2h victim before first action): infer from map? rare
                continue
            alive[d] -= 1
            qs = _qside(e['id'])
            if qs and qdead[qs] is None:
                qdead[qs] = rnd

            t = T[d]
            t['deaths'] += 1
            rsn = e['reason']
            t['death_' + rsn] = t.get('death_' + rsn, 0) + 1
            if rsn == 'noValidAction':
                la = last_action.get(e['id'])
                if la == 'suicide':
                    t['suicides'] += 1
                elif la == 'split':
                    t['badSplits'] += 1
                else:
                    t['badSteps'] += 1
        elif ty == 'sonarPing':
            d = team_of.get(e['senderId'])
            if d is None:
                continue
            t = T[d]
            t['sonar'] += 1
            hk = e.get('hitKind')
            if hk:
                t['sonar_' + hk] = t.get('sonar_' + hk, 0) + 1
        elif ty == 'dragonUpdate':
            qs = _qside(e['id'])
            if qs:
                qhead[qs] = e['head']
        elif ty == 'tileChange':
            if not e['hasPearl'] and cur is not None:
                d = team_of.get(cur)
                if d:
                    T[d]['pearlsEaten'] += 1
                qs = _qside(cur)
                if qs and qdead[qs] is None:
                    qlen[qs] += 1
                    qate[qs] += 1
                    qmax[qs] = max(qmax[qs], qlen[qs])
    res = rep.get('result') or {}
    out = {
        'map': board['name'], 'botA': rep['botA'], 'botB': rep['botB'],
        'rounds': rnd + 1, 'winner': res.get('winner'),
        'endReason': res.get('endReason'), 'terminated': res.get('terminated'),
        'resA': res.get('teamA'), 'resB': res.get('teamB'),
        'teams': T, 'maxAlive': max_alive, 'aliveHist': hist,
        'nStart': n_start,
        'queenLen': qlen, 'queenMaxLen': qmax, 'queenDeathRound': qdead,
        'queenAte': qate,
    }
    # per-action sonar rate
    for s in 'AB':
        T[s]['sonarPerAction'] = round(T[s]['sonar'] / max(1, T[s]['actions']), 3)
    return out


def summarize(rows, side=None):
    """Aggregate stats dicts -> compact means. side='A'|'B'|None(both)."""
    agg = {}
    n = 0
    wins = 0
    for g in rows:
        for s in 'AB':
            if side and s != side:
                continue
            t = g['teams'][s]
            for k, v in t.items():
                agg[k] = agg.get(k, 0) + v
            n += 1
            if g['winner'] == s:
                wins += 1
        agg.setdefault('_rounds', 0)
        agg['_rounds'] += g['rounds']
        agg.setdefault('_games', 0)
        agg['_games'] += 1
    games = agg.pop('_games')
    rounds = agg.pop('_rounds')
    out = {k: round(v / n, 2) for k, v in agg.items()}
    out['games'] = games
    out['teamGames'] = n
    out['avgRounds'] = round(rounds / max(1, games), 1)
    out['winRate'] = round(wins / max(1, n), 3)
    out['peakAlive'] = round(sum(g['maxAlive'][s] for g in rows for s in 'AB' if not side or s == side) / max(1, n), 2)
    return out


if __name__ == '__main__':
    for p in sys.argv[1:]:
        print(json.dumps(game_stats(p)))
