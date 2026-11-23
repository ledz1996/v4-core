from sweep_read import *
def trace(target,data,kind,v1=10**15,v2=0,url=ARCH):
    m,p=req(target,data,kind,v_pm_to_a=v1,v_a_to_t=v2)
    call,blk,ov=p
    r=rpc('debug_traceCall',[call,blk,{'tracer':'callTracer','tracerConfig':{'withLog':True},'stateOverrides':ov}],url=url,raw=True)
    return r
def walk(c,depth=0,out=None):
    out=[] if out is None else out
    out.append('  '*depth+f"{c.get('type')} from={c.get('from')} to={c.get('to')} value={c.get('value')} err={c.get('error')} out={(c.get('output') or '')[:74]}")
    for l in c.get('logs',[]): out.append('  '*depth+f"   LOG address={l['address']} topics={l['topics']} data={l['data'][:140]}")
    for s in c.get('calls',[]): walk(s,depth+1,out)
    return out
if __name__=='__main__':
    raw_action='17938e13'+w(32)+w(4+96)+'01000006'+w(0xdead)+w(150)+w(1)+'00'*28  # sendRawAction(bytes) with a spot send shaped payload
    res={}
    for name,t,d in [('bridge','0x2222222222222222222222222222222222222222',''),('corewriter','0x3333333333333333333333333333333333333333',raw_action)]:
        for k in range(4):
            for v2 in ((0,7) if k in (0,3) else (0,)):
                r=trace(t,d,k,v2=v2)
                key=f'{name}:{KINDS[k]}:v{v2}'; res[key]=r
                print('==',key)
                if 'error' in r: print('  ERR',r['error']); continue
                print('\n'.join(walk(r['result'])))
    json.dump(res,open('raw/trace_sys_contracts.json','w'))
