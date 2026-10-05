"""Conveyor telemetry: feed-window (r360-499) death accounting per side.

Per game/side: nva deaths (die-in-place feeds), hitHeadToHead deaths (transit
losses), hitSelf, other, plus longest@end, total@end, win. Aggregated per
(candidate|base) x map.
Usage: python3 analysis/feed_window_telemetry.py <replay_dir> <cand_name> <base_name>
"""
import collections, glob, os, re, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../tooling'))
from parse_replay import parse  # noqa: E402
import replay_metrics as rm      # noqa: E402

FEED_AT, FEED_STOP = 360, 499


def analyze(path):
    r = parse(path)
    W, H, dr, edges = rm.parse_map(r['map'])
    team = {i: 'AB'[t] for i, (t, b) in enumerate(dr)}
    rnd = 0
    d = {'A': collections.Counter(), 'B': collections.Counter()}
    for e in r['events']:
        ty = e['type']
        if ty == 'roundStart':
            rnd = e['round']
        elif ty == 'dragonSplit':
            team[e['childId']] = e['team']
        elif ty == 'dragonDeath':
            s = team.get(e['id'])
            if s and FEED_AT <= rnd <= FEED_STOP:
                d[s][e['reason']] += 1
                d[s]['deaths'] += 1
    res = r['result'] or {}
    mname = re.search(r'MAP_NAME (.+)', r['map'])
    return {'map': mname.group(1) if mname else '?', 'd': d, 'res': res}


def main():
    rdir, cand, base = sys.argv[1], sys.argv[2], sys.argv[3]
    agg = collections.defaultdict(collections.Counter)
    wins = collections.Counter()
    for f in sorted(glob.glob(os.path.join(rdir, '*.replay'))):
        try:
            a = analyze(f)
        except Exception as ex:
            print('ERR', f, ex); continue
        res = a['res']
        # cand seat letter: parse filename tag or botA/botB (ladder strips; local keeps)
        ba, bb = res.get('botA') or '', res.get('botB') or ''
        # local kmatch replays embed bot names
        cseat = 'A' if cand in ba else ('B' if cand in bb else None)
        if cseat is None:
            # fall back: check dir names in path or skip
            m = re.search(r'([AB])_?cand', os.path.basename(f))
            cseat = m.group(1) if m else 'A'
        bseat = 'B' if cseat == 'A' else 'A'
        for seat, who in [(cseat, 'cand'), (bseat, 'base')]:
            for k, v in a['d'][seat].items():
                agg[(a['map'], who)][k] += v
                agg[('ALL', who)][k] += v
            tr = res.get('team' + seat, {})
            agg[(a['map'], who)]['longest'] += tr.get('longestDragon', 0)
            agg[('ALL', who)]['longest'] += tr.get('longestDragon', 0)
            agg[(a['map'], who)]['games'] += 1
            agg[('ALL', who)]['games'] += 1
        win = res.get('winner')
        wins[(a['map'], 'cand' if win == cseat else 'base')] += 1
        wins[('ALL', 'cand' if win == cseat else 'base')] += 1
    maps = sorted({k[0] for k in agg if k[0] != 'ALL'}) + ['ALL']
    print(f'{"map":16s} {"who":5s} {"g":>3s} {"nva":>5s} {"h2h":>5s} {"self":>5s} {"wall":>5s} {"other":>5s} {"longest":>7s} {"win":>4s}')
    for m in maps:
        for who in ('cand', 'base'):
            c = agg[(m, who)]
            g = max(1, c['games'])
            print(f'{m:16s} {who:5s} {c["games"]:>3d} {c["noValidAction"]/g:5.1f} {c["hitHeadToHead"]/g:5.1f} '
                  f'{c["hitSelf"]/g:5.1f} {c["hitWall"]/g:5.1f} '
                  f'{(c["hitOtherBody"]+c["tle"]+c["instructions"])/g:5.1f} {c["longest"]/g:7.1f} '
                  f'{wins[(m,who)]:>4d}')


if __name__ == '__main__':
    main()
