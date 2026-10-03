"""Offline map features (the same signals the bot can measure in game) for every map file."""
import sys, glob, os, collections
def parse(path):
    W=H=0; edges={}; tiles={}; dr=[]
    for line in open(path):
        p=line.split()
        if not p: continue
        if p[0]=='MAP': W,H=int(p[1]),int(p[2])
        elif p[0]=='TILE': tiles[(int(p[1]),int(p[2]))]=(int(p[3]),int(p[4]))
        elif p[0]=='EDGE': edges[int(p[1])]=(int(p[2]),int(p[3]))
        elif p[0]=='DRAGON':
            t,n=int(p[1]),int(p[2]); xs=list(map(int,p[3:3+2*n])); dr.append((t,list(zip(xs[::2],xs[1::2]))))
    return W,H,edges,tiles,dr
def graph(W,H,edges):
    def ek(i): return edges.get(i,(0,-1))
    # portals: pair ends by id -> treat as walls here but count them
    nb=collections.defaultdict(list)
    portals=0
    for y in range(H):
        for x in range(W):
            # north edge of (x,y): index 2y*(W+1)+x ; west edge: (2y+1)*(W+1)+x
            k,_=ek(2*y*(W+1)+x)
            if k==0: a=(x,y); b=(x,(y-1)%H); nb[a].append(b); nb[b].append(a)
            elif k==2: portals+=1
            k,_=ek((2*y+1)*(W+1)+x)
            if k==0: a=(x,y); b=((x-1)%W,y); nb[a].append(b); nb[b].append(a)
            elif k==2: portals+=1
    return nb,portals
def bfs(nb,src):
    d={src:0}; q=[src]
    for c in q:
        for n in nb[c]:
            if n not in d: d[n]=d[c]+1; q.append(n)
    return d
def core2(nb,cells):
    deg={c:len(set(nb[c])) for c in cells}; alive=set(cells); q=[c for c in cells if deg[c]<=1]
    while q:
        c=q.pop()
        if c not in alive: continue
        alive.discard(c)
        for n in set(nb[c]):
            if n in alive:
                deg[n]-=1
                if deg[n]<=1: q.append(n)
    return alive
def feats(path):
    W,H,edges,tiles,dr=parse(path)
    nb,portals=graph(W,H,edges)
    cells=[(x,y) for y in range(H) for x in range(W)]
    kelp=sum(1 for v in edges.values() if v[0]==1)
    qa,qb=dr[0][1][0],dr[1][1][0]
    da=bfs(nb,qa)
    region=len(da)
    # cage: region reachable by our queen within 7x7 of her start
    qd=da.get(qb,-1)
    cheb=max(min(abs(qa[0]-qb[0]),W-abs(qa[0]-qb[0])),min(abs(qa[1]-qb[1]),H-abs(qa[1]-qb[1])))
    rate=sum(2.0/(a+b) for (a,b) in tiles.values() if b>0)
    fount=sum(1 for (a,b) in tiles.values() if 0<b<=2)
    core=core2(nb,cells)
    # local 7x7 openness around queen start: tiles reachable from qa within the 7x7 box
    box=set((((qa[0]+dx)%W),((qa[1]+dy)%H)) for dx in range(-3,4) for dy in range(-3,4))
    d=[qa];seen={qa}
    for c in d:
        for n in nb[c]:
            if n in box and n not in seen: seen.add(n); d.append(n)
    return dict(map=os.path.basename(path)[:-4],W=W,H=H,area=W*H,start=len(dr)//2,
        qlen=len(dr[0][1]),region=region,qbox=len(seen),qdist=qd,qcheb=cheb,
        kelpfrac=round(kelp/(2*W*H),3),portals=portals,
        rate=round(rate,2),rate_per100=round(100*rate/(W*H),2),fount=fount,
        deadend=round(1-len(core)/len(cells),3))
if __name__=='__main__':
    rows=[feats(p) for p in sorted(glob.glob(os.path.expanduser(sys.argv[1] if len(sys.argv)>1 else '~/maps-all')+'/*.map'))]
    ks=list(rows[0])
    print(' '.join(f'{k:>9}' for k in ks))
    for r in sorted(rows,key=lambda r:r['area']): print(' '.join(f'{str(r[k]):>9}' for k in ks))
