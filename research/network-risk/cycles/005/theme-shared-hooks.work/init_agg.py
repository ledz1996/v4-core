# Hook census for chains with millions of pools: count pools per hook, keep the three latest pools of each hook as samples.
# Read-only: eth_getLogs. usage: python3 init_agg.py <chainId> <url> <chunk> <fromBlock> <toBlock> <workers> <tag>
import sys, json, gzip, threading, collections
from lib import *
from fetch import getlogs_range
INIT = '0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438'
cid = int(sys.argv[1]); url = sys.argv[2]; chunk = int(sys.argv[3]); lo = int(sys.argv[4]); hi = int(sys.argv[5]); workers = int(sys.argv[6]); tag = sys.argv[7]
pm = net(cid)['poolManager']; lock = threading.Lock()
cnt = collections.Counter(); dyn = collections.Counter(); samp = {}; total = [0]; hookless = []
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
st = getlogs_range(url, {'address': pm, 'topics': [INIT]}, lo, hi, chunk, workers=workers, on_logs=on, label='%d agg%s' % (cid, tag))
json.dump(dict(chainId=cid, url=url, lo=lo, hi=hi, nFail=len(st['fail']), fail=st['fail'][:20], req=st['req'], total=total[0], counts=dict(cnt), dyn=dict(dyn),
               rows=sorted(hookless)[-20:] + [r for s in samp.values() for r in sorted(s)[-3:]]), gzip.open('raw/agg_%d%s.json.gz' % (cid, tag), 'wt'))
print(cid, 'total', total[0], 'hooks', len(cnt), 'fail', len(st['fail']), 'req', st['req'])
for h, k in cnt.most_common(12): print('   ', h, k)
