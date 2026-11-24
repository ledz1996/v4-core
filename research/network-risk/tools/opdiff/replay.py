"""Full replay of swaps that took more than one step. swaps.py leaves two groups
unproven: "multi" (a few units from the single-step values) and "other" (far from
them, because the swap crossed liquidity that came back to the same total). This
script reruns Pool.swap step by step in the transcription of the source, reading the
tick bitmap and the liquidityNet of each crossed tick from the PoolManager's storage
at the block of the swap through extsload. The tick spacing is not in the Swap event,
so the candidates are tried in turn; only the right one reproduces the amounts.

Usage: python3 replay.py <swaps.json> <out.json>
"""
import sys, json, time, concurrent.futures as cf
from evm import rpc, keccak, MASK, s, u, ref_signextend
import v4math as m

EXT = '0x' + keccak(b'extsload(bytes32)')[:4].hex()
SPACINGS = [1, 10, 60, 200, 2, 5, 20, 50, 100, 4, 8, 15, 25, 30, 40, 80, 120, 150, 250, 300, 500, 1000, 2000, 3, 6, 12, 16, 32, 64, 128, 887]


class Chain:
    def __init__(self, url, pm): self.url, self.pm, self.cache = url, pm, {}

    def sload(self, slot, block):
        k = (slot, block)
        if k not in self.cache:
            for attempt in range(6):
                try:
                    self.cache[k] = int(rpc(self.url, 'eth_call', [{'to': self.pm, 'data': EXT + slot.to_bytes(32, 'big').hex()}, hex(block)], timeout=40), 16); break
                except Exception as e:  # noqa
                    if attempt < 5 and ('429' in str(e) or 'rate' in str(e).lower()): time.sleep(3 * (attempt + 1)); continue
                    raise
        return self.cache[k]


def compress(tick, sp):
    q = abs(tick) // sp
    q = -q if tick < 0 else q
    return q - (1 if (tick < 0 and tick % sp != 0) else 0)


def next_tick(ch, base, block, tick, sp, lte):
    c = compress(tick, sp)
    if lte:
        word, bit = c >> 8, c & 0xff
        mask = MASK >> (255 - bit)
        masked = ch.sload(int.from_bytes(keccak(u(word).to_bytes(32, 'big') + ((base + 5) & MASK).to_bytes(32, 'big')), 'big'), block) & mask
        return ((c - (bit - m.most_significant_bit(masked))) * sp, True) if masked else ((c - bit) * sp, False)
    c += 1
    word, bit = c >> 8, c & 0xff
    mask = MASK ^ ((1 << bit) - 1)
    masked = ch.sload(int.from_bytes(keccak(u(word).to_bytes(32, 'big') + ((base + 5) & MASK).to_bytes(32, 'big')), 'big'), block) & mask
    return ((c + (m.least_significant_bit(masked) - bit)) * sp, True) if masked else ((c + (255 - bit)) * sp, False)


def swap(ch, base, block, p, tick, liq, zfo, amount, limit, fee, sp, max_steps=3000):
    remaining = amount; calc = 0; steps = 0
    while not (remaining == 0 or p == limit):
        steps += 1
        if steps > max_steps: raise m.Revert('too many steps')
        start = p
        tn, init = next_tick(ch, base, block, tick, sp, zfo)
        tn = max(m.MIN_TICK, min(m.MAX_TICK, tn))
        pn = m.get_sqrt_price_at_tick(tn)
        target = (pn if pn >= limit else limit) if zfo else (pn if pn < limit else limit)
        p, a_in, a_out, f = m.compute_swap_step(p, target, liq, remaining, fee)
        if amount > 0:
            remaining -= a_out; calc -= a_in + f
        else:
            remaining += a_in + f; calc += a_out
        if p == pn:
            if init:
                w0 = ch.sload(int.from_bytes(keccak(u(tn).to_bytes(32, 'big') + ((base + 4) & MASK).to_bytes(32, 'big')), 'big'), block)
                net = (w0 >> 128); net = net - (1 << 128) if net >> 127 else net
                liq = liq - net if zfo else liq + net
                if liq < 0 or liq >> 128: raise m.Revert('liquidity out of range')
            tick = tn - 1 if zfo else tn
        elif p != start:
            tick = m.get_tick_at_sqrt_price(p)
    return p, tick, liq, amount - remaining, calc, steps


def replay(ch, smp):
    p0, p1, liq, a0, a1 = int(smp['p0']), int(smp['p1']), int(smp['liq']), int(smp['a0']), int(smp['a1'])
    zfo = p1 < p0; paid, got = (-a0, a1) if zfo else (-a1, a0)
    base = int.from_bytes(keccak(bytes.fromhex(smp['pool'][2:]) + (6).to_bytes(32, 'big')), 'big')
    why = 'no spacing reproduced it'
    for block in (smp['block'], smp['block'] - 1):
        for sp in SPACINGS:
            stop = False
            # the price limit is not in the event: the swap either ran with an open limit and used up its amount,
            # or it stopped at a limit equal to the end price
            edge = m.MIN_SQRT_PRICE + 1 if zfo else m.MAX_SQRT_PRICE - 1
            for mode, amount, limit in (('exactIn', -paid, edge), ('exactOut', got, edge), ('exactIn', -paid, p1), ('exactOut', got, p1)):
                if mode == 'exactOut' and smp['fee'] >= m.MAX_SWAP_FEE: continue
                try:
                    p, tick, l, used, calc, steps = swap(ch, base, block, p0, smp['tick0'], liq, zfo, amount, limit, smp['fee'], sp)
                except m.Revert:
                    continue
                except Exception as e:  # noqa
                    why = 'state not served: ' + str(e)[:60]; stop = True; break
                r_paid, r_got = (-used, calc) if mode == 'exactIn' else (-calc, used)
                if p == p1 and l == liq and r_paid == paid and r_got == got and tick == smp['tick1']:
                    return {'ok': True, 'mode': mode, 'limit': 'open' if limit == edge else 'end price', 'spacing': sp, 'steps': steps, 'block': block}
            if stop: break
    return {'ok': False, 'why': why}


if __name__ == '__main__':
    import os
    src, out = sys.argv[1], sys.argv[2]
    nets = {n['chainId']: n for n in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'state', 'networks.json')))['networks']}
    STATE_RPC = {1: 'https://mainnet.gateway.tenderly.co', 8453: 'https://base.gateway.tenderly.co', 56: 'https://bsc-rpc.publicnode.com'}
    jobs = []
    for r in json.load(open(src))['results']:
        for kind in ('otherSamples', 'multiSamples'):
            for smp in r.get(kind, []):
                jobs.append((r['chainId'], r['name'], kind[:-7], smp))
    chains = {cid: Chain(STATE_RPC.get(cid, nets[cid]['rpc']), nets[cid]['poolManager']) for cid in {j[0] for j in jobs}}

    def work(j):
        cid, name, kind, smp = j
        try:
            res = replay(chains[cid], smp)
        except Exception as e:  # noqa
            res = {'ok': False, 'why': str(e)[:100]}
        return {'chainId': cid, 'name': name, 'kind': kind, 'tx': smp['tx'], **res}

    with cf.ThreadPoolExecutor(4) as ex:
        res = list(ex.map(work, jobs))
    summ = {}
    for r in res:
        k = (r['name'], r['kind']); a = summ.setdefault(k, {'replayed': 0, 'failed': 0, 'maxSteps': 0, 'why': {}})
        if r['ok']:
            a['replayed'] += 1; a['maxSteps'] = max(a['maxSteps'], r['steps'])
        else:
            a['failed'] += 1; w = r['why'][:40]; a['why'][w] = a['why'].get(w, 0) + 1
    for k, v in sorted(summ.items()): print(k, v)
    json.dump({'results': res}, open(out, 'w'), indent=1)
