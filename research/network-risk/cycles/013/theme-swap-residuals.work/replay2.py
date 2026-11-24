"""replay2.py: every mined Swap event of the PoolManager in a window, rerun from exact state.

For one network and endpoint this script
  1. reads the newest window of Swap, ModifyLiquidity and ProtocolFeeUpdated events of the PoolManager;
  2. carries each pool's price, tick and in-range liquidity forward event by event, in (block, logIndex)
     order, starting from slot0 and liquidity read with extsload at the parent block of the pool's first
     event in the window (src/libraries/Pool.sol:206-226 for the liquidity change of ModifyLiquidity);
  3. tests every swap against the single-step outcomes of SwapMath.computeSwapStep (as tools/opdiff/swaps.py);
  4. reruns every swap the single step does not reproduce through the whole loop of Pool.swap
     (src/libraries/Pool.sol:344-437), with the tick spacing taken from the pool's Initialize event, the
     tick bitmap and liquidityNet read at the parent block and moved forward by the ModifyLiquidity events of
     that pool earlier in the same block (updateTick, flipTick and clearTick, Pool.sol:520-560, 592-600);
  5. checks the fee in the event against slot0's lpFee and protocolFee (Pool.sol:300-308,
     ProtocolFeeLibrary.calculateSwapFee) for static-fee pools, and, for swaps that are the only event of
     their pool in the block, the change of feeGrowthGlobal against the per-step fee and protocol fee split
     (Pool.sol:384-407, UnsafeMath.simpleMulDiv).

All arithmetic goes through tools/opdiff/v4math.py, a transcription of src/libraries written with the
EVM reference semantics. Read-only JSON-RPC only.

Usage: python3 replay2.py <chainId> <out.json> [--want N] [--log URL] [--state URL] [--extra samples.json]
"""
import sys, os, json, time, argparse, threading, concurrent.futures as cf
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from evm import rpc as _rpc, keccak, MASK, s, u, ref_signextend
import v4math as m
from endpoints import NETS, log_urls, state_urls

SWAP = '0x' + keccak(b'Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)').hex()
MODIFY = '0x' + keccak(b'ModifyLiquidity(bytes32,address,int24,int24,int256,bytes32)').hex()
INIT = '0x' + keccak(b'Initialize(bytes32,address,address,uint24,int24,address,uint160,int24)').hex()
PFEE = '0x' + keccak(b'ProtocolFeeUpdated(bytes32,uint24)').hex()
EXTN = '0x' + keccak(b'extsload(bytes32[])')[:4].hex()
POOLS_SLOT = 6  # src/libraries/StateLibrary.sol:11, PoolManager._pools
SPACINGS = [1, 10, 60, 200, 2, 5, 20, 50, 100, 4, 8, 15, 25, 30, 40, 80, 90, 120, 150, 250, 300, 500, 1000, 2000, 3, 6, 12, 16, 32, 64, 128, 887]
Q128 = 1 << 128
PKSEL = '0x' + keccak(b'poolKeys(bytes25)')[:4].hex()
def cid_of(pm): return next((c for c, n in NETS.items() if n['poolManager'].lower() == pm.lower()), None)


def word(d, i): return int(d[2 + 64 * i:2 + 64 * (i + 1)], 16)
def s24(x): return s(ref_signextend(2, x & 0xffffff))
def s128(x): return x - (1 << 128) if x >> 127 else x


class Rpc:
    def __init__(self, urls): self.urls = list(urls); self.i = 0; self.lock = threading.Lock(); self.calls = 0

    def __call__(self, method, params, timeout=90, tries=8):
        last = None; hard = set()
        for k in range(tries):
            with self.lock:
                url = self.urls[self.i % len(self.urls)]; self.i += 1; self.calls += 1
            if url in hard: continue
            try:
                return _rpc(url, method, params, timeout=timeout)
            except Exception as e:  # noqa
                last = e; msg = str(e).lower()
                if any(x in msg for x in ('too large', 'exceed', 'range', 'limit', 'too many results', 'historical state', 'missing trie', 'not available', 'pruned')) and '429' not in msg:
                    hard.add(url)  # this endpoint cannot answer; try the others once
                    if len(hard) >= len(self.urls): raise
                    continue
                time.sleep(min(15, 1.5 * (k + 1)))
        raise last


class State:
    """Storage of the PoolManager at the end of a block, read through extsload(bytes32[])."""
    def __init__(self, r, pm): self.r, self.pm, self.cache, self.lock = r, pm, {}, threading.Lock()

    def load(self, slots, block):
        need = [x for x in dict.fromkeys(slots) if (x, block) not in self.cache]
        for i in range(0, len(need), 64):
            part = need[i:i + 64]
            data = EXTN + (32).to_bytes(32, 'big').hex() + len(part).to_bytes(32, 'big').hex() + ''.join(x.to_bytes(32, 'big').hex() for x in part)
            res = self.r('eth_call', [{'to': self.pm, 'data': data}, hex(block)])
            n = word(res, 1); assert n == len(part), (n, len(part))
            with self.lock:
                for j, x in enumerate(part): self.cache[(x, block)] = word(res, 2 + j)
        return [self.cache[(x, block)] for x in slots]


def pool_base(pid): return int.from_bytes(keccak(bytes.fromhex(pid[2:]) + POOLS_SLOT.to_bytes(32, 'big')), 'big')
def map_slot(key, base_off): return int.from_bytes(keccak(u(key).to_bytes(32, 'big') + (base_off & MASK).to_bytes(32, 'big')), 'big')


class PoolView:
    """Tick bitmap and tick info of one pool as they stood before a given log of a block: the parent block's
    storage plus the ModifyLiquidity events of the pool earlier in that block (Pool.modifyLiquidity)."""
    def __init__(self, st, pid, block, spacing, mods):
        self.st, self.base, self.parent, self.sp = st, pool_base(pid), block - 1, spacing
        self.over = {}
        for (tl, tu, delta) in mods:
            if delta == 0: continue
            fl = self._update(tl, delta, False); fu = self._update(tu, delta, True)
            if fl: self._flip(tl)
            if fu: self._flip(tu)
            if delta < 0:
                if fl: self.over[self.tick_slot(tl)] = 0
                if fu: self.over[self.tick_slot(tu)] = 0

    def sload(self, slot):
        if slot in self.over: return self.over[slot]
        return self.st.load([slot], self.parent)[0]

    def tick_slot(self, t): return map_slot(t, self.base + 4)
    def word_slot(self, w): return map_slot(w, self.base + 5)

    def _update(self, t, delta, upper):  # Pool.updateTick, liquidityGross and liquidityNet only
        sl = self.tick_slot(t); w = self.sload(sl)
        gross, net = w & ((1 << 128) - 1), s128(w >> 128)
        after = gross + delta
        if after < 0 or after >> 128: raise m.Revert('gross out of range')
        flipped = (after == 0) != (gross == 0)
        net = net - delta if upper else net + delta
        self.over[sl] = (after & ((1 << 128) - 1)) | ((net & ((1 << 128) - 1)) << 128)
        return flipped

    def _flip(self, t):  # TickBitmap.flipTick
        assert t % self.sp == 0
        c = int(t / self.sp)
        sl = self.word_slot(c >> 8); self.over[sl] = self.sload(sl) ^ (1 << (c & 0xff))

    def net(self, t): return s128(self.sload(self.tick_slot(t)) >> 128)

    def next_tick(self, tick, lte):  # TickBitmap.nextInitializedTickWithinOneWord
        sp = self.sp
        c = int(tick / sp) - (1 if (tick < 0 and tick % sp != 0) else 0)
        if lte:
            w, bit = c >> 8, c & 0xff
            masked = self.sload(self.word_slot(w)) & (MASK >> (255 - bit))
            return ((c - (bit - m.most_significant_bit(masked))) * sp, True) if masked else ((c - bit) * sp, False)
        c += 1
        w, bit = c >> 8, c & 0xff
        masked = self.sload(self.word_slot(w)) & (MASK ^ ((1 << bit) - 1))
        return ((c + (m.least_significant_bit(masked) - bit)) * sp, True) if masked else ((c + (255 - bit)) * sp, False)


def swap_loop(view, p, tick, liq, zfo, amount, limit, fee, protocol_fee=0, max_steps=4000):
    """Pool.swap, src/libraries/Pool.sol:344-437. amount < 0 is exact input."""
    remaining = amount; calc = 0; steps = 0; to_protocol = 0; fg = 0
    while not (remaining == 0 or p == limit):
        steps += 1
        if steps > max_steps: raise m.Revert('too many steps')
        start = p
        tn, init = view.next_tick(tick, zfo)
        tn = max(m.MIN_TICK, min(m.MAX_TICK, tn))
        pn = m.get_sqrt_price_at_tick(tn)
        target = (pn if pn >= limit else limit) if zfo else (pn if pn < limit else limit)
        p, a_in, a_out, f = m.compute_swap_step(p, target, liq, remaining, fee)
        if amount > 0:
            remaining -= a_out; calc -= a_in + f
        else:
            remaining += a_in + f; calc += a_out
        if protocol_fee > 0:
            delta = f if fee == protocol_fee else (a_in + f) * protocol_fee // 10 ** 6
            f -= delta; to_protocol += delta
        if liq > 0: fg = (fg + (f * Q128) // liq) & MASK
        if p == pn:
            if init:
                net = view.net(tn)
                liq = liq - net if zfo else liq + net
                if liq < 0 or liq >> 128: raise m.Revert('liquidity out of range')
            tick = tn - 1 if zfo else tn
        elif p != start:
            tick = m.get_tick_at_sqrt_price(p)
    return p, tick, liq, amount - remaining, calc, steps, to_protocol, fg


def event_amounts(zfo, amount, used, calc):
    # Pool.sol:451-462: "if currency1 is specified"
    if zfo != (amount < 0): return calc, used
    return used, calc


def calc_swap_fee(pf, lp):  # ProtocolFeeLibrary.calculateSwapFee
    pf &= 0xfff
    return pf + lp - (pf * lp) // 10 ** 6


def full_replay(view, ev, pre, protocol_fee):
    p0, tick0, liq0 = pre
    if ev['a0'] == 0 and ev['a1'] == 0 and ev['p'] == p0 and ev['tick'] == tick0 and ev['liq'] == liq0:
        # amountToSwap of 0 after the hook's beforeSwap delta: Pool.swap returns at Pool.sol:320 with no state change
        return {'ok': True, 'mode': 'zeroAmount', 'limit': 'none', 'steps': 0, 'zfo': True, 'toProtocol': 0, 'feeGrowthDelta': 0}
    zfo = ev['p'] < p0 if ev['p'] != p0 else None
    out = []
    for z in ([zfo] if zfo is not None else [True, False]):
        paid, got = (-ev['a0'], ev['a1']) if z else (-ev['a1'], ev['a0'])
        edge = m.MIN_SQRT_PRICE + 1 if z else m.MAX_SQRT_PRICE - 1
        big = 1 << 127
        cands = [('exactIn', -paid, edge), ('exactOut', got, edge), ('exactIn', -paid, ev['p']), ('exactOut', got, ev['p']),
                 ('exactIn-to-limit', -big, ev['p']), ('exactOut-to-limit', big - 1, ev['p'])]
        for mode, amount, limit in cands:
            if amount == 0: continue
            if amount > 0 and ev['fee'] >= m.MAX_SWAP_FEE: continue
            if limit == p0 or (z and limit > p0) or ((not z) and limit < p0): continue
            try:
                p, tick, l, used, calc, steps, tp, fg = swap_loop(view, p0, tick0, liq0, z, amount, limit, ev['fee'], protocol_fee)
            except m.Revert as e:
                out.append((mode, 'revert ' + str(e))); continue
            a0, a1 = event_amounts(z, amount, used, calc)
            if p == ev['p'] and tick == ev['tick'] and l == ev['liq'] and a0 == ev['a0'] and a1 == ev['a1']:
                return {'ok': True, 'mode': mode, 'limit': 'open' if limit == edge else 'end price', 'steps': steps, 'zfo': z,
                        'toProtocol': tp, 'feeGrowthDelta': fg}
            out.append((mode, {'p': str(p), 'tick': tick, 'liq': str(l), 'a0': str(a0), 'a1': str(a1), 'steps': steps}))
    return {'ok': False, 'tries': out}


def collect(r, pm, want, max_calls=400, hi=None, budget=float(os.environ.get('BUDGET', 300))):
    t_end = time.time() + budget
    head = int(r('eth_blockNumber', []), 16) - 3 if hi is None else hi
    span = 2000; hi = head; logs = []; calls = 0; lo_seen = head; nsw = 0
    while nsw < want and calls < max_calls and hi > 0 and time.time() < t_end:
        lo = max(0, hi - span + 1); calls += 1
        try:
            part = r('eth_getLogs', [{'address': pm, 'fromBlock': hex(lo), 'toBlock': hex(hi), 'topics': [[SWAP, MODIFY, PFEE]]}], tries=4)
        except Exception as e:  # noqa
            if span <= 5: raise
            span = max(5, span // 4); time.sleep(0.5); continue
        logs = part + logs; lo_seen = lo; hi = lo - 1
        nsw += sum(1 for x in part if x['topics'][0] == SWAP)
        if len(part) < 300 and span < 100000: span = min(100000, span * 2)
    return logs, lo_seen, head


def find_keys(r, pm, pids, head, cache, cid=None):
    """Pool keys. First source: PositionManager.poolKeys(bytes25), a public mapping of the periphery contract, checked by
    hashing the key back to the pool id (src/types/PoolId.sol:11-14). Second source: Initialize events by pool id (topic 1)
    over the history from the PoolManager's deployment block, chunked when the endpoint limits ranges."""
    need = [p for p in pids if p not in cache]
    posm = NETS[cid]['contracts'].get('PositionManager') if cid else None
    def pk(pid):
        try:
            rr = r('eth_call', [{'to': posm, 'data': PKSEL + pid[2:52] + '00' * 7}, 'latest'], tries=3)
        except Exception:  # noqa
            return None
        if len(rr) >= 2 + 64 * 5 and '0x' + keccak(bytes.fromhex(rr[2:2 + 64 * 5])).hex() == pid:
            return {'c0': '0x' + rr[26:66], 'c1': '0x' + rr[90:130], 'fee': word(rr, 2), 'spacing': s(word(rr, 3)),
                    'hooks': '0x' + rr[2 + 64 * 4 + 24:2 + 64 * 5], 'source': 'PositionManager.poolKeys'}
        return None
    if posm and need:
        with cf.ThreadPoolExecutor(8) as ex:
            for pid, k in zip(need, ex.map(pk, need)):
                if k: cache[pid] = k
    need = [p for p in pids if p not in cache]
    if not need: return cache
    start = 0
    try:  # deployment block of the PoolManager, by bisection on eth_getCode
        lo_b, hi_b = 0, head
        while lo_b < hi_b:
            mid = (lo_b + hi_b) // 2
            if len(r('eth_getCode', [pm, hex(mid)], tries=3)) > 2: hi_b = mid
            else: lo_b = mid + 1
        start = lo_b
    except Exception:  # noqa
        start = 0
    for i in range(0, len(need), 50):
        ids = need[i:i + 50]
        got = None
        for span in (head + 1, 10_000_000, 1_000_000, 100_000, 50_000, 10_000):
            try:
                got = []; lo = start
                if span < head + 1 and ((head - start) // span) > 1500: got = None; break
                while lo <= head:
                    hi = min(head, lo + span - 1)
                    got += r('eth_getLogs', [{'address': pm, 'fromBlock': hex(lo), 'toBlock': hex(hi), 'topics': [INIT, ids]}], tries=3)
                    lo = hi + 1
                break
            except Exception:  # noqa
                got = None
        for x in got or []:
            d = x['data']
            cache[x['topics'][1]] = {'c0': '0x' + x['topics'][2][26:], 'c1': '0x' + x['topics'][3][26:], 'fee': word(d, 0),
                                     'spacing': s(word(d, 1)), 'hooks': '0x%040x' % word(d, 2), 'block': int(x['blockNumber'], 16), 'source': 'Initialize event'}
    return cache


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('chain', type=int); ap.add_argument('out')
    ap.add_argument('--want', type=int, default=3000); ap.add_argument('--log', action='append'); ap.add_argument('--state', action='append')
    ap.add_argument('--max-calls', type=int, default=400); ap.add_argument('--threads', type=int, default=6)
    ap.add_argument('--raw', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'raw'))
    a = ap.parse_args()
    cid = a.chain; pm = NETS[cid]['poolManager']
    rl = Rpc(a.log or log_urls(cid)); rs = Rpc(a.state or state_urls(cid)); st = State(rs, pm)
    lp = os.path.join(a.raw, f'logs-{cid}.json')
    if os.path.exists(lp):
        L = json.load(open(lp))
    else:
        logs, lo, head = collect(rl, pm, a.want, a.max_calls)
        L = {'chainId': cid, 'lo': lo, 'head': head, 'logs': logs}; json.dump(L, open(lp, 'w'))
    logs = sorted(L['logs'], key=lambda x: (int(x['blockNumber'], 16), int(x['logIndex'], 16)))
    # events per pool per block, to build the in-block overlay and to know which swaps are alone in their block
    per_block = {}
    for x in logs:
        if x['topics'][0] in (SWAP, MODIFY): per_block.setdefault((x['topics'][1], int(x['blockNumber'], 16)), []).append(x)
    res = {'chainId': cid, 'name': NETS[cid]['name'], 'blocks': [L['lo'], L['head']], 'logUrls': rl.urls, 'stateUrls': rs.urls,
           'swaps': 0, 'tick': {'exact': 0, 'boundary': 0, 'mismatch': 0}, 'single': {}, 'fullLoop': 0, 'setAside': {},
           'unmatched': [], 'fullLoopSamples': [], 'feeCheck': {'static': 0, 'staticMismatch': 0, 'dynamic': 0, 'mismatches': []},
           'pendingWhy': {}, 'feeGrowth': {'checked': 0, 'match': 0, 'mismatch': []}, 'maxSteps': 0, 'crossings': 0}
    state = {}   # pid -> dict(p, tick, liq, lp, pf) or None when the parent read failed
    pending = []  # swaps needing the full loop: (ev, pre, pf)
    first_block = {}

    def init_pool(pid, block):
        base = pool_base(pid)
        s0, fg0, fg1, liq = st.load([base, base + 1, base + 2, base + 3], block - 1)
        if s0 == 0:  # initialized in this block: start from the Initialize event (PoolManager.sol:128-138, Pool.sol:100-107)
            ini = rl('eth_getLogs', [{'address': pm, 'fromBlock': hex(block), 'toBlock': hex(block), 'topics': [INIT, pid]}])
            if not ini: raise RuntimeError('pool not initialized at parent and no Initialize event in block')
            d = ini[0]['data']; fee = word(d, 0)
            res['initInWindow'] = res.get('initInWindow', 0) + 1
            return {'p': word(d, 3), 'tick': s24(word(d, 4)), 'pf': 0, 'lp': 0 if fee == 0x800000 else fee, 'liq': 0}
        return {'p': s0 & ((1 << 160) - 1), 'tick': s24(s0 >> 160), 'pf': (s0 >> 184) & 0xffffff, 'lp': (s0 >> 208) & 0xffffff, 'liq': liq}

    for x in logs:
        t0 = x['topics'][0]; pid = x['topics'][1] if len(x['topics']) > 1 else None; blk = int(x['blockNumber'], 16); d = x['data']
        if pid not in state:
            if t0 == PFEE: continue
            try:
                state[pid] = init_pool(pid, blk)
            except Exception as e:  # noqa
                state[pid] = None; res['setAside'].setdefault('missing archive state', 0)
                res.setdefault('stateErrors', []).append(str(e)[:120])
        stp = state[pid]
        if t0 == PFEE:
            if stp: stp['pf'] = word(d, 0) & 0xffffff
            continue
        if t0 == MODIFY:
            if stp:
                tl, tu, delta = s24(word(d, 0)), s24(word(d, 1)), s(word(d, 2))
                if delta != 0 and tl <= stp['tick'] < tu: stp['liq'] += delta
            continue
        ev = {'tx': x['transactionHash'], 'pool': pid, 'block': blk, 'logIndex': int(x['logIndex'], 16), 'a0': s(word(d, 0)), 'a1': s(word(d, 1)),
              'p': word(d, 2), 'liq': word(d, 3), 'tick': s24(word(d, 4)), 'fee': word(d, 5)}
        res['swaps'] += 1
        try:
            tp = m.get_tick_at_sqrt_price(ev['p'])
            k = 'exact' if tp == ev['tick'] else ('boundary' if ev['tick'] == tp - 1 and m.get_sqrt_price_at_tick(tp) == ev['p'] else 'mismatch')
        except m.Revert:
            k = 'mismatch'
        res['tick'][k] += 1
        if stp is None:
            res['setAside']['missing archive state'] += 1; continue
        pre = (stp['p'], stp['tick'], stp['liq'])
        # fee check (Pool.sol:300-308): static-fee pools have no override, so the event fee follows from slot0
        zfo = ev['p'] < pre[0]
        pfd = (stp['pf'] & 0xfff) if zfo else (stp['pf'] >> 12)
        c = None
        if ev['p'] != pre[0] and pre[2] == ev['liq'] and pre[2] > 0:
            from_swaps = __import__('swaps').check_amounts
            c = from_swaps(pre[0], ev['p'], pre[2], ev['a0'], ev['a1'], ev['fee'])
            if c == 'multi': c = None
        if c:
            res['single'][c] = res['single'].get(c, 0) + 1
        else:
            why = 'no price move' if ev['p'] == pre[0] else ('liquidity changed' if pre[2] != ev['liq'] else ('zero liquidity' if pre[2] == 0 else 'single step fails'))
            res['pendingWhy'][why] = res['pendingWhy'].get(why, 0) + 1
            pending.append((ev, pre, pfd, dict(stp)))
        stp.update(p=ev['p'], tick=ev['tick'], liq=ev['liq'])

    print(cid, 'stage 1', res['swaps'], res['single'], res['pendingWhy'], 'calls', rl.calls + rs.calls, flush=True)
    if os.environ.get('STAGE1'): return
    # keys for the pools whose swaps need the full loop
    kp = os.path.join(a.raw, f'keys-{cid}.json')
    keys = json.load(open(kp)) if os.path.exists(kp) else {}
    keys = find_keys(rl, pm, sorted({ev['pool'] for ev, *_ in pending}), L['head'], keys, cid)
    # third source: the swap transaction's own calldata, searched for 160 bytes that hash to the pool id
    for pid in sorted({ev['pool'] for ev, *_ in pending if ev['pool'] not in keys}):
        for ev in [e for e, *_ in pending if e['pool'] == pid][:3]:
            try:
                tx = rl('eth_getTransactionByHash', [ev['tx']], tries=3); data = bytes.fromhex(tx['input'][2:])
            except Exception:  # noqa
                continue
            hit = None
            for off in range(0, max(0, len(data) - 159)):
                if '0x' + keccak(data[off:off + 160]).hex() == pid: hit = data[off:off + 160]; break
            if hit:
                w = [int.from_bytes(hit[32 * i:32 * i + 32], 'big') for i in range(5)]
                keys[pid] = {'c0': '0x%040x' % w[0], 'c1': '0x%040x' % w[1], 'fee': w[2], 'spacing': s(w[3]), 'hooks': '0x%040x' % w[4], 'source': 'swap calldata'}
                break
    json.dump(keys, open(kp, 'w'))
    # fee check for static-fee pools with a known key, for every swap
    res['keysFound'] = sum(1 for ev, *_ in pending if ev['pool'] in keys)

    def work(item):
        ev, pre, pfd, stp = item
        key = keys.get(ev['pool'])
        mods = []
        for y in per_block[(ev['pool'], ev['block'])]:
            if int(y['logIndex'], 16) >= ev['logIndex']: break
            if y['topics'][0] == MODIFY: mods.append((s24(word(y['data'], 0)), s24(word(y['data'], 1)), s(word(y['data'], 2))))
        spacings = [key['spacing']] if key else SPACINGS
        last = None
        for sp in spacings:
            try:
                view = PoolView(st, ev['pool'], ev['block'], sp, mods)
                r = full_replay(view, ev, pre, pfd)
            except AssertionError:
                continue
            except m.Revert as e:
                last = {'ok': False, 'why': 'overlay ' + str(e)}; continue
            except Exception as e:  # noqa
                return {'ok': False, 'why': 'missing archive state: ' + str(e)[:100]}
            r['spacing'] = sp; r['keyKnown'] = bool(key)
            if r['ok']: return r
            last = last or r
        return last or {'ok': False, 'why': 'no spacing'}

    with cf.ThreadPoolExecutor(a.threads) as ex:
        outs = list(ex.map(work, pending))
    fg_jobs = []
    for (ev, pre, pfd, stp), r in zip(pending, outs):
        if r.get('ok'):
            res['fullLoop'] += 1; res['maxSteps'] = max(res['maxSteps'], r['steps'])
            key = keys.get(ev['pool']); md = res.setdefault('loopModes', {}); md[r['mode']] = md.get(r['mode'], 0) + 1
            kk = res.setdefault('loopKey', {'known': 0, 'spacingInferred': 0}); kk['known' if r['keyKnown'] else 'spacingInferred'] += 1
            hk = int(key['hooks'], 16) if key else None
            if key:
                hs = res.setdefault('loopHooks', {'none': 0, 'hookNoDelta': 0, 'hookReturnsDelta': 0})
                hs['none' if hk == 0 else ('hookReturnsDelta' if hk & 0xc else 'hookNoDelta')] += 1
            if r['mode'] == 'zeroAmount':
                z = res.setdefault('zeroAmount', {'beforeSwapReturnsDelta': 0, 'otherHook': 0, 'noHook': 0, 'keyUnknown': 0, 'samples': []})
                zk = 'keyUnknown' if hk is None else ('noHook' if hk == 0 else ('beforeSwapReturnsDelta' if hk & 0x8 else 'otherHook'))
                z[zk] += 1
                if zk != 'beforeSwapReturnsDelta' and len(z['samples']) < 10: z['samples'].append({'tx': ev['tx'], 'pool': ev['pool'], 'hooks': key and key['hooks']})
            if r['steps'] > 1: res['crossings'] += 1
            if len(res['fullLoopSamples']) < 15: res['fullLoopSamples'].append({'tx': ev['tx'], 'steps': r['steps'], 'mode': r['mode'], 'spacing': r['spacing'], 'keyKnown': r['keyKnown']})
            if len(per_block[(ev['pool'], ev['block'])]) == 1: fg_jobs.append((ev, r))
        elif 'missing archive state' in r.get('why', ''):
            res['setAside']['missing archive state'] = res['setAside'].get('missing archive state', 0) + 1
            if len(res.setdefault('stateErrors', [])) < 5: res['stateErrors'].append(r['why'])
        else:
            res['unmatched'].append({**ev, 'pre': {'p': str(pre[0]), 'tick': pre[1], 'liq': str(pre[2])}, 'key': keys.get(ev['pool']), 'result': r,
                                     'p': str(ev['p']), 'liq': str(ev['liq']), 'a0': str(ev['a0']), 'a1': str(ev['a1'])})
    # fee growth: swaps replayed by the full loop that are the only event of their pool in the block
    for ev, r in fg_jobs[:40]:
        base = pool_base(ev['pool']); off = 1 if r['zfo'] else 2
        try:
            b, aft = st.load([base + off], ev['block'] - 1)[0], st.load([base + off], ev['block'])[0]
        except Exception:  # noqa
            continue
        res['feeGrowth']['checked'] += 1
        if (aft - b) & MASK == r['feeGrowthDelta']: res['feeGrowth']['match'] += 1
        else: res['feeGrowth']['mismatch'].append({'tx': ev['tx'], 'expected': str(r['feeGrowthDelta']), 'mined': str((aft - b) & MASK)})
    # fee check on static-fee pools with a key
    for ev, pre, pfd, stp in pending:
        key = keys.get(ev['pool'])
        if not key: continue
        if key['fee'] == 0x800000: res['feeCheck']['dynamic'] += 1; continue
        exp = stp['lp'] if pfd == 0 else calc_swap_fee(pfd, stp['lp'])
        res['feeCheck']['static'] += 1
        if exp != ev['fee']:
            res['feeCheck']['staticMismatch'] += 1; res['feeCheck']['mismatches'].append({'tx': ev['tx'], 'expected': exp, 'event': ev['fee']})
    res['pending'] = len(pending); res['rpcCalls'] = rl.calls + rs.calls
    json.dump(res, open(a.out, 'w'), indent=1)
    print(cid, NETS[cid]['name'], 'swaps', res['swaps'], 'tick', res['tick'], 'single', sum(res['single'].values()), res['single'], 'loop', res['fullLoop'],
          'aside', res['setAside'], 'unmatched', len(res['unmatched']), 'keys', res['keysFound'], '/', len(pending), 'fee', {k: v for k, v in res['feeCheck'].items() if k != 'mismatches'},
          'fg', res['feeGrowth']['checked'], res['feeGrowth']['match'], 'maxSteps', res['maxSteps'], flush=True)


if __name__ == '__main__':
    main()
