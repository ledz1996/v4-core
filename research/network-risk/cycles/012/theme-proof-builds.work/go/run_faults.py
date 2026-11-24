# Planted-fault check: the same harness with a wrong Mul64 or an unguarded wasm shift must report mismatches.
# A vector that does not finish in 0.2 s (a reduction loop that a wrong product sends far) counts as a mismatch.
# Usage: python3 -I run_faults.py <tools/opdiff dir> <workdir> <out.json>
import sys,json,random,signal
sys.path.insert(0,sys.argv[2]); sys.path.insert(1,sys.argv[1])
import run_vectors as R, targeted, battery, u256py as U
class TO(Exception): pass
def h(*a): raise TO()
signal.signal(signal.SIGALRM,h)
VT=targeted.vectors(); rnd=random.Random(3); sample=rnd.sample(VT,3000)
out={}
for p in ('fault_mul','fault_shift'):
    U.PRIM=p; ran=bad=to=0; per={}
    for t in sample:
        op,a,b,c=t[:4]
        signal.setitimer(signal.ITIMER_REAL,0.2)
        try: got=R.evm(op,a,b,c)
        except TO: got='timeout'; to+=1
        except Exception as e: got='exc'
        finally: signal.setitimer(signal.ITIMER_REAL,0)
        if got is None: continue
        ran+=1
        if got!=battery.reference(op,a,b,c,b''): bad+=1; per[op]=per.get(op,0)+1
    out[p]={'ran':ran,'mismatch':bad,'timeouts':to,'mismatchPerOp':per}; print(p,out[p],flush=True)
json.dump(out,open(sys.argv[3],'w'),indent=1)
