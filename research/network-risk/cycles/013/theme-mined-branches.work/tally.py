"""Event-level tally of a PoolManager log dump: kinds of logs and of ERC-6909 transfers."""
import sys, json, gzip, collections
from common import *
p = sys.argv[1]; d = json.load(gzip.open(p) if p.endswith('.gz') else open(p))
c = collections.Counter(); txs = collections.defaultdict(set)
for l in d['logs']:
    n = EV.get(l['topics'][0], l['topics'][0][:10]); c[n] += 1; txs[n].add(l['tx'])
    if n == 'Transfer6909':
        caller = '0x' + l['data'][26:66]; fr = '0x' + l['topics'][1][26:]; to = '0x' + l['topics'][2][26:]
        k = 'mint' if int(fr, 16) == 0 else 'burn' if int(to, 16) == 0 else ('transfer' if caller == fr else 'transferByOther')
        if k == 'burn' and caller != fr: k = 'burnByOther'
        c['6909:' + k] += 1; txs['6909:' + k].add(l['tx'])
    if n == 'Initialize':
        fee = int(l['data'][2:66], 16); hooks = int(l['data'][130:194], 16)
        if fee == 0x800000: c['init:dynamicFee'] += 1
        for bit, nm in ((3, 'bsRD'), (2, 'asRD'), (1, 'aalRD'), (0, 'arlRD')):
            if hooks >> bit & 1 and hooks: c['init:hookFlag:' + nm] += 1
lo = d.get('lo', d.get('fromBlock')); hi = d.get('hi')
print(json.dumps({'blocks': [lo, hi], 'logs': dict(c), 'txs': {k: len(v) for k, v in txs.items()}}))
