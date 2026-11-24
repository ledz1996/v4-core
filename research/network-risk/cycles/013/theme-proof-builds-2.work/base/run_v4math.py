# Pool math of tools/opdiff/v4math.py with every opcode routed through the RV64IM build (build/ops.elf).
# Usage: python3 -I run_v4math.py <tools/opdiff dir> <out.json>
import sys, os, json, random
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here); sys.path.insert(1, sys.argv[1])
import run_vectors as RV
from evm import REF, MASK
import v4math as V4r
ticks = list(range(V4r.MIN_TICK, V4r.MAX_TICK + 1, 997)) + list(range(-150, 151)) + list(range(V4r.MAX_TICK - 100, V4r.MAX_TICK + 1)) + list(range(V4r.MIN_TICK, V4r.MIN_TICK + 101))
cache = {t: V4r.get_sqrt_price_at_tick(t) for t in ticks}
RV.init([])
ev = RV.evm
import v4math as V4
V4.mul = lambda a, b: ev('MUL', a, b, 0); V4.add = lambda a, b: ev('ADD', a, b, 0); V4.sub = lambda a, b: ev('SUB', a, b, 0)
V4.div = lambda a, b: ev('DIV', a, b, 0); V4.shl = lambda n, x: ev('SHL', n, x, 0); V4.shr = lambda n, x: ev('SHR', n, x, 0)
V4.mulmod = lambda a, b, c: ev('MULMOD', a, b, c); V4.lt = lambda a, b: ev('LT', a, b, 0); V4.gt = lambda a, b: ev('GT', a, b, 0)
V4.ref_byte = lambda i, x: ev('BYTE', i, x, 0); V4.ref_signextend = lambda i, x: ev('SIGNEXTEND', i, x, 0); V4.ref_sar = lambda n, x: ev('SAR', n, x, 0)
R = dict(REF); R['MOD'] = lambda a, b, c: ev('MOD', a, b, 0); R['SGT'] = lambda a, b, c: ev('SGT', a, b, 0); V4.REF = R
rnd = random.Random(1); bad = 0; cnt = 0
for _ in range(3000):
    a = rnd.getrandbits(rnd.choice((64, 128, 200, 256))); b = rnd.getrandbits(rnd.choice((64, 128, 200, 256))); d = rnd.getrandbits(rnd.choice((64, 128, 200, 256))) or 1
    if (a * b) // d > MASK: continue
    cnt += 1
    if V4.mul_div(a, b, d) != (a * b) // d or V4.mul_div_rounding_up(a, b, d) != -((-a * b) // d): bad += 1
for _ in range(1500):
    x = rnd.getrandbits(rnd.randrange(1, 257)) or 1; cnt += 1
    if V4.most_significant_bit(x) != x.bit_length() - 1 or V4.least_significant_bit(x) != (x & -x).bit_length() - 1: bad += 1
tb = 0
for t in ticks:
    p = V4.get_sqrt_price_at_tick(t)
    if p != cache[t]: tb += 1
    if p < V4.MAX_SQRT_PRICE and V4.get_tick_at_sqrt_price(p) != t: tb += 1
    if t > V4.MIN_TICK and V4.get_tick_at_sqrt_price(p - 1) != t - 1: tb += 1
r = {'mulDivAndBitScanCases': cnt, 'bad': bad, 'ticks': len(ticks), 'tickBad': tb, 'rv64Instructions': RV.E.steps}
print(r); json.dump(r, open(sys.argv[2], 'w'), indent=1)
