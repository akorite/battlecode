"""losssurvey lane: pull last-100 battles, per-game detail, and download replays
of every game we lost. Caches raw API responses under ladder_data/.

Usage: python3 tooling/losssurvey_collect.py
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error

ROOT = os.path.expanduser('~/repos/battlecode')
DATA = os.path.join(ROOT, 'ladder_data')
REPLAYS = os.path.join(ROOT, 'ladder_replays')
TEAM = 351

os.makedirs(DATA, exist_ok=True)
os.makedirs(REPLAYS, exist_ok=True)

key = json.load(open(os.path.expanduser('~/.unswbc/keys.json')))['key']


def req(p):
    r = urllib.request.Request(
        f'https://game.battlecode.au/api/v1/{p}',
        headers={'Authorization': f'Bearer {key}',
                 'Origin': 'https://game.battlecode.au',
                 'User-Agent': 'unswbc/1.2.7'})
    return json.loads(urllib.request.urlopen(r, timeout=60).read())


_op = urllib.request.build_opener(
    type('NoRedirect', (urllib.request.HTTPRedirectHandler,),
         {'redirect_request': lambda *a, **k: None}))


def get_replay(game_id, dest):
    if os.path.exists(dest):
        return 'cached'
    r = urllib.request.Request(
        f'https://game.battlecode.au/api/v1/battles/{game_id}/replay',
        headers={'Authorization': f'Bearer {key}',
                 'Origin': 'https://game.battlecode.au',
                 'User-Agent': 'unswbc/1.2.7'})
    try:
        resp = _op.open(r, timeout=60)
        if resp.status != 302:
            return f'http{resp.status}'
        loc = resp.headers.get('Location')
    except urllib.error.HTTPError as e:
        if e.code != 302:
            return f'http{e.code}'
        loc = e.headers.get('Location')
    if not loc:
        return 'noloc'
    try:
        r2 = urllib.request.Request(loc, headers={'User-Agent': 'unswbc/1.2.7'})
        data = urllib.request.urlopen(r2, timeout=120).read()
    except urllib.error.HTTPError as e:
        return f'dl-http{e.code}'
    with open(dest, 'wb') as f:
        f.write(data)
    return f'ok({len(data)}B)'


def main():
    battles = req('battles?limit=100')
    json.dump(battles, open(f'{DATA}/battles_list.json', 'w'), indent=1)
    print(f'battles list: {len(battles)} (ids {battles[0]["id"]}..{battles[-1]["id"]})')

    details = {}
    det_path = f'{DATA}/battle_details.json'
    if os.path.exists(det_path):
        details = json.load(open(det_path))

    for i, b in enumerate(battles):
        bid = b['id']
        if str(bid) in details:
            continue
        try:
            details[str(bid)] = req(f'battles/{bid}')
        except Exception as e:
            print(f'  battle {bid}: detail ERR {e}')
            details[str(bid)] = None
        if i % 10 == 9:
            json.dump(details, open(det_path, 'w'), indent=1)
    json.dump(details, open(det_path, 'w'), indent=1)
    print(f'details: {len(details)}')

    # flatten to per-game rows; our side letter from match teamAId
    rows = []
    for b in battles:
        d = details.get(str(b['id']))
        if not d:
            continue
        m = d['match']
        our = 'a' if m['teamAId'] == TEAM else 'b'
        for g in d['games']:
            if g['status'] != 'completed' or not g.get('hasReplay'):
                continue
            won = g['winner'] == our
            draw = g['winner'] not in ('a', 'b')
            rows.append({
                'gameId': g['id'], 'battleId': b['id'], 'at': b['at'],
                'ranked': b['ranked'], 'map': g['mapName'],
                'opponent': b['opponent'], 'opponentId': b['opponentId'],
                'opponentElo': b['opponentElo'], 'ourSide': our,
                'winner': g['winner'], 'won': won, 'draw': draw,
                'eloChange': b['eloChange'], 'outcome': b['outcome'],
            })
    rows.sort(key=lambda r: r['gameId'])
    json.dump(rows, open(f'{DATA}/games.json', 'w'), indent=1)

    ranked = [r for r in rows if r['ranked']]
    losses = [r for r in ranked if not r['won'] and not r['draw']]
    draws = [r for r in ranked if r['draw']]
    print(f'games: {len(rows)} total, {len(ranked)} ranked '
          f'(W {sum(1 for r in ranked if r["won"])} / L {len(losses)} / D {len(draws)})')
    print(f'unranked: {len(rows)-len(ranked)}')

    idx = []
    for r in losses + draws:
        dest = f'{REPLAYS}/{r["gameId"]}.replay'
        st = get_replay(r['gameId'], dest)
        idx.append({'gameId': r['gameId'], 'file': dest if st.startswith(('ok', 'cached')) else None,
                    'status': st, 'map': r['map'], 'opponent': r['opponent'],
                    'ourSide': r['ourSide'], 'ranked': r['ranked'], 'draw': r['draw']})
        print(f'  {r["gameId"]} {r["map"]:<20} vs {r["opponent"]:<30} side={r["ourSide"]} -> {st}')
        time.sleep(0.05)
    json.dump(idx, open(f'{DATA}/replay_index.json', 'w'), indent=1)
    ok = sum(1 for x in idx if x['file'])
    print(f'replays: {ok}/{len(idx)} downloaded')


if __name__ == '__main__':
    sys.exit(main())
