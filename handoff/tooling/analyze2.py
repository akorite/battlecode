"""Analyze pass 2: base stats (analyze.game_stats) + bceval eval curve + feature snapshots.
Incremental: only processes game ids missing from lists/game_stats2.jsonl."""
import json, os, sys
from multiprocessing import Pool
from analyze import game_stats
from bceval_adapter import replay_features, _score

_sc=None
def _score_l():
    global _sc
    if _sc is None: _sc=_score()
    return _sc

# eval the expensive pass only on: all pre-Sep-30 games, any game involving a
# top-10 team, and a deterministic 25% sample of the rest
_TOP10={306,264,314,91,70,206,27,20,213,952}
_SEP30_MS=1782864000*1000  # unused; computed below from era buckets instead
def _want_eval(g):
    import datetime
    d=datetime.datetime.utcfromtimestamp(g['at']/1000)
    if d < datetime.datetime(2026,9,30): return True
    if g['a']['id'] in _TOP10 or g['b']['id'] in _TOP10: return True
    return g['id'] % 4 == 0

def _work(g):
    path=f"replays/{g['id']}.replay"
    if not os.path.exists(path): return None
    s=game_stats(g,path)
    if s is None: return None
    s['topTeam']=g['a']['id'] if False else g.get('topTeam')
    if not _want_eval(g):
        s['eval_ok']=False; s['eval_skipped']=True
        return s
    # eval pass
    try:
        game,rows=replay_features(path,every=50)
        sc=_score_l()
        ev=[[r['round'],round(sc.win_probability(r['round'],r['a'],r['b']),3)] for r in rows]
        s['eval']=ev
        R=g.get('rounds') or game['last_round'] or 500
        # snapshot rows at ~25/50/75% progress for aggregation
        snaps={}
        for frac in (0.25,0.5,0.75):
            tgt=int(frac*R)
            row=min(rows,key=lambda r:abs(r['round']-tgt) if r['round']<=500 else 1e9)
            snaps[str(frac)]={'round':row['round'],'a':row['a'],'b':row['b']}
        s['feat']=snaps
        s['parts_end']={k:round(v,3) for k,v in sc.logit_parts(rows[-1]['round'],rows[-1]['a'],rows[-1]['b']).items()}
        s['eval_ok']=game['ok']
    except Exception as e:
        s['eval_error']=str(e)[:200]
    return s

def main():
    games=json.load(open('lists/games3.json'))
    done=set()
    opath='lists/game_stats2.jsonl'
    if os.path.exists(opath):
        for l in open(opath):
            try: done.add(json.loads(l)['id'])
            except Exception: pass
    todo=[g for g in games if g['id'] not in done]
    print('todo',len(todo),flush=True)
    out=open(opath,'a')
    ok=0
    with Pool(8) as pool:
        for s in pool.imap_unordered(_work,todo,chunksize=4):
            if s:
                ok+=1; out.write(json.dumps(s)+'\n')
                if ok%200==0: out.flush(); print(ok,flush=True)
    out.close()
    print('done',ok)

if __name__=='__main__':
    main()
