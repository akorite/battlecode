"""Contested-starvation forensics: how 1700+ winners out-eat us in
contested zones. Per side per game:
  eff120: eaten pearls r0-120 / unit-rounds alive r0-120 (+ eaten120)
  contested eats: eat where enemy head within cheb-3 of cell at eat round
  steals: eat where enemy was closer-or-equal the round before (we
          reached into their claim)
  drop recycling: same-team death drop eaten <=5r by own side; and the
          share of those re-eats that happened in the contest zone
          (enemy head <=4 of cell at re-eat round)
  contest density: mean friendly heads within cheb-4 of the eat cell at
          eat round, split contested/uncontested
  splits r0-120, alive at 30/60/120
Us vs them resolved by caller passing our side letter.
"""
import sys, os, glob, json, collections
sys.path.insert(0, '/home/ubuntu/bc/handoff/tooling')
from parse_replay import parse
from pocket_metric import parse_map

def tc(W,H,a,b):
    dx=min(abs(a[0]-b[0]),W-abs(a[0]-b[0]));dy=min(abs(a[1]-b[1]),H-abs(a[1]-b[1]));return max(dx,dy)

def analyze(path):
    r=parse(path); W,H,dr,_=parse_map(r['map'])
    team={i:'AB'[t] for i,(t,_b) in enumerate(dr)}
    heads_hist=collections.defaultdict(dict); body={};born={};died={}
    rnd=0;maxr=0
    pearl_evs=[]
    splits=collections.Counter()
    for e in r['events']:
        ty=e['type']
        if ty=='roundStart':rnd+=1;maxr=rnd
        elif ty=='tileChange' and 'hasPearl' in e:
            pearl_evs.append((rnd,tuple(e['tile']),e['hasPearl']))
        elif ty=='dragonUpdate':
            i=e['id'];b=body.setdefault(i,collections.deque())
            h,tl=tuple(e['head']),tuple(e['tail'])
            if not b:
                if h[0]==tl[0] or h[1]==tl[1]:
                    x,y=tl;hx,hy=h;sx=(hx>x)-(hx<x);sy=(hy>y)-(hy<y)
                    while (x,y)!=(hx,hy):b.append((x,y));x+=sx;y+=sy
                    b.append((hx,hy));b.reverse()
                else:b.append(h)
            else:
                if b[0]!=h:b.appendleft(h)
                while len(b)>1 and b[-1]!=tl:b.pop()
            heads_hist[i][rnd]=h;born.setdefault(i,1)
        elif ty=='dragonSplit':
            team[e['childId']]=e['team'];born[e['childId']]=rnd;splits[(e['team'],rnd)]+=1
            body[e['parentId']]=collections.deque(tuple(x) for x in e['parentBody'])
            body[e['childId']]=collections.deque(tuple(x) for x in e['childBody'])
            heads_hist[e['parentId']][rnd]=tuple(e['parentBody'][0])
            heads_hist[e['childId']][rnd]=tuple(e['childBody'][0])
        elif ty=='dragonDeath':died[e['id']]=rnd
    harr={}
    for i,hh in heads_hist.items():
        arr=[None]*(maxr+1);last=None
        for rr in range(maxr+1):
            if rr in hh:last=hh[rr]
            arr[rr]=last
        harr[i]=arr
    def alive(i,rr):return born.get(i,1<<30)<=rr<died.get(i,1<<30)
    # per-side unit-rounds + alive marks
    ur120=collections.Counter();al=collections.defaultdict(collections.Counter)
    for i in harr:
        s=team.get(i)
        for rr in range(1,min(121,maxr+1)):
            if alive(i,rr):ur120[s]+=1
        for mark in (30,60,120):
            if mark<=maxr and alive(i,mark):al[s][mark]+=1
    # pearl removals -> eater attribution (nearest alive head d<=1)
    rem=[(rr,c) for rr,c,v in pearl_evs if not v]
    addl=collections.defaultdict(list)
    for rr,c,v in pearl_evs:
        if v:addl[c].append(rr)
    st=collections.defaultdict(collections.Counter)
    eat_cells=collections.defaultdict(list)
    for rr,c in rem:
        best=None;bd=99;bd2=99
        for i in harr:
            if not alive(i,rr):continue
            h=harr[i][rr]
            if not h:continue
            d=tc(W,H,h,c)
            if d<bd:bd=d;best=i
        if bd>1 or best is None:continue
        s=team[best];eat_cells[s].append((rr,c))
        st[s]['eats']+=1
        if rr<=120:st[s]['eats120']+=1
        # contested: enemy head within cheb-3 at eat round
        eside='B' if s=='A' else 'A'
        en=min((tc(W,H,harr[j][rr],c) for j in harr if j!=best and team.get(j)==eside and alive(j,rr) and harr[j][rr]),default=99)
        al_=min((tc(W,H,harr[j][rr],c) for j in harr if j!=best and team.get(j)==s and alive(j,rr) and harr[j][rr]),default=99)
        allyD=sum(1 for j in harr if j!=best and team.get(j)==s and alive(j,rr) and harr[j][rr] and tc(W,H,harr[j][rr],c)<=4)
        enemD=sum(1 for j in harr if team.get(j)==eside and alive(j,rr) and harr[j][rr] and tc(W,H,harr[j][rr],c)<=4)
        if en<=3:
            st[s]['contested']+=1
            st[s]['con_density']+=allyD;st[s]['con_edensity']+=enemD;st[s]['con_n']+=1
            # steal: enemy equidistant-or-closer previous round
            enp=min((tc(W,H,harr[j][rr-1],c) for j in harr if team.get(j)==eside and alive(j,rr-1) and harr[j][rr-1]),default=99) if rr>0 else 99
            myp=tc(W,H,harr[best][rr-1],c) if harr[best][rr-1] else 99
            if enp<=myp:st[s]['steals']+=1
        else:
            st[s]['free_density']+=allyD;st[s]['free_n']+=1
        if en<=4:st[s]['zone_eats']+=1
    # drop recycling (same-team death drop -> same-team eat <=5r)
    # deaths per id: need dead head cell; reuse heads_hist tail? approximate with last harr pos
    drops=collections.defaultdict(lambda:{'tot':0,'rec5':0,'zone':0})
    rem_at=collections.defaultdict(set)
    for rr,c in rem:rem_at[c].add(rr)
    for i,dd in died.items():
        s=team.get(i);h=harr[i][dd] if dd<len(harr[i]) else None
        if not h:continue
        # drop cells: adds at dd..dd+1 within cheb-2 of death head (drop-recycle def)
        for rr2,c,v in pearl_evs:
            if v and dd<=rr2<=dd+1 and tc(W,H,h,c)<=2:
                drops[s]['tot']+=1
                rr3=next((x for x in sorted(rem_at.get(c,())) if x>rr2),None)
                if rr3 is not None and rr3-rr2<=5:
                    # eaten by own side? eater at rr3
                    best=None;bd=99
                    for j in harr:
                        if not alive(j,rr3):continue
                        hj=harr[j][rr3]
                        if not hj:continue
                        d=tc(W,H,hj,c)
                        if d<bd:bd=d;best=j
                    if best is not None and bd<=1 and team[best]==s:
                        drops[s]['rec5']+=1
                        eside='B' if s=='A' else 'A'
                        en=min((tc(W,H,harr[j][rr3],c) for j in harr if team.get(j)==eside and alive(j,rr3) and harr[j][rr3]),default=99)
                        if en<=4:drops[s]['zone']+=1
    out={}
    for s in 'AB':
        d=st[s];o={}
        o['eats']=d['eats'];o['eats120']=d['eats120']
        o['ur120']=ur120[s]
        o['eff120']=d['eats120']/ur120[s] if ur120[s] else 0
        o['contested']=d['contested'];o['steals']=d['steals']
        o['zone_eats']=d['zone_eats']
        o['con_density']=d['con_density']/d['con_n'] if d['con_n'] else 0
        o['con_edensity']=d['con_edensity']/d['con_n'] if d['con_n'] else 0
        o['free_density']=d['free_density']/d['free_n'] if d['free_n'] else 0
        o['split120']=sum(v for (t,rr),v in splits.items() if t==s and rr<=120)
        o['alive30']=al[s][30];o['alive60']=al[s][60];o['alive120']=al[s][120]
        o['drops']=drops[s]['tot'];o['rec5']=drops[s]['rec5'];o['rec_zone']=drops[s]['zone']
        o['maxr']=maxr
        out[s]=o
    res=r.get('result') or {}
    return out,res.get('winner'),res.get('teamA',{}),res.get('teamB',{}),os.path.basename(path)

if __name__=='__main__':
    pass
