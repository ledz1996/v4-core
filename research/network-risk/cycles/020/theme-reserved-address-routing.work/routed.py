import json
S=json.load(open('raw/sweep_summary.json'))
R={}
import glob
for f in glob.glob('raw/sweep_*.json'):
    if 'summary' in f or 'all' in f: continue
    R.update(json.load(open(f)))
def H(x): return '0x'+('%x'%x).rjust(40,'0')
res={}
for cid,r in R.items():
    s=r['sweep']; cold=S[cid]['coldEmpty']
    nat=[i for i in range(1,0x200) if s[H(i)]!=cold]
    runs=[]
    for i in nat:
        if runs and i==runs[-1][1]+1: runs[-1][1]=i
        else: runs.append([i,i])
    res[cid]=' '.join(('%#x-%#x'%(a,b) if a!=b else '%#x'%a) for a,b in runs)
    print(cid, res[cid])
json.dump(res,open('raw/routed_low.json','w'),indent=1)
