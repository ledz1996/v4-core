# For the one site whose 0-or-64 value is still in $3 (v1) at a return, follow it in each of the 8 jal callers
# of the containing function (entry 0x12004bf10), from the instruction after the call's delay slot.
import os,sys,json
os.environ['TEXT']=sys.argv[1]; sys.argv=[sys.argv[0]]
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import cfg_scan as C
calls=[0x120045848,0x120045c20,0x120045f84,0x120046524,0x12004680c,0x120046b9c,0x120046dd4,0x120047230]
out=[C.scan(c,3,start=c+8) for c in calls]
for o in out: print(o['site'],o['steps'],o['flags'][:3],o['safeReads'],o['events'])
json.dump(out,open('ret_callers.json','w'),indent=1)
