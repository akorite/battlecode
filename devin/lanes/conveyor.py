"""conveyor.py — r0-99 conveyor-death forensics, us vs top teams.
Corpus: ladder_replays129/*.replay + seats.json {mid: [seat,opp,elo]}.
Conveyor reasons: noValidAction, hitSelf, hitOtherBody.
Per conveyor death <=r99: victim len, d to nearest ally head, eaters
(allies head within cheb-2 of death cell) — queen? longest?; feeder
location = dist to own queen head(s) and own longest head and own
centroid. Plus conveyor share of all deaths per round bucket.
Usage: python3 devin/lanes/conveyor.py
"""
import sys, io, glob, json, contextlib, collections, statistics as st
sys.path.insert(0, '/home/ubuntu/bc/handoff/tooling')
from parse_replay import parse

CONV={'noValidAction','hitSelf','hitOtherBody'}
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
    return W,H,free,wrap

seats=json.load(open('/home/ubuntu/bc/ladder_replays129/seats.json'))
rows=[]; shares=collections.defaultdict(lambda: collections.Counter())
for f in sorted(glob.glob('/home/ubuntu/bc/ladder_replays129/*.replay')):
    mid=f.split('/')[-1].split('.')[0][1:]
    if mid not in seats: continue
    ourseat,opp,elo=seats[mid]
    with contextlib.redirect_stdout(io.StringIO()):
        r=parse(f)
    W,H,free,wrap=dims(r['map'])
    ourparity=0 if ourseat=='A' else 1
    rnd=0; cur={}; dead=set()
    for e in r['events']:
        t=e['type']
        if t=='roundStart': rnd+=1
        elif t=='dragonUpdate':
            cur[e['id']]=(tuple(e['head']),abs(e['head'][0]-e['tail'][0])+abs(e['head'][1]-e['tail'][1])+1)
        elif t=='dragonSplit':
            if e['childBody']: cur[e['childId']]=(tuple(e['childBody'][0]),len(e['childBody']))
            if e['parentBody']: cur[e['parentId']]=(tuple(e['parentBody'][0]),len(e['parentBody']))
        elif t=='dragonDeath':
            i=e['id']; side='us' if i%2==ourparity else 'them'
            bucket=min(rnd//25,99)
            shares[side][(bucket,'conv' if e['reason'] in CONV else 'other')]+=1
            if rnd<=99 and i in cur:
                h,L=cur[i]
                mates=[(j,v) for j,v in cur.items() if j%2==i%2 and j!=i and j not in dead]
                qids={0,2} if i%2==0 else {1,3}
                queens=[(j,v) for j,v in mates if j in qids]
                longest_j,longest_v=max(mates,key=lambda x:x[1][1],default=(None,(None,0)))
                d_ally=min((cheb(h,v[0],W,H,wrap) for j,v in mates),default=None)
                eaters=[j for j,v in mates if cheb(h,v[0],W,H,wrap)<=2]
                d_q=min((cheb(h,v[0],W,H,wrap) for j,v in queens),default=None)
                d_long=cheb(h,longest_v[0],W,H,wrap) if longest_v[0] else None
                cx=sum(v[0][0] for j,v in mates)/len(mates) if mates else None
                cy=sum(v[0][1] for j,v in mates)/len(mates) if mates else None
                d_cen=cheb(h,(round(cx),round(cy)),W,H,wrap) if cx is not None else None
                rows.append({'side':side,'r':rnd,'reason':e['reason'],'len':L,
                             'd_ally':d_ally,'n_eat':len(eaters),
                             'eat_queen':any(j in qids for j in eaters),
                             'eat_long':longest_j in eaters,
                             'd_q':d_q,'d_long':d_long,'d_cen':d_cen})
            dead.add(i)

def report(side):
    conv=[r for r in rows if r['side']==side and r['reason'] in CONV]
    allr=[r for r in rows if r['side']==side]
    print(f"\n===== {side} (r0-99): {len(allr)} deaths, {len(conv)} conveyor ({100*len(conv)/max(len(allr),1):.0f}%) =====")
    print("len histogram (conveyor):", dict(sorted(collections.Counter(r['len'] for r in conv).items())))
    print("len histogram (all):     ", dict(sorted(collections.Counter(r['len'] for r in allr).items())))
    al=[r['d_ally'] for r in conv if r['d_ally'] is not None]
    print(f"d_ally: median {st.median(al)} mean {st.mean(al):.2f} | <=2 {100*sum(1 for x in al if x<=2)/len(al):.0f}%")
    ne=[r['n_eat'] for r in conv]
    print(f"eaters within 2: mean {st.mean(ne):.2f} | >=1: {100*sum(1 for x in ne if x>=1)/len(ne):.0f}% | queen ate: {100*sum(1 for r in conv if r['eat_queen'])/len(conv):.0f}% | longest ate: {100*sum(1 for r in conv if r['eat_long'])/len(conv):.0f}%")
    for k in ('d_q','d_long','d_cen'):
        xs=[r[k] for r in conv if r[k] is not None]
        if xs: print(f"{k}: median {st.median(xs)} mean {st.mean(xs):.1f}")
report('them'); report('us')

print("\n===== conveyor share of deaths per 25r bucket =====")
for b in sorted({b for s in shares.values() for b,_ in s}):
    line=f"r{b*25}-{b*25+24}: "
    for side in ('them','us'):
        c=shares[side].get((b,'conv'),0); o=shares[side].get((b,'other'),0)
        line+=f" {side} {100*c/max(c+o,1):.0f}% ({c}/{c+o})  "
    print(line)
