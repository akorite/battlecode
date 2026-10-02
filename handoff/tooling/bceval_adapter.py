"""Port of bceval.features.replay_features onto our dict-based replay decoder.
Uses bceval's mapdata (pure python) and score.py for the model."""
import sys, os, importlib.util
_HERE=os.path.dirname(os.path.abspath(__file__))
def _load(name, relpath):
    spec=importlib.util.spec_from_file_location(name, os.path.join(_HERE,'battlecode-eval','bceval',relpath))
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
_mapdata=_load('bc_mapdata','mapdata.py')
map_data, step=_mapdata.map_data, _mapdata.step
def _score():
    return _load('bc_score','score.py')
from parse_replay import parse

RICH_GAP = 60
HOT_SHARE = 0.30
WINDOW = 25
FAR = 30
TEAM_FEATURES = [
    "alive","total","longest","second","third","big5","big10",
    "eat","eat_rich","eat_hot","deaths","lost_len","kills_h2h",
    "terr","supply","rich_ctrl","hot_ctrl","pearls_near",
    "champ_enemy_d","champ_enemy_n3","champ_enemy_n6","champ_ally_d","champ_exits",
]
DIRIDX = {'N':0,'E':1,'S':2,'W':3}

def _map_name(text):
    for line in text.split("\n"):
        p=line.split()
        if p and p[0]=="MAP_NAME": return " ".join(p[1:]).strip()
    return ""

def _spawn_rates(text):
    rate={}
    for line in text.split("\n"):
        p=line.split()
        if p and p[0]=="TILE":
            lo,hi=int(p[3]),int(p[4])
            if hi>0: rate[(int(p[1]),int(p[2]))]=2.0/max(1,lo+hi)
    return rate

def _hot_tiles(rate):
    total,acc,hot=sum(rate.values()),0.0,set()
    for t,r in sorted(rate.items(),key=lambda kv:-kv[1]):
        if acc>=HOT_SHARE*total: break
        hot.add(t); acc+=r
    return hot

def _neighbours(board):
    nb={}
    for y in range(board["height"]):
        for x in range(board["width"]):
            nb[(x,y)]=[t for t in (step(board,(x,y),d) for d in range(4)) if t is not None]
    return nb

def _bfs_multi(nb,sources):
    dist,lab={},{}; frontier=[]
    for t,l in sources.items():
        if t in dist:
            if lab[t]!=l: lab[t]=None
            continue
        dist[t],lab[t]=0,l; frontier.append(t)
    d=0
    while frontier:
        d+=1; nxt=[]
        for t in frontier:
            lt=lab[t]
            for u in nb[t]:
                if u not in dist:
                    dist[u],lab[u]=d,lt; nxt.append(u)
                elif dist[u]==d and lab[u]!=lt: lab[u]=None
        frontier=nxt
    return dist,lab

def _bfs_from(nb,start,cap):
    dist={start:0}; frontier=[start]
    for d in range(1,cap+1):
        nxt=[]
        for t in frontier:
            for u in nb[t]:
                if u not in dist: dist[u]=d; nxt.append(u)
        frontier=nxt
        if not frontier: break
    return dist

def _snapshot(dragons,pearls,nb,rate,rich,hot,hist,rnd):
    alive={"A":[],"B":[]}
    for d in dragons.values():
        if d["alive"] and d["body"]: alive[d["team"]].append(d)
    occupied=set()
    for side in "AB":
        for d in alive[side]: occupied.update(d["body"])
    heads={}
    for side in "AB":
        for d in alive[side]:
            h=d["body"][0]
            heads[h]=side if heads.get(h,side)==side else None
    _,lab=_bfs_multi(nb,heads) if heads else ({},{})
    out={}; lo=rnd-WINDOW
    for side in "AB":
        other="B" if side=="A" else "A"
        lens=sorted((len(d["body"]) for d in alive[side]),reverse=True)+[0,0,0]
        f={"alive":len(alive[side]),"total":sum(lens),"longest":lens[0],
           "second":lens[1],"third":lens[2],
           "big5":sum(1 for L in lens if L>=5),"big10":sum(1 for L in lens if L>=10)}
        h=hist[side]
        f["eat"]=sum(1 for r in h["eat"] if r>=lo)
        f["eat_rich"]=sum(1 for r in h["eat_rich"] if r>=lo)
        f["eat_hot"]=sum(1 for r in h["eat_hot"] if r>=lo)
        f["deaths"]=sum(1 for r,_ in h["death"] if r>=lo)
        f["lost_len"]=sum(L for r,L in h["death"] if r>=lo)
        f["kills_h2h"]=sum(1 for r in h["h2h"] if r>=lo)
        mine=[tile for tile,l in lab.items() if l==side]
        f["terr"]=len(mine)
        f["supply"]=sum(rate.get(tile,0.0) for tile in mine)
        f["rich_ctrl"]=sum(1 for tile in mine if tile in rich)
        f["hot_ctrl"]=sum(1 for tile in mine if tile in hot)
        f["pearls_near"]=sum(1 for p in pearls if lab.get(p)==side)
        champ=max(alive[side],key=lambda d:len(d["body"]),default=None)
        if champ is None:
            f.update(champ_enemy_d=0,champ_enemy_n3=0,champ_enemy_n6=0,champ_ally_d=0,champ_exits=0)
        else:
            ch=champ["body"][0]; cd=_bfs_from(nb,ch,FAR)
            ed=[cd[d["body"][0]] for d in alive[other] if d["body"][0] in cd]
            ad=[cd[d["body"][0]] for d in alive[side] if d is not champ and d["body"][0] in cd]
            f["champ_enemy_d"]=min(ed,default=FAR+1)
            f["champ_enemy_n3"]=sum(1 for x in ed if x<=3)
            f["champ_enemy_n6"]=sum(1 for x in ed if x<=6)
            f["champ_ally_d"]=min(ad,default=FAR+1)
            f["champ_exits"]=sum(1 for u in nb[ch] if u not in occupied)
        out[side]=f
    return out

def replay_features(path, every=25):
    """(game, rows): rows hold TEAM_FEATURES per side every `every` rounds + final (round 501)."""
    rep=parse(path)
    board=map_data(rep["map"])
    nb=_neighbours(board)
    rate=_spawn_rates(rep["map"])
    rich={t for t,r in rate.items() if 2.0/r<=RICH_GAP}
    hot=_hot_tiles(rate)
    dragons={i:{**d,"alive":True,"body":[tuple(p) for p in d["body"]],"pending":0}
             for i,d in enumerate(board["dragons"])}
    pearls=set()
    hist={s:{"eat":[],"eat_rich":[],"eat_hot":[],"death":[],"h2h":[]} for s in "AB"}
    rows=[]; rnd=0; cur=None
    want=set(range(every,501,every))|{1}
    for ev in rep["events"]:
        kind=ev["type"]
        if kind=="roundStart":
            rnd=ev["round"]
            if rnd in want:
                snap=_snapshot(dragons,pearls,nb,rate,rich,hot,hist,rnd)
                rows.append({"round":rnd,"a":snap["A"],"b":snap["B"]})
        elif kind=="turnStart":
            cur=ev["id"]
        elif kind=="tileChange":
            tile=tuple(ev["tile"])
            if ev["hasPearl"]: pearls.add(tile); continue
            pearls.discard(tile)
            d=dragons.get(cur) if cur is not None else None
            if d:
                hist[d["team"]]["eat"].append(rnd)
                if tile in rich: hist[d["team"]]["eat_rich"].append(rnd)
                if tile in hot: hist[d["team"]]["eat_hot"].append(rnd)
        elif kind=="dragonAction":
            i=ev["id"]; a=ev.get("action")
            d=dragons.get(i)
            if not d or not d["alive"] or not a or a["kind"]!="move": continue
            d["pending"]=0
            for direction in a["steps"]:
                dest=step(board,d["body"][0],DIRIDX[direction])
                if dest is None: break
                d["body"].insert(0,dest); d["pending"]+=1
        elif kind=="dragonUpdate":
            d=dragons.get(ev["id"])
            if not d or not d["alive"]: continue
            head,tail=tuple(ev["head"]),tuple(ev["tail"])
            if d["body"] and d["body"][0]!=head and d["pending"]:
                del d["body"][:d["pending"]]
            d["pending"]=0
            if not d["body"] or d["body"][0]!=head: d["body"].insert(0,head)
            at=[n for n,p in enumerate(d["body"]) if p==tail]
            d["body"]=d["body"][:at[0]+1] if at else [head,tail]
        elif kind=="dragonSplit":
            t=ev["team"]
            dragons.setdefault(ev["parentId"],{"team":t,"alive":True,"pending":0})
            dragons[ev["parentId"]].update({"team":t,"alive":True,"pending":0,
                "body":[tuple(p) for p in ev["parentBody"]]})
            dragons[ev["childId"]]={"team":t,"alive":True,"pending":0,
                "body":[tuple(p) for p in ev["childBody"]]}
        elif kind=="dragonDeath":
            d=dragons.get(ev["id"])
            if not d or not d["alive"]: continue
            d["alive"]=False
            hist[d["team"]]["death"].append((rnd,len(d["body"])))
            if ev["reason"]=="hitHeadToHead":
                hist["B" if d["team"]=="A" else "A"]["h2h"].append(rnd)
    final=_snapshot(dragons,pearls,nb,rate,rich,hot,hist,rnd)
    rows.append({"round":501,"a":final["A"],"b":final["B"]})
    res=rep["result"] or {}
    ta,tb=res.get("teamA",{}),res.get("teamB",{})
    ok=all((final[s]["alive"],final[s]["longest"],final[s]["total"])
           ==(st.get("dragonCount"),st.get("longestDragon"),st.get("totalLength"))
           for s,st in (("A",ta),("B",tb))) if ta and tb else False
    game={"map":_map_name(rep["map"]),"bot_a":rep["botA"],"bot_b":rep["botB"],
          "winner":res.get("winner"),"end":res.get("endReason"),"last_round":rnd,"ok":ok}
    return game,rows

if __name__=="__main__":
    import glob,time
    sc=_score(); win_probability, logit_parts=sc.win_probability, sc.logit_parts
    p=sorted(glob.glob('replays/*.replay'))[0]
    t0=time.time()
    game,rows=replay_features(p,every=25)
    print(game, f'{time.time()-t0:.2f}s', len(rows),'rows')
    for r in rows[:6]:
        print(r["round"], round(win_probability(r["round"],r["a"],r["b"]),3),
              {k:round(v,2) for k,v in logit_parts(r["round"],r["a"],r["b"]).items()})
    print('last:',rows[-1]["round"],round(win_probability(rows[-1]["round"],rows[-1]["a"],rows[-1]["b"]),3))
