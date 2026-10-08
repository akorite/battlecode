"""prodcad.py — production cadence forensics: top-8 vs us.
seats2.json: {mid: [flag, seat, name, elo, opp, opp_elo]} flag T=top team, U=us.
Per split event: parent id, round, child len, child spawn cell, map.
Metrics:
 (1) parent regrowth: rounds until SAME parent splits again, median
     by era r0-120/120-300/300+
 (2) child len at birth dist + child's delay to ITS first split
 (3) split location: cheb distance from the child's spawn cell to the
     parent's OWN spawn cell (its r0 position or birth cell) and to the
     team's centroid; "territory depth" = cheb to nearest enemy head
 (4) alive unit count per 50r bucket + saturation round (>=90% of peak)
Usage: python3 devin/lanes/prodcad.py
"""
import sys, io, glob, json, contextlib, collections, statistics as st
sys.path.insert(0,'/home/ubuntu/bc/handoff/tooling')
from parse_replay import parse

def cheb(a,b,W,H,wrap):
    dx=abs(a[0]-b[0]); dy=abs(a[1]-b[1])
    if wrap: dx=min(dx,W-dx); dy=min(dy,H-dy)
    return max(dx,dy)
def dims(mt):
    W=H=0; free=set()
    for ln in mt.splitlines():
        t=ln.split()
        if not t: continue
        if t[0]=='MAP': W,H=int(t[1]),int(t[2])
        elif t[0]=='TILE': free.add((int(t[1]),int(t[2])))
    wrap=any((0,y) in free for y in range(H)) and any((W-1,y) in free for y in range(H))
    return W,H,wrap

def era(r): return 0 if r<=120 else (1 if r<=300 else 2)

def analyze(path, topparity):
    with contextlib.redirect_stdout(io.StringIO()):
        r=parse(path)
    W,H,wrap=dims(r['map'])
    rnd=0; cur={}; dead=set(); born={}  # id->birth round, birth cell
    last_split={}   # parent id -> last split round
    first_parent={} # id -> first round it parented
    resplit={0:[],1:[],2:[]}  # era -> intervals
    childlen=[]; firstsplit=[]  # child len at birth; delay to first split of a child
    loc=[]          # (d_spawn, d_cen, d_enemy)
    alive=collections.defaultdict(lambda: collections.Counter())
    side=lambda i:'top' if i%2==topparity else 'opp'
    for e in r['events']:
        t=e['type']
        if t=='roundStart':
            rnd+=1
            for i,(h,L) in cur.items():
                if i not in dead: alive[side(i)][rnd//50]+=1
        elif t=='dragonUpdate':
            cur[e['id']]=(tuple(e['head']),abs(e['head'][0]-e['tail'][0])+abs(e['head'][1]-e['tail'][1])+1)
            born.setdefault(e['id'],(rnd,cur[e['id']][0]))
        elif t=='dragonSplit':
            pid,cid=e['parentId'],e['childId']
            tm=0 if e['team']=='A' else 1
            s='top' if tm==topparity else 'opp'
            if pid in last_split and rnd>0:
                resplit[era(rnd)].append((s,rnd-last_split[pid]))
            last_split[pid]=rnd
            clen=len(e['childBody'])
            if e['childBody']:
                ch=tuple(e['childBody'][0])
                cur[cid]=(ch,clen); born[cid]=(rnd,ch)
                childlen.append((s,clen,rnd))
            if e['parentBody']: cur[pid]=(tuple(e['parentBody'][0]),len(e['parentBody']))
            # first split of this child later — recorded via born+last_split
            # location: dist from birth cell + centroid + enemy
            if e['childBody']:
                mates=[v[0] for j,v in cur.items() if j%2==tm and j not in dead]
                enes=[v[0] for j,v in cur.items() if j%2!=tm and j not in dead]
                bc=born.get(pid,(None,None))[1] or (e['parentBody'] and tuple(e['parentBody'][-1]))
                cx=sum(x[0] for x in mates)/len(mates) if mates else ch[0]
                cy=sum(x[1] for x in mates)/len(mates) if mates else ch[1]
                den=min((cheb(ch,x,W,H,wrap) for x in enes),default=None)
                loc.append((s,cheb(ch,bc,W,H,wrap) if bc else None,
                            cheb(ch,(round(cx),round(cy)),W,H,wrap),den,rnd))
        elif t=='dragonDeath':
            dead.add(e['id'])
    # child first-split delay: children that later appear as parents
    # approximate: a child splits first time when its id becomes a parent
    # we see it in last_split — compute born->first-split
    # (re-scan: need first split per id)
    return resplit,childlen,loc,alive,born,firstsplit

def run(files,seats,label):
    R=collections.defaultdict(list); CL=collections.defaultdict(list)
    LOC=collections.defaultdict(list); AL=collections.defaultdict(lambda: collections.defaultdict(int))
    FS=collections.defaultdict(list)
    ng=0
    for f in files:
        mid=f.split('/')[-1].split('.')[0][1:]
        if mid not in seats: continue
        flag,seat,name,elo,opp,oelo=seats[mid]
        tp=0 if seat=='A' else 1
        try:
            resplit,childlen,loc,alive,born,firstsplit=analyze(f,tp)
        except Exception as ex:
            print(f,'ERR',ex,file=sys.stderr); continue
        ng+=1
        for e_,xs in resplit.items():
            for s,v in xs: R[(s,e_)].append(v)
        for s,cl,rnd in childlen: CL[s].append(cl)
        for s,a,b,c,rnd in loc: LOC[s].append((a,b,c))
        for s,d in firstsplit: FS[s].append(d)
        for s,buckets in alive.items():
            for b,n in buckets.items(): AL[s][b]+=n
    print(f"\n########## {label} ({ng} games) ##########")
    for s in ('top','opp'):
        if not CL[s]: continue
        print(f"[{s}]")
        for e_ in range(3):
            xs=R[(s,e_)]
            if xs: print(f"  parent resplit era{e_}: n={len(xs)} median {st.median(xs):.0f} mean {st.mean(xs):.1f} p25 {sorted(xs)[len(xs)//4]} p75 {sorted(xs)[3*len(xs)//4]}")
        print(f"  child len dist: {dict(sorted(collections.Counter(CL[s]).items()))}")
        if FS[s]:
            xs=sorted(FS[s]); print(f"  child->first-split delay: n={len(xs)} median {st.median(xs):.0f} mean {st.mean(xs):.1f} p25 {xs[len(xs)//4]}")
        for idx,lab in ((0,'d_parentbirth'),(1,'d_centroid'),(2,'d_enemy')):
            xs=[x[idx] for x in LOC[s] if x[idx] is not None]
            if xs: print(f"  {lab}: median {st.median(xs):.1f} mean {st.mean(xs):.1f}")
        pk=max(AL[s].values()) if AL[s] else 1
        sat=min((b for b in sorted(AL[s]) if AL[s][b]>=0.9*pk),default=None)
        print(f"  alive/50r-bucket sums: {dict(sorted(AL[s].items()))} peak {pk} sat@{sat}")

run(sorted(glob.glob('/home/ubuntu/bc/ladder_top/*.replay')),
    json.load(open('/home/ubuntu/bc/ladder_top/seats2.json')),'TOP-8 replays')
run(sorted(glob.glob('/home/ubuntu/bc/ladder_us424/*.replay')),
    json.load(open('/home/ubuntu/bc/ladder_top/seats2.json')),'OUR v424 ladder')
