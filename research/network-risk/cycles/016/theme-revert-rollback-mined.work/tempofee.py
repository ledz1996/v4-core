"""Read-only. Tempo: for PoolManager transactions, compare receipt logs with the surviving logs of the call trace
after removing receipt logs that the trace does not contain, and list what those extra logs are (address, topic0,
from, to). Usage: python3 tempofee.py <scan_4217.json> <n> <out.json>"""
import sys, json
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff'); sys.path.insert(0, '.')
import scan as S
d = json.load(open(sys.argv[1])); n = int(sys.argv[2]); u = 'https://rpc.mainnet.tempo.xyz'
txs = [r['tx'] for r in d['mismatch']][:n] + [r['tx'] for r in d['hits']]
res = []; kinds = {}
for h in txs:
    t = S.R(u, 'debug_traceTransaction', [h, {'tracer': 'callTracer', 'tracerConfig': {'withLog': True}}])
    ol = []; S.ordered_logs(t, False, ol)
    rec = S.R(u, 'eth_getTransactionReceipt', [h])
    rl = [(l['address'].lower(), tuple(x.lower() for x in l['topics']), l['data'].lower()) for l in rec['logs']]
    extra = [x for x in rl if x not in ol]
    rest = [x for x in rl if x in ol]
    for x in extra:
        k = (x[0][:12], x[1][0][:10], ('0x' + x[1][2][-40:]) if len(x[1]) > 2 else '')
        kinds[str(k)] = kinds.get(str(k), 0) + 1
    res.append({'tx': h, 'type': rec.get('type'), 'extraAtEnd': rl[len(rl) - len(extra):] == extra, 'restEqualsTraceInOrder': rest == ol, 'nExtra': len(extra)})
summ = {'txs': len(res), 'restEqual': sum(r['restEqualsTraceInOrder'] for r in res), 'extraAtEnd': sum(r['extraAtEnd'] for r in res), 'extraKinds': kinds}
json.dump({'summary': summ, 'rows': res}, open(sys.argv[3], 'w'), indent=1); print(json.dumps(summ))
