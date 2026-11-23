# For every token whose full balance transfer from the PoolManager was refused: does a transfer of one unit, of 1 percent or of the
# full balance to a second recipient pass (eth_call with from = PoolManager)? Classes: limit (a smaller amount passes), frozen (not
# even one unit passes), recipient (full passes to the other recipient). usage: python3 why_batch.py <chainId>
import sys, json, gzip, collections
from concurrent.futures import ThreadPoolExecutor
from common import *
from why2 import dec
cid = int(sys.argv[1]); pm = net(cid)['poolManager'].lower()
xf = json.load(gzip.open('raw/xfer_%d.json.gz' % cid)); odd = xf['odd']
rej = [t for t, w in odd.items() if w[0] != 'callfail' and w[0] > 0 and (w[1] & 1) and not (w[1] & 2)]
SINK = '0x00000000000000000000000000000000005111c0'; EOA = '0x1111111111111111111111111111111111111111'
import random
if len(sys.argv) > 2:
    random.seed(6); rej = random.sample(rej, min(len(rej), int(sys.argv[2]))); print('sample of', len(rej), flush=True)
def one(t):
    b = odd[t][0]; o = {}
    for label, to, amt in (('one', SINK, 1), ('1pct', SINK, b // 100), ('half', SINK, b // 2), ('full_eoa', EOA, b), ('full', SINK, b)):
        r = ecall(cid, t, sel('transfer(address,uint256)') + adr(to) + u256(amt), frm=pm, gas=3_000_000, rot=int(t[-3:], 16))
        o[label] = dec(r if isinstance(r, str) else {'error': r.get('error')})
    ok = lambda k: o[k].startswith('ok') and (o[k].endswith('empty') or o[k].endswith('1'))
    o['cls'] = 'passes-now' if ok('full') else 'recipient' if ok('full_eoa') else 'limit' if (ok('half') or ok('1pct') or ok('one')) else 'frozen'
    o['bal'] = str(b); return t, o
with ThreadPoolExecutor(3) as ex: res = dict(ex.map(one, rej))
json.dump(res, gzip.open('raw/why_%d.json.gz' % cid, 'wt'))
c = collections.Counter(o['cls'] for o in res.values()); print(cid, 'rejected', len(rej), 'of', sum(1 for t, w in odd.items() if w[0] != 'callfail' and w[0] > 0 and (w[1] & 1) and not (w[1] & 2)), dict(c))
msgs = collections.Counter(o['one'][:110] for o in res.values() if o['cls'] == 'frozen'); 
for m, k in msgs.most_common(25): print('  ', k, m)
