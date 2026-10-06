"""v315 funnel audit: loss classification + conveyor verification.

Part 1 (games.jsonl): classify each cand loss under production rules —
  ELIM (teamEliminated) / LONGEST (roundLimit, c.longest<b.longest) /
  TOTAL (longest tie, total behind) / DRAW.
  Annotate: queen death round/reason, champ-length gap, queen==our-longest.

Part 2 (replays): funnel check — fraction of noValidAction deaths during the
  feed window whose last head is within cheb-2 of the own queen's head
  (die-in-place at the funnel), per side; nva timing histogram; alive counts.

Usage: python3 analysis/v315_funnel.py <results_dir>
"""
import collections, glob, json, os, re, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../tooling'))
from parse_replay import parse  # noqa: E402
import replay_metrics as rm      # noqa: E402

FEED_AT, FEED_STOP, FEED_DIST = 340, 490, 2
CHFEED = re.compile(r'r(\d+) chfeed .*?L=(\d+) .*?fh=(-?\d+) fa=(\d+).*?hx=(\d+) hy=(\d+)')
LOCKED = re.compile(r'r(\d+) (\S+) .*?L=(\d+) .*?fh=(-?\d+) fa=(-?\d+)')


def tdist(a, b, W, H):
    dx = abs(a[0] - b[0]); dx = min(dx, W - dx)
    dy = abs(a[1] - b[1]); dy = min(dy, H - dy)
    return dx + dy


MASK64 = (1 << 64) - 1
KSECRET = 0x6A09E667F3BCC908


def mix64(z):
    z = (z + 0x9E3779B97F4A7C15) & MASK64
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK64
    return (z ^ (z >> 31)) & MASK64


def sonar_key(payload, rnd, team):
    k = KSECRET ^ payload ^ ((rnd & 0x3FF) << 48) ^ (ord(team) << 58)
    return mix64(k) >> 48


def ping_ours(v, rnd, team):
    tag = v >> 48
    if tag in (0xC0A1 ^ 0x1111, 0xC0A1 ^ 0x2222):
        return True
    pl = v & ((1 << 48) - 1)
    return tag in (sonar_key(pl, rnd, team), sonar_key(pl, rnd - 1, team))


KAGE = [0, 1, 2, 3, 7, 15, 31, 40]


def decode_champ(v):
    """MsgChamp -> (champId, x, y, len, isQueen, age_ub)"""
    return (int((v >> 32) & 0xFFFF), int((v >> 20) & 0xFF), int((v >> 12) & 0xFF),
            int((v >> 4) & 0xFF), int((v >> 3) & 1), KAGE[int(v & 7)])


def funnel(path):
    r = parse(path)
    W, H, dr, edges = rm.parse_map(r['map'])
    team = {}
    heads = {}
    queen_of = {}
    for i, (t, body) in enumerate(dr):
        team[i] = 'AB'[t]
        heads[i] = tuple(body[0])
        queen_of['AB'[t]] = i
    rnd = 0
    # per side: nva deaths in window near/far queen head; queen head timeline
    qhead = {'A': {}, 'B': {}}   # round -> queen head (while alive)
    qdead = {'A': None, 'B': None}
    out = {'A': collections.Counter(), 'B': collections.Counter()}
    nva_rounds = {'A': [], 'B': []}
    last_deaths = {'A': [], 'B': []}   # (round,reason) tail for elim annotation
    alive = {'A': set(), 'B': set()}
    for i in heads:
        alive[team[i]].add(i)
    chfeeds = []   # (round, len, fh_cell, feedAge, hx, hy, dragon_id)
    locks = []     # (round, why, len, fh_cell, feedAge)
    champ_rpt = {'A': {}, 'B': {}}   # side -> round -> (cell, isQueen, len) freshest champ ping
    champ_isq = {'A': collections.Counter(), 'B': collections.Counter()}
    for e in r['events']:
        ty = e['type']
        if ty == 'roundStart':
            rnd = e['round']
            for s in 'AB':
                q = queen_of.get(s)
                if q is not None and q in heads and qdead[s] is None:
                    qhead[s][rnd] = heads[q]
        elif ty == 'dragonSplit':
            team[e['childId']] = e['team']
            heads[e['childId']] = tuple(e['childBody'][0]) if e['childBody'] else heads.get(e['childId'])
            heads[e['parentId']] = tuple(e['parentBody'][0]) if e['parentBody'] else heads.get(e['parentId'])
            alive[e['team']].add(e['childId'])
        elif ty == 'dragonUpdate':
            heads[e['id']] = tuple(e['head'])
        elif ty == 'dragonDeath':
            i = e['id']
            alive[team.get(i, '?')].discard(i) if team.get(i) in 'AB' else None
            if i in alive.get(team.get(i, ''), ()):
                alive[team[i]].discard(i)
            s = team.get(i)
            if s is None:
                continue
            alive[s].discard(i)
            if i == queen_of.get(s):
                qdead[s] = rnd
            if FEED_AT <= rnd <= FEED_STOP and e['reason'] == 'noValidAction':
                h = heads.get(i)
                q = queen_of.get(s)
                qh = heads.get(q) if (q is not None and qdead[s] is None) else None
                d = tdist(h, qh, W, H) if (h and qh) else 99
                # nearest OTHER own-dragon head (any teammate may eat the drop)
                d_own = min((tdist(h, hh, W, H) for j, hh in heads.items()
                             if team.get(j) == s and j != i and j in alive[s]), default=99)
                # freshest champ report <=5r old for this side
                d_ch = 99
                for rback in range(rnd, rnd - 6, -1):
                    if rback in champ_rpt[s]:
                        cx, cy, ciq, cl = champ_rpt[s][rback]
                        d_ch = tdist(h, (cx, cy), W, H)
                        if ciq:
                            out[s]['nva_champ_isq'] += 1
                        break
                out[s]['nva'] += 1
                nva_rounds[s].append(rnd)
                if d <= FEED_DIST:
                    out[s]['nva_near_q'] += 1
                elif d <= 4:
                    out[s]['nva_d34'] += 1
                if d_own <= FEED_DIST:
                    out[s]['nva_near_own'] += 1
                if d_ch <= FEED_DIST:
                    out[s]['nva_near_champ'] += 1
                elif d_ch <= 4:
                    out[s]['nva_champ_d34'] += 1
            if FEED_AT <= rnd <= FEED_STOP:
                out[s]['win_deaths'] += 1
                out[s]['win_' + e['reason']] += 1
            last_deaths[s].append((rnd, e['reason']))
        elif ty == 'sonarPing':
            v = e.get('value')
            snd = e['senderId']
            st = team.get(snd)
            if v is not None and st in 'AB' and ping_ours(v, rnd, st) and ((v >> 28) & 0xF) == 2:
                cid, cx, cy, cl, ciq, cage = decode_champ(v)
                champ_rpt[st][rnd] = (cx, cy, ciq, cl)
                champ_isq[st]['q' if ciq else 'n'] += 1
        elif ty == 'dragonLog':
            m = CHFEED.search(e['text'])
            if m:
                chfeeds.append({'r': int(m.group(1)), 'L': int(m.group(2)),
                                'fh': int(m.group(3)), 'fa': int(m.group(4)),
                                'xy': (int(m.group(5)), int(m.group(6))), 'id': e['id']})
                continue
            m2 = LOCKED.search(e['text'])
            if m2 and int(m2.group(4)) >= 0:
                locks.append({'r': int(m2.group(1)), 'why': m2.group(2),
                              'L': int(m2.group(3)), 'fh': int(m2.group(4)),
                              'fa': int(m2.group(5))})
    return {'qdead': qdead, 'out': out, 'nva_rounds': nva_rounds,
            'chfeeds': chfeeds, 'locks': locks, 'W': W, 'H': H,
            'champ_isq': champ_isq, 'champ_rpt': champ_rpt,
            'last_deaths': last_deaths, 'alive_end': {s: len(alive[s]) for s in 'AB'},
            'res': r['result']}


def classify(g):
    """-> (class, mechanism str)"""
    c, b = g['c'], g['b']
    if g['end'] == 'teamEliminated':
        # which side eliminated? candWin==0 means we died out (or both)
        return ('ELIM', f"r{g['rounds']} elim")
    lg, tg = b['longest'] - c['longest'], b['total'] - c['total']
    if lg > 0:
        return ('LONGEST', f"gap {lg} (c{c['longest']} vs b{b['longest']})")
    if tg > 0:
        return ('TOTAL', f"total gap {tg}")
    return ('DRAW', '')


def mech(c):
    """proximate mechanism text for a side dict"""
    s = []
    if c['qDeadRound'] is not None:
        s.append(f"Qdied r{c['qDeadRound']} {c['qDeadReason']}")
    else:
        s.append(f"Qend={c['queenEnd']}")
    s.append(f"q==longest:{c['queenEnd'] == c['longest']}")
    s.append(f"alive{c['alive']} nva{c.get('d_noValidAction', 0)}")
    return ' '.join(s)


def main():
    rdir = sys.argv[1]
    G = [json.loads(l) for l in open(os.path.join(rdir, 'games.jsonl'))]
    seen = {}
    for g in G:
        seen[(g['map'], g['seed'], g['candSide'])] = g
    G = list(seen.values())
    losses = [g for g in G if g['candWin'] == 0]
    wins = [g for g in G if g['candWin'] == 1]
    print(f'== v315 audit: {len(G)} games, cand {sum(g["candWin"] for g in G)/len(G):.1%} ==')
    classes = collections.Counter()
    print('\n-- cand losses under production rules (elim -> longest -> total) --')
    for g in sorted(losses, key=lambda x: (x['map'], x['candSide'])):
        cls, det = classify(g)
        classes[cls] += 1
        print(f"  {g['map']:<18} s{g['seed']} cand={g['candSide']} {cls:<8} {det:<38} | us: {mech(g['c'])}  them: {mech(g['b'])}")
    print('classes:', dict(classes))
    # queen end distributions
    cq = [g['c']['queenEnd'] for g in G]
    bq = [g['b']['queenEnd'] for g in G]
    import statistics
    print(f'\nqueenEnd@end: cand med {statistics.median(cq):.1f} mean {sum(cq)/len(cq):.2f} | base med {statistics.median(bq):.1f} mean {sum(bq)/len(bq):.2f}')
    print('  cand queenEnd hist:', sorted(collections.Counter(min(q, 20) // 5 * 5 for q in cq).items()))
    print('  base queenEnd hist:', sorted(collections.Counter(min(q, 20) // 5 * 5 for q in bq).items()))
    cqd = sum(1 for g in G if g['c']['qDeadRound'] is not None)
    bqd = sum(1 for g in G if g['b']['qDeadRound'] is not None)
    print(f'queen deaths/game: cand {cqd}/{len(G)}  base {bqd}/{len(G)}')
    cl = [g['c']['longest'] for g in G]; bl = [g['b']['longest'] for g in G]
    print(f'longest@end: cand {sum(cl)/len(cl):.1f}  base {sum(bl)/len(bl):.1f}')

    # Part 2: funnel from replays
    print('\n-- funnel (replays): nva deaths in feed window near own queen head --')
    per_side = collections.defaultdict(collections.Counter)
    timing = collections.defaultdict(list)
    near_by_map = collections.defaultdict(lambda: collections.Counter())
    champ_q_share = collections.defaultdict(lambda: collections.Counter())
    for f in sorted(glob.glob(os.path.join(rdir, 'replays', '*.replay'))):
        m = re.search(r'([a-z_]+)-s\d+-(abyss_\w+)-(abyss_\w+)\.replay', os.path.basename(f))
        if not m:
            continue
        mapn, botA, botB = m.group(1), m.group(2), m.group(3)
        try:
            a = funnel(f)
        except Exception as ex:
            print('ERR', f, ex); continue
        cseat = 'A' if 'v315' in botA else 'B'   # cand = v315
        for seat, who in [(cseat, 'cand'), ('B' if cseat == 'A' else 'A', 'base')]:
            o = a['out'][seat]
            for k, v in o.items():
                per_side[who][k] += v
            for k, v in a['champ_isq'][seat].items():
                champ_q_share[who][k] += v
            if o['nva']:
                timing[who] += a['nva_rounds'][seat]
                near_by_map[mapn][who + '_nva'] += o['nva']
                near_by_map[mapn][who + '_near'] += o['nva_near_champ']
                near_by_map[mapn][who + '_near_own'] += o['nva_near_own']
    print(f'  champ pings reporting queen (share of all): cand {champ_q_share["cand"]["q"]}/{champ_q_share["cand"]["q"]+champ_q_share["cand"]["n"]}  base {champ_q_share["base"]["q"]}/{champ_q_share["base"]["q"]+champ_q_share["base"]["n"]}')
    for who in ('cand', 'base'):
        o = per_side[who]
        print(f"  {who}: nva {o['nva']}  near-champ(<=2) {o['nva_near_champ']} ({100*o['nva_near_champ']/max(1,o['nva']):.0f}%) +d34 {o['nva_champ_d34']}  near-own(<=2) {o['nva_near_own']} ({100*o['nva_near_own']/max(1,o['nva']):.0f}%)  win deaths {o['win_deaths']} (h2h {o['win_hitHeadToHead']})")
        print(f"      (near queen-head only: {o['nva_near_q']}; champ pings reporting queen: {o['nva_champ_isq']}/{o['nva']})")
        if timing[who]:
            ts = sorted(timing[who])
            early = sum(1 for t in ts if t < FEED_AT + 20)
            print(f"    nva timing: n={len(ts)} front20r={early} ({100*early/len(ts):.0f}%)  med r{ts[len(ts)//2]}")
    print('\n  per-map nva near-rate (cand|base):')
    for mp, c in sorted(near_by_map.items()):
        cn, cbn = c['cand_nva'], c['base_nva']
        print(f"    {mp:<18} cand {c['cand_near']}/{cn} ({100*c['cand_near']/max(1,cn):.0f}%) own {c['cand_near_own']}/{cn}  base {c['base_near']}/{cbn} ({100*c['base_near']/max(1,cbn):.0f}%) own {c['base_near_own']}/{cbn}")

    # dbg replays: exact funnel emit check (chfeed lines carry fh target + feeder xy)
    print('\n-- dbg replays: chfeed emit check (exact distance to locked feedHead) --')
    cf_stats = collections.Counter()
    mid_stats = collections.Counter()
    lock_stats = collections.Counter()
    lock_whys = collections.Counter()
    feeder_lens = []
    fa_hist = collections.Counter()
    lock_err = []
    lock_err_q = []
    lock_err_nq = []
    seen_pairs = set()
    dbg_by_map = collections.defaultdict(lambda: collections.Counter())
    for f in sorted(glob.glob(os.path.join(rdir, 'replays', '*.replay'))):
        try:
            a = funnel(f)
        except Exception:
            continue
        mm = re.search(r'([a-z_]+)-s\d+-abyss', os.path.basename(f))
        mapn = mm.group(1) if mm else '?'
        W, H = a['W'], a['H']
        # which seat runs the dbg build (its dragonLog lines carry the telemetry)
        base = os.path.basename(f)
        dbg_side = 'A' if '-abyss_v315dbg-abyss_' in base or base.split('-')[2] == 'abyss_v315dbg' else 'B'
        for cf in a['chfeeds']:
            key = (f, cf['id'], cf['r'])
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            cell, xy = cf['fh'], cf['xy']
            d = tdist(xy, (cell % W, cell // W), W, H) if cell >= 0 else 99
            era = 'win' if cf['r'] >= 340 else 'mid'
            tgt = cf_stats if era == 'win' else mid_stats
            tgt['n'] += 1
            # emit legality: BFS-to-neighbor(fh) <= fd=2  <=>  manhattan(head,fh) <= 3
            if d <= 3:
                tgt['within_fd'] += 1
            tgt['manh' + str(min(d, 9))] += 1
            if cf['L'] <= (7 if era == 'win' else 5):
                tgt['len_ok'] += 1
            fa_hist[min(cf['fa'], 40)] += 1
            # lock error: distance locked target -> freshest own champ ping (<=5r)
            e = 99; eisq = None
            for rback in range(cf['r'], cf['r'] - 6, -1):
                if rback in a['champ_rpt'][dbg_side]:
                    hit = a['champ_rpt'][dbg_side][rback]
                    e = tdist((cell % W, cell // W), (hit[0], hit[1]), W, H) if cell >= 0 else 99
                    eisq = hit[2]
                    break
            if era == 'win':
                lock_err.append(e)
                (lock_err_q if eisq else lock_err_nq).append(e)
                dbg_by_map[mapn]['chfeed'] += 1
                if d <= 3:
                    dbg_by_map[mapn]['within'] += 1
            if era == 'win':
                feeder_lens.append(cf['L'])
        dbg_by_map[mapn]['nva_dbg'] += a['out'][dbg_side]['nva']
        dbg_by_map[mapn]['games'] += 1
        for lk in a['locks']:
            lock_stats['n'] += 1
            if lk['fa'] == 0:
                lock_stats['live'] += 1
            elif lk['fa'] <= 30:
                lock_stats['heard_fresh'] += 1
            else:
                lock_stats['stale'] += 1
            lock_whys[lk['why']] += 1
    for nm, tgt in (('window(r>=340)', cf_stats), ('midFeed(r<340)', mid_stats)):
        if tgt['n']:
            print(f"  {nm} chfeed emits: {tgt['n']}  manh<=3 of lock (emit-legal): {tgt['within_fd']} ({100*tgt['within_fd']/tgt['n']:.0f}%)  len_ok: {tgt['len_ok']}")
            print(f"      manh dist hist: {sorted((k,v) for k,v in tgt.items() if k.startswith('manh'))}")
    if cf_stats['n']:
        import statistics as st
        print(f"  window feeder lens: med {st.median(feeder_lens)}  hist {sorted(collections.Counter(feeder_lens).items())}")
        print(f"  feedAge hist on chfeed emits: {sorted(fa_hist.items())}")
        if lock_err:
            for nm, le0 in (('all', lock_err), ('vs queen-ping', lock_err_q), ('vs champ-ping', lock_err_nq)):
                if not le0:
                    continue
                le = sorted(le0)
                print(f"  lock error {nm} (fh -> freshest champ ping <=5r): n={len(le)} med {le[len(le)//2]}  <=2: {sum(1 for x in le if x<=2)} ({100*sum(1 for x in le if x<=2)/len(le):.0f}%)  >6: {sum(1 for x in le if x>6)} ({100*sum(1 for x in le if x>6)/len(le):.0f}%)  nopng: {sum(1 for x in le if x==99)}")
    if lock_stats['n']:
        print(f"  feed-locked dragon-rounds: {lock_stats['n']}  live(fa=0) {lock_stats['live']}  heard<=30 {lock_stats['heard_fresh']}  stale>30 {lock_stats['stale']}")
        print(f"  whys while locked: {dict(lock_whys.most_common(10))}")
    print('\n  per-map (dbg side): chfeed window emits vs window nva deaths')
    for mp, c in sorted(dbg_by_map.items()):
        print(f"    {mp:<16} games {c['games']:>2}  chfeed {c['chfeed']:>3} (manh<=3 {c['within']})  win-nva {c['nva_dbg']:>3}  chfeed/nva {100*c['chfeed']/max(1,c['nva_dbg']):.0f}%")


if __name__ == '__main__':
    main()
