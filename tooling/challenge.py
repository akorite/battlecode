"""Challenge-battle helpers: POST battles vs a specific team, poll status,
download the replay when done. Auth: ~/.unswbc/keys.json bearer.

  python3 tooling/challenge.py post --team 306 [--n 5]          # queue n games vs team id
  python3 tooling/challenge.py status <battle_id> [<id>...]
  python3 tooling/challenge.py pull <battle_id> [--out replays] # wait + download + gstats
  python3 tooling/challenge.py bench --teams 306,20,206,314,213 [--each 4]
"""
import argparse, gzip, json, os, sys, time, urllib.request

BASE = 'https://game.battlecode.au'
KEYS = os.path.expanduser('~/.unswbc/keys.json')

def key():
    d = json.load(open(KEYS))
    return list(d.values())[0]

def req(method, path, body=None):
    r = urllib.request.Request(f'{BASE}/api/v1/{path}', method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={'Authorization': f'Bearer {key()}', 'Content-Type': 'application/json',
                 'User-Agent': 'unswbc/1.2.3'})
    try:
        return json.loads(urllib.request.urlopen(r, timeout=60).read() or b'{}')
    except urllib.error.HTTPError as e:
        sys.exit(f'{method} {path}: {e.code} {e.read()[:300]!r}')

def post(team, ranked=False):
    return req('POST', 'battles', {'teamId': team, 'ranked': ranked})['ids']

def status(bid):
    d = req('GET', f'battles/{bid}')
    m = d['match']
    us = 'a' if m.get('teamAId') == 351 else 'b'  # our team id; battles we post put us on side A
    return {'id': m['id'], 'status': m['status'], 'map': d['mapName'],
            'vs': d['teamBName'] if us == 'a' else d.get('teamAName'),
            'winner': m['winner'], 'us': us, 'won': m['winner'] == us,
            'games': [(g['id'], g['status'], g.get('winner'), g.get('hasReplay'))
                      for g in d['games']]}

def replay(match_id, outdir):
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, f'm{match_id}.replay')
    if os.path.exists(path):
        return path
    r = urllib.request.Request(f'{BASE}/api/matches/{match_id}/replay',
                               headers={'User-Agent': 'bc-scout'})
    data = urllib.request.urlopen(r, timeout=60).read()
    try:
        data = gzip.decompress(data)
    except OSError:
        pass
    open(path, 'wb').write(data)
    return path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['post', 'status', 'pull', 'bench', 'me'])
    ap.add_argument('ids', nargs='*', type=int)
    ap.add_argument('--team', type=int, default=0)
    ap.add_argument('--teams', default='')
    ap.add_argument('--n', type=int, default=1)
    ap.add_argument('--each', type=int, default=4)
    ap.add_argument('--ranked', action='store_true')
    ap.add_argument('--out', default=os.path.join(os.environ.get('BC_REPO', os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'ladder_replays'))
    ap.add_argument('--wait', type=int, default=900)
    a = ap.parse_args()

    if a.cmd == 'me':
        print(json.dumps(req('GET', 'me'), indent=1))
    elif a.cmd == 'post':
        for _ in range(a.n):
            print(post(a.team, a.ranked))
            time.sleep(1)
    elif a.cmd == 'status':
        for bid in a.ids:
            print(json.dumps(status(bid)))
    elif a.cmd == 'pull':
        deadline = time.time() + a.wait
        for bid in a.ids:
            while True:
                s = status(bid)
                done = all(g[1] in ('finished', 'done', 'completed') or g[3] for g in s['games'])
                if done or s['status'] in ('finished', 'done', 'completed'):
                    break
                if time.time() > deadline:
                    print(bid, 'TIMEOUT', json.dumps(s)); break
                time.sleep(15)
            print(json.dumps(s))
            for gid, gs, gw, rep in s['games']:
                if rep:
                    print(' ', gid, s['map'], 'winner', gw, '->', replay(gid, a.out))
    elif a.cmd == 'bench':
        all_ids = []
        for t in a.teams.split(','):
            ids = []
            for _ in range(a.each):
                ids += post(int(t), a.ranked)
                time.sleep(1)
            print(f'team {t}: queued {ids}')
            all_ids += ids
        print('ALL', ' '.join(map(str, all_ids)))

if __name__ == '__main__':
    main()
