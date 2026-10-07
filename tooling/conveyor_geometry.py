#!/usr/bin/env python3
"""Conveyor geometry on ladder replays: death sites vs ally/enemy heads,
eater attribution, bud sizes, queen positions. Usage: conveyor_geometry.py REPLAY..."""
import sys, os, glob
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'handoff', 'tooling'))
import parse_replay
from collections import defaultdict

def cheb(a,b): return max(abs(a[0]-b[0]),abs(a[1]-b[1]))

def analyze(path):
    d = parse_replay.parse(path)
    ev = d['events']
    rnd=0; last={}; team={}; out=[]
    splits=[]; deaths=[]
    for e in ev:
        t=e['type']
        if t=='roundStart': rnd=e['round']
        elif t=='dragonUpdate':
            last[e['id']]={'head':tuple(e['head']),'len':len(e.get('tail',[]))+1,'rnd':rnd}
        elif t=='dragonSplit':
            team[e['childId']]=e['team']
            pl=len(e.get('parentBody',[])); cl=len(e.get('childBody',[]))
            splits.append((rnd,e['team'],pl,cl))
            last[e['childId']]={'head':tuple(e['childBody'][0]) if e.get('childBody') else e.get('head',(0,0)),'len':cl,'rnd':rnd}
        elif t=='dragonDeath':
            deaths.append((rnd,e['id'],e['reason']))
    # queens: ids 0-3, team via r0 splits (parents)
    return {'splits':splits,'deaths':deaths,'last':last,'team':team,'rounds':d.get('rounds',0),'map':d.get('map','?'),'winner':d.get('winner','?')}

all_s=[]; all_d=[]
files=[]
for pat in sys.argv[1:]:
    files += glob.glob(pat) if any(c in pat for c in '*?[') else [pat]
for f in files:
    try: r=analyze(f)
    except Exception as ex:
        print('skip',f,ex); continue
    # per-death geometry: distance victim to nearest ally head at that round.
    # rebuild positions per round is heavy; use last-known within +-3 rounds.
    for (rnd,vid,reason) in r['deaths']:
        v=r['last'].get(vid)
        if not v: continue
        vt=r['team'].get(vid, 'A' if vid%2 else 'B')  # parity fallback for queens
        allies=[(abs(s['rnd']-rnd),cheb(v['head'],s['head']),i) for i,s in r['last'].items()
                if i!=vid and r['team'].get(i,'A' if i%2 else 'B')==vt and s['head']]
        foes=[(abs(s['rnd']-rnd),cheb(v['head'],s['head']),i) for i,s in r['last'].items()
              if r['team'].get(i,'A' if i%2 else 'B')!=vt and s['head']]
        allies=[a for a in allies if a[0]<=3]; foes=[f2 for f2 in foes if f2[0]<=3]
        da=min([a[1] for a in allies]) if allies else 99
        de=min([f2[1] for f2 in foes]) if foes else 99
        all_d.append((reason,v['len'],da,de))
    for (rnd,tm,pl,cl) in r['splits']:
        all_s.append((pl,cl))

import statistics as st
print('deaths:',len(all_d),'splits:',len(all_s))
by=defaultdict(list)
for (reason,l,da,de) in all_d: by[reason].append((l,da,de))
for reason,rows in sorted(by.items()):
    ls=[x[0] for x in rows]; das=[x[1] for x in rows]; des=[x[2] for x in rows]
    print(f'{reason:15s} n={len(rows):4d} len med{st.median(ls):4.0f} dAlly med{st.median(das):4.0f} dFoe med{st.median(des):4.0f} | dAlly<=1: {sum(1 for a in das if a<=1)/len(das):.0%} dAlly<=2: {sum(1 for a in das if a<=2)/len(das):.0%}')
pl=[p for p,c in all_s]; cl=[c for p,c in all_s]
print('split parent len: med',st.median(pl),'p25',sorted(pl)[len(pl)//4],'p75',sorted(pl)[3*len(pl)//4])
print('split child len:  med',st.median(cl),'p25',sorted(cl)[len(cl)//4],'p75',sorted(cl)[3*len(cl)//4])
