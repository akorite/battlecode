#!/usr/bin/env python3
"""Ladder loss census: classify each v157-era game by loss cause.
Joins matches list (seat/opponent) with replay_metrics per replay.
Usage: ladder_census.py [--json]
Causes: queen-dead | outfed | elim | feed-race | longest-race | win"""
import json, os, subprocess, sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)


def main():
    import argparse as _ap
    _p=_ap.ArgumentParser(); _p.add_argument('--dir',default='ladder_replays'); _p.add_argument('--cut',type=int,default=0); _a=_p.parse_args()
    import urllib.request, re
    d = urllib.request.urlopen(urllib.request.Request(
        'https://game.battlecode.au/teams/351', headers={'User-Agent': 'bc-scout'}), timeout=20).read().decode('utf8', 'replace')
    idx = d.find('history:[')
    hist = re.findall(r'\{date:"([^"]+)",elo:(\d+)\}', d[idx:])
    deploy = None
    for i in range(1, len(hist)):
        if int(hist[i][1]) == 1500 and int(hist[i - 1][1]) != 1500:
            deploy = hist[i][0]
    print('# last submission reset (v157 deploy):', deploy, file=sys.stderr)

    import datetime
    # matches via ladder.py
    p = subprocess.run([sys.executable, os.path.join(BASE, 'ladder.py'), 'matches', '--team', '351', '--pages', '4'],
                       capture_output=True, text=True)
    ms = [json.loads(l) for l in p.stdout.splitlines() if l.strip().startswith('{')]
    from email.utils import parsedate_to_datetime
    dep_ms = _a.cut or int(datetime.datetime.fromisoformat(deploy.replace('Z', '+00:00')).timestamp() * 1000)
    ms = [m for m in ms if m['at'] >= dep_ms]
    print(f'# v157-era matches: {len(ms)}', file=sys.stderr)

    rows = []
    for m in ms:
        rp = os.path.join(os.path.dirname(BASE), _a.dir, f"m{m['id']}.replay")
        if not os.path.exists(rp):
            continue
        out = subprocess.run([sys.executable, os.path.join(BASE, 'replay_metrics.py'), rp],
                             capture_output=True, text=True)
        line = [l for l in out.stdout.splitlines() if l.strip().startswith('{')]
        if not line:
            continue
        g = json.loads(line[0])
        ours = 'a' if m['a']['id'] == 351 else 'b'
        s = g.get(ours.upper()) or {}
        o = g.get('B' if ours == 'a' else 'A') or {}
        win = s.get('win', False)
        cause = 'win'
        if not win:
            end = g.get('end', '')
            if 'elim' in end.lower() or end == 'eliminated':
                cause = 'elim'
            elif s.get('qDeadRound') and not o.get('qDeadRound'):
                cause = 'queen-dead'
            elif s.get('qDeadRound') and o.get('qDeadRound'):
                cause = 'both-dead-race'
            elif (o.get('queenEnd') or 0) - (s.get('queenEnd') or 0) >= 8:
                cause = 'outfed'
            elif s.get('total', 0) > o.get('total', 0) * 1.5:
                cause = 'longest-race'
            else:
                cause = 'feed-race'
        rows.append(dict(id=m['id'], map=m['map'], seat=ours.upper(), win=win, cause=cause,
                         opp=m['b' if ours == 'a' else 'a']['name'], elo=m['b' if ours == 'a' else 'a']['elo'],
                         end=g.get('end'), rounds=g.get('rounds'), qdead=s.get('qDeadRound'), qwhy=s.get('qDeadReason'),
                         oqdead=o.get('qDeadRound'), qlen=s.get('queenEnd'), qeat=s.get('qEaten'), oqeat=o.get('qEaten'), oqlen=o.get('queenEnd'),
                         longest=s.get('longest'), olongest=o.get('longest'),
                         total=s.get('total'), ototal=o.get('total'), eaten=s.get('eaten'), oeaten=o.get('eaten')))
        rows[-1] = {k: v for k, v in rows[-1].items()}
    for r in rows:
        tag = ' ' if r['win'] else '*'
        print(f"{tag} {r['id']} {r['map'][:16]:16s} {r['seat']} {'W' if r['win'] else 'L'} {r['cause']:15s} "
              f"end={str(r['end']):12s} qd={str(r['qdead']):>4s}/{str(r['qwhy'])[:16]:16s} "
              f"ql={str(r['qlen']):>4s}v{str(r['oqlen']):<4s} ln={str(r['longest'])}v{str(r['olongest'])} "
              f"tot={r['total']}v{r['ototal']} e={r['eaten']}v{r['oeaten']} qe={r.get('qeat')}v{r.get('oqeat')} vs {r['opp'][:18]}")
    import collections
    c = collections.Counter(r['cause'] for r in rows if not r['win'])
    print('\nloss causes:', dict(c), f"(n={sum(c.values())})")


if __name__ == '__main__':
    main()
