"""forage.py — decompose per-unit forage efficiency r0-120, top teams vs us.
Pearl state: beds = TILE lines w/ field3==1; live set starts full;
tileChange{hasPearl} flips; pearlCountdown marks regenerating beds.
Per side per unit-round r0-120:
 (a) cheb head -> nearest live pearl
 (b) fraction with a live pearl within cheb<=3 (vision)
 (c) contested eats: >=2 same-team units had eaten-pearl as nearest
     (prev round, within 6) -> does the loser re-eat within 8r?
 (d) eats where eater was within 2 of the bed BEFORE it spawned
     (pre-positioned) vs arrived after; fresh-respawn beds (<=15r)
Usage: python3 devin/lanes/forage.py
"""
import sys, io, glob, json, contextlib, collections, statistics as st
sys.path.insert(0,'/home/ubuntu/bc/handoff/tooling')
from parse_replay import parse

VIS=3
def cheb(a,b,W,H,wrap):
    dx=abs(a[0]-b[0]); dy=abs(a[1]-b[1])
    if wrap: dx=min(dx,W-dx); dy=min(dy,H-dy)
    return max(dx,dy)
def dims(mt):
    W=H=0; free=set(); beds={}
    for ln in mt.splitlines():
        t=ln.split()
        if not t: continue
        if t[0]=='MAP': W,H=int(t[1]),int(t[2])
        elif t[0]=='TILE':
            x,y=int(t[1]),int(t[2]); free.add((x,y))
            if len(t)>3 and int(t[3])==1: beds[(x,y)]=int(t[4]) if len(t)>4 else 0
    wrap=any((0,y) in free for y in range(H)) and any((W-1,y) in free for y in range(H))
    return W,H,free,beds,wrap

def analyze(path, topparity):
    with contextlib.redirect_stdout(io.StringIO()):
        r=parse(path)
    W,H,free,beds,wrap=dims(r['map'])
    live=set(beds)             # pearls present at start (assume)
    countdown={}               # bed -> last countdown seen
    spawned={}                 # bed -> round it (re)spawned
    rnd=0; cur={}; dead=set()
    stats={s:{'dist':[],'see':0,'ur':0,'eats':[]} for s in ('top','opp')}
    contested=[]               # per eaten pearl: list of loser outcomes
    targeting={}               # id -> pearl cell it is heading for (nearest live)
    last_eat={}                # id -> last round it ate
    pending=set()
    for e in r['events']:
        t=e['type']
        if t=='roundStart':
            rnd+=1
            if rnd>120: break
            if rnd>=1:
                live_l=list(live)
                for i,(h,L) in cur.items():
                    if i in dead: continue
                    side='top' if i%2==topparity else 'opp'
                    S=stats[side]; S['ur']+=1
                    if live_l:
                        np=min(live_l,key=lambda p: cheb(h,p,W,H,wrap))
                        d=cheb(h,np,W,H,wrap); S['dist'].append(d)
                        if d<=VIS: S['see']+=1
                        targeting[i]=np
                    else: targeting.pop(i,None)
        elif t=='pearlCountdown':
            countdown[tuple(e['tile'])]=e['countdown']
        elif t=='tileChange':
            cell=tuple(e['tile'])
            if e['hasPearl']:
                live.add(cell); spawned[cell]=rnd
            elif cell in live:
                live.discard(cell)   # eaten
                # eater: unit on/adjacent cell
                eaters=[i for i,(h,L) in cur.items() if i not in dead and cheb(h,cell,W,H,wrap)<=1]
                if eaters:
                    ei=min(eaters,key=lambda i:cheb(cur[i][0],cell,W,H,wrap))
                    side='top' if ei%2==topparity else 'opp'
                    stats[side]['eats'].append((rnd,ei,cell))
                    last_eat[ei]=rnd
                    # contested: same-team units that also targeted this pearl, within 6
                    losers=[j for j,p in targeting.items() if p==cell and j!=ei
                            and j in cur and j not in dead and j%2==ei%2
                            and cheb(cur[j][0],cell,W,H,wrap)<=6]
                    if losers:
                        contested.append({'side':side,'rnd':rnd,'losers':losers,'cell':cell})
                    # pre-positioned: eater was within 2 BEFORE spawn
                    sp=spawned.get(cell,0)
                    stats[side].setdefault('pre',[]).append((sp, rnd, cheb(cur[ei][0],cell,W,H,wrap)))
        elif t=='dragonUpdate':
            cur[e['id']]=(tuple(e['head']),abs(e['head'][0]-e['tail'][0])+abs(e['head'][1]-e['tail'][1])+1)
        elif t=='dragonSplit':
            if e['childBody']: cur[e['childId']]=(tuple(e['childBody'][0]),len(e['childBody']))
            if e['parentBody']: cur[e['parentId']]=(tuple(e['parentBody'][0]),len(e['parentBody']))
        elif t=='dragonDeath':
            dead.add(e['id']); targeting.pop(e['id'],None)
    # contested outcomes: did loser eat within 8r after the contest?
    cont_out={s:{'re':0,'no':0,'n':0} for s in ('top','opp')}
    for c in contested:
        for j in c['losers']:
            le=last_eat.get(j)
            ok = le is not None and c['rnd'] < le <= c['rnd']+8
            cont_out[c['side']]['re' if ok else 'no']+=1; cont_out[c['side']]['n']+=1
    # pre-positioned metric: eat on a bed that spawned <=15r ago AND eater was on it at spawn
    return stats,cont_out

files=sorted(glob.glob('/home/ubuntu/bc/ladder_top/*.replay'))
seats=json.load(open('/home/ubuntu/bc/ladder_top/seats.json'))
files2=sorted(glob.glob('/home/ubuntu/bc/ladder_replays129/*.replay'))
seats2=json.load(open('/home/ubuntu/bc/ladder_replays129/seats.json'))

agg=collections.defaultdict(lambda:{'dist':[],'see':0,'ur':0,'eats':0,'units':set(),'cont':{'re':0,'no':0,'n':0},'fresh':0,'stale':0,'pre':0,'post':0,'ngames':0})
for f in files:
    mid=f.split('/')[-1].split('.')[0][1:]
    if mid not in seats: continue
    topseat=seats[mid][0]; tp=0 if topseat=='A' else 1
    st_,co=analyze(f,tp)
    for s in ('top','opp'):
        A=agg['top' if s=='top' else 'topopp']
        A['dist']+=st_[s]['dist']; A['see']+=st_[s]['see']; A['ur']+=st_[s]['ur']
        A['eats']+=len(st_[s]['eats'])
        for _,_,c in st_[s]['eats']: A['units'].add(c)
        for k in ('re','no','n'): A['cont'][k]+=co[s][k]
        for sp,rd,dd in st_[s].get('pre',[]):
            if rd-sp<=15 and dd<=1: A['pre']+=1
            else: A['post']+=1
            if rd-sp<=15: A['fresh']+=1
            else: A['stale']+=1
    agg['top']['ngames']+=1
for f in files2:
    mid=f.split('/')[-1].split('.')[0][1:]
    if mid not in seats2: continue
    us=seats2[mid][0]; tp=0 if us=='A' else 1  # 'top' slot = us
    st_,co=analyze(f,tp)
    A=agg['us']
    A['dist']+=st_['top']['dist']; A['see']+=st_['top']['see']; A['ur']+=st_['top']['ur']
    A['eats']+=len(st_['top']['eats'])
    for _,_,c in st_['top']['eats']: A['units'].add(c)
    for k in ('re','no','n'): A['cont'][k]+=co['top'][k]
    for sp,rd,dd in st_['top'].get('pre',[]):
        if rd-sp<=15 and dd<=1: A['pre']+=1
        else: A['post']+=1
        if rd-sp<=15: A['fresh']+=1
        else: A['stale']+=1
    A['ngames']+=1

print(f"{'side':8}{'unitR':>7}{'eats':>6}{'e/u':>6}{'medD':>6}{'see%':>6}{'cont_n':>7}{'re8r%':>6}{'fresh%':>7}{'pre%':>6}")
for lab,k in (('top-5','top'),('top-opp','topopp'),('US','us')):
    A=agg[k]
    med=st.median(A['dist']) if A['dist'] else 0
    epu=A['eats']/max(A['ur'],1)*100
    see=100*A['see']/max(A['ur'],1)
    re8=100*A['cont']['re']/max(A['cont']['n'],1)
    fresh=100*A['fresh']/max(A['fresh']+A['stale'],1)
    pre=100*A['pre']/max(A['pre']+A['post'],1)
    print(f"{lab:8}{A['ur']:>7}{A['eats']:>6}{epu:>6.1f}{med:>6.1f}{see:>6.0f}{A['cont']['n']:>7}{re8:>6.0f}{fresh:>7.0f}{pre:>6.0f}")
print("\ngames:",{k:v['ngames'] for k,v in agg.items()})
print("contested breakdown:", {k:v['cont'] for k,v in agg.items()})
