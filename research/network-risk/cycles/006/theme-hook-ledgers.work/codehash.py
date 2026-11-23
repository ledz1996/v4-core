# Group hook addresses by code hash. Uses eth_call with a state override that places a 24 byte read-only lens at a scratch address:
# for every 32 byte word of calldata it writes EXTCODEHASH(word) to the same offset of the return data. No state is changed.
# usage: python3 codehash.py <chainId>
import sys, collections, threading
from common import *
import concurrent.futures as cf
os.chdir(C5)
from summ import census
os.chdir(HERE)
LENS = '0x5f5b3681101560145780353f81526020016001565b365ff3'
LA = '0x00000000000000000000000000000000000c0de1'
def hashes(u, addrs):
    r = rpc(u, 'eth_call', [{'to': LA, 'data': '0x' + ''.join(adr(a) for a in addrs)}, 'latest', {LA: {'code': LENS}}], timeout=90)
    r = r[2:]
    assert len(r) == 64 * len(addrs), len(r)
    return [r[i * 64:(i + 1) * 64] for i in range(len(addrs))]
def main(cid):
    os.chdir(C5); cnt, dyn, rows, total, cov = census(cid); os.chdir(HERE)
    Z = '0x' + '0' * 40
    hooks = sorted(h for h in cnt if h != Z)
    us = urls(cid); out = {}; lock = threading.Lock(); fails = []
    def one(ch):
        last = None
        for u in us:
            try:
                hs = hashes(u, ch)
                with lock:
                    for a, h in zip(ch, hs): out[a] = h
                return
            except Exception as e: last = repr(e)[:150]
        if len(ch) > 50:
            m = len(ch) // 2; one(ch[:m]); one(ch[m:])
        else:
            with lock: fails.append(last)
    B = 2000
    with cf.ThreadPoolExecutor(4) as ex: list(ex.map(one, [hooks[i:i + B] for i in range(0, len(hooks), B)]))
    g = collections.defaultdict(list)
    for a, h in out.items(): g[h].append(a)
    groups = sorted(g.items(), key=lambda kv: -len(kv[1]))
    pools = {h: sum(cnt[a] for a in v) for h, v in g.items()}
    json.dump(dict(chainId=cid, hooks=len(hooks), hashed=len(out), fails=fails[:10], groups=[dict(codeHash=h, n=len(v), pools=pools[h], sample=sorted(v, key=lambda a: -cnt[a])[:5]) for h, v in groups], byHook=out), gzip.open(os.path.join(RAW, 'codehash_%d.json.gz' % cid), 'wt'))
    print(cid, 'hooks', len(hooks), 'hashed', len(out), 'groups', len(groups), 'fails', len(fails), fails[:2])
    for h, v in groups[:14]: print('   ', h[:16], 'n', len(v), 'pools', pools[h], sorted(v, key=lambda a: -cnt[a])[:2])
if __name__ == '__main__': main(int(sys.argv[1]))
