"""Inputs for the five exact sites (cycle 17). Writes into runs/:
world-prologue.txt  the deployed PoolManager with bytes 0..46 replaced by an 18-instruction prologue that copies
                    calldata[0x120:] to memory, pushes eight calldata words and jumps to calldata word 0; a
                    JUMPDEST at pc 37 returns the top stack word. The other 23,962 bytes are unchanged.
world-hook.txt      the cycle 16 world plus a hook double at ...ab0088 (BEFORE_SWAP | BEFORE_SWAP_RETURNS_DELTA)
prol-q128.txt       entry at 0x5703 (mulDiv(a, b, 2^128), the copy Position.update calls, MULMOD at pc 22378)
prol-q96.txt        entry at 0x5810 (mulDiv(a, b, 2^96), the copy getAmount1Delta calls, MULMOD at pc 22639)
prol-sar.txt        entry at 0x3c94 (Hooks.beforeSwap parse of the returned delta, SAR at pc 15519), word in memory
prol-shl.txt        entry at 0x40d7 (bytes4(data) mask for data shorter than 4 bytes, SHL at pc 16642)
cdl.txt             extsload(bytes32[]) and exttload(bytes32[]) with edge offsets and lengths (CALLDATALOAD pc 12232)
hook.txt            swaps through the hook double with edge BeforeSwapDelta words (SAR pc 15519)
pm-q96.txt          ordinary initialize, modifyLiquidity and swap calls that reach pc 22639 with prod1 = 1
pm-q128.txt         ordinary donate and modifyLiquidity calls that reach pc 22378 with prod1 >= 1
expect.json         Python results for the prologue inputs"""
import json, os, random, sys
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import v4math as V
W16 = os.path.join(os.path.dirname(__file__), '../../../016/theme-monad-harness-exact.work')
OUT = os.path.join(os.path.dirname(__file__), '../runs'); os.makedirs(OUT, exist_ok=True)
PM = '188d586ddcf52439676ca21a244753fa19f9ea8e'
A = '00000000000000000000000000000000000a11ce'
T1 = '0000000000000000000000000000000000001001'; T2 = '0000000000000000000000000000000000001002'
HOOK = '0000000000000000000000000000000000ab0088'
M256 = (1 << 256) - 1
SEL = {'initialize': '6276cbbe', 'modifyLiquidity': '5a6bcfda', 'swap': 'f3cd914c', 'donate': '234266d7', 'unlock': '48c89491',
       'extsloadN': 'dbd035ff', 'exttloadN': '9bf6645f', 'settle': '11da60b4', 'sync': 'a5841194'}
def w(x): return '%064x' % (x & M256)
def a32(a): return '0' * 24 + a
def key(c0, c1, fee, ts, hooks='0' * 40): return a32(c0) + a32(c1) + w(fee) + w(ts) + a32(hooks)
def call(to, data, value=0, gas=25_000_000): return (to, value, gas, data)
def script(steps): return ''.join(to + w(v) + '%016x' % g + '%08x' % (len(d) // 2) + d for to, v, g, d in steps)
def unlock(steps):
    s = script(steps); n = len(s) // 2
    return SEL['unlock'] + w(0x20) + w(n) + s + '00' * ((32 - n % 32) % 32)
def CLOSE(c): return ('0' * 36 + 'ffff', 0, 0, c)
def tx(frm, to, data, value=0, gas=150_000_000): return 'TX %s %s %x %d %s' % (frm, to, value, gas, data)
code = bytearray.fromhex(open(os.path.join(W16, 'monad-pm-runtime.hex')).read().strip().removeprefix('0x'))
assert len(code) == 24009
# ---- prologue
P = bytes.fromhex('610120' '36' '03' '610120' '5f' '37') + bytes.fromhex('6101003''5') + b''.join(bytes([0x60, off, 0x35]) for off in range(0xe0, 0x1f, -0x20)) \
    + bytes.fromhex('5f3556') + bytes.fromhex('5b5f5260205ff3')
RET = P.index(bytes.fromhex('5b5f5260205ff3'))
assert RET == 38 and len(P) == 45
P = P + b'\x00' * 2
assert 0x5b not in code[:47][:0] and code[47] == 0x80 and code[18] == 0x5b
patched = bytearray(code); patched[:47] = P
world = open(os.path.join(W16, 'world.txt')).read().split('\n')
wl = [l for l in world if l and not l.startswith('code ')]
open(os.path.join(OUT, 'world-prologue.txt'), 'w').write('code %s %s\n' % (PM, patched.hex()) + '\n'.join(wl) + '\n')
# ---- hook double
def asm(items):
    # items: opcode hex strings, ('label', name) or ('push2', name)
    out = bytearray(); labels = {}; fix = []
    for it in items:
        if isinstance(it, tuple) and it[0] == 'label': labels[it[1]] = len(out); out.append(0x5b)
        elif isinstance(it, tuple) and it[0] == 'push2': out.append(0x61); fix.append((len(out), it[1])); out += b'\0\0'
        else: out += bytes.fromhex(it)
    for pos, nm in fix: out[pos:pos + 2] = labels[nm].to_bytes(2, 'big')
    return bytes(out)
hook = asm(['5f35', '60e0', '1c', '80', '6300000001', '14', ('push2', 'SET'), '57', '63575e24b4', '14', ('push2', 'BS'), '57',
            '5f35', '5f52', '6020', '5ff3',
            ('label', 'SET'), '50', '600435', '5f55', '602435', '600155', '604435', '600255', '606435', '600355', '608435', '600455', '00',
            ('label', 'BS'), '600354', '80', '15', ('push2', 'OK'), '57', '600454', '5f52', '6001', '90', '03', '5f', 'fd',
            ('label', 'OK'), '50', '5f54', '5f52', '600154', '602052', '600254', '604052', '6060', '5ff3'])
open(os.path.join(OUT, 'world-hook.txt'), 'w').write('\n'.join(world).rstrip('\n') + '\ncode %s %s\n' % (HOOK, hook.hex()))
r = random.Random(17)
expect = {}
def prol_tx(name, target, words, mem=b''):
    assert len(words) <= 8
    ws = list(words) + [0] * (8 - len(words))
    data = w(target) + ''.join(w(x) for x in ws) + mem.hex()
    return ['SCEN ' + name, tx(A, PM, data, gas=30_000_000)]
def factor_pair(n, lo_b=2, hi_b=10 ** 6):
    if n == (1 << 256) + 1:  # the Fermat number F8 = 1238926361552897 x 93461639715357977769163558199606896584051237541638188580280321
        return 93461639715357977769163558199606896584051237541638188580280321, 1238926361552897
    for b in range(lo_b, hi_b):
        if n % b == 0 and n // b <= M256: return n // b, b
    return None
def muldiv(a, b, d):
    p = a * b
    if (p >> 256) >= d: return None
    return p // d
EDGE128 = [0, 1, 2, (1 << 64) - 1, 1 << 64, (1 << 64) + 1, (1 << 63), (1 << 96) - 1, 1 << 96, (1 << 96) + 1, (1 << 127), (1 << 128) - 1]
def lo_edges(): return EDGE128 + [r.getrandbits(128) for _ in range(4)]
def kvals(N):
    return sorted(set([0, 1, 2, N - 2, N - 1, N, N + 1, N + 2, (1 << 96) - 1, 1 << 96, (1 << 96) + 1, (1 << 128) - 1, 1 << 128, (1 << 128) + 1,
                       (1 << 160) - 1, 1 << 160, (1 << 255), M256 - 1, M256] + [r.getrandbits(256) for _ in range(6)] + [r.getrandbits(100) for _ in range(4)]))
for nm, entry, N in (('q128', 0x5703, 1 << 128), ('q96', 0x5810, 1 << 96)):
    lines = []; ex = {}
    cases = []
    # prod1 = 1, prod0 = k: a * b = 2^256 + k with a small divisor b (both operand orders)
    for k in kvals(N):
        fp = factor_pair((1 << 256) + k)
        if fp: cases += [('p1k%x' % k, fp[0], fp[1]), ('p1k%xs' % k, fp[1], fp[0])]
        # the same product split with b below 2^128 (a liquidity) when such a split exists among small multiples
    # prod1 = 1 with b below 2^128 and a below 2^160 (the shapes a pool can produce), prod0 just below and above N
    for _ in range(60):
        b = r.randint(1 << 96, (1 << 127) - 1)
        a = ((1 << 256) + b - 1) // b + r.choice([0, 1, 2, r.randint(0, 1 << 30)])
        cases.append(('pool%d' % len(cases), a, b))
    # largest prod1 the require allows, and one above
    mx = N - 1
    for a, b in ((M256, N - 1), (M256, N), (M256, N + 1), ((mx << 256 | M256) // M256, M256), (((mx + 1) << 256) // M256 + 1, M256)):
        cases.append(('max%d' % len(cases), a & M256, b & M256))
    # limb edges of the low 128 bits of both operands (the only words the 2^96 and 2^128 arms read), with high words set
    for alo in lo_edges():
        for blo in lo_edges():
            ahi = r.getrandbits(128) | 1 << 127; bhi = 0 if r.random() < 0.7 else r.getrandbits(r.randint(1, 30))
            a = ahi << 128 | alo; b = bhi << 128 | blo
            if b == 0: continue
            cases.append(('lim%d' % len(cases), a, b))
    for cname, a, b in cases:
        # the function at the entry takes [x, y, ret] with x on top; x * y is symmetric, both orders are listed
        lines += prol_tx('%s-%s' % (nm, cname), entry, [a, b, RET])
        ex['%s-%s' % (nm, cname)] = {'a': a, 'b': b, 'N': N, 'mulmod': (a * b) % N, 'prod1': (a * b) >> 256, 'result': muldiv(a, b, N)}
    open(os.path.join(OUT, 'prol-%s.txt' % nm), 'w').write('\n'.join(lines) + '\n'); expect[nm] = ex
# SAR block 0x3c94: stack [s0 = memory pointer, s1 ..], word at s0 + 0x40; the prologue copies calldata[0x120:] to memory 0
lines = []; ex = {}
words = [0, 1, M256, 1 << 255, (1 << 255) - 1, 1 << 128, (1 << 128) - 1, (1 << 127), (1 << 127) - 1, ((1 << 128) - 1) << 128,
         ((1 << 127) - 1) << 128 | (1 << 127), (M256 ^ ((1 << 128) - 1)) | 1, ((1 << 128) - 1) << 128 | ((1 << 127) - 1),
         (1 << 255) | (1 << 127), 1 << 254, (1 << 192), (1 << 64), (1 << 191) | (1 << 63)] + [r.getrandbits(256) for _ in range(40)]
for i, X in enumerate(words):
    for s0 in (0, 0x20):
        mem = bytearray(0x100); mem[s0 + 0x40:s0 + 0x60] = X.to_bytes(32, 'big')
        n = 'sar-%d-%d' % (i, s0)
        lines += prol_tx(n, 0x3c94, [s0, 0, 0, 0, 0, 0, 0, 0], bytes(mem))
        ex[n] = {'X': X, 'sar128': V.ref_sar(128, X) if hasattr(V, 'ref_sar') else None}
open(os.path.join(OUT, 'prol-sar.txt'), 'w').write('\n'.join(lines) + '\n'); expect['sar'] = ex
# SHL block 0x40d7: stack [s0 = length, s1, s2 ..]; SHL(3, 4 - s0)
lines = []; ex = {}
for i, s0 in enumerate([0, 1, 2, 3, 4, 5, 31, 32, 33, 1 << 64, (1 << 253) - 1, 1 << 253, (1 << 253) + 4, 1 << 255, M256, M256 - 1, M256 - 3] + [r.getrandbits(256) for _ in range(30)]):
    n = 'shl-%d' % i
    lines += prol_tx(n, 0x40d7, [s0, 0, 0, 0, 0, 0, 0, 0])
    v = (4 - s0) & M256
    ex[n] = {'s0': s0, 'value': v, 'shl3': (v << 3) & M256}
open(os.path.join(OUT, 'prol-shl.txt'), 'w').write('\n'.join(lines) + '\n'); expect['shl'] = ex
json.dump(expect, open(os.path.join(OUT, 'expect.json'), 'w'))
# ---- CALLDATALOAD 12232: extsload(bytes32[]) / exttload(bytes32[]) with the offset word anywhere
lines = []; n = 0
for sel in (SEL['extsloadN'], SEL['exttloadN']):
    for off in [0x20, 0x21, 0x3f, 0x40, 0x41, 0x5f, 0x60, 0x7f, 0x80, 0x100, 0x1ff, 0x1000, 0x10001, 0x3ffff]:
        for ln in [0, 1, 2, 3, 31, 32, 33, 64, 1 << 32, (1 << 64) - 1, 1 << 64, 1 << 255, M256]:
            for tail in (0, 1, 31):
                body = bytearray(max(off + 32, 64) + 32 * (min(ln, 40) if ln < 1 << 32 else 0) + tail)
                body[0:32] = off.to_bytes(32, 'big')
                body[off:off + 32] = ln.to_bytes(32, 'big')
                for j in range(min(ln, 40) if ln < 1 << 32 else 0):
                    body[off + 32 + 32 * j:off + 64 + 32 * j] = r.choice([0, 1, 2, r.getrandbits(256)]).to_bytes(32, 'big')
                lines += ['SCEN cdl-%d' % n, tx(A, PM, sel + bytes(body).hex(), gas=30_000_000)]; n += 1
    # the length word ending exactly at the end of calldata, and one byte short of it
    for off in range(0x20, 0x60):
        for cut in (0, 1):
            body = bytearray(off + 32 - cut); body[0:32] = off.to_bytes(32, 'big')
            if off + 32 - cut <= len(body): pass
            body[off:off + 32 - cut] = (0).to_bytes(32, 'big')[:32 - cut]
            lines += ['SCEN cdl-%d' % n, tx(A, PM, sel + bytes(body).hex(), gas=30_000_000)]; n += 1
open(os.path.join(OUT, 'cdl.txt'), 'w').write('\n'.join(lines) + '\n')
# ---- hook swaps (SAR 15519 in the PoolManager's own call path)
lines = []
specs = [0, 1, -1, 2, -2, (1 << 127) - 1, -(1 << 127), -(1 << 127) + 1, 1 << 64, -(1 << 64), 12345, -12345]
unspecs = [0, 1, -1, (1 << 127) - 1, -(1 << 127), -(1 << 127) + 1, 1 << 100, -(1 << 100), 777]
def i128(x): return x & ((1 << 128) - 1)
idx = 0
for zf in (True, False):
    for amt in [-1, 1, -(1 << 127), -((1 << 127) - 1), (1 << 127) - 1, -(10 ** 18), 10 ** 18, -(1 << 100), 1 << 100]:
        for s in specs:
            for u in r.sample(unspecs, 3):
                k = key(T1, T2, 3000, 60, HOOK)
                ts = 60; lo, hi = -(887272 // ts * ts), 887272 // ts * ts
                d = (i128(s) << 128) | i128(u)
                name = 'hk%d' % idx; idx += 1
                lines.append('SCEN ' + name)
                lines.append(tx(A, HOOK, '00000001' + w(0x575e24b4 << 224) + w(d) + w(0) + w(0) + w(0)))
                lines.append(tx(A, PM, SEL['initialize'] + k + w(1 << 96)))
                liq = r.choice([10 ** 18, 1 << 100, (1 << 107)])
                steps = [call(PM, SEL['modifyLiquidity'] + k + w(lo) + w(hi) + w(liq) + w(0) + w(32 * 10) + w(0))]
                lim = V.MIN_SQRT_PRICE + 1 if zf else V.MAX_SQRT_PRICE - 1
                steps.append(call(PM, SEL['swap'] + k + w(int(zf)) + w(amt) + w(lim) + w(32 * 9) + w(0)))
                lines.append(tx(A, PM, unlock(steps)))
    # a reverting hook (revert data of 0 to 4 bytes): the bytes4(data) of the HookCallFailed wrapper uses the call data
for ln in range(0, 6):
    k = key(T1, T2, 500, 10, HOOK)
    lines += ['SCEN hkrev%d' % ln, tx(A, HOOK, '00000001' + w(0) + w(0) + w(0) + w(ln + 1) + w(0xdeadbeef << 224)),
              tx(A, PM, SEL['initialize'] + k + w(1 << 96)),
              tx(A, PM, unlock([call(PM, SEL['modifyLiquidity'] + k + w(-887270) + w(887270) + w(10 ** 18) + w(0) + w(32 * 10) + w(0)),
                                call(PM, SEL['swap'] + k + w(1) + w(-1000) + w(V.MIN_SQRT_PRICE + 1) + w(32 * 9) + w(0))]))]
open(os.path.join(OUT, 'hook.txt'), 'w').write('\n'.join(lines) + '\n')
# ---- ordinary calls reaching pc 22639 with prod1 = 1 (getAmount1Delta inside SwapMath and modifyLiquidity)
lines = []; pmq = {}
ts = 32767
for i in range(80):
    lo = r.choice([5, 8, 10, 13]) * ts; hi = 27 * ts
    sa = V.get_sqrt_price_at_tick(lo); sb = V.get_sqrt_price_at_tick(hi)
    # liquidity L and price limit sa + diff with 2^256 <= L * diff < 2^257
    Lmax = ((1 << 128) - 1) // (2 * (887272 // ts) + 1)
    for _ in range(100):
        L = r.randint(1 << 96, Lmax)
        diff = ((1 << 256) + L - 1) // L + r.choice([0, 1, r.randint(0, 1 << 20), r.randint(0, 1 << 60)])
        if sa + diff < sb and L * diff < 1 << 257: break
    k = key(T1, T2, r.choice([0, 500, 3000]), ts)
    start = sa - r.randint(1, 1 << 40)
    name = 'q96-%d' % i
    steps = [call(PM, SEL['modifyLiquidity'] + k + w(lo) + w(hi) + w(L) + w(0) + w(32 * 10) + w(0))]
    kind = i % 4
    if kind == 0: amt = -r.randint(1, 10 ** 24)            # exact input, any size: compares against amountIn >= 2^160
    elif kind == 1: amt = -r.randint(1 << 160, 1 << 200)    # exact input above 2^160
    elif kind == 2: amt = V.amount0_delta(sa, sa + diff, L, False) if hasattr(V, 'amount0_delta') else 10 ** 20  # exact output of the range's token0
    else: amt = r.randint(1, 10 ** 20)
    if isinstance(amt, tuple): amt = amt[0]
    steps.append(call(PM, SEL['swap'] + k + w(0) + w(amt) + w(sa + diff) + w(32 * 9) + w(0)))
    steps.append(CLOSE(T1)); steps.append(CLOSE(T2))
    # an LP adding the same range below the current price: getAmount1Delta(sa, sb, L) in modifyLiquidity
    steps.append(call(PM, SEL['modifyLiquidity'] + k + w(lo) + w(hi - ts) + w(L) + w(1) + w(32 * 10) + w(0)))
    lines += ['SCEN ' + name, tx(A, PM, SEL['initialize'] + k + w(start)), tx(A, PM, unlock(steps))]
    pmq[name] = {'L': L, 'diff': diff, 'prod1': (L * diff) >> 256, 'prod0': (L * diff) & M256}
open(os.path.join(OUT, 'pm-q96.txt'), 'w').write('\n'.join(lines) + '\n')
json.dump(pmq, open(os.path.join(OUT, 'pm-q96.json'), 'w'))
# ---- ordinary calls reaching pc 22378 with prod1 >= 1: donations in one unlock, then a poke of the position
lines = []
for i in range(30):
    ts = r.choice([1, 60, 200]); lo, hi = -(887272 // ts * ts), 887272 // ts * ts
    k = key(T1, T2, 3000, ts)
    L = r.choice([1, 2, 3, 1000, r.randint(2, 1 << 40)])
    steps = [call(PM, SEL['modifyLiquidity'] + k + w(lo) + w(hi) + w(L) + w(0) + w(32 * 10) + w(0))]
    nd = r.randint(1, 4)
    for _ in range(nd):
        steps.append(call(PM, SEL['donate'] + k + w(r.choice([(1 << 127) - 1, r.getrandbits(126)])) + w(r.choice([0, (1 << 127) - 1, r.getrandbits(120)])) + w(32 * 8) + w(0)))
    steps.append(call(PM, SEL['modifyLiquidity'] + k + w(lo) + w(hi) + w(0) + w(0) + w(32 * 10) + w(0)))
    steps.append(call(PM, SEL['modifyLiquidity'] + k + w(lo) + w(hi) + w(-L) + w(0) + w(32 * 10) + w(0)))
    lines += ['SCEN q128-%d' % i, tx(A, PM, SEL['initialize'] + k + w(1 << 96)), tx(A, PM, unlock(steps))]
open(os.path.join(OUT, 'pm-q128.txt'), 'w').write('\n'.join(lines) + '\n')
print('ok', {f: sum(1 for l in open(os.path.join(OUT, f)) if l.startswith('SCEN')) for f in os.listdir(OUT) if f.endswith('.txt') and not f.startswith('world') and not f.startswith('s30')})
