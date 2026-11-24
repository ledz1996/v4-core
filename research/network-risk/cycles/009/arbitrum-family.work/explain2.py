"""Explain the pmdiff2 script(s) where Elysium differs from Ethereum: first differing call, and the
same script with larger gas. Usage: python3 -I explain2.py <idx> ..."""
import sys, os, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools', 'opdiff'))
from evm import rpc
import pmdiff as P, pmdiff2 as Q
rnd = random.Random(11_2026_11_24); scripts = [Q.script(rnd, i) for i in range(300)]
code = P.fetch_code(); ov = {P.PM: {'code': '0x' + code.hex(), 'balance': hex(10 ** 19)}, P.DRV: {'code': '0x' + Q.driver().hex()},
      '0x' + Q.TOKEN.to_bytes(20, 'big').hex(): {'code': '0x' + Q.token().hex()}}
for f in Q.HOOK_FLAGS: ov['0x' + (Q.HOOK_BASE | f).to_bytes(20, 'big').hex()] = {'code': '0x' + Q.hook().hex()}
U = {1: 'https://ethereum-rpc.publicnode.com', 99901: 'https://rpc.elysium.kinetiq.xyz'}
from evm import networks
U[1] = [n[2] for n in networks() if n[0] == 1][0]
def call(cid, data, g): return P.parse(bytes.fromhex(rpc(U[cid], 'eth_call', [{'to': P.DRV, 'data': '0x' + data.hex(), 'gas': hex(g)}, 'latest', ov], timeout=120)[2:]))
for i in map(int, sys.argv[1:]):
    data, kinds, meta = scripts[i]
    for g in (25_000_000, 50_000_000):
        a = call(1, data, g); b = call(99901, data, g)
        first = next((k for k, (x, y) in enumerate(zip(a, b)) if x != y), None)
        if first is None and len(a) != len(b): first = min(len(a), len(b))
        print('script', i, 'gas', g, 'calls eth', len(a), 'ely', len(b), 'first diff', first, kinds[first] if first is not None and first < len(kinds) else None,
              'eth', (a[first][0], a[first][1][:40].hex()) if first is not None and first < len(a) else None,
              'ely', (b[first][0], b[first][1][:40].hex()) if first is not None and first < len(b) else None, meta)
