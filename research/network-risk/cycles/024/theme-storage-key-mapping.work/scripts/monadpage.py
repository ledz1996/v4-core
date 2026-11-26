"""Monad page encoding check (read-only). Monad v0.16.x stores storage in pages of 128 slots keyed by slot >> 7
(category/execution/monad/db/storage_page.hpp). This reads whole pages of real PoolManager storage, with no
override, through extsload(bytes32,uint256) inside the EVM and through eth_getStorageAt slot by slot, and compares
them. Pages: page 0 (fixed slots 0..6) and the pages that hold the state words of pools found in recent Initialize
logs (pool state slot S = keccak(id, 6), words S..S+6, which may straddle two pages).

Usage: python3 monadpage.py <out.json> [chainId ...]   (default 143 and 1 as reference)
"""
import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'tools', 'opdiff'))
from evm import keccak, rpc as _rpc  # noqa: E402


def rpc(url, m, params):
    last = None
    for k in range(8):
        try:
            r = _rpc(url, m, params); time.sleep(0.25); return r
        except Exception as e:  # noqa
            last = e; time.sleep(3 * (k + 1))
    raise last

NET = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'state', 'networks.json')
INIT = '0x' + keccak(b'Initialize(bytes32,address,address,uint24,int24,address,uint160,int24)').hex()
SEL = keccak(b'extsload(bytes32,uint256)')[:4]


def h(*w):
    return int.from_bytes(keccak(b''.join(x.to_bytes(32, 'big') for x in w)), 'big')


def page(n, blk, start):
    data = SEL + start.to_bytes(32, 'big') + (128).to_bytes(32, 'big')
    out = bytes.fromhex(rpc(n['rpc'], 'eth_call', [{'to': n['poolManager'], 'data': '0x' + data.hex()}, blk])[2:])
    words = [int.from_bytes(out[64 + 32 * i:96 + 32 * i], 'big') for i in range(128)]
    gs = []
    for i in range(128):
        for k in range(4):
            try:
                gs.append(int(rpc(n['rpc'], 'eth_getStorageAt', [n['poolManager'], hex(start + i), blk]), 16)); break
            except Exception:  # noqa
                time.sleep(1 + k)
        else:
            gs.append(None)
    return words, gs


def run(n, npools=3, span=2000):
    rec = {'chainId': n['chainId'], 'rpc': n['rpc'], 'clientBefore': rpc(n['rpc'], 'web3_clientVersion', [])}
    blk = rpc(n['rpc'], 'eth_blockNumber', []); rec['block'] = int(blk, 16)
    ids = []
    b = int(blk, 16)
    for k in range(20):
        try:
            logs = rpc(n['rpc'], 'eth_getLogs', [{'address': n['poolManager'], 'topics': [INIT],
                                                   'fromBlock': hex(b - span), 'toBlock': hex(b)}])
        except Exception as e:  # noqa
            rec.setdefault('logErrors', []).append(str(e)[:200]); logs = []
        for lg in logs:
            if lg['topics'][1] not in ids:
                ids.append(lg['topics'][1])
        if len(ids) >= npools:
            break
        b -= span
    pages = {0}
    for pid in ids[:npools]:
        s = h(int(pid, 16), 6)
        pages |= {s >> 7, (s + 6) >> 7}
    rec['poolIds'] = ids[:npools]; rec['pages'] = []
    for p in sorted(pages):
        w, g = page(n, blk, p << 7)
        diff = [{'slot': hex((p << 7) + i), 'extsload': hex(w[i]), 'getStorageAt': None if g[i] is None else hex(g[i])}
                for i in range(128) if g[i] != w[i]]
        rec['pages'].append({'page': hex(p), 'nonzero': [hex((p << 7) + i) for i in range(128) if w[i]],
                             'mismatches': diff})
    rec['clientAfter'] = rpc(n['rpc'], 'web3_clientVersion', [])
    rec['time'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    return rec


if __name__ == '__main__':
    want = [int(x) for x in sys.argv[2:]] or [143, 1]
    nets = {n['chainId']: n for n in json.load(open(NET))['networks']}
    res = []
    for c in want:
        r = run(nets[c])
        print(c, r['clientBefore'], r['block'], len(r['poolIds']), [(p['page'][:10], len(p['nonzero']), len(p['mismatches'])) for p in r['pages']], flush=True)
        res.append(r)
    json.dump(res, open(sys.argv[1], 'w'), indent=1)
