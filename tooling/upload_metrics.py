"""Per-upload ladder metrics (steering brief §5): parse our replays and emit the
canonical table — per opponent tier + per map.
Usage: python3 tooling/upload_metrics.py <match_ids...> | --since <id>
"""
import sys, collections, glob
sys.path.insert(0, 'handoff/tooling')
from parse_replay import parse

def bodylen(e):
    # dragonUpdate carries head/tail; splits carry body arrays. For length we use
    # the engine's own 'body' when present else infer 2.
    return len(e.get('body', [])) if 'body' in e else None

def game_metrics(path):
    rep = parse(path)
    teams = {}
    for e in rep['events']:
        if e['type'] == 'dragonSplit':
            teams[e['childId']] = e['team']; teams[e['parentId']] = e['team']
    dead = set()
    deaths = collections.defaultdict(list)   # team -> [(round,reason)]
    rd = -1
    alive_r = collections.defaultdict(lambda: collections.Counter())
    len_sum = collections.defaultdict(lambda: collections.Counter())
    max_len = collections.defaultdict(lambda: collections.Counter())
    queen_dead = {'A': None, 'B': None}
    schooltime = 'schooltime' in rep['map'].lower()
    queen_alive_r5 = {'A': None, 'B': None}
    hitself_300_399 = collections.Counter()
    for e in rep['events']:
        if e['type'] == 'roundStart': rd = e['round']
        elif e['type'] == 'dragonUpdate':
            t = teams.get(e['id'])
            if not t: continue
            if e['id'] in dead: continue
            alive_r[t][rd] += 0  # marker (counted via seen below)
        elif e['type'] == 'dragonDeath':
            dead.add(e['id']); t = teams.get(e['id'])
            if t:
                deaths[t].append((rd, e['reason']))
                if 300 <= rd <= 399 and e['reason'] == 'hitSelf': hitself_300_399[t] += 1
                if e['id'] == 0: queen_dead['A'] = rd
                if e['id'] == 1: queen_dead['B'] = rd
    # second pass: alive counts + lengths per checkpoint round
    check = [5, 25, 50, 100, 200, 300, 400, 499]
    live = {'A': collections.Counter(), 'B': collections.Counter()}
    lens = {'A': collections.defaultdict(list), 'B': collections.defaultdict(list)}
    # rebuild alive sets at checkpoints: a dragon is alive at r if first update <= r < death
    first_seen = {}; last_seen = {}; maxlen = collections.defaultdict(lambda: collections.Counter())
    rd = -1
    for e in rep['events']:
        if e['type'] == 'roundStart': rd = e['round']
        elif e['type'] == 'dragonUpdate':
            i = e['id']; t = teams.get(i)
            if not t: continue
            first_seen.setdefault(i, rd); last_seen[i] = rd
    deadr = {}
    rd = -1
    for e in rep['events']:
        if e['type'] == 'roundStart': rd = e['round']
        elif e['type'] == 'dragonDeath': deadr[e['id']] = rd
    for i, t in teams.items():
        d = deadr.get(i, 10**9)
        for c in check:
            if first_seen.get(i, 10**9) <= c < d:
                live[t][c] += 1
    # lengths: from split parentBody/childBody and death bodies — approx via
    # 'dragonUpdate' head-tail manhattan? The replay lacks body. Use maxlen from
    # split events' parentBody length.
    plen = collections.defaultdict(dict)
    rd = -1
    for e in rep['events']:
        if e['type'] == 'roundStart': rd = e['round']
        elif e['type'] == 'dragonSplit':
            plen[e['parentId']][rd] = len(e.get('parentBody', []))
            plen[e['childId']][rd] = len(e.get('childBody', []))
    # propagate: at each checkpoint, each dragon's last known len
    for i, t in teams.items():
        ks = sorted(plen.get(i, {}))
        for c in check:
            prior = [k for k in ks if k <= c]
            if prior: lens[t][c]  # placeholder
            last = plen[i][prior[-1]] if prior else (2 if first_seen.get(i, 10**9) <= c < deadr.get(i, 10**9) else 0)
            maxlen[t][c] = max(maxlen[t][c], last)
    return {
        'map': next((l.split('MAP_NAME ')[1].split()[0] for l in rep['map'].splitlines() if 'MAP_NAME' in l), '?'),
        'rounds': rd,
        'deaths': {t: dict(collections.Counter(x[1] for x in deaths[t])) for t in 'AB'},
        'hitSelf300': dict(hitself_300_399),
        'queenDead': queen_dead,
        'alive': {t: dict(live[t]) for t in 'AB'},
        'maxlen': {t: dict(maxlen[t]) for t in 'AB'},
    }

if __name__ == '__main__':
    files = sys.argv[1:]
    if not files: files = sorted(glob.glob('ladder_replays/*.replay'))
    for f in files:
        try:
            m = game_metrics(f)
            print(f"{f.split('/')[-1]:<22} {m['map']:<14} r{m['rounds']} alive {m['alive']} maxlen {m['maxlen']} hs300 {m['hitSelf300']} qdead {m['queenDead']}")
        except Exception as ex:
            print(f, 'ERR', ex)
