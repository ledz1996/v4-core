"""Task 4: the KECCAK256 cache routine of conduit-op-reth v2.5.1 (alloy-primitives 1.7.3 keccak_cache::compute
0x22b8990, the copy all three KECCAK256 handlers of tables 0x5ab3128.. call; 0x3ae0af0 is instruction for instruction
the same) and the uncached keccak256_impl 0x34a5120 it tail-calls for length 0 and length 88 and up, run from their
own disassembly in the x86-64 model (rethj.py LazyProg and CPU), with the CRYPTOGAMS SHA3_absorb / SHA3_squeeze
0x5a78380 / 0x5a78460 reached through their GOT slots 0x5be44d0 / 0x5be44d8 and run too. Only memcpy, memset and bcmp
are Python. The cache table (CACHE 0x5c06b50: bucket pointer, capacity; Once state 0x5c06b80) is placed in model
memory with 0x20000 buckets of 0x80 bytes (the capacity is set by the harness; the code reads it from CACHE+8).
Nothing from the binary is executed. Seed recorded. Every mismatch record is saved in full.
usage: python3 -I kcache_run.py <out.json> [fault] [quick]"""
import json, os, random, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from rethj import LazyProg, CPU, Stop, M64
from evm import keccak

BIN = '/home/user/v4-core/research/network-risk/cycles/035/op-stack-eth.work/dl/conduit251/x/app/conduit-op-reth'
FDE = '/home/user/v4-core/research/network-risk/cycles/035/op-stack-eth.work/build/c251.fde'
HERE = os.path.dirname(os.path.abspath(__file__))
COMPUTE, IMPL = 0x22b8990, 0x34a5120
CACHE, ONCE = 0x5c06b50, 0x5c06b80
GOT_MEMCPY, GOT_MEMMOVE, GOT_MEMSET, GOT_BCMP = 0x5be4488, 0x5be4480, 0x5be44c8, 0x5be4490
INTERNAL = {0x5be44d0: 0x5a78380, 0x5be44d8: 0x5a78460}
BUCKETS, CAP = 0x300000000, 0x20000
IN, OUTB = 0x30000000, 0x31000000
OUT = sys.argv[1]; FAULT = sys.argv[2] if len(sys.argv) > 2 else 'none'; QUICK = len(sys.argv) > 3
RSEED = 2026112736
FAULTS = {
    'padc': {0x22b8b6a: 'mov    BYTE PTR [rsp+r14*1+0xff],0x1'},       # padding byte one early, cached path
    'pad': {0x34a5205: 'mov    BYTE PTR [rsp+r14*1+0xcf],0x1'},        # same, uncached path
    'lenchk': {0x22b8ab3: 'nop'},                                       # hit without the length byte compare
    'tagchk': {0x22b8a99: 'nop'},                                       # hit without the tag compare
    'bcmp8': {}, 'none': {}}


class KCPU(CPU):
    def i_call(self, o, pc, n):
        m = re.match(r'^QWORD PTR \[0x([0-9a-f]+)\]$', o[0])
        if m and int(m.group(1), 16) in INTERNAL:
            self.r['rsp'] -= 8; self.write(self.r['rsp'], 8, n); return INTERNAL[int(m.group(1), 16)]
        return super().i_call(o, pc, n)

    def step(self, pc):
        if pc not in self.p.ins: self.p.load(pc)
        body = self.p.ins.get(pc, '')
        if body.startswith('repz ret'):          # CRYPTOGAMS uses 'repz ret' as a plain return
            self.visited.add(pc); self.steps += 1
            a = self.read(self.r['rsp'], 8); self.r['rsp'] += 8; return a
        if body.startswith('rep movs BYTE PTR'):
            self.visited.add(pc); self.steps += 1
            for _ in range(self.r['rcx']):
                self.write(self.r['rdi'], 1, self.read(self.r['rsi'], 1))
                self.r['rdi'] = (self.r['rdi'] + 1) & M64; self.r['rsi'] = (self.r['rsi'] + 1) & M64
            self.r['rcx'] = 0
            return self.p.nxt[pc]
        return super().step(pc)

    def i_cmpxchg(self, o, pc, n):
        d = self.opnd(o[0]); s = self.opnd(o[1]); b = d[2]
        cur = self.get(d); acc = self.r['rax'] & ((1 << b) - 1)
        self._sub(('r', 'rax' if b == 64 else 'eax', b), ('i', cur, None), 0, store=False)
        if acc == cur: self.zf = 1; self.put(d, self.get(s, b))
        else: self.zf = 0; self.setr('rax' if b == 64 else 'eax', cur)


img = open(os.path.join(HERE, '..', 'build', 'img-conduit.bin'), 'rb').read()
os.makedirs(os.path.join(HERE, '..', 'build', 'dis-conduit'), exist_ok=True)
prog = LazyProg(BIN, FDE, os.path.join(HERE, '..', 'build', 'dis-conduit'))


def memcpy(c):
    d, s, k = c.r['rdi'], c.r['rsi'], c.r['rdx']
    if k: c.write(d, k, c.read(s, k))
    c.r['rax'] = d
def memset(c):
    d, v, k = c.r['rdi'], c.r['rsi'] & 0xff, c.r['rdx']
    if k: c.write(d, k, int.from_bytes(bytes([v]) * k, 'little'))
    c.r['rax'] = d
def bcmp(c):
    a, b, k = c.r['rdi'], c.r['rsi'], c.r['rdx']
    if FAULT == 'bcmp8': k = max(0, k - 8)
    c.r['rax'] = 0 if k == 0 or c.read(a, k) == c.read(b, k) else 1

cpu = KCPU(prog, img, {}, {GOT_MEMCPY: memcpy, GOT_MEMMOVE: memcpy, GOT_MEMSET: memset, GOT_BCMP: bcmp}, FAULTS[FAULT], {})
cpu.write(ONCE, 4, 0); cpu.write(CACHE, 8, BUCKETS); cpu.write(CACHE + 8, 8, CAP)
cpu.write((cpu.fs + 0x28) & M64, 8, 0x1122334455667788)
res = {'model': 'conduit-op-reth v2.5.1 keccak_cache::compute 0x22b8990', 'fault': FAULT, 'seed': RSEED, 'sets': {}, 'records': [],
       'errors': 0, 'started': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
rnd = random.Random(RSEED)


def rec(setname, ok, err=None, **kw):
    st = res['sets'].setdefault(setname, [0, 0, 0]); st[0] += 1
    if err is not None: st[2] += 1; res['errors'] += 1; kw.update(error=err, set=setname); res['records'].append(kw)
    elif not ok: st[1] += 1; kw['set'] = setname; res['records'].append(kw)


def run(fn, data):
    if data: cpu.write(IN, len(data), int.from_bytes(data, 'little'))
    for k in list(cpu.r): cpu.r[k] = 0
    cpu.y = [0] * 16
    cpu.r['rdi'], cpu.r['rsi'], cpu.r['rdx'] = OUTB, IN, len(data)
    rsp = 0x7ffff0000000 - 8; cpu.write(rsp, 8, 0xdead0000); cpu.r['rsp'] = rsp; cpu.budget = 0
    pc = fn
    while pc != 0xdead0000: pc = cpu.step(pc)
    return cpu.read(OUTB, 32).to_bytes(32, 'little')


def h64(data):
    """The bucket hash the routine computes, read back by running it on a fresh table entry: the tag and index are
    taken from the bucket the routine just wrote (the one whose length byte and key now hold data)."""
    raise NotImplementedError


def direct(setname, data, fn=COMPUTE, expect=None):
    try: got = run(fn, data)
    except Stop as e: rec(setname, False, str(e), input=data.hex()); return None
    want = keccak(data) if expect is None else expect
    rec(setname, got == want, input=data.hex(), model=got.hex(), reference=want.hex())
    return got


def find_bucket(data):
    """After a miss stored data, find its bucket by scanning the buckets the model memory holds (written ones)."""
    for a in sorted({(x - BUCKETS) // 0x80 for x in cpu.mem if BUCKETS <= x < BUCKETS + CAP * 0x80}):
        b = BUCKETS + a * 0x80
        n = cpu.read(b + 8, 1)
        if n == len(data) and cpu.read(b + 9, n).to_bytes(n, 'little') == data: return b
    return None


lengths = list(range(0, 1101)) if not QUICK else list(range(0, 300)) + [535, 543, 544, 1087, 1088, 1089]
for n in lengths:
    direct('compute_len_0_1100', bytes(rnd.getrandbits(8) for _ in range(n)))
for n in (list(range(0, 300)) if not QUICK else list(range(0, 140))):
    direct('impl_len_0_299', bytes(rnd.getrandbits(8) for _ in range(n)), fn=IMPL)
# second call: lengths 1..87 hit the entry the first call stored
for n in list(range(1, 88)) + [135, 136, 137, 271, 272, 273]:
    d = bytes(rnd.getrandbits(8) for _ in range(n)); direct('first_call', d); direct('second_call', d)
# PoolManager shapes: 64-byte mapping keys, PoolId (160 bytes, uncached), Position key (58 -> 32 bytes path)
for i in range(200 if not QUICK else 40):
    for d in (rnd.getrandbits(256).to_bytes(32, 'big') + (i % 12).to_bytes(32, 'big'),
              rnd.getrandbits(160).to_bytes(20, 'big') + rnd.getrandbits(160).to_bytes(20, 'big'),
              bytes(12) + rnd.getrandbits(160).to_bytes(20, 'big') + rnd.getrandbits(256).to_bytes(32, 'big'),
              rnd.getrandbits(1280).to_bytes(160, 'big'), rnd.getrandbits(464).to_bytes(58, 'big')):
        direct('v4_shapes', d); direct('v4_shapes_again', d)
# planted probes: store key K (a miss writes its bucket), then rewrite that bucket so it holds a key K' != K with the
# same tag and a marker hash; probing K must not return the marker. Positive control: bucket holds K with the marker.
MARK = bytes(range(0xa0, 0xc0))
kinds = ['flip_any', 'flip_last8', 'flip_first', 'shorter', 'longer', 'lenbyte', 'locked', 'othertag']
for i in range(500 if not QUICK else 100):
    n = rnd.randint(2, 86); k = bytes(rnd.getrandbits(8) for _ in range(n))
    direct('probe_setup', k)
    b = find_bucket(k)
    if b is None: rec('probe_setup_bucket', False, 'bucket not found', input=k.hex()); continue
    tag = cpu.read(b, 8)
    for kind in kinds + ['control']:
        kk = bytearray(k); ln = n; t = tag
        if kind == 'flip_any': j = rnd.randrange(n); kk[j] ^= 1 << rnd.randrange(8)
        elif kind == 'flip_last8': j = n - 1 - rnd.randrange(min(8, n)); kk[j] ^= 1 << rnd.randrange(8)
        elif kind == 'flip_first': kk[0] ^= 0x80
        elif kind == 'shorter': ln = n - 1
        elif kind == 'longer': kk = kk + bytes([rnd.getrandbits(8)]); ln = n + 1
        elif kind == 'lenbyte': ln = n - 1          # same bytes, length byte one smaller
        elif kind == 'locked': t = tag | 1
        elif kind == 'othertag': t = tag ^ (1 << 40)
        cpu.write(b, 8, t); cpu.write(b + 8, 1, ln)
        cpu.write(b + 9, 0x57, int.from_bytes(bytes(kk[:0x57]).ljust(0x57, b'\0'), 'little'))
        cpu.write(b + 0x60, 32, int.from_bytes(MARK, 'little'))
        try: got = run(COMPUTE, k)
        except Stop as e: rec('probe_' + kind, False, str(e), input=k.hex()); continue
        if kind == 'control': rec('probe_control', got == MARK, input=k.hex(), model=got.hex(), reference=MARK.hex())
        else: rec('probe_' + kind, got == keccak(k), input=k.hex(), model=got.hex(), reference=keccak(k).hex(), planted_hit=(got == MARK))
res['steps'] = cpu.steps; res['instructions_visited'] = len(cpu.visited) if hasattr(cpu, 'visited') else None
res['finished'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
res['wrong'] = sum(v[1] for v in res['sets'].values()); res['cases'] = sum(v[0] for v in res['sets'].values())
res['planted_false_hits'] = sum(1 for r in res['records'] if r.get('planted_hit'))
json.dump(res, open(OUT, 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != 'records'}))
for r in res['records'][:3]: print(r)
