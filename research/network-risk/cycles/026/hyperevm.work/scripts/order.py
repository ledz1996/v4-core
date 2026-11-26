"""Read-only: fetch recent HyperEVM blocks and record transaction order against gas price, type and sender.
Usage: python3 -I order.py <rpc> <nblocks> <out.json>"""
import sys, json, urllib.request
rpc, n, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
def rq(b):
    r=urllib.request.Request(rpc,data=json.dumps(b).encode(),headers={'content-type':'application/json','user-agent':'research-client'})
    return json.load(urllib.request.urlopen(r,timeout=60))
head=int(rq({"jsonrpc":"2.0","id":1,"method":"eth_blockNumber","params":[]})['result'],16)
cv=rq({"jsonrpc":"2.0","id":1,"method":"web3_clientVersion","params":[]})['result']
blocks=[]
for s in range(head-n, head, 10):
    res=rq([{"jsonrpc":"2.0","id":k,"method":"eth_getBlockByNumber","params":[hex(k),True]} for k in range(s,min(s+10,head))])
    for x in res:
        b=x.get('result')
        if not b: continue
        bf=int(b.get('baseFeePerGas','0x0'),16)
        txs=[]
        for t in b['transactions']:
            gp=int(t.get('gasPrice','0x0'),16); mp=int(t.get('maxPriorityFeePerGas',t.get('gasPrice','0x0')),16); mf=int(t.get('maxFeePerGas',t.get('gasPrice','0x0')),16)
            tip=min(mp, mf-bf) if t.get('type') in ('0x2',) else gp-bf
            txs.append({'from':t['from'],'nonce':int(t['nonce'],16),'type':t.get('type'),'gasPrice':gp,'tip':tip,'gas':int(t['gas'],16)})
        blocks.append({'number':int(b['number'],16),'gasLimit':int(b['gasLimit'],16),'gasUsed':int(b['gasUsed'],16),'baseFee':bf,'txs':txs})
desc=0; notdesc=0; multi=0; samesender_inorder=0; samesender_out=0
for b in blocks:
    t=b['txs']
    if len(t)<2: continue
    multi+=1
    tips=[x['tip'] for x in t]
    if all(tips[i]>=tips[i+1] for i in range(len(tips)-1)): desc+=1
    else: notdesc+=1
    last={}
    for x in t:
        if x['from'] in last:
            if x['nonce']>last[x['from']]: samesender_inorder+=1
            else: samesender_out+=1
        last[x['from']]=x['nonce']
summ={'client':cv,'head':head,'blocks':len(blocks),'multiTxBlocks':multi,'tipNonIncreasing':desc,'tipNotSorted':notdesc,'sameSenderInNonceOrder':samesender_inorder,'sameSenderOutOfOrder':samesender_out,
 'gasLimits':sorted(set(b['gasLimit'] for b in blocks))}
print(json.dumps(summ))
json.dump({'summary':summ,'blocks':blocks},open(out,'w'))
