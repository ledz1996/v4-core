"""Task 4 (L-1241): send the cycle 32 2,000-vector sample (send2000.py, seed 3205) to mainnet.optimism.io in small
batches, each as one JSON-RPC batch request [web3_clientVersion, eth_call, web3_clientVersion], and attribute a batch
to a build only when both version answers in that request are equal. Batches are repeated (resampling batch order,
seed 33_1241_04) until each build seen has answered all 2,000 vectors or the request budget is spent. Read-only.
usage: python3 -I pin_op.py <out.json> [url] [budget]"""
import json, random, sys, time, urllib.request
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/032/theme-opstack-reth-binary-lift.work/scripts')
import battery, targeted, v4shapes
from evm import STUB, _ctx
OUT = sys.argv[1]
URL = sys.argv[2] if len(sys.argv) > 2 else 'https://mainnet.optimism.io'
BUDGET = int(sys.argv[3]) if len(sys.argv) > 3 else 600
V = [t for t in battery.vectors() if t[0] in battery.ID] + [t for t in targeted.vectors() if t[0] in battery.ID]
base = '/home/user/v4-core/research/network-risk/cycles/025/stablecoin-l1.work/'
for name in ('maxmod', 'maxmod2'):
    g = {'__file__': base + name + '.py', '__name__': name + '_v'}; exec(open(base + name + '.py').read().split("\nif __name__")[0], g)
    V += [('MULMOD', a, b, n) for a, b, n in g['vecs']()] + [('ADDMOD', a, b, n) for a, b, n in g['vecs']()]
V += [(op, a, b, c) for tag, op, a, b, c in v4shapes.vectors() if op in battery.ID]
S = random.Random(3205).sample(V, 2000)
code = battery.dispatcher()
SIZE = 50
batches = [S[i:i + SIZE] for i in range(0, len(S), SIZE)]
rnd = random.Random(33_1241_04)


def post(body):
    r = urllib.request.Request(URL, json.dumps(body).encode(), {'content-type': 'application/json', 'user-agent': 'curl/8'})
    with urllib.request.urlopen(r, timeout=90, context=_ctx) as f:
        return f.status, json.load(f)


out = {'url': URL, 'seed': 3205, 'orderSeed': 33_1241_04, 'batchSize': SIZE, 'requests': 0, 'builds': {}, 'unpinned': 0,
       'errors': [], 'started': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
need = {}
for k in range(BUDGET):
    seen = out['builds']
    # next batch: one not yet answered by every build seen so far
    order = list(range(len(batches))); rnd.shuffle(order)
    bi = next((i for i in order if any(i not in b['batches'] for b in seen.values())), order[0]) if seen else order[0]
    batch = batches[bi]; data = battery.encode(batch)
    body = [{'jsonrpc': '2.0', 'id': 1, 'method': 'web3_clientVersion', 'params': []},
            {'jsonrpc': '2.0', 'id': 2, 'method': 'eth_call', 'params': [{'to': STUB, 'data': '0x' + data.hex()}, 'latest',
                                                                          {STUB: {'code': '0x' + code.hex()}}]},
            {'jsonrpc': '2.0', 'id': 3, 'method': 'web3_clientVersion', 'params': []}]
    try:
        st, res = post(body); out['requests'] += 1
    except Exception as e:
        out['errors'].append(str(e)[:200]); out['requests'] += 1
        if 'HTTP Error 403' in str(e) or 'HTTP Error 429' in str(e):
            out['refused'] = str(e)[:200]; break
        time.sleep(3); continue
    res = {r.get('id'): r for r in res} if isinstance(res, list) else {}
    v1, v3 = res.get(1, {}).get('result'), res.get(3, {}).get('result')
    call = res.get(2, {})
    if v1 is None or v1 != v3 or 'result' not in call:
        out['unpinned'] += 1
        if 'error' in call:
            out['errors'].append(json.dumps(call['error'])[:200])
        continue
    b = seen.setdefault(v1, {'batches': {}, 'vectors': 0, 'mismatches': []})
    if bi in b['batches']:
        continue
    r = bytes.fromhex(call['result'][2:]); exp = battery.expected(batch, data)
    bad = []
    for j, (t, e) in enumerate(zip(batch, exp)):
        got = int.from_bytes(r[32 * j:32 * j + 32], 'big')
        if got != e:
            bad.append({'op': t[0], 'a': hex(t[1]), 'b': hex(t[2]), 'c': hex(t[3]), 'got': hex(got), 'want': hex(e)})
    b['batches'][bi] = len(batch); b['vectors'] += len(batch); b['mismatches'] += bad
    if seen and all(len(x['batches']) == len(batches) for x in seen.values()) and len(seen) >= 2:
        break
    time.sleep(0.3)
for b in out['builds'].values():
    b['batches'] = len(b['batches'])
out['finished'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
json.dump(out, open(OUT, 'w'), indent=1)
print(json.dumps({k: {'vectors': v['vectors'], 'mismatches': len(v['mismatches'])} for k, v in out['builds'].items()}),
      'requests', out['requests'], 'unpinned', out['unpinned'], 'errors', len(out['errors']))
