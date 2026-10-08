"""Pawn-donation recipe vs engine rule: dead dragons drop ceil(len/2) pearls
on segments 0,2,4,... of their body.

For every death of side `tag`:
 (a) pawn (len-2) drops: who eats the drop pearl (lands on head cell)?
     eater's length at eat round, is it the team-longest / queen / any len>=4
     ally / short ally / enemy / decayed(k=5). Also eater's distance at death
     round (was the consumer already adjacent?)
 (b) pawn death mix: reason distribution, on-bed share (death head within
     cheb-1 of a >=3-add bed cell), dist to nearest len>=4 ally head.
 (c) unit-count threshold: pawn-death rate conditioned on team alive-count
     bins, plus spawn->death lag for split-born pawns.
 Engine-rule verification: fraction of len-2 deaths with a hasPearl add at
 the head cell same round; for len>=3 share of expected seg-0/2/4 cells
 receiving an add.
Winner = result.winner; tag sides 'win'/'lose'.
"""
import sys, os, glob, json, collections, bisect
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../handoff/tooling'))
from parse_replay import parse
from pocket_metric import parse_map

def tcheb(W, H, a, b):
    dx = abs(a[0] - b[0]); dy = abs(a[1] - b[1])
    return max(min(dx, W - dx), min(dy, H - dy))

QID = {'A': 0, 'B': 1}

def analyze(path):
    r = parse(path)
    W, H, dr, _ = parse_map(r['map'])
    team = {i: 'AB'[t] for i, (t, _b) in enumerate(dr)}
    winner = (r.get('result') or {}).get('winner')
    body = {}; heads = {}; born = {}
    lendat = collections.defaultdict(list)   # id -> [(rnd,len)]
    rnd = 0
    deaths = []          # (rnd,id,team,reason,bodylist)
    adds = collections.defaultdict(list)     # cell -> [add rounds]
    rems = collections.defaultdict(list)     # cell -> [removal rounds]
    bedscore = collections.Counter()
    maxr = 0
    events = r['events']
    # first pass: per-unit head timeline + death records + pearl events
    hhead = collections.defaultdict(dict)
    for e in events:
        ty = e['type']
        if ty == 'roundStart':
            rnd += 1; maxr = rnd
        elif ty == 'tileChange':
            c = tuple(e['tile'])
            if e.get('hasPearl'):
                adds[c].append(rnd); bedscore[c] += 1
            else:
                rems[c].append(rnd)
        elif ty == 'dragonUpdate':
            i = e['id']; b = body.setdefault(i, collections.deque())
            h, tl = tuple(e['head']), tuple(e['tail'])
            if not b:
                # seed straight-line body head..tail when collinear
                if h[0] == tl[0] or h[1] == tl[1]:
                    x, y = tl; hx, hy = h
                    sx = (hx > x) - (hx < x); sy = (hy > y) - (hy < y)
                    while (x, y) != (hx, hy):
                        b.append((x, y)); x += sx; y += sy
                    b.append((hx, hy)); b.reverse()
                else:
                    b.append(h)
            else:
                if b[0] != h: b.appendleft(h)
                while len(b) > 1 and b[-1] != tl: b.pop()
            heads[i] = h; hhead[i][rnd] = h
            born.setdefault(i, 1)
            lendat[i].append((rnd, len(b)))
        elif ty == 'dragonSplit':
            body[e['parentId']] = collections.deque(tuple(x) for x in e['parentBody'])
            body[e['childId']] = collections.deque(tuple(x) for x in e['childBody'])
            team[e['childId']] = e['team']; born[e['childId']] = rnd
            heads[e['parentId']] = tuple(e['parentBody'][0])
            heads[e['childId']] = tuple(e['childBody'][0])
            hhead[e['parentId']][rnd] = tuple(e['parentBody'][0])
            hhead[e['childId']][rnd] = tuple(e['childBody'][0])
            lendat[e['parentId']].append((rnd, len(e['parentBody'])))
            lendat[e['childId']].append((rnd, len(e['childBody'])))
        elif ty == 'dragonDeath':
            i = e['id']
            if i in body:
                deaths.append((rnd, i, team.get(i), e['reason'], list(body[i])))
                body.pop(i); heads.pop(i, None)
            lendat[i].append((rnd, 0))
    # per-round arrays for heads + alive + lengths
    harr = {}; lenarr = {}
    for i, hh in hhead.items():
        arr = [None]*(maxr+2); last = None
        for rr in range(0, maxr+1):
            if rr in hh: last = hh[rr]
            arr[rr] = last
        harr[i] = arr
    for i, ld in lendat.items():
        ld.sort()
        rr_ = [x[0] for x in ld]; vv = [x[1] for x in ld]
        arr = [0]*(maxr+2)
        for k in range(len(rr_)):
            a = rr_[k]; b2 = rr_[k+1] if k+1 < len(rr_) else maxr+1
            for x in range(a, min(b2, maxr+1)): arr[x] = vv[k]
        lenarr[i] = arr
    def alive_cnt(s, rr):
        return sum(1 for i in harr if team.get(i) == s and lenarr[i][rr] > 0)
    beds = {c for c, n in bedscore.items() if n >= 3}

    # collect outcomes per side-tag
    out = collections.defaultdict(lambda: collections.Counter())
    per_death = []
    for drr, i, s, reason, bl in deaths:
        if s is None or winner is None or not bl: continue
        tag = 'win' if s == winner else 'lose'
        h = bl[0]
        L = len(bl)
        seg = bl[::2]                    # expected drop cells
        # engine verification
        exp = len(seg); got = 0
        for c in seg:
            if any(a >= drr and a <= drr+1 for a in adds.get(c, [])): got += 1
        out[tag]['exp_drops'] += exp; out[tag]['got_drops'] += got
        if L == 2:
            out[tag][f'L2_{reason}'] += 1
            out[tag]['L2_tot'] += 1
        # alive count of own team at death
        ac = alive_cnt(s, drr)
        # nearest len>=4 ally head (excl self)
        dl4 = min((tcheb(W, H, h, harr[j][drr]) for j in harr
                   if j != i and team.get(j) == s and lenarr[j][drr] >= 4 and harr[j][drr]),
                  default=None)
        # on-bed?
        onbed = any(tcheb(W, H, h, bc) <= 1 for bc in beds)
        # drops: attribute each seg cell's add
        drop_info = []
        for c in seg:
            arnd = next((a for a in adds.get(c, []) if a >= drr and a <= drr+1), None)
            if arnd is None: continue
            rr2 = next((x for x in rems.get(c, []) if x > arnd), None)
            ent = {'cell': c}
            if rr2 is None or rr2 - arnd > 5:
                ent['fate'] = 'decay5' if rr2 is None or rr2 - arnd > 5 else '?'
                if rr2 is not None and rr2 - arnd <= 20: ent['fate'] = 'late'
                ent['rr2'] = rr2
            else:
                # eater = nearest head at rr2 within d<=1
                best, bd = None, 2
                for j in harr:
                    hj = harr[j][rr2]
                    if hj is None or lenarr[j][rr2] <= 0: continue
                    dd = tcheb(W, H, hj, c)
                    if dd < bd: bd, best = dd, j
                if best is None:
                    ent['fate'] = 'unattr'
                else:
                    et = team.get(best); el = lenarr[best][rr2]
                    ent['eater_team'] = et; ent['eater_len'] = el
                    ent['eater_queen'] = (best == QID.get(et))
                    ent['eater_d_at_death'] = tcheb(W, H, harr[best][drr], c) if harr[best][drr] else None
                    ent['fate'] = 'ally' if et == s else 'enemy'
                    # is eater the team longest?
                    ml = max((lenarr[j][rr2] for j in harr if team.get(j) == et), default=0)
                    ent['eater_longest'] = el == ml and el > 0
            drop_info.append(ent)
        per_death.append({'tag': tag, 'team': s, 'rnd': drr, 'reason': reason,
                          'len': L, 'alive': ac, 'dl4': dl4, 'onbed': onbed,
                          'drops': drop_info, 'born': born.get(i)})
    return per_death, maxr

def main():
    all_d = []
    for f in sorted(glob.glob(sys.argv[1] + '/*.replay')):
        try:
            pd, mx = analyze(f)
            for d in pd: d['match'] = os.path.basename(f)
            all_d.extend(pd)
        except Exception as ex:
            print('ERR', f, ex)
    print('deaths', len(all_d))
    for tag in ('win', 'lose'):
        dd = [d for d in all_d if d['tag'] == tag]
        pawns = [d for d in dd if d['len'] == 2]
        print(f"\n== {tag}: {len(dd)} deaths, {len(pawns)} pawn(len2)")
        rs = collections.Counter(d['reason'] for d in pawns)
        print(' pawn reasons:', dict(rs))
        onb = sum(1 for d in pawns if d['onbed'])
        dl4 = [d['dl4'] for d in pawns if d['dl4'] is not None]
        dl4.sort()
        print(f" pawn on-bed {onb} ({100*onb/max(len(pawns),1):.0f}%) | d->len>=4 ally med {dl4[len(dl4)//2] if dl4 else '-'} p25 {dl4[len(dl4)//4] if dl4 else '-'} | within2 {sum(1 for x in dl4 if x<=2)}")
        # alive-count distribution at pawn deaths
        acs = sorted(d['alive'] for d in pawns)
        print(f" alive@death med {acs[len(acs)//2] if acs else '-'} p25 {acs[len(acs)//4] if acs else '-'} p75 {acs[3*len(acs)//4] if acs else '-'}")
        bins = collections.Counter(min(d['alive'],20)//5*5 for d in pawns)
        print(' alive bins:', dict(sorted(bins.items())))
        # drops fate
        fates = collections.Counter(); elens = []
        longest = queen = ge4 = short = 0
        near0 = 0; tot = 0
        for d in pawns:
            for drp in d['drops']:
                tot += 1
                fates[drp.get('fate','?')] += 1
                if drp.get('fate') == 'ally':
                    el = drp['eater_len']; elens.append(el)
                    longest += drp.get('eater_longest') and 1 or 0
                    queen += drp.get('eater_queen') and 1 or 0
                    ge4 += (el >= 4) and 1 or 0
                    short += (el < 4) and 1 or 0
                    if drp.get('eater_d_at_death') is not None and drp['eater_d_at_death'] <= 2: near0 += 1
        elens.sort()
        print(f" pawn drops {tot}: {dict(fates)}")
        if elens:
            print(f" ally-eater len med {elens[len(elens)//2]} p25 {elens[len(elens)//4]} p75 {elens[3*len(elens)//4]} | longest {longest} queen {queen} len>=4 {ge4} len<4 {short} | eater<=2 at death {near0}")
        # spawn->death lag for split-born pawns
        lags = sorted(d['rnd'] - d['born'] for d in pawns if d['born'] and d['rnd'] >= d['born'])
        if lags:
            print(f" pawn age@death med {lags[len(lags)//2]} p25 {lags[len(lags)//4]} | <=5 {sum(1 for x in lags if x<=5)} <=15 {sum(1 for x in lags if x<=15)}")

main()
