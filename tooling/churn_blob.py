"""Churn-geometry: where do deaths land vs the rolling longest (champ),
and what mechanism keeps winners' churn in-blob?

Per replay, per side:
  dc_med / dc dist  : death cell -> champ head (longest live OTHER same-side
                      dragon) at death round. All deaths + deliberate-only.
  sc_med            : child spawn head -> champ head at split round
                      (excluding the parent itself from champ candidacy? no -
                      champ = longest live same-side, parent excluded if it IS
                      the longest? we allow parent since it's alive).
  liveR_med         : per 25 rounds, median over live same-side heads of
                      dist(head -> champ head). Actual swarm spread.
  forage_med        : consume events (tileChange pearl False): cell ->
                      champ head at that round. Forage radius around champ.
  delib share       : hitSelf+noValidAction fraction of deaths.

Answers: in-blob churn = swarm co-located (small liveR), spawn placement
(small sc), or deliberate die-in-place near champ (delib dc small but
liveR large)?

Usage: python3 churn_blob.py <replay_or_dir> [...] -> JSONL (one per file,
fields sideA/sideB dicts)
"""
import collections, glob, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
from parse_replay import parse
from pocket_metric import parse_map

def med(v):
    if not v: return None
    v = sorted(v); return v[len(v) // 2]

def analyze(path):
    r = parse(path)
    ev = r['events']
    W, H, dr, edges = parse_map(r['map'])
    def dist(a, b):
        dx = abs(a[0] - b[0]); dy = abs(a[1] - b[1])
        return max(min(dx, W - dx), min(dy, H - dy))
    body, team, heads = {}, {}, {}
    spawn0 = {}
    for e in ev:
        if e['type'] == 'roundStart': break
        if e['type'] == 'dragonUpdate' and e['id'] < len(dr):
            t, b = dr[e['id']]
            body[e['id']] = collections.deque(b)
            team[e['id']] = 'AB'[t]
            heads[e['id']] = tuple(b[0])
            spawn0[e['id']] = (tuple(b[0]), 'AB'[t])
    S = {s: {'dc': [], 'dc_cheb': [], 'dc_delib': [], 'sc': [], 'liveR': [], 'forage': [],
             'deaths': 0, 'delib': 0, 'splits': 0, 'dc_by': collections.defaultdict(list),
             'sd': [], 'spawn': {}, 'dc_len4': [], 'dc_end': []} for s in 'AB'}
    for i,(sp,s) in spawn0.items():
        S[s]['spawn'][i] = sp
    rnd = 0
    flips = []          # (cell, rnd) consume candidates
    live_end = {}       # final live set per side for end-champ
    def champ_of(s, exclude=None):
        best, blen = None, 0
        for j, b2 in body.items():
            if j == exclude or team.get(j) != s: continue
            if len(b2) > blen: blen, best = len(b2), j
        return best
    for e in ev:
        ty = e['type']
        if ty == 'roundStart':
            rnd = e['round']
            if rnd % 25 == 0:
                for s in 'AB':
                    c = champ_of(s)
                    if c is None: continue
                    ch = heads.get(c)
                    if ch is None: continue
                    ds = [dist(h, ch) for i, h in heads.items()
                          if team.get(i) == s and i != c]
                    m = med(ds)
                    if m is not None: S[s]['liveR'].append(m)
        elif ty == 'dragonUpdate':
            i = e['id']
            if i not in body: continue
            b = body[i]; h, tl = tuple(e['head']), tuple(e['tail'])
            if b[0] != h: b.appendleft(h)
            while len(b) > 1 and b[-1] != tl: b.pop()
            heads[i] = h
        elif ty == 'dragonSplit':
            s = e['team']
            body[e['parentId']] = collections.deque(tuple(x) for x in e['parentBody'])
            c = e['childId']
            body[c] = collections.deque(tuple(x) for x in e['childBody'])
            team[c] = s
            heads[e['parentId']] = tuple(e['parentBody'][0])
            heads[c] = tuple(e['childBody'][0])
            S[s]['spawn'][c] = heads[c]
            S[s]['splits'] += 1
            ch_id = champ_of(s, exclude=c)
            if ch_id is not None and ch_id in heads:
                S[s]['sc'].append(dist(heads[c], heads[ch_id]))
        elif ty == 'tileChange':
            if e.get('hasPearl') is False:
                flips.append((tuple(e['tile']), rnd))
        elif ty == 'dragonDeath':
            i = e['id']
            s = team.get(i)
            if s is None: continue
            h = heads.get(i)
            if h is not None: S[s].setdefault('_deathcells', []).append((rnd, h))
            c = champ_of(s, exclude=i)
            if h and c is not None and c in heads:
                d = dist(h, heads[c])
                S[s]['dc'].append(d)
                S[s]['dc_cheb'].append(max(abs(h[0]-heads[c][0]), abs(h[1]-heads[c][1])))
                S[s]['dc_by'][e['reason']].append(d)
                if len(body[i]) >= 4: S[s]['dc_len4'].append(d)
                if e['reason'] in ('hitSelf', 'noValidAction'):
                    S[s]['dc_delib'].append(d)
            S[s]['deaths'] += 1
            if h and i in S[s]['spawn']:
                S[s]['sd'].append(dist(h, S[s]['spawn'][i]))
            if e['reason'] in ('hitSelf', 'noValidAction'): S[s]['delib'] += 1
            body.pop(i, None); heads.pop(i, None)
    # end-champ positions: last-known head of each side's final longest
    for s in 'AB':
        eid = champ_of(s)
        eh = heads.get(eid) if eid is not None else None
        if eh is not None:
            for rr, hh in S[s].get('_deathcells', []):
                S[s]['dc_end'].append(dist(hh, eh))
    # end-champ per side = longest of final live set; attribute flips by round is
    # expensive, approximate forage with pos snapshot: skip if no live heads
    res = {'file': os.path.basename(path)}
    # forage: rebuild from flips needs per-round heads; approximated during loop
    # already skipped -> compute via stored flips + final pass over nothing
    for s in 'AB':
        d = S[s]
        res[s] = {
            'deaths': d['deaths'], 'delib': d['delib'], 'splits': d['splits'],
            'dc_med': med(d['dc']), 'dc_mean': round(sum(d['dc']) / max(1, len(d['dc'])), 1),
            'dc_delib_med': med(d['dc_delib']),
            'sc_med': med(d['sc']), 'sc_mean': round(sum(d['sc']) / max(1, len(d['sc'])), 1),
            'liveR_med': med(d['liveR']), 'liveR_mean': round(sum(d['liveR']) / max(1, len(d['liveR'])), 1),
            'dc_cheb_med': med(d['dc_cheb']), 'dc_cheb_mean': round(sum(d['dc_cheb'])/max(1,len(d['dc_cheb'])),1),
            'sd_med': med(d['sd']),
            'dc_len4_med': med([x for x in d['dc_len4']]),
            'dc_end_med': med(d['dc_end']),
            'dc_by': {k: med(v) for k, v in d['dc_by'].items()},
        }
        ds = sorted(d['dc'])
        res[s]['dc_p25'] = ds[len(ds) // 4] if ds else None
        res[s]['dc_p75'] = ds[3 * len(ds) // 4] if ds else None
    return res

if __name__ == '__main__':
    files = []
    for a in sys.argv[1:]:
        if os.path.isdir(a): files += sorted(glob.glob(os.path.join(a, '*.replay')))
        else: files.append(a)
    for f in files:
        try:
            print(json.dumps(analyze(f)))
        except Exception as ex:
            print(json.dumps({'file': os.path.basename(f), 'error': str(ex)}))
