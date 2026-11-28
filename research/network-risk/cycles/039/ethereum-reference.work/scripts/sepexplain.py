"""Cycle 39: for each pmdiff (set 1) or pmdiff2 (set 2) script whose Sepolia (Amsterdam) answer differs from the
mainnet reference, fetch both answers again and say which call differs first and how, then rerun the script on
Sepolia with a gas limit of 200,000,000 (EIP-8037: execution gas stays capped at 2^24 minus intrinsic on reth and
Tenderly, the rest becomes the state gas reservoir) and report whether it then equals the reference.
Also runs the script on mainnet with gas 2^24, to show whether mainnet fails it the same way under that budget.
usage: python3 sepexplain.py <1|2> <pmdiff json> <out json> <sepolia url>"""
import json, os, random, sys, time
TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'tools', 'opdiff')
sys.path.insert(0, TOOLS)
from evm import rpc
import pmdiff as P
SET, SRC, OUT, URL = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
ETH = 'https://ethereum-rpc.publicnode.com'
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
            last = e; time.sleep(3 * (k + 1))
    return ('ERR ' + str(last)[:200]).encode()


diff = [i for r in res['results'] for i in r['different']]
rows = []
for i in diff:
    data, kinds, meta = scripts[i]
    ref = P.parse(call(ETH, data, 25_000_000))
    got = P.parse(call(URL, data, 25_000_000))
    first = next((k for k, (a, b) in enumerate(zip(ref, got)) if a != b), None)
    if first is None and len(ref) != len(got): first = min(len(ref), len(got))
    row = {'script': i, 'calls': len(kinds), 'refCalls': len(ref), 'gotCalls': len(got)}
    if first is None:
        row['first'] = None
    else:
        row['first'] = first; row['kind'] = kinds[first] if first < len(kinds) else '?'
        row['ref'] = [ref[first][0], ref[first][1][:68].hex()] if first < len(ref) else None
        row['got'] = [got[first][0], got[first][1][:68].hex()] if first < len(got) else None
        row['laterCallsAfterFirstMatchRef'] = None
    big = P.parse(call(URL, data, 200_000_000))
    row['equalWith200M'] = big == ref
    # mainnet (Osaka) with the gas a reth or Tenderly eth_call leaves for execution under EIP-8037 on Sepolia
    capped = P.parse(call(ETH, data, 16_777_216))
    row['mainnetAt2^24EqualsSepolia25M'] = capped == got
    row['mainnetAt2^24EqualsRef'] = capped == ref
    rows.append(row); print(row, flush=True)
json.dump({'set': SET, 'url': URL, 'rows': rows}, open(OUT, 'w'), indent=1)
print('scripts', len(rows), 'equal with 200M', sum(r['equalWith200M'] for r in rows))
