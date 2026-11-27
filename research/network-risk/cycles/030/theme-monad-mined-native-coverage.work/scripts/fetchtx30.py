"""For blocks whose whole-block trace exceeded the endpoint's response size limit: trace each transaction that has a
PoolManager log (eth_getLogs) on its own with the same three tracers, in fetch30's file format. Read-only.
Usage: python3 -I fetchtx30.py <logs.json> <outdir> <block> [block ...]"""
import sys, os, json, gzip
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rpc30 import R
import fetch30 as F
U = ['https://rpc.monad.xyz', 'https://rpc-mainnet.monadinfra.com']
L = json.load(open(sys.argv[1])); od = sys.argv[2]
for b in map(int, sys.argv[3:]):
    hs = list(dict.fromkeys(l['tx'] for l in L['logs'] if l['b'] == b)); txs = []
    for h in hs:
        rc = R(U, 'eth_getTransactionReceipt', [h])[0]
        ct = R(U, 'debug_traceTransaction', [h, {'tracer': 'callTracer', 'tracerConfig': {'withLog': True}}])[0]
        ps = R(U, 'debug_traceTransaction', [h, {'tracer': 'prestateTracer'}])[0]
        pd = R(U, 'debug_traceTransaction', [h, {'tracer': 'prestateTracer', 'tracerConfig': {'diffMode': True}}])[0]
        st = lambda a: None if a is None else {k: v for k, v in a.items() if k != 'code'}
        txs.append({'i': int(rc['transactionIndex'], 16), 'hash': h, 'call': ct, 'pre': st(ps.get(F.PM)),
                    'diff': {'pre': st(pd.get('pre', {}).get(F.PM)), 'post': st(pd.get('post', {}).get(F.PM))}})
    txs.sort(key=lambda t: t['i'])
    with gzip.open(os.path.join(od, f'{b}.json.gz'), 'wt') as f:
        json.dump({'block': b, 'ntx': None, 'keep': [t['i'] for t in txs], 'perTx': True, 'urls': U, 'txs': txs}, f)
    print(b, len(txs), flush=True)
