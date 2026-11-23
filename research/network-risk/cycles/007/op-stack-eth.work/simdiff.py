import sys, gzip, time; sys.path.insert(0,'.')
from lib import *
STUB='0x3660409003806040600037600060008260006020356000355af16000523d600060203e3d6020016000f3'
READER='0x5f5b8036111560145780355481526020016001565b365ff3'
SINK='0x00000000000000000000000000000000005141c0'; EOA='0x00000000000000000000000000000000000a11ce'
def pad(a):
    if isinstance(a,int): a=hex(a)
    return a.lower().replace('0x','').rjust(64,'0')
def fwd(token,payload): return '0x'+pad(token)+pad(0)+payload
def diff(url,pm,token,bal,roundtrip=True):
    out_leg='a9059cbb'+pad(SINK)+pad(bal)
    al=rpc(url,'eth_createAccessList',[{'from':pm,'to':token,'data':'0x'+out_leg},'latest'])
    if 'result' not in al: return {'err':'accessList '+json.dumps(al)[:160]}
    acl=[(e['address'].lower(),e['storageKeys']) for e in al['result'].get('accessList',[]) if e['storageKeys']]
    if al['result'].get('error'): return {'err':'accessList exec '+str(al['result']['error'])[:120]}
    before={}
    for a,keys in acl:
        for k in keys:
            before[(a,k)]=rpc(url,'eth_getStorageAt',[a,k,'latest']).get('result')
    calls=[{'from':EOA,'to':pm,'data':fwd(token,out_leg)}]
    if roundtrip: calls.append({'from':EOA,'to':SINK,'data':fwd(token,'a9059cbb'+pad(pm)+pad(bal))})
    b2ov={a:{'code':READER} for a,_ in acl}
    b2calls=[{'from':EOA,'to':a,'data':'0x'+''.join(k[2:] for k in keys)} for a,keys in acl]
    req={'blockStateCalls':[{'stateOverrides':{pm:{'code':STUB},SINK:{'code':STUB}},'calls':calls},{'stateOverrides':b2ov,'calls':b2calls}]}
    r=rpc(url,'eth_simulateV1',[req,'latest'],timeout=40)
    if 'result' not in r: return {'err':'sim '+json.dumps(r)[:200]}
    res=r['result']
    ok=[c.get('returnData','0x')[2:66] for c in res[0]['calls']]
    legs=[(int(x,16) if x else None) for x in ok]
    changed={}
    for (a,keys),c in zip(acl,res[1]['calls']):
        rd=c.get('returnData','0x')[2:]
        for i,k in enumerate(keys):
            after='0x'+rd[i*64:(i+1)*64]
            if after!=before[(a,k)]: changed[f'{a}:{k}']=(before[(a,k)],after)
    return {'legs':legs,'nSlots':len(before),'accounts':[a for a,_ in acl],'changed':changed}
if __name__=='__main__':
    chain=int(sys.argv[1]); url=sys.argv[2]; budget=float(sys.argv[3])
    pm=PM[chain]
    d=json.load(gzip.open(f'../../004/theme-balance-reconcile.work/raw/currencies_{chain}.json.gz'))
    toks=[t['address'] for t in d.get('scout',[])]+[a for a in d.get('currencies',{}) if a!='0x'+'0'*40]
    seen=[]; [seen.append(t.lower()) for t in toks if t.lower() not in seen]
    out={}; t0=time.time(); n=0
    for t in seen:
        if time.time()-t0>budget: break
        b=call(url,t,'0x70a08231'+pad(pm))
        if 'result' not in b or len(b['result'])<66: out[t]={'bal':None}; continue
        bal=int(b['result'][:66],16)
        if bal==0: out[t]={'bal':0}; continue
        out[t]={'bal':bal,'round':diff(url,pm,t,bal,True),'oneway':diff(url,pm,t,bal,False)}; n+=1
    json.dump(out,open(f'raw/simdiff_{chain}.json','w'))
    print('tokens tested',n,'of',len(seen),'elapsed',int(time.time()-t0))
