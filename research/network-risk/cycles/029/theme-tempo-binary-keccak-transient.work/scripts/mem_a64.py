"""Runs the shipped aarch64 CALLDATALOAD and MCOPY handlers of tempo v1.19.1 (dispatch families B and A,
B:CALLDATALOAD 0x3b60e34, A:CALLDATALOAD 0x3b5c6cc, B:MCOPY 0x3b561e4, A:MCOPY 0x3b5db9c which calls it) in
the cycle 28 a64emu model, with memcpy and memmove modelled in Python (memmove as an overlap-safe copy).
Memory is pre-sized to 0x800 bytes so the resize routine is not entered; MCOPY with a zero length and huge
offsets is included because it must not touch memory or fail.

usage: python3 -I mem_a64.py <binary> <a64_mem.s> <out.json> [fault]
Faults: 'memcpy_fwd' models memmove as a forward byte loop (wrong on overlap with dst > src);
'cd_bound' turns the in-bounds test 'cmp x2, #0x20' of B:CALLDATALOAD into 'cmp x2, #0x1f'.
"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from a64emu import Prog, Mem, CPU as _CPU, Stop, M64, VLANE, lanes, pack


class CPU(_CPU):
    def i_rev64(self, o):
        w, n = self._vw(o[0]); assert w == 8
        b = lanes(self.vget(o[1]), 8, n)
        out = []
        for i in range(0, n, 8):
            out += list(reversed(b[i:i + 8]))
        self.vset(o[0], pack(out, 8))

    def i_ext(self, o):
        w, n = self._vw(o[0]); assert w == 8
        k = int(o[3].lstrip('#'), 0)
        cat = self.vget(o[1]) | (self.vget(o[2]) << (8 * n))
        self.vset(o[0], (cat >> (8 * k)) & ((1 << (8 * n)) - 1))

BIN, ASM, OUT = sys.argv[1:4]
FAULT = sys.argv[4] if len(sys.argv) > 4 else 'none'
SEED = 2026112730
M = (1 << 256) - 1
fb = open(BIN, 'rb').read()
prog = Prog([open(ASM).read()])
H = {('B', 'CALLDATALOAD'): 0x3b60e34, ('A', 'CALLDATALOAD'): 0x3b5c6cc, ('B', 'MCOPY'): 0x3b561e4, ('A', 'MCOPY'): 0x3b5db9c}
STACK, LENP, CTX, PARAMS, SP, CD, EMEM = 0x30000000, 0x31000000, 0x32000000, 0x33000000, 0x7ff000000000, 0x34000000, 0x35000000
GUARD = 0xa5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5
MEMSZ = 0x800


def ext_memcpy(cpu):
    d, s, n = cpu.x[0], cpu.x[1], cpu.x[2]
    data = [cpu.m.read(s + i, 1) for i in range(n)]
    for i, v in enumerate(data):
        cpu.m.write(d + i, 1, v)


def ext_memmove(cpu):
    d, s, n = cpu.x[0], cpu.x[1], cpu.x[2]
    if FAULT == 'memcpy_fwd':
        for i in range(n):
            cpu.m.write(d + i, 1, cpu.m.read(s + i, 1))
        return
    ext_memcpy(cpu)


def panic(cpu): raise Stop('panic called')


EXTERNS = {0x18855b0: ext_memcpy, 0x1884a50: ext_memmove, 0x1c838dc: panic, 0x1c87b30: panic, 0x1d8a004: lambda c: (_ for _ in ()).throw(Stop('resize entered'))}
faults = {}
if FAULT == 'cd_bound':
    faults[0x3b60e84] = lambda cpu, mn, ops: ('cmp', ['x2', '#0x1f'])
elif FAULT not in ('none', 'memcpy_fwd'):
    raise SystemExit('unknown fault')
visited = set()


def run(fam, op, words, calldata=b'', memory=b''):
    mem = Mem(fb, 0, 0x18742d8)
    st = mem.add(STACK, 32 * 8)
    stack = [GUARD, GUARD] + list(reversed(words))
    for i, w in enumerate(stack):
        st[32 * i:32 * i + 32] = w.to_bytes(32, 'little')
    mem.add(LENP, 8); mem.write(LENP, 8, len(stack))
    mem.add(CTX, 0x400); mem.add(PARAMS, 0x400)
    mem.write(CTX + 0xb0, 8, PARAMS)
    mem.write(PARAMS + 0x354, 4, 3)
    mem.write(CTX + 0xf8, 8, 1 << 40)
    cdr = mem.add(CD, max(1, len(calldata)) + 64)
    cdr[:len(calldata)] = calldata
    for i in range(len(calldata), len(cdr)):
        cdr[i] = 0x5a  # bytes past the end of calldata are junk; they must not be read
    mem.write(CTX + 0x60, 8, CD); mem.write(CTX + 0x68, 8, len(calldata))
    em = mem.add(EMEM, MEMSZ)
    em[:len(memory)] = memory
    mem.write(CTX + 0x8, 8, EMEM); mem.write(CTX + 0x10, 8, MEMSZ); mem.write(CTX + 0x18, 8, MEMSZ)
    mem.write(CTX + 0x128, 8, MEMSZ // 32)
    mem.add(SP - 0x20000, 0x20000)
    cpu = CPU(prog, mem, externs=EXTERNS, faults=faults)
    cpu.x[31] = SP
    k = len(words)
    h = H[(fam, op)]
    if fam == 'B':
        r = cpu.call(h, [0, STACK, LENP, CTX])
        status = r & 0xff
        newlen = mem.read(LENP, 8)
    else:
        r = cpu.call(h, [len(stack), STACK, 1 << 40, CTX])
        status = mem.read(CTX + 0x147, 1)
        newlen = r & 0x7ff
    visited.update(cpu.visited)
    for i in range(2):
        if int.from_bytes(st[32 * i:32 * i + 32], 'little') != GUARD:
            raise Stop('guard word changed')
    top = int.from_bytes(st[32 * (newlen - 1):32 * newlen], 'little') if newlen else None
    return status, newlen, top, bytes(em)


rnd = random.Random(SEED)
res = {'fault': FAULT, 'seed': SEED, 'byCase': {}, 'records': [], 'cases': 0, 'mismatches': 0, 'errors': 0}


def rec(key, ok, info):
    st = res['byCase'].setdefault(key, [0, 0, 0]); st[0] += 1; res['cases'] += 1
    if ok is None:
        st[2] += 1; res['errors'] += 1
    elif not ok:
        st[1] += 1; res['mismatches'] += 1
    if ok is not True and len(res['records']) < 300:
        res['records'].append(info)


def ref_cdload(cd, off):
    return int.from_bytes((cd[off:off + 32] if off < len(cd) else b'').ljust(32, b'\0'), 'big')


# CALLDATALOAD
offs_fixed = [0, 1, 31, 32, 33, 63, 64, 99, 100, 127, 128, 129, 1 << 16, (1 << 32) - 1, 1 << 32, (1 << 64) - 1, 1 << 64,
              (1 << 64) + 5, 1 << 255, M, M - 31]
for n in [0, 1, 4, 31, 32, 33, 36, 63, 64, 65, 100, 132, 164, 260]:
    cd = bytes(rnd.getrandbits(8) for _ in range(n))
    offs = set(offs_fixed) | {max(0, n - d) for d in range(0, 34)} | {n + d for d in range(0, 3)}
    for off in sorted(offs):
        want = ref_cdload(cd, off)
        for fam in ('B', 'A'):
            info = {'op': 'CALLDATALOAD', 'family': fam, 'cdlen': n, 'offset': hex(off)}
            try:
                status, nl, top, _ = run(fam, 'CALLDATALOAD', [off], cd)
            except Stop as e:
                info['error'] = str(e); rec(fam + ':CALLDATALOAD', None, info); continue
            ok = status == 0 and nl == 3 and top == want
            if not ok: info.update(model=hex(top) if top is not None else None, reference=hex(want), status=status)
            rec(fam + ':CALLDATALOAD', ok, info)

# MCOPY: battery vectors plus random and overlap edges
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import battery
mc = []
for op, a, b, c in battery.vectors():
    if op == 'MCOPY':
        mc.append((a.to_bytes(32, 'big') + b.to_bytes(32, 'big'), c & 0xff, (c >> 8) & 0xff, (c >> 16) & 0xff, 'battery'))
for _ in range(600):
    base = bytes(rnd.getrandbits(8) for _ in range(0x400))
    ln = rnd.choice([1, 2, 31, 32, 33, 63, 64, 65, rnd.randrange(1, 0x300)])
    src = rnd.randrange(0, 0x400 - ln + 1) if ln <= 0x400 else 0
    dst = rnd.choice([src + 1, src - 1, src + 31, src - 31, src + 32, src, rnd.randrange(0, 0x400)])
    dst = max(0, min(0x400 - ln, dst))
    mc.append((base, dst, src, ln, 'overlap'))
for z in [(1 << 200, 5, 0), (M, M, 0), (1 << 64, 0, 0)]:
    mc.append((bytes(64), z[0], z[1], z[2], 'zeroLengthHugeOffsets'))
for base, dst, src, ln, tag in mc:
    memb = bytearray(base.ljust(MEMSZ, b'\0'))
    if ln:
        memb[dst:dst + ln] = bytes(memb[src:src + ln])
    for fam in ('B', 'A'):
        info = {'op': 'MCOPY', 'family': fam, 'tag': tag, 'dst': hex(dst), 'src': hex(src), 'len': hex(ln)}
        try:
            status, nl, top, em = run(fam, 'MCOPY', [dst, src, ln], b'', base)
        except Stop as e:
            info['error'] = str(e); rec(fam + ':MCOPY:' + tag, None, info); continue
        ok = status == 0 and nl == 2 and em == bytes(memb)
        if not ok:
            info.update(status=status, firstDiff=next((i for i in range(MEMSZ) if em[i] != memb[i]), None))
        rec(fam + ':MCOPY:' + tag, ok, info)
res['visited'] = len(visited)
res['programInstructions'] = len(prog.ins)
json.dump(res, open(OUT, 'w'), indent=1)
print(OUT, 'cases', res['cases'], 'mismatches', res['mismatches'], 'errors', res['errors'], 'visited', len(visited))
