#!/usr/bin/env python3
"""Aggregate sprej census: sum the LAST dump per dragon id per game side."""
import sys,glob,io,contextlib,json
sys.path.insert(0,'handoff/tooling')
from parse_replay import parse
WHY=["ok","unitLimit","bodyUnknown","eat","fight","hunt","feed","hideLen",
     "late","queenBud","keepFloor","len","lateRebuild","enemyNear","roomyP","roomyC"]
import os
os.makedirs('/tmp/sprej',exist_ok=True)
for f in sorted(glob.glob('results/v237sp_census/replays/*.replay')):
    nm=f.split('/')[-1][:-7]; a,b=nm.split('-')[-2:]
    candA='v237sp' in a
    buf=io.StringIO()
    with contextlib.redirect_stdout(buf):
        try: p=parse(f)
        except Exception as e: print('ERR',nm,e); continue
    last={}
    for e in p['events']:
        if e['type']=='dragonLog' and e['text'].startswith('sprej'):
            last[e['id']]=[int(x) for x in e['text'].split()[1:]]
    tot=[0]*16
    for i,c in last.items():
        for j in range(16): tot[j]+=c[j]
    mapn=nm.rsplit('-',2)[0]
    w=p['result']['winner']
    print(f"{mapn:>14} cand={'A' if candA else 'B'} w={w} dragons={len(last)} | " +
          " ".join(f"{WHY[i]}={tot[i]}" for i in range(16) if tot[i]))
