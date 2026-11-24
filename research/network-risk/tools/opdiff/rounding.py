"""How many mined swaps of a network depend on the rounding that
SqrtPriceMath.getAmount1Delta takes from mulmod(liquidity, priceDifference, 2^96), and
do they all carry the exact amount. On Monad this instruction runs as compiled code
that a simulated call cannot reach, so mined results are the only test of it.
Usage: SWAPS_WANT=40000 SWAPS_CALLS=500 python3 rounding.py <chainId> <out.json>"""
import sys, json, os
import swaps as W, v4math as m
from evm import s

cid = int(sys.argv[1]); out = sys.argv[2]
n = [x for x in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'state', 'networks.json')))['networks'] if x['chainId'] == cid][0]
logs, lo, head = W.collect(n['rpc'], n['poolManager'])
last = {}; c = {'chainId': cid, 'swaps': 0, 'paired': 0, 'amount1RoundedUp': 0, 'remainderNonzero': 0, 'remainderZero': 0, 'endOnTickBoundary': 0, 'token1Out': 0}
for lg in sorted(logs, key=lambda x: (int(x['blockNumber'], 16), int(x['logIndex'], 16))):
    pid = lg['topics'][1]
    if lg['topics'][0] == W.MODIFY: last.pop(pid, None); continue
    d = lg['data']; a0, a1 = s(W.word(d, 0)), s(W.word(d, 1)); price = W.word(d, 2); liq = W.word(d, 3)
    tick = s(m.ref_signextend(2, W.word(d, 4) & 0xffffff)); fee = W.word(d, 5); c['swaps'] += 1
    prev = last.get(pid)
    if prev and prev[1] == liq and liq > 0 and prev[0] != price:
        k = W.check_amounts(prev[0], price, liq, a0, a1, fee)
        if k in ('exactIn', 'exactOut', 'target'):
            c['paired'] += 1
            if price < prev[0]: c['token1Out'] += 1  # amount1 computed without rounding up; the product still goes through mulDiv with 2^96
            if k in ('exactOut', 'target') and price > prev[0]:  # token1 paid in: the amount includes the rounding bit
                c['amount1RoundedUp'] += 1
                c['remainderNonzero' if (liq * (price - prev[0])) % (1 << 96) else 'remainderZero'] += 1
            if k == 'target' and (m.get_sqrt_price_at_tick(tick) == price or m.get_sqrt_price_at_tick(tick + 1) == price): c['endOnTickBoundary'] += 1
    last[pid] = (price, liq, tick)
c['blocks'] = [lo, head]
print(c); json.dump(c, open(out, 'w'), indent=1)
