# How many pooled BSC tokens share the implementation of the four BNC4 paying tokens, and how much BNC4 does a transfer by the
# PoolManager address release in total? eth_call with the MIRROR stub at the PoolManager address. Nothing is sent.
import sys, os, json, gzip
HERE2 = os.path.dirname(os.path.abspath(__file__))
T6 = os.path.join(HERE2, '..', '..', '006', 'theme-currency-lists.work')
sys.path.insert(0, T6)
from common import *
from mirror import MIRROR, SINK
from concurrent.futures import ThreadPoolExecutor
cid = 56; pm = net(cid)['poolManager']; X = '0x7c8d5502b544ddaf8852fc46d1174e34876d545c'
IMPL = '0xd442ecf61c6742167600bcf063e1d761304f8014'
d = json.load(gzip.open(os.path.join(T6, 'raw', 'proxies_56.json.gz')))['impl']
fam = sorted(t for t, lst in d.items() if any(im.lower() == IMPL for k, im in lst))
bal = json.load(gzip.open(os.path.join(T6, 'raw', 'bal_56.json.gz')))
held = [t for t in fam if bal.get(t) not in (None, 'fail') and int(bal[t]) > 2]
print('tokens on implementation', IMPL, len(fam), 'with a PoolManager balance in the cycle 6 list', len(held), flush=True)
def one(t):
    r = ecall(cid, pm, '0x' + adr(SINK) + adr(t) + adr(X) + adr(t), {pm: {'code': MIRROR}}, gas=30_000_000, rot=int(t[-2:], 16), tries=4)
    if isinstance(r, str) and len(r) == 2 + 256:
        v = [int(r[2 + 64 * i: 66 + 64 * i], 16) for i in range(4)]; return t, v
    return t, None
rows = []
with ThreadPoolExecutor(4) as ex:
    for t, v in ex.map(one, held): rows.append((t, v))
ok = [(t, v) for t, v in rows if v]; moved = [(t, v) for t, v in ok if v[2] != v[3]]; paid = [(t, v[1] - v[0]) for t, v in moved if v[1] != v[0]]
print('answered', len(ok), 'token moved', len(moved), 'BNC4 balance changed', len(paid), 'sum of BNC4 released', sum(p for t, p in paid), flush=True)
for t, p in sorted(paid, key=lambda x: -x[1])[:15]: print('  ', t, p)
json.dump(dict(impl=IMPL, family=len(fam), held=len(held), answered=len(ok), moved=len(moved), paid=[[t, str(p)] for t, p in paid], block=rpc(urls2(cid)[0], 'eth_blockNumber', [])),
          open(os.path.join(HERE2, 'raw', 'bnc4_family.json'), 'w'), indent=1)
