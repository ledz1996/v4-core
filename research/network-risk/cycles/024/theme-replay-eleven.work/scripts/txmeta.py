"""Transaction metadata for the replay sample (cycle 24): type, number of calls of a Tempo batched transaction, feeToken
(Tempo), feeCurrency (Celo CIP-64), gas price fields (X Layer gasless transactions carry a zero price), from, to.
usage: txmeta.py <cid> <url> <window.json> <out.json>  (batched eth_getTransactionByHash, bracketed by web3_clientVersion)"""
import sys, json, urllib.request, ssl, time
from rpcu import call
CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
cid, url, wf, outp = int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
W = json.load(open(wf)); hs = [t[0] for t in W['txs']]
try: out = json.load(open(outp))
except Exception: out = {'meta': {}}
out['clientBefore'] = call(url, 'web3_clientVersion', [])
todo = [h for h in hs if h not in out['meta']]
BS = int(sys.argv[5]) if len(sys.argv) > 5 else 20
for j in range(0, len(todo), BS):
    part = todo[j:j + BS]
    for k in range(6):
        try:
            body = json.dumps([{'jsonrpc': '2.0', 'id': n, 'method': 'eth_getTransactionByHash', 'params': [h]} for n, h in enumerate(part)]).encode()
            r = json.loads(urllib.request.urlopen(urllib.request.Request(url, body, {'content-type': 'application/json', 'user-agent': 'rpc-client'}), timeout=60, context=CTX).read())
            if isinstance(r, dict): raise RuntimeError(str(r)[:200])
            for x in r:
                t = x.get('result')
                if not t: continue
                out['meta'][part[x['id']]] = {'type': t.get('type'), 'calls': len(t['calls']) if isinstance(t.get('calls'), list) else None, 'feeToken': t.get('feeToken'),
                    'feeCurrency': t.get('feeCurrency'), 'gasPrice': t.get('gasPrice'), 'maxFeePerGas': t.get('maxFeePerGas'), 'from': t.get('from'), 'to': t.get('to'),
                    'callTargets': [c.get('to') for c in t['calls']][:10] if isinstance(t.get('calls'), list) else None}
            break
        except Exception as e:
            time.sleep(2 + 3 * k)
out['clientAfter'] = call(url, 'web3_clientVersion', [])
json.dump(out, open(outp, 'w'))
print(cid, len(out['meta']), 'of', len(hs))
