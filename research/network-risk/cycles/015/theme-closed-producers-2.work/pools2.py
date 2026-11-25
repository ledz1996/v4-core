"""Pool keys of the v3 style emitters on HyperEVM read from the pools themselves (factory, token0, token1, fee, tickSpacing)
and checked against factory.getPool(token0, token1, fee). Replaces the slow PoolCreated scan of factories.py. Read only.
Writes raw/pools999.json in the shape v3check.py reads."""
import sys, os, json, collections, urllib.request, ssl, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
U = 'https://rpc.purroofgroup.com'
CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
def batch(calls):
    out = [None] * len(calls)
    for i in range(0, len(calls), 100):
        part = calls[i:i + 100]
        req = [{'jsonrpc': '2.0', 'id': j, 'method': 'eth_call', 'params': [{'to': t, 'data': d}, 'latest']} for j, (t, d) in enumerate(part)]
        for k in range(6):
            try:
                r = json.loads(urllib.request.urlopen(urllib.request.Request(U, json.dumps(req).encode(), {'content-type': 'application/json'}), timeout=120, context=CTX).read())
                for x in r: out[i + x['id']] = x.get('result')
                break
            except Exception:
                time.sleep(2 + k)
    return out
cnt = collections.Counter()
for line in open('raw/logs999.jsonl'):
    for r in json.loads(line)['rows']:
        if r[0] == 'S': cnt[r[4]] += 1
em = [a for a, n in cnt.most_common() if n >= 50]
sels = ['0xc45a0155', '0x0dfe1681', '0xd21220a7', '0xddca3f43', '0xd0c93a7c']  # factory token0 token1 fee tickSpacing
res = batch([(a, s) for a in em for s in sels])
pools = {}; bad = collections.Counter()
chk = []
for i, a in enumerate(em):
    v = res[5 * i:5 * i + 5]
    if any((x is None or len(x) != 66) for x in v): bad['noKey'] += cnt[a]; continue
    f, t0, t1 = '0x' + v[0][-40:], '0x' + v[1][-40:], '0x' + v[2][-40:]
    fee = int(v[3], 16); ts = int(v[4], 16); ts = ts - (1 << 256) if ts >> 255 else ts
    if not (0 < ts < 32768) or fee >= 10 ** 6: bad['oddKey'] += cnt[a]; continue
    pools[a] = {'factory': f, 'fee': fee, 'tickSpacing': ts, 'token0': t0, 'token1': t1}
    chk.append((f, '0x1698ee82' + t0[2:].rjust(64, '0') + t1[2:].rjust(64, '0') + hex(fee)[2:].rjust(64, '0')))
gp = batch(chk)
ok = {}
for (a, p), g in zip(list(pools.items()), gp):
    if g and len(g) == 66 and '0x' + g[-40:] == a: ok[a] = p
    else: bad['getPoolMismatch'] += cnt[a]
fac = collections.Counter()
for a, p in ok.items(): fac[p['factory']] += cnt[a]
json.dump({'pools': ok, 'swapCount': {p: cnt[p] for p in ok}, 'factorySwaps': dict(fac), 'totalSwaps': sum(cnt.values()),
           'covered': sum(cnt[p] for p in ok), 'excluded': dict(bad), 'method': 'pool getters + factory.getPool'}, open('raw/pools999.json', 'w'), indent=0)
print('emitters>=50', len(em), 'pools', len(ok), 'covered', sum(cnt[p] for p in ok), 'of', sum(cnt.values()), dict(bad))
print(fac.most_common(12))
