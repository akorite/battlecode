import sys, time
sys.path.insert(0,'/home/ubuntu/bc/tooling')
import challenge
# Re-derived 2026-10-06 from observed per-game deltas: +400-Elo opponents pay
# ~30/win ~1-2/loss (profitable at ~15% WR); +50-200 opponents cost ~7/loss
# symmetric (need >50%, we have none) -> CUT; near-parity teams we beat >60%
# are the grind base.
targets = [(70,'chad gdp',6),(226,'Knight Capital',6),(1955,'Quaker Qubits?',0),
           (230,'my cactus died',10),(849,'Milk Dragon',8),(141,'Sarvottam',8),
           (303,'Oswald',6),(273,'Quantify',5),(1081,'nooberGamer',4),
           (799,'Tony S',4)]
targets = [(t,n,k) for t,n,k in targets if k>0]
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
