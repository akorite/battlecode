import sys, json, time, datetime
sys.path.insert(0, '/home/ubuntu/.venv-bc/lib/python3.12/site-packages')
from unswbc.api import request

key = json.load(open('/home/ubuntu/.unswbc/keys.json'))['key']
SINCE = '2026-10-03T18:40'   # v106 activation
w = l = 0
per_map = {}
per_opp = {}
n = 0
b = request('battles?limit=100', key)
rows = b if isinstance(b, list) else b.get('battles', [])
for g in rows:
    mid = g.get('id')
    time.sleep(1.6)
    m = request('battles/%d' % mid, key).get('match', {})
    if (m.get('startedAt') or '') < SINCE:
        continue
    if m.get('status') != 'completed':
        continue
    n += 1
    win = m.get('winner')
    mine = 'a' if m.get('teamAId') == 351 else 'b'
    opp = (g.get("teamBName") if mine=="a" else g.get("teamAName"))
    res = 'D' if win is None else ('W' if win == mine else 'L')
    if res == 'W':
        w += 1
    elif res == 'L':
        l += 1
    per_opp[opp] = per_opp.get(opp, [0, 0, 0])
    per_opp[opp][{'W': 0, 'L': 1, 'D': 2}[res]] += 1
    for gm in m.get('games', []):
        pass  # map detail already in match.games? games[] has mapName+winner
    print(mid, m.get('startedAt','')[:19], opp, res,
          'elo', m.get('eloChangeA') if mine == 'a' else m.get('eloChangeB'),
          'games:', [(gm.get('mapName'), gm.get('winner')) for gm in m.get('games', [])])
print('v106 ranked matches:', n, 'W', w, 'L', l)
print('per-opp:', per_opp)
