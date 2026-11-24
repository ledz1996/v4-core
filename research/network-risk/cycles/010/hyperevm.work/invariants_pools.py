"""L-602 on HyperEVM: run the checks of invariants.py (I1 to I4) over the 344 pool ids that cycle 7 collected
(cycles/007/hyperevm.work/raw/pools.json), because the recent log window of invariants.py holds no PoolManager log.
Read only: eth_call to extsload and to PositionManager.poolKeys, and eth_getStorageAt.
Usage: python3 invariants_pools.py <out.json> [maxPools]"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import invariants as I
from evm import rpc

if __name__ == '__main__':
    out = sys.argv[1]; maxp = int(sys.argv[2]) if len(sys.argv) > 2 else 400
    n = I.nets[999]; url = n['rpc']; pm = n['poolManager']; posm = n['contracts']['PositionManager']
    root = __file__.rsplit('/', 4)[0]
    pids = [p[0] for p in json.load(open(root + '/cycles/007/hyperevm.work/raw/pools.json'))['pools']]
    head = int(rpc(url, 'eth_blockNumber', []), 16); block = 'latest'
    res = []; skipped = 0
    for pid in pids[:maxp]:
        k = I.pool_key(url, posm, pid, block)
        if not k: skipped += 1; continue
        try:
            r = I.check_pool(url, pm, pid, k['tickSpacing'], block, 2 if len(res) < 60 else 0)
        except Exception as e:  # noqa
            print('ERR', pid, str(e)[:100], flush=True); skipped += 1; continue
        r['key'] = k; res.append(r)
        if r['violations']: print('VIOLATION', pid, r['violations'][:3], flush=True)
    summary = {'chainId': 999, 'blockAtStart': head, 'poolsSeen': len(pids), 'poolsChecked': len(res), 'skipped': skipped,
               'initializedTicks': sum(r['initializedTicks'] for r in res), 'bitmapWords': sum(r['words'] for r in res),
               'negativeTickPools': sum(1 for r in res if r['tick'] < 0),
               'getStorageAtCompared': sum(len(r['getStorageAt']) for r in res),
               'getStorageAtSlotsNearPageEdge': sum(1 for r in res for g in r['getStorageAt'] if g['offsetInPage'] >= 125),
               'violations': sum(len(r['violations']) for r in res)}
    print(json.dumps(summary), flush=True)
    json.dump({'summary': summary, 'pools': res}, open(out, 'w'), indent=1)
