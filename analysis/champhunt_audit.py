"""v310 champ-hunter mechanism audit.

Per replay (from a kmatch run of abyss_v310dbg --keep-replays):
  (a) eligibility: per dragon-round, did a len>=8 non-queen enemy candidate
      exist (chelig logs)? within champHuntMaxDist=20 (dist<=20)? rank<3?
  (b) assignment: chassign log count; convergence = hunter head->target-cell
      distance before vs +10 rounds after; hunter-per-target clustering.
  (c) outcomes: do hunted enemies (chassign id or cell match) die more often
      than unhunted enemies reported len>=8 via our MsgEnemy sonar pings?

Only the v310dbg side emits chelig/chassign lines. The 'r<round> <why>' lines
show which Choice won each turn (champ-hunt / champ-ram whys).

Usage: python3 analysis/champhunt_audit.py <replay_glob...>
"""
import collections, glob, math, os, re, statistics, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../tooling'))
from parse_replay import parse  # noqa: E402
import replay_metrics as rm      # noqa: E402

CHEBIG = re.compile(r'chelig cell=(-?\d+) len=(\d+) seen=(\d) dist=(-?\d+) rank=(-?\d+)')
CHASSIGN = re.compile(r'chassign (id=(-?\d+) |heard )?cell=(-?\d+)(?: len=(\d+))?(?: gain=(-?[\d.]+) mult=(-?[\d.]+))?')
WHY = re.compile(r'r(\d+) (\S+)')

MAX_DIST, HUNT_LEN, HUNTER_COUNT = 20, 8, 3


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
    """value is ours: top-16 tag matches this/last round's key (sonarKeyed)
    or the fixed team tag (older bots with sonarKeyed=0)."""
    tag = v >> 48
    if tag in (0xC0A1 ^ 0x1111, 0xC0A1 ^ 0x2222):
        return True
    pl = v & ((1 << 48) - 1)
    return tag in (sonar_key(pl, rnd, team), sonar_key(pl, rnd - 1, team))


def decode_enemy(v):
    """MsgEnemy sonar value -> (id, x, y, len, isQueen). Caller filters tag."""
    return (int((v >> 32) & 0xFFFF), int((v >> 20) & 0xFF), int((v >> 12) & 0xFF),
            int((v >> 4) & 0xFF), int(v & 0xF))


def msg_type(v):
    return int((v >> 28) & 0xF)


def analyze(path):
    r = parse(path)
    W, H, dr, edges = rm.parse_map(r['map'])
    team = {}
    heads = {}
    for i, (t, body) in enumerate(dr):
        team[i] = 'AB'[t]
        heads[i] = tuple(body[0])
    rnd = 0

    elig = collections.defaultdict(list)     # team -> per-round [n_eligible_dragons]
    elig_near = collections.defaultdict(list)  # team -> per-round [n with dist<=20 & rank<3]
    elig_dist_any = collections.defaultdict(list)  # per-round [n with dist<=20]
    assigns = []                             # (round, hunter_id, team, tgt_id, cell, len, gain, mult)
    why_counts = collections.Counter()
    enemy_len = collections.defaultdict(int) # enemy id -> max len ever reported len>=1
    enemy_cell = collections.defaultdict(dict)  # enemy id -> {round: cell}
    seen_hunt_events = []                    # for convergence tracking
    deaths = {}                              # dragon id -> (round, reason)
    rounds_elig = collections.defaultdict(set)   # team -> set of rounds with >=1 chelig
    rounds_total = collections.defaultdict(set)  # team -> set of rounds with >=1 dragon logging r<r>

    per_round_elig = collections.defaultdict(lambda: collections.defaultdict(int))  # team -> rnd -> count
    per_round_pass = collections.defaultdict(lambda: collections.defaultdict(int))  # pass all gates
    per_round_distok = collections.defaultdict(lambda: collections.defaultdict(int))

    cur = {}
    for e in r['events']:
        ty = e['type']
        if ty == 'roundStart':
            rnd = e['round']
        elif ty == 'dragonSplit':
            team[e['childId']] = e['team']
            team[e['parentId']] = e['team']
            heads[e['childId']] = tuple(e['childBody'][0]) if e['childBody'] else heads.get(e['childId'])
            heads[e['parentId']] = tuple(e['parentBody'][0]) if e['parentBody'] else heads.get(e['parentId'])
        elif ty == 'dragonUpdate':
            heads[e['id']] = tuple(e['head'])
        elif ty == 'dragonDeath':
            deaths[e['id']] = (rnd, e['reason'])
        elif ty == 'sonarPing' and e.get('hitKind') in ('enemy', 'enemyHead'):
            v = e.get('value')
            if v is None:
                continue
            snd = e['senderId']
            if not ping_ours(v, rnd, team.get(snd, 'A')) or msg_type(v) != 1:
                continue
            eid, ex, ey, elen, eq = decode_enemy(v)
            enemy_len[eid] = max(enemy_len[eid], elen)
            enemy_cell[eid][rnd] = (ex, ey)
        elif ty == 'dragonLog':
            txt = e['text']
            m = CHEBIG.search(txt)
            if m:
                t = team.get(e['id'])
                cell, ln, seen, dist, rank = (int(m.group(1)), int(m.group(2)),
                                            int(m.group(3)), int(m.group(4)), int(m.group(5)))
                per_round_elig[t][rnd] += 1
                rounds_elig[t].add(rnd)
                if dist <= MAX_DIST and dist >= 0:
                    per_round_distok[t][rnd] += 1
                    if 0 <= rank < HUNTER_COUNT:
                        per_round_pass[t][rnd] += 1
                continue
            m = CHASSIGN.search(txt)
            if m:
                tid = int(m.group(2)) if m.group(2) else -1
                cell, ln = int(m.group(3)), int(m.group(4) or 0)
                gain = float(m.group(5)) if m.group(5) else None
                mult = float(m.group(6)) if m.group(6) else None
                assigns.append({'r': rnd, 'hunter': e['id'], 'team': team.get(e['id']),
                                'tgt': tid, 'cell': cell, 'len': ln, 'gain': gain,
                                'mult': mult, 'head': heads.get(e['id'])})
                continue
            m = WHY.match(txt)
            if m and m.group(2) in ('champ-hunt', 'champ-ram'):
                why_counts[m.group(2)] += 1
                rounds_total[team.get(e['id'])].add(rnd)
                continue
            if WHY.match(txt):
                rounds_total[team.get(e['id'])].add(rnd)

    # (b) convergence: hunter head -> target cell dist now vs +10r
    conv = []
    for a in assigns:
        if a['head'] is None:
            continue
        d0 = tdist(a['head'], (a['cell'] % W, a['cell'] // W), W, H)
        # find hunter head 10 rounds later — need head timeline; replay heads
        # dict only holds latest, so do a second pass below.
        conv.append((a, d0))
    mname = re.search(r'MAP_NAME\s+(\S+)', r['map'])
    return {'path': path, 'map': mname.group(1) if mname else os.path.basename(path), 'result': r['result'],
            'elig': per_round_elig, 'distok': per_round_distok, 'pass': per_round_pass,
            'assigns': assigns, 'why': why_counts, 'enemy_len': enemy_len,
            'enemy_cell': enemy_cell, 'deaths': deaths, 'team': team,
            'heads_final': heads, 'W': W, 'H': H,
            'rounds_elig': rounds_elig}


def convergence(path):
    """Second pass: for each chassign, track hunter head -> target dist over +15r."""
    r = parse(path)
    W, H, dr, edges = rm.parse_map(r['map'])
    rnd = 0
    heads = {}
    watches = []   # {hunter, cell, team, r0, d0, ds}
    out = []
    pending = collections.defaultdict(list)  # id -> watch idx
    for e in r['events']:
        ty = e['type']
        if ty == 'roundStart':
            rnd = e['round']
            for i, w in enumerate(watches):
                if w['done']:
                    continue
                h = heads.get(w['hunter'])
                if h is None:
                    continue
                d = tdist(h, w['cellxy'], W, H)
                w['ds'][rnd - w['r0']] = d
                if rnd - w['r0'] >= 12:
                    w['done'] = True
        elif ty == 'dragonUpdate':
            heads[e['id']] = tuple(e['head'])
        elif ty == 'dragonSplit':
            heads[e['childId']] = tuple(e['childBody'][0]) if e['childBody'] else heads.get(e['childId'])
            heads[e['parentId']] = tuple(e['parentBody'][0]) if e['parentBody'] else heads.get(e['parentId'])
        elif ty == 'dragonLog':
            m = CHASSIGN.search(e['text'])
            if m:
                cell = int(m.group(3))
                mult = float(m.group(6)) if m.group(6) else None
                h = heads.get(e['id'])
                cellxy = (cell % W, cell // W)
                watches.append({'hunter': e['id'], 'cellxy': cellxy, 'mult': mult,
                                'r0': rnd, 'd0': tdist(h, cellxy, W, H) if h else None,
                                'ds': {}, 'done': False})
    for w in watches:
        if w['d0'] is None or not w['ds']:
            continue
        d_end = w['ds'].get(12, max(w['ds'].values() if w['ds'] else [None]))
        # min distance achieved within 12 rounds
        dmin = min(w['ds'].values())
        out.append({'r0': w['r0'], 'd0': w['d0'], 'd12': w['ds'].get(12), 'dmin': dmin,
                    'mult': w['mult']})
    return out


def main():
    files = []
    for g in sys.argv[1:]:
        files += glob.glob(g)
    files = sorted(set(files))
    all_conv = []
    agg = collections.defaultdict(list)
    agg['hunted_death_reason'] = collections.Counter()
    death_stats = collections.defaultdict(lambda: {'hunted': [0, 0], 'unhunted': [0, 0]})
    game_rows = []
    for p in files:
        try:
            a = analyze(p)
        except Exception as ex:
            print(f'skip {p}: {ex}', file=sys.stderr)
            continue
        # (a) per team-round eligibility
        for t in 'AB':
            for rnd, n in a['elig'][t].items():
                agg['elig_per_round'].append(n)
                agg['distok_per_round'].append(a['distok'][t].get(rnd, 0))
                agg['pass_per_round'].append(a['pass'][t].get(rnd, 0))
        game_elig = sum(sum(d.values()) for d in a['elig'].values())
        game_pass = sum(sum(d.values()) for d in a['pass'].values())
        game_asg = len(a['assigns'])
        # clustering: distinct hunters per (target, 20-round window)
        tgt_windows = collections.defaultdict(set)
        for x in a['assigns']:
            tgt_windows[(x['tgt'] if x['tgt'] >= 0 else x['cell'], x['r'] // 20)].add(x['hunter'])
        for k, s in tgt_windows.items():
            agg['hunters_per_target_window'].append(len(s))
        # hunted-enemy death reasons
        for x in a['assigns']:
            if x['tgt'] >= 0 and x['tgt'] in a['deaths']:
                dr_, rr = a['deaths'][x['tgt']]
                if 0 <= dr_ - x['r'] <= 15:
                    agg['hunted_death_reason'][rr] += 1
        conv = convergence(p)
        all_conv += conv
        # (c) hunted vs unhunted len>=8 enemies
        enemy_team = None
        if a['assigns']:
            teams = [x['team'] for x in a['assigns'] if x['team']]
            if teams:
                enemy_team = 'B' if teams[0] == 'A' else 'A'
        hunted_ids = set(x['tgt'] for x in a['assigns'] if x['tgt'] >= 0)
        # heard assignments: match cell to enemy head at that round — skip, rare
        hunted, unhunted = [], []
        for eid, ln in a['enemy_len'].items():
            if ln < HUNT_LEN or a['team'].get(eid) != enemy_team:
                continue
            (hunted if eid in hunted_ids else unhunted).append(eid)
        for grp, lst in (('hunted', hunted), ('unhunted', unhunted)):
            for eid in lst:
                dead = eid in a['deaths']
                death_stats['all'][grp][dead] += 1
        game_rows.append({'map': a['map'], 'n_asg': game_asg,
                          'elig_dr': game_elig, 'pass_dr': game_pass,
                          'why_ram': a['why']['champ-ram'], 'why_hunt': a['why']['champ-hunt'],
                          'hunted': len(hunted), 'unhunted': len(unhunted),
                          'hunted_dead': sum(1 for i in hunted if i in a['deaths']),
                          'unhunted_dead': sum(1 for i in unhunted if i in a['deaths'])})

    def med(v):
        return statistics.median(v) if v else float('nan')

    print(f'games: {len(game_rows)}')
    print(f'\n(a) eligibility (per team-round, when a len>=8 non-queen candidate exists):')
    print(f'  dragons logging chelig per eligible round: med {med(agg["elig_per_round"]):.1f}')
    print(f'  of those, dist<=20: med {med(agg["distok_per_round"]):.1f}')
    print(f'  of those, rank<3 too: med {med(agg["pass_per_round"]):.1f}')
    tot_elig = sum(agg['elig_per_round']); tot_pass = sum(agg['pass_per_round'])
    print(f'  total dragon-rounds eligible: {tot_elig}; fully pass gates: {tot_pass}')
    print(f'\n(b) assignments: {sum(r["n_asg"] for r in game_rows)} total')
    print(f'  distinct hunters per (target, 20r window): med {med(agg["hunters_per_target_window"]):.1f}  max {max(agg["hunters_per_target_window"] or [0])}')
    print(f'  why counts: champ-hunt turns={sum(r["why_hunt"] for r in game_rows)}, champ-ram turns={sum(r["why_ram"] for r in game_rows)}')
    if agg['hunted_death_reason']:
        print(f'  hunted-target deaths within 15r of assignment: {dict(agg["hunted_death_reason"])}')
    if all_conv:
        d0 = [c['d0'] for c in all_conv if c['d0'] is not None]
        dmin = [c['dmin'] for c in all_conv if c['dmin'] is not None]
        d12 = [c['d12'] for c in all_conv if c.get('d12') is not None]
        print(f'  convergence n={len(d0)}: med dist at assign {med(d0):.1f} -> min over next 12r {med(dmin):.1f} -> at +12r {med(d12):.1f}')
        repelled = sum(1 for c in all_conv if c['dmin'] is not None and c['d0'] is not None and c['dmin'] >= c['d0'] - 0)
        adj = sum(1 for c in all_conv if c['dmin'] is not None and c['dmin'] <= 2)
        print(f'  never got closer than start: {repelled}/{len(all_conv)}')
        print(f'  reached cheb<=2 of target cell: {adj}/{len(all_conv)}')
        # repulsion test: seen assignments with negative pull multiplier
        for lab, sel in (('mult<0 (repulsion)', lambda m: m is not None and m < 0),
                         ('mult>=0', lambda m: m is not None and m >= 0),
                         ('heard (no seen tgt)', lambda m: m is None)):
            sub = [c for c in all_conv if sel(c['mult'])]
            if not sub:
                continue
            a2 = sum(1 for c in sub if c['dmin'] is not None and c['dmin'] <= 2)
            dm = med([c['dmin'] for c in sub if c['dmin'] is not None])
            print(f'  {lab}: n={len(sub)}  reach<=2: {a2} ({100*a2/len(sub):.0f}%)  med dmin {dm:.1f}')
    print(f'\n(c) enemy len>=8 death rates:')
    for grp in ('hunted', 'unhunted'):
        d, a_ = death_stats['all'][grp]
        n = d + a_
        print(f'  {grp}: {d}/{n} died ({100*d/max(1,n):.0f}%)')
    print('\nper-game: map asg elig_dr pass_dr ram hunt hunted[dead/tot] unhunted[dead/tot]')
    for g in game_rows:
        print(f'  {g["map"]:<18} {g["n_asg"]:>3} {g["elig_dr"]:>5} {g["pass_dr"]:>5} {g["why_ram"]:>4} {g["why_hunt"]:>4}  {g["hunted_dead"]}/{g["hunted"]} {g["unhunted_dead"]}/{g["unhunted"]}')


if __name__ == '__main__':
    main()
