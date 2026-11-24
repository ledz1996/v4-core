"""Exercise the uncovered fallback of getNextSqrtPriceFromAmount0RoundingUp (add) at
SqrtPriceMath.sol:52, pcs 23901-23932, which pool scripts never reached, and compare with the
source semantics. Usage: python3 -I fallback.py"""
import sys, os, random, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H
M = 1 << 256; MASK = M - 1; U160 = (1 << 160) - 1
MIN_P, MAX_P = 4295128739, 1461446703485210103287273052203988822378723970342
def up(a, b): return -(-a // b)
def model(p, L, a):
    if a == 0: return p
    n1 = L << 96; prod = (a * p) & MASK
    if prod // a == p and n1 + prod < M:
        q = up(n1 * p, n1 + prod)
        return 'revert' if q >= M else q & U160
    den = n1 // p + a
    return 'revert' if den >= M else up(n1, den) & U160
rnd = random.Random(52); n = 0; bad = 0; fb = 0
for _ in range(3000):
    p = rnd.choice([rnd.randint(MAX_P >> 8, MAX_P - 1), rnd.randint(MIN_P, MAX_P - 1), MAX_P - 1])
    L = rnd.choice([rnd.getrandbits(128), (1 << 128) - 1, rnd.getrandbits(rnd.randint(1, 128)) | 1])
    a = rnd.choice([rnd.getrandbits(rnd.randint(90, 200)), (M - 1) // p + 1, rnd.getrandbits(256)]) or 1
    w = H.World({H.PM: H.HCODE}); w.init_stack = [H.RET, a, L, p]; w.init_pc = H.EP['fun_getNextSqrtPriceFromAmount0RoundingUp']
    ok, ret = w.run(H.PM, H.PM, 0, 0, b'', False, 0)
    got = w.final_stack[-1] if ok else 'revert'
    n += 1; bad += got != model(p, L, a); fb += 23901 in w.cover.get(H.PM, set())
print(json.dumps({'cases': n, 'mismatches': bad, 'casesThroughPc23901': fb}))
