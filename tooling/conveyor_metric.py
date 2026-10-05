"""Conveyor efficiency per steering rule: for each side in a replay,
- feeders lost = our len<=5 dragons dying hitHeadToHead in the feed window (r360-499)
- nva feeds = our noValidAction deaths in the window
- champ gain = longest@end vs longest@r360 (approx via update tracking)
Usage: conveyor_metric.py <replay> ..."""
import sys, glob
sys.path.insert(0,'handoff/tooling')
import parse_replay

def analyze(path, feedAt=360):
    d = parse_replay.parse(path); ev = d['events']
    teams = {}          # id -> 'A'/'B'
    lens  = {}          # id -> len (approx from split child count + updates)
    for e in ev:
        if e['type'] == 'dragonSplit':
            teams[e['childId']] = e['team']
            if e['parentId'] not in teams and e.get('team'):
                teams[e['parentId']] = e['team']
    # queens 0->A,1->B
    teams.setdefault(0,'A'); teams.setdefault(1,'B')
    rnd = 0
    win = {'A':{'nva':0,'h2h_small':0,'h2h_big':0,'wall':0,'self':0,'body':0},
           'B':{'nva':0,'h2h_small':0,'h2h_big':0,'wall':0,'self':0,'body':0}}
    for e in ev:
        if e['type']=='roundStart': rnd=e['round']
        if e['type']=='dragonDeath':
            t = teams.get(e['id']); r=e['reason']
            if not t or rnd < feedAt: continue
            if r=='noValidAction': win[t]['nva']+=1
            elif r=='hitHeadToHead': win[t]['h2h_small']+=1   # size split needs len; lump for now
            elif r=='hitWall': win[t]['wall']+=1
            elif r=='hitSelf': win[t]['self']+=1
            elif r=='hitOtherBody': win[t]['body']+=1
    res=d['result']
    return win,res

if __name__=='__main__':
    tot={'A':{},'B':{}}; n=0
    for f in sys.argv[1:]:
        win,res=analyze(f); n+=1
        # which side is cand? filename carries names
        for s in 'AB':
            for k,v in win[s].items(): tot[s][k]=tot[s].get(k,0)+v
        print(f"{f.split('/')[-1]:55s} A:{win['A']} longestA={res['teamA']['longestDragon']} | B:{win['B']} longestB={res['teamB']['longestDragon']}")
    print('== means ==')
    for s in 'AB':
        print(' ',s,{k:round(v/n,1) for k,v in tot[s].items()})
