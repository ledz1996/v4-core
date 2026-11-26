"""Retry prestateTracer for stored records that have none. usage: refetch_pre.py <cid> <url>. Read-only."""
import json, os, sys, gzip, glob, time
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/023/theme-state-replay.work/scripts')
from rpcu import call
from eps import NETS
cid = int(sys.argv[1]); url = sys.argv[2]; PM = NETS[cid]['poolManager'].lower()
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../raw/%d' % cid)
v, e = call(url, 'web3_clientVersion', [], 30); open(D + '/brackets.jsonl', 'a').write(json.dumps({'tag': 'refetch-start', 'url': url, 'client': v, 't': time.time()}) + '\n')
for fn in glob.glob(D + '/tx/*.json.gz'):
    r = json.load(gzip.open(fn))
    if r.get('pre') is not None: continue
    for k in range(6):
        p, e = call(url, 'debug_traceTransaction', [r['hash'], {'tracer': 'prestateTracer', 'tracerConfig': {'disableCode': True}}], 120)
        if p is not None: break
        open(D + '/errors.jsonl', 'a').write(json.dumps({'stage': 'refetch', 'url': url, 'tx': r['hash'], 'err': e[:200]}) + '\n'); time.sleep(5 + 5 * k)
    if p is None: print('fail', r['hash']); continue
    r['pre'] = {k: v for k, v in p.items() if k.lower() == PM}; [a.pop('code', None) for a in r['pre'].values()]; r['preUrl'] = url
    gzip.open(fn + '.tmp', 'wt').write(json.dumps(r)); os.rename(fn + '.tmp', fn); print('ok', r['hash'])
v, e = call(url, 'web3_clientVersion', [], 30); open(D + '/brackets.jsonl', 'a').write(json.dumps({'tag': 'refetch-end', 'url': url, 'client': v, 't': time.time()}) + '\n')
