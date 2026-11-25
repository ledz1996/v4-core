"""L-185: ordered PoolManager frames of every PoolManager transaction on HyperEVM (call traces from the
archive client), to find a transaction that leaves a sync(ERC-20) without a later settle and a later
transaction of the same block that makes a native settle with value. Read only."""
import sys, json, time, urllib.request, concurrent.futures as cf, collections
U = 'https://rpc.purroofgroup.com'; PM = '0x12d4fd9c5dedd00ab8a0bce2cf0167bbf94b6b1f'
SYNC, SETTLE, SETTLEFOR = '0xa5841194', '0x11da60b4', '0x3dd45adb'
def rpc(m, p):
    for i in range(8):
        r = urllib.request.Request(U, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": m, "params": p}).encode(), headers={'content-type': 'application/json', 'user-agent': 'probe'})
        try:
            j = json.load(urllib.request.urlopen(r, timeout=120))
            if 'error' in j: raise Exception(str(j['error']))
            return j['result']
        except Exception as e: err = e; time.sleep(1 + i)
    raise err
def walk(fr, acc, rev=False):
    err = fr.get('error'); r = rev or bool(err)
    if (fr.get('to') or '').lower() == PM:
        inp = fr.get('input', '0x')
        acc.append({'sel': inp[:10], 'arg': '0x' + inp[34:74] if len(inp) >= 74 else None, 'value': int(fr.get('value', '0x0') or '0x0', 16), 'rev': r, 'type': fr.get('type')})
    for c in fr.get('calls', []) or []: walk(c, acc, r)
def one(h):
    t = rpc('debug_traceTransaction', [h, {'tracer': 'callTracer'}]); rc = rpc('eth_getTransactionReceipt', [h])
    acc = []; walk(t, acc)
    return {'tx': h, 'block': int(rc['blockNumber'], 16), 'idx': int(rc['transactionIndex'], 16), 'status': rc['status'], 'frames': acc}
txs = json.load(open('/home/user/v4-core/research/network-risk/cycles/015/theme-closed-producers-2.work/raw/pmtx-999.json'))
rows = []
with cf.ThreadPoolExecutor(8) as ex:
    for r in ex.map(one, txs): rows.append(r)
def leaves_sync(fr):  # last effective (not reverted) PM frame state: is a currency synced at the end?
    synced = None
    for f in fr:
        if f['rev']: continue
        if f['sel'] == SYNC: synced = f['arg']
        elif f['sel'] in (SETTLE, SETTLEFOR): synced = None
    return synced
def native_settle_unsynced(fr):
    synced = None; hits = []
    for f in fr:
        if f['rev']: continue
        if f['sel'] == SYNC: synced = f['arg']
        elif f['sel'] in (SETTLE, SETTLEFOR):
            if f['value'] > 0 and synced is None: hits.append(f)
            synced = None
    return hits
byblock = collections.defaultdict(list)
for r in rows: byblock[r['block']].append(r)
st = collections.Counter(); pairs = []
for b, rs in byblock.items():
    rs.sort(key=lambda r: r['idx'])
    for i, r in enumerate(rs):
        s = leaves_sync(r['frames']) if r['status'] == '0x1' else None
        if s and s != '0x' + '0' * 40:
            st['txLeavingSyncedErc20'] += 1
            for r2 in rs[i + 1:]:
                if r2['status'] == '0x1' and native_settle_unsynced(r2['frames']):
                    pairs.append({'block': b, 'first': r['tx'], 'second': r2['tx']})
        if r['status'] == '0x1' and native_settle_unsynced(r['frames']): st['txWithNativeSettleNoOwnSync'] += 1
st['tx'] = len(rows); st['blocks'] = len(byblock); st['blocksWithSeveralPmTx'] = sum(1 for v in byblock.values() if len(v) > 1)
st['framesSync'] = sum(1 for r in rows for f in r['frames'] if f['sel'] == SYNC)
print(dict(st), 'pairs', len(pairs), pairs[:5])
json.dump({'stats': st, 'pairs': pairs, 'txLeavingSync': [r['tx'] for r in rows if r['status'] == '0x1' and leaves_sync(r['frames']) not in (None, '0x' + '0' * 40)]}, open(sys.argv[1], 'w'), indent=1)
