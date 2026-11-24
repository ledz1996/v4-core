"""Mined swaps against the source's arithmetic. eth_call can run on a different code
path than block production (an interpreter where blocks use compiled code), so this
check reads results that blocks already contain: the Swap events of the deployed
PoolManager. For every event it tests relations that the pool math fixes exactly:

  tick   the tick in the event equals getTickAtSqrtPrice(price), or the price sits
         exactly on the boundary above it (a swap that stopped on a tick going down)
  amount for two consecutive swaps of one pool with no liquidity change between
         them, the amounts and the end price follow from the start price, the
         liquidity and the fee by one of the three single-step cases of
         SwapMath.computeSwapStep

A swap of several steps at one liquidity rounds once per step and lands a few units
from the single-step values; it is counted as "multi". Whatever fits none of this is
"other" and is listed for a closer look. Usage: python3 swaps.py <out.json> [chainId ...]
"""
import sys, os, json, time, concurrent.futures as cf
from evm import rpc, networks, keccak, s, MASK
import v4math as m

SWAP = '0x' + keccak(b'Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)').hex()
MODIFY = '0x' + keccak(b'ModifyLiquidity(bytes32,address,int24,int24,int256,bytes32)').hex()
INIT = '0x' + keccak(b'Initialize(bytes32,address,address,uint24,int24,address,uint160,int24)').hex()


def get_logs(url, pm, lo, hi):
    return rpc(url, 'eth_getLogs', [{'address': pm, 'fromBlock': hex(lo), 'toBlock': hex(hi), 'topics': [[SWAP, MODIFY]]}], timeout=90)


def collect(url, pm, want=int(os.environ.get('SWAPS_WANT', 6000)), max_calls=int(os.environ.get('SWAPS_CALLS', 60))):
    head = int(rpc(url, 'eth_blockNumber', []), 16) - 2
    span = 2000; hi = head; logs = []; calls = 0; lo_seen = head
    while len(logs) < want and calls < max_calls and hi > 0:
        lo = max(0, hi - span + 1); calls += 1
        try:
            part = get_logs(url, pm, lo, hi)
        except Exception as e:  # noqa
            if span <= 5: break
            span = max(5, span // 4); time.sleep(0.5); continue
        logs = part + logs; lo_seen = lo; hi = lo - 1
        if len(part) < 200 and span < 50000: span = min(50000, span * 2)
    return logs, lo_seen, head


def word(d, i): return int(d[2 + 64 * i:2 + 64 * (i + 1)], 16)


def check_tick(price, tick):
    t = m.get_tick_at_sqrt_price(price)
    if tick == t: return 'exact'
    if tick == t - 1 and m.get_sqrt_price_at_tick(t) == price: return 'boundary'
    return None


def check_amounts(p0, p1, liq, a0, a1, fee):
    """a0, a1 as emitted: negative means the swapper paid."""
    zero_for_one = p1 < p0
    paid, got = (-a0, a1) if zero_for_one else (-a1, a0)
    if paid < 0 or got < 0: return None
    try:
        out = m.amount1_delta(p1, p0, liq, False) if zero_for_one else m.amount0_delta(p0, p1, liq, False)
        # exact input that stopped inside the range
        less_fee = m.mul_div(paid, m.MAX_SWAP_FEE - fee, m.MAX_SWAP_FEE)
        if m.next_price_from_input(p0, liq, less_fee, zero_for_one) == p1 and out == got: return 'exactIn'
        amt_in = m.amount0_delta(p1, p0, liq, True) if zero_for_one else m.amount1_delta(p0, p1, liq, True)
        if fee < m.MAX_SWAP_FEE:
            total = amt_in + m.mul_div_rounding_up(amt_in, fee, m.MAX_SWAP_FEE - fee)
            # exact output that stopped inside the range
            if total == paid and got <= out:
                try:
                    if m.next_price_from_output(p0, liq, got, zero_for_one) == p1: return 'exactOut'
                except m.Revert:
                    pass
            # price target reached (limit price or a tick boundary without a liquidity change)
            if total == paid and out == got: return 'target'
            # several steps at one liquidity (the step ends at a tick bitmap word boundary or at an initialized tick with
            # zero net liquidity): each step rounds on its own, so the output is a few units below and the input a few
            # units above the single-step values
            if 0 <= out - got <= 64 and 0 <= paid - total <= 64: return 'multi'
    except m.Revert:
        return None
    return None


def run(n):
    cid, name, url = n[:3]; pm = n[3]
    res = {'chainId': cid, 'name': name, 'swaps': 0, 'tick': {'exact': 0, 'boundary': 0, 'mismatch': 0}, 'pairs': 0,
           'amount': {'exactIn': 0, 'exactOut': 0, 'target': 0, 'multi': 0, 'other': 0}, 'tickMismatches': [], 'otherSamples': [], 'multiSamples': []}
    try:
        logs, lo, head = collect(url, pm)
    except Exception as e:  # noqa
        res['error'] = str(e)[:200]; return res
    res['blocks'] = [lo, head]
    last = {}  # pool id -> (price, liquidity, clean)
    for lg in sorted(logs, key=lambda x: (int(x['blockNumber'], 16), int(x['logIndex'], 16))):
        pid = lg['topics'][1]
        if lg['topics'][0] == MODIFY:
            last.pop(pid, None); continue
        d = lg['data']
        a0, a1 = s(word(d, 0)), s(word(d, 1)); price = word(d, 2); liq = word(d, 3)
        tick = s(m.ref_signextend(2, word(d, 4) & 0xffffff)); fee = word(d, 5)
        res['swaps'] += 1
        try:
            k = check_tick(price, tick)
        except m.Revert:
            k = None
        if k: res['tick'][k] += 1
        else:
            res['tick']['mismatch'] += 1
            if len(res['tickMismatches']) < 10: res['tickMismatches'].append({'tx': lg['transactionHash'], 'price': str(price), 'tick': tick})
        prev = last.get(pid)
        if prev and prev[1] == liq and liq > 0 and prev[0] != price:
            res['pairs'] += 1
            c = check_amounts(prev[0], price, liq, a0, a1, fee)
            sample = {'tx': lg['transactionHash'], 'pool': pid, 'block': int(lg['blockNumber'], 16), 'p0': str(prev[0]), 'tick0': prev[2],
                      'p1': str(price), 'tick1': tick, 'liq': str(liq), 'a0': str(a0), 'a1': str(a1), 'fee': fee}
            if c:
                res['amount'][c] += 1
                if c == 'multi': res['multiSamples'] = (res['multiSamples'] + [sample])[-25:]  # keep the newest: old state is pruned on some endpoints
            else:
                res['amount']['other'] += 1
                res['otherSamples'] = (res['otherSamples'] + [sample])[-60:]
        last[pid] = (price, liq, tick)
    return res


if __name__ == '__main__':
    out = sys.argv[1]; only = set(map(int, sys.argv[2:]))
    import os
    nets = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'state', 'networks.json')))['networks']
    # endpoints that serve eth_getLogs where the default endpoint of the network does not
    LOG_RPC = {8453: 'https://base.gateway.tenderly.co', 56: 'https://bsc-rpc.publicnode.com', 999: 'https://rpc.hyperlend.finance'}
    jobs = [(n['chainId'], n['name'], LOG_RPC.get(n['chainId'], n['rpc']), n['poolManager']) for n in nets if not only or n['chainId'] in only]
    res = []
    with cf.ThreadPoolExecutor(7) as ex:
        for r in ex.map(run, jobs):
            print(f"{r['chainId']:>8} {r['name']:16} swaps {r['swaps']:>6} tick {r['tick']} pairs {r['pairs']} amount {r['amount']} {r.get('error', '')}", flush=True)
            res.append(r)
    if only and os.path.exists(out):  # a partial rerun replaces only the networks it ran
        old = json.load(open(out))['results']
        res = [r for r in old if r['chainId'] not in only] + res
    json.dump({'results': res}, open(out, 'w'), indent=1)
