"""L-1023 search: CIP-64 (type 0x7b) transactions in recent Celo blocks whose sender's balance of the
fee currency at the parent block is at most gasLimit*maxFeePerGas (a debit that could clear the slot).
Read-only: eth_getBlockByNumber and eth_call balanceOf at the parent block on forno.
Usage: python3 cip64_scan.py <out.json> <nblocks>"""
import sys, json, urllib.request
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff'); import evm
U = 'https://forno.celo.org'
def batch(reqs):
    body = json.dumps([{'jsonrpc': '2.0', 'id': i, 'method': m, 'params': p} for i, (m, p) in enumerate(reqs)]).encode()
    for _ in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(U, data=body, headers={'content-type': 'application/json', 'user-agent': 'curl/8'}), timeout=60, context=evm._ctx) as r:
                return {x['id']: x.get('result') for x in json.load(r)}
        except Exception: pass
    return {}
out, n = sys.argv[1], int(sys.argv[2])
head = int(batch([('eth_blockNumber', [])])[0], 16)
txs = []; seen = 0
for s in range(head - n, head, 50):
    res = batch([('eth_getBlockByNumber', [hex(b), True]) for b in range(s, min(s + 50, head))])
    for b in res.values():
        if not b: continue
        for t in b['transactions']:
            seen += 1
            if t.get('type') == '0x7b' and t.get('feeCurrency'):
                txs.append((int(b['number'], 16), t))
cands = []
for i in range(0, len(txs), 40):
    chunk = txs[i:i + 40]
    res = batch([('eth_call', [{'to': t['feeCurrency'], 'data': '0x70a08231' + t['from'][2:].rjust(64, '0')}, hex(bn - 1)]) for bn, t in chunk])
    for k, (bn, t) in enumerate(chunk):
        bal = res.get(k); 
        if not bal or bal == '0x': continue
        bal = int(bal, 16); debit = int(t['gas'], 16) * int(t['maxFeePerGas'], 16)
        if bal <= debit * 2:
            cands.append({'block': bn, 'hash': t['hash'], 'from': t['from'], 'feeCurrency': t['feeCurrency'], 'balanceParent': bal, 'maxDebit': debit})
json.dump({'blocks': n, 'head': head, 'txSeen': seen, 'cip64': len(txs), 'candidates': cands}, open(out, 'w'), indent=1)
print('blocks', n, 'tx', seen, 'cip64', len(txs), 'candidates', len(cands))
