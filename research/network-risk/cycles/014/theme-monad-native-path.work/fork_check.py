"""For unmatched v3-style swaps of one factory: does the output follow from start price, end price and
liquidity (fee-free part of SwapMath), and which fee in pips reproduces the input? Usage: python3 fork_check.py <logs.jsonl> <factory> <out.json>"""
import sys, os, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import bigcheck as B, collect as C
import v4math as m
from evm import s
meta = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'raw', 'v3meta.json')))
fac = sys.argv[2].lower()
pools = {a for a, v in meta.items() if v.get('factory') and v.get('fee') and ('0x' + v['factory'][-40:]) == fac}
logs = []
for line in open(sys.argv[1]):
    for l in json.loads(line)['logs'] or []:
        if l['a'] in pools: logs.append(l)
logs.sort(key=lambda l: (l['b'], l['i']))
last = {}; st = collections.Counter(); fees = collections.Counter(); samples = []
for l in logs:
    if l['t'][0] != C.V3SWAP: last.pop(l['a'], None); continue
    d = l['d']; a0, a1 = s(B.word(d, 0)), s(B.word(d, 1)); p1, L = B.word(d, 2), B.word(d, 3); fee = int(meta[l['a']]['fee'], 16)
    pv = last.get(l['a']); last[l['a']] = (p1, L)
    if not pv or pv[1] != L or L == 0 or pv[0] == p1: continue
    p0 = pv[0]; zfo = p1 < p0; paid, got = (a0, -a1) if zfo else (a1, -a0)
    mode, _ = B.check(p0, p1, L, paid, got, fee)
    if mode: st['matchStaticFee'] += 1; continue
    out = m.amount1_delta(p1, p0, L, False) if zfo else m.amount0_delta(p0, p1, L, False)
    ain = m.amount0_delta(p1, p0, L, True) if zfo else m.amount1_delta(p0, p1, L, True)
    if out != got: st['outputDiffers'] += 1; samples.append(l['h']); continue
    # find fee pips f that reproduces exact input: next_price_from_input(p0, L, mulDiv(paid, 1e6-f, 1e6)) == p1
    hit = None
    f0 = 10**6 - (ain * 10**6) // paid if paid else 0
    for f in range(max(0, f0 - 3), min(10**6, f0 + 4)):
        try:
            if m.next_price_from_input(p0, L, m.mul_div(paid, 10**6 - f, 10**6), zfo) == p1: hit = f; break
        except m.Revert: pass
    if hit is None: st['outputExactFeeNotFound'] += 1
    else: st['outputExactOtherFee'] += 1; fees[(fee, hit)] += 1
json.dump({'factory': fac, 'pools': len(pools), 'stats': st, 'feePairs': {f'{a}->{b}': c for (a, b), c in fees.most_common(40)}, 'outputDiffersSamples': samples[:20]}, open(sys.argv[3], 'w'), indent=1)
print(st, fees.most_common(10))
