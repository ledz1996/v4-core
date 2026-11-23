# What does every hook address hold? For one network: ERC-6909 claims at the PoolManager (pairs from the cycle 5 claim mint logs
# plus every hook x the most used currencies), ERC-20 balances of the most used currencies, and the native balance.
# Read-only: eth_call through Multicall3 aggregate3. usage: python3 rank.py <chainId>
import sys, glob, collections, threading, time
from common import *
import concurrent.futures as cf
os.chdir(C5)
from summ import census
os.chdir(HERE)
Z = '0x' + '0' * 40
def main(cid):
    n = net(cid); pm = n['poolManager'].lower()
    os.chdir(C5); cnt, dyn, rows, total, cov = census(cid); os.chdir(HERE)
    hooks = sorted(h for h in cnt if h != Z); hs = set(hooks)
    cur = collections.Counter()
    for r in rows:
        if r[6] != Z: cur[r[2]] += 1; cur[r[3]] += 1
    top = [c for c, _ in cur.most_common(14)]
    if Z not in top: top.append(Z)
    pairs = set(); nm = 0
    for f in glob.glob(os.path.join(C5U, 'raw', 'mints_%d_*.jsonl.gz' % cid)):
        for line in gzip.open(f, 'rt'):
            nm += 1
            # row: block, tx, logIndex, caller, to, id, amount
            i = line.find('"0x', 80)  # cheap prefilter is not reliable; parse
            r = json.loads(line)
            if r[4] in hs: pairs.add((r[4], '0x' + r[5][-40:]))
    mintPairs = len(pairs)
    for h in hooks:
        for c in top[:5] if len(hooks) > 20000 else top: pairs.add((h, c))
    calls = []  # (kind, hook, cur, target, data)
    for h, c in sorted(pairs): calls.append(('claim', h, c, pm, '00fdd58e' + adr(h) + adr(c)))
    for h in hooks:
        calls.append(('native', h, Z, MC3, '4d2301cc' + adr(h)))
        for c in top:
            if c != Z: calls.append(('erc20', h, c, c, '70a08231' + adr(h)))
    print(cid, n['name'], 'hooks', len(hooks), 'mint rows', nm, 'mint pairs with hook receiver', mintPairs, 'calls', len(calls), 'top', top, flush=True)
    us = urls(cid); res = {}; lock = threading.Lock(); fails = []
    B = 1200 if cid not in (999,) else 300
    def one(chunk, depth=0):
        last = None
        for u in us:
            try:
                out = mc3(u, [(t, d) for _, _, _, t, d in chunk]); break
            except Exception as e: last = repr(e)[:160]; out = None
        if out is None:
            if len(chunk) > 20:
                m = len(chunk) // 2; one(chunk[:m], depth + 1); one(chunk[m:], depth + 1); return
            with lock: fails.append((len(chunk), last)); return
        with lock:
            for (k, h, c, _, _), (ok, b) in zip(chunk, out):
                if ok and len(b) >= 64:
                    v = int(b[:64], 16)
                    if v: res[(k, h, c)] = v
    chunks = [calls[i:i + B] for i in range(0, len(calls), B)]
    bn = int(rpc(us[0], 'eth_blockNumber', []), 16)
    done = 0
    with cf.ThreadPoolExecutor(4) as ex:
        for _ in ex.map(one, chunks):
            done += 1
            if done % 100 == 0: print(cid, 'chunks', done, '/', len(chunks), 'nonzero', len(res), 'fails', len(fails), flush=True)
    out = dict(chainId=cid, block=bn, url=us[0], hooks=len(hooks), mintRows=nm, mintPairs=mintPairs, calls=len(calls), top=top, fails=fails[:30], nFails=len(fails),
               rows=[[k, h, c, str(v)] for (k, h, c), v in sorted(res.items())])
    json.dump(out, gzip.open(os.path.join(RAW, 'rank_%d.json.gz' % cid), 'wt'))
    print(cid, 'done block', bn, 'nonzero', len(res), 'fails', len(fails), fails[:3], flush=True)
if __name__ == '__main__': main(int(sys.argv[1]))
