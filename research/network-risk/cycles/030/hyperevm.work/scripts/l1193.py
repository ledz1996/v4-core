"""L-1193: storage writes of recent PoolManager blocks, replica prestate diff vs official and second replica.
Usage: l1193.py <logs.json> <out.json> [nblocks]"""
import sys, json, urllib.request, time
src, out = sys.argv[1], sys.argv[2]; N = int(sys.argv[3]) if len(sys.argv) > 3 else 50
PM = '0x12d4fd9c5dedd00ab8a0bce2cf0167bbf94b6b1f'
OFF = 'https://rpc.hyperliquid.xyz/evm'; R1 = 'https://rpc.purroofgroup.com'; R2 = 'https://rpc.hyperlend.finance/archive'
def rpc(url, m, p, tries=6):
    for i in range(tries):
        try:
            r = urllib.request.Request(url, json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(), {'content-type': 'application/json', 'user-agent': 'curl/8.5.0'})
            j = json.load(urllib.request.urlopen(r, timeout=120))
            if 'error' in j and 'rate' in str(j['error']).lower(): time.sleep(2 + 2 * i); continue
            return j
        except Exception as e:
            time.sleep(2 + 2 * i); err = str(e)
    return {'error': err}
T = {'0xf208f4912782fd25c7f114ca3723a2d5dd6f3bcc3ac8db5af63baa85f711d5ec', '0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f'}
logs = json.load(open(src))['logs']
blocks = sorted({int(l['blockNumber'], 16) for l in logs if l['topics'][0] in T})[-N:]
txs = {}
for l in logs:
    b = int(l['blockNumber'], 16)
    if b in blocks: txs.setdefault(b, set()).add(l['transactionHash'])
res = {'blocks': blocks, 'items': [], 'diffs': []}
writes = {}  # (addr,slot) -> (block, txindex order, post)
import os, pickle
CACHE = out + '.writes.pkl'
if os.path.exists(CACHE): writes = pickle.load(open(CACHE, 'rb')); blocks_todo = []
else: blocks_todo = blocks
for b in blocks_todo:
    for h in sorted(txs[b]):
        tr = rpc(R1, 'debug_traceTransaction', [h, {'tracer': 'prestateTracer', 'tracerConfig': {'diffMode': True}}])
        if 'result' not in tr: res['diffs'].append({'tx': h, 'traceError': tr.get('error')}); continue
        post = tr['result'].get('post', {}); pre = tr['result'].get('pre', {})
        for a, acc in post.items():
            for s, v in (acc.get('storage') or {}).items():
                writes[(a.lower(), s)] = (b, h, v)
        # slots zeroed: in pre but absent in post storage -> written to zero
        for a, acc in pre.items():
            pa = (post.get(a) or {})
            if a in post and 'storage' in acc:
                for s in acc['storage']:
                    if s not in (pa.get('storage') or {}): writes[(a.lower(), s)] = (b, h, '0x' + '0' * 64)
pickle.dump(writes, open(CACHE, 'wb'))
print('blocks', len(blocks), blocks[0], blocks[-1], 'txs', sum(len(v) for v in txs.values()), 'written slots', len(writes))
norm = lambda v: int(v, 16) if isinstance(v, str) and v.startswith('0x') else None
nd = 0; npm = 0
pmw = [(s, b, h, v) for (a, s), (b, h, v) in sorted(writes.items(), key=lambda kv: kv[1][0]) if a == PM]
def batch(url, reqs):
    outv = []; C = 10 if 'hyperlend' in url else 20
    for i in range(0, len(reqs), C):
        chunk = reqs[i:i + C]
        if 'hyperlend' in url: time.sleep(0.5)
        body = [{'jsonrpc': '2.0', 'id': k, 'method': 'eth_getStorageAt', 'params': [PM, s, blk]} for k, (s, blk) in enumerate(chunk)]
        for t in range(8):
            try:
                r = urllib.request.Request(url, json.dumps(body).encode(), {'content-type': 'application/json', 'user-agent': 'curl/8.5.0'})
                j = json.load(urllib.request.urlopen(r, timeout=120))
                if isinstance(j, list) and all('result' in x for x in j): break
                print('bad', str([x for x in j if 'result' not in x][:1] if isinstance(j, list) else j)[:300], flush=True)
            except Exception as e: j = None; print('exc', str(e)[:200], flush=True)
            print(url, i, "retry", t, flush=True); time.sleep(2 + t)
        m = {x['id']: x.get('result') for x in (j or []) if isinstance(x, dict)}
        outv += [m.get(k) for k in range(len(chunk))]
    print(url, 'done', len(outv), sum(1 for x in outv if x is None), 'missing', flush=True)
    return outv
got = {}
for name, url in (('r1', R1), ('r2', R2), ('off', OFF)):
    got[name + '_atBlock'] = batch(url, [(s, hex(b)) for s, b, h, v in pmw])
    got[name + '_latest'] = batch(url, [(s, 'latest') for s, b, h, v in pmw])
for i, (s, b, h, v) in enumerate(pmw):
    npm += 1
    item = {'slot': s, 'block': b, 'tx': h, 'tracePost': v}
    for k in got: item[k] = got[k][i]
    vals = {k: norm(item[k]) for k in item if k.endswith('_atBlock') or k.endswith('_latest')}
    item['agree_atBlock'] = norm(v) == vals['r1_atBlock'] == vals['r2_atBlock']
    item['agree_latest'] = vals['r1_latest'] == vals['r2_latest'] == vals['off_latest']
    item['off_atBlock_eq_trace'] = vals['off_atBlock'] == norm(v)
    if not (item['agree_atBlock'] and item['agree_latest']): nd += 1
    res['items'].append(item)
res['summary'] = {'pmSlotsWritten': npm, 'disagreements': nd, 'otherAddrSlots': len(writes) - npm,
                  'offAtBlockEqTrace': sum(1 for i in res['items'] if i['off_atBlock_eq_trace']),
                  'stillLatestOnReplica': sum(1 for i in res['items'] if norm(i['r1_latest']) == norm(i['tracePost']))}
print(res['summary'])
json.dump(res, open(out, 'w'), indent=1)
