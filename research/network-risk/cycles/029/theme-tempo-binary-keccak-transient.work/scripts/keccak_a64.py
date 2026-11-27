"""Runs the shipped aarch64 keccak path of tempo v1.19.1 (alloy-primitives 1.7.3 keccak_cache_global
compute at 0x3b487d4 and the four fixed/variable length Keccak-256 routines it calls) in the cycle 28
a64emu model. Nothing from the release is executed on a CPU; the disassembly text is interpreted.

usage: python3 -I keccak_a64.py <binary> <a64_kcache.s> <out.json> [fault]

Sets:
  direct   each keccak routine called directly (20, 32, 64 byte routines and the generic one)
  battery  the KECCAK256 (offset, length) pairs of tools/opdiff/battery.py over its 0x440 byte memory
  shapes   64 byte inputs of the PoolManager's shapes: CurrencyDelta (target, currency), pools mapping
           (pool id, 6), ticks mapping (tick, keccak(id,6)+4), positions (position key, keccak(id,6)+6),
           ERC6909 balanceOf/allowance nested mappings, and position keys (owner, lower, upper, salt) of 26 bytes... no:
           the position key preimage is abi.encodePacked(owner, tickLower, tickUpper, salt) = 58 bytes
  cache    the cache in front: repeated inputs (hits), inputs that differ only in a late byte or only in length,
           and buckets planted by hand with the right tag but another key, a key that is a prefix, a key of the
           same bytes with another length; a hit must only come back for an identical key
Faults (to show the checks see a wrong result): 'theta' changes one eor of the 64 byte routine into an orr;
'bcmp' makes the cache ignore the bcmp result (any tag and length match is a hit); 'lenchk' skips the
length byte comparison.
"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from a64emu import Prog, Mem, CPU, Stop, M64, VLANE, lanes, pack
from evm import keccak

BIN, ASM, OUT = sys.argv[1:4]
FAULT = sys.argv[4] if len(sys.argv) > 4 else 'none'
SEED = 2026112729
fb = open(BIN, 'rb').read()
prog = Prog([open(ASM).read()])

K20, K32, K64, KGEN, KCACHE = 0x18ead54, 0x18eb104, 0x18eb4c4, 0x18ea188, 0x3b487d4
CACHE_GLOBAL = 0x5e7de40     # (bucket base, capacity) read at 0x3b48900
ONCE_STATE = 0x5e7de70       # ldar w8 at 0x3b4880c; nonzero sends to the init path
BUCKETS = 0x40000000
CAP = 1 << 8                 # model capacity (the release uses 1 << 17; only the masks depend on it)


class CPU2(CPU):
    def i_ld1r(self, o):
        r = o[0].strip('{} ')
        w, n = self._vw(r)
        a, wb, nv = self.addr(o[1:])
        e = self.m.read(a, w // 8)
        self.vset(r, pack([e] * n, w))
        if wb: self.wr(wb, nv)

    def i_stlr(self, o):
        n, vec = self._regsize(o[0]); self._st(o, n, vec)

    def _sh(self, s):
        return int(s.lstrip('#'), 0)

    def i_shl(self, o):
        w, n = self._vw(o[0]); s = self._sh(o[2])
        self.vset(o[0], pack([(x << s) & ((1 << w) - 1) for x in lanes(self.vget(o[1]), w, n)], w))

    def i_usra(self, o):
        w, n = self._vw(o[0]); s = self._sh(o[2])
        d = lanes(self.vget(o[0]), w, n); a = lanes(self.vget(o[1]), w, n)
        self.vset(o[0], pack([(x + (y >> s)) & ((1 << w) - 1) for x, y in zip(d, a)], w))

    def i_fneg(self, o):
        w, n = self._vw(o[0])
        self.vset(o[0], pack([x ^ (1 << (w - 1)) for x in lanes(self.vget(o[1]), w, n)], w))

    def i_zip1(self, o):
        w, n = self._vw(o[0]); a = lanes(self.vget(o[1]), w, n); b = lanes(self.vget(o[2]), w, n)
        out = []
        for i in range(n // 2):
            out += [a[i], b[i]]
        self.vset(o[0], pack(out, w))


def ext_memcpy(cpu):
    d, s, n = cpu.x[0], cpu.x[1], cpu.x[2]
    data = [cpu.m.read(s + i, 1) for i in range(n)]
    for i, v in enumerate(data):
        cpu.m.write(d + i, 1, v)


def ext_bcmp(cpu):
    a, b, n = cpu.x[0], cpu.x[1], cpu.x[2]
    r = 0
    for i in range(n):
        if cpu.m.read(a + i, 1) != cpu.m.read(b + i, 1):
            r = 1; break
    if FAULT == 'bcmp':
        r = 0
    cpu.x[0] = r


def ext_cas8_acq(cpu):
    exp, new, addr = cpu.x[0], cpu.x[1], cpu.x[2]
    old = cpu.m.read(addr, 8)
    if old == exp:
        cpu.m.write(addr, 8, new)
    cpu.x[0] = old


def ext_init(cpu):
    raise Stop('init path taken')


EXTERNS = {0x18855b0: ext_memcpy, 0x1885350: ext_bcmp, 0x5c667e0: ext_cas8_acq, 0x3b48bd4: ext_init}
faults = {}
if FAULT == 'theta':
    # first vector eor of the 64 byte routine after the loads
    faults[0x18eb578] = lambda cpu, mn, ops: ('orr', ops)
elif FAULT == 'lenchk':
    faults[0x3b48948] = lambda cpu, mn, ops: ('nop', [])
elif FAULT not in ('none', 'bcmp'):
    raise SystemExit('unknown fault')

IN, OUTB, SP = 0x30000000, 0x31000000, 0x7ff000000000
mem = Mem(fb, 0, 0x18742d8)
mem.add(IN, 0x2000)
mem.add(OUTB, 0x100)
mem.add(SP - 0x40000, 0x40000)
mem.add(CACHE_GLOBAL & ~0xfff, 0x1000)
mem.add(BUCKETS, CAP * 128)
mem.write(CACHE_GLOBAL, 8, BUCKETS)
mem.write(CACHE_GLOBAL + 8, 8, CAP)
mem.write(ONCE_STATE, 4, 0)
visited = set()
steps = [0]


def call(fn, data):
    for i, b in enumerate(data):
        mem.write(IN + i, 1, b)
    for i in range(32):
        mem.write(OUTB + i, 1, 0)
    cpu = CPU2(prog, mem, externs=EXTERNS, faults=faults)
    cpu.x[31] = SP
    cpu.call(fn, [OUTB, IN, len(data)], maxsteps=20_000_000)
    visited.update(cpu.visited)
    steps[0] += cpu.steps
    return bytes(mem.read(OUTB + i, 1) for i in range(32))


def bucket_of(data):
    """Return (index, tag) of the bucket the shipped code chose, found by looking for the stored key."""
    for i in range(CAP):
        b = BUCKETS + 128 * i
        if mem.read(b + 8, 1) == len(data) and bytes(mem.read(b + 9 + j, 1) for j in range(len(data))) == data:
            return i, mem.read(b, 8)
    return None, None


res = {'fault': FAULT, 'seed': SEED, 'modelCapacity': CAP, 'sets': {}, 'records': [], 'errors': 0}
rnd = random.Random(SEED)


def check(setname, fn, data, expect=None):
    st = res['sets'].setdefault(setname, [0, 0, 0])
    st[0] += 1
    want = keccak(bytes(data)) if expect is None else expect
    try:
        got = call(fn, data)
    except Stop as e:
        st[2] += 1; res['errors'] += 1
        if len(res['records']) < 500:
            res['records'].append({'set': setname, 'fn': hex(fn), 'input': bytes(data).hex(), 'error': str(e)})
        return None
    if got != want:
        st[1] += 1
        if len(res['records']) < 500:
            res['records'].append({'set': setname, 'fn': hex(fn), 'input': bytes(data).hex(), 'model': got.hex(), 'reference': want.hex()})
    return got


def rb(n): return bytes(rnd.getrandbits(8) for _ in range(n))
def w(x): return (x % (1 << 256)).to_bytes(32, 'big')


# 1. direct routines
for _ in range(150):
    check('direct20', K20, rb(20))
    check('direct32', K32, rb(32))
    check('direct64', K64, rb(64))
for n in list(range(1, 300)) + [135, 136, 137, 271, 272, 273, 408, 409, 1023, 1024]:
    check('directGeneric', KGEN, rb(n))
for d in (bytes(64), b'\xff' * 64, bytes(20), b'\xff' * 32, bytes(32)):
    fn = {20: K20, 32: K32, 64: K64}[len(d)]
    check('directEdge', fn, d)

# 2. battery KECCAK pairs through the cache entry (which picks the routine by length)
sys.argv_saved = sys.argv
import battery
for op, a, b, c in battery.vectors():
    if op != 'KECCAK':
        continue
    m = a.to_bytes(32, 'big') + b.to_bytes(32, 'big') + bytes(0x400)
    off, ln = c & 0xff, (c >> 8) & 0x3ff
    if ln == 0:
        continue  # the handler returns the empty-hash constant without calling the routine
    check('battery', KCACHE, m[off:off + ln])
    check('battery-again', KCACHE, m[off:off + ln])  # second call is a cache hit for len <= 87

# 3. PoolManager shapes (64 byte and 58 byte preimages)
A160 = (1 << 160) - 1
addrs = [0, 1, A160, 0x4200000000000000000000000000000000000006, 0x20c0000000000000000000000000000000000000,
         0x20C0000000000000000000000000000000000001, 0xfffffffffffffffffffffffffffffffffffffffe] + [rnd.getrandbits(160) for _ in range(60)]
seen = {}
coll = 0
for t in addrs[:30]:
    for c in addrs[:30]:
        d = w(t) + w(c)   # CurrencyDelta._computeSlot (src/libraries/CurrencyDelta.sol:10-15)
        g = check('currencyDelta', KCACHE, d)
        g2 = check('currencyDelta-hit', KCACHE, d)
        if g is not None:
            if g in seen and seen[g] != d:
                coll += 1
            seen[g] = d
res['currencyDeltaDistinctInputs'] = len(seen)
res['currencyDeltaDigestCollisions'] = coll
for _ in range(400):
    pid = rb(32)
    check('poolsSlot', KCACHE, pid + w(6))
    base = int.from_bytes(keccak(pid + w(6)), 'big')
    tick = rnd.randrange(-887272, 887273)
    check('ticksSlot', KCACHE, w(tick) + w(base + 4))
    check('bitmapSlot', KCACHE, w(tick >> 8) + w(base + 5))
    owner, lo, hi, salt = rnd.getrandbits(160), rnd.randrange(-887272, 0), rnd.randrange(0, 887273), rb(32)
    pk = owner.to_bytes(20, 'big') + (lo % (1 << 24)).to_bytes(3, 'big') + (hi % (1 << 24)).to_bytes(3, 'big') + salt
    check('positionKey58', KCACHE, pk)
    check('positionsSlot', KCACHE, keccak(pk) + w(base + 6))
    o, i = rnd.getrandbits(160), rnd.getrandbits(256)
    check('erc6909Balance', KCACHE, w(o) + w(4))  # outer level shape; slot number not material to the hash path
    check('erc6909BalanceInner', KCACHE, w(i) + keccak(w(o) + w(4)))

# 4. cache logic: near-identical keys and planted buckets
for _ in range(300):
    n = rnd.randrange(1, 88)
    d = bytearray(rb(n))
    check('cacheRepeat', KCACHE, bytes(d))
    d2 = bytearray(d); d2[-1] ^= 1 << rnd.randrange(8)
    check('cacheLastBit', KCACHE, bytes(d2))
    if n > 1:
        check('cacheShorter', KCACHE, bytes(d[:-1]))
    if n < 87:
        check('cacheLonger', KCACHE, bytes(d) + b'\x00')
    check('cacheRepeat2', KCACHE, bytes(d))

planted = {'cases': 0, 'falseHits': 0, 'notFound': 0}
for _ in range(300):
    n = rnd.randrange(2, 88)
    a = rb(n)
    check('plantSeed', KCACHE, a)
    idx, tag = bucket_of(a)
    if idx is None:
        planted['notFound'] += 1
        continue
    b = BUCKETS + 128 * idx
    kind = rnd.choice(('otherKeySameLen', 'shorterPrefix', 'longerExtension'))
    if kind == 'otherKeySameLen':
        k = bytearray(a); k[rnd.randrange(n)] ^= 0x80
        stored_len, stored = n, bytes(k)
    elif kind == 'shorterPrefix':
        stored_len, stored = n - 1, a[:-1]
    else:
        if n == 87:
            continue
        stored_len, stored = n + 1, a + bytes([rnd.getrandbits(8)])
    mem.write(b + 8, 1, stored_len)
    for j in range(87):
        mem.write(b + 9 + j, 1, stored[j] if j < len(stored) else 0)
    poison = bytes([0xee] * 32)
    for j in range(32):
        mem.write(b + 0x60 + j, 1, poison[j])
    mem.write(b, 8, tag)
    probe = a
    planted['cases'] += 1
    g = check('planted-' + kind, KCACHE, probe)
    if g == poison:
        planted['falseHits'] += 1
res['planted'] = planted
res['visitedInstructions'] = len(visited)
res['programInstructions'] = len(prog.ins)
res['steps'] = steps[0]
res['totals'] = {'cases': sum(v[0] for v in res['sets'].values()), 'mismatches': sum(v[1] for v in res['sets'].values()),
                 'errors': res['errors']}
json.dump(res, open(OUT, 'w'), indent=1)
print(OUT, json.dumps(res['totals']), 'planted', planted, 'visited', len(visited), 'of', len(prog.ins))
