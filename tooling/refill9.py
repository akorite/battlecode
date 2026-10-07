import sys, time
sys.path.insert(0,'/home/ubuntu/bc/tooling')
import challenge
# Floor: ranked needs opponent >=1636. Beatable: MSDT 3-2, slither 3-2.
targets = [(406,'MartinShkreli',10),(1102,'slither hither',10)]
todo = {tid:n for tid,name,n in targets}
names = {tid:name for tid,name,n in targets}
deadline = time.time()+8*3600
while any(v>0 for v in todo.values()) and time.time()<deadline:
    busy = False
    for tid,name,n in targets:
        if todo[tid]<=0: continue
        try:
            challenge.post(tid, ranked=True)
            todo[tid]-=1; print(f'{names[tid]}: ok',flush=True); time.sleep(0.7)
        except BaseException as e:
            s=str(e)
            if '429' in s or 'more than' in s.lower() or 'cap' in s.lower() or 'limit' in s.lower(): busy=True
            else: print(f'{names[tid]}: err {s[:90]}',flush=True); todo[tid]=0
    if any(v>0 for v in todo.values()):
        time.sleep(240 if busy else 10)
print('done',todo,flush=True)
