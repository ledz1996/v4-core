from lib import *
import concurrent.futures as cf
head=int(rpc('eth_blockNumber',[],url=ARCH),16)
START=45998366
TOP={'Initialize':'0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438'}
def get(a):
    b=min(a+99999,head)
    return rpc('eth_getLogs',[{'fromBlock':hex(a),'toBlock':hex(b),'address':PM}],url=ARCH)
logs=[]
with cf.ThreadPoolExecutor(5) as ex:
    for L in ex.map(get,range(START,head+1,100000)): logs+=L
print('all PoolManager logs',len(logs),'head',head)
json.dump({'head':head,'logs':logs},open('raw/pm_logs.json','w'))
by={}
for l in logs: by[l['topics'][0]]=by.get(l['topics'][0],0)+1
print(by)
cur=set(); pools=[]
for l in logs:
    if l['topics'][0]==TOP['Initialize']:
        c0='0x'+l['topics'][2][-40:]; c1='0x'+l['topics'][3][-40:]; cur|={c0,c1}; pools.append((l['topics'][1],c0,c1))
print('pools',len(pools),'currencies',len(cur))
json.dump({'pools':pools,'currencies':sorted(cur)},open('raw/pools.json','w'))
