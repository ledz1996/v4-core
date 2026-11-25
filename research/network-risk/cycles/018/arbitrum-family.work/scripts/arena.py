# Shared stack arena of the Nitro go-ethereum fork 0e44603 (core/vm/stack.go: one arena per EVM, each call frame
# claims the slots above its parent's top, and stack() grows the backing slice with slices.Grow when fewer than
# 1024 free slots remain). Each frame pushes K+1 values, calls itself with depth d-1 so that the child forces a
# growth of the arena, then sums its own values after the call and adds the child's sum. A parent that read a
# stale or moved slot after the child grew the arena would return a wrong sum. Expected: (d+1) * K(K+1)/2.
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../tools/opdiff'))
from evm import call_code
NETS = {1: 'https://ethereum-rpc.publicnode.com', 42161: 'https://arb1.arbitrum.io/rpc',
        4663: 'https://rpc.mainnet.chain.robinhood.com', 99901: 'https://rpc.elysium.kinetiq.xyz'}
def prog(K):
    c = bytearray()
    c += bytes([0x60, 0x00])                       # 0  PUSH1 0
    loop = len(c); c += bytes([0x5b, 0x80, 0x60, 0x01, 0x01, 0x80, 0x61, K >> 8, K & 0xff, 0x11, 0x60, loop, 0x57])
    c += bytes([0x60, 0x00, 0x35])                 # d
    j1 = len(c); c += bytes([0x80, 0x15, 0x61, 0, 0, 0x57])
    c += bytes([0x60, 0x01, 0x90, 0x03, 0x60, 0x00, 0x52])
    c += bytes([0x60, 0x20, 0x60, 0x00, 0x60, 0x20, 0x60, 0x00, 0x60, 0x00, 0x30, 0x5a, 0xf1, 0x50, 0x60, 0x00, 0x51])
    j2 = len(c); c += bytes([0x61, 0, 0, 0x56])
    skip = len(c); c += bytes([0x5b, 0x50, 0x60, 0x00])
    end = len(c); c += bytes([0x5b])
    c += bytes([0x01]) * (K + 1)
    c += bytes([0x60, 0x00, 0x52, 0x60, 0x20, 0x60, 0x00, 0xf3])
    c[j1 + 3], c[j1 + 4] = skip >> 8, skip & 0xff
    c[j2 + 1], c[j2 + 2] = end >> 8, end & 0xff
    return bytes(c)
out = {}
for cid, url in NETS.items():
    rows = []
    for K in (1, 500, 1000):
        code = prog(K)
        for d in (0, 1, 2, 3, 5, 8):
            exp = (d + 1) * K * (K + 1) // 2
            try:
                got = int.from_bytes(call_code(url, code, d.to_bytes(32, 'big'), gas=30_000_000), 'big')
            except Exception as e:
                got = 'ERR ' + str(e)[:100]
            rows.append({'K': K, 'd': d, 'expected': exp, 'got': got, 'ok': got == exp})
    out[cid] = rows
    print(cid, sum(r['ok'] for r in rows), '/', len(rows), [r for r in rows if not r['ok']][:3], flush=True)
json.dump(out, open(sys.argv[1], 'w'), indent=0)
