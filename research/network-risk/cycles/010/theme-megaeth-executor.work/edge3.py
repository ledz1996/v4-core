"""Rerun the three crossed swaps of crossed.json that ran out of liquidity to the top of the price range,
with an exact input larger than what was used and the end price as limit (the specified amount is not in the event)."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools', 'opdiff'))
from evm import keccak
import v4math as m, replay as R
d = json.load(open(sys.argv[1])); ch = R.Chain('https://mainnet.megaeth.com/rpc', '0xacb7e78fa05d562e0a5d3089ec896d57d057d38e')
out = []
for f in d['failures']:
    p0, p1, l0, l1, a0, a1 = map(int, (f['p0'], f['p1'], f['liq0'], f['liq1'], f['a0'], f['a1']))
    zfo = p1 < p0; paid, got = (-a0, a1) if zfo else (-a1, a0)
    base = int.from_bytes(keccak(bytes.fromhex(f['pool'][2:]) + (6).to_bytes(32, 'big')), 'big')
    for block in (f['block'], f['block'] - 1):
        for amt in (-(10 ** 30), 10 ** 30):
            p, tick, l, used, calc, steps = R.swap(ch, base, block, p0, f['tick0'], l0, zfo, amt, p1, f['fee'], f['spacing'])
            rp, rg = (-used, calc) if amt < 0 else (-calc, used)
            ok = p == p1 and l == l1 and tick == f['tick1'] and rp == paid and rg == got
            out.append({'tx': f['tx'], 'block': block, 'mode': 'exactIn' if amt < 0 else 'exactOut', 'ok': ok, 'steps': steps, 'paid': [str(paid), str(rp)], 'got': [str(got), str(rg)]})
            print(out[-1])
json.dump(out, open(sys.argv[2], 'w'), indent=1)
