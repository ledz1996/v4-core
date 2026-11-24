import gzip, json, collections
from common import *
d = json.load(gzip.open('/home/user/v4-core/research/network-risk/cycles/012/theme-mined-liquidity-2.work/raw/monad-scan.json.gz'))
c = collections.Counter(); txs = collections.defaultdict(set)
for l in d['logs']:
    n = EV.get(l['topics'][0], l['topics'][0][:10]); c[n] += 1
    if n == 'Transfer6909':
        caller = '0x' + l['data'][26:66]; fr = '0x' + l['topics'][1][26:]; to = '0x' + l['topics'][2][26:]
        k = 'mint' if int(fr, 16) == 0 else 'burn' if int(to, 16) == 0 else ('transfer' if caller == fr else 'transferFromOther')
        c['6909:' + k] += 1; txs['6909:' + k].add(l['tx'])
    txs[n].add(l['tx'])
print(d['fromBlock'], d['hi'], dict(c)); print({k: len(v) for k, v in txs.items()})
