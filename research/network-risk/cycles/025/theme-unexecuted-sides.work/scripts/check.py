"""Task 3: check returned words against arithmetic that does not come from src/.

Usage: python3 check.py <allcases.json> <results.json> <out.json>
Swap cases: with L the active liquidity and [a, b] the part of the price move inside the position (Fractions), the
exact amounts are A0 = L*2^96*(b-a)/(a*b) and A1 = L*(b-a)/2^96. The pool must receive gross input g with
g*(1e6-f) >= 1e6*A_in and pay output o <= A_out, take no more than |amountSpecified| on exact input and pay no more
than amountSpecified on exact output, and credit LPs no more fee than g - A_in. The only use of v4math is the price of
the two position ticks (where liquidity starts), which is a property of the pool and not of the swap being checked.
Donate, clear, settleFor and ERC-6909 cases are checked for conservation of balances and deltas.
"""
import sys, os, json
from fractions import Fraction as F
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v4math as V
M = (1 << 256) - 1; Q96 = 1 << 96; Q128 = 1 << 128; MASK160 = (1 << 160) - 1


def s128(x):
    x &= (1 << 128) - 1
    return x - (1 << 128) if x >> 127 else x


def s256(x):
    return x - (1 << 256) if x >> 255 else x


def unpack(d):
    return s128(d >> 128), s128(d)


def check_swap(c, W, kind):
    i = 6 if kind == 0 else 9
    out = {'id': c['id'], 'tag': c['tag']}
    if W[0] != 1: return dict(out, status='init reverted', sel=hex(W[1] >> 224))
    if W[3] == 0: return dict(out, status='liquidity add reverted', sel=hex(W[4] >> 224))
    if kind == 5 and W[6] != 1: out['dynFeeUpdate'] = 'reverted %#x' % (W[7] >> 224)
    A = W[i:i + 6]; sw = W[i + 6:i + 9]; Bs = W[i + 9:i + 15]; bal = W[i + 15:i + 19]
    if sw[0] != 1: return dict(out, status='swap reverted', sel=hex(sw[1] >> 224))
    d0, d1 = unpack(sw[1])
    viol = []
    # consistency: delta of the driver moved by exactly the swap delta
    if (s256(Bs[0]) - s256(A[0]), s256(Bs[1]) - s256(A[1])) != (d0, d1): viol.append('snapshot delta != swap delta')
    s0, s1 = A[2] & MASK160, Bs[2] & MASK160
    L = A[5]
    f = (A[2] >> 208) & 0xffffff if kind == 0 else None
    if kind == 5: f = (Bs[2] >> 208) & 0xffffff
    zfo, amt = c['zfo'], c['amt']
    pl, pu = V.get_sqrt_price_at_tick(c['tl']), V.get_sqrt_price_at_tick(c['tu'])
    lo, hi = max(min(s0, s1), pl), min(max(s0, s1), pu)
    if hi <= lo: La = 0; A0 = A1 = F(0)
    else:
        La = c['liq'] if W[3] == 1 else 0
        A0 = F(La * Q96 * (hi - lo), lo * hi); A1 = F(La * (hi - lo), Q96)
    if zfo:
        g, o, Ain, Aout = -d0, d1, A0, A1
        if s1 > s0: viol.append('price moved up on zeroForOne')
    else:
        g, o, Ain, Aout = -d1, d0, A1, A0
        if s1 < s0: viol.append('price moved down on oneForZero')
    if g < 0: viol.append('pool paid on the input side')
    if o < 0: viol.append('pool received on the output side')
    if g * (10 ** 6 - f) < Ain * 10 ** 6: viol.append('input below the exact amount plus fee')
    if o > Aout: viol.append('output above the exact amount')
    if amt < 0 and g > -amt: viol.append('took more than amountSpecified')
    if amt > 0 and o > amt: viol.append('paid more than amountSpecified')
    fgi = 3 if zfo else 4
    dfg = (Bs[fgi] - A[fgi]) & M
    if La and F(dfg * La, Q128) > g - Ain: viol.append('fee growth credits more than the fee paid')
    out.update(status='ok', s0=s0, s1=s1, L=La, fee=f, gross=g, out=o, slackIn=float(g - Ain / (F(10 ** 6 - f, 10 ** 6) if f < 10 ** 6 else 1)) if f < 10 ** 6 else None,
               slackOut=float(Aout - o), violations=viol)
    # conservation after settlement: PoolManager holds deposit plus swap net
    dep0, dep1 = unpack(W[4])
    if bal[0] != -dep0 - d0 or bal[1] != -dep1 - d1: viol.append('PoolManager balance != deposits plus swap delta')
    return out


def check_donate(c, W):
    out = {'id': c['id'], 'tag': c['tag']}
    if W[0] != 1: return dict(out, status='init reverted')
    if W[3] == 0: return dict(out, status='liquidity add reverted', sel=hex(W[4] >> 224))
    A = W[6:12]; dn = W[12:15]; Bs = W[15:21]; bal = W[21:25]
    a0, a1 = c['p']
    if dn[0] != 1: return dict(out, status='donate reverted', sel=hex(dn[1] >> 224))
    viol = []
    d0, d1 = unpack(dn[1])
    if (d0, d1) != (-a0, -a1): viol.append('donate delta != amounts')
    L = A[5]
    for k, a in ((3, a0), (4, a1)):
        dfg = (Bs[k] - A[k]) & M
        if dfg * L > a * Q128: viol.append('fee growth credits more than donated')
        if a and L and (dfg + 1) * L <= a * Q128: viol.append('fee growth below floor(a*2^128/L)')
    dep0, dep1 = unpack(W[4])
    if bal[0] != -dep0 + a0 or bal[1] != -dep1 + a1: viol.append('PoolManager balance != deposits plus donation')
    return dict(out, status='ok', violations=viol)


def check_clear(c, W):
    a, x = c['p']
    st, dlt, cl, dl2, bal = W[0:3], W[3], W[4:7], W[7], W[8:12]
    viol = []
    if st[0] != 1 or st[1] != a: viol.append('settle did not credit the payment')
    if dlt != a: viol.append('delta after settle != payment')
    exact = (x == a and a < (1 << 127))
    if exact:
        if cl[0] != 1 or dl2 != 0: viol.append('exact clear failed')
        if bal[0] != a or bal[2] != 0: viol.append('cleared credit left the PoolManager')
    else:
        if cl[0] == 1: viol.append('wrong amount was cleared')
        if dl2 != a: viol.append('delta changed by a failed clear')
        if bal[0] != 0 or bal[2] != a: viol.append('credit not returned after failed clear')
    return {'id': c['id'], 'tag': c['tag'], 'status': 'ok', 'clearOk': cl[0], 'sel': hex(cl[1] >> 224) if not cl[0] else None, 'violations': viol}


def check_settlefor(c, W):
    a = c['p'][0]
    sf, dD, dS, tk, dD2, dS2, bal, sbal = W[0:3], W[3], W[4], W[5:8], W[6 + 2], W[9], W[10:14], W[14]
    dD2, dS2 = W[8], W[9]
    viol = []
    if sf[0] != 1 or sf[1] != a: viol.append('settleFor did not report the payment')
    if dD != 0 or dS != a: viol.append('credit not booked to the recipient only')
    if tk[0] != 1 or dD2 != 0 or dS2 != 0: viol.append('recipient could not take its credit')
    if sbal != a or bal[0] != 0: viol.append('balances do not conserve')
    return {'id': c['id'], 'tag': c['tag'], 'status': 'ok', 'violations': viol}


def check_6909(c, W):
    a, x, fin, y, z, wv = c['p']
    viol = []
    # final block: D, B, R, S claims, isOperator, delta D, delta S, PM t0, PM t1, D t0, D t1, S t0
    fin_ = W[-12:]
    cD, cB, cR, cS, op, dD, dS, pm0, pm1, D0, D1, S0 = fin_[0:12]
    claims = cD + cB + cR + cS
    if claims != pm0: viol.append('claims %d != PoolManager balance %d' % (claims, pm0))
    if pm0 + D0 + S0 != max(a, 0) and a < (1 << 127): viol.append('token units not conserved')
    if dD or dS: viol.append('open delta')
    return {'id': c['id'], 'tag': c['tag'], 'status': 'ok', 'claims': [cD, cB, cR, cS], 'violations': viol}


def main():
    allc = json.load(open(sys.argv[1])); res = json.load(open(sys.argv[2]))['results']
    rows = []
    for c in allc['cases']:
        r = res.get(str(c['id'])) or res.get(c['id'])
        if r is None: continue
        if not r.get('ok'):
            rows.append({'id': c['id'], 'tag': c['tag'], 'status': 'unlock reverted', 'revert': r.get('revert', r.get('error', ''))[:80]}); continue
        W = [int(x, 16) for x in r['w']]
        k = c['kind']
        if k in (0, 5): rows.append(check_swap(c, W, k))
        elif k == 1: rows.append(check_donate(c, W))
        elif k == 2: rows.append(check_clear(c, W))
        elif k == 3: rows.append(check_settlefor(c, W))
        elif k == 4: rows.append(check_6909(c, W))
        else: rows.append({'id': c['id'], 'tag': c['tag'], 'status': 'raw', 'words': len(W)})
    from collections import Counter
    st = Counter(x['status'] for x in rows)
    viol = [x for x in rows if x.get('violations')]
    print(st); print('cases with a violation', len(viol))
    for x in viol[:20]: print(x['id'], x['tag'], x['violations'])
    json.dump({'status': dict(st), 'violations': viol, 'rows': rows}, open(sys.argv[3], 'w'), indent=0)


if __name__ == '__main__':
    main()
