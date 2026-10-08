import sys,os,glob,json,collections
sys.path.insert(0,'/home/ubuntu/bc/handoff/tooling')
from pawn_donation import analyze
tot=collections.Counter(); alivebins=collections.Counter(); alivebase=collections.Counter()
files=sorted(glob.glob('/home/ubuntu/bc/ciallo_replays/*.replay'))+sorted(glob.glob('/home/ubuntu/bc/cursey_replays/*.replay'))
import pawn_donation as P
for f in files:
    r=None
    pd,mx=P.analyze(f)
    # engine check + alive bins
    for d in pd:
        for c in d['drops']: pass
    for d in pd:
        tag=d['tag']
        if d['len']==2:
            b=min(d['alive'],400)
            alivebins[tag][b//50*50]+=1
    all_d=pd
for tag in ('win','lose'):
    print(tag, 'pawn alive bins:', dict(sorted(alivebins[tag].items())))
