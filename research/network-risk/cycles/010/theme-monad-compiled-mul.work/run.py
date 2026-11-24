"""Runs the transcriptions of muljit.py against Python integers.

Usage: python3 -I run.py <workdir> <path> <cases> <seed>
paths: mulmod96, mulmod128, mulmodall (exp 1..255, both operands variable or one literal),
       tickconst (the 19 TickMath multipliers, the first-step select, 255738958999603826347141, 3),
       mullit (every literal of the form mul_optimized inlines, random), runtimemul, mul192,
       muldiv (FullMath.mulDiv and mulDivRoundingUp composed from compiled pieces), exp
Writes <workdir>/run-<path>-<seed>.json with counts and the first failures.
"""
import sys, os, json, random, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import muljit as J

U = 1 << 256; M = U - 1

_SITES = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sites.json')))['sites']
# every literal that sites.py found as an operand of MUL in the runtime bytecode, in pc order
SITE_MUL_LITERALS = []
for _s in _SITES:
    if _s['op'] == 'MUL':
        for _v in _s['operandsTopFirst']:
            if _v is not None and int(_v, 16) not in SITE_MUL_LITERALS: SITE_MUL_LITERALS.append(int(_v, 16))


def operand(rng, kind=None):
    k = kind if kind is not None else rng.randrange(12)
    if k == 0: return rng.getrandbits(256)
    if k == 1: return M
    if k == 2: return sum((rng.getrandbits(64) | 1 | (1 << 63)) << (64 * i) for i in range(4))  # all limbs set
    if k == 3: return rng.getrandbits(256) & ~((1 << 64) - 1)          # low limb zero
    if k == 4: return rng.getrandbits(256) & ~((1 << 128) - 1)         # two low limbs zero
    if k == 5: return rng.getrandbits(rng.randrange(1, 129))            # below 2^128
    if k == 6: return (1 << 128) + rng.getrandbits(128) | (rng.getrandbits(128) << 128)  # above 2^128
    if k == 7: return (U - rng.getrandbits(rng.randrange(1, 200))) % U  # negative small
    if k == 8: return 1 << rng.randrange(256)
    if k == 9: return ((1 << rng.randrange(1, 257)) - 1)
    if k == 10:  # limbs that are each 0, 1, 2^63, 2^64-1, or random
        ch = [0, 1, 1 << 63, (1 << 64) - 1, (1 << 32) - 1, 1 << 32, (1 << 31)]
        return sum((rng.choice(ch) if rng.random() < 0.7 else rng.getrandbits(64)) << (64 * i) for i in range(4))
    return rng.getrandbits(rng.randrange(1, 257))


def scenario(rng, right_kind):
    """Choose where the operands live. right_kind: 'lit', 'var'."""
    order = rng.sample([0, 1, 2], 3)
    occ = {}
    lk = rng.choice(['reg', 'reg', 'mem', 'avx'])
    left = None
    same = right_kind == 'var' and rng.random() < 0.15
    if lk == 'reg':
        ls = rng.randrange(3); occ[ls] = 'left'; left = ('reg', ls)
    elif lk == 'mem':
        left = ('mem', 0x1000)
    else:
        left = ('avx', None)
    right = None
    if right_kind == 'var':
        if same:
            right = left if left[0] != 'avx' else ('mem', 0x1000)
            if left[0] == 'avx': left = ('mem', 0x1000)
        else:
            rk = rng.choice(['reg', 'mem'])
            if rk == 'reg':
                free = [s for s in range(3) if s not in occ]
                rs = rng.choice(free); occ[rs] = 'right'; right = ('reg', rs)
            else:
                right = ('mem', 0x2000)
    for s in range(3):
        if s not in occ and rng.random() < 0.4: occ[s] = 'live'
    return order, occ, left, right, same


def run_mwbs(rng, bit_size, a, b_lit, b, stats, fails, label, right_kind):
    """One call of mul_with_bit_size with a random register picture. b_lit: literal value or None."""
    cpu = J.CPU(); em = J.Emitter(cpu)
    order, occ, left, right, same = scenario(rng, right_kind)
    if right_kind == 'var' and right[0] == 'reg' and -(-bit_size // 64) > 2:
        right = ('mem', 0x2000); occ = {k: v for k, v in occ.items() if v != 'right'}
    # place values
    if left[0] == 'reg': J.put_set(cpu, left[1], a)
    elif left[0] == 'mem': J.put_mem(cpu, left[1], a)
    else: left = ('avx', a)
    if right_kind == 'var':
        if same:
            b = a
        elif right[0] == 'reg': J.put_set(cpu, right[1], b)
        else: J.put_mem(cpu, right[1], b)
    before = {s: J.read_set(cpu, s) for s in range(3) if occ.get(s) in ('live', 'right', 'left')}
    rbx, rbp = cpu.reg['rbx'], cpu.reg['rbp']
    mem_before = dict(cpu.mem)
    al = J.Alloc(occ, order)
    try:
        if right_kind == 'lit':
            dst = J.mul_with_bit_size(cpu, em, al, bit_size, left, b_lit, set())
        else:
            dst = J.mul_with_bit_size(cpu, em, al, bit_size, left, right, {right[1]} if right[0] == 'reg' else set())
    except AssertionError as e:
        stats['assert'] = stats.get('assert', 0) + 1
        if len(fails) < 20: fails.append({'label': label, 'assert': str(e), 'a': hex(a), 'b': hex(b)})
        return
    want = (a * (b if right_kind == 'var' else b_lit)) % (1 << bit_size)
    got = 0 if isinstance(dst, tuple) else J.read_set(cpu, dst)
    ok = got == want
    side = []
    for s, v in before.items():
        if s in al.spilled: continue
        if J.read_set(cpu, s) != v: side.append(s)
    if cpu.reg['rbx'] != rbx or cpu.reg['rbp'] != rbp or cpu.stk: side.append('rbx/rbp/stack')
    for k, v in mem_before.items():
        if cpu.mem.get(k) != v: side.append('mem%x' % k)
    stats['n'] = stats.get('n', 0) + 1
    if not ok or side:
        stats['fail'] = stats.get('fail', 0) + 1
        if len(fails) < 20:
            fails.append({'label': label, 'bits': bit_size, 'a': hex(a), 'b': hex(b if right_kind == 'var' else b_lit),
                          'want': hex(want), 'got': hex(got), 'clobbered': [str(x) for x in side],
                          'left': str(left[0]), 'right': str(right), 'occ': {str(k): v for k, v in occ.items()}, 'order': order})


def mul_mod2(rng, exp, a, b, b_is_lit, stats, fails, label):
    """emitter.cpp 7991-8084 dispatch, then the chosen path."""
    mask = (1 << exp) - 1
    last_ix = (exp - 1) >> 6
    if b_is_lit:
        bm = b & mask
        has_zero = any(J.limbs(bm)[i] == 0 for i in range(last_ix + 1))
        if last_ix <= 1 or has_zero:
            stats['inline_lit'] = stats.get('inline_lit', 0) + 1
            return run_mwbs(rng, exp, a, bm, b, stats, fails, label + '/lit', 'lit')
        path = 'runtime'
    elif last_ix <= 1:
        stats['inline_var'] = stats.get('inline_var', 0) + 1
        return run_mwbs(rng, exp, a, None, b, stats, fails, label + '/var', 'var')
    else:
        path = 'runtime'
    # runtime path: result slot = a slot (rdi == rsi, as the runtime call allows)
    cpu = J.CPU(); J.put_mem(cpu, 0x3000, a); J.put_mem(cpu, 0x4000, b)
    if exp <= 192: J.runtime_mul_192(cpu, 0x5000, 0x3000, 0x4000)
    else: J.runtime_mul(cpu, 0x5000, 0x3000, 0x4000)
    res = J.Mem(0x5000 + last_ix * 8)
    if exp & 63:
        lm = J.limbs(mask)[last_ix]
        if lm.bit_length() < 32: cpu.and_imm(res, lm)
        else: cpu.mov('rax', lm); cpu.mem[res.addr] &= cpu.reg['rax']
    if last_ix < 3:
        assert last_ix == 2
        cpu.mov(res.add(8), 0)
    got = J.read_mem(cpu, 0x5000); want = (a * b) & mask
    stats['n'] = stats.get('n', 0) + 1; stats['runtime'] = stats.get('runtime', 0) + 1
    if got != want:
        stats['fail'] = stats.get('fail', 0) + 1
        if len(fails) < 20: fails.append({'label': label + '/rt', 'exp': exp, 'a': hex(a), 'b': hex(b), 'got': hex(got), 'want': hex(want)})


def mul_optimized(rng, a_lit, b, stats, fails, label):
    """emitter.cpp 6983-7043 with the literal a and variable b."""
    if a_lit == 0: stats['n'] = stats.get('n', 0) + 1; return
    a_shift = a_lit
    if J.limbs(a_lit)[3] >> 63: a_shift = (-a_lit) % U
    if J.popcount(a_shift) == 1:
        stats['shiftpath'] = stats.get('shiftpath', 0) + 1
        k = a_shift.bit_length() - 1
        x = (b << k) % U
        if J.limbs(a_shift)[3] != J.limbs(a_lit)[3]: x = (-x) % U
        stats['n'] = stats.get('n', 0) + 1
        if x != (a_lit * b) % U:
            stats['fail'] = stats.get('fail', 0) + 1
            if len(fails) < 20: fails.append({'label': label + '/shift', 'a': hex(a_lit), 'b': hex(b)})
        return
    if any(l == 0 for l in J.limbs(a_lit)):
        stats['inline'] = stats.get('inline', 0) + 1
        return run_mwbs(rng, 256, b, a_lit, a_lit, stats, fails, label + '/inline', 'lit')
    stats['runtime'] = stats.get('runtime', 0) + 1
    rt_mul(rng, b, a_lit, stats, fails, label + '/rt')


def rt_mul(rng, a, b, stats, fails, label, same_ok=True):
    cpu = J.CPU(); alias = rng.randrange(4 if same_ok else 3)
    pa, pb, pr = 0x3000, 0x4000, 0x5000
    if alias == 1: pr = pa
    elif alias == 2: pr = pb
    elif alias == 3: pb = pa; b = a
    J.put_mem(cpu, pa, a);
    if pb != pa: J.put_mem(cpu, pb, b)
    r12, r13 = cpu.reg['r12'], cpu.reg['r13']
    J.runtime_mul(cpu, pr, pa, pb)
    got = J.read_mem(cpu, pr); want = (a * b) % U
    stats['n'] = stats.get('n', 0) + 1
    if got != want or cpu.reg['r12'] != r12 or cpu.reg['r13'] != r13 or cpu.stk:
        stats['fail'] = stats.get('fail', 0) + 1
        if len(fails) < 20: fails.append({'label': label, 'alias': alias, 'a': hex(a), 'b': hex(b), 'got': hex(got), 'want': hex(want)})
    return got


def muldiv_compiled(rng, a, b, d, roundup, stats):
    """FullMath.mulDiv (src/libraries/FullMath.sol:14-102) with every MUL and MULMOD taken
    through the compiled path it takes in this bytecode: a*b, prod1*twos and the inverse
    products through monad_vm_runtime_mul, 3*denominator through mul_with_bit_size, the
    mulmod by not(0) and by a variable denominator through the shared library (Python),
    a power of two denominator through mul_mod2."""
    def mul(x, y):
        st = {}; fl = []
        r = rt_mul(rng, x, y, st, fl, 'x', same_ok=(x == y))
        if fl: stats.setdefault('mfail', []).append(fl[0])
        return r
    def mulmod(x, y, m):
        if m and m & (m - 1) == 0 and m > 1:
            st = {}; fl = []
            e = m.bit_length() - 1
            # reproduce the value with mul_mod2; result checked inside, failure recorded
            mul_mod2(rng, e, x, y, False, st, fl, 'muldiv')
            if fl: stats.setdefault('mfail', []).append(fl[0])
        return (x * y) % m if m else 0
    prod0 = mul(a, b)
    mm = (a * b) % M
    prod1 = (mm - prod0 - (1 if mm < prod0 else 0)) % U
    if not d > prod1: return None
    if prod1 == 0:
        r = prod0 // d
    else:
        rem = mulmod(a, b, d)
        prod1 = (prod1 - (1 if rem > prod0 else 0)) % U
        prod0 = (prod0 - rem) % U
        twos = ((-d) % U) & d
        d2 = d // twos
        prod0 = prod0 // twos
        twos = ((((-twos) % U) // twos) + 1) % U
        prod0 |= mul(prod1, twos)
        st = {}; fl = []
        run_mwbs(rng, 256, d2, 3, 3, st, fl, 'muldiv3', 'lit')
        if fl: stats.setdefault('mfail', []).append(fl[0])
        inv = ((3 * d2) % U) ^ 2
        for _ in range(6):
            inv = mul(inv, (2 - mul(d2, inv)) % U)
        r = mul(prod0, inv)
    if roundup and mulmod(a, b, d) != 0:
        r += 1
        if r >= U: return None
    return r


def main():
    wd, path, n, seed = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    rng = random.Random(seed); random.seed(seed + 1)
    stats = {}; fails = []; t0 = time.time()
    for i in range(n):
        if path in ('mulmod96', 'mulmod128'):
            e = 96 if path == 'mulmod96' else 128
            a = operand(rng); b = operand(rng)
            if i % 4 == 0:  # one operand below 2^128, the other above
                a = operand(rng, 5); b = operand(rng, 6)
                if rng.random() < 0.5: a, b = b, a
            mul_mod2(rng, e, a, b, False, stats, fails, path)
        elif path == 'mulmodall':
            e = rng.randrange(1, 256)
            a = operand(rng); b = operand(rng)
            mul_mod2(rng, e, a, b, rng.random() < 0.5, stats, fails, 'e%d' % e)
        elif path == 'tickconst':
            c = SITE_MUL_LITERALS[i % len(SITE_MUL_LITERALS)]
            b = operand(rng)
            if i % 3 == 0:
                b = rng.getrandbits(rng.randrange(1, 257))
            mul_optimized(rng, c, b, stats, fails, hex(c)[:12])
        elif path == 'mullit':
            c = operand(rng)
            ls = J.limbs(c)
            if rng.random() < 0.7:  # force a zero limb so that the inline path is taken
                z = rng.randrange(4); ls[z] = 0; c = J.join(ls)
            mul_optimized(rng, c, operand(rng), stats, fails, 'lit')
        elif path == 'runtimemul':
            rt_mul(rng, operand(rng), operand(rng), stats, fails, 'rt')
        elif path == 'mul192':
            a = operand(rng); b = operand(rng)
            cpu = J.CPU(); J.put_mem(cpu, 0x3000, a); J.put_mem(cpu, 0x4000, b)
            pr = rng.choice([0x5000, 0x3000, 0x4000])
            J.runtime_mul_192(cpu, pr, 0x3000, 0x4000)
            got = J.read_mem(cpu, pr) & ((1 << 192) - 1); want = (a * b) % (1 << 192)
            stats['n'] = stats.get('n', 0) + 1
            if got != want:
                stats['fail'] = stats.get('fail', 0) + 1
                if len(fails) < 20: fails.append({'a': hex(a), 'b': hex(b), 'pr': pr})
        elif path == 'muldiv':
            k = rng.randrange(6)
            if k == 0: d = 1 << 128
            elif k == 1: d = 1 << 96
            elif k == 2: d = 10 ** 6
            elif k == 3: d = 10 ** 6 - rng.randrange(1, 10 ** 6)
            else: d = operand(rng) or 1
            a = operand(rng); b = operand(rng)
            if rng.random() < 0.5:  # make the product need more than 256 bits and the quotient fit
                a = rng.getrandbits(256) | (1 << 200); b = rng.getrandbits(rng.randrange(1, 257))
            ru = rng.random() < 0.5
            got = muldiv_compiled(rng, a, b, d, ru, stats)
            want = None
            if d and (a * b) // d < U:
                want = (a * b) // d
                if ru and (a * b) % d:
                    want += 1
                    if want >= U: want = None
            stats['n'] = stats.get('n', 0) + 1
            stats['wide'] = stats.get('wide', 0) + int((a * b) >= U and want is not None)
            if got != want:
                stats['fail'] = stats.get('fail', 0) + 1
                if len(fails) < 20: fails.append({'a': hex(a), 'b': hex(b), 'd': hex(d), 'got': str(got), 'want': str(want)})
        elif path == 'exp':
            k = rng.randrange(2, 256); base = 1 << k
            ls = J.limbs(operand(rng))
            if rng.random() < 0.8: ls[1:] = [0, 0, 0]
            if rng.random() < 0.5: ls[0] = rng.getrandbits(rng.randrange(1, 64))
            n_ = J.join(ls)
            gp0 = ls[0]; rax = gp0
            if J.popcount(k) == 1:
                gp0 = (gp0 << (k.bit_length() - 1)) & J.M64
                if rax & 0xFFFFFFFF80000000: gp0 = rax
            else:
                s = (gp0 - (1 << 64)) if gp0 >> 63 else gp0
                p = s * k
                ovf = not (-(1 << 63) <= p < (1 << 63))
                gp0 = rax if ovf else p & J.M64
            sh = J.join([gp0] + ls[1:])
            got = (1 << sh) % U if sh < 256 else 0
            want = pow(base, n_, U)
            stats['n'] = stats.get('n', 0) + 1
            if got != want:
                stats['fail'] = stats.get('fail', 0) + 1
                if len(fails) < 20: fails.append({'k': k, 'n': hex(n_), 'got': hex(got), 'want': hex(want)})
    stats['seconds'] = round(time.time() - t0, 1)
    json.dump({'path': path, 'seed': seed, 'stats': stats, 'failures': fails},
              open(os.path.join(wd, 'run-%s-%d.json' % (path, seed)), 'w'), indent=1)
    print(path, seed, json.dumps(stats), len(fails))


if __name__ == '__main__':
    main()
