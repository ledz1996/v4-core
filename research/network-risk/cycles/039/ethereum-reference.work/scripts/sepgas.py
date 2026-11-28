"""Cycle 39: for the set 1 and set 2 scripts that differ on Sepolia (Amsterdam), compare call by call the mainnet
answer at 50,000,000 gas (the publicnode eth_call cap) with the Sepolia geth answer (rpc.sepolia.ethpandaops.io) at
200,000,000 gas, and classify every differing call: 'oog' when one side is a failure with empty return data, the
signature of an out-of-gas child; 'other' otherwise. eth_call with state override only.
usage: python3 sepgas.py <1|2> <pmdiff json> <out json>"""
import json, os, random, sys, time
TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'tools', 'opdiff')
sys.path.insert(0, TOOLS)
from evm import rpc
import pmdiff as P
SET, SRC, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
ETH = 'https://ethereum-rpc.publicnode.com'; SEP = 'https://rpc.sepolia.ethpandaops.io'
res = json.load(open(SRC)); n = res['scripts']
if SET == '1':
    rnd = random.Random(7_2026_11_24); scripts = [P.script(rnd) for _ in range(n)]
    code = P.fetch_code(); drv = P.driver()
    ov = {P.PM: {'code': '0x' + code.hex()}, P.DRV: {'code': '0x' + drv.hex()}}
else:
    import pmdiff2 as Q
    rnd = random.Random(11_2026_11_24); scripts = [Q.script(rnd, i) for i in range(n)]
    code = P.fetch_code(); drv = Q.driver(); tok = Q.token(); hk = Q.hook()
    ov = {P.PM: {'code': '0x' + code.hex(), 'balance': hex(10 ** 19)}, P.DRV: {'code': '0x' + drv.hex()},
          '0x' + Q.TOKEN.to_bytes(20, 'big').hex(): {'code': '0x' + tok.hex()}}
    for f in Q.HOOK_FLAGS: ov['0x' + (Q.HOOK_BASE | f).to_bytes(20, 'big').hex()] = {'code': '0x' + hk.hex()}
def call(url, data, g):
    for k in range(6):
        try:
            return bytes.fromhex(rpc(url, 'eth_call', [{'to': P.DRV, 'data': '0x' + data.hex(), 'gas': hex(g)}, 'latest', ov], timeout=120)[2:])
        except Exception as e:  # noqa
            last = e; time.sleep(4 * (k + 1))
    raise last
diff = [i for r in res['results'] for i in r['different']]
rows = []
for i in diff:
    data, kinds, meta = scripts[i]
    a = P.parse(call(ETH, data, 50_000_000)); b = P.parse(call(SEP, data, 200_000_000))
    a25 = P.parse(call(ETH, data, 25_000_000))
    cls = {'oog': 0, 'other': 0}; others = []
    for k in range(max(len(a), len(b))):
        x = a[k] if k < len(a) else None; y = b[k] if k < len(b) else None
        if x == y: continue
        if x is None or y is None or (x[0] == 0 and len(x[1]) == 0) or (y[0] == 0 and len(y[1]) == 0):
            cls['oog'] += 1
        else:
            cls['other'] += 1; others.append([k, kinds[k] if k < len(kinds) else '?', [x[0], x[1][:68].hex()], [y[0], y[1][:68].hex()]])
    oog25 = sum(1 for x in a25 if x[0] == 0 and len(x[1]) == 0)
    row = {'script': i, 'calls': len(kinds), 'eth50M': len(a), 'sep200M': len(b), 'equal': a == b, 'diffCalls': cls,
           'others': others[:5], 'emptyFailuresEth25M': oog25, 'emptyFailuresEth50M': sum(1 for x in a if x[0] == 0 and len(x[1]) == 0)}
    rows.append(row); print(row, flush=True)
json.dump({'set': SET, 'rows': rows}, open(OUT, 'w'), indent=1)
