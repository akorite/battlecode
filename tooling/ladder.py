"""Ladder helpers: fetch our (or any team's) recent matches + download replays.

The games page embeds SvelteKit objects as JS literals — parse loosely.

  python3 tooling/ladder.py matches --team <id> [--pages 3]
  python3 tooling/ladder.py replays --team <id> [--n 20] [--out ladder_replays]
  python3 tooling/ladder.py find --name Cognoscenti        # locate team id
"""
import argparse, gzip, json, os, re, sys, urllib.request

BASE = 'https://game.battlecode.au'

def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'bc-scout'})
    return urllib.request.urlopen(req, timeout=30).read()

MATCH_RE = re.compile(
    r'\{id:(\d+),ranked:(?:true|false),status:"(\w+)",winner:"(\w+)",hasReplay:(true|false),'
    r'challenge:(?:true|false),tournament:(?:true|false),at:new Date\((\d+)\),mapName:"([^"]+)",'
    r'a:\{id:(\d+),name:"([^"]+)",elo:([\d.]+)\},b:\{id:(\d+),name:"([^"]+)",elo:([\d.]+)\}')

def matches(team, pages=3):
    out = []
    for p in range(1, pages + 1):
        html = get(f'{BASE}/games?teams={team}&page={p}').decode('utf-8', 'replace')
        found = MATCH_RE.findall(html)
        if not found:
            break
        for m in found:
            out.append({
                'id': int(m[0]), 'status': m[1], 'winner': m[2],
                'hasReplay': m[3] == 'true', 'at': int(m[4]), 'map': m[5],
                'a': {'id': int(m[6]), 'name': m[7], 'elo': float(m[8])},
                'b': {'id': int(m[9]), 'name': m[10], 'elo': float(m[11])},
            })
    return out

def replay(match_id, outdir):
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, f'm{match_id}.replay')
    if os.path.exists(path):
        return path
    data = get(f'{BASE}/api/matches/{match_id}/replay')
    try:
        data = gzip.decompress(data)
    except OSError:
        pass
    open(path, 'wb').write(data)
    return path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['matches', 'replays', 'find'])
    ap.add_argument('--team', type=int, default=0)
    ap.add_argument('--name', default='')
    ap.add_argument('--pages', type=int, default=3)
    ap.add_argument('--n', type=int, default=20)
    ap.add_argument('--out', default=os.path.join(os.environ.get('BC_REPO', os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'ladder_replays'))
    a = ap.parse_args()

    if a.cmd == 'matches':
        for m in matches(a.team, a.pages):
            print(json.dumps(m))
    elif a.cmd == 'replays':
        got = 0
        for m in matches(a.team, a.pages):
            if got >= a.n:
                break
            if not m['hasReplay']:
                continue
            try:
                p = replay(m['id'], a.out)
                opp = m['a']['name'] if m['b']['id'] == a.team else m['b']['name']
                print(m['id'], m['map'], 'vs', opp, '->', p)
                got += 1
            except Exception as e:
                print(m['id'], 'FAIL', e, file=sys.stderr)
    elif a.cmd == 'find':
        # scan recent games until the name shows up
        for t in range(1, 100):
            html = get(f'{BASE}/games?page={t}').decode('utf-8', 'replace')
            for m in MATCH_RE.findall(html):
                for side, off in (('a', 6), ('b', 9)):
                    if a.name.lower() in m[off + 1].lower():
                        print(m[0], m[5], m[off], m[off + 1], 'elo', m[off + 2])
            if t > 60 and not a.name:
                break

if __name__ == '__main__':
    main()
