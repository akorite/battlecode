"""opcad.py — opening cadence bisect r0-90 per-10r buckets, us vs opp.
Corpus: replays144/*.replay + ids.json [mid,map,ourSeat,winner].
Per side: alive, splits, eaten (tileChange pearl->gone attrib), intake
rate (eats/unit-round), lifetimes of units dying<=90, deaths by cause,
queen bud cadence (rounds between queen splits), worker first-split,
child survival to len>=4, unique tiles visited (map coverage).
Usage: python3 devin/lanes/opcad.py
"""
import sys, io, glob, json, contextlib, collections, statistics as st
sys.path.insert(0,'/home/ubuntu/bc/handoff/tooling')
from parse_replay import parse

def cheb(a,b): return max(abs(a[0]-b[0]),abs(a[1]-b[1]))
def analyze(path, ourparity):
    with contextlib.redirect_stdout(io.StringIO()):
        r=parse(path)
    rnd=0; cur={}; dead=set(); born={}
    B=collections.defaultdict(int)  # (side,metric)->count
    det=collections.defaultdict(lambda: collections.Counter())
    visits=collections.defaultdict(set)
    qsplits=collections.defaultdict(list)
    firstsplit={}
    kids={}
    eaten_tiles=set(); last_h={}
    wfirst={}
    for e in r['events']:
        t=e['type']
        if t=='roundStart':
            rnd+=1
            if rnd>90: break
            b=rnd//10
            for i,(h,L) in cur.items():
                if i in dead: continue
                s='us' if i%2==ourparity else 'them'
                B[(s,'alive'+str(b))]+=1; B[(s,'ur')]+=1
                visits[s].add(h)
        elif t=='tileChange':
            cell=tuple(e['tile'])
            if not e['hasPearl'] and cell in eaten_tiles: pass
            if not e['hasPearl']:
                eaters=[i for i,(h,L) in cur.items() if i not in dead and cheb(h,cell)<=1]
                if eaters:
                    ei=min(eaters,key=lambda i:cheb(cur[i][0],cell))
                    s='us' if ei%2==ourparity else 'them'
                    B[(s,'eaten'+str(rnd//10))]+=1
        elif t=='dragonUpdate':
            cur[e['id']]=(tuple(e['head']),abs(e['head'][0]-e['tail'][0])+abs(e['head'][1]-e['tail'][1])+1)
            born.setdefault(e['id'],rnd)
        elif t=='dragonSplit':
            tm=0 if e['team']=='A' else 1
            s='us' if tm==ourparity else 'them'
            B[(s,'splits'+str(rnd//10))]+=1
            pid,cid=e['parentId'],e['childId']
            if pid<4: qsplits[s].append(rnd)
            elif s not in wfirst or rnd<wfirst[s]: wfirst[s]=rnd
            kids[cid]={'side':s,'born':rnd,'clen':len(e['childBody']),'maxlen':len(e['childBody'])}
            if e['childBody']: cur[cid]=(tuple(e['childBody'][0]),len(e['childBody']))
            if e['parentBody']: cur[pid]=(tuple(e['parentBody'][0]),len(e['parentBody']))
        elif t=='dragonDeath':
            i=e['id']; s='us' if i%2==ourparity else 'them'
            det[s][e['reason']]+=1
            if i in kids: kids[i]['died']=rnd
            dead.add(i)
    return B,det,visits,qsplits,kids,wfirst

files=sorted(glob.glob('/home/ubuntu/bc/replays144/*.replay'))
ids={str(x[0]):x for x in json.load(open('/home/ubuntu/bc/replays144/ids.json'))}
AGG=collections.defaultdict(lambda: collections.Counter())
DET=collections.defaultdict(lambda: collections.Counter())
VIS=collections.defaultdict(list); QS=collections.defaultdict(list)
KID=collections.defaultdict(list); WF=collections.defaultdict(list)
ng=0
for f in files:
    mid=f.split('/')[-1].split('.')[0][1:]
    if mid not in ids: continue
    seat=ids[mid][2]; ourp=0 if seat=='A' else 1
    try: B,det,vis,qs,kids,wf=analyze(f,ourp)
    except Exception as ex: print(f,'ERR',ex,file=sys.stderr); continue
    ng+=1
    for (s,k),v in B.items(): AGG[s][k]+=v
    for s,d in det.items():
        for rsn,n in d.items(): DET[s][rsn]+=n
    for s,v in vis.items(): VIS[s].append(len(v))
    for s,xs in qs.items(): QS[s].extend(xs)
    for c in kids.values(): KID[c['side']].append(c)
    for s,r_ in wf.items(): WF[s].append(r_)

print(f"########## {ng} small-map games r0-90 ##########")
for s in ('us','them'):
    print(f"\n[{s}] alive/splits/eaten per 10r bucket (sums over {ng}g):")
    ur=AGG[s]['ur']
    for b in range(9):
        a=AGG[s][f'alive{b}']; sp=AGG[s][f'splits{b}']; e=AGG[s][f'eaten{b}']
        print(f"  r{b*10:>2}-{b*10+9}: alive_sum {a:>5} splits {sp:>4} eaten {e:>4}")
    print(f"  unit-rounds total {ur} | eats {sum(AGG[s][f'eaten{b}'] for b in range(9))} | per-unit intake {100*sum(AGG[s][f'eaten{b}'] for b in range(9))/max(ur,1):.2f}/100ur")
    print(f"  deaths<=90 by cause: {dict(DET[s])}")
    q=sorted(QS[s]); gaps=[b-a for a,b in zip(q,q[1:])]
    print(f"  queen splits: {q[:12]}{'...' if len(q)>12 else ''} | inter-split median {st.median(gaps) if gaps else '-'}")
    # worker first-split: earliest round a non-queen parent split
    # (worker splits captured via firstsplit dict per game — need tracking; approximated via KID birth ages)
    mk=[c for c in KID[s] if c['maxlen']>=4]
    print(f"  children n={len(KID[s])} reached len>=4: {len(mk)} ({100*len(mk)/max(len(KID[s]),1):.0f}%)")
    if VIS[s]: print(f"  map coverage: mean unique tiles {st.mean(VIS[s]):.0f} median {st.median(VIS[s]):.0f}")
    if WF[s]: print(f"  worker first-split round: median {st.median(WF[s]):.0f} mean {st.mean(WF[s]):.1f} (n={len(WF[s])})")
# worker first-split: children of non-queen parents born<=90 that themselves split — not tracked; print queen first splits only
