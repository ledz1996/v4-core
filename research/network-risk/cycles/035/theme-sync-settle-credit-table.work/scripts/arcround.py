"""Arc: one rounding bracket on the USDC face, live. sync(0x3600), forced native inflow of exactly the wei
missing to the next face unit (computed from the PoolManager's balance at the pinned block), settle, then
a native take of the same wei count. Records the face credit, the native debt and the gas the whole
bracket used (eth_simulateV1 where served, else eth_estimateGas of a non-reverting variant is not possible,
so gas is recorded from the simulate result only). Read-only. usage: python3 -I arcround.py <out.json>"""
import sys, json
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/035/theme-sync-settle-credit-table.work/scripts')
import credtab as C
from rpcu import rpc, version
url = 'https://rpc.mainnet.arc.io'; pm = '0x8366a39cc670b4001a1121b8f6a443a643e40951'; F = '0x3600000000000000000000000000000000000000'
out = {'before': version(url, 5042)}
b = rpc(url, 'eth_getBlockByNumber', ['latest', False]); bn = b['result']['number']; out['block'] = bn; out['baseFee'] = b['result'].get('baseFeePerGas')
bal = int(rpc(url, 'eth_getBalance', [pm, bn])['result'], 16); out['pmNative'] = bal
v = 10**12 - bal % 10**12; out['forced'] = v
steps = [C.CALL(F, C.balOf(F, pm), label='face before'), C.CALL(pm, C.sel('sync(address)') + C.a32(F), label='sync(face)'),
         C.CREATE(v, bytes([0x73]) + bytes.fromhex(pm[2:]) + bytes([0xff]), 'forced inflow'),
         C.CALL(F, C.balOf(F, pm), label='face after'), C.CALL(pm, C.sel('settle()'), label='settle'),
         C.CALL(pm, C.sel('take(address,address,uint256)') + C.a32(C.ZERO) + C.a32(C.DRV) + C.w(v), label='native take v'),
         C.CALL(pm, C.sel('exttload(bytes32)') + C.dslot(C.DRV, F), label='delta face'),
         C.CALL(pm, C.sel('exttload(bytes32)') + C.dslot(C.DRV, C.ZERO), label='delta native')]
rec = C.run(url, 5042, pm, 'arc rounding bracket', steps, bn); out['call'] = rec
drv = C.driver(pm); data = b''.join(s for _, s in steps)
tx = {'from': '0x00000000000000000000000000000000000a11ce', 'to': C.DRV, 'data': '0x' + data.hex(), 'gas': hex(15_000_000)}
out['simulate'] = rpc(url, 'eth_simulateV1', [{'blockStateCalls': [{'stateOverrides': {C.DRV: {'code': '0x' + drv.hex(), 'balance': hex(10**21)}}, 'calls': [tx]}]}, bn], 120)
out['after'] = version(url, 5042)
json.dump(out, open(sys.argv[1], 'w'), indent=1)
for s in rec.get('steps', []): print(s['label'], s['ok'], s['ret'][:64])
print('forced', v, 'sim', str(out['simulate'])[:300])
