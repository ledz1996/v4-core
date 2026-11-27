"""Cycle 37 theme-native-face-inflows, follow-ups. Read-only. (1) Celo: top-level eth_call to the transfer precompile
0xfd from an EOA, moving the PoolManager's CELO to the caller. (2) Arc: face take of 1 unit naming the PoolManager
between sync(face) and settle. (3) OP Mainnet and Zora: recipient and withdrawal network of the four fee vaults.
(4) OP Mainnet and Zora: eth_simulateV1 with a deposit-typed (0x7e) call that carries value to the PoolManager.
Bracketed with web3_clientVersion. No randomness, no seed. usage: python3 -I extra.py <out.json>"""
import sys, json
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/035/theme-sync-settle-credit-table.work/scripts')
import credtab as C
from rpcu import rpc, version
S = C.sel; out = {}
EOA = '0x00000000000000000000000000000000000a11ce'
# 1 Celo
u = 'https://forno.celo.org'; pm = '0x288dc841a52fca2707c6947b3a777c5e56cd87bc'
o = {'before': version(u, 42220)}
o['eoaCall0xfd'] = rpc(u, 'eth_call', [{'from': EOA, 'to': '0x00000000000000000000000000000000000000fd', 'data': '0x' + (C.a32(pm) + C.a32(EOA) + C.w(1)).hex()}, 'latest'])
o['pmCall0xfd_fromPM'] = rpc(u, 'eth_call', [{'from': pm, 'to': '0x00000000000000000000000000000000000000fd', 'data': '0x' + (C.a32(pm) + C.a32(EOA) + C.w(1)).hex()}, 'latest'])
o['after'] = version(u, 42220); out['42220'] = o; print('celo', json.dumps(o)[:900])
# 2 Arc
u = 'https://rpc.mainnet.arc.io'; pm = '0x8366a39cc670b4001a1121b8f6a443a643e40951'; F = '0x3600000000000000000000000000000000000000'
o = {'before': version(u, 5042)}
b = rpc(u, 'eth_getBlockByNumber', ['latest', False])['result']['number']; o['block'] = b
steps = [C.CALL(F, C.balOf(F, pm), label='face before'), C.BAL(pm, 'native before'), C.CALL(pm, S('sync(address)') + C.a32(F), label='sync(face)'),
         C.CALL(pm, S('take(address,address,uint256)') + C.a32(F) + C.a32(pm) + C.w(1), label='take(face, PM, 1)'),
         C.CALL(F, C.balOf(F, pm), label='face after'), C.BAL(pm, 'native after'), C.CALL(pm, S('settle()'), label='settle'),
         C.CALL(pm, S('exttload(bytes32)') + C.dslot(C.DRV, F), label='delta(driver,face)')]
rec = C.run(u, 5042, pm, 'arc face take to PM', steps, b); o['case'] = rec
for s in rec.get('steps', []): print('  arc', s['label'], s['ok'], s['ret'][:120])
o['after'] = version(u, 5042); out['5042'] = o
# 3, 4 OP and Zora
VAULTS = {'SequencerFeeVault': '0x4200000000000000000000000000000000000011', 'BaseFeeVault': '0x4200000000000000000000000000000000000019',
          'L1FeeVault': '0x420000000000000000000000000000000000001a', 'OperatorFeeVault': '0x420000000000000000000000000000000000001b'}
for cid, u, pm in [(10, 'https://mainnet.optimism.io', '0x9a13f98cb987694c9f086b1f5eb990eea8264ec3'), (7777777, 'https://rpc.zora.energy/', '0x0575338e4c17006ae181b47900a84404247ca30f')]:
    o = {'before': version(u, cid), 'vaults': {}}
    for n, a in VAULTS.items():
        v = {}
        for f in ['recipient()', 'RECIPIENT()', 'withdrawalNetwork()', 'WITHDRAWAL_NETWORK()', 'minWithdrawalAmount()']:
            v[f] = rpc(u, 'eth_call', [{'to': a, 'data': '0x' + S(f).hex()}, 'latest']).get('result')
        v['balance'] = rpc(u, 'eth_getBalance', [a, 'latest']).get('result'); o['vaults'][n] = v
    dep = {'type': '0x7e', 'from': EOA, 'to': pm, 'value': hex(10**6), 'mint': hex(10**6), 'sourceHash': '0x' + '11' * 32, 'gas': hex(100000), 'isSystemTx': False}
    o['depositSim'] = rpc(u, 'eth_simulateV1', [{'blockStateCalls': [{'calls': [dep]}]}, 'latest'], 120)
    o['after'] = version(u, cid); out[str(cid)] = o
    print(cid, json.dumps(o['vaults'])[:1500]); print(cid, 'dep', str(o['depositSim'])[:600])
json.dump(out, open(sys.argv[1], 'w'), indent=1)
