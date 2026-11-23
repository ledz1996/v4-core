# Does a transfer made by the PoolManager itself (one third of its balance) leave it with more or less than balance minus amount?
# More means that any transfer can start a rise of the reported balance (auto rebase, reflection); less means a sender side charge.
import sys, json, gzip, os
from concurrent.futures import ThreadPoolExecutor
from common import *
from asm import THIRD
RCP = '0x00000000000000000000000000000000000a11ce'
def run(cid, per=150, workers=5):
    d, rows = universe(cid)
    toks = [r['token'] for r in rows if int(r.get('bal2') or 0) > 2 and r['token'] != '0x' + '0' * 40]
    pm = net(cid)['poolManager']
    def one(chunk, depth=0):
        r = ecall(cid, pm, '0x' + adr(RCP) + ''.join(adr(t) for t in chunk), {pm: {'code': THIRD}}, gas=45_000_000, rot=depth + len(chunk))
        if isinstance(r, str) and len(r) == 2 + 256 * len(chunk):
            return {t: [int(r[2 + 256 * j + 64 * m: 66 + 256 * j + 64 * m], 16) for m in range(4)] for j, t in enumerate(chunk)}
        if len(chunk) > 1:
            h = len(chunk) // 2; o = one(chunk[:h], depth + 1); o.update(one(chunk[h:], depth + 1)); return o
        return {}
    out = {}
    with ThreadPoolExecutor(workers) as ex:
        for res in ex.map(lambda i: one(toks[i:i + per]), range(0, len(toks), per)): out.update(res)
    odd = {}
    for t, (b0, ok, b1, ba) in out.items():
        if not ok or b0 < 3: continue
        amt = b0 // 3; d1 = b1 - (b0 - amt)
        if d1 != 0: odd[t] = [str(b0), str(amt), str(d1), str(ba - amt)]
    json.dump(dict(chainId=cid, tested=len(out), odd=odd), gzip.open(os.path.join(RAW, 'third_%d.json.gz' % cid), 'wt'))
    up = sum(1 for v in odd.values() if int(v[2]) > 0); dn = len(odd) - up
    nofee_up = sum(1 for v in odd.values() if int(v[2]) > 0 and int(v[3]) >= 0)
    print(cid, net(cid)['name'], 'tested', len(out), 'senderKeepsMore', up, 'ofWhichRecipientGotFull', nofee_up, 'senderLosesMore', dn, flush=True)
if __name__ == '__main__':
    for c in sys.argv[1:]: run(int(c))
