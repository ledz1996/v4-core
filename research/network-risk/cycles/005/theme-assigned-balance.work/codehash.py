# For every currency with a balance at the PoolManager: EXTCODEHASH through a stub placed by state override.
import sys, json, gzip, os
from concurrent.futures import ThreadPoolExecutor
from common import *
def run(cid, per=2000):
    d, rows = universe(cid)
    toks = [r['token'] for r in rows if int(r.get('bal2') or 0) > 0 and r['token'] != '0x' + '0' * 40]
    us = urls(cid)
    if cid == 196: us = ['https://xlayerrpc.okx.com']
    out = {}
    def job(i):
        chunk = toks[i:i + per]
        data = '0x' + ''.join(adr(t) for t in chunk)
        last = None
        for k in range(6):
            u = us[k % len(us)]
            try:
                r = call_override(u, STUB, data, {STUB: {'code': CODEHASH_STUB}}, timeout=90)
                assert len(r) == 2 + 64 * len(chunk), 'short'
                return {t: r[2 + 64 * j: 66 + 64 * j] for j, t in enumerate(chunk)}
            except Exception as e:
                last = str(e)[:150]; time.sleep(1 + k)
        print('fail', cid, i, last, flush=True)
        return {}
    with ThreadPoolExecutor(6) as ex:
        for res in ex.map(job, range(0, len(toks), per)):
            out.update(res)
    json.dump(out, gzip.open(os.path.join(RAW, 'codehash_%d.json.gz' % cid), 'wt'))
    print(cid, net(cid)['name'], 'tokens', len(toks), 'hashed', len(out), 'unique', len(set(out.values())), flush=True)
if __name__ == '__main__':
    for c in sys.argv[1:]: run(int(c))
