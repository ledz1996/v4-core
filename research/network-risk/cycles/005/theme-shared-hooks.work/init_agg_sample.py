# Sampled hook census for a dense block range: read every k-th window of 1000 blocks, count pools per hook, keep three latest pools per hook.
# Read-only: eth_getLogs. usage: python3 init_agg_sample.py <chainId> <url> <fromBlock> <toBlock> <k> <offset> <workers> <tag>
import sys, json, gzip, threading, collections, concurrent.futures as cf
from lib import *
from fetch import getlogs_range
INIT = '0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438'
cid = int(sys.argv[1]); url = sys.argv[2]; lo = int(sys.argv[3]); hi = int(sys.argv[4]); K = int(sys.argv[5]); off = int(sys.argv[6]); workers = int(sys.argv[7]); tag = sys.argv[8]
pm = net(cid)['poolManager']; lock = threading.Lock()
cnt = collections.Counter(); dyn = collections.Counter(); samp = {}; total = [0]; hookless = []; fails = []; done = [0]
def on(logs):
    with lock:
        for l in logs:
            if l.get('removed'): continue
            d = l['data'][2:]; t = l['topics']; h = '0x' + d[128:192][-40:]
            row = (int(l['blockNumber'], 16), t[1], '0x' + t[2][-40:], '0x' + t[3][-40:], int(d[0:64], 16), int(d[64:128], 16), h, l['transactionHash'])
            total[0] += 1; cnt[h] += 1
            if row[4] == 0x800000: dyn[h] += 1
            if int(h, 16) == 0:
                hookless.append(row)
                if len(hookless) > 40: hookless[:] = sorted(hookless)[-20:]
            else:
                s = samp.setdefault(h, []); s.append(row)
                if len(s) > 6: s[:] = sorted(s)[-3:]
wins = [a for i, a in enumerate(range(lo, hi + 1, 1000)) if i % K == off]
def one(a):
    st = getlogs_range(url, {'address': pm, 'topics': [INIT]}, a, min(a + 999, hi), 1000, workers=1, on_logs=on)
    with lock:
        fails.extend(st['fail']); done[0] += 1
        if done[0] % 200 == 0: print('windows', done[0], '/', len(wins), 'logs', total[0], flush=True)
with cf.ThreadPoolExecutor(workers) as ex: list(ex.map(one, wins))
json.dump(dict(chainId=cid, url=url, lo=lo, hi=hi, sampleEvery=K, windows=len(wins), nFail=len(fails), fail=fails[:20], total=total[0], counts=dict(cnt), dyn=dict(dyn),
               rows=sorted(hookless)[-20:] + [r for s in samp.values() for r in sorted(s)[-3:]]), gzip.open('raw/agg_%d%s.json.gz' % (cid, tag), 'wt'))
print(cid, 'sampled total', total[0], 'hooks', len(cnt), 'fail', len(fails))
for h, k in cnt.most_common(12): print('   ', h, k)
