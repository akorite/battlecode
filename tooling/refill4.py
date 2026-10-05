import sys, time
sys.path.insert(0,'/home/ubuntu/bc/tooling')
import challenge
# measured win-rate vs elo-premium: only fire where wins are achievable
targets = [(70,'chad gdp',6),(226,'Knight Capital',6),(7,'Just Keep Swimming',5),
           (837,'Nitronics',4),(538,'Um_nik',4),(1081,'nooberGamer',4),
           (919,'1234',3),(799,'Tony S',4),(141,'Sarvottam',3)]
todo = {tid:n for tid,name,n in targets}
names = {tid:name for tid,name,n in targets}
deadline = time.time()+2.5*3600
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
