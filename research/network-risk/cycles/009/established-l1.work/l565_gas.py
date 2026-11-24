"""Lead L-565. Measured gas per initialized tick crossing and per empty bitmap step in
Pool.swap on the deployed PoolManagers, read only.

For each chain: take the busiest hookless pools from recent Swap logs, read their key
from the PositionManager (poolKeys(bytes25)), read slot0 and liquidity through
extsload at a fixed block, and for a ladder of exact-input amounts
  1. replay Pool.swap step by step (tools/opdiff/replay.py transcription) against
     storage at that block, counting initialized crossings and other steps, and
  2. call the deployed Quoter quoteExactInputSingle at the same block, which returns
     (amountOut, gasEstimate).
The simulated amountOut must equal the Quoter's. A least squares fit of gasEstimate on
(1, crossings, emptySteps) gives the marginal cost of each.

Usage: python3 l565_gas.py <out.json> [chainId ...]
"""
import sys, os, json, time
T = '/home/user/v4-core/research/network-risk/tools/opdiff'
sys.path.insert(0, T)
from evm import rpc, keccak, MASK, s, u
import v4math as m
import replay as R

NETS = {n['chainId']: n for n in json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))['networks']}
RPC = {137: 'https://polygon-bor-rpc.publicnode.com', 56: 'https://bsc-dataseed1.bnbchain.org', 43114: 'https://avalanche-c-chain-rpc.publicnode.com'}
LOGRPC = {137: 'https://polygon-bor-rpc.publicnode.com', 56: 'https://bsc-rpc.publicnode.com', 43114: 'https://avalanche-c-chain-rpc.publicnode.com'}
SWAP = '0x' + keccak(b'Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)').hex()


def sel(sig): return keccak(sig.encode())[:4].hex()


def w(x): return '%064x' % (x & MASK)


def call(url, to, data, block):
    for k in range(5):
        try:
            return rpc(url, 'eth_call', [{'to': to, 'data': data, 'gas': hex(30_000_000)}, hex(block)], timeout=60)
        except Exception as e:  # noqa
            last = e; time.sleep(2 * (k + 1))
    raise last


def pools(cid, head, n=6):
    url = LOGRPC[cid]; pm = NETS[cid]['poolManager']; cnt = {}
    hi = head; span = 2000 if cid != 43114 else 20000
    for _ in range(12):
        try:
            logs = rpc(url, 'eth_getLogs', [{'address': pm, 'fromBlock': hex(hi - span + 1), 'toBlock': hex(hi), 'topics': [SWAP]}], timeout=90)
        except Exception:
            span //= 2; continue
        for l in logs: cnt[l['topics'][1]] = cnt.get(l['topics'][1], 0) + 1
        hi -= span
        if sum(cnt.values()) > 3000: break
    return sorted(cnt.items(), key=lambda kv: -kv[1])[:40]


def pool_key(cid, pid, block):
    posm = NETS[cid]['contracts']['PositionManager']
    r = call(RPC[cid], posm, '0x' + sel('poolKeys(bytes25)') + pid[2:52] + '0' * 14, block)
    c0, c1, fee, sp, hooks = [int(r[2 + 64 * i:66 + 64 * i], 16) for i in range(5)]
    return c0, c1, fee, s(sp) if sp >> 255 else sp, hooks


def quote(cid, key, zfo, amount, block):
    c0, c1, fee, sp, hooks = key
    q = NETS[cid]['contracts']['Quoter']
    # quoteExactInputSingle(((address,address,uint24,int24,address),bool,uint128,bytes))
    data = '0x' + sel('quoteExactInputSingle(((address,address,uint24,int24,address),bool,uint128,bytes))') + w(0x20) + \
        w(c0) + w(c1) + w(fee) + w(sp) + w(hooks) + w(int(zfo)) + w(amount) + w(0x100) + w(0)
    r = call(RPC[cid], q, data, block)
    return int(r[2:66], 16), int(r[66:130], 16)


def sim(ch, base, block, p, tick, liq, zfo, amount, fee, sp):
    """replay.swap with step classification; amount > 0 is exact input here (v4: negative)."""
    remaining = amount; calc = 0; cross = 0; empty = 0; steps = 0
    limit = m.MIN_SQRT_PRICE + 1 if zfo else m.MAX_SQRT_PRICE - 1
    while not (remaining == 0 or p == limit):
        steps += 1
        if steps > 600: raise m.Revert('too many steps')
        tn, init = R.next_tick(ch, base, block, tick, sp, zfo)
        tn = max(m.MIN_TICK, min(m.MAX_TICK, tn))
        pn = m.get_sqrt_price_at_tick(tn)
        target = (pn if pn >= limit else limit) if zfo else (pn if pn < limit else limit)
        start = p
        p, a_in, a_out, f = m.compute_swap_step(p, target, liq, remaining, fee)
        remaining += a_in + f; calc += a_out
        if p == pn:
            if init:
                w0 = ch.sload(int.from_bytes(keccak(u(tn).to_bytes(32, 'big') + ((base + 4) & MASK).to_bytes(32, 'big')), 'big'), block)
                net = (w0 >> 128); net = net - (1 << 128) if net >> 127 else net
                liq = liq - net if zfo else liq + net
                cross += 1
            else:
                empty += 1
            tick = tn - 1 if zfo else tn
        elif p != start:
            tick = m.get_tick_at_sqrt_price(p)
    return calc, cross, empty, steps


def fit(rows):
    # least squares gas = a + b*cross + c*empty
    import itertools
    X = [(1.0, r['cross'], r['empty']) for r in rows]; y = [r['gas'] for r in rows]
    A = [[sum(x[i] * x[j] for x in X) for j in range(3)] for i in range(3)]
    bvec = [sum(x[i] * yy for x, yy in zip(X, y)) for i in range(3)]
    # solve 3x3
    import copy
    M = [A[i] + [bvec[i]] for i in range(3)]
    for c in range(3):
        piv = max(range(c, 3), key=lambda r: abs(M[r][c]))
        if abs(M[piv][c]) < 1e-9: return None
        M[c], M[piv] = M[piv], M[c]
        for r in range(3):
            if r != c:
                f = M[r][c] / M[c][c]; M[r] = [a - f * b for a, b in zip(M[r], M[c])]
    return [M[i][3] / M[i][i] for i in range(3)]


def run(cid):
    url = RPC[cid]; pm = NETS[cid]['poolManager']
    block = int(rpc(url, 'eth_blockNumber', []), 16) - 5
    ch = R.Chain(url, pm)
    out = {'chainId': cid, 'block': block, 'rpc': url, 'pools': []}
    for pid, n in pools(cid, block):
        if len(out['pools']) >= int(os.environ.get('NPOOLS', 2)): break
        try:
            key = pool_key(cid, pid, block)
        except Exception as e:  # noqa
            continue
        if key[4] != 0 or key[0] == key[1] == 0 or key[2] & 0x800000: continue
        base = int.from_bytes(keccak(bytes.fromhex(pid[2:]) + (6).to_bytes(32, 'big')), 'big')
        s0 = ch.sload(base, block); liq = ch.sload(base + 3, block) & ((1 << 128) - 1)
        p = s0 & ((1 << 160) - 1); tick = (s0 >> 160) & 0xffffff; tick = tick - (1 << 24) if tick >> 23 else tick
        proto = (s0 >> 184) & 0xffffff; lp = (s0 >> 208) & 0xffffff
        if liq == 0: continue
        rows = []
        for zfo in (True, False):
            for e in range(0, int(os.environ.get('NAMOUNTS', 60))):
                amount = int(10 ** (3 + e * 0.35))
                if amount >= 1 << 127: break
                try:
                    pf = (proto & 0xfff) if zfo else (proto >> 12)
                    fee = pf + lp - pf * lp // 1000000 if pf else lp
                    calc, cross, empty, steps = sim(ch, base, block, p, tick, liq, zfo, -amount, fee, key[3])
                    q_out, gas = quote(cid, key, zfo, amount, block)
                except Exception as ex:  # noqa
                    rows.append({'zfo': zfo, 'amountIn': str(amount), 'error': str(ex)[:120]}); break
                rows.append({'zfo': zfo, 'amountIn': str(amount), 'simOut': str(calc), 'quoterOut': str(q_out), 'match': calc == q_out,
                             'cross': cross, 'empty': empty, 'steps': steps, 'gas': gas})
                if steps > 400: break
        good = [r for r in rows if r.get('match')]
        coef = fit(good) if len(good) >= 6 else None
        out['pools'].append({'poolId': pid, 'swapsInWindow': n, 'key': [hex(key[0]), hex(key[1]), key[2], key[3], hex(key[4])],
                             'tick': tick, 'liquidity': str(liq), 'lpFee': lp, 'protocolFee': proto, 'rows': rows, 'matched': len(good),
                             'fit': None if coef is None else {'base': round(coef[0]), 'perCrossing': round(coef[1]), 'perEmptyStep': round(coef[2])},
                             'maxCross': max([r['cross'] for r in good] or [0]), 'maxEmpty': max([r['empty'] for r in good] or [0])})
        json.dump(out, open(os.environ.get('PARTIAL', '/dev/null'), 'w'), indent=1)
        print(cid, pid[:12], 'sp', key[3], 'matched', len(good), '/', len(rows), out['pools'][-1]['fit'], 'maxCross', out['pools'][-1]['maxCross'], 'maxEmpty', out['pools'][-1]['maxEmpty'], flush=True)
    return out


if __name__ == '__main__':
    o = sys.argv[1]; ids = [int(x) for x in sys.argv[2:]] or [137, 56, 43114]
    res = [run(c) for c in ids]
    json.dump({'results': res}, open(o, 'w'), indent=1)
