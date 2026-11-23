# For every unique code hash among pooled currencies: fetch the code once, list PUSH4 operands, note proxy patterns.
import sys, json, gzip, os, random
from concurrent.futures import ThreadPoolExecutor
from common import *
SLOTS = {
 '360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc': 'eip1967',
 'a3f0ad74e5423aebfd80e3ef4346578335a9a72aeaee59ff6cb3582b35133d50': 'beacon',
 '7050c9e0f4ca769c69bd3a8ef740bc37934f8e2c036e5a723fd8ee048ed3f8c3': 'zos',
 'c5f16f0fcc639fa48a6947836d9850f504798523bf8c9a3a87d5876cf622bcf7': 'eip1822',
}
EMPTY = ('c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470', '0' * 64)
def parse(code):
    b = bytes.fromhex(code[2:])
    sels = set(); i = 0; n = len(b); deleg = False; embedded = []
    while i < n:
        op = b[i]
        if 0x60 <= op <= 0x7f:
            k = op - 0x5f
            arg = b[i + 1:i + 1 + k]
            if k == 4: sels.add(arg.hex())
            elif k == 3: sels.add('00' + arg.hex())
            elif k == 20: embedded.append('0x' + arg.hex())
            i += 1 + k
        else:
            if op == 0xf4: deleg = True
            i += 1
    h = code[2:]
    kinds = [v for k, v in SLOTS.items() if k in h]
    if h.startswith('363d3d373d3d3d363d73') or h.startswith('36603057343d5230'): kinds.append('minimal')
    if h.startswith('ef0100'): kinds.append('7702')
    return dict(size=n, sels=sorted(sels), deleg=deleg, kinds=kinds, emb=embedded[:6] if (deleg and n < 3000) else [])
def run(cid, per=20, workers=8):
    if cid == 196: per, workers = 5, 3
    hashes = json.load(gzip.open(os.path.join(RAW, 'codehash_%d.json.gz' % cid)))
    rep = {}
    cnt = {}
    for t, h in hashes.items():
        cnt[h] = cnt.get(h, 0) + 1
        if h not in rep: rep[h] = t
    fn = os.path.join(RAW, 'selectors_%d.json.gz' % cid)
    out = json.load(gzip.open(fn)) if os.path.exists(fn) else {}
    todo = [h for h in rep if h not in EMPTY and h not in out]
    us = urls(cid)
    if cid == 196: us = ['https://xlayerrpc.okx.com']
    def job(i):
        hs = todo[i:i + per]
        last = None
        for k in range(8):
            u = us[(i // per + k) % len(us)]
            try:
                res = batch(u, [('eth_getCode', [rep[h], 'latest']) for h in hs], timeout=90)
                o = {}
                for h, c in zip(hs, res):
                    if isinstance(c, str) and len(c) > 2:
                        p = parse(c); p['rep'] = rep[h]; p['n'] = cnt[h]; o[h] = p
                if len(o) < len(hs) * 0.5 and k < 7: raise Exception('partial %d/%d %s' % (len(o), len(hs), str(res[0])[:80]))
                return o
            except Exception as e:
                last = str(e)[:150]; time.sleep(0.5 + k)
        print('fail', cid, i, last, flush=True)
        return {}
    done = 0
    with ThreadPoolExecutor(workers) as ex:
        for res in ex.map(job, range(0, len(todo), per)):
            out.update(res); done += per
            if done % 4000 == 0:
                print(cid, 'progress', done, len(todo), flush=True)
                json.dump(out, gzip.open(fn, 'wt'))
    json.dump(out, gzip.open(fn, 'wt'))
    print(cid, net(cid)['name'], 'unique', len(rep), 'parsed', len(out), flush=True)
if __name__ == '__main__':
    for c in sys.argv[1:]: run(int(c))
