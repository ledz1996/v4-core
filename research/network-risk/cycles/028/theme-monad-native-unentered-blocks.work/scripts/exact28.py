"""Cycle 28: exact-fraction check of the F scenarios of scen28.py (one swap per run transaction, liquidity 1e20 over
[-600, 600], prices kept inside the range). For each swap, with a and b the pool price before and after (slot0 words of
the snapshots) and L the liquidity: A0 = L*2^96*|b-a|/(a*b), A1 = L*|b-a|/2^96. The pool must receive g with
g*(1e6-fee) >= 1e6*A_in, pay o <= A_out, take exactly |amountSpecified| on exact input and pay exactly amountSpecified on
exact output, and credit LPs (fee growth times L / 2^128) plus the protocol no more than g - A_in. A planted one-unit
overpayment is applied to every swap to show the check can fail. Nothing here comes from src/ or v4math.
Usage: python3 -I exact28.py <results.json> <engine: ref|0.16.5|0.16.7> <out.json>"""
import sys, json
from fractions import Fraction as F
R = json.load(open(sys.argv[1])); eng = sys.argv[2]
Q96 = 1 << 96; Q128 = 1 << 128; M160 = (1 << 160) - 1
def s128(x): x &= (1 << 128) - 1; return x - (1 << 128) if x >> 127 else x
FSW = [(True, -10 ** 18), (False, 3 * 10 ** 17), (False, -2 * 10 ** 18), (True, 5 * 10 ** 17), (True, -1), (False, -2), (True, 1), (False, 7)]
rows = []; planted = 0; nsw = 0
for nm, r in R['results'].items():
    if not nm.startswith('F '): continue
    lp = int(nm.split('lp=')[1].split()[0]); pfv = int(nm.split('pf=')[1], 16)
    outs = r['ref'] if eng == 'ref' else r[eng]['native']
    runs = [o for o in outs if 'w' in o]
    snaps = [[int(x, 16) for x in o['w']] for o in runs]
    L = 10 ** 20
    acc = [int(x[1], 16) for x in outs[-1]['calls']]
    pacc = [0, 0]
    for k, (zfo, amt) in enumerate(FSW):
        W0, W1 = snaps[k], snaps[k + 1]
        nsw += 1
        if W1[0] != 1: rows.append({'scen': nm, 'swap': k, 'status': 'reverted'}); continue
        d0, d1 = s128(W1[1] >> 128), s128(W1[1])
        sl_a = W0[-8] if k else W0[-8]
        a = (W0[len(W0) - 8]) & M160; b = W1[len(W1) - 8] & M160
        fg0a, fg1a, fg0b, fg1b = W0[-7], W0[-6], W1[-7], W1[-6]
        lo, hi = min(a, b), max(a, b)
        A0 = F(L * Q96 * (hi - lo), lo * hi); A1 = F(L * (hi - lo), Q96)
        pf = (pfv & 0xfff) if zfo else (pfv >> 12)
        fee = lp if pf == 0 else pf + lp - pf * lp // 10 ** 6
        if zfo: g, o, Ai, Ao, fgd = -d0, d1, A0, A1, fg0b - fg0a
        else: g, o, Ai, Ao, fgd = -d1, d0, A1, A0, fg1b - fg1a
        v = []
        def chk(o):
            v = []
            if g * (10 ** 6 - fee) < Ai * 10 ** 6: v.append('input below exact plus fee')
            if o > Ao: v.append('output above exact')
            if amt < 0 and g != -amt: v.append('input differs from exact-in amount')
            if amt > 0 and o != amt: v.append('output differs from exact-out amount')
            if F(fgd * L, Q128) > g - Ai: v.append('LP fee credit above gross minus exact')
            if (zfo and (b > a)) or (not zfo and b < a): v.append('price moved the wrong way')
            return v
        v = chk(o)
        if chk(o + 1): planted += 1
        rows.append({'scen': nm, 'swap': k, 'zfo': zfo, 'amountSpecified': amt, 'gross': g, 'out': o, 'exactIn': str(Ai), 'exactOut': str(Ao),
                     'fee': fee, 'violations': v})
    rows.append({'scen': nm, 'protocolFeesAccrued': acc})
bad = [x for x in rows if x.get('violations')]
json.dump({'engine': eng, 'swaps': nsw, 'violations': len(bad), 'plantedCaught': planted, 'rows': rows}, open(sys.argv[3], 'w'), indent=0)
print(eng, 'swaps', nsw, 'checked', sum(1 for x in rows if 'violations' in x), 'violations', len(bad), 'planted caught', planted, bad[:3])
