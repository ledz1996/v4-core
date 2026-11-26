"""Task 3, injected state: an exact-output swap (zeroForOne, currency1 out) that stops short of its target with an output above
2^160, which takes the mulDivRoundingUp branch of getNextSqrtPriceFromAmount1RoundingDown (SqrtPriceMath.sol:102-106, blocks
20892-20974 with the MULMOD at pc 20958). The pool is created by initialize; its liquidity word (Pool.State slot 3) is then written
directly, because no ordinary account can deposit enough (each deposit is capped below 2^127 by toInt128). Analysis only.
Usage: PM_BUILD=... python3 t3inject.py <out file>"""
import sys, os
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import sets2tx as S
import pmdiff6 as R6, v4math as m
code = S.P.fetch_code(); PMI = S.PMI
out = sys.argv[1]; n = 0
k = R6.key(R6.T0, R6.T1, 3000, 60, 0)
with open(out, 'w') as f:
    for tick in (887000, 880000, 870000):
        p0 = m.get_sqrt_price_at_tick(tick)
        for L in ((1 << 127), (1 << 127) - 1, 3 << 120, (1 << 128) - 1):
            for amt in ((1 << 160) + 1, 1 << 161, (1 << 161) + 12345, 1 << 170, (1 << 175) * 3 + 1):
                w = R6.world(code)
                ok, _ = w.call(0, R6.DRV, 0, b'\xff' + R6.it(PMI, R6.init(k, p0)) + R6.end(0), False, 0)  # locked mode: the driver calls initialize directly
                assert w.storage.get((PMI, R6.pslot(k, 0)), 0) != 0
                assert ok
                w.storage[(PMI, R6.pslot(k, 3))] = L
                w.nodes = []; w.loglist = []
                data = R6.it(PMI, R6.swap(k, True, amt, m.MIN_SQRT_PRICE + 1)) + R6.end(0)
                n += 1
                print(S.write_tx(f, f'inject-t{tick}-L{L.bit_length()}-{n}', w, R6.DRV, data, 20_000_000))
