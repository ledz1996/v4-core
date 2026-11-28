"""Cycle 38: byte conversion routines of the holiman/uint256 copy linked into each Go binary, run in the models:
(*Int).WriteToSlice and PutUint256 (word to memory, the MSTORE and return data direction) for every destination
length 0..40, (*Int).SetBytes for every source length 0..40 and the fixed-width SetBytes1..32 (memory, calldata and
PUSH to word), each against Python. erigon v3.8.2 pins uint256 087f4b32f234, whose WriteToSlice and shift helpers
are rewritten relative to v1.3.2. Seed 38_1128_06. usage: python3 -I conv.py <target> <out.json>"""
import json, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import goshim as G, targets, models, gloop
# the switch tables, bswap and rotates of these routines need the gloop CPU additions (computed jumps, bswap, rol)
for k in ('_target', 'i_call', 'i_jmp', 'i_bswap', '_rot', 'i_rol', 'i_ror'):
    setattr(models.X64, k, gloop.LoopCPU.__dict__[k])
TGT, OUT = sys.argv[1], sys.argv[2]
m = targets.model(TGT)
U = G.U + '(*Int).'
B = G.OPND + 0x200
rnd = random.Random(381128_06)
words = [0, 1, G.M, 1 << 255, 0x0102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f20] + [rnd.getrandbits(256) for _ in range(40)]
res = {'target': TGT, 'cases': 0, 'mismatches': 0, 'errors': 0, 'byFn': {}, 'records': []}


def call(cpu, name, args):
    if m.arch == 'amd64':
        m._x64call(cpu, m.entry(U + name), dict(zip(['rax', 'rbx', 'rcx', 'rdi', 'rsi'], args)))
        return cpu.r['rax']
    m._a64call(cpu, m.entry(U + name), args)
    return cpu.x[0]


def note(fn, ok, rec):
    st = res['byFn'].setdefault(fn, [0, 0, 0]); st[0] += 1; res['cases'] += 1
    if ok is None:
        st[2] += 1; res['errors'] += 1; res['records'].append(rec)
    elif not ok:
        st[1] += 1; res['mismatches'] += 1; res['records'].append(rec)


for w in words:
    for n in range(0, 41):
        for fn in ('WriteToSlice', 'PutUint256'):
            if U + fn not in m.fns or (fn == 'PutUint256' and n < 32):
                continue
            cpu = m._x64() if m.arch == 'amd64' else m._a64()
            m.wr(cpu, G.OPND, w)
            for i in range(0, 64, 8):
                m.wr(cpu, B + i, 0xa5a5a5a5a5a5a5a5, 8)
            try:
                call(cpu, fn, [G.OPND, B, n, n])
                got = bytes(m.rd(cpu, B + i, 1) for i in range(64))
            except Exception as e:
                note(fn, None, {'fn': fn, 'w': hex(w), 'n': n, 'error': str(e)}); continue
            k = min(n, 32)
            want = (w & ((1 << (8 * k)) - 1)).to_bytes(k, 'big') + b'\xa5' * (64 - k)
            note(fn, got == want, {'fn': fn, 'w': hex(w), 'n': n, 'model': got.hex(), 'reference': want.hex()})
        # SetBytes from a buffer of n bytes
        buf = w.to_bytes(32, 'big')[::-1][:n][::-1] if n <= 32 else (b'\x77' * (n - 32) + w.to_bytes(32, 'big'))
        names = ['SetBytes'] + (['SetBytes%d' % n] if 1 <= n <= 32 else [])
        for fn in names:
            if U + fn not in m.fns:
                continue
            cpu = m._x64() if m.arch == 'amd64' else m._a64()
            m.wr(cpu, G.OPND, G.GUARD)
            for i in range(0, 48, 8):
                m.wr(cpu, B + i, int.from_bytes((buf + b'\0' * 48)[i:i + 8], 'little'), 8)
            try:
                call(cpu, fn, [G.OPND, B, n, n])
                got = m.rd(cpu, G.OPND)
            except Exception as e:
                note(fn if fn == 'SetBytes' else 'SetBytesN', None, {'fn': fn, 'w': hex(w), 'n': n, 'error': str(e)}); continue
            want = int.from_bytes(buf[-32:], 'big') if n else 0
            note(fn if fn == 'SetBytes' else 'SetBytesN', got == want, {'fn': fn, 'w': hex(w), 'n': n, 'model': hex(got), 'reference': hex(want)})
json.dump(res, open(OUT, 'w'), indent=1)
print(OUT, res['cases'], res['mismatches'], res['errors'], res['byFn'], res['records'][:2])
