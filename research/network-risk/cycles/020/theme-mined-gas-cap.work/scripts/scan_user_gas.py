"""Largest gas limit among user transactions (gas price > 0, not an OP deposit) in the last K blocks.
usage: python3 -I scan_user_gas.py <out.json> K chainId ..."""
import sys, json
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/020/theme-mined-gas-cap.work/scripts')
from rpc import call, BY
out = {}
K = int(sys.argv[2])
for cid in map(int, sys.argv[3:]):
    url = BY[cid]['rpc']; hn = int(call(url, 'eth_blockNumber', [])['result'], 16)
    top = []; n = 0
    for b in range(hn, hn - K, -1):
        blk = (call(url, 'eth_getBlockByNumber', [hex(b), True]) or {}).get('result')
        if not blk: continue
        for t in blk['transactions']:
            if t.get('type') == '0x7e' or int(t.get('gasPrice', t.get('maxFeePerGas', '0x0')) or '0x0', 16) == 0: continue
            n += 1; top.append((int(t['gas'], 16), t['hash'], t['from'], t['to'], b))
    top.sort(reverse=True)
    out[cid] = {'from': hn - K + 1, 'to': hn, 'userTxs': n, 'top5': top[:5]}
    print(cid, out[cid]['from'], hn, n, top[:3])
json.dump(out, open(sys.argv[1], 'w'), indent=1)
