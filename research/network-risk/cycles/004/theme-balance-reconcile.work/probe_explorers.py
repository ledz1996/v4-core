# Check which Blockscout style explorers serve the token holdings page of the PoolManager.
import json, requests, concurrent.futures as cf
from lib import *
EXP = {1:['https://eth.blockscout.com'],10:['https://optimism.blockscout.com','https://explorer.optimism.io'],8453:['https://base.blockscout.com'],130:['https://unichain.blockscout.com'],
 7777777:['https://explorer.zora.energy'],480:['https://worldchain-mainnet.explorer.alchemy.com','https://worldscan.org'],57073:['https://explorer.inkonchain.com'],1868:['https://soneium.blockscout.com'],
 42220:['https://celo.blockscout.com'],196:['https://xlayer.blockscout.com','https://www.oklink.com/xlayer'],42161:['https://arbitrum.blockscout.com'],4663:['https://explorer.mainnet.chain.robinhood.com','https://robinhood.blockscout.com'],
 99901:['https://explorer.elysium.kinetiq.xyz','https://elysium.blockscout.com'],137:['https://polygon.blockscout.com'],56:['https://bsc.blockscout.com'],43114:['https://avalanche.blockscout.com'],
 143:['https://monad.blockscout.com','https://monadexplorer.com','https://explorer.monad.xyz'],4326:['https://megaeth.blockscout.com','https://www.megaexplorer.xyz'],4217:['https://explore.tempo.xyz','https://explore.mainnet.tempo.xyz'],
 5042:['https://arcscan.app','https://explorer.arc.io','https://explorer.mainnet.arc.io'],999:['https://www.hyperscan.com','https://hyperevm.blockscout.com']}
def f(a):
    cid,u=a; pm=net(cid)['poolManager']
    try:
        r=requests.get(u+'/api/v2/addresses/'+pm+'/tokens?type=ERC-20',timeout=20,headers={'user-agent':'curl/8'})
        if r.status_code!=200: return (cid,u,'http %d'%r.status_code)
        j=r.json(); return (cid,u,'OK',len(j.get('items',[])),json.dumps(j.get('next_page_params'))[:120], [ (i['token'].get('symbol'), i['token'].get('exchange_rate')) for i in j['items'][:4]])
    except Exception as e: return (cid,u,'ERR '+repr(e)[:80])
with cf.ThreadPoolExecutor(20) as ex:
    res=list(ex.map(f,[(c,u) for c,us in EXP.items() for u in us]))
json.dump(res,open('raw/explorers.json','w'),indent=1)
for r in res: print(r)
