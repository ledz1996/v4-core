"""Producer check for theme-state-replay. A debug trace is a re-execution by the node that answers it, so the post
state in a prestate diff is what that node computed. The state a node serves through eth_getStorageAt at a block is
what was committed for the block. On Monad the committed state comes from block execution (the path that compiles
frequently used contracts), and on MegaETH and HyperEVM the official endpoint serves the producer's state while the
trace comes from a replica or an interpreter. For every block of the window, this takes the last traced post value of
every PoolManager word the window's transactions changed in that block, and the PoolManager's native balance, and
compares them with eth_getStorageAt and eth_getBalance at that block on the committed-state endpoint.
Only blocks whose window transactions were all traced are used.
usage: committed.py <chainId> <max_blocks> [url ...]"""
import json, os, sys, gzip, glob, time, collections
from rpcu import call
from eps import NETS
import urllib.request, ssl
CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
BS = 20
cid = int(sys.argv[1]); maxb = int(sys.argv[2]); urls = sys.argv[3:] or [NETS[cid]['rpc']]
PM = NETS[cid]['poolManager'].lower(); D = '../raw/%d' % cid
w = json.load(open(D + '/window.json'))
byblk = collections.defaultdict(list)
for h, b, i in w['txs']: byblk[b].append((i, h))
def batch(u, reqs):
    body = json.dumps([{'jsonrpc': '2.0', 'id': k, 'method': m, 'params': p} for k, (m, p) in enumerate(reqs)]).encode()
    rq = urllib.request.Request(u, body, {'content-type': 'application/json', 'user-agent': 'rpc-client'})
    r = json.loads(urllib.request.urlopen(rq, timeout=120, context=CTX).read())
    if isinstance(r, dict): raise RuntimeError(json.dumps(r)[:300])
    r = sorted(r, key=lambda x: x['id'])
    return [x.get('result') if 'result' in x else ('ERR', x.get('error')) for x in r]
res = {'chainId': cid, 'urls': urls, 'blocks': 0, 'words': 0, 'balances': 0, 'mismatch': [], 'skippedIncomplete': 0, 'errors': 0, 'errSamples': []}
res['clientBefore'] = [call(u, 'web3_clientVersion', [], 20) for u in urls]
done = 0; k = 0
for b in sorted(byblk, reverse=True):
    if done >= maxb: break
    txs = sorted(byblk[b]); recs = []
    ok = True
    for i, h in txs:
        p = '%s/tx/%s.json.gz' % (D, h)
        if not os.path.exists(p): ok = False; break
        recs.append(json.load(gzip.open(p)))
    if not ok: res['skippedIncomplete'] += 1; continue
    final = {}; bal = None
    for r in recs:
        dpre = next((v for kk, v in r['diff']['pre'].items() if kk.lower() == PM), {})
        dpost = next((v for kk, v in r['diff']['post'].items() if kk.lower() == PM), {})
        for s_ in set(dpre.get('storage') or {}) | set(dpost.get('storage') or {}):
            final[int(s_, 16)] = int((dpost.get('storage') or {}).get(s_, '0x0'), 16)
        if 'balance' in dpost: bal = int(dpost['balance'], 16)
    if not final and bal is None: continue
    reqs = [('eth_getStorageAt', [PM, hex(s_), hex(b)]) for s_ in sorted(final)]
    if bal is not None: reqs.append(('eth_getBalance', [PM, hex(b)]))
    got = None
    for t in range(3):
        u = urls[(k + t) % len(urls)]
        try:
            got = []
            for j in range(0, len(reqs), BS): got += batch(u, reqs[j:j + BS])
            if any(isinstance(x, tuple) for x in got): raise RuntimeError(str([x for x in got if isinstance(x, tuple)][:1]))
            break
        except Exception as e:
            got = None; res['errors'] += 1
            if len(res['errSamples']) < 10: res['errSamples'].append([u, b, str(e)[:200]])
            time.sleep(1 + t)
    k += 1
    if k % 100 == 0: print(json.dumps({'progress': k, 'blocks': res['blocks'], 'errors': res['errors'], 'mismatch': len(res['mismatch'])}), flush=True)
    if got is None: continue
    done += 1; res['blocks'] += 1
    for (s_, v), g in zip(sorted(final.items()), got):
        res['words'] += 1
        if int(g, 16) != v: res['mismatch'].append({'block': b, 'slot': hex(s_), 'traced': hex(v), 'committed': g, 'txs': [h for _, h in txs]})
    if bal is not None:
        res['balances'] += 1
        if int(got[-1], 16) != bal: res['mismatch'].append({'block': b, 'balance': True, 'traced': bal, 'committed': int(got[-1], 16), 'txs': [h for _, h in txs]})
res['clientAfter'] = [call(u, 'web3_clientVersion', [], 20) for u in urls]
json.dump(res, open(D + '/committed-%s.json' % urls[0].split('/')[2], 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != 'mismatch'}), 'mismatches', len(res['mismatch']))
