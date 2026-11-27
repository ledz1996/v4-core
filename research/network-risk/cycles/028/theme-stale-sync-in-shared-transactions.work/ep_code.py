# eth_getCode of EntryPoint v0.6 to v0.9 and Multicall3 on all 21 networks, bracketed by web3_clientVersion.
import sys, os, json, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from config import CFG
A = {'EPv06': '0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789', 'EPv07': '0x0000000071727De22E5E9d8BAf0edAc6f37da032', 'EPv08': '0x4337084D9E255Ff0702461CF8895CE9E3b5Ff108', 'EPv09': '0x433709009B8330FDa32311DF1C2AFA402eD8D009', 'Multicall3': MC3}
def one(n):
    for u in [n['rpc']] + CFG[n['chainId']]['state']:
        try:
            r = dict(chainId=n['chainId'], name=n['name'], url=u, clientBefore=rpc(u, 'web3_clientVersion', []))
            for k, a in A.items(): r[k] = len(rpc(u, 'eth_getCode', [a, 'latest'])) // 2 - 1
            r['clientAfter'] = rpc(u, 'web3_clientVersion', []); return r
        except Exception as e: last = str(e)[:120]
    return dict(chainId=n['chainId'], err=last)
with cf.ThreadPoolExecutor(7) as ex: res = list(ex.map(one, NETS))
json.dump(res, open('out/ep_code.json', 'w'), indent=1)
for r in res: print(r['chainId'], r.get('name'), [r.get(k) for k in A], r.get('clientBefore', '')[:40], r.get('err', ''))
