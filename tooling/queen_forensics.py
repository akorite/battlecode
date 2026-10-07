#!/usr/bin/env python3
"""Queen + champ forensics on replays: winning vs losing side."""
import sys, os, glob
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'handoff', 'tooling'))
import parse_replay
from collections import defaultdict
import statistics as st

def cheb(a,b): return max(abs(a[0]-b[0]),abs(a[1]-b[1]))

files=[]
for pat in sys.argv[1:]:
    files += glob.glob(pat) if any(c in pat for c in '*?[') else [pat]

agg=defaultdict(lambda: {'qbud':[],'qlen':[],'qdead':0,'splits':0,'n':0,
                         'longest':[],'total':[],'count':[],
                         'qdc':defaultdict(list)})
for f in files:
    try: d=parse_replay.parse(f)
    except Exception as ex: print('skip',f,ex); continue
    ev=d['events']; rnd=0
    last={}; team={}
    splits=defaultdict(list); deaths=defaultdict(list)
    qtrack=defaultdict(lambda: defaultdict(list))
    for e in ev:
        t=e['type']
        if t=='roundStart': rnd=e['round']
        elif t=='dragonUpdate':
            last[e['id']]={'head':tuple(e['head']),'len':len(e.get('tail',[]))+1,'rnd':rnd}
        elif t=='dragonSplit':
            team[e['childId']]=e['team']
            pl=len(e.get('parentBody',[])); cl=len(e.get('childBody',[]))
            splits[e['team']].append((rnd,pl,cl,e.get('parentId',-1)))
        elif t=='dragonDeath':
            deaths[e['id']%2 and 'B' or 'A'].append((rnd,e['id'],e['reason']))
    # team assignment for queen ids: queens are ids 0,1 — team via first splits' parents is
    # unreliable; ladder convention: id 0 -> A, id 1 -> B (same as parity rule used before).
    byrnd=defaultdict(list)
    for i,s in last.items(): byrnd[s['rnd']].append((i,s))
    for R,items in byrnd.items():
        if R%50: continue
        for tm,qid in (('A',0),('B',1)):
            q=last.get(qid)
            if not q or q['rnd']!=R: continue
            allies=[s['head'] for i,s in items if i!=qid and (team.get(i) or ('A' if i%2==0 else 'B'))==tm]
            if not allies: continue
            cx=sum(h[0] for h in allies)/len(allies); cy=sum(h[1] for h in allies)/len(allies)
            qtrack[tm][R].append((cheb(q['head'],(round(cx),round(cy))),q['len']))
    res=d.get('result') or {}
    win=res.get('winner','?')
    for tm,qid,tk in (('A',0,'teamA'),('B',1,'teamB')):
        side='W' if win==tm else 'L'
        g=agg[side]; g['n']+=1
        st_ = res.get(tk) or {}
        if st_: g['longest'].append(st_.get('longestDragon',0)); g['total'].append(st_.get('totalLength',0)); g['count'].append(st_.get('dragonCount',0))
        g['qbud'].append(len([x for x in splits[tm] if x[3]==qid]))
        g['splits']+=len(splits[tm])
        g['qdead']+=1 if any(x[1]==qid for x in deaths[tm]) else 0
        g['qlen'].append(last[qid]['len'] if qid in last else 0)
        for R,v in qtrack[tm].items():
            for dc,ln in v: g['qdc'][R].append((dc,ln))

for side in ('W','L'):
    g=agg[side]
    print(f"=== {side} (n={g['n']})")
    if g['longest']: print(f"  end: longest med {st.median(g['longest']):.0f} | total med {st.median(g['total']):.0f} | count med {st.median(g['count']):.0f}")
    print(f"  queen buds/game: med {st.median(g['qbud'])} | splits/game {g['splits']/g['n']:.0f}")
    print(f"  queen end len: med {st.median(g['qlen']):.0f} | died {g['qdead']}/{g['n']}")
    for R in sorted(g['qdc']):
        dcs=[x[0] for x in g['qdc'][R]]; lns=[x[1] for x in g['qdc'][R]]
        print(f"    r{R:3d}: queen-centroid med {st.median(dcs):.0f}  qlen med {st.median(lns):.0f} (n={len(dcs)})")
