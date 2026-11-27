"""Cycle 29 high-throughput, lead L-1152: mined census of the unchecked subtractions of getFeeGrowthInside
(src/libraries/Pool.sol:498-509) on MegaETH. For each ModifyLiquidity log of the PoolManager whose pool has no other
PoolManager log in the same block, the tick and fee growth words are read at the parent block, the fee growth inside
is computed with the three branches of Pool.getFeeGrowthInside (and the tick initialisation rule of Pool.updateTick for a
tick that was empty), and the result is compared with the feeGrowthInside0/1LastX128 that the producer wrote into the
position at the block itself. It records which subtraction borrowed. Read-only.
Usage: python3 -I fgi_census.py <out.json> <url> <pm> <nblocks back> [step]"""
import sys, os, json, time
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import rpc, keccak
M = (1 << 256) - 1
def w(x): return (x & M).to_bytes(32, 'big')
TOPIC = '0x' + keccak(b'ModifyLiquidity(bytes32,address,int24,int24,int256,bytes32)').hex()
def s24(x): x &= 0xffffff; return x - (1 << 24) if x >> 23 else x
def s256(x): return x - (1 << 256) if x >> 255 else x

def R(url, m, p):
    for k in range(6):
        try: return rpc(url, m, p, timeout=60)
        except Exception as e:  # noqa
            last = e; time.sleep(2 * (k + 1))
    raise last

def main():
    out, url, pm, back = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    step = int(sys.argv[5]) if len(sys.argv) > 5 else 10000
    cv0 = R(url, 'web3_clientVersion', [])
    head = int(R(url, 'eth_blockNumber', []), 16)
    logs = []; frm = head - back
    while frm < head:
        to = min(frm + step - 1, head)
        try:
            logs += R(url, 'eth_getLogs', [{'address': pm, 'fromBlock': hex(frm), 'toBlock': hex(to)}])
        except Exception as e:  # noqa
            print('getLogs', frm, to, str(e)[:200]); step = max(step // 4, 100); continue
        frm = to + 1
    per = {}
    for l in logs: per.setdefault((int(l['blockNumber'], 16), l['topics'][1]), []).append(l)
    cand = [v[0] for v in per.values() if len(v) == 1 and v[0]['topics'][0] == TOPIC]
    print('logs', len(logs), 'single ModifyLiquidity candidates', len(cand), flush=True)
    rows = []; stats = {'checked': 0, 'equal': 0, 'different': 0, 'error': 0, 'borrow': {'below': 0, 'above': 0, 'inside': 0}}
    for l in cand:
        b = int(l['blockNumber'], 16); pid = int(l['topics'][1], 16); sender = int(l['topics'][2], 16)
        d = bytes.fromhex(l['data'][2:]); tl = s24(int.from_bytes(d[0:32], 'big')); tu = s24(int.from_bytes(d[32:64], 'big'))
        ld = s256(int.from_bytes(d[64:96], 'big')); salt = d[96:128]
        base = int.from_bytes(keccak(w(pid) + w(6)), 'big')
        def ts(t, j): return '0x%x' % ((int.from_bytes(keccak(w(t) + w(base + 4)), 'big') + j) & M)
        pk = keccak(sender.to_bytes(20, 'big') + (tl & 0xffffff).to_bytes(3, 'big') + (tu & 0xffffff).to_bytes(3, 'big') + salt)
        ps = int.from_bytes(keccak(pk + w(base + 6)), 'big')
        try:
            g = lambda s, blk: int(R(url, 'eth_getStorageAt', [pm, s if isinstance(s, str) else '0x%x' % s, hex(blk)]), 16)
            p = b - 1
            slot0 = g(base, p); cur = s24(slot0 >> 160); fg = [g(base + 1, p), g(base + 2, p)]
            lo = [g(ts(tl, 0), p), g(ts(tl, 1), p), g(ts(tl, 2), p)]; up = [g(ts(tu, 0), p), g(ts(tu, 1), p), g(ts(tu, 2), p)]
            # Pool.updateTick: a tick with no gross liquidity gets outside = global when tick <= current, else 0 (only if liquidityDelta != 0)
            if ld != 0:
                if lo[0] & ((1 << 128) - 1) == 0: lo[1], lo[2] = (fg[0], fg[1]) if tl <= cur else (0, 0)
                if up[0] & ((1 << 128) - 1) == 0: up[1], up[2] = (fg[0], fg[1]) if tu <= cur else (0, 0)
            ins = []; br = []
            for k in (0, 1):
                a, c = lo[1 + k], up[1 + k]
                if cur < tl: v = a - c; br.append(('below', v < 0))
                elif cur >= tu: v = c - a; br.append(('above', v < 0))
                else: v = fg[k] - a - c; br.append(('inside', v < 0))
                ins.append(v & M)
            got = [g(ps + 1, b), g(ps + 2, b)]
            liq_after = g(ps, b)
            eq = got == ins
            # a fully removed position keeps its last fee growth words (Position.update writes them before liquidity drops)
            row = {'block': b, 'tx': l['transactionHash'], 'pool': l['topics'][1], 'tl': tl, 'tu': tu, 'cur': cur, 'ld': str(ld),
                   'branch': [x for x, _ in br], 'borrow': [y for _, y in br], 'equal': eq, 'liqAfter': str(liq_after)}
            if not eq: row.update(ref=[hex(x) for x in ins], got=[hex(x) for x in got])
            stats['checked'] += 1; stats['equal' if eq else 'different'] += 1
            for x, y in br:
                if y: stats['borrow'][x] += 1
        except Exception as e:  # noqa
            row = {'block': b, 'tx': l['transactionHash'], 'error': str(e)[:300]}; stats['error'] += 1
        rows.append(row)
    res = {'url': url, 'pm': pm, 'head': head, 'from': head - back, 'clientBefore': cv0, 'clientAfter': R(url, 'web3_clientVersion', []),
           'logs': len(logs), 'stats': stats, 'rows': rows}
    print(json.dumps(stats), res['clientBefore'], res['clientAfter'])
    json.dump(res, open(out, 'w'), indent=1)

if __name__ == '__main__': main()
