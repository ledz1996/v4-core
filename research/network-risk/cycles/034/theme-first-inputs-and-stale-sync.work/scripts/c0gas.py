"""Rerun case C0 (the no-liquidity walk across the range) with the most gas an endpoint grants, compare with pyevm."""
import sys, json
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/034/theme-first-inputs-and-stale-sync.work/scripts')
import wide as W, pmdiff as P
from evm import rpc
ref = {r['name']: r for r in json.load(open('out/wide-ref.json'))}['C0-gasbound-zeroForOne-exactIn-no-liquidity-walk']
code = P.fetch_code(); drv = P.driver(); ov = {P.PM: {'code': '0x' + code.hex()}, P.DRV: {'code': '0x' + drv.hex()}}
c = [x for x in W.CASES if x['name'].startswith('C0')][0]
out = {}
for label, url, gas in [('monad', 'https://rpc.monad.xyz', 150_000_000), ('mega', 'https://mainnet.megaeth.com/rpc', 1_000_000_000), ('hl-purroof', 'https://rpc.purroofgroup.com', 100_000_000)]:
    v = rpc(url, 'web3_clientVersion', [])
    try: r = rpc(url, 'eth_call', [{'to': P.DRV, 'data': '0x' + c['data'].hex(), 'gas': hex(gas)}, 'latest', ov], timeout=180); eq = r[2:] == ref['returnHex']
    except Exception as e: r = 'ERR ' + str(e)[:200]; eq = False
    out[label] = {'clientVersion': v, 'gas': gas, 'equal': eq, 'answer': None if eq else r}
    print(label, v, gas, eq, '' if eq else str(r)[:200])
json.dump(out, open('out/c0-gas.json', 'w'), indent=1)
