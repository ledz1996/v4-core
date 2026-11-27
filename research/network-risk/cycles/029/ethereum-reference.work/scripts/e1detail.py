"""Prints reference and endpoint return data for scenario E1 of scen28 (delegatecall into the PoolManager). Read-only."""
import sys, json
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/029/ethereum-reference.work/scripts')
import simscen as M
S = M.S
nm = [k for k in S.SCEN if k.startswith('E1')][0]; sc = S.SCEN[nm]
ref_outs, ref_st = S.ref(sc)
cs = S.codes_for(S.PM, [sc['key']]); cs.update({int(a, 16): bytes.fromhex(b) for a, b in sc.get('codes', {}).items()})
ov = {M.h(a): {'code': '0x' + c.hex()} for a, c in cs.items()}
calls = [{'from': M.h(S.EOA), 'to': M.h(S.addr(t['to'])), 'data': '0x' + t['data'], 'gas': hex(25_000_000)} for t in sc['txs']]
r = M.post(sys.argv[1], {'jsonrpc': '2.0', 'id': 1, 'method': 'eth_simulateV1', 'params': [{'blockStateCalls': [{'blockOverrides': {'gasLimit': hex(25_000_000 * len(calls))}, 'stateOverrides': ov, 'calls': calls}]}, 'latest']})
for i, ((ok, ret), c) in enumerate(zip(ref_outs, r['result'][0]['calls'])):
    print(i, sc['txs'][i]['to'], 'ref', ok, ret[:200]); print('   got', c.get('status'), (c.get('returnData') or '')[:202], str(c.get('error'))[:150])
