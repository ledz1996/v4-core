"""BNB Smart Chain: per block, native value into and out of the PoolManager in the call frames of every
PoolManager transaction of the block, against the balance difference. Read-only.
Usage: bsc_block_native.py <block> [<block> ...]"""
import sys, json, time
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import rpc
PM = '0x28e2ea090877bf75740558f6bfb36a5ffee9e9df'; TR = 'https://bsc-mainnet.nodereal.io/v1/64a9df0874fb4a93b9d0a3849de012d3'
out = []
for b in map(int, sys.argv[1:]):
    blk = rpc('https://bsc-rpc.publicnode.com', 'eth_getBlockByNumber', [hex(b), True], timeout=60)
    tot = [0, 0]; per = {}
    pmtx = {l['transactionHash'] for l in rpc('https://bsc-rpc.publicnode.com', 'eth_getLogs', [{'address': PM, 'fromBlock': hex(b), 'toBlock': hex(b)}])}
    blk['transactions'] = [x for x in blk['transactions'] if x['hash'] in pmtx]
    for tx in blk['transactions']:
        for k in range(10):
            try: t = rpc(TR, 'debug_traceTransaction', [tx['hash'], {'tracer': 'callTracer'}], timeout=60); break
            except Exception: time.sleep(3 + 3 * k)
        time.sleep(1)
        acc = [0, 0]
        def walk(c, ok):
            ok = ok and not c.get('error'); v = int(c.get('value') or '0x0', 16)
            if ok and v and c.get('type') in ('CALL', 'CREATE', 'CREATE2', 'SELFDESTRUCT', 'CALLCODE'):
                if (c.get('from') or '').lower() == PM: acc[0] += v
                if (c.get('to') or '').lower() == PM: acc[1] += v
            for k in c.get('calls') or []: walk(k, ok)
        walk(t, True)
        if acc != [0, 0]: per[tx['hash']] = [str(acc[0]), str(acc[1])]
        tot[0] += acc[0]; tot[1] += acc[1]
    bd = int(rpc('https://bsc.rpc.sentio.xyz', 'eth_getBalance', [PM, hex(b)]), 16) - int(rpc('https://bsc.rpc.sentio.xyz', 'eth_getBalance', [PM, hex(b - 1)]), 16)
    out.append({'block': b, 'txsTraced': len(blk['transactions']), 'perTx': per, 'out': str(tot[0]), 'in': str(tot[1]), 'balanceDiff': str(bd), 'diff': str(bd - (tot[1] - tot[0]))})
    print(json.dumps(out[-1]))
json.dump(out, open('raw/bsc-block-native.json', 'w'), indent=1)
