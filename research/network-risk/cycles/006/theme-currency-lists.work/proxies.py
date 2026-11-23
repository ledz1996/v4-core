# Resolve proxies among pooled currencies without batch requests: the proxy code is replaced by a stub that returns the
# usual implementation slots (state override, eth_call), then implementation code is fetched and its selectors listed.
import sys, json, gzip, os
from concurrent.futures import ThreadPoolExecutor
from common import *
from asm import SLOADER4, DRIVER80, DRIVERSEL
from tokcode import parse
def run(cid, per=150):
    hashes = json.load(gzip.open(os.path.join(RAW, 'codehash_%d.json.gz' % cid)))
    se = json.load(gzip.open(os.path.join(RAW, 'selectors_%d.json.gz' % cid)))
    cand = [t for t, h in hashes.items() if h in se and (se[h]['kinds'] or (se[h]['deleg'] and se[h]['size'] < 4000))]
    impl = {}
    def job(i):
        ch = cand[i:i + per]
        ov = {STUB: {'code': DRIVER80}}
        for t in ch: ov[t] = {'code': SLOADER4}
        r = ecall(cid, STUB, '0x' + ''.join(adr(t) for t in ch), ov, rot=i // per)
        o = {}
        if not isinstance(r, str) or len(r) != 2 + 256 * len(ch):
            print('fail', cid, i, str(r)[:160], flush=True); return o
        for j, t in enumerate(ch):
            found = []
            for m, kk in enumerate(('eip1967', 'beacon', 'zos', 'eip1822')):
                v = int(r[2 + 256 * j + 64 * m: 66 + 256 * j + 64 * m], 16)
                if v and v < 2 ** 160: found.append((kk, '0x%040x' % v))
            emb = se[hashes[t]].get('emb') or []
            if 'minimal' in se[hashes[t]]['kinds'] or (not found and emb): found += [('emb', e) for e in emb]
            o[t] = found
        return o
    with ThreadPoolExecutor(4) as ex:
        for res in ex.map(job, range(0, len(cand), per)): impl.update(res)
    # implementation() on unresolved candidates and on beacons
    unresolved = [t for t in cand if not impl.get(t)]
    beacons = sorted({a for t, f in impl.items() for k, a in f if k == 'beacon'})
    bimpl = {}
    ask = unresolved + beacons
    for i in range(0, len(ask), 200):
        ch = ask[i:i + 200]
        r = ecall(cid, STUB, '0x5c60da1b' + '0' * 56 + ''.join(adr(t) for t in ch), {STUB: {'code': DRIVERSEL}})
        if not isinstance(r, str) or len(r) != 2 + 64 * len(ch): print('implfn fail', cid, str(r)[:120], flush=True); continue
        for j, t in enumerate(ch):
            v = int(r[2 + 64 * j: 66 + 64 * j], 16)
            if v and v < 2 ** 160:
                if t in beacons: bimpl[t] = '0x%040x' % v
                else: impl[t] = [('implfn', '0x%040x' % v)]
    targets = set()
    for t, f in impl.items():
        for k, a in f: targets.add(bimpl.get(a, a) if k == 'beacon' else a)
    targets = sorted(targets); codes = {}
    us = urls2(cid)
    def job2(i):
        a = targets[i]
        for k in range(6):
            try:
                c = rpc(us[(i + k) % len(us)], 'eth_getCode', [a, 'latest'], timeout=60, tries=1)
                return a, parse(c) if isinstance(c, str) and len(c) > 2 else None
            except Exception as e: time.sleep(0.5 * (k + 1))
        return a, None
    with ThreadPoolExecutor(5) as ex:
        for a, p in ex.map(job2, range(len(targets))):
            if p: codes[a] = p
    json.dump(dict(impl=impl, beacon=bimpl, code=codes), gzip.open(os.path.join(RAW, 'proxies_%d.json.gz' % cid), 'wt'))
    print(cid, net(cid)['name'], 'proxy candidates', len(cand), 'resolved', sum(1 for f in impl.values() if f), 'targets', len(targets), 'impl codes', len(codes), flush=True)
if __name__ == '__main__':
    for c in sys.argv[1:]: run(int(c))
