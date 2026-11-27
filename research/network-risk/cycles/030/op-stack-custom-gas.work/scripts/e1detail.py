"""Cycle 30 op-stack-custom-gas: scen28 scenario E1 on one endpoint through eth_simulateV1, printing the reference and
the returned status, return data and error of every transaction. Read-only. Usage: python3 e1detail.py <out.json> <url> [name-prefix]"""
import sys, json
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/028/theme-monad-native-unentered-blocks.work/scripts')
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/029/op-stack-eth.work/scripts')
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/030/op-stack-custom-gas.work/scripts')
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import scen28 as X, scen_rpc as SR, l1195 as L
out, url = sys.argv[1], sys.argv[2]; pre = sys.argv[3] if len(sys.argv) > 3 else 'E1'
nm = [k for k in X.SCEN if k.startswith(pre)][0]; sc = X.SCEN[nm]; ref, _ = X.ref(sc)
blocks = []
for i, tx in enumerate(sc['txs']):
    b = {'calls': [{'from': '0x%040x' % X.EOA, 'to': '0x%040x' % X.addr(tx['to']), 'data': '0x' + tx['data'], 'gas': hex(25_000_000)}]}
    if i == 0: b['stateOverrides'] = SR.ov_for(sc)
    blocks.append(b)
r = L.batch(url, 'eth_simulateV1', [{'blockStateCalls': blocks, 'validation': False}, 'latest'])
rows = []
calls = [c for b in r[2]['result'] for c in b['calls']]
for i, (tx, (rok, rret), c) in enumerate(zip(sc['txs'], ref, calls)):
    rows.append({'i': i, 'to': tx['to'], 'data': tx['data'][:80], 'refOk': rok, 'refRet': rret[:140], 'status': c['status'], 'ret': c.get('returnData', '')[:140], 'error': c.get('error'), 'gasUsed': int(c['gasUsed'], 16)})
    print(rows[-1])
json.dump({'url': url, 'client': [r[1].get('result'), r[3].get('result')], 'scenario': nm, 'rows': rows}, open(out, 'w'), indent=1)
