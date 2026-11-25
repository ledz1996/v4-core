import json,glob
R={}
for f in glob.glob('raw/sweep_*.json'):
    if 'summary' in f or 'all' in f: continue
    R.update(json.load(open(f)))
def fmt(x):
    if isinstance(x,str): return 'ok:%dB%s'%((len(x)-2)//2,':2a' if x.endswith('2a') and len(x)==66 else (':'+x[:14] if len(x)>2 else ''))
    if isinstance(x,dict) and 'httperror' in x: return 'HTTP%s'%x['httperror']
    if isinstance(x,dict): return 'ERR:'+str(x.get('message'))[:40]+(':'+str(x.get('data'))[:12] if x.get('data') else '')
    return str(x)
for cid in sorted(R,key=int):
    ov=R[cid]['override']
    print('==',cid, '| direct:',{a[-8:]:(fmt(v['call']),fmt(v['estimateGas'])) for a,v in R[cid]['direct'].items()})
    for a,v in ov.items():
        print('   ',a,fmt(v['noOverride']),'|',fmt(v['stubOverride']))
