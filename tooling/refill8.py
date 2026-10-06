import sys, time
sys.path.insert(0,'/home/ubuntu/bc/tooling')
import challenge
# Proven-beatable targets only (>=55% observed WR at near-par or better Elo).
# No +400 asymmetric shots (falsified: -9 to -26 per lost series).
targets = [(421,'unemployed',8),(141,'Sarvottam',8),(324,'Mr Aura',6),
           (190,'risq-v',6),(230,'my cactus died',8),(420,'ThatsThat',6),
           (799,'Tony S',6),(849,'Milk Dragon',8),
           (796,'Nexus Lab',5),(303,'Oswald',5)]
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
