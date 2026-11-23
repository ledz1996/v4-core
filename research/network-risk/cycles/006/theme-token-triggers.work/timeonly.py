# What does the passage of time alone do to the PoolManager balance of each target token? One block is pinned per network and
# the base trial (no call by A) is run with the block time moved by 0, 8 hours, 91 days and 400 days: balance read, hand-out of
# a third (mode A stub) and full balance transfer. Differences between the four runs come from the time only.
import sys, json, gzip, os
from concurrent.futures import ThreadPoolExecutor
from base import *
from sweep import item, DTS, MULTI_B
def run(cid, workers=5):
    disc = jz(os.path.join(RAW6, 'discover_%d.json.gz' % cid)); pm = net(cid)['poolManager'].lower()
    tov = json.load(open(os.path.join(RAW6, 'time_override.json')))
    us = [u for u in urls2(cid) if (tov.get(str(cid)) or {}).get(u, {}).get('ok')]
    if not us: print(cid, 'no endpoint with a time override'); return
    out = {}
    def job(t):
        o = disc[t]; b = int(o['bal'])
        if b < 3: return t, None
        res = {}
        for k in range(len(us)):
            u = us[(hash(t) + k) % len(us)]
            try:
                blk = rpc(u, 'eth_getBlockByNumber', ['latest', False], timeout=30, tries=2); bn = hex(int(blk['number'], 16) - 2); now = int(blk['timestamp'], 16)
                res = {}
                for dt in DTS:
                    for mode, stub, amt in (('A', MULTI, b // 3), ('B', MULTI_B, 0)):
                        data = '0x' + adr(t) + adr(A) + u256(amt) + adr(SINK) + item(adr(t) + sel('balanceOf(address)')[2:] + adr(pm))
                        r = ecall_t(cid, u, pm, data, {pm: {'code': stub}, A: {'code': FWD}}, gas=30_000_000, block=bn, dt=dt, now=now, timeout=60)
                        if not (isinstance(r, str) and len(r) == 2 + 512): raise Exception(str(r)[:100])
                        res['%s%d' % (mode, dt)] = [int(r[2 + 64 * m: 66 + 64 * m], 16) for m in range(8)]
                return t, dict(block=int(bn, 16), now=now, r=res)
            except Exception as e: res = {'err': str(e)[:120]}
        return t, res
    with ThreadPoolExecutor(workers) as ex:
        for t, r in ex.map(job, list(disc)):
            if r: out[t] = r
    json.dump(out, gzip.open(os.path.join(RAW6, 'timeonly_%d.json.gz' % cid), 'wt'))
    n = 0; errs = sum(1 for r in out.values() if 'err' in r)
    for t, r in out.items():
        if 'err' in r: continue
        x = r['r']; diffs = []
        for dt in DTS[1:]:
            for mode in 'AB':
                a = x['%s0' % mode]; b = x['%s%d' % (mode, dt)]
                if a[0] != b[0] or a[1] != b[1] or a[5] != b[5] or a[3] != b[3]:
                    diffs.append('%s+%d: bal %d->%d handout %d->%d full %d->%d' % (mode, dt, a[0], b[0], a[1], b[1], a[5], b[5]))
        if diffs:
            n += 1; print(' ', cid, t, disc[t]['sym'], '$%d' % min(disc[t]['usd'], 9e15), '|', ' ; '.join(diffs)[:420], flush=True)
    print(cid, net(cid)['name'], 'tokens', len(out), 'errors', errs, 'time dependent', n, flush=True)
if __name__ == '__main__':
    for c in sys.argv[1:]: run(int(c))
