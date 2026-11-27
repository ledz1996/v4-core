"""Opcode operand records from the transcribed pool math (tools/opdiff/v4math.py): every MUL, ADD, SUB, DIV,
SHL, SHR, MULMOD, LT, GT, BYTE, SAR, SIGNEXTEND the transcription executes while computing tick and price
conversions, mulDiv and swap steps on seeded random inputs. Seed 3201."""
import random, sys
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import v4math as V
REC = []
def wrap(name, op, order):
    f = getattr(V, name)
    def g(*args):
        a = [args[i] for i in order] + [0] * (3 - len(order))
        REC.append((op, a[0], a[1], a[2])); return f(*args)
    setattr(V, name, g)
wrap('mul', 'MUL', (0, 1)); wrap('add', 'ADD', (0, 1)); wrap('sub', 'SUB', (0, 1)); wrap('div', 'DIV', (0, 1))
wrap('shl', 'SHL', (0, 1)); wrap('shr', 'SHR', (0, 1)); wrap('mulmod', 'MULMOD', (0, 1, 2))
wrap('lt', 'LT', (0, 1)); wrap('gt', 'GT', (0, 1)); wrap('ref_byte', 'BYTE', (0, 1))
for nm, op in (('ref_sar', 'SAR'), ('ref_signextend', 'SIGNEXTEND')):
    if hasattr(V, nm): wrap(nm, op, (0, 1))

def vectors(seed=3201, n=800, cap=4000):
    rnd = random.Random(seed); out = []
    def rr(bits): return rnd.getrandbits(rnd.randint(1, bits))
    for i in range(n):
        REC.clear()
        try:
            t = rnd.randint(V.MIN_TICK, V.MAX_TICK); p = V.get_sqrt_price_at_tick(t)
            V.get_tick_at_sqrt_price(rnd.randint(V.MIN_SQRT_PRICE, V.MAX_SQRT_PRICE - 1))
            V.get_tick_at_sqrt_price(p)
            q = V.get_sqrt_price_at_tick(rnd.randint(V.MIN_TICK, V.MAX_TICK))
            L = rr(128)
            V.compute_swap_step(p, q, L, (rr(255) if rnd.random() < .5 else -rr(255)) & V.MASK if False else rnd.choice([1, -1]) * rr(200), rnd.choice([0, 100, 500, 3000, 10000, 999999, 10 ** 6 - 1]))
        except Exception:
            pass
        try:
            V.mul_div(rr(256), rr(256), rr(256) or 1)
        except Exception:
            pass
        out.extend(REC)
    seen = set(); per = {}; res = []
    for r in out:
        if r in seen: continue
        seen.add(r); per.setdefault(r[0], []).append(r)
    for op in sorted(per):
        L = per[op]; rnd.shuffle(L)
        res.extend(('v4math', *x) for x in L[:cap])
    return res
if __name__ == '__main__':
    import collections; v = vectors(); print(len(v), collections.Counter(x[1] for x in v))
