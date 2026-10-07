"""v321 residual decomposition — LONGEST-class concentration + ELIM-class starvation.

Q1 (LONGEST): where does post-mutual-death length concentrate? Per side per round,
  rolling-longest dragon = argmax L over that side's dbg lines (both sides run
  BC_DEBUG: every alive dragon logs `r.. <why> .. L=.. id=.. .. oq=.. hx=.. hy=..`
  each turn). Funnel-to-bell: nva death distance to own side's rolling-longest head,
  bucketed per era (340-379/380-419/420-459/460-499). End-state top-3 lengths.
  Champ stability = distinct dragonIds holding rolling-longest after mutual death.

Q2 (ELIM): queen alive at elim round? Her L trajectory r100->elim (her own L=
  lines, dragon id == side's queen id). Donations = nva deaths within manh<=3 of
  her head while alive. Buds = dragonSplit with parentId==queen. Rounds at L<4.

Usage: python3 analysis/v321_residual.py <results_dir>
"""
import collections, glob, json, os, re, sys, statistics

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../tooling'))
from parse_replay import parse  # noqa: E402
import replay_metrics as rm      # noqa: E402

LOG = re.compile(
    r'r(\d+) (\S+) depth=(-?\d+) ms=(-?\d+) L=(-?\d+) body=(-?\d+) id=(-?\d+) U=(-?\d+) '
    r'g=(-?\d+) fh=(-?\d+) fa=(-?\d+) sc=(-?\d+) qr=(-?\d+) ql=(-?\d+) ch=(-?\d+) '
    r'hd=(-?\d+) oq=(-?\d+) hx=(-?\d+) hy=(-?\d+)')

FEED_AT, FEED_STOP = 340, 499
ERAS = [(340, 379), (380, 419), (420, 459), (460, 499)]
ELIM_ERAS = [(0, 99), (100, 199), (200, 299), (300, 499)]


def tdist(a, b, W, H):
    dx = abs(a[0] - b[0]); dx = min(dx, W - dx)
    dy = abs(a[1] - b[1]); dy = min(dy, H - dy)
    return dx + dy


def parse_game(path):
    """-> per-side structures. team[id] = 'A'|'B'."""
    r = parse(path)
    W, H, dr, edges = rm.parse_map(r['map'])
    team = {}
    queen_of = {}
    for i, (t, body) in enumerate(dr):
        team[i] = 'AB'[t]
        queen_of['AB'[t]] = i          # initial dragons = queens
    for e in r['events']:
        if e['type'] == 'dragonSplit':
            team[e['childId']] = e['team']
    # second pass: logs
    # logs[side][round][id] = dict(L,x,y,why,U,sc,fa,fh,g)
    logs = {'A': collections.defaultdict(dict), 'B': collections.defaultdict(dict)}
    deaths = []          # (round, side, id, reason, head_xy)
    splits = []          # (round, side, parentId, childId)
    heads = {i: tuple(b[0]) for i, (t, b) in enumerate(dr)}
    alive = {'A': set(), 'B': set()}
    for i in heads:
        alive[team[i]].add(i)
    rnd = 0
    qdead = {'A': None, 'B': None}
    last_round = 0
    for e in r['events']:
        ty = e['type']
        if ty == 'roundStart':
            rnd = e['round']
            last_round = rnd
        elif ty == 'dragonUpdate':
            heads[e['id']] = tuple(e['head'])
        elif ty == 'dragonSplit':
            team[e['childId']] = e['team']
            heads[e['childId']] = tuple(e['childBody'][0]) if e['childBody'] else heads.get(e['childId'])
            heads[e['parentId']] = tuple(e['parentBody'][0]) if e['parentBody'] else heads.get(e['parentId'])
            alive[e['team']].add(e['childId'])
            splits.append((rnd, e['team'], e['parentId'], e['childId']))
        elif ty == 'dragonDeath':
            i = e['id']
            s = team.get(i)
            if s:
                alive[s].discard(i)
                if i == queen_of.get(s):
                    qdead[s] = rnd
                deaths.append((rnd, s, i, e['reason'], heads.get(i)))
        elif ty == 'dragonLog':
            m = LOG.search(e['text'])
            if not m:
                continue
            g = m.groups()
            i = int(g[6]); s = team.get(i)
            if s is None:
                continue
            rr = int(g[0])
            logs[s][rr][i] = {'L': int(g[4]), 'why': g[1], 'U': int(g[7]),
                              'x': int(g[17]), 'y': int(g[18]), 'fa': int(g[10]),
                              'fh': int(g[9]), 'sc': int(g[11]), 'g': int(g[8]),
                              'ch': int(g[14]), 'oq': int(g[16]), 'ql': int(g[13])}
    return {'W': W, 'H': H, 'team': team, 'queen_of': queen_of, 'logs': logs,
            'deaths': deaths, 'splits': splits, 'qdead': qdead,
            'res': r['result'], 'rounds': last_round}


def rolling_longest(logs_side, rnd, W, H):
    """(id,L,x,y) of side's max-L dragon logging at rnd; falls back <=3r."""
    for rb in range(rnd, rnd - 4, -1):
        d = logs_side.get(rb)
        if d:
            i = max(d, key=lambda j: (d[j]['L'], j))
            v = d[i]
            return i, v['L'], (v['x'], v['y'])
    return None, 0, None


def end_lengths(logs_side, rounds, dead_ids=None):
    """last logged L per dragon still alive at end -> sorted desc list.
    A dragon counts as alive at end if it logged within the last 15 rounds
    AND is not in dead_ids (paranoia double-check)."""
    last = {}
    for rnd, dd in logs_side.items():
        for i, v in dd.items():
            last[i] = (rnd, v['L'])
    cutoff = (rounds or 0) - 15
    return sorted((v[1] for i, v in last.items()
                   if v[0] >= cutoff and (dead_ids is None or i not in dead_ids)),
                  reverse=True)


def classify(g):
    c, b = g['c'], g['b']
    if g['end'] == 'teamEliminated':
        return 'ELIM'
    if c['queenEnd'] != b['queenEnd']:
        return 'QUEENEND'
    if c['longest'] != b['longest']:
        return 'LONGEST'
    if c['total'] != b['total']:
        return 'TOTAL'
    return 'DRAW'


def q1_longest(path, seat_loss):
    """For one replay: per-side funnel metrics in LONGEST games.
    seat_loss: which seat letter lost ('A' or 'B'). Returns aggregates."""
    a = parse_game(path)
    W, H = a['W'], a['H']
    feedAt = 320 if W * H <= 2000 else FEED_AT   # corridor override in v321 adjustByMap
    eras = [(feedAt + 40*k, feedAt + 40*k + 39) for k in range(4)]
    win_seat = 'B' if seat_loss == 'A' else 'A'
    mdeath = max(x for x in a['qdead'].values() if x is not None) if all(v is not None for v in a['qdead'].values()) else None
    res = {'loss': seat_loss, 'win': win_seat, 'mdeath': mdeath, 'W': W, 'H': H}
    for seat in 'AB':
        who = 'loss' if seat == seat_loss else 'win'
        # rolling-longest post-mutual-death (or feedAt+ if no mutual death)
        start = (mdeath + 1) if mdeath else feedAt
        ids = set(); traj = []
        for rr in range(start, min(FEED_STOP, 500) + 1):
            i, L, xy = rolling_longest(a['logs'][seat], rr, W, H)
            if i is not None:
                ids.add(i)
                traj.append((rr, L))
        res[who + '_champs_after_death'] = len(ids)
        res[who + '_traj'] = traj
        # funnel: nva deaths, dist to rolling longest
        era_nva = {e: [0, 0] for e, _ in enumerate(ERAS)}   # [count, within3]
        era_chfeed = {e: 0 for e, _ in enumerate(ERAS)}
        era_dists = {e: [] for e, _ in enumerate(ERAS)}
        for (rr, s, i, reason, xy) in a['deaths']:
            if s != seat or reason != 'noValidAction' or xy is None or not (feedAt <= rr <= FEED_STOP):
                continue
            _, L, lxy = rolling_longest(a['logs'][seat], rr, W, H)
            d = tdist(xy, lxy, W, H) if lxy else 99
            ei = min((rr - feedAt) // 40, 3)
            era_nva[ei][0] += 1
            era_dists[ei].append(d)
            if d <= 3:
                era_nva[ei][1] += 1
        res[who + '_era_dists'] = era_dists
        # feed emits per era (funnel still running?): chfeed + box-feed whys;
        # donor pool per era = distinct ids logging (alive) in that era
        era_pool = {e: set() for e, _ in enumerate(ERAS)}
        for rr, dd in a['logs'][seat].items():
            if not (feedAt <= rr <= FEED_STOP):
                continue
            for i, v in dd.items():
                era_pool[min((rr - feedAt) // 40, 3)].add(i)
                if v['why'].startswith('chfeed') or v['why'].startswith('box-feed'):
                    ei = min((rr - feedAt) // 40, 3)
                    era_chfeed[ei] += 1
        res[who + '_era_pool'] = {e: len(s) for e, s in era_pool.items()}
        dead = {i for (rr, s, i, reason, xy) in a['deaths'] if s == seat}
        res[who + '_era_nva'] = era_nva
        res[who + '_era_chfeed'] = era_chfeed
        res[who + '_end3'] = end_lengths(a['logs'][seat], a['rounds'], dead)[:3]
        el = end_lengths(a['logs'][seat], a['rounds'], dead)
        res[who + '_endtot'] = sum(el)
        res[who + '_top1share'] = (el[0] / sum(el)) if el and sum(el) else 0
    return res


def funnel_geom(path, seat):
    """Discriminating funnel metrics for one side:
    - lock: eligible worker-rounds (alive, L<=8) with fh>=0 per era
    - chdist: manh(head -> own resolved champHead_) for worker-rounds with ch>=0
    - churn: concurrent selfChamps and distinct resolved targets per round
    - emits: chfeed/box-feed whys per era
    Returns dict of era-keyed stats."""
    a = parse_game(path); W, H = a['W'], a['H']
    feedAt = 320 if W * H <= 2000 else 340
    eras = [(feedAt, feedAt + 39), (feedAt + 40, feedAt + 79),
            (feedAt + 80, feedAt + 119), (max(feedAt + 120, 460), 499)]
    out = {'lock': [], 'chdist': [], 'within12': [], 'selfChamps': [], 'targets': [],
           'emits': [], 'alive': [], 'pool': []}
    for lo, hi in eras:
        lock = tot = 0
        ds = []
        scs = []
        tg = []
        emits = 0
        pool = set()
        alive_n = []
        for rr in range(lo, hi + 1):
            dd = a['logs'][seat].get(rr)
            if not dd:
                continue
            alive_n.append(len(dd))
            nsc = sum(1 for v in dd.values() if v['sc'])
            if nsc:
                scs.append(nsc)
            tset = {v['ch'] for v in dd.values() if v['ch'] >= 0}
            if tset:
                tg.append(len(tset))
            for i, v in dd.items():
                if v['L'] > 8:
                    continue
                if v['why'] in ('chfeed', 'box-feed'):
                    emits += 1
                if rr >= feedAt:
                    pool.add(i)
                    tot += 1
                    if v['fh'] >= 0:
                        lock += 1
                    if v['ch'] >= 0 and not v['sc']:
                        ds.append(tdist((v['x'], v['y']), (v['ch'] % W, v['ch'] // W), W, H))
        ds.sort()
        out['lock'].append((lock, tot))
        out['chdist'].append(ds[len(ds) // 2] if ds else None)
        out['within12'].append(round(100 * sum(1 for d in ds if d <= 12) / max(1, len(ds))))
        out['selfChamps'].append(round(statistics.median(scs)) if scs else None)
        out['targets'].append(round(statistics.median(tg)) if tg else None)
        out['emits'].append(emits)
        out['alive'].append(round(statistics.median(alive_n)) if alive_n else None)
        out['pool'].append(len(pool))
    return out


def q2_elim(path, seat_loss, elim_round):
    a = parse_game(path)
    W, H = a['W'], a['H']
    q = a['queen_of'][seat_loss]
    res = {'seat': seat_loss, 'qid': q}
    # queen trajectory: her own logged lines
    traj = {}      # round -> L
    qpos = {}
    for rr, dd in a['logs'][seat_loss].items():
        if q in dd:
            traj[rr] = dd[q]['L']
            qpos[rr] = (dd[q]['x'], dd[q]['y'])
    res['q_traj'] = traj
    res['qpos'] = qpos
    res['q_alive_at_elim'] = (a['qdead'][seat_loss] is None or a['qdead'][seat_loss] >= elim_round)
    res['q_dead_round'] = a['qdead'][seat_loss]
    # rounds spent ALIVE at L<4 between r100 and min(elim, her death)
    qend = min(elim_round, res['q_dead_round'] or elim_round)
    lt4 = 0; obs = 0; lastL = None
    for rr in range(100, qend + 1):
        if rr in traj:
            lastL = traj[rr]
        if lastL is not None:
            obs += 1
            lt4 += lastL < 4
    res['rounds_lt4'] = lt4
    res['observed_rounds'] = obs
    res['q_max_L'] = max(traj.values()) if traj else 0
    res['q_last_L'] = traj[max(traj)] if traj else 0
    # her buds
    res['q_buds'] = sum(1 for (rr, s, p, c) in a['splits'] if s == seat_loss and p == q)
    res['buds_by_era'] = [sum(1 for (rr, s, p, c) in a['splits']
                             if s == seat_loss and p == q and lo <= rr <= hi)
                          for lo, hi in ELIM_ERAS]
    # team splits total (units spawning at all)
    res['team_splits'] = [sum(1 for (rr, s, p, c) in a['splits']
                            if s == seat_loss and lo <= rr <= hi)
                          for lo, hi in ELIM_ERAS]
    # donations: own-side deaths within manh<=3 of her head while she was alive —
    # split by reason (nva = designed drop, other = combat scraps near her)
    don = 0; don_all = 0; oth = 0; oth_all = 0
    for (rr, s, i, reason, xy) in a['deaths']:
        if s != seat_loss or xy is None:
            continue
        qh = None
        for rb in range(rr, rr - 6, -1):
            if rb in qpos:
                qh = qpos[rb]; break
        if qh is None:
            continue
        if reason == 'noValidAction':
            don_all += 1
            don += tdist(xy, qh, W, H) <= 3
        else:
            oth_all += 1
            oth += tdist(xy, qh, W, H) <= 3
    res['donations_near'] = don
    res['nva_while_qalive'] = don_all
    res['other_near'] = oth
    res['other_deaths'] = oth_all
    res['q_dead_reason'] = next((e[3] for e in a['deaths'] if e[2] == q and e[1] == seat_loss), None)
    # how hidden: her median open-nb? use movement — distinct cells visited r100+
    res['q_cells'] = len(set(qpos.values()))
    # alive trajectories: count dragons logging per round per side (alive = logged)
    def alive_at(seat, rr):
        for rb in range(rr, rr - 6, -1):
            if rb in a['logs'][seat]:
                return len(a['logs'][seat][rb])
        return None
    res['alive_traj'] = {s: [alive_at(s, r0) for r0 in (100, 200, 300, 400)]
                       for s in 'AB'}
    res['alive_at_qdead'] = {s: alive_at(s, res['q_dead_round'] or elim_round)
                             for s in 'AB'}
    # first round loser side's alive fell below winner's (the bleed-out point)
    res['cross_round'] = None
    for rr in range(1, elim_round + 1):
        la = alive_at(seat_loss, rr); wa = alive_at('B' if seat_loss == 'A' else 'A', rr)
        if la is not None and wa is not None and la < wa:
            res['cross_round'] = rr
            break
    return res


def seat_of_loss(g):
    """which seat letter holds the losing side."""
    return g['candSide'] if g['candWin'] == 0 else ('B' if g['candSide'] == 'A' else 'A')


def main():
    rdir = sys.argv[1]
    G = [json.loads(l) for l in open(os.path.join(rdir, 'games.jsonl'))]
    seen = {}
    for g in G:
        seen[(g['map'], g['seed'], g['candSide'])] = g
    G = list(seen.values())
    candw = sum(g['candWin'] for g in G)
    print(f'== v321 residual: {len(G)} games, cand {candw/len(G):.1%} ==')
    cls = collections.Counter(classify(g) for g in G if g['candWin'] == 0)
    print('cand loss classes:', dict(cls))

    # map replay filename -> (map, seed, candSeat): TWO files per map+seed
    # (one per seat pairing); filename order gives seat of each bot.
    repl = {}
    for f in glob.glob(os.path.join(rdir, 'replays', '*.replay')):
        m = re.search(r'([a-z_]+)-s(\d+)-(abyss_\w+)-(abyss_\w+)\.replay',
                      os.path.basename(f))
        if m:
            cand_seat = 'A' if 'v321' in m.group(3) else 'B'
            repl[(m.group(1), int(m.group(2)), cand_seat)] = f

    losses = [g for g in G if g['candWin'] == 0]
    long_losses = [g for g in losses if classify(g) == 'LONGEST']
    elim_losses = [g for g in losses if classify(g) == 'ELIM']
    qe_losses = [g for g in losses if classify(g) == 'QUEENEND']
    print(f'\nLONGEST {len(long_losses)}  ELIM {len(elim_losses)}  QUEENEND {len(qe_losses)}')

    # ---------------- QUEENEND (context table) ----------------
    print('\n-- QUEENEND-class losses (key-1: their queenEnd > ours) --')
    for g in sorted(qe_losses, key=lambda x: x['map']):
        loser_d = g['c']; win_d = g['b']
        print(f"  {g['map']:<16} s{g['seed']} cand={g['candSide']} r{g['rounds']} | ourQ {loser_d['qDeadReason']} r{loser_d['qDeadRound']} qE={loser_d['queenEnd']} | theirQ qE={win_d['queenEnd']} dead={win_d['qDeadRound']} | longest {loser_d['longest']}v{win_d['longest']} alive {loser_d['alive']}v{win_d['alive']}")

    # ---------------- Q1 ----------------
    print('\n===== Q1: LONGEST-class funnel/concentration =====')
    agg = collections.defaultdict(lambda: collections.Counter())
    era_nva = {'win': collections.Counter(), 'loss': collections.Counter()}
    era_nva_near = {'win': collections.Counter(), 'loss': collections.Counter()}
    era_cf = {'win': collections.Counter(), 'loss': collections.Counter()}
    era_d = {'win': collections.defaultdict(list), 'loss': collections.defaultdict(list)}
    era_pool = {'win': collections.defaultdict(list), 'loss': collections.defaultdict(list)}
    champswitch = {'win': [], 'loss': []}
    top1share = {'win': [], 'loss': []}
    conc_rows = []
    permap = collections.defaultdict(lambda: collections.Counter())
    done = 0
    for g in long_losses:
        f = repl.get((g['map'], g['seed'], g['candSide']))
        if not f:
            continue
        seat = seat_of_loss(g)
        try:
            res = q1_longest(f, seat)
        except Exception as ex:
            print('ERR', os.path.basename(f), ex); continue
        done += 1
        for who in ('win', 'loss'):
            en = res[who + '_era_nva']
            for ei in range(4):
                era_nva[who][ei] += en[ei][0]
                era_nva_near[who][ei] += en[ei][1]
                era_cf[who][ei] += res[who + '_era_chfeed'][ei]
                era_d[who][ei] += res[who + '_era_dists'][ei]
                era_pool[who][ei].append(res[who + '_era_pool'][ei])
            champswitch[who].append(res[who + '_champs_after_death'])
            top1share[who].append(res[who + '_top1share'])
        conc_rows.append((g['map'], g['seed'], seat,
                          res['loss_end3'], res['win_end3'],
                          res['loss_endtot'], res['win_endtot'],
                          res['mdeath'],
                          res['loss_champs_after_death'], res['win_champs_after_death']))
        permap[g['map']]['n'] += 1
        permap[g['map']]['loss_top1'] += res['loss_end3'][0] if res['loss_end3'] else 0
        permap[g['map']]['win_top1'] += res['win_end3'][0] if res['win_end3'] else 0
    print(f'analyzed {done}/{len(long_losses)} LONGEST replays')
    if done:
        print('\n  era table (both sides, all LONGEST losses; era0 = feedAt..+39, feedAt=320 corridor/340 open):')
        print(f'  {"era":<10} | {"nva win/loss":<14} | {"near<=3 win/loss":<16} | {"chfeed win/loss":<14} | {"pool win/loss":<13} | medD')
        for ei, (lo, hi) in enumerate(ERAS):
            wn, ln = era_nva['win'][ei], era_nva['loss'][ei]
            wnn, lnn = era_nva_near['win'][ei], era_nva_near['loss'][ei]
            wc, lc = era_cf['win'][ei], era_cf['loss'][ei]
            wd = statistics.median(era_d['win'][ei]) if era_d['win'][ei] else -1
            ld = statistics.median(era_d['loss'][ei]) if era_d['loss'][ei] else -1
            wp = statistics.median(era_pool['win'][ei]) if era_pool['win'][ei] else -1
            lp = statistics.median(era_pool['loss'][ei]) if era_pool['loss'][ei] else -1
            print(f'  r{lo}-{hi:<5} | {wn:>4}/{ln:<4}       | {wnn:>4} ({100*wnn/max(1,wn):.0f}%)/{lnn:>4} ({100*lnn/max(1,ln):.0f}%) | {wc:>4}/{lc:<4} | {wp:>4.0f}/{lp:<4.0f} | medD {wd:.0f}/{ld:.0f}')
        for who in ('win', 'loss'):
            cs = champswitch[who]; t1 = top1share[who]
            print(f'  {who}: post-death longest-holder count med {statistics.median(cs):.0f} (mean {sum(cs)/len(cs):.1f}) | end top1 share med {statistics.median(t1):.2f} mean {sum(t1)/len(t1):.2f}')
        print('\n  per-loss concentration rows:')
        for mp, sd, seat, l3, w3, lt, wt, md, lc, wc in conc_rows:
            print(f'    {mp:<16} s{sd} loss={seat} mdeath={md} | end top3 loss {l3} (tot {lt}) vs win {w3} (tot {wt}) | longest-holders {lc}v{wc}')

    # ---- funnel geometry per LONGEST loss: lock rate / target distance / churn ----
    print('\n  funnel geometry per loss (era0+era1 = feedAt..+79; lock% = fh+ of eligible;')
    print('  chdist = med manh worker->own resolved champ; w12 = % of those <=12;')
    print('  sc = med concurrent selfChamps; tgts = med distinct resolved targets; emits):')
    geom_agg = {'win': collections.defaultdict(list), 'loss': collections.defaultdict(list)}
    for g in long_losses:
        f = repl.get((g['map'], g['seed'], g['candSide']))
        if not f:
            continue
        seat = seat_of_loss(g)
        try:
            gl = funnel_geom(f, seat)
            gw = funnel_geom(f, 'B' if seat == 'A' else 'A')
        except Exception as ex:
            print('GEOM ERR', os.path.basename(f), ex); continue
        def summar(gd):
            lock = sum(l for l, t in gd['lock'][:2]); tot = sum(t for l, t in gd['lock'][:2])
            dd = [d for d in gd['chdist'][:2] if d is not None]
            return dict(lockpct=100 * lock / max(1, tot),
                        chdist=statistics.median(dd) if dd else None,
                        w12=round(statistics.mean(gd['within12'][:2])),
                        sc=statistics.median([x for x in gd['selfChamps'][:2] if x]) if any(gd['selfChamps'][:2]) else None,
                        tgts=statistics.median([x for x in gd['targets'][:2] if x]) if any(gd['targets'][:2]) else None,
                        emits=sum(gd['emits'][:2]), alive0=gd['alive'][0], alive3=gd['alive'][3])
        sl, sw = summar(gl), summar(gw)
        for k in sl:
            geom_agg['loss'][k].append(sl[k] if sl[k] is not None else float('nan'))
            geom_agg['win'][k].append(sw[k] if sw[k] is not None else float('nan'))
        print(f'    {g["map"]:<16} s{g["seed"]} loss={seat} | lock% {sl["lockpct"]:.1f}v{sw["lockpct"]:.1f} | chdist {sl["chdist"]}v{sw["chdist"]} | w12 {sl["w12"]}v{sw["w12"]} | sc {sl["sc"]}v{sw["sc"]} | tgts {sl["tgts"]}v{sw["tgts"]} | emits {sl["emits"]}v{sw["emits"]} | alive {sl["alive0"]}->{sl["alive3"]}v{sw["alive0"]}->{sw["alive3"]}')
    if geom_agg['loss']:
        print('  medians:')
        for k in ('lockpct', 'chdist', 'w12', 'sc', 'tgts', 'emits'):
            lv = [x for x in geom_agg['loss'][k] if x == x]
            wv = [x for x in geom_agg['win'][k] if x == x]
            if lv and wv:
                print(f'    {k:<8} loss {statistics.median(lv):.1f} vs win {statistics.median(wv):.1f}')

    # ---------------- Q2 ----------------
    print('\n===== Q2: ELIM-class queen starvation =====')
    rows = []
    for g in elim_losses:
        f = repl.get((g['map'], g['seed'], g['candSide']))
        if not f:
            continue
        seat = seat_of_loss(g)
        try:
            res = q2_elim(f, seat, g['rounds'])
        except Exception as ex:
            print('ERR', os.path.basename(f), ex); continue
        # L at key checkpoints
        t = res['q_traj']
        def lat(rr):
            ks = [k for k in t if k <= rr]
            return t[max(ks)] if ks else None
        # winner-side queen status (from games.jsonl)
        loser_d = g['c'] if g['candSide'] == seat else g['b']
        win_d = g['b'] if g['candSide'] == seat else g['c']
        res['their_qdead'] = win_d['qDeadRound']
        res['their_qreason'] = win_d['qDeadReason']
        res['their_alive'] = win_d['alive']
        res['our_alive'] = loser_d['alive']
        rows.append((g['map'], g['seed'], seat, g['rounds'], res,
                     lat(100), lat(200), lat(300)))
    print(f'analyzed {len(rows)}/{len(elim_losses)} ELIM replays')
    print(f'  {"map":<16} {"seed":<4} {"seat":<4} {"elimR":<5} | {"qAlive":<6} {"qDeadR":<6} {"qReason":<14} {"L100":<4} {"L200":<4} {"L300":<4} {"maxL":<4} | buds | donations | hide')
    alive_ct = starved = 0
    for mp, sd, seat, er, res, l1, l2, l3 in sorted(rows):
        alive = res['q_alive_at_elim']
        alive_ct += alive
        buds = sum(res['buds_by_era'][1:])
        if res['q_max_L'] < 4:
            starved += 1
        tq = f'r{res["their_qdead"]}{res["their_qreason"][:4]}' if res['their_qdead'] is not None else 'alive'
        at = res['alive_traj'][seat]; wt = res['alive_traj']['B' if seat == 'A' else 'A']
        print(f'  {mp:<16} s{sd:<3} {seat:<4} r{er:<4} | {"Y" if alive else "N":<6} r{str(res["q_dead_round"]):<5} {str(res["q_dead_reason"]):<14} {str(l1):<4} {str(l2):<4} {str(l3):<4} {res["q_max_L"]:<4} | {res["q_buds"]:>3} buds {res["buds_by_era"]} splits {res["team_splits"]} | nva {res["donations_near"]}/{res["nva_while_qalive"]} oth {res["other_near"]}/{res["other_deaths"]} | lt4 {res["rounds_lt4"]}/{res["observed_rounds"]} cells {res["q_cells"]} | them:{tq} alive@{res["q_dead_round"] or er}:{res["alive_at_qdead"][seat]}v{res["alive_at_qdead"]["B" if seat=="A" else "A"]} cross:r{res["cross_round"]} traj{at}v{wt}')
    if rows:
        print(f'\n  queen alive at elim: {alive_ct}/{len(rows)}   never reached L>=4: {starved}/{len(rows)}')
        # distribution of elim rounds + queen L at end
        elims = sorted(g['rounds'] for g in elim_losses)
        print(f'  elim rounds: med r{elims[len(elims)//2]}  range r{elims[0]}-r{elims[-1]}')
        qdeads = [g['c']['qDeadRound'] if g['candSide'] == seat_of_loss(g) else g['b']['qDeadRound'] for g in elim_losses]
        # simpler: use rows res
        dq = sorted(r[4]['q_dead_round'] for r in rows if r[4]['q_dead_round'] is not None)
        if dq:
            print(f'  queen death rounds (dead queens): med r{dq[len(dq)//2]}')


if __name__ == '__main__':
    main()
