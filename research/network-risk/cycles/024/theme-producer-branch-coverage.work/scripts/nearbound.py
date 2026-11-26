"""Find Swap logs whose end state is near the tick or price bounds, or whose pool liquidity is at least 2^96. usage: nearbound.py <logs json>..."""
import json, sys
def s(x, b): x &= (1 << b) - 1; return x - (1 << b) if x >> (b - 1) else x
MINP, MAXP = 4295128739, 1461446703485210103287273052203988822378723970342
ex = []; n = 0; hiP = 0; hiL = 0
for f in sys.argv[1:]:
    for l in json.load(open(f))['logs']:
        w = [int(l['data'][2 + 64 * i:2 + 64 * (i + 1)], 16) for i in range(6)]
        a0, a1, p, L, t = s(w[0], 128), s(w[1], 128), w[2], w[3], s(w[4], 24); n += 1
        hiP = max(hiP, p); hiL = max(hiL, L)
        if t < -887272 + 25600 or t > 887272 - 25600 or p - MINP < 65536 or MAXP - p < 65536 or L >= 1 << 96 or p >= 1 << 129:
            ex.append((int(l['blockNumber'], 16), l['transactionHash'], t, p.bit_length(), L.bit_length(), a0, a1))
print(n, 'maxPriceBits', hiP.bit_length(), 'maxLiquidityBits', hiL.bit_length(), len(ex), len({e[1] for e in ex}))
for e in ex[:40]: print(e)
