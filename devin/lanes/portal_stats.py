"""Portal transits per side from kmatch replays.
A transit = dragonUpdate head lands >1 torus-step from its previous head.
Prints per-map aggregates: transits by r25/r50/first-transit round, split by
which named bot held that side."""
import collections, glob, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../handoff/tooling'))
from parse_replay import parse

def analyze(path):
    r = parse(path)
    ev = r['events']
    W = H = 0
    dr = []
    for line in r['map'].split('\n'):
        p = line.split()
        if not p: continue
        if p[0] == 'MAP': W, H = int(p[1]), int(p[2])
        elif p[0] == 'DRAGON':
            t, n = int(p[1]), int(p[2])
            c = list(map(int, p[3:3+2*n]))
            dr.append((t, [(c[2*i], c[2*i+1]) for i in range(n)]))
    head, team = {}, {}
    for e in ev:
        if e['type'] == 'roundStart': break
        if e['type'] == 'dragonUpdate' and e['id'] < len(dr):
            t, b = dr[e['id']]
            head[e['id']] = tuple(b[0]); team[e['id']] = 'AB'[t]
    transit = collections.defaultdict(list)
    rnd = 0
    for e in ev:
        if e['type'] == 'roundStart': rnd = e['round']
        elif e['type'] == 'dragonUpdate':
            i = e['id']
            nh = tuple(e['head'])
            if i in head:
                oh = head[i]
                dx = min(abs(nh[0]-oh[0]), W-abs(nh[0]-oh[0]))
                dy = min(abs(nh[1]-oh[1]), H-abs(nh[1]-oh[1]))
                if dx+dy > 1:
                    transit[team[i]].append(rnd)
            head[i] = nh
        elif e['type'] == 'dragonSplit':
            head[e['childId']] = tuple(e['childBody'][0]); team[e['childId']] = e['team']
    return {'A':r['botA'],'B':r['botB']}, transit

if __name__ == '__main__':
    d = sys.argv[1]
    agg = collections.defaultdict(lambda: collections.Counter())
    for f in sorted(glob.glob(os.path.join(d, '*.replay'))):
        mapname = os.path.basename(f).split('-s')[0]
        bots, tr = analyze(f)
        for side, rs in tr.items():
            bot = bots[side]
            k = (mapname, bot)
            agg[k]['games'] += 0  # counted below
            agg[k]['tr'] += len(rs)
            agg[k]['tr25'] += sum(1 for x in rs if x <= 25)
            agg[k]['tr50'] += sum(1 for x in rs if x <= 50)
            if rs: agg[k]['first'] = min(agg[k].get('first', 999), min(rs))
    counts = collections.Counter()
    for f in glob.glob(os.path.join(d, '*.replay')):
        r = parse(f)
        mapname = os.path.basename(f).split('-s')[0]
        for s, b in {'A':r['botA'],'B':r['botB']}.items():
            counts[(mapname, b)] += 1
    print(f"{'map':<18}{'bot':<18}{'g':>3}{'tr':>4}{'tr<=25':>7}{'tr<=50':>7}{'firstR':>7}")
    for k in sorted(agg):
        a = agg[k]
        print(f"{k[0]:<18}{k[1]:<18}{counts[k]:>3}{a['tr']:>4}{a['tr25']:>7}{a['tr50']:>7}{a.get('first','-'):>7}")

# Winner benchmarks pearls@r25/r50: QoS 6/20, Trophy 10/44, Default 6/18,
# Stripes 8/24, PD 20/35, Devil 12/54, TD 1/4
BENCH = {'queen_of_spades':(6,20),'trophy':(10,44),'default':(6,18),'stripes':(8,24),'dilemma':(20,35),'devil':(12,54),'tower_defense':(1,4)}
def bench(tag_games):
    import json as J
    agg = collections.defaultdict(lambda: collections.Counter())
    for l in open(tag_games):
        g = J.loads(l)
        for side in ('c','b'):
            a = agg[(g['map'], 'cand' if side=='c' else 'base')]
            a['n'] += 1
            a['e25'] += g[side].get('eat25') or 0
            a['e50'] += g[side].get('eat50') or 0
            a['tl25'] += g[side].get('tl25') or 0
            a['n25'] += g[side].get('n25') or 0
    print(f"{'map':<16}{'side':<6}{'e25':>5}{'(win)':>6}{'e50':>5}{'(win)':>6}{'n25':>5}{'tl25':>6}")
    for (m,s),a in sorted(agg.items()):
        n=a['n']; b25,b50=BENCH.get(m,(0,0))
        print(f"{m:<16}{s:<6}{a['e25']/n:>5.1f}{b25:>6}{a['e50']/n:>5.1f}{b50:>6}{a['n25']/n:>5.1f}{a['tl25']/n:>6.1f}")
if __name__ == '__main__' and len(sys.argv) > 2:
    bench(sys.argv[2])
