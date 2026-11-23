# Full history: ERC-20 Transfer logs whose sender is the PoolManager and whose recipient is the zero address or a
# burn address. A take to such an address inside a swap is ordinary. A hit in a transaction where the PoolManager
# emitted no event at all means the token moved the PoolManager's balance by itself.
# usage: python3 scan_burns.py <chainId>
import sys, json, gzip, threading
from lib import *
from config import CFG
from fetch import getlogs_range
from scan_mints import SCAN, block_at
DEAD = ['0x' + '0' * 64, pad_addr('0x000000000000000000000000000000000000dead'), pad_addr('0xdead000000000000000042069420694206942069'), pad_addr('0x0000000000000000000000000000000000000001')]
def main():
    cid = int(sys.argv[1]); n = net(cid); pm = n['poolManager']; c = dict(CFG[cid]); u = c['logs']
    if len(sys.argv) > 4: u = sys.argv[4]
    head = int(rpc(u, 'eth_blockNumber', []), 16)
    first = SCAN[cid][3]
    lo = int(sys.argv[2]) if len(sys.argv) > 2 else (first if first is not None else block_at(SCAN[cid][0], 1735689600, head))
    rows = []; lock = threading.Lock()
    def on(logs):
        with lock:
            for l in logs:
                if len(l['topics']) == 3 and len(l['data']) == 66:
                    rows.append([int(l['blockNumber'], 16), l['transactionHash'], l['address'].lower(), '0x' + l['topics'][2][-40:], str(int(l['data'], 16))])
    chunk = int(sys.argv[3]) if len(sys.argv) > 3 else max(c['chunk'], c.get('initChunk') or 0)
    st = getlogs_range(u, {'topics': [TRANSFER, pad_addr(pm), DEAD]}, lo, head, chunk, workers=c.get('workers', 4), on_logs=on, label='burns %d' % cid)
    json.dump(dict(chainId=cid, url=u, fromBlock=lo, toBlock=head, requests=st['req'], nFail=len(st['fail']), fail=st['fail'][:10], rows=rows), gzip.open('raw/burns_%d.json.gz' % cid, 'wt'))
    print(cid, 'range', lo, head, 'rows', len(rows), 'tokens', len(set(r[2] for r in rows)), 'txs', len(set(r[1] for r in rows)), 'req', st['req'], 'fail', len(st['fail']), st['fail'][:2], flush=True)
if __name__ == '__main__':
    main()
