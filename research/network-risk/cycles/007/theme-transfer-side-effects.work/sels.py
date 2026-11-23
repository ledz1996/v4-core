# Selector list of every priced currency: own code and implementation code. Uses the cycle 5 and 6 files and fetches what they lack.
import sys, json, os
from concurrent.futures import ThreadPoolExecutor
from base import *
sys.path.insert(0, W6C)
from tokcode import parse
IMPL_SLOTS = ['0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc', '0x7050c9e0f4ca769c69bd3a8ef740bc37934f8e2c036e5a723fd8ee048ed3f8c3', '0xc5f16f0fcc639fa48a6947836d9850f504798523bf8c9a3a87d5876cf622bcf7']
BEACON = '0xa3f0ad74e5423aebfd80e3ef4346578335a9a72aeaee59ff6cb3582b35133d50'
def rr(cid, method, params, rot=0, tries=6):
    us = urls2(cid); last = None
    for k in range(tries):
        try: return rpc(us[(rot + k) % len(us)], method, params, timeout=60, tries=1)
        except Exception as e: last = str(e)[:200]; time.sleep(0.4 * (k + 1))
    return {'error': last}
def run(cid, workers=8):
    live = jz(os.path.join(RAW7, 'live_%d.json.gz' % cid))['rows']
    toks = sorted(live)
    out = {}
    def job(t):
        rot = hash(t) % 5
        c = rr(cid, 'eth_getCode', [t, 'latest'], rot)
        if not isinstance(c, str): return t, dict(err=str(c)[:100])
        p = parse(c); sels = set(p['sels']); impls = []
        emb = []
        b = bytes.fromhex(c[2:]); i = 0
        while i < len(b):
            op = b[i]
            if 0x60 <= op <= 0x7f:
                k = op - 0x5f
                if k == 20: emb.append('0x' + b[i + 1:i + 21].hex())
                i += 1 + k
            else: i += 1
        if p['deleg'] or len(b) < 3000:
            cands = set()
            for s in IMPL_SLOTS:
                v = rr(cid, 'eth_getStorageAt', [t, s, 'latest'], rot)
                if isinstance(v, str) and len(v) > 2 and 2 ** 24 < int(v, 16) < 2 ** 160: cands.add('0x%040x' % int(v, 16))
            v = rr(cid, 'eth_getStorageAt', [t, BEACON, 'latest'], rot)
            if isinstance(v, str) and len(v) > 2 and 2 ** 24 < int(v, 16) < 2 ** 160:
                r = ecall(cid, '0x%040x' % int(v, 16), '0x5c60da1b', rot=rot, tries=2)
                if isinstance(r, str) and len(r) == 66 and 2 ** 24 < int(r, 16) < 2 ** 160: cands.add('0x%040x' % int(r, 16))
            r = ecall(cid, t, '0x5c60da1b', rot=rot, tries=2)
            if isinstance(r, str) and len(r) == 66 and 2 ** 24 < int(r, 16) < 2 ** 160: cands.add('0x%040x' % int(r, 16))
            if len(b) < 200:
                for e in emb:
                    if len(e) == 42 and int(e, 16) > 2 ** 24 and e != '0x' + 'f' * 40: cands.add(e)
            for a in cands:
                c2 = rr(cid, 'eth_getCode', [a, 'latest'], rot)
                if isinstance(c2, str) and len(c2) > 2:
                    p2 = parse(c2); sels |= set(p2['sels']); impls.append(a)
                    b2 = bytes.fromhex(c2[2:]); i = 0
                    while i < len(b2):
                        op = b2[i]
                        if 0x60 <= op <= 0x7f:
                            k = op - 0x5f
                            if k == 20: emb.append('0x' + b2[i + 1:i + 21].hex())
                            i += 1 + k
                        else: i += 1
        emb = sorted(set(e for e in emb if len(e) == 42 and 2 ** 60 < int(e, 16) < 2 ** 160 - 2 ** 100))[:30]
        return t, dict(size=len(b), sels=sorted(sels), impls=impls, emb=emb)
    with ThreadPoolExecutor(workers) as ex:
        for n, (t, o) in enumerate(ex.map(job, toks)):
            out[t] = o
            if n % 1000 == 999: print(cid, n + 1, len(toks), flush=True)
    wz(os.path.join(RAW7, 'sels_%d.json.gz' % cid), out)
    print(cid, net(cid)['name'], 'tokens', len(out), 'errs', sum(1 for o in out.values() if 'err' in o), 'nocode', sum(1 for o in out.values() if o.get('size') == 0), 'withImpl', sum(1 for o in out.values() if o.get('impls')),
          'avg sels', sum(len(o.get('sels') or []) for o in out.values()) // max(1, len(out)), flush=True)
if __name__ == '__main__':
    for c in sys.argv[1:]: run(int(c))
