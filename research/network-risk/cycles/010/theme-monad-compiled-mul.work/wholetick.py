"""Every tick of the range through the compiled multiplication paths.

For each tick in a slice of [-887272, 887272]: getSqrtPriceAtTick and then
getTickAtSqrtPrice of the result, as tools/opdiff/v4math.py writes them from
src/libraries/TickMath.sol, with every MUL replaced by the transcription of the path
Monad v0.16.5 compiles it to: a multiply by one of the literals of sites.json goes through
mul_optimized (and so mul_with_bit_size and MulEmitter, or the runtime call for full width
literals), mul(r, r) goes through monad_vm_runtime_mul with both operand pointers equal, and
every other product through monad_vm_runtime_mul. Each compiled product is checked against
Python integers, with a fresh random register picture each time, and
getTickAtSqrtPrice(getSqrtPriceAtTick(t)) == t is checked as well.
Usage: python3 -I wholetick.py <repo>/research/network-risk <workdir> <slice> <slices>
"""
import sys, os, json, random, time
base, wd, k, K = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
sys.path.insert(0, os.path.join(base, 'tools', 'opdiff')); sys.path.insert(0, wd)
import v4math as V
import run as R

rng = random.Random(1000 + k); random.seed(2000 + k)
LIT = set(R.SITE_MUL_LITERALS)
stats = {}; fails = []
def cmul(a, b):
    if b in LIT: R.mul_optimized(rng, b, a, stats, fails, 'tick')
    elif a in LIT: R.mul_optimized(rng, a, b, stats, fails, 'tick')
    else:
        same = a == b
        R.rt_mul(rng, a, b, stats, fails, 'rr' if same else 'rt', same_ok=same)
    return (a * b) % (1 << 256)
V.mul = cmul
t0 = time.time(); bad = []; n = 0; bits = 0
for tick in range(-887272 + k, 887273, K):
    p = V.get_sqrt_price_at_tick(tick)
    if tick == 887272:  # MAX_SQRT_PRICE is outside the domain of getTickAtSqrtPrice (TickMath.sol:128-130)
        n += 1; continue
    t = V.get_tick_at_sqrt_price(p)
    n += 1
    if t != tick and len(bad) < 20: bad.append([tick, p, t])
out = {'slice': k, 'slices': K, 'ticks': n, 'roundTripMismatch': bad, 'mulStats': stats, 'mulFailures': fails,
       'seconds': round(time.time() - t0, 1)}
json.dump(out, open(os.path.join(wd, 'wholetick-%d-of-%d.json' % (k, K)), 'w'), indent=1)
print(k, n, len(bad), stats, len(fails))
