"""throughput.py — winner-vs-loser length/throughput stats per game.
(1) alive-length distribution r100-300 by W/L team
(2) round at which each team hits 20/50/100 cumulative splits
(3) len-2 (<=3) children: fraction ever reaching len>=4; position of
    children = dist from own queen head and from own longest dragon head
    at the round the child is alive (averaged over its life <=r200)
Usage: python3 devin/lanes/throughput.py <replay-glob...>
"""
import sys, io, glob, contextlib, collections, statistics as st
sys.path.insert(0, '/home/ubuntu/bc/handoff/tooling')
from parse_replay import parse

def cheb(a,b): return max(abs(a[0]-b[0]),abs(a[1]-b[1]))
def L(h,t): return abs(h[0]-t[0])+abs(h[1]-t[1])+1

def analyze(path):
    with contextlib.redirect_stdout(io.StringIO()):
        r=parse(path)
    rnd=0; cur={}; dead=set(); splits={0:0,1:0}
    lenhist={0:collections.Counter(),1:collections.Counter()}  # midgame alive lens
    reach={0:{},1:{}}  # team -> {20:r,50:r,100:r}
    children={}  # id -> {'team':t,'born':r,'clen':n,'maxlen':n,'pos':[]}
    queen={0:None,1:None}
    res=r.get('result') or {}
    winner=res.get('winner')  # 'A'/'B'/None
    for e in r['events']:
        t=e['type']
        if t=='roundStart':
            rnd+=1
            if 100<=rnd<=300:
                for i,(h,l) in cur.items():
                    if i not in dead: lenhist[i%2][min(l,10)]+=1
            # child positions each round <=200
            if rnd<=200:
                for cid,c in children.items():
                    if cid in cur and cid not in dead:
                        ch=cur[cid][0]
                        qh=cur.get(queen[c['team']],(None,))[0] if queen[c['team']] is not None else None
                        longest=-1; lh=None
                        for j,(hj,lj) in cur.items():
                            if j%2==c['team'] and j not in dead and lj>longest:
                                longest,lh=lj,hj
                        c['pos'].append((cheb(ch,qh) if qh else None,
                                         cheb(ch,lh) if lh else None))
        elif t=='dragonUpdate':
            i=e['id']; cur[i]=(tuple(e['head']),L(e['head'],e['tail']))
            if i in children:
                c=children[i]; c['maxlen']=max(c['maxlen'],cur[i][1])
            if i<2: queen[i]=(i)  # queen ids 0/1
        elif t=='dragonSplit':
            team=0 if e['team']=='A' else 1
            splits[team]+=1
            for k in (20,50,100):
                if splits[team]==k and k not in reach[team]: reach[team][k]=rnd
            cid=e['childId']
            children[cid]={'team':team,'born':rnd,'clen':len(e['childBody']),'maxlen':len(e['childBody']),'pos':[]}
            if e['childBody']: cur[cid]=(tuple(e['childBody'][0]),len(e['childBody']))
            if e['parentBody']: cur[e['parentId']]=(tuple(e['parentBody'][0]),len(e['parentBody']))
        elif t=='dragonDeath':
            dead.add(e['id'])
    wside = 0 if winner=='A' else 1
    return {'rows':lenhist,'reach':reach,'children':children,'w':wside,'winner':winner,
            'map':path.split('/')[-1].split('-s')[0]}

games=[]
for g in sys.argv[1:]:
    for f in sorted(glob.glob(g)):
        try: games.append(analyze(f))
        except Exception as ex: print(f,'ERR',ex,file=sys.stderr)

# (1) midgame length dist W vs L
Wc=collections.Counter(); Lc=collections.Counter()
for g in games:
    Wc+=g['rows'][g['w']]; Lc+=g['rows'][1-g['w']]
def show(c,lab):
    tot=sum(c.values())
    ge4=sum(v for k,v in c.items() if k>=4)
    print(f"{lab}: n={tot} | len2 {100*c[2]/tot:.0f}% len3 {100*c[3]/tot:.0f}% len4-9 {100*sum(c[k] for k in range(4,10))/tot:.0f}% len10+ {100*c[10]/tot:.0f}% | alive>=4: {100*ge4/tot:.0f}%")
print("=== (1) midgame (r100-300) alive-length distribution ===")
show(Wc,'winner'); show(Lc,'loser')

# (2) rounds to split milestones
print("\n=== (2) median round reaching cumulative splits ===")
for k in (20,50,100):
    for who,wi in (('W',1),('L',0)):
        xs=[g['reach'][g['w'] if wi else 1-g['w']].get(k) for g in games]
        xs=[x for x in xs if x is not None]
        print(f"{k} splits {who}: n={len(xs)} median {st.median(xs) if xs else '-'} mean {st.mean(xs):.0f}" if xs else f"{k} splits {who}: n=0")

# (3) child survival to len>=4
print("\n=== (3) len-2/3 children reaching len>=4 ===")
for who in ('W','L'):
    kids=[c for g in games for c in g['children'].values()
          if c['clen']<=3 and (g['w'] if who=='W' else 1-g['w'])==c['team']]
    made=[c for c in kids if c['maxlen']>=4]
    dq=[st.mean([p[0] for p in c['pos'] if p[0] is not None]) for c in kids if c['pos'] and any(p[0] is not None for p in c['pos'])]
    dl=[st.mean([p[1] for p in c['pos'] if p[1] is not None]) for c in kids if c['pos'] and any(p[1] is not None for p in c['pos'])]
    dqm=[st.mean([p[0] for p in c['pos'] if p[0] is not None]) for c in made if c['pos'] and any(p[0] is not None for p in c['pos'])]
    dlm=[st.mean([p[1] for p in c['pos'] if p[1] is not None]) for c in made if c['pos'] and any(p[1] is not None for p in c['pos'])]
    print(f"{who}: children n={len(kids)} reached4={len(made)} ({100*len(made)/max(len(kids),1):.0f}%)")
    if dq: print(f"   d_queen mean all={st.mean(dq):.1f} survivors={st.mean(dqm) if dqm else 0:.1f} | d_longest all={st.mean(dl):.1f} survivors={st.mean(dlm) if dlm else 0:.1f}")
print('games:',len(games),'| no-winner:',sum(1 for g in games if g['winner'] is None))
