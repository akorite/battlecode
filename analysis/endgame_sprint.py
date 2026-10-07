"""Endgame forensics: is there a scripted sprint at the bell?

On top-10-vs-top-10 replays that reached roundLimit:
  (a) nva deaths in last 60r, winners vs losers (mass-suicide into champ?)
  (b) winner totalLength r440 -> r500 (liquidation vs churn)
  (c) mean worker dist-to-queen trend r440->500 (convergence?)

Usage: python3 analysis/endgame_sprint.py
"""
import collections, glob, json, os, statistics, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../tooling'))
from parse_replay import parse  # noqa: E402
import replay_metrics as rm    # noqa: E402

WINDOW = 60  # last 60 rounds


def analyze(path, meta):
    r = parse(path)
    ev = r['events']
    W, H, dr, edges = rm.parse_map(r['map'])
    team = {i: 'AB'[t] for i, (t, b) in enumerate(dr)}
    queen = {s: min(i for i in team if team[i] == s) for s in 'AB'}
    body = {i: collections.deque(tuple(x) for x in b) for i, (t, b) in enumerate(dr)}

    def tcheb(a, b):
        dx = min(abs(a[0] - b[0]), W - abs(a[0] - b[0]))
        dy = min(abs(a[1] - b[1]), H - abs(a[1] - b[1]))
        return max(dx, dy)

    # snapshots per round
    tot_len = collections.defaultdict(dict)      # rnd -> {team: totalLen}
    alive_n = collections.defaultdict(dict)      # rnd -> {team: n}
    worker_dq = collections.defaultdict(dict)    # rnd -> {team: mean dist worker->queen}
    nva = collections.defaultdict(lambda: collections.Counter())  # rnd -> team -> nva deaths
    nva_dq = []                                  # (rnd, team, dist dead->queen, dist dead->champ)
    last_r = 0

    for e in ev:
        if not isinstance(e, dict):
            continue
        ty = e['type']
        if ty == 'roundStart':
            rnd = e['round']
            last_r = max(last_r, rnd)
            for s in 'AB':
                hs = [b for i, b in body.items() if team[i] == s]
                if hs:
                    tot_len[rnd][s] = sum(len(b) for b in hs)
                    alive_n[rnd][s] = len(hs)
                    q = queen[s]
                    if q in body:
                        qh = body[q][0]
                        ds = [tcheb(b[0], qh) for i, b in body.items() if team[i] == s and i != q]
                        if ds:
                            worker_dq[rnd][s] = statistics.mean(ds)
            continue
        if ty == 'dragonUpdate':
            i = e['id']
            if i not in body:
                continue
            b = body[i]
            h, tl = tuple(e['head']), tuple(e['tail'])
            if b[0] != h:
                b.appendleft(h)
                while len(b) > 1 and b[-1] != tl:
                    b.pop()
            continue
        if ty == 'dragonSplit':
            team[e['childId']] = e['team']
            body[e['parentId']] = collections.deque(tuple(x) for x in e['parentBody'])
            body[e['childId']] = collections.deque(tuple(x) for x in e['childBody'])
            continue
        if ty == 'dragonDeath':
            i = e['id']
            s = team.get(i)
            if e['reason'] == 'noValidAction' and s:
                nva[rnd][s] += 1
                # distances at death round (head snapshot = last body head)
                dh = body[i][0]
                q = queen[s]
                dq = tcheb(dh, body[q][0]) if q in body else None
                mates = [(len(b), b[0]) for j, b in body.items() if j != i and team.get(j) == s]
                dch = None
                if mates:
                    ch = max(mates)[1]
                    dch = tcheb(dh, ch)
                nva_dq.append((rnd, s, dq, dch))
            body.pop(i, None)

    return {'map': meta['map'], 'a': meta['a']['name'], 'b': meta['b']['name'],
            'winner': meta['winner'], 'last_r': last_r,
            'tot_len': dict(tot_len), 'alive_n': dict(alive_n),
            'worker_dq': dict(worker_dq), 'nva': dict(nva), 'nva_dq': nva_dq}


def bin10(rr):
    return rr // 10 * 10


def main():
    games = []
    for f in sorted(glob.glob('toptop_replays/*.replay')):
        meta = json.load(open(f.replace('.replay', '.json')))
        try:
            games.append(analyze(f, meta))
        except Exception as ex:
            print(f, 'FAIL', repr(ex)[:120])

    # only games that reached roundLimit: last round >= 490
    rl = [g for g in games if g['last_r'] >= 490]
    el = [g for g in games if g['last_r'] < 490]
    print(f"games={len(games)} roundLimit={len(rl)} eliminated-early={len(el)} "
          f"(early last_r: {[g['last_r'] for g in el]})")

    print('\n== (a) nva deaths in last 60r, winner vs loser side ==')
    for won in (True, False):
        cnt = collections.Counter()
        per_game = []
        for g in rl:
            side = (g['winner'] if won else ('b' if g['winner'] == 'a' else 'a')).upper()
            lo = g['last_r'] - WINDOW
            n = sum(c for rr, c in g['nva'].items() for s, cc in [ (None,0) ] if False)
            n = sum(g['nva'].get(rr, {}).get(side, 0) for rr in range(lo, g['last_r'] + 1))
            per_game.append(n)
            for rr in range(lo, g['last_r'] + 1):
                cnt[bin10(rr)] += g['nva'].get(rr, {}).get(side, 0)
        tot = sum(per_game)
        print(f"  {'W' if won else 'L'}: total={tot} med/game={statistics.median(per_game)} "
              f"per10r: " + ' '.join(f'r{k}:{v}' for k, v in sorted(cnt.items())))

    # nva death distances to queen/champ in window
    print('\n  nva deaths r440+: dist dead->champ (rolling-longest) and ->queen')
    for won in (True, False):
        dq, dch = [], []
        for g in rl:
            side = (g['winner'] if won else ('b' if g['winner'] == 'a' else 'a')).upper()
            lo = g['last_r'] - WINDOW
            for (rr, s, q_d, c_d) in g['nva_dq']:
                if s == side and rr >= lo:
                    if q_d is not None: dq.append(q_d)
                    if c_d is not None: dch.append(c_d)
        if dch:
            print(f"  {'W' if won else 'L'}: n={len(dch)} med dChamp={statistics.median(dch)} med dQueen={statistics.median(dq) if dq else 'n/a'} "
                  f"| <=8: {sum(1 for d in dch if d<=8)/len(dch):.2f} <=12: {sum(1 for d in dch if d<=12)/len(dch):.2f}")

    print('\n== (b) winner totalLength last 60r (r440 vs r500-ish) ==')
    for won in (True, False):
        starts, ends, deltas = [], [], []
        for g in rl:
            side = (g['winner'] if won else ('b' if g['winner'] == 'a' else 'a')).upper()
            lo = g['last_r'] - WINDOW
            s0 = g['tot_len'].get(lo, {}).get(side)
            s1 = g['tot_len'].get(g['last_r'], {}).get(side)
            if s0 and s1:
                starts.append(s0); ends.append(s1); deltas.append(s1 - s0)
        if deltas:
            print(f"  {'W' if won else 'L'}: n={len(deltas)} med r440={statistics.median(starts)} -> end={statistics.median(ends)} "
                  f"delta med={statistics.median(deltas)} mean={statistics.mean(deltas):+.1f} "
                  f"grew:{sum(1 for d in deltas if d>0)}/{len(deltas)}")

    print('\n== (c) mean worker dist-to-queen trend last 60r ==')
    for won in (True, False):
        bybin = collections.defaultdict(list)
        for g in rl:
            side = (g['winner'] if won else ('b' if g['winner'] == 'a' else 'a')).upper()
            lo = g['last_r'] - WINDOW
            for rr in range(lo, g['last_r'] + 1):
                v = g['worker_dq'].get(rr, {}).get(side)
                if v is not None:
                    bybin[bin10(rr)].append(v)
        print(f"  {'W' if won else 'L'}: " + ' '.join(f'r{k}:{statistics.mean(v):.1f}' for k, v in sorted(bybin.items())))

    print('\n== per-game summary (roundLimit games) ==')
    for g in rl:
        ws, ls_ = g['winner'].upper(), ('B' if g['winner'] == 'a' else 'A')
        lo = g['last_r'] - WINDOW
        w0, w1 = g['tot_len'].get(lo, {}).get(ws), g['tot_len'].get(g['last_r'], {}).get(ws)
        l0, l1 = g['tot_len'].get(lo, {}).get(ls_), g['tot_len'].get(g['last_r'], {}).get(ls_)
        wn = sum(g['nva'].get(rr, {}).get(ws, 0) for rr in range(lo, g['last_r']+1))
        ln = sum(g['nva'].get(rr, {}).get(ls_, 0) for rr in range(lo, g['last_r']+1))
        wd0 = g['worker_dq'].get(lo, {}).get(ws); wd1 = g['worker_dq'].get(g['last_r'], {}).get(ws)
        print(f"  {g['map']:<14} {g['a']} v {g['b']} w:{ws} | W totlen {w0}->{w1} nva {wn} dQ {wd0 and round(wd0,1)}->{wd1 and round(wd1,1)} | L totlen {l0}->{l1} nva {ln}")


if __name__ == '__main__':
    main()
