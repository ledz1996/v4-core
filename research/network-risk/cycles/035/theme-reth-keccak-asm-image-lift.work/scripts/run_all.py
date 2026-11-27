"""Task 2 and Task 4 driver: runs the X Layer image's KECCAK256 path in the model (xlmodel.py) and compares every
result with the pure Python Keccak-256 of tools/opdiff/evm.py (the one pyevm.py imports).
usage: python3 -I run_all.py <scriptsdir> <binary> <asm> <out.json> [fault] [quick]
Seed 2026112735. Every mismatch record is saved in full (no cap)."""
import json, random, sys, time
sys.path.insert(0, sys.argv[1])
from xlmodel import *

BIN, ASM, OUT = sys.argv[2:5]
FAULT = sys.argv[5] if len(sys.argv) > 5 else 'none'
QUICK = len(sys.argv) > 6 and sys.argv[6] == 'quick'
RSEED = 2026112735
rnd = random.Random(RSEED)
m = Model(BIN, ASM, FAULT)
IN, OUTB = 0x30000000, 0x31000000
# handler fixture
INTERP, CTX, GASP, SHMEM, STACK, MEMBUF = 0x40000000, 0x41000000, 0x42000000, 0x43000000, 0x44000000, 0x50000000
res = {'model': NAME, 'fault': FAULT, 'seed': RSEED, 'binary': BIN, 'sets': {}, 'records': [], 'errors': 0}


def rec(setname, ok, err=None, **kw):
    st = res['sets'].setdefault(setname, [0, 0, 0])
    st[0] += 1
    if err is not None:
        st[2] += 1; res['errors'] += 1; kw['error'] = err; kw['set'] = setname; res['records'].append(kw)
    elif not ok:
        st[1] += 1; kw['set'] = setname; res['records'].append(kw)


def direct(setname, fn, data):
    m.wr(IN, len(data), int.from_bytes(data, 'little'))
    try:
        m.run(fn, [OUTB, IN, len(data)])
    except Stop as e:
        rec(setname, False, str(e), fn=hex(fn), input=data.hex()); return None
    got = m.rd(OUTB, 32).to_bytes(32, 'little')
    want = keccak(data)
    rec(setname, got == want, fn=hex(fn), input=data.hex(), model=got.hex(), reference=want.hex())
    return got


def handler(setname, data, off, fn=HANDLER):
    """KECCAK256 opcode with stack [.., size, offset] and EVM memory holding data at offset."""
    ctxoff = HFIX['ctx'][fn]
    mem_ctx = 0x40   # a non-zero memory context offset of the call frame inside the shared buffer
    m.wr(INTERP + 0x38, 8, 2); m.wr(INTERP + 0x30, 8, STACK)
    m.wr(STACK, 32, len(data)); m.wr(STACK + 32, 32, off)
    m.wr(INTERP + 0x190, 8, 10 ** 9); m.wr(INTERP + 0x178, 8, 1 << 20)
    m.wr(INTERP + 0x18, 8, mem_ctx); m.wr(INTERP + 0x10, 8, SHMEM)
    m.wr(SHMEM + 0x10, 8, 0); m.wr(SHMEM + 0x20, 8, MEMBUF)
    m.wr(CTX + ctxoff, 8, GASP); m.wr(GASP + HFIX['wordgas'], 8, 6)
    if HFIX['limit'] is not None: m.wr(INTERP + HFIX['limit'], 8, 1 << 40)
    # garbage around the input so that a read outside [off, off+len) changes the hash
    base = MEMBUF + mem_ctx + off
    m.wr(base - 40, 40, rnd.getrandbits(320)); m.wr(base + len(data), 40, rnd.getrandbits(320))
    if data: m.wr(base, len(data), int.from_bytes(data, 'little'))
    try:
        c = m.run(fn, [INTERP, CTX])
    except Stop as e:
        rec(setname, False, str(e), fn=hex(fn), input=data.hex(), offset=off); return None
    rax = c.r['rax'] & 0xff
    w = m.rd(STACK, 32)
    got = w.to_bytes(32, 'big')
    want = keccak(data)
    ok = (rax == 0 or not HFIX.get('status', True)) and got == want and m.rd(INTERP + 0x38, 8) == 1 and m.rd(SHMEM + 0x10, 8) == 0 \
        and m.rd(INTERP + 0x190, 8) == 10 ** 9 - 6 * ((len(data) + 31) // 32)
    rec(setname, ok, fn=hex(fn), input=data.hex(), offset=off, model=got.hex(), reference=want.hex(), status=rax)
    return got


def rb(n): return bytes(rnd.getrandbits(8) for _ in range(n))
def w(x): return (x % (1 << 256)).to_bytes(32, 'big')


t0 = time.time()
# 1. every length 0..1100 through the cache entry (picks cached, uncached or empty path), then a second call
lens = range(0, 1101) if not QUICK else list(range(0, 140)) + [271, 272, 273]
for n in lens:
    d = rb(n)
    direct('len-kcache', KCACHE, d)
    if n <= 87:
        direct('len-kcache-again', KCACHE, d)
    if n >= 1:
        direct('len-klong', KLONG, d)
# 2. block boundaries, several inputs each, all three entries and both handlers
for n in (135, 136, 137, 271, 272, 273):
    for _ in range(8 if not QUICK else 2):
        d = rb(n)
        direct('boundary-kcache', KCACHE, d); direct('boundary-klong', KLONG, d)
        handler('boundary-handler', d, rnd.randrange(0, 64)); handler('boundary-handler2', d, rnd.randrange(0, 64), HANDLER2)
    for b in (0x00, 0xff, 0x01, 0x80):
        d = bytes([b]) * n
        direct('boundary-const', KCACHE, d)
# 3. unaligned source addresses 0..31 through the handler
for off in range(32):
    for n in (0, 1, 20, 32, 58, 63, 64, 65, 87, 88, 135, 136, 137, 160, 271, 272, 273, 1023):
        if QUICK and n not in (58, 64, 136, 160): continue
        handler('unaligned', rb(n), off + 32 * rnd.randrange(0, 4))
# 4. src shapes
A160 = (1 << 160) - 1
addrs = [0, 1, A160, 0x4200000000000000000000000000000000000006, 0xfffffffffffffffffffffffffffffffffffffffe] + \
        [rnd.getrandbits(160) for _ in range(40)]
NS = 300 if not QUICK else 30
for k in range(NS):
    # PoolId (src/types/PoolId.sol:14): keccak256(poolKey, 0xa0), five words
    c0, c1 = sorted((rnd.choice(addrs), rnd.choice(addrs)))
    fee = rnd.choice([0, 100, 500, 3000, 10000, 0x800000, rnd.getrandbits(24)])
    ts = rnd.choice([1, 10, 60, 200, 32767, rnd.randrange(1, 32768)])
    hooks = rnd.choice(addrs)
    pk = w(c0) + w(c1) + w(fee) + w(ts) + w(hooks)
    handler('poolId160', pk, 0x80 + 32 * rnd.randrange(0, 8))
    direct('poolId160-direct', KCACHE, pk)
    # Position key (src/libraries/Position.sol:55-60): 58 bytes at fmp+0x0c
    owner = rnd.choice(addrs); lo = rnd.randrange(-887272, 0); hi = rnd.randrange(0, 887273); salt = rb(32)
    key = owner.to_bytes(20, 'big') + (lo % (1 << 24)).to_bytes(3, 'big') + (hi % (1 << 24)).to_bytes(3, 'big') + salt
    fmp = 0x80 + 32 * rnd.randrange(0, 16)
    handler('positionKey58', key, fmp + 0x0c)
    handler('positionKey58-hit', key, fmp + 0x0c)
    # CurrencyDelta (src/libraries/CurrencyDelta.sol:12-14): keccak256(0, 64) of target, currency
    d = w(rnd.choice(addrs)) + w(rnd.choice(addrs))
    handler('currencyDelta64', d, 0); handler('currencyDelta64-hit', d, 0)
    # mapping slots with a small second word: pools[id] (slot 6), positions/ticks/bitmap at small offsets
    pid = keccak(pk)
    handler('mappingSmallSlot64', pid + w(rnd.choice([0, 1, 4, 5, 6])), 0)
    base = int.from_bytes(keccak(pid + w(6)), 'big')
    tick = rnd.randrange(-887272, 887273)
    handler('ticksSlot64', w(tick) + w(base + 4), 0)
    handler('bitmapSlot64', w(tick >> 8) + w(base + 5), 0)
    handler('positionsSlot64', keccak(key) + w(base + 6), 0)
    # ERC-6909 balances: keccak(owner . slot) then keccak(id . inner)
    o, i = rnd.choice(addrs), rnd.getrandbits(256)
    inner = keccak(w(o) + w(rnd.choice([1, 2, 3, 4])))
    handler('erc6909Outer64', w(o) + w(4), 0)
    handler('erc6909Inner64', w(i) + inner, 0)
res['shapeSeconds'] = round(time.time() - t0, 1)

# 5. the cache: planted entries that share a bucket and a tag with the probe
def bucket_and_tag(data):
    m.wr(IN, len(data), int.from_bytes(data, 'little'))
    c = m.run(HASHER, [HSEED, SECRET, IN, len(data)])
    h = c.r['rax']
    return h & (CAP - 1), h & (-CAP & M64)


def plant(idx, tag, key, value, locked=False):
    b = BUCKETS + 128 * idx
    m.wr(b, 8, tag | (1 if locked else 0)); m.wr(b + 8, 1, len(key) & 0xff)
    pad = key + rb(87 - len(key)) if len(key) <= 87 else key[:87]
    m.wr(b + 9, 87, int.from_bytes(pad, 'little')); m.wr(b + 0x60, 32, int.from_bytes(value, 'little'))


planted = {'probes': 0, 'falseHits': 0, 'positiveControls': 0, 'positiveHits': 0, 'kinds': {}}
NP = 3500 if not QUICK else 150
shapes = ['rand', 'pos58', 'delta64', 'slot64']
for k in range(NP):
    s = rnd.choice(shapes)
    if s == 'rand': a = rb(rnd.randrange(1, 88))
    elif s == 'pos58': a = rb(20) + rb(6) + rb(32)
    elif s == 'delta64': a = w(rnd.getrandbits(160)) + w(rnd.getrandbits(160))
    else: a = rb(32) + w(rnd.choice([4, 5, 6]))
    n = len(a)
    idx, tag = bucket_and_tag(a)
    kind = rnd.choice(('flipByte', 'flipLast8', 'flipFirst', 'shorterPrefix', 'longerExtension', 'lockedSameKey',
                       'otherTagSameKey', 'lenWrap'))
    poison = bytes([0xee]) * 31 + bytes([rnd.getrandbits(8)])
    if kind == 'flipByte':
        kk = bytearray(a); kk[rnd.randrange(n)] ^= 1 << rnd.randrange(8); plant(idx, tag, bytes(kk), poison)
    elif kind == 'flipLast8':
        kk = bytearray(a); kk[rnd.randrange(max(0, n - 8), n)] ^= 1 << rnd.randrange(8); plant(idx, tag, bytes(kk), poison)
    elif kind == 'flipFirst':
        kk = bytearray(a); kk[0] ^= 0x80; plant(idx, tag, bytes(kk), poison)
    elif kind == 'shorterPrefix':
        if n < 2: continue
        plant(idx, tag, a[:-1], poison)
    elif kind == 'longerExtension':
        if n >= 87: continue
        plant(idx, tag, a + rb(1), poison)
    elif kind == 'lockedSameKey':
        plant(idx, tag, a, poison, locked=True)
    elif kind == 'otherTagSameKey':
        plant(idx, (tag + CAP) & M64, a, poison)
    else:   # stored length byte equal to len+256 truncated: same byte, different key length cannot occur (len<=87)
        plant(idx, tag, a[:-1] if n > 1 else a + b'\x00', poison)
    planted['kinds'][kind] = planted['kinds'].get(kind, 0) + 1
    planted['probes'] += 1
    g = handler('planted-' + kind, a, rnd.randrange(0, 64)) if k % 3 == 0 else direct('planted-' + kind, KCACHE, a)
    if g == poison: planted['falseHits'] += 1
    # after the probe the bucket holds the probe's own correct entry; a repeat must hit and be right
    direct('planted-repeat', KCACHE, a)
    # positive control: plant the exact key with a marker value; a hit must return the marker
    if k % 4 == 0:
        mark = bytes([0x5a]) * 32
        plant(idx, tag, a, mark)
        m.wr(IN, n, int.from_bytes(a, 'little')); m.run(KCACHE, [OUTB, IN, n])
        planted['positiveControls'] += 1
        if m.rd(OUTB, 32).to_bytes(32, 'little') == mark: planted['positiveHits'] += 1
        plant(idx, tag, a, keccak(a))
res['planted'] = planted

# 6. bulk cache lookups: a working set that overfills one bucket region, repeated lookups mixing hits and misses
NB = 14000 if not QUICK else 200
pool = [rb(rnd.choice([20, 32, 52, 58, 64, 87, rnd.randrange(1, 88)])) for _ in range(800 if not QUICK else 50)]
for k in range(NB):
    a = rnd.choice(pool)
    if rnd.random() < 0.2:
        a = bytearray(a); a[rnd.randrange(len(a))] ^= 1; a = bytes(a)
    direct('bulk-lookup', KCACHE, a)

res['visitedInstructions'] = len(m.visited)
res['programInstructions'] = len(m.prog.ins)
res['steps'] = m.steps
res['seconds'] = round(time.time() - t0, 1)
cache_lookups = sum(v[0] for kk, v in res['sets'].items() if kk.startswith(('planted', 'bulk', 'len-kcache-again')) or kk.endswith('-hit'))
res['cacheLookups'] = cache_lookups
res['totals'] = {'cases': sum(v[0] for v in res['sets'].values()), 'mismatches': sum(v[1] for v in res['sets'].values()),
                 'errors': res['errors']}
json.dump(res, open(OUT, 'w'), indent=1)
print(OUT, json.dumps(res['totals']), 'planted', planted, 'cacheLookups', cache_lookups, 'visited', len(m.visited), 'of', len(m.prog.ins), res['seconds'], 's')
