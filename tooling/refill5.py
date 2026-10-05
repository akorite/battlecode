import sys, time
sys.path.insert(0,'/home/ubuntu/bc/tooling')
import challenge
# Retargeted from 80-set history: only proven 3-5/5 records. Elo-premium first.
targets = [(226,'Knight Capital',8),(70,'chad gdp',8),(1081,'nooberGamer',8),
           (919,'1234',6),(275,'verity',5),(357,'tozoman',5),(879,'Wapowpow',5),
           (799,'Tony S',6),(141,'Sarvottam',5),(303,'Oswald',5),(796,'Nexus Lab',5),
           (1038,'Larper',4),(711,'Just Reboot Normalize',4),(705,'Hydra',5)]
todo = {tid:n for tid,name,n in targets}
names = {tid:name for tid,name,n in targets}
deadline = time.time()+3*3600
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
