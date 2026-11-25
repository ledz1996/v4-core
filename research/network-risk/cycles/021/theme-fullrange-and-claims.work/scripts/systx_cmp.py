"""Cycle 21, task 3 (L-946). For 200 HyperEVM blocks drawn with random.Random(SEED) from [head-SPAN, head-100], compare
the system transactions the official endpoint returns (eth_getSystemTxsByBlockNumber) with what the archive client
nanoreth returns for the same block (eth_getBlockByNumber with full transactions, where nanoreth lists the system
transactions first, and eth_getBlockReceipts for their status and logs). Also compare header fields (hash,
receiptsRoot, transactionsRoot, gasUsed) and the signed transaction hash list. Fields compared per system transaction:
type, chainId, nonce, gasPrice, gas, to, value, input, from, and position (index). Hashes are recorded but not required
to match, because the two clients compute system transaction hashes differently (observed on block 0x31c68f5).
usage: python3 -I systx_cmp.py <out.json> <seed> <span> <archiveUrl> [n]"""
import sys, json, random, time, urllib.request
OFF = 'https://rpc.hyperliquid.xyz/evm'
out, seed, span, ARC = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
N = int(sys.argv[5]) if len(sys.argv) > 5 else 200
def rpc(url, m, p, tries=8):
    last = None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(), headers={'content-type': 'application/json', 'user-agent': 'rpc-client/1.0'})
            with urllib.request.urlopen(req, timeout=60) as r: j = json.loads(r.read())
            if 'error' in j:
                last = j['error']
                if 'rate' in str(j['error']).lower(): time.sleep(3 * (k + 1)); continue
                return {'error': j['error']}
            return {'result': j['result']}
        except Exception as e:
            last = str(e)[:200]; time.sleep(3 * (k + 1))
    return {'error': last}
F = ('type', 'chainId', 'nonce', 'gasPrice', 'gas', 'to', 'value', 'input', 'from')
def norm(t): return {k: (t.get(k) or '').lower() if isinstance(t.get(k), str) or t.get(k) is None else t.get(k) for k in F}
res = {'seed': seed, 'span': span, 'official': OFF, 'archive': ARC, 'start': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
       'clientVersionBefore': {OFF: rpc(OFF, 'web3_clientVersion', []), ARC: rpc(ARC, 'web3_clientVersion', [])}}
head = int(rpc(OFF, 'eth_blockNumber', [])['result'], 16); res['head'] = head
rnd = random.Random(seed); blocks = sorted(rnd.sample(range(head - span, head - 100), N)); res['blocks'] = blocks
rows = []; summ = {'blocks': 0, 'errors': 0, 'withSystemTxs': 0, 'systemTxs': 0, 'fieldMismatch': 0, 'countMismatch': 0, 'headerMismatch': 0,
                   'signedMismatch': 0, 'notFirst': 0, 'hashEqual': 0, 'archiveFailedSystemTx': 0, 'touchesPoolManager': 0}
PM = '12d4fd9c5dedd00ab8a0bce2cf0167bbf94b6b1f'
for b in blocks:
    B = hex(b); row = {'block': b}
    so = rpc(OFF, 'eth_getSystemTxsByBlockNumber', [B]); bo = rpc(OFF, 'eth_getBlockByNumber', [B, False])
    ba = rpc(ARC, 'eth_getBlockByNumber', [B, True]); ra = rpc(ARC, 'eth_getBlockReceipts', [B])
    if any('error' in x for x in (so, bo, ba, ra)) or ba.get('result') is None or bo.get('result') is None:
        row['error'] = [x.get('error') for x in (so, bo, ba, ra)]; summ['errors'] += 1; rows.append(row); continue
    summ['blocks'] += 1
    sys_o = so['result'] or []; Bo = bo['result']; Ba = ba['result']; Ra = ra['result'] or []
    hdr = {k: [Bo.get(k), Ba.get(k)] for k in ('hash', 'receiptsRoot', 'transactionsRoot', 'gasUsed', 'stateRoot')}
    row['headerEqual'] = all(a == c for a, c in hdr.values())
    if not row['headerEqual']: summ['headerMismatch'] += 1; row['header'] = hdr
    k = len(sys_o); txa = Ba['transactions']
    sys_a = txa[:k]; signed_a = [t['hash'] for t in txa[k:]]
    row['nSystem'] = k; row['nArchiveTx'] = len(txa)
    if signed_a != Bo['transactions']:
        summ['signedMismatch'] += 1; row['signed'] = {'official': Bo['transactions'], 'archiveAfterSystem': signed_a}
    if k:
        summ['withSystemTxs'] += 1; summ['systemTxs'] += k
    if any(t.get('gasPrice') == '0x0' and t.get('r') in ('0x0', None) for t in txa[k:]):
        summ['countMismatch'] += 1; row['extraUnsignedInArchive'] = True
    mism = []
    for i, (a, c) in enumerate(zip(sys_o, sys_a)):
        na, nc = norm(a), norm(c)
        if na != nc: mism.append({'i': i, 'official': a, 'archive': c})
        if a.get('hash') == c.get('hash'): summ['hashEqual'] += 1
        if int(a.get('transactionIndex', '0x0'), 16) != i: summ['notFirst'] += 1
        if PM in json.dumps(a).lower(): summ['touchesPoolManager'] += 1
    for i in range(k):
        if i < len(Ra) and Ra[i].get('status') != '0x1': summ['archiveFailedSystemTx'] += 1
    row['systemArchiveReceipts'] = [{'status': r.get('status'), 'cumulativeGasUsed': r.get('cumulativeGasUsed'), 'logs': len(r.get('logs', []))} for r in Ra[:k]]
    row['systemHashes'] = [[a.get('hash'), c.get('hash')] for a, c in zip(sys_o, sys_a)]
    if mism: summ['fieldMismatch'] += 1; row['mismatch'] = mism
    rows.append(row)
    time.sleep(0.4)
res['rows'] = rows; res['summary'] = summ
res['clientVersionAfter'] = {OFF: rpc(OFF, 'web3_clientVersion', []), ARC: rpc(ARC, 'web3_clientVersion', [])}; res['end'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
json.dump(res, open(out, 'w'), indent=1)
print(json.dumps(summ)); print(res['clientVersionBefore'], res['clientVersionAfter'])
