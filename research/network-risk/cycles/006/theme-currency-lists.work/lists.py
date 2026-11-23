# Part one: Initialize rows for BNB Smart Chain, World Chain and X Layer. Rows of cycle 5 (theme-shared-hooks.work/raw/init_*.json.gz)
# are reused and extended to the head. X Layer is read in full through rpc.nodeflare.app, which serves 100,000 block ranges.
# Read-only: eth_getLogs, eth_blockNumber. usage: python3 lists.py <chainId>
import sys, json, gzip, threading, os
from lib import *
from fetch import getlogs_range
INIT = '0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438'
C5 = '../../005/theme-shared-hooks.work/raw/'
SRC = {56: ('https://bsc-mainnet.nodereal.io/v1/64a9df0874fb4a93b9d0a3849de012d3', 10000, ['init_56_a', 'init_56_b', 'init_56_c']),
       480: ('https://sparkling-autumn-dinghy.worldchain-mainnet.quiknode.pro', 10000, ['init_480']),
       196: ('https://rpc.nodeflare.app/xlayer/public', 100000, [])}
def row(l):
    d = l['data'][2:]; t = l['topics']
    return [int(l['blockNumber'], 16), t[1], '0x' + t[2][-40:], '0x' + t[3][-40:], int(d[0:64], 16), int(d[64:128], 16), '0x' + d[128:192][-40:], l['transactionHash']]
def run(cid):
    url, chunk, olds = SRC[cid]; pm = net(cid)['poolManager']
    rows = []; lo = {196: 46106392}.get(cid); first = None
    for f in olds:
        d = json.load(gzip.open(C5 + f + '.json.gz')); rows += d['rows']; lo = d['hi'] + 1
        first = d['lo'] if first is None else min(first, d['lo'])
    head = int(rpc(url, 'eth_blockNumber', []), 16) - 20
    lock = threading.Lock(); new = []
    def on(logs):
        with lock: new.extend(row(l) for l in logs if not l.get('removed'))
    st = getlogs_range(url, {'address': pm, 'topics': [INIT]}, lo, head, chunk, workers=3, on_logs=on, label='%d init' % cid)
    seen = set(); out = []
    for r in sorted(rows + new, key=lambda r: (r[0], r[1])):
        if r[1] in seen: continue
        seen.add(r[1]); out.append(r)
    json.dump(dict(chainId=cid, url=url, lo=first if first is not None else lo, hi=head, reused=len(rows), fetched=len(new), fetchedFrom=lo, nFail=len(st['fail']), fail=st['fail'][:50], rows=out),
              gzip.open('raw/init_%d.json.gz' % cid, 'wt'))
    cur = {}
    for r in out:
        for c in (r[2], r[3]):
            e = cur.setdefault(c, [0, r[0]]); e[0] += 1
    json.dump(dict(chainId=cid, lo=first if first is not None else lo, hi=head, pools=len(out), currencies=cur), gzip.open('raw/currencies_%d.json.gz' % cid, 'wt'))
    print(cid, 'pools', len(out), 'currencies', len(cur), 'reused', len(rows), 'fetched', len(new), 'from', lo, 'to', head, 'fail', len(st['fail']), st['fail'][:3], flush=True)
if __name__ == '__main__':
    for c in sys.argv[1:]: run(int(c))
