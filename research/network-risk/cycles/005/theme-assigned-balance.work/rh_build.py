# Robinhood Chain: build selector families from (a) one token per code hash shared by more than 3 tokens, (b) up to 3 sampled tokens per code size.
import json, gzip, os, collections, hashlib, re
from concurrent.futures import ThreadPoolExecutor
from common import *
from tokcode import parse
from asm import SLOADER4, DRIVER80
cid = 4663
h = json.load(gzip.open(os.path.join(RAW, 'codehash_%d.json.gz' % cid)))
cnt = collections.Counter(h.values()); rep = {}
for t, x in h.items():
    if cnt[x] > 3 and x not in rep: rep[x] = t
print('shared hashes', len(rep), 'tokens covered', sum(cnt[x] for x in rep), flush=True)
us = urls2(cid); codes = {}
reps = list(rep.items())
def job(i):
    x, t = reps[i]
    for k in range(5):
        try:
            c = rpc(us[(i + k) % len(us)], 'eth_getCode', [t, 'latest'], timeout=60, tries=1)
            p = parse(c); p['rep'] = t; p['n'] = cnt[x]; return t, p
        except Exception as e: time.sleep(0.5 * (k + 1))
    return t, None
with ThreadPoolExecutor(6) as ex:
    for t, p in ex.map(job, range(len(reps))):
        if p: codes[t] = p
fam_s = json.load(gzip.open(os.path.join(RAW, 'rh_families.json.gz')))
for t, p in fam_s['code'].items(): codes.setdefault(t, p)
# proxies among representatives
cand = [t for t, p in codes.items() if p['kinds'] or (p['deleg'] and p['size'] < 4000)]
impl = {}
for i in range(0, len(cand), 150):
    ch = cand[i:i + 150]; ov = {STUB: {'code': DRIVER80}}
    for t in ch: ov[t] = {'code': SLOADER4}
    r = ecall(cid, STUB, '0x' + ''.join(adr(t) for t in ch), ov)
    if not isinstance(r, str) or len(r) != 2 + 256 * len(ch): print('fail', str(r)[:100]); continue
    for j, t in enumerate(ch):
        f = []
        for m in range(4):
            v = int(r[2 + 256 * j + 64 * m: 66 + 256 * j + 64 * m], 16)
            if v and v < 2 ** 160: f.append('0x%040x' % v)
        if not f: f = codes[t].get('emb') or []
        impl[t] = f
targets = sorted({a for f in impl.values() for a in f}); icode = {}
for i, a in enumerate(targets):
    try:
        c = rpc(us[i % len(us)], 'eth_getCode', [a, 'latest'], timeout=60, tries=3)
        if len(c) > 2: icode[a] = parse(c)
    except Exception as e: pass
print('reps', len(codes), 'proxy reps', len(cand), 'impl targets', len(targets), 'impl codes', len(icode), flush=True)
json.dump(dict(codes=codes, impl=impl, icode=icode), gzip.open(os.path.join(RAW, 'rh_codes.json.gz'), 'wt'))
