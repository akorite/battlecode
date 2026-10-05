#!/usr/bin/env python3
"""Spawn-position forensics: for each dragonSplit, record parent/child
geometry and the child's later survival; split by side (ours=loser A,
theirs=winner B in our loss replays)."""
import sys, json, gzip, io, contextlib, glob
from collections import deque, defaultdict
sys.path.insert(0, 'handoff/tooling')
from parse_replay import parse

MAPDIR='engine/maps/'
MAPBYNAME={}
def loadmap(name):
    if name in MAPBYNAME: return MAPBYNAME[name]
    import os
    for f in os.listdir(MAPDIR):
        if not f.endswith('.map'): continue
        for ln in open(MAPDIR+f):
            if ln.startswith('MAP_NAME'):
                MAPBYNAME[ln.split(None,1)[1].strip()] = MAPDIR+f
                break
    return MAPBYNAME.get(name)

def grid(path):
    W=H=None; free=set()
    for ln in open(path):
        p=ln.split()
        if not p: continue
        if p[0]=='MAP': W,H=int(p[1]),int(p[2])
        elif p[0]=='TILE': free.add((int(p[1]),int(p[2])))
    return W,H,free

def bfs_multi(free, W, H, starts, targets):
    """dist from nearest start cell to each target cell; wrap torus."""
    INF=10**9; dist={s:0 for s in starts}
    dq=deque(starts)
    found={}
    while dq:
        c=dq.popleft(); d=dist[c]
        if c in targets: found[c]=d
        if len(found)==len(targets): break
        x,y=c
        for nx,ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
            nc=(nx%W,ny%H)
            if nc not in free or nc in dist: continue
            dist[nc]=d+1; dq.append(nc)
    return {t:found.get(t,INF) for t in targets}

def analyze(path):
    buf=io.StringIO()
    with contextlib.redirect_stdout(buf):
        try: p=parse(path)
        except Exception as e: return None,str(e)
    W=H=None; free=set(); name='?'
    for ln in p['map'].splitlines():
        q=ln.split()
        if not q: continue
        if q[0]=='MAP': W,H=int(q[1]),int(q[2])
        elif q[0]=='MAP_NAME': name=ln.split(None,1)[1].strip()
        elif q[0]=='TILE': free.add((int(q[1]),int(q[2])))
    if W is None: return None,'nomap'
    rnd=0; heads={}; lens={}; deaths={}; end=0
    splits=[]  # (round,team,parentId,childId,parentHead,childHead,childLen)
    updates={} # id->round of last update (idle dragons skip turns)
    for e in p['events']:
        t=e['type']
        if t=='roundStart': rnd=e['round']; end=rnd
        elif t=='dragonUpdate':
            heads[e['id']]=tuple(e['head'])
            lens[e['id']]=abs(e['head'][0]-e['tail'][0])+abs(e['head'][1]-e['tail'][1])+1
            updates[e['id']]=rnd
        elif t=='dragonDeath': deaths[e['id']]=(rnd,e['reason'])
        elif t=='dragonSplit':
            ph=tuple(e['parentBody'][0]) if e['parentBody'] else None
            ch=tuple(e['childBody'][0]) if e['childBody'] else None
            splits.append((rnd,e['team'],e['parentId'],e['childId'],ph,ch,len(e['childBody'])))
            if ch:
                heads[e['childId']]=ch; lens[e['childId']]=len(e['childBody']); updates[e['childId']]=rnd
            if ph:
                heads[e['parentId']]=ph
    # per-split metrics using positions as of the split round — need a re-walk
    # snapshot approach: track state up to each split in event order.
    rows=[]
    heads={}; lens={}; dead=set(); rnd=0
    si=0
    for e in p['events']:
        t=e['type']
        if t=='roundStart': rnd=e['round']
        elif t=='dragonUpdate':
            heads[e['id']]=tuple(e['head'])
            lens[e['id']]=abs(e['head'][0]-e['tail'][0])+abs(e['head'][1]-e['tail'][1])+1
        elif t=='dragonDeath': dead.add(e['id'])
        elif t=='dragonSplit':
            team=e['team']; pid=e['parentId']; cid=e['childId']
            ph=tuple(e['parentBody'][0]) if e['parentBody'] else heads.get(pid)
            ch=tuple(e['childBody'][0]) if e['childBody'] else None
            enemy='B' if team=='A' else 'A'
            own_heads=[h for i,h in heads.items() if i%2==(0 if team=='A' else 1) and i not in dead]
            en_heads=[h for i,h in heads.items() if i%2==(0 if enemy=='A' else 1) and i not in dead]
            d_enemy=None; d_cen=None; own_near4=0; d_parent=None
            if ch:
                if en_heads:
                    dm=bfs_multi(free,W,H,set(en_heads),{ch}); d_enemy=dm[ch]
                if own_heads:
                    cx=sum(h[0] for h in own_heads)/len(own_heads)
                    cy=sum(h[1] for h in own_heads)/len(own_heads)
                    # torus-aware centroid distance ~ manhattan on wrapped axes
                    dx=min(abs(ch[0]-cx), W-abs(ch[0]-cx)); dy=min(abs(ch[1]-cy), H-abs(ch[1]-cy))
                    d_cen=dx+dy
                    for h in own_heads:
                        dx=min(abs(ch[0]-h[0]),W-abs(ch[0]-h[0])); dy=min(abs(ch[1]-h[1]),H-abs(ch[1]-h[1]))
                        if dx+dy<=4: own_near4+=1
                if ph:
                    dx=min(abs(ch[0]-ph[0]),W-abs(ch[0]-ph[0])); dy=min(abs(ch[1]-ph[1]),H-abs(ch[1]-ph[1]))
                    d_parent=dx+dy
            life=(deaths.get(cid,(end+1,'alive'))[0]-rnd)
            rows.append({'round':rnd,'team':team,'pid':pid,'cid':cid,'clen':len(e['childBody']),
                'plen':lens.get(pid),'d_enemy':d_enemy,'d_cen':d_cen,'own_near4':own_near4,
                'd_parent':d_parent,'life':life,
                'death':deaths.get(cid,(None,'alive'))[1]})
            if ch: heads[cid]=ch; lens[cid]=len(e['childBody'])
            if ph: heads[pid]=ph
    return {'map':name,'winner':p['result']['winner'] if p['result'] else None,
            'end':p['result']['endReason'] if p['result'] else None,'rows':rows},None

out=[]
files=sorted(glob.glob('ladder_replays/*.replay')+glob.glob('pdtd_replays/*.replay'))
for f in files:
    r,err=analyze(f)
    if r is None: print('SKIP',f,err,file=sys.stderr); continue
    out.append(r)
    print(f, r['map'], 'winner',r['winner'],'splits',len(r['rows']),file=sys.stderr)
json.dump(out,open('/tmp/spawndiag.json','w'))
print('WROTE',len(out),'games')
