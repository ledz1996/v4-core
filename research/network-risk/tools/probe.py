import json,sys,re,hashlib,urllib.request,ssl,concurrent.futures as cf
DL=sys.argv[1]
txt=open(DL+'/deployments.txt').read()
nets=[]
main=txt.split('## Testnet Deployments')[0]
for m in re.finditer(r'## ([^\n:]+): (\d+)\nContract \| Address\n(.*?)(?=\n\n## |\Z)',main,flags=re.S):
    rows=dict(r.split(' | ') for r in m.group(3).strip().split('\n') if ' | ' in r)
    nets.append({'name':m.group(1).strip(),'chainId':int(m.group(2)),'contracts':rows})
chains={c['chainId']:c for c in json.load(open(DL+'/chains.json'))}
extra={1:['https://ethereum-rpc.publicnode.com'],42220:['https://forno.celo.org'],130:['https://mainnet.unichain.org'],999:['https://rpc.hyperliquid.xyz/evm']}
ctx=ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
def rpc(url,method,params):
    req=urllib.request.Request(url,data=json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params}).encode(),headers={'content-type':'application/json','user-agent':'curl/8'})
    with urllib.request.urlopen(req,timeout=15,context=ctx) as r:
        j=json.load(r)
    if 'error' in j: raise Exception(str(j['error'])[:80])
    return j['result']
def probe(n):
    cid=n['chainId']; c=chains.get(cid,{})
    urls=extra.get(cid,[])+[u for u in c.get('rpc',[]) if u.startswith('https') and '${' not in u]
    pm=n['contracts']['PoolManager']
    out={'name':n['name'],'chainId':cid,'poolManager':pm,'nativeSymbol':c.get('nativeCurrency',{}).get('symbol'),'nativeDecimals':c.get('nativeCurrency',{}).get('decimals'),'rpcTried':len(urls)}
    for u in urls[:8]:
        try:
            if int(rpc(u,'eth_chainId',[]),16)!=cid: continue
            code=rpc(u,'eth_getCode',[pm,'latest'])
            b=bytes.fromhex(code[2:])
            out.update(rpc=u,codeLen=len(b),codeSha256=hashlib.sha256(b).hexdigest()[:16])
            # mask immutables: replace occurrences of own address
            masked=b.replace(bytes.fromhex(pm[2:].lower().rjust(40,'0')),b'\x00'*20)
            out['maskedSha256']=hashlib.sha256(masked).hexdigest()[:16]
            out['selfAddrOccurrences']=b.count(bytes.fromhex(pm[2:]))
            out['owner']='0x'+rpc(u,'eth_call',[{'to':pm,'data':'0x8da5cb5b'},'latest'])[-40:]
            out['protocolFeeController']='0x'+rpc(u,'eth_call',[{'to':pm,'data':'0xf02de3b2'},'latest'])[-40:]
            try: out['ownerCodeLen']=(len(rpc(u,'eth_getCode',[out['owner'],'latest']))-2)//2
            except Exception as e: pass
            try: out['pfcCodeLen']=(len(rpc(u,'eth_getCode',[out['protocolFeeController'],'latest']))-2)//2
            except Exception as e: pass
            try:
                blk=rpc(u,'eth_getBlockByNumber',['latest',False])
                out['blockGasLimit']=int(blk['gasLimit'],16); out['blockNumber']=int(blk['number'],16)
                out['hasBaseFee']='baseFeePerGas' in blk; out['hasBlobFields']='blobGasUsed' in blk
                out['extraBlockFields']=sorted(set(blk.keys())-set('hash parentHash sha3Uncles miner stateRoot transactionsRoot receiptsRoot logsBloom difficulty number gasLimit gasUsed timestamp extraData mixHash nonce baseFeePerGas withdrawalsRoot blobGasUsed excessBlobGas parentBeaconBlockRoot requestsHash size totalDifficulty transactions uncles withdrawals'.split()))
            except Exception as e: out['blkErr']=str(e)[:60]
            break
        except Exception as e:
            out.setdefault('errors',[]).append(u.split('/')[2]+': '+str(e)[:50])
    return out
with cf.ThreadPoolExecutor(12) as ex: res=list(ex.map(probe,nets))
json.dump({"networks":nets,"probe":res},open(sys.argv[2],"w"),indent=1)
for r in res:
    print(f"{r['name']:16} {r['chainId']:>8} native={r.get('nativeSymbol')}/{r.get('nativeDecimals')} len={r.get('codeLen')} sha={r.get('codeSha256')} masked={r.get('maskedSha256')} self#={r.get('selfAddrOccurrences')} owner={r.get('owner')}({r.get('ownerCodeLen')}) pfc={r.get('protocolFeeController')}({r.get('pfcCodeLen')}) gasLimit={r.get('blockGasLimit')} extra={r.get('extraBlockFields')} {'' if r.get('rpc') else 'NO RPC '+str(r.get('errors'))[:200]}")
