# Full balance transfer test: a measuring stub at the PoolManager address (state override, eth_call only)
# sends the whole balance of every pooled currency to a sink and reads balances after.
import sys, json, gzip, os
from concurrent.futures import ThreadPoolExecutor
from common import *
from asm import XFER
SINK = '0x00000000000000000000000000000000005111c0'
def run(cid, per=150, workers=6, gas=45_000_000):
    d, rows = universe(cid)
    toks = [r['token'] for r in rows if int(r.get('bal2') or 0) > 0 and r['token'] != '0x' + '0' * 40]
    pm = net(cid)['poolManager']
    us = urls(cid)
    if cid == 196: us = ['https://xlayerrpc.okx.com']
    b1 = int(rpc(us[0], 'eth_blockNumber', []), 16)
    def one(chunk, depth=0):
        data = '0x' + adr(SINK) + ''.join(adr(t) for t in chunk)
        last = None
        for k in range(4):
            u = us[(k + depth) % len(us)]
            try:
                r = call_override(u, pm, data, {pm: {'code': XFER}}, gas=gas, timeout=120)
                if len(r) != 2 + 256 * len(chunk): raise Exception('short %d' % len(r))
                o = {}
                for j, t in enumerate(chunk):
                    w = [int(r[2 + 256 * j + 64 * m: 66 + 256 * j + 64 * m], 16) for m in range(4)]
                    o[t] = w
                return o
            except Exception as e:
                last = str(e)[:160]; time.sleep(0.5 + k)
        if len(chunk) > 1:
            h = len(chunk) // 2
            o = one(chunk[:h], depth + 1); o.update(one(chunk[h:], depth + 1)); return o
        return {chunk[0]: ['callfail', last]}
    out = {}; done = 0
    with ThreadPoolExecutor(workers) as ex:
        for res in ex.map(lambda i: one(toks[i:i + per]), range(0, len(toks), per)):
            out.update(res); done += per
            if done % 30000 == 0: print(cid, 'progress', done, len(toks), flush=True)
    b2 = int(rpc(us[0], 'eth_blockNumber', []), 16)
    odd = {t: w for t, w in out.items() if w[0] == 'callfail' or w[1] != 7 or w[2] != 0 or w[3] != w[0]}
    json.dump(dict(chainId=cid, blocks=[b1, b2], n=len(toks), tested=len(out), odd=odd, bal={t: str(w[0]) for t, w in out.items() if w[0] != 'callfail'}),
              gzip.open(os.path.join(RAW, 'xfer_%d.json.gz' % cid), 'wt'))
    nf = sum(1 for w in odd.values() if w[0] != 'callfail' and (w[1] & 2) == 0 and w[0] > 0)
    print(cid, net(cid)['name'], 'tested', len(out), 'blocks', b1, b2, 'odd', len(odd), 'fullTransferRejected', nf, 'callfail', sum(1 for w in odd.values() if w[0] == 'callfail'), flush=True)
if __name__ == '__main__':
    for c in sys.argv[1:]: run(int(c))
