"""Cross-slot invariants of committed PoolManager storage, read through extsload by eth_call.

For every pool that had a Swap or ModifyLiquidity log in the recent window:
  I1  every bit set in the tick bitmap names a tick whose liquidityGross is nonzero
  I2  the pool's liquidity slot equals the sum of liquidityNet over initialized ticks at or below slot0.tick
  I3  the liquidityNet of all initialized ticks sums to zero
  I4  for a sample of tick records, eth_getStorageAt of the three slots equals extsload of the same slots
A storage layer that merged, dropped or misplaced slots of one page or one bucket would break these, because the
slots involved are keccak slots spread over many pages, written by different transactions in different blocks.
Slot layout from src/libraries/StateLibrary.sol:11-28 and src/libraries/Pool.sol:68-91.

Usage: python3 invariants.py <out.json> <chainId> [maxPools]
"""
import sys, os, json, time
sys.path.insert(0, __file__.rsplit('/', 4)[0] + '/tools/opdiff')
from evm import rpc, keccak
import swaps as SW

M = (1 << 256) - 1
nets = {n['chainId']: n for n in json.load(open(__file__.rsplit('/', 4)[0] + '/state/networks.json'))['networks']}


def h(x): return '0x' + x.to_bytes(32, 'big').hex()
def kk(a, b): return int.from_bytes(keccak(a.to_bytes(32, 'big') + b.to_bytes(32, 'big')), 'big')


def extsload_many(url, pm, slots, block):
    out = []
    for i in range(0, len(slots), 1500):
        part = slots[i:i + 1500]
        # extsload(bytes32[]) selector
        sel = keccak(b'extsload(bytes32[])')[:4]
        data = sel + (32).to_bytes(32, 'big') + len(part).to_bytes(32, 'big') + b''.join(s.to_bytes(32, 'big') for s in part)
        for k in range(4):
            try:
                r = rpc(url, 'eth_call', [{'to': pm, 'data': '0x' + data.hex()}, block], timeout=90); break
            except Exception as e:  # noqa
                if k == 3: raise
                time.sleep(2 * (k + 1))
        b = bytes.fromhex(r[2:]); n = int.from_bytes(b[32:64], 'big')
        out += [int.from_bytes(b[64 + 32 * j:96 + 32 * j], 'big') for j in range(n)]
    return out


def pool_key(url, posm, pid, block):
    sel = keccak(b'poolKeys(bytes25)')[:4]
    data = sel + bytes.fromhex(pid[2:52]).ljust(32, b'\0')
    try:
        r = bytes.fromhex(rpc(url, 'eth_call', [{'to': posm, 'data': '0x' + data.hex()}, block])[2:])
    except Exception:  # noqa
        return None
    if len(r) < 160: return None
    c0, c1, fee, ts, hooks = [int.from_bytes(r[32 * i:32 * i + 32], 'big') for i in range(5)]
    ts = ts - (1 << 256) if ts >> 255 else ts
    if ts == 0 and c1 == 0: return None
    # the key must hash to the pool id
    enc = b''.join(x.to_bytes(32, 'big') for x in (c0, c1, fee, ts & M, hooks))
    if '0x' + keccak(enc).hex() != pid.lower(): return None
    return {'currency0': hex(c0), 'currency1': hex(c1), 'fee': fee, 'tickSpacing': ts, 'hooks': hex(hooks)}


def sgn(v, bits): return v - (1 << bits) if v >> (bits - 1) else v


def check_pool(url, pm, pid, ts, block, sample_getstorage):
    base = kk(int(pid, 16), 6)
    s0, liq = extsload_many(url, pm, [base, base + 3], block)
    tick = sgn((s0 >> 160) & 0xffffff, 24); liq &= (1 << 128) - 1
    lo = (-887272 // ts) >> 8; hi = (887272 // ts) >> 8
    words = list(range(lo, hi + 1))
    wslots = [kk(w & M, base + 5) for w in words]
    wv = extsload_many(url, pm, wslots, block)
    ticks = []
    for w, v in zip(words, wv):
        b = 0
        while v:
            if v & 1: ticks.append((w * 256 + b) * ts)
            v >>= 1; b += 1
    tslots = [kk(t & M, base + 4) for t in ticks]
    tv = extsload_many(url, pm, tslots, block) if tslots else []
    bad = []; s_below = 0; s_all = 0
    for t, v in zip(ticks, tv):
        gross = v & ((1 << 128) - 1); net = sgn(v >> 128, 128)
        if gross == 0: bad.append(('I1', t))
        s_all += net
        if t <= tick: s_below += net
    if s_below != liq: bad.append(('I2', s_below, liq))
    if s_all != 0: bad.append(('I3', s_all))
    gs = []
    for t, sl in list(zip(ticks, tslots))[:sample_getstorage]:
        ext = extsload_many(url, pm, [sl, sl + 1, sl + 2], block)
        got = [int(rpc(url, 'eth_getStorageAt', [pm, h(sl + j), block]), 16) for j in range(3)]
        gs.append({'tick': t, 'offsetInPage': sl & 0x7f, 'same': ext == got})
        if ext != got: bad.append(('I4', t, [hex(x) for x in ext], [hex(x) for x in got]))
    return {'pool': pid, 'tickSpacing': ts, 'tick': tick, 'liquidity': liq, 'initializedTicks': len(ticks), 'words': len(words),
            'violations': bad, 'getStorageAt': gs}


if __name__ == '__main__':
    out = sys.argv[1]; cid = int(sys.argv[2]); maxp = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    n = nets[cid]; url = n['rpc']; pm = n['poolManager']; posm = n['contracts']['PositionManager']
    os.environ.setdefault('SWAPS_WANT', '6000')
    logs, lo, head = SW.collect(url, pm)
    block = hex(head)
    pids = []
    for lg in reversed(logs):
        p = lg['topics'][1]
        if p not in pids: pids.append(p)
    print(cid, 'logs', len(logs), 'blocks', lo, head, 'pools', len(pids), flush=True)
    res = []; skipped = 0
    for pid in pids[:maxp]:
        k = pool_key(url, posm, pid, block)
        if not k: skipped += 1; continue
        try:
            r = check_pool(url, pm, pid, k['tickSpacing'], block, 2 if len(res) < 60 else 0)
        except Exception as e:  # noqa
            print('ERR', pid, str(e)[:100], flush=True); skipped += 1; continue
        r['key'] = k; res.append(r)
        if r['violations']: print('VIOLATION', pid, r['violations'][:3], flush=True)
    summary = {'chainId': cid, 'block': head, 'windowFrom': lo, 'poolsSeen': len(pids), 'poolsChecked': len(res), 'skipped': skipped,
               'initializedTicks': sum(r['initializedTicks'] for r in res), 'bitmapWords': sum(r['words'] for r in res),
               'getStorageAtCompared': sum(len(r['getStorageAt']) for r in res),
               'getStorageAtSlotsNearPageEdge': sum(1 for r in res for g in r['getStorageAt'] if g['offsetInPage'] >= 125),
               'violations': sum(len(r['violations']) for r in res)}
    print(json.dumps(summary), flush=True)
    json.dump({'summary': summary, 'pools': res}, open(out, 'w'), indent=1)
