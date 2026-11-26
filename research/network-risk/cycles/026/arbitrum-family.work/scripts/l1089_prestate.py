"""Lead L-1089, second route. Pocket (nitro v3.12.4) now serves debug_traceTransaction
with the prestateTracer for Arbitrum One transaction 0x06c45e81... . Every storage word
the transaction read is in that prestate, so its three swaps are replayed through the
Pool.swap transcription of tools/opdiff/replay.py reading only from the prestate. A slot
the transcription reads that is not in the prestate is reported (it would mean the
transcription walks a path the chain did not).
"""
import sys, os, json
OPD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'tools', 'opdiff')
sys.path.insert(0, OPD)
from evm import keccak
import replay as R
R.SPACINGS = R.SPACINGS + list(range(7656, 7716))  # cycle 26: full-range bitmap bits at compressed -115 and 115 bound the spacing to 7656..7715

W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'raw')
pre = json.load(open(os.path.join(W, 'tx06c45e-prestate.json')))['result']
rc = json.load(open(os.path.join(W, '..', '..', '..', '025', 'arbitrum-family.work', 'raw', 'tx06c45e.json')))['result']
PM = '0x360e68faccca8ca495c1b759fd9eee466db9fb32'
st = {int(k, 16): int(v, 16) for a, acc in pre.items() if a.lower() == PM for k, v in acc.get('storage', {}).items()}
SWAP = '0x' + keccak(b'Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)').hex()


class Pre:
    missing = []

    def sload(self, slot, block):
        if slot not in st:
            Pre.missing.append(hex(slot)); return 0
        return st[slot]


def s(x, bits): return x - (1 << bits) if x >> (bits - 1) else x


out = {'prestateSlots': len(st), 'swaps': []}
state = {}
for lg in sorted([l for l in rc['logs'] if l['address'].lower() == PM and l['topics'][0] == SWAP], key=lambda l: int(l['logIndex'], 16)):
    pool = lg['topics'][1]; d = lg['data'][2:]; w = [int(d[64 * i:64 * i + 64], 16) for i in range(6)]
    base = int.from_bytes(keccak(bytes.fromhex(pool[2:]) + (6).to_bytes(32, 'big')), 'big')
    if pool not in state:
        s0 = st[base]; state[pool] = (s0 & ((1 << 160) - 1), s(s0 >> 160 & 0xffffff, 24), st[base + 3])
    p0, t0, l0 = state[pool]
    smp = {'pool': pool, 'p0': p0, 'tick0': t0, 'liq': l0, 'p1': w[2], 'tick1': s(w[4], 256), 'a0': s(w[0], 256), 'a1': s(w[1], 256), 'fee': w[5], 'block': int(rc['blockNumber'], 16), 'tx': rc['transactionHash']}
    Pre.missing = []
    if l0 != w[3]:
        res = {'ok': False, 'why': 'liquidity changed across the swap; replay.replay requires equal start and end liquidity'}
        # run anyway via swap with each spacing
        for sp in R.SPACINGS:
            zfo = w[2] < p0; paid, got = (-smp['a0'], smp['a1']) if zfo else (-smp['a1'], smp['a0'])
            edge = R.m.MIN_SQRT_PRICE + 1 if zfo else R.m.MAX_SQRT_PRICE - 1
            for mode, amount, limit in (('exactIn', -paid, edge), ('exactOut', got, edge), ('exactIn', -paid, w[2]), ('exactOut', got, w[2])):
                try:
                    p, tick, l, used, calc, steps = R.swap(Pre(), base, 0, p0, t0, l0, zfo, amount, limit, w[5], sp)
                except R.m.Revert:
                    continue
                r_paid, r_got = (-used, calc) if mode == 'exactIn' else (-calc, used)
                if p == w[2] and l == w[3] and r_paid == paid and r_got == got and tick == smp['tick1']:
                    res = {'ok': True, 'mode': mode, 'spacing': sp, 'steps': steps, 'liquidityCrossed': True}; break
            if res['ok']: break
    else:
        res = R.replay(Pre(), smp)
    out['swaps'].append({'logIndex': int(lg['logIndex'], 16), 'pool': pool, 'start': [hex(p0), t0, l0], 'end': [hex(w[2]), s(w[4], 256), w[3]],
                         'amount0': smp['a0'], 'amount1': smp['a1'], 'fee': w[5], 'result': res, 'slotsNotInPrestate': sorted(set(Pre.missing))[:20]})
    state[pool] = (w[2], s(w[4], 256), w[3])
json.dump(out, open(os.path.join(W, 'l1089-prestate-replay.json'), 'w'), indent=1)
print(json.dumps(out, indent=1))
