"""Read-only sweep: eth_call from the PoolManager address to standard precompiles with the three call shapes
the PoolManager issues (P1 empty calldata with value, P2 transfer(address,uint256), P3 balanceOf(PoolManager)).
Usage: python3 -I pcsweep.py <rpc> <out.json>"""
import sys, json, urllib.request
rpc, out = sys.argv[1], sys.argv[2]
PM = '0x12d4fd9c5dedd00ab8a0bce2cf0167bbf94b6b1f'
def call(obj, i):
    return {"jsonrpc":"2.0","id":i,"method":"eth_call","params":[obj,"latest"]}
addrs = list(range(1, 0x14)) + [0x100]
shapes = {
 'P1_value_1wei': lambda a: {"from":PM,"to":a,"value":"0x1","gas":"0x1c9c380"},
 'P1_zero': lambda a: {"from":PM,"to":a,"gas":"0x1c9c380"},
 'P2_transfer_1': lambda a: {"from":PM,"to":a,"gas":"0x1c9c380","data":"0xa9059cbb"+"00"*12+"1111111111111111111111111111111111111111"+"%064x"%1},
 'P2_transfer_0': lambda a: {"from":PM,"to":a,"gas":"0x1c9c380","data":"0xa9059cbb"+"00"*12+"1111111111111111111111111111111111111111"+"%064x"%0},
 'P3_balanceOf': lambda a: {"from":PM,"to":a,"gas":"0x1c9c380","data":"0x70a08231"+"00"*12+PM[2:]},
}
reqs=[]; meta=[]
reqs.append({"jsonrpc":"2.0","id":0,"method":"web3_clientVersion","params":[]})
reqs.append({"jsonrpc":"2.0","id":1,"method":"eth_blockNumber","params":[]})
i=2
for a in addrs:
    ah='0x%040x'%a
    for k,f in shapes.items():
        reqs.append(call(f(ah),i)); meta.append((ah,k,i)); i+=1
res={}
for j in range(0,len(reqs),20):
    body=json.dumps(reqs[j:j+20]).encode()
    r=urllib.request.Request(rpc,data=body,headers={'content-type':'application/json','user-agent':'research-client'})
    for x in json.load(urllib.request.urlopen(r,timeout=60)): res[x['id']]=x
rows=[]
for ah,k,i in meta:
    x=res.get(i,{})
    rows.append({'addr':ah,'shape':k,'result':x.get('result'),'error':x.get('error')})
json.dump({'rpc':rpc,'client':res[0].get('result'),'block':res[1].get('result'),'rows':rows},open(out,'w'),indent=1)
for r in rows: print(r['addr'][-4:],r['shape'],(r['result'] or '')[:70], (r['error'] or {}).get('message','') if r['error'] else '')
