"""Scenario generator for harness.cpp. Writes world.txt and scen-<seed>.txt.

Each scenario builds pools from empty storage and then drives the paths that
no mined Monad transaction has used: clear of an exact credit, transferFrom and
burn through an allowance or an operator, approve, donate, the overflow
fallback of getNextSqrtPriceFromAmount0RoundingUp (large exact-input
zeroForOne swaps), and amounts above 2^160. Random amounts are drawn from edge
sets around 2^64, 2^96, 2^128, 2^159..2^161, 2^255 and 2^256-1."""
import random, sys

PM = '188d586ddcf52439676ca21a244753fa19f9ea8e'
A = '00000000000000000000000000000000000a11ce'
B = '0000000000000000000000000000000000000b0b'
C = '000000000000000000000000000000000000c0de'
T1 = '0000000000000000000000000000000000001001'
T2 = '0000000000000000000000000000000000001002'
NATIVE = '0' * 40
SEL = {
    'approve': '426a8493', 'balanceOf': '00fdd58e', 'burn': 'f5298aca', 'clear': '80f0b44c', 'donate': '234266d7',
    'initialize': '6276cbbe', 'isOperator': 'b6363cf2', 'mint': '156e29f6', 'modifyLiquidity': '5a6bcfda',
    'setOperator': '558a7297', 'settle': '11da60b4', 'settleFor': '3dd45adb', 'swap': 'f3cd914c', 'sync': 'a5841194',
    'take': '0b0d9c09', 'transfer': '095bcdb6', 'erc20transfer': 'a9059cbb', 'transferFrom': 'fe99049a', 'unlock': '48c89491',
    'allowance': '598af9e7', 'exttload': 'f135baaa', 'extsload': '1e2eaeaf'}
M256 = (1 << 256) - 1
MIN_SQRT = 4295128739
MAX_SQRT = 1461446703485210103287273052203988822378723970342


def w(x):
    return '%064x' % (x & M256)


def a32(a):
    return '0' * 24 + a


def key(c0, c1, fee, ts):
    return a32(c0) + a32(c1) + w(fee) + w(ts) + a32(NATIVE)


def edge(r, top=256):
    k = r.random()
    if k < 0.25:
        e = r.choice([0, 1, 2, 63, 64, 95, 96, 127, 128, 159, 160, 161, 200, 254, 255, 256])
        e = min(e, top)
        return max(0, (1 << e) + r.choice([-2, -1, 0, 1, 2])) & ((1 << top) - 1 if top < 256 else M256)
    if k < 0.5:
        return r.getrandbits(r.randint(1, top))
    if k < 0.6:
        return (1 << top) - 1
    return r.randint(0, 10 ** r.randint(1, 30))


def call(to, sel, args='', value=0, gas=5_000_000):
    return (to, value, gas, SEL[sel] + args)


def script(steps):
    out = ''
    for to, value, gas, data in steps:
        out += to + w(value) + '%016x' % gas + '%08x' % (len(data) // 2) + data
    return out


def CLOSE(c):
    return ('0' * 36 + 'ffff', 0, 0, c)


def unlock(steps):
    s = script(steps)
    n = len(s) // 2
    pad = (32 - n % 32) % 32
    return SEL['unlock'] + w(0x20) + w(n) + s + '00' * pad


def tx(frm, data, value=0, gas=60_000_000):
    return 'TX %s %s %x %d %s' % (frm, PM, value, gas, data)


def CLEAREXACT(c):
    return ('0' * 36 + 'fffe', 0, 0, c)


def small(r):
    return r.choice([0, 1, 2, r.randint(0, 1000), r.getrandbits(r.randint(1, 100)), r.getrandbits(r.randint(1, 120))])


def amt_any(r):
    return small(r) if r.random() < 0.5 else edge(r)


def scenario(r, idx):
    lines = ['SCEN s%d' % idx]
    users = [A, B, C]
    kind = r.choice(['plain', 'plain', 'fallback', 'fallback', 'edgeprice', 'big1', 'big1'])
    lines[0] += '-' + kind
    first_fb = True
    fee = r.choice([0, 100, 500, 3000, 10000, 999999])
    ts = r.choice([1, 10, 60, 200])
    lo, hi = -(887272 // ts * ts), 887272 // ts * ts
    if kind == 'fallback':
        fee = r.choice([0, 100, 500, 3000])
        if r.random() < 0.6:
            # price just below tick 0 with a position [min, 0] on a wide spacing: the
            # step target is the lowest tick, so an exact input above 2^256 / sqrtP
            # stays below the amount needed to reach it and the overflow fallback runs
            ts = r.choice([16384, 32767])
            lo, hi = -(887272 // ts * ts), 0
            sqrtp = (1 << 96) - (1 << r.randint(40, 70))
            liq = r.randint(1 << 98, 1 << 106)
            lines[0] += 'A'
        else:
            # high price, wide spacing (one bitmap word spans 256 * tickSpacing ticks)
            ts = r.choice([8192, 16384, 32767])
            lo, hi = -(887272 // ts * ts), 887272 // ts * ts
            e = r.randint(120, 159)
            sqrtp = min(r.randint(1 << (e - 1), (1 << e) - 1), MAX_SQRT - 1)
            liq = max(min(r.getrandbits(r.randint(20, 90)) | 1, 1 << 80), 1 << max(1, 196 - e))
    elif kind == 'big1':
        # mirror image: price just above tick 0, position [0, max]; oneForZero exact
        # input above 2^160 takes the mulDiv branch of getNextSqrtPriceFromAmount1RoundingDown
        ts = r.choice([16384, 32767])
        lo, hi = 0, 887272 // ts * ts
        sqrtp = (1 << 96) + (1 << r.randint(40, 70))
        liq = r.randint(1 << 98, 1 << 106)
    elif kind == 'edgeprice':
        sqrtp = r.choice([MIN_SQRT, MIN_SQRT + r.randint(0, 10 ** 6), MAX_SQRT - 1 - r.randint(0, 10 ** 6)])
        liq = r.choice([1, 1000, 10 ** 18, r.getrandbits(r.randint(1, 60))])
    else:
        sqrtp = r.choice([1 << 96, (1 << 96) * r.randint(1, 1000) // r.randint(1, 1000), r.randint(MIN_SQRT, MAX_SQRT - 1)])
        liq = r.choice([1, 1000, 10 ** 18, 10 ** 22, 1 << 80, r.getrandbits(r.randint(1, 90))])
        if r.random() < 0.4:
            c = r.randint(-800000, 800000) // ts * ts
            lo, hi = c - ts * r.randint(1, 50), c + ts * r.randint(1, 50)
    c0, c1 = (NATIVE, T1) if r.random() < 0.5 else (T1, T2)
    k = key(c0, c1, fee, ts)
    u = r.choice(users)
    lines.append(tx(u, SEL['initialize'] + k + w(sqrtp)))
    steps = [call(PM, 'modifyLiquidity', k + w(lo) + w(hi) + w(liq) + w(r.getrandbits(256)) + w(32 * 10) + w(0), gas=10_000_000)]
    for c in (c0, c1):
        if r.random() < 0.6:  # overpay so that an exact credit exists
            amt = r.randint(1, 1 << r.randint(1, 126))
            if c == NATIVE:
                steps.append(call(PM, 'settle', '', value=amt))
            else:
                steps.append(call(PM, 'sync', a32(c)))
                steps.append(call(c, 'erc20transfer', a32(PM) + w(amt)))
                steps.append(call(PM, 'settle'))
    steps.append(CLOSE(c0))
    steps.append(CLOSE(c1))
    # claims for every user so that allowance and operator paths have balances
    for v in users:
        for c in (c0, c1):
            steps.append(call(PM, 'mint', a32(v) + a32(c) + w(r.getrandbits(r.randint(60, 126)))))
    steps += [CLOSE(c0), CLOSE(c1)]
    lines.append(tx(u, unlock(steps)))
    for _ in range(r.randint(3, 10)):
        op = r.random()
        s_, t = r.choice(users), r.choice(users)
        cid = a32(r.choice([c0, c1]))
        if op < 0.25:
            lines.append(tx(s_, SEL['approve'] + a32(t) + cid + w(r.choice([amt_any(r), M256, M256 - 1, 1 << 160, (1 << 160) - 1]))))
        elif op < 0.35:
            lines.append(tx(s_, SEL['setOperator'] + a32(t) + w(r.choice([0, 1, 2, M256]))))
        elif op < 0.75:
            lines.append(tx(t, SEL['transferFrom'] + a32(s_) + a32(r.choice(users)) + cid + w(amt_any(r))))
        elif op < 0.85:
            lines.append(tx(s_, SEL['transfer'] + a32(t) + cid + w(amt_any(r))))
        else:
            lines.append(tx(s_, SEL['allowance'] + a32(s_) + a32(t) + cid))
    for _round in range(r.randint(1, 3)):
        steps = []
        for _ in range(r.randint(3, 10)):
            op = r.random()
            cid = r.choice([c0, c1])
            if op < 0.15:
                steps.append(call(PM, 'burn', a32(r.choice(users)) + a32(cid) + w(amt_any(r))))
            elif op < 0.3:
                steps.append(call(PM, 'donate', k + w(amt_any(r)) + w(amt_any(r)) + w(32 * 8) + w(0), gas=8_000_000))
            elif op < 0.6:
                if kind == 'fallback' and (first_fb or r.random() < 0.5):
                    first_fb = False
                    zf1 = True
                    lo_amt = 2 * (((1 << 256) // sqrtp) + 1) * 1000000 // (1000000 - fee) + 2
                    hi_amt = min((liq << 64) // 2, (1 << 255) - 1)
                    amt = -r.randint(lo_amt, max(lo_amt, hi_amt)) if r.random() < 0.85 else -r.randint(lo_amt, (1 << 255) - 1)
                elif kind == 'big1' and r.random() < 0.6:
                    zf1 = False
                    amt = -r.randint((1 << 160) + 1, 1 << r.randint(161, 166)) if r.random() < 0.7 else r.randint(1, 1 << r.randint(60, 130))
                else:
                    zf1 = r.random() < 0.5
                    amt = amt_any(r)
                    amt = -amt if r.random() < 0.6 else amt
                    if amt >= 1 << 255 or amt < -(1 << 255):
                        amt = amt % (1 << 255)
                lim = MIN_SQRT + 1 if zf1 else MAX_SQRT - 1
                if r.random() < 0.2:
                    lim = r.randint(MIN_SQRT, MAX_SQRT)
                steps.append(call(PM, 'swap', k + w(int(zf1)) + w(amt) + w(lim) + w(32 * 9) + w(0), gas=25_000_000))
            elif op < 0.7:
                steps.append(CLEAREXACT(cid))
            elif op < 0.75:
                steps.append(call(PM, 'clear', a32(cid) + w(amt_any(r))))
            elif op < 0.82:
                steps.append(call(PM, 'take', a32(cid) + a32(r.choice(users)) + w(small(r))))
            elif op < 0.9:
                steps.append(call(PM, 'mint', a32(r.choice(users)) + a32(cid) + w(amt_any(r))))
            else:
                steps.append(call(PM, 'transferFrom', a32(r.choice(users)) + a32(r.choice(users)) + a32(cid) + w(amt_any(r))))
        if r.random() < 0.85:
            steps += [r.choice([CLEAREXACT, CLOSE])(c0), r.choice([CLEAREXACT, CLOSE])(c1), CLOSE(c0), CLOSE(c1)]
        lines.append(tx(r.choice(users), unlock(steps)))
    for s_ in users:
        for t in users:
            lines.append(tx(s_, SEL['allowance'] + a32(s_) + a32(t) + a32(c0)))
            lines.append(tx(s_, SEL['isOperator'] + a32(s_) + a32(t)))
        lines.append(tx(s_, SEL['balanceOf'] + a32(s_) + a32(c1)))
    return lines


def main():
    seed, n = int(sys.argv[1]), int(sys.argv[2])
    r = random.Random(seed)
    code = open(sys.argv[3]).read().strip()
    with open('world.txt', 'w') as f:
        f.write('code %s %s\n' % (PM, code))
        for u in (A, B, C):
            f.write('bal %s %x\n' % (u, 1 << 200))
            for t in (T1, T2):
                f.write('tok %s %s %x\n' % (t, u, 1 << 200))
        f.write('token %s\ntoken %s\n' % (T1, T2))
    with open('scen-%d.txt' % seed, 'w') as f:
        for i in range(n):
            f.write('\n'.join(scenario(r, i)) + '\n')


if __name__ == '__main__':
    main()
