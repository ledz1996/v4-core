# Find the storage slot behind balanceOf(A) for each target token, so that the ordinary account A can be given a balance by
# state override without the PoolManager sending anything (a transfer by the PoolManager resets inactivity timers).
# All candidate slots are written at once with distinct values; the value that balanceOf(A) returns names the slot.
import sys, json, gzip, os
from concurrent.futures import ThreadPoolExecutor
from base import *
from keccak import keccak256
def h(b): return '0x' + keccak256(b).hex()
a20 = bytes.fromhex(A[2:]); a32 = a20.rjust(32, b'\0')
CAND = []
for s in range(0, 72):
    CAND.append(('sol', s, h(a32 + s.to_bytes(32, 'big'))))
    CAND.append(('vy', s, h(s.to_bytes(32, 'big') + a32)))
for nm, base in (('oz5', 0x52c63247e1f47db19d5ce0460030c497f067ca4cebf71ba98eeadabe20bace00),):
    for k in range(0, 3): CAND.append((nm, k, h(a32 + (base + k).to_bytes(32, 'big'))))
CAND.append(('solady', 0, h(a20 + b'\0' * 8 + bytes.fromhex('87a211a2'))))
# other namespaced layouts found by hand can be appended here
UNIT = 10 ** 15
def find(cid, t, holders, rot=0):
    """returns (holder address, kind, n, slot, factor) or None"""
    for hd in holders:
        diff = {c[2]: '0x' + u256(UNIT * (i + 1)) for i, c in enumerate(CAND)}
        r = ecall(cid, t, sel('balanceOf(address)') + adr(A), {hd: {'stateDiff': diff}}, rot=rot)
        if not isinstance(r, str) or len(r) < 66: continue
        v = int(r[2:66], 16)
        if v == 0: continue
        if v % UNIT == 0 and 1 <= v // UNIT <= len(CAND):
            c = CAND[v // UNIT - 1]; return dict(holder=hd, kind=c[0], n=c[1], slot=c[2], exact=True)
        # scaled or packed: test candidates one by one
        r0 = ecall(cid, t, sel('balanceOf(address)') + adr(A), rot=rot)
        v0 = int(r0[2:66], 16) if isinstance(r0, str) and len(r0) >= 66 else 0
        for c in CAND:
            r = ecall(cid, t, sel('balanceOf(address)') + adr(A), {hd: {'stateDiff': {c[2]: '0x' + u256(10 ** 24)}}}, rot=rot)
            if isinstance(r, str) and len(r) >= 66 and int(r[2:66], 16) != v0:
                return dict(holder=hd, kind=c[0], n=c[1], slot=c[2], exact=False, got=str(int(r[2:66], 16)))
    return None
def run(cid, workers=6):
    fn = os.path.join(RAW6, 'discover_%d.json.gz' % cid); d = jz(fn)
    def job(x):
        t, o = x
        if 'err' in o: return t, None, None
        ts = ecall(cid, t, sel('totalSupply()'), rot=hash(t) % 5)
        ts = int(ts[2:66], 16) if isinstance(ts, str) and len(ts) >= 66 else 0
        return t, find(cid, t, [t] + [a for a, r in o['rel'].items() if r['kind'] == 'acl'], rot=hash(t) % 5), ts
    out = {}
    with ThreadPoolExecutor(workers) as ex:
        for t, f, ts in ex.map(job, list(d.items())):
            if f: f['totalSupply'] = str(ts); out[t] = f
    json.dump(out, gzip.open(os.path.join(RAW6, 'slots_%d.json.gz' % cid), 'wt'))
    print(cid, net(cid)['name'], 'tokens', len(d), 'slot found', len(out), 'exact', sum(1 for f in out.values() if f['exact']), flush=True)
if __name__ == '__main__':
    for c in sys.argv[1:]: run(int(c))
