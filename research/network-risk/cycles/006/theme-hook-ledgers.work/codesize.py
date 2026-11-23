# Group hook addresses by code size (EXTCODESIZE lens through a state override), then compare sample bytecodes inside the largest groups.
# usage: python3 codesize.py <chainId>
import sys, collections, threading
from common import *
import concurrent.futures as cf
os.chdir(C5)
from summ import census, flags
os.chdir(HERE)
LENS = '0x5f5b3681101560145780353b81526020016001565b365ff3'
LA = '0x00000000000000000000000000000000000c0de1'
def sizes(u, addrs):
    r = rpc(u, 'eth_call', [{'to': LA, 'data': '0x' + ''.join(adr(a) for a in addrs)}, 'latest', {LA: {'code': LENS}}], timeout=90)[2:]
    assert len(r) == 64 * len(addrs)
    return [int(r[i * 64:(i + 1) * 64], 16) for i in range(len(addrs))]
def main(cid):
    os.chdir(C5); cnt, dyn, rows, total, cov = census(cid); os.chdir(HERE)
    Z = '0x' + '0' * 40
    hooks = sorted(h for h in cnt if h != Z)
    us = urls(cid); out = {}; lock = threading.Lock(); fails = []
    def one(ch):
        last = None
        for u in us:
            try:
                hs = sizes(u, ch)
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
    for a, h in out.items(): g[(h, int(a, 16) & 0x3fff)].append(a)
    groups = sorted(g.items(), key=lambda kv: -len(kv[1]))
    json.dump(dict(chainId=cid, hooks=len(hooks), sized=len(out), fails=fails[:10], groups=[dict(size=k[0], flags=hex(k[1]), n=len(v), pools=sum(cnt[a] for a in v), sample=sorted(v, key=lambda a: -cnt[a])[:6]) for k, v in groups], byHook=out), gzip.open(os.path.join(RAW, 'codesize_%d.json.gz' % cid), 'wt'))
    print(cid, 'hooks', len(hooks), 'sized', len(out), 'groups', len(groups), 'fails', len(fails), fails[:2])
    for k, v in groups[:16]: print('   size', k[0], 'flags', hex(k[1]), ','.join(flags(hex(k[1]))), 'n', len(v), 'pools', sum(cnt[a] for a in v), sorted(v, key=lambda a: -cnt[a])[:2])
if __name__ == '__main__': main(int(sys.argv[1]))
