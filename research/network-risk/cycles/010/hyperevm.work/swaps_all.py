"""Lead L-581 and angle 1 on HyperEVM: the whole Swap and ModifyLiquidity history of the PoolManager since its
deployment (cycle 7 put the first PoolManager log after block 45,998,366), read from the archive endpoint
rpc.purroofgroup.com (nanoreth), and checked with the relations of tools/opdiff/swaps.py (tick relation and
single-step amounts). Adds a census of the ticks: negative ticks, ticks within 2^16 of MIN_TICK or MAX_TICK.
Read only (eth_getLogs). Usage: python3 swaps_all.py <out.json> [fromBlock]"""
import sys, os, json, time
sys.path.insert(0, __file__.rsplit('/', 4)[0] + '/tools/opdiff')
import swaps as SW
from evm import rpc

URL = 'https://rpc.purroofgroup.com'
PM = '0x12D4Fd9C5DeDd00ab8a0bCe2CF0167bbf94b6B1F'


def collect_all(url, pm, start):
    head = int(rpc(url, 'eth_blockNumber', []), 16) - 2
    lo = start; span = 20000; logs = []
    while lo <= head:
        hi = min(head, lo + span - 1)
        for k in range(6):
            try:
                part = SW.get_logs(url, pm, lo, hi); break
            except Exception as e:  # noqa
                if 'range' in str(e).lower() or 'limit' in str(e).lower() or 'too many' in str(e).lower():
                    span = max(500, span // 2); hi = min(head, lo + span - 1)
                time.sleep(2 * (k + 1))
        else:
            raise RuntimeError('logs failed at %d' % lo)
        logs += part; lo = hi + 1
    return logs, start, head


if __name__ == '__main__':
    out = sys.argv[1]; start = int(sys.argv[2]) if len(sys.argv) > 2 else 45_990_000
    logs, lo, head = collect_all(URL, PM, start)
    print('logs', len(logs), 'blocks', lo, head, flush=True)
    SW.collect = lambda url, pm: (logs, lo, head)
    res = SW.run((999, 'HyperEVM', URL, PM))
    ticks = []
    for lg in logs:
        if lg['topics'][0] != SW.SWAP: continue
        t = SW.word(lg['data'], 4) & 0xffffff
        ticks.append(t - (1 << 24) if t >> 23 else t)
    res['tickCensus'] = {'swaps': len(ticks), 'negative': sum(1 for t in ticks if t < 0),
                         'nearMin': sum(1 for t in ticks if t < -887272 + 65536), 'nearMax': sum(1 for t in ticks if t > 887272 - 65536),
                         'min': min(ticks) if ticks else None, 'max': max(ticks) if ticks else None,
                         'modifyLiquidityLogs': sum(1 for lg in logs if lg['topics'][0] == SW.MODIFY),
                         'firstLogBlock': int(logs[0]['blockNumber'], 16) if logs else None}
    print(json.dumps({k: v for k, v in res.items() if k not in ('multiSamples', 'otherSamples')}), flush=True)
    json.dump(res, open(out, 'w'), indent=1)
