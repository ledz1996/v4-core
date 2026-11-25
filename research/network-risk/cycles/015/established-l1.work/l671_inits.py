import json, urllib.request, time
T0='0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438'
d=json.load(open('raw_l671_pools.json'))
pids=sorted({p for k,v in d.items() if k!='initInTx' for p in v['pools']})
keys={}
for p in pids:
    u=f'https://api.routescan.io/v2/network/mainnet/evm/43114/etherscan/api?module=logs&action=getLogs&address=0x06380c0e0912312b5150364b9dc4542ba0dbbc85&topic0={T0}&topic1={p}&topic0_1_opr=and&fromBlock=0&toBlock=latest'
    r=json.load(urllib.request.urlopen(urllib.request.Request(u,headers={'user-agent':'curl/8'}),timeout=60))
    for x in r.get('result') or []:
        dd=x['data']; w=[int(dd[2+64*i:66+64*i],16) for i in range(3)]
        sp=w[1]-(1<<256) if w[1]>>255 else w[1]
        keys[x['topics'][1]]={'c0':'0x'+x['topics'][2][26:],'c1':'0x'+x['topics'][3][26:],'fee':w[0],'spacing':sp,'hooks':'0x%040x'%w[2],'block':int(x['blockNumber'],16),'tx':x['transactionHash']}
    print(p, keys.get(p)); time.sleep(1)
json.dump(keys,open('raw/inits-43114.json','w'),indent=1)
json.dump([k for k in d if k!='initInTx'],open('raw/l671_only.json','w'))
