# Robinhood Chain: 294,326 distinct code hashes. Group currencies by code size, then fetch code for a few per size.
import sys, json, gzip, os, random, collections
from concurrent.futures import ThreadPoolExecutor
from common import *
from tokcode import parse
cid = 4663
SIZE_STUB = CODEHASH_STUB.replace('3f8152', '3b8152')
h = json.load(gzip.open(os.path.join(RAW, 'codehash_%d.json.gz' % cid)))
cnt = collections.Counter(h.values())
single = [t for t, x in h.items() if cnt[x] <= 3]
sizes = {}
def job(i):
    ch = single[i:i + 2000]
    r = ecall(cid, STUB, '0x' + ''.join(adr(t) for t in ch), {STUB: {'code': SIZE_STUB}}, rot=i // 2000)
    if not isinstance(r, str) or len(r) != 2 + 64 * len(ch): print('fail', i, str(r)[:100], flush=True); return {}
    return {t: int(r[2 + 64 * j: 66 + 64 * j], 16) for j, t in enumerate(ch)}
with ThreadPoolExecutor(4) as ex:
    for res in ex.map(job, range(0, len(single), 2000)): sizes.update(res)
by = collections.defaultdict(list)
for t, s in sizes.items(): by[s].append(t)
print('tokens', len(sizes), 'distinct sizes', len(by), flush=True)
json.dump({str(k): len(v) for k, v in by.items()}, open(os.path.join(RAW, 'rh_sizecount.json'), 'w'))
random.seed(7)
picks = []
for s, ts in by.items(): picks += random.sample(ts, min(3, len(ts)))
print('picks', len(picks), flush=True)
us = urls2(cid); out = {}
def job2(i):
    t = picks[i]
    for k in range(5):
        try:
            c = rpc(us[(i + k) % len(us)], 'eth_getCode', [t, 'latest'], timeout=60, tries=1)
            p = parse(c); p['rep'] = t; p['n'] = len(by[sizes[t]]); return t, p
        except Exception as e: time.sleep(0.5 * (k + 1))
    return t, None
with ThreadPoolExecutor(6) as ex:
    for t, p in ex.map(job2, range(len(picks))):
        if p: out[t] = p
json.dump(dict(sizes={t: sizes[t] for t in picks}, code=out), gzip.open(os.path.join(RAW, 'rh_families.json.gz'), 'wt'))
print('fetched', len(out), flush=True)
