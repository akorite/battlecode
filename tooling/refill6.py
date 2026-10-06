import sys, time
sys.path.insert(0,'/home/ubuntu/bc/tooling')
import challenge
# Re-derived 2026-10-06 from last-80 ladder series: dropped <=20% teams
# (chad gdp, Knight Capital, tozoman, Wapowpow). Ordered by series-win x Elo.
targets = [(230,'my cactus died',10),(1081,'nooberGamer',10),(919,'1234',8),
           (799,'Tony S',8),(30,'life is NP hard',6),(705,'Hydra',6),
           (796,'Nexus Lab',6),(275,'verity',4),(116,'Spearhead Capital',4),
           (273,'Quantify',4),(303,'Oswald',5),(141,'Sarvottam',4),
           (849,'Milk Dragon',4),(221,'hm',3),(75,'Average Individuals',3),(529,'meowest',3)]
todo = {tid:n for tid,name,n in targets}
names = {tid:name for tid,name,n in targets}
deadline = time.time()+6*3600
while any(v>0 for v in todo.values()) and time.time()<deadline:
    busy = False
    for tid,name,n in targets:
        if todo[tid]<=0: continue
        try:
            challenge.post(tid, ranked=True)
            todo[tid]-=1; print(f'{names[tid]}: ok',flush=True); time.sleep(0.7)
        except BaseException as e:
            s=str(e)
            if '429' in s or 'more than' in s.lower() or 'cap' in s.lower() or 'limit' in s.lower() or 'used its' in s: busy=True
            else: print(f'{names[tid]}: err {s[:90]}',flush=True); todo[tid]=0
    if any(v>0 for v in todo.values()):
        time.sleep(180 if busy else 10)
print('done',todo,flush=True)
