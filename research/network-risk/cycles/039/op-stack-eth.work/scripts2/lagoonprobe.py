"""Read-only probe: does eth_call with a block time override past lagoon_time run Lagoon rules?
Calls the BLS12-381 G1 MSM precompile (0x0c) with 900 all-zero pairs (144,000 bytes), which the
Lagoon limit (817 pairs) rejects and the Jovian limit (1,806 pairs) accepts.
Usage: python3 -I lagoonprobe.py <toolsdir> <out.json> chainId..."""
import sys, json
sys.path.insert(0, sys.argv[1])
from evm import rpc, networks
out = sys.argv[2]; only = set(map(int, sys.argv[3:]))
data = '0x' + '00' * (160 * 900)
res = []
for cid, name, url in networks():
    if cid not in only: continue
    row = {'chainId': cid, 'rpc': url}
    try:
        row['clientVersion'] = rpc(url, 'web3_clientVersion', [])
        b = rpc(url, 'eth_getBlockByNumber', ['latest', False]); row['latest'] = [int(b['number'], 16), int(b['timestamp'], 16)]
    except Exception as e: row['head_err'] = str(e)[:200]
    for tag, ov in [('now', None), ('lagoon+100', {'time': hex(1799683301)})]:
        p = [{'to': '0x000000000000000000000000000000000000000c', 'data': data, 'gas': hex(20_000_000)}, 'latest', {}]
        if ov: p.append(ov)
        try: r = rpc(url, 'eth_call', p, timeout=90); row[tag] = 'ok len %d' % ((len(r) - 2) // 2)
        except Exception as e: row[tag] = 'err ' + str(e)[:200]
    print(row); res.append(row)
json.dump(res, open(out, 'w'), indent=1)
