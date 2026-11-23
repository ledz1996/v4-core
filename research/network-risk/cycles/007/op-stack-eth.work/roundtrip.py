import sys, gzip, time; sys.path.insert(0,'.')
from lib import *
STUB='0x3660409003806040600037600060008260006020356000355af16000523d600060203e3d6020016000f3'
BATCH='0x5f5b80361115602f57803560601c8160140135'+'60f01c'+'80836016015f37'+'5f5f825f5f865af1'+'50'+'9050'+'01601601'+'600156'+'5b00'
X='0x00000000000000000000000000000000000ba7c4'; SINK='0x00000000000000000000000000000000005141c0'
def pad(a):
    if isinstance(a,int): a=hex(a)
    return a.lower().replace('0x','').rjust(64,'0')
def rec(stub,token,payload):
    inner=pad(token)+pad(0)+payload
    return stub[2:].lower()+format(len(inner)//2,'04x')+inner
def trace(url,pm,token,bal,roundtrip=True):
    data=rec(pm,token,'a9059cbb'+pad(SINK)+pad(bal))
    if roundtrip: data+=rec(SINK,token,'a9059cbb'+pad(pm)+pad(bal))
    ov={pm:{'code':STUB},SINK:{'code':STUB},X:{'code':BATCH}}
    tx={'from':'0x00000000000000000000000000000000000a11ce','to':X,'data':'0x'+data,'gas':hex(8_000_000)}
    return rpc(url,'debug_traceCall',[tx,'latest',{'tracer':'prestateTracer','tracerConfig':{'diffMode':True},'stateOverrides':ov}],timeout=40)
def analyse(r,token,pm):
    if 'result' not in r: return {'err':json.dumps(r)[:200]}
    pre,post=r['result'].get('pre',{}),r['result'].get('post',{})
    changed={}
    for a,v in post.items():
        st=v.get('storage',{})
        if st: changed[a]={k:(pre.get(a,{}).get('storage',{}).get(k),val) for k,val in st.items()}
    # slots present in pre but deleted (set to zero) in post
    for a,v in pre.items():
        for k,val in v.get('storage',{}).items():
            if a in post and 'storage' in post[a] and k in post[a]['storage']: continue
            # prestate diff mode lists pre slots that changed; if not in post => became zero
            changed.setdefault(a,{})[k]=(val,'0x0(deleted)')
    return {'changed':changed}
if __name__=='__main__':
    chain=int(sys.argv[1]); url=sys.argv[2]; limit=int(sys.argv[3]); budget=float(sys.argv[4])
    pm=PM[chain]
    d=json.load(gzip.open(f'../../004/theme-balance-reconcile.work/raw/currencies_{chain}.json.gz'))
    toks=[t['address'] for t in d.get('scout',[])]+[a for a in d.get('currencies',{}) if a!='0x'+'0'*40]
    seen=[]; [seen.append(t.lower()) for t in toks if t.lower() not in seen]
    out={}; t0=time.time(); n=0
    for t in seen[:limit]:
        if time.time()-t0>budget: break
        b=call(url,t,'0x70a08231'+pad(pm))
        if 'result' not in b or len(b['result'])<66: out[t]={'bal':None}; continue
        bal=int(b['result'][:66],16)
        if bal==0: out[t]={'bal':0}; continue
        rt=analyse(trace(url,pm,t,bal,True),t,pm); ow=analyse(trace(url,pm,t,bal,False),t,pm)
        out[t]={'bal':bal,'round':rt,'oneway':ow}; n+=1
        time.sleep(0.15)
    json.dump(out,open(f'raw/roundtrip_{chain}.json','w'))
    print('tokens traced',n,'of',len(seen),'elapsed',int(time.time()-t0))
