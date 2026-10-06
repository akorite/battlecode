"""deathgeo.py — len<=3 death forensics: where do our short dragons die?
For every dragonDeath with last-known len<=3 record:
  round, map, team(A/B), reason, death cell, dist to nearest ally head,
  nearest enemy head dist, enemies within cheb-3 of death cell,
  and the prior-round geometry for the cover-seek counterfactual:
  enemy<=4 at decide? ally<=2 at decide? nearest ally dist/dir at decide.
Usage: python3 devin/lanes/deathgeo.py <replay-glob...>"""
import sys, io, glob, contextlib, collections, re
sys.path.insert(0, '/home/ubuntu/bc/handoff/tooling')
from parse_replay import parse

def cheb(a, b, W=None, H=None, wrap=False):
    dx = abs(a[0]-b[0]); dy = abs(a[1]-b[1])
    if wrap and W and H:
        dx = min(dx, W-dx); dy = min(dy, H-dy)
    return max(dx, dy)

def map_dims(maptext):
    W=H=0; free=set()
    for ln in maptext.splitlines():
        t=ln.split()
        if not t: continue
        if t[0]=='MAP': W,H=int(t[1]),int(t[2])
        elif t[0]=='TILE': free.add((int(t[1]),int(t[2])))
    # porous edge => torus on that axis
    wrapx = any((0,y) in free for y in range(H)) and any((W-1,y) in free for y in range(H))
    wrapy = any((x,0) in free for x in range(W)) and any((x,H-1) in free for x in range(W))
    return W,H,free,wrapx and wrapy

def analyze(path):
    with contextlib.redirect_stdout(io.StringIO()):
        r = parse(path)
    W,H,free,wrap = map_dims(r['map'])
    rnd=0
    cur={}          # id -> (head,len) latest
    prev={}         # id -> head at previous round
    prevstate=None  # snapshot {id:(head,len)} entering this round
    dead=set()
    rows=[]
    def snapshot(): return {i:v for i,v in cur.items() if i not in dead}
    for e in r['events']:
        t=e['type']
        if t=='roundStart':
            prevstate = snapshot(); rnd=e.get('round',rnd+1)
        elif t=='dragonUpdate':
            cur[e['id']]=(tuple(e['head']), abs(e['head'][0]-e['tail'][0])+abs(e['head'][1]-e['tail'][1])+1)
        elif t=='dragonSplit':
            pid,cid=e['parentId'],e['childId']
            if e['childBody']: cur[cid]=(tuple(e['childBody'][0]), len(e['childBody']))
            if e['parentBody']: cur[pid]=(tuple(e['parentBody'][0]), len(e['parentBody']))
        elif t=='dragonDeath':
            i=e['id']
            if i in cur:
                h,L = cur[i]
                if L<=3:
                    team = 'A' if i%2==0 else 'B'
                    # current-round positions: everyone still alive
                    allies=[(j,v[0]) for j,v in cur.items() if j%2==i%2 and j!=i and j not in dead]
                    enes=[(j,v[0]) for j,v in cur.items() if j%2!=i%2 and j not in dead]
                    d_ally=min((cheb(h,a[1],W,H,wrap) for a in allies), default=None)
                    en3=[j for j,eh in enes if cheb(h,eh,W,H,wrap)<=3]
                    d_en=min((cheb(h,eh,W,H,wrap) for j,eh in enes), default=None)
                    # prior-round geometry for counterfactual
                    pf={}
                    if prevstate and i in prevstate:
                        ph=prevstate[i][0]
                        pallies=[v[0] for j,v in prevstate.items() if j%2==i%2 and j!=i]
                        penes=[v[0] for j,v in prevstate.items() if j%2!=i%2]
                        pf['p_en_min']=min((cheb(ph,eh,W,H,wrap) for eh in penes), default=None)
                        pf['p_ally_min']=min((cheb(ph,ah,W,H,wrap) for ah in pallies), default=None)
                        # nearest ally head at prev round + its dist now
                        if pallies:
                            na=min(pallies, key=lambda ah: cheb(ph,ah,W,H,wrap))
                            pf['p_na']=na
                        if penes:
                            ne=min(penes, key=lambda eh: cheb(ph,eh,W,H,wrap))
                            pf['p_ne']=ne; pf['p_ne_d']=cheb(ph,ne,W,H,wrap)
                            # would a 1-step toward nearest ally increase dist to nearest enemy?
                            if 'p_na' in pf:
                                ax,ay=na; px,py=ph
                                step=(px+(ax>px)-(ax<px), py+(ay>py)-(ay<py))
                                pf['step_up']=cheb(step,ne,W,H,wrap) > pf['p_ne_d']
                                pf['step_free']=step in free
                    mname=re.match(r'(.+)-s\d+-(\w+)-(\w+)\.replay', path.split('/')[-1])
                    side = 'cand' if (mname and (mname.group(2) if team=='A' else mname.group(3))=='abyss_v263') else 'base'
                    rows.append({'map':mname.group(1) if mname else path.split('/')[-1].split('-s')[0],'team':team,'side':side,
                                 'round':rnd,'reason':e['reason'],'len':L,'cell':h,
                                 'd_ally':d_ally,'d_en':d_en,'en3':len(en3),**pf})
            dead.add(i)
    return rows

out=[]
for g in sys.argv[1:]:
    for f in sorted(glob.glob(g)):
        try:
            rows=analyze(f); out.extend(rows)
            print(f, len(rows), 'len<=3 deaths', file=sys.stderr)
        except Exception as ex:
            print(f,'ERR',ex, file=sys.stderr)

# ---- report ----
REASONS=['hitHeadToHead','hitWall','hitSelf','hitOtherBody','noValidAction']
def agg(rows,label):
    print(f"\n=== {label} (n={len(rows)}) ===")
    print("reason mix:", dict(collections.Counter(r['reason'] for r in rows)))
    al=[r['d_ally'] for r in rows if r['d_ally'] is not None]
    en=[r['d_en'] for r in rows if r['d_en'] is not None]
    if al: print(f"d_ally median {sorted(al)[len(al)//2]:.0f} mean {sum(al)/len(al):.2f} (<=2: {100*sum(1 for x in al if x<=2)/len(al):.0f}%)")
    if en: print(f"d_en   median {sorted(en)[len(en)//2]:.0f} mean {sum(en)/len(en):.2f} (<=3: {100*sum(1 for x in en if x<=3)/len(en):.0f}%)")
    print(f"enemy within cheb-3 of death cell: {100*sum(1 for r in rows if r['en3']>0)/len(rows):.0f}%")

for side in ('cand','base'):
    agg([r for r in out if r.get('side')==side], f'{side} (v263 = cand)')
for reason in REASONS:
    sub=[r for r in out if r['reason']==reason]
    if sub:
        al=[r['d_ally'] for r in sub if r['d_ally'] is not None]
        print(f"{reason}: n={len(sub)} d_ally<=2 {100*sum(1 for x in al if x<=2)/max(len(al),1):.0f}% median_r {sorted(r['round'] for r in sub)[len(sub)//2]}")

# counterfactual on victim-ram-ish deaths (h2h or en3>0)
cand=[r for r in out if r.get('p_en_min') is not None]
fire=[r for r in cand if r['p_en_min']<=4 and (r['p_ally_min'] is None or r['p_ally_min']>2)]
print(f"\n=== cover-seek counterfactual (all len<=3 deaths) ===")
print(f"deaths with prior-round snapshot: {len(cand)}/{len(out)}")
print(f"rule fires (enemy<=4 && no ally<=2): {len(fire)} ({100*len(fire)/len(out):.0f}%)")
saved=[r for r in fire if r.get('step_up') and r.get('step_free') and r['reason']=='hitHeadToHead']
print(f"fires + toward-ally step increases dist-to-enemy + cell free + h2h: {len(saved)} ({100*len(saved)/len(out):.0f}%)")
bymap=collections.defaultdict(lambda:[0,0])
for r in out: bymap[r['map']][0]+=1
for r in saved: bymap[r['map']][1]+=1
for m,(tot,sv) in sorted(bymap.items()): print(f"  {m}: {sv}/{tot} plausibly saved ({100*sv/max(tot,1):.0f}%)")
fire_h2h=[r for r in fire if r['reason']=='hitHeadToHead']
print(f"of the fired set, reasons: {dict(collections.Counter(r['reason'] for r in fire))}")
print(f"median round of fired h2h deaths: {sorted(r['round'] for r in fire_h2h)[len(fire_h2h)//2] if fire_h2h else '-'}")
