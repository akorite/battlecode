import sys, time
sys.path.insert(0,'/home/ubuntu/bc/tooling')
import challenge
targets = [(1081,'nooberGamer',12),(919,'1234',8),(436,'zzz3nith',8),(799,'Tony S',6),
           (837,'Nitronics',4),(7,'Just Keep Swimming',4),(538,'Um_nik',4),
           (928,'Ron Squad',4),(226,'Knight Capital',3),(141,'Sarvottam',4),
           (742,'Imagine Winning',4),(762,'Maccas',4),
           (70,'chad gdp',3),(501,'Quaker Qubits',3),(952,'Cache me outside',2)]
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
