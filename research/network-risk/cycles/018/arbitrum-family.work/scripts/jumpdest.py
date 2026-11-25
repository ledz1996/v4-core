# Jump destination analysis around the int8 comparison in codeBitmapInternal (core/vm/analysis_legacy.go:79 of the
# Nitro go-ethereum fork 0e44603). For every opcode byte b placed before a JUMPDEST at distance k, a JUMP to that
# JUMPDEST must succeed unless b is PUSHn with k < n (the 0x5b is push data). One eth_call per vector by state override.
import sys, os, json
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../tools/opdiff'))
from evm import call_code
NETS = {42161: 'https://arb1.arbitrum.io/rpc', 4663: 'https://rpc.mainnet.chain.robinhood.com', 99901: 'https://rpc.elysium.kinetiq.xyz'}
TAIL = bytes.fromhex('600160005260206000f3')
def vec():
    out = []
    for b in range(256):
        n = b - 0x5f if 0x60 <= b <= 0x7f else 0
        ks = sorted({0, 1, max(n - 1, 0), n, n + 1}) if n else [0, 1]
        for k in ks:
            t = 5 + k
            code = bytes([0x61, t >> 8, t & 0xff, 0x56, b]) + b'\x00' * k + b'\x5b' + TAIL
            out.append((b, k, code, not (n and k < n)))
    return out
def run(url, v):
    b, k, code, ok = v
    try:
        r = call_code(url, code, retries=2)
        got = r == (1).to_bytes(32, 'big')
    except Exception as e:
        got = False if 'invalid jump' in str(e).lower() or 'reverted' in str(e).lower() or 'invalid' in str(e).lower() else ('ERR ' + str(e)[:120])
    return b, k, ok, got
V = vec()
res = {}
for cid, url in NETS.items():
    with ThreadPoolExecutor(8) as ex:
        rs = list(ex.map(lambda v: run(url, v), V))
    mism = [r for r in rs if r[3] is not r[2] and r[3] != r[2]]
    errs = [r for r in rs if isinstance(r[3], str)]
    res[cid] = {'vectors': len(rs), 'mismatches': mism, 'errors': errs}
    print(cid, 'vectors', len(rs), 'mismatches', len(mism), 'errors', len(errs), flush=True)
json.dump(res, open(sys.argv[1], 'w'), indent=0)
