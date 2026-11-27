"""Runs the shipped x86_64 keccak path of tempo v1.19.1 in the cycle 28 x86emu2 model: the
keccak_cache_global compute at 0x416a680 (alloy-primitives 1.7.3 with fixed-cache 0.1.10), the
20, 32 and 64 byte routines 0x19129d0, 0x1912ae0, 0x1912be0, the generic routine 0x1912820, the long-input
entry 0x1915ec0, and keccak-asm's CRYPTOGAMS SHA3_absorb 0x6a0ab80, SHA3_squeeze 0x6a0ac60 and
KeccakF1600 0x6a0a800 that they reach through GOT slots. The x86_64 build is the one that answers
rpc.mainnet.tempo.xyz. Nothing from the release is executed; its disassembly text is interpreted.

usage: python3 -I keccak_x64.py <binary> <x64_kcache.s> <out.json> [fault]
Faults: 'theta' turns the first xor of KeccakF1600's round body into an or; 'bcmp' and 'lenchk' as in
keccak_a64.py (lenchk removes the length byte comparison at 0x416a7a3).
"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from x86emu2 import CPU2, Prog, Stop, rewrite_rip, M64
from evm import keccak

BIN, ASM, OUT = sys.argv[1:4]
FAULT = sys.argv[4] if len(sys.argv) > 4 else 'none'
SEED = 2026112729
fb = open(BIN, 'rb').read()
prog = Prog(rewrite_rip(open(ASM).read()))
K20, K32, K64, KGEN, KCACHE = 0x19129d0, 0x1912ae0, 0x1912be0, 0x1912820, 0x416a680
CACHE_GLOBAL = 0x6cb5cc0
ONCE_STATE = 0x6cb5cf0
BUCKETS = 0x40000000
CAP = 1 << 8
TEXT_LO, TEXT_HI, TEXT_DELTA = 0x189bb00, 0x189bb00 + 0x521d110, 0x1000


class CPU3(CPU2):
    def read(self, a, n):
        if TEXT_LO <= a and a + n <= TEXT_HI and (a not in self.mem):
            return int.from_bytes(self.fb[a - TEXT_DELTA:a - TEXT_DELTA + n], 'little')
        return super().read(a, n)

    def step(self, pc):
        body = self.p.ins.get(pc, '')
        if body.startswith('repz ret'):
            self.visited.add(pc)
            a = self.read(self.r['rsp'], 8); self.r['rsp'] += 8; return a
        if body.startswith('rep movs BYTE PTR'):
            self.visited.add(pc)
            for _ in range(self.r['rcx']):
                self.write(self.r['rdi'], 1, self.read(self.r['rsi'], 1))
                self.r['rdi'] = (self.r['rdi'] + 1) & M64; self.r['rsi'] = (self.r['rsi'] + 1) & M64
            self.r['rcx'] = 0
            return self.p.nxt[pc]
        if body.startswith('lock '):
            saved = body
            self.p.ins[pc] = body[5:].strip()
            try:
                return super().step(pc)
            finally:
                self.p.ins[pc] = saved
        return super().step(pc)

    def i_rol(self, o, pc, n):
        d = self.opnd(o[0]); b = d[2]
        c = self._shcount(self.opnd(o[1]) if len(o) > 1 else ('i', 1, None), b)
        if c == 0: return
        x = self.get(d); r = ((x << c) | (x >> (b - c))) & ((1 << b) - 1)
        self.cf = r & 1; self.of = ((r >> (b - 1)) & 1) ^ self.cf
        self.put(d, r)

    def i_cmpxchg(self, o, pc, n):
        d = self.opnd(o[0]); s = self.opnd(o[1]); b = d[2]
        cur = self.get(d)
        acc = self.r['rax'] & ((1 << b) - 1)
        self._sub(('r', 'rax' if b == 64 else 'eax', b), ('i', cur, None), 0, store=False)
        if acc == cur:
            self.zf = 1; self.put(d, self.get(s, b))
        else:
            self.zf = 0; self.setr('rax' if b == 64 else 'eax', cur)

    def i_pause(self, o, pc, n): pass

    INTERNAL = {0x6c845d8: 0x6a0ab80, 0x6c845e0: 0x6a0ac60}   # R_X86_64_RELATIVE slots to SHA3_absorb, SHA3_squeeze

    def i_call(self, o, pc, n):
        import re as _re
        m = _re.match(r'^QWORD PTR \[0x([0-9a-f]+)\]$', o[0])
        if m and int(m.group(1), 16) in self.INTERNAL:
            self.r['rsp'] -= 8; self.write(self.r['rsp'], 8, n); return self.INTERNAL[int(m.group(1), 16)]
        return super().i_call(o, pc, n)


def ext_memcpy(cpu):
    d, s, n = cpu.r['rdi'], cpu.r['rsi'], cpu.r['rdx']
    data = [cpu.read(s + i, 1) for i in range(n)]
    for i, v in enumerate(data):
        cpu.write(d + i, 1, v)
    cpu.r['rax'] = d


def ext_bcmp(cpu):
    a, b, n = cpu.r['rdi'], cpu.r['rsi'], cpu.r['rdx']
    r = 0
    for i in range(n):
        if cpu.read(a + i, 1) != cpu.read(b + i, 1):
            r = 1; break
    if FAULT == 'bcmp':
        r = 0
    cpu.r['rax'] = r


def ext_init(cpu):
    raise Stop('init path taken')


GOT = {0x6c84570: ext_memcpy, 0x6c84590: ext_bcmp}
EXTERNS = {0x416b5a0: ext_init}
faults = {}
if FAULT == 'theta':
    import re as _re
    # first 'xor' inside KeccakF1600's round body (0x6a0a800 onwards)
    for a in sorted(prog.ins):
        if 0x6a0a800 <= a < 0x6a0aae0 and prog.ins[a].startswith('xor'):
            faults[a] = 'or' + prog.ins[a][3:]; break
elif FAULT == 'lenchk':
    faults[0x416a7a3] = 'nop'
elif FAULT not in ('none', 'bcmp'):
    raise SystemExit('unknown fault')

IN, OUTB = 0x30000000, 0x31000000
state = {}   # persistent memory between calls: the cache buckets and globals
visited = set()
steps = [0]


class MemView:
    def read(self, a, n):
        return int.from_bytes(bytes(state.get(a + i, 0) for i in range(n)), 'little')

    def write(self, a, n, v):
        for i in range(n):
            state[a + i] = (v >> (8 * i)) & 0xff


mem = MemView()
mem.write(CACHE_GLOBAL, 8, BUCKETS)
mem.write(CACHE_GLOBAL + 8, 8, CAP)
mem.write(ONCE_STATE, 4, 0)


def call(fn, data):
    cpu = CPU3(prog, fb, 0x189aab8, externs=EXTERNS, got=GOT, faults=faults)
    cpu.mem = state   # share the cache memory across calls
    for k in [k for k in state if not (BUCKETS <= k < BUCKETS + CAP * 128 or CACHE_GLOBAL <= k < CACHE_GLOBAL + 0x40)]:
        del state[k]
    for i, b in enumerate(data):
        cpu.write(IN + i, 1, b)
    cpu.write(cpu.fs + 0x28, 8, 0x1122334455667788)
    cpu.call(fn, [OUTB, IN, len(data)], maxsteps=20_000_000)
    visited.update(cpu.visited)
    steps[0] += cpu.steps
    return bytes(cpu.read(OUTB + i, 1) for i in range(32))


def bucket_of(data):
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
