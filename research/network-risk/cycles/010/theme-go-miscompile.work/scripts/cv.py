import json,subprocess,sys,collections,time
eps=[(1,'https://ethereum-rpc.publicnode.com'),(10,'https://mainnet.optimism.io'),(8453,'https://mainnet.base.org/'),(130,'https://mainnet.unichain.org'),(7777777,'https://rpc.zora.energy/'),(480,'https://worldchain-mainnet.g.alchemy.com/public'),(57073,'https://rpc-gel.inkonchain.com'),(1868,'https://rpc.soneium.org'),(42220,'https://forno.celo.org'),(196,'https://rpc.xlayer.tech'),(42161,'https://arb1.arbitrum.io/rpc'),(4663,'https://rpc.mainnet.chain.robinhood.com'),(99901,'https://rpc.elysium.kinetiq.xyz'),(137,'https://polygon.drpc.org'),(137,'https://polygon-bor-rpc.publicnode.com'),(137,'https://polygon-rpc.com'),(56,'https://bsc-dataseed1.bnbchain.org'),(56,'https://bsc-dataseed2.bnbchain.org'),(56,'https://bsc-dataseed.bnbchain.org'),(56,'https://bsc-rpc.publicnode.com'),(43114,'https://api.avax.network/ext/bc/C/rpc'),(43114,'https://avalanche-c-chain-rpc.publicnode.com'),(143,'https://rpc.monad.xyz'),(4326,'https://mainnet.megaeth.com/rpc'),(4217,'https://rpc.mainnet.tempo.xyz'),(5042,'https://rpc.mainnet.arc.io'),(999,'https://rpc.hyperliquid.xyz/evm')]
N=int(sys.argv[1]) if len(sys.argv)>1 else 6
out={}
for cid,u in eps:
    c=collections.Counter()
    for i in range(N):
        body=json.dumps([{"jsonrpc":"2.0","id":1,"method":"web3_clientVersion","params":[]},{"jsonrpc":"2.0","id":2,"method":"eth_blockNumber","params":[]}])
        r=subprocess.run(['curl','-s','-m','15','-H','Content-Type: application/json','--data',body,u],capture_output=True,text=True)
        try:
            j=json.loads(r.stdout); j=j if isinstance(j,list) else [j]
            v=[x for x in j if x.get('id')==1][0]
            c[v.get('result') or json.dumps(v.get('error'))[:80]]+=1
        except Exception as e: c['ERR '+r.stdout[:80]]+=1
    out[f'{cid} {u}']=dict(c); print(cid,u,dict(c),flush=True)
json.dump({'queried':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'results':out},open('/home/user/v4-core/research/network-risk/cycles/010/theme-go-miscompile.work/clientversions.json','w'),indent=1)
