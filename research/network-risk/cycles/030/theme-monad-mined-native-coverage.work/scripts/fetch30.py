"""Fetch callTracer (with logs), prestateTracer and prestateTracer diffMode for whole Monad blocks; keep the transactions whose call
tree reaches the PoolManager (successful or failed). Read-only. Usage: python3 -I fetch30.py <blocks.txt> <outdir> <threads> url [url ...]"""
import sys, os, json, gzip, time
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rpc30 import R
PM = '0x188d586ddcf52439676ca21a244753fa19f9ea8e'
def touches(n):
    if (n.get('to') or '').lower() == PM: return True
    return any(touches(c) for c in n.get('calls', []))
def one(b, urls, od):
    fn = os.path.join(od, f'{b}.json.gz')
    if os.path.exists(fn): return 'have'
    try:
        ct, u1 = R(urls, 'debug_traceBlockByNumber', [hex(b), {'tracer': 'callTracer', 'tracerConfig': {'withLog': True}}], timeout=180)
        keep = [i for i, t in enumerate(ct) if 'result' in t and touches(t['result'])]
        rec = {'block': b, 'ntx': len(ct), 'keep': keep, 'urls': [u1]}
        if keep:
            ps, u2 = R(urls, 'debug_traceBlockByNumber', [hex(b), {'tracer': 'prestateTracer'}], timeout=180)
            pd, u3 = R(urls, 'debug_traceBlockByNumber', [hex(b), {'tracer': 'prestateTracer', 'tracerConfig': {'diffMode': True}}], timeout=180)
            assert len(ps) == len(ct) == len(pd)
            def strip(a):
                if a is None: return None
                a = dict(a); c = a.pop('code', None)
                if c is not None: a['codeLen'] = (len(c) - 2) // 2
                return a
            def pmonly(x):
                r = x.get('result', {})
                if 'pre' in r: return {'pre': strip(r['pre'].get(PM)), 'post': strip(r.get('post', {}).get(PM))}
                return strip(r.get(PM))
            rec['txs'] = [{'i': i, 'hash': ct[i].get('txHash'), 'call': ct[i]['result'], 'pre': pmonly(ps[i]), 'diff': pmonly(pd[i])} for i in keep]
            rec['urls'] += [u2, u3]
        with gzip.open(fn + '.tmp', 'wt') as f: json.dump(rec, f)
        os.rename(fn + '.tmp', fn); return len(keep)
    except Exception as e:
        return 'error ' + str(e)[:200]
if __name__ == '__main__':
    bl = [int(x) for x in open(sys.argv[1]).read().split()]; od = sys.argv[2]; nth = int(sys.argv[3]); urls = sys.argv[4:]
    os.makedirs(od, exist_ok=True)
    cv = {u: R(u, 'web3_clientVersion', [])[0] for u in urls}
    json.dump({'t': time.time(), 'clientVersion': cv}, open(os.path.join(od, f'_cv_before_{int(time.time())}.json'), 'w'))
    with ThreadPoolExecutor(nth) as ex:
        for b, r in zip(bl, ex.map(lambda b: one(b, urls, od), bl)): print(b, r, flush=True)
    cv = {u: R(u, 'web3_clientVersion', [])[0] for u in urls}
    json.dump({'t': time.time(), 'clientVersion': cv}, open(os.path.join(od, f'_cv_after_{int(time.time())}.json'), 'w'))
