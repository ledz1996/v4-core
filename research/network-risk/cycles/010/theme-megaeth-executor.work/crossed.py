"""MegaETH (4326): full replay of mined swaps that crossed initialized ticks, plus the
distribution of ticks (negative, near the ends of the range). Read-only.

Collects Swap, ModifyLiquidity and Initialize logs of the PoolManager, pairs each swap with
the previous swap of the same pool when no ModifyLiquidity lies between, and replays with the
transcription of Pool.swap in tools/opdiff (replay.next_tick, v4math.compute_swap_step) every
pair whose liquidity changed (crossed an initialized tick) or whose amounts do not fit one
step. Tick spacing comes from the Initialize event. The end price, end tick, end liquidity and
both amounts must agree to the unit.

Usage: python3 crossed.py <out.json>
"""
import sys, os, json, time, concurrent.futures as cf
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools', 'opdiff'))
from evm import rpc, keccak, MASK, s, u, ref_signextend
import v4math as m
import replay as R
import swaps as S

URL = 'https://mainnet.megaeth.com/rpc'
PM = '0xacb7e78fa05d562e0a5d3089ec896d57d057d38e'
INIT = S.INIT


def logs_all(want, max_calls):
    os.environ['SWAPS_WANT'] = str(want)
    return S.collect(URL, PM, want=want, max_calls=max_calls)


def inits():
    out = {}
    r = rpc(URL, 'eth_getLogs', [{'address': PM, 'fromBlock': '0x0', 'toBlock': 'latest', 'topics': [INIT]}], timeout=120)
    for lg in r:
        d = lg['data']
        fee = S.word(d, 0); sp = s(S.word(d, 1)); hooks = '0x' + d[2 + 64 * 2 + 24:2 + 64 * 3]
        price = S.word(d, 3); tick = s(S.word(d, 4))
        out[lg['topics'][1]] = {'fee': fee, 'spacing': sp, 'hooks': hooks, 'price': price, 'tick': tick,
                                'c0': '0x' + lg['topics'][2][26:], 'c1': '0x' + lg['topics'][3][26:]}
    return out


def replay_one(ch, smp, sp):
    p0, p1, liq0, liq1, a0, a1 = smp['p0'], smp['p1'], smp['liq0'], smp['liq1'], smp['a0'], smp['a1']
    zfo = p1 < p0; paid, got = (-a0, a1) if zfo else (-a1, a0)
    base = int.from_bytes(keccak(bytes.fromhex(smp['pool'][2:]) + (6).to_bytes(32, 'big')), 'big')
    edge = m.MIN_SQRT_PRICE + 1 if zfo else m.MAX_SQRT_PRICE - 1
    for block in (smp['block'], smp['block'] - 1):
        for mode, amount, limit in (('exactIn', -paid, edge), ('exactOut', got, edge), ('exactIn', -paid, p1), ('exactOut', got, p1)):
            if mode == 'exactOut' and smp['fee'] >= m.MAX_SWAP_FEE: continue
            if amount == 0: continue
            try:
                p, tick, l, used, calc, steps = R.swap(ch, base, block, p0, smp['tick0'], liq0, zfo, amount, limit, smp['fee'], sp)
            except m.Revert:
                continue
            r_paid, r_got = (-used, calc) if mode == 'exactIn' else (-calc, used)
            if p == p1 and l == liq1 and r_paid == paid and r_got == got and tick == smp['tick1']:
                return {'ok': True, 'mode': mode, 'limit': 'open' if limit == edge else 'end price', 'steps': steps, 'block': block}
    return {'ok': False}


def main():
    out = sys.argv[1]
    want = int(os.environ.get('WANT', 60000)); calls = int(os.environ.get('CALLS', 600))
    pools = inits()
    logs, lo, head = logs_all(want, calls)
    print('logs', len(logs), 'blocks', lo, head, 'pools', len(pools), flush=True)
    last = {}; jobs = []; ticks = []; nswap = 0; tickbad = []
    for lg in sorted(logs, key=lambda x: (int(x['blockNumber'], 16), int(x['logIndex'], 16))):
        pid = lg['topics'][1]
        if lg['topics'][0] == S.MODIFY:
            last.pop(pid, None); continue
        d = lg['data']; nswap += 1
        a0, a1 = s(S.word(d, 0)), s(S.word(d, 1)); price = S.word(d, 2); liq = S.word(d, 3)
        tick = s(ref_signextend(2, S.word(d, 4) & 0xffffff)); fee = S.word(d, 5)
        ticks.append(tick)
        try:
            k = S.check_tick(price, tick)
        except m.Revert:
            k = None
        if not k: tickbad.append(lg['transactionHash'])
        prev = last.get(pid)
        if prev and prev[0] != price and pid in pools:
            smp = {'tx': lg['transactionHash'], 'pool': pid, 'block': int(lg['blockNumber'], 16), 'p0': prev[0], 'tick0': prev[2],
                   'p1': price, 'tick1': tick, 'liq0': prev[1], 'liq1': liq, 'a0': a0, 'a1': a1, 'fee': fee,
                   'spacing': pools[pid]['spacing'], 'hooks': pools[pid]['hooks']}
            if prev[1] != liq:
                smp['kind'] = 'crossedLiquidity'; jobs.append(smp)
            elif liq > 0 and S.check_amounts(prev[0], price, liq, a0, a1, fee) not in ('exactIn', 'exactOut', 'target'):
                smp['kind'] = 'multiStep'; jobs.append(smp)
            elif (tick < -600000 or tick > 600000):
                smp['kind'] = 'extremeTick'; jobs.append(smp)
        last[pid] = (price, liq, tick)
    print('swaps', nswap, 'jobs', len(jobs), flush=True)
    ch = R.Chain(URL, PM)

    def work(smp):
        try:
            r = replay_one(ch, smp, smp['spacing'])
        except Exception as e:  # noqa
            r = {'ok': False, 'why': str(e)[:100]}
        return {**{k: (str(v) if isinstance(v, int) and abs(v) > 2 ** 53 else v) for k, v in smp.items()}, **r}

    with cf.ThreadPoolExecutor(6) as ex:
        res = list(ex.map(work, jobs))
    summ = {}
    for r in res:
        a = summ.setdefault(r['kind'], {'n': 0, 'ok': 0, 'fail': 0, 'maxSteps': 0, 'hooked': 0, 'failedHooked': 0})
        a['n'] += 1; hooked = int(r['hooks'], 16) != 0; a['hooked'] += hooked
        if r['ok']: a['ok'] += 1; a['maxSteps'] = max(a['maxSteps'], r['steps'])
        else: a['fail'] += 1; a['failedHooked'] += hooked
    neg = [t for t in ticks if t < 0]
    dist = {'swaps': nswap, 'negative': len(neg), 'min': min(ticks), 'max': max(ticks),
            'below-400000': sum(t < -400000 for t in ticks), 'above400000': sum(t > 400000 for t in ticks),
            'beyond600000': sum(abs(t) > 600000 for t in ticks), 'beyond800000': sum(abs(t) > 800000 for t in ticks),
            'tickRelationFailures': tickbad[:20], 'tickRelationFailureCount': len(tickbad)}
    json.dump({'chainId': 4326, 'rpc': URL, 'blocks': [lo, head], 'pools': len(pools), 'ticks': dist, 'summary': summ,
               'failures': [r for r in res if not r['ok']][:80], 'results': res}, open(out, 'w'), indent=1, default=str)
    print(json.dumps({'ticks': dist, 'summary': summ}, indent=1))


if __name__ == '__main__':
    main()
