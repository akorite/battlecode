#!/usr/bin/env python3
"""Early-elim classification: for each teamEliminated game lost by ~r300,
classify (a) our queen rammed, (b) queen-vs-queen ram, (c) colony attrition,
(d) pearl deficit; plus winner/loser state at r25/r50/r100."""
import sys, json, glob, io, contextlib, statistics as st
sys.path.insert(0,'handoff/tooling')
from parse_replay import parse

def mean(xs): return round(st.mean(xs),1) if xs else None

def analyze(path, who_is_us):
    buf=io.StringIO()
    with contextlib.redirect_stdout(buf):
        try: p=parse(path)
        except Exception as e: return None
    if not p['result'] or p['result']['endReason']!='teamEliminated': return None
    loser='A' if p['result']['winner']=='B' else 'B'
    if who_is_us=='A' and loser!='A': return None   # only our losses
    name='?'; W=H=0
    for ln in p['map'].splitlines():
        q=ln.split()
        if q and q[0]=='MAP': W,H=int(q[1]),int(q[2])
        if q and q[0]=='MAP_NAME': name=ln.split(None,1)[1].strip()
    rnd=0; end=0; pearls={'A':0,'B':0}
    heads={}; dead={}; splits={'A':[],'B':[]}
    # pearl attribution: tileChange hasPearl False -> nearest head <=1
    lastheads={'A':[],'B':[]}
    snap={}
    deathorder=[]
    qd={}
    for e in p['events']:
        t=e['type']
        if t=='roundStart':
            rnd=e['round']; end=rnd
            if rnd in (25,50,100):
                snap[rnd]={'heads':dict(heads),'dead':set(dead),'pearls':dict(pearls),
                           'splits':{s:len(splits[s]) for s in 'AB'}}
        elif t=='dragonUpdate':
            heads[e['id']]=tuple(e['head'])
        elif t=='dragonDeath':
            dead[e['id']]=(rnd,e['reason']); deathorder.append((e['id'],rnd,e['reason']))
            if e['id'] in (0,1): qd[e['id']]=(rnd,e['reason'])
        elif t=='dragonSplit': splits[e['team']].append(rnd)
        elif t=='tileChange' and not e['hasPearl']:
            # nearest living head within cheb 1 of the tile
            tx,ty=e['tile']
            best=None
            for i,h in heads.items():
                if i in dead: continue
                if abs(h[0]-tx)<=1 and abs(h[1]-ty)<=1:
                    best='A' if i%2==0 else 'B'; break
            if best: pearls[best]+=1
    # classify
    loserq=0 if loser=='A' else 1
    winnerq=1-loserq
    lq_death=qd.get(loserq); wq_death=qd.get(winnerq)
    loserkills=[d for d in deathorder if d[0]%2==(0 if loser=='A' else 1)]
    cls='attrition'
    detail=''
    if lq_death and lq_death[1]=='hitHeadToHead' and (not wq_death or wq_death[0]>=lq_death[0]):
        cls='queen-rammed'; detail=f"queen h2h @{lq_death[0]}"
        if wq_death and wq_death[0]==lq_death[0]: cls='queen-v-queen'; detail+= " mutual"
    if cls=='attrition':
        # pearl deficit check at r50
        p50=snap.get(50,{}).get('pearls',{})
        if p50.get(loser,0) <= 0.5*max(1,p50.get('A' if loser=='B' else 'B',1)):
            cls='pearl-deficit'
    return {'map':name,'loser':loser,'end':end,'cls':cls,'detail':detail,
            'lq':lq_death,'wq':wq_death,
            'snap':snap,
            'loserkills_first':[d for d in deathorder if d[0]%2==(0 if loser=='A' else 1)][:3],
            'nc':W*H}

games=[]
for f in sorted(glob.glob('ladder_replays/*.replay')+glob.glob('pdtd_replays/*.replay')):
    r=analyze(f,'A')   # we are team A on ladder
    if r and r['end']<=300:
        r['file']=f.split('/')[-1]
        games.append(r)
        print(f"{r['file']:>20} {r['map']:>18} elim@{r['end']:>3} -> {r['cls']} {r['detail']} lq={r['lq']} wq={r['wq']}")
print()
from collections import Counter
print("CLASS COUNTS:",Counter(g['cls'] for g in games))
# winner-state comparison at r25/r50/r100
print("\n=== winner vs loser state at checkpoints (our losses) ===")
for R in (25,50,100):
    rows=[(g['map'],g['snap'][R]) for g in games if R in g['snap']]
    if not rows: continue
    wal=sum(len([1 for i,h in s['heads'].items() if i%2==1 and i not in s['dead']]) for m,s in rows)/len(rows)
    lal=sum(len([1 for i,h in s['heads'].items() if i%2==0 and i not in s['dead']]) for m,s in rows)/len(rows)
    wsp=sum(s['splits']['B'] for m,s in rows)/len(rows)
    lsp=sum(s['splits']['A'] for m,s in rows)/len(rows)
    wp=sum(s['pearls']['B'] for m,s in rows)/len(rows)
    lp=sum(s['pearls']['A'] for m,s in rows)/len(rows)
    print(f"r{R} n={len(rows)}: alive L={lal:.1f} W={wal:.1f} | splits L={lsp:.1f} W={wsp:.1f} | pearls L={lp:.1f} W={wp:.1f}")
