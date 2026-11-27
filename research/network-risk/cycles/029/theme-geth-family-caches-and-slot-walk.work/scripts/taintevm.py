"""Provenance tracking on top of the reference interpreter (tools/opdiff/pyevm.py).

Every stack word and every 32 byte memory word written by MSTORE carries a tag that says how
the value was produced:
  ('C',)            built only from PUSH constants (and arithmetic on constants)
  ('K', n)          the output of the n-th KECCAK256 of the run
  ('KO', n, off)    a KECCAK256 output plus a constant off (ADD with a constant operand)
  ('X', why)        anything else: call data, CALLER, a loaded word, a mix of the above
At every SSTORE, SLOAD, TSTORE and TLOAD the tag of the slot operand is recorded per program
counter, together with the tags of the words that went into the keccak behind it. The semantics
are those of pyevm.World.run; only the tags are added. Analysis tool, no transactions.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'tools', 'opdiff'))
from evm import MASK, SIGN, M, keccak, ref_sdiv, ref_smod, ref_signextend, ref_byte, ref_sar
import pyevm
from pyevm import Halt, NAMES

C = ('C',)


def tag_of_word(mtags, off):
    return mtags.get(off, ('X', 'mem'))


def kill(mtags, off, size):
    if size == 0: return
    if size <= 4096 and size < 2 * len(mtags):
        for k in range(max(0, off - 31), off + size):
            if k in mtags: del mtags[k]
        return
    for k in [k for k in mtags if k + 32 > off and k < off + size]: del mtags[k]


class TaintWorld(pyevm.World):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.sites = {}  # (op, pc) -> {classkey: count}
        self.kin = {}  # keccak serial -> (pc, size, tuple of word tags)
        self.kser = 0
        self.watch = None  # address whose sites are recorded

    def record(self, op, pc, tag, val, me):
        if self.watch is not None and me != self.watch: return
        if tag[0] == 'C': key = ('C', val)
        elif tag[0] == 'K': key = ('K', self.kdesc(tag[1]))
        elif tag[0] == 'KO': key = ('KO', self.kdesc(tag[1]), tag[2])
        else: key = ('X', tag[1])
        d = self.sites.setdefault((op, pc), {})
        d[key] = d.get(key, 0) + 1

    def kdesc(self, n):
        pc, size, words = self.kin[n]
        out = []
        for t in words:
            if t[0] == 'C': out.append('C')
            elif t[0] in ('K', 'KO'): out.append('K' + ('+%d' % t[2] if t[0] == 'KO' else '') + '(' + self.kdesc(t[1]) + ')')
            else: out.append('X:' + t[1])
        return 'keccak@%d/%d[%s]' % (pc, size, ','.join(out))

    def run(self, code_addr, me, caller, value, data, static, depth):
        code = self.codes[code_addr]; jd = self.jd[code_addr]; n = len(code)
        st = []; ts = []; mem = bytearray(); mt = {}; pc = 0; rd = b''
        cov = self.cover.setdefault(code_addr, set()); ops = self.ops

        def ext(off, size):
            if size == 0: return
            if off + size > (1 << 24): raise Halt('memory too large')
            need = (off + size + 31) // 32 * 32
            if need > len(mem): mem.extend(bytes(need - len(mem)))

        def push(v, t): st.append(v); ts.append(t)

        def pop():
            ts.pop(); return st.pop()

        while True:
            if pc >= n: return True, b''
            op = code[pc]
            self.steps += 1
            if self.max_steps and self.steps > self.max_steps: raise TimeoutError('step limit')
            cov.add(pc); ops[op] = ops.get(op, 0) + 1
            try:
                if 0x60 <= op <= 0x7f:
                    k = op - 0x5f; push(int.from_bytes(code[pc + 1:pc + 1 + k].ljust(k, b'\0'), 'big'), C); pc += k + 1
                    if len(st) > 1024: raise Halt('stack overflow')
                    continue
                if 0x80 <= op <= 0x8f:
                    push(st[-(op - 0x7f)], ts[-(op - 0x7f)]); pc += 1
                    if len(st) > 1024: raise Halt('stack overflow')
                    continue
                if 0x90 <= op <= 0x9f:
                    k = op - 0x8e; st[-1], st[-k] = st[-k], st[-1]; ts[-1], ts[-k] = ts[-k], ts[-1]; pc += 1; continue
                if op == 0x5b: pc += 1; continue
                if op == 0x50: pop(); pc += 1; continue
                if op == 0x5f:
                    push(0, C); pc += 1
                    if len(st) > 1024: raise Halt('stack overflow')
                    continue
                if 0x01 <= op <= 0x1d and op not in (0x0c, 0x0d, 0x0e, 0x0f):
                    nin = 3 if op in (0x08, 0x09) else 1 if op in (0x15, 0x19) else 2
                    tin = ts[-nin:]; vin = st[-nin:]
                    a = st.pop()
                    if op == 0x01: r = (a + st[-1]) & MASK
                    elif op == 0x02: r = (a * st[-1]) & MASK
                    elif op == 0x03: r = (a - st[-1]) & MASK
                    elif op == 0x04: b = st[-1]; r = a // b if b else 0
                    elif op == 0x05: r = ref_sdiv(a, st[-1])
                    elif op == 0x06: b = st[-1]; r = a % b if b else 0
                    elif op == 0x07: r = ref_smod(a, st[-1])
                    elif op == 0x08: b = st.pop(); c = st[-1]; r = (a + b) % c if c else 0
                    elif op == 0x09: b = st.pop(); c = st[-1]; r = (a * b) % c if c else 0
                    elif op == 0x0a: r = pow(a, st[-1], M)
                    elif op == 0x0b: r = ref_signextend(a, st[-1])
                    elif op == 0x10: r = int(a < st[-1])
                    elif op == 0x11: r = int(a > st[-1])
                    elif op == 0x12: b = st[-1]; r = int((a - M if a & SIGN else a) < (b - M if b & SIGN else b))
                    elif op == 0x13: b = st[-1]; r = int((a - M if a & SIGN else a) > (b - M if b & SIGN else b))
                    elif op == 0x14: r = int(a == st[-1])
                    elif op == 0x15: st.append(a); r = int(a == 0)
                    elif op == 0x16: r = a & st[-1]
                    elif op == 0x17: r = a | st[-1]
                    elif op == 0x18: r = a ^ st[-1]
                    elif op == 0x19: st.append(a); r = a ^ MASK
                    elif op == 0x1a: r = ref_byte(a, st[-1])
                    elif op == 0x1b: r = (st[-1] << a) & MASK if a < 256 else 0
                    elif op == 0x1c: r = st[-1] >> a if a < 256 else 0
                    elif op == 0x1d: r = ref_sar(a, st[-1])
                    st[-1] = r
                    for _ in range(nin): ts.pop()
                    if all(t[0] == 'C' for t in tin): t = C
                    elif op == 0x01 and len(tin) == 2 and {tin[0][0], tin[1][0]} <= {'C', 'K', 'KO'} and [x[0] for x in tin].count('C') == 1:
                        kt = tin[0] if tin[0][0] != 'C' else tin[1]; cv = vin[0] if tin[0][0] == 'C' else vin[1]
                        off = (kt[2] if kt[0] == 'KO' else 0) + cv
                        t = ('KO', kt[1], off)
                    elif op == 0x16 and len(tin) == 2 and any(x[0] == 'C' and v == MASK for x, v in zip(tin, vin)):
                        t = tin[0] if tin[1][0] == 'C' else tin[1]
                    else:
                        t = ('X', NAMES[op] + '(' + ','.join(x[0] for x in tin) + ')')
                    ts.append(t)
                elif op == 0x20:
                    off = pop(); size = pop(); ext(off, size)
                    words = tuple(tag_of_word(mt, off + j) for j in range(0, size, 32)) if off % 32 == 0 and size % 32 == 0 else (('X', 'unaligned:%d+%d' % (off % 32, size)),)
                    self.kser += 1; self.kin[self.kser] = (pc, size, words)
                    push(int.from_bytes(keccak(bytes(mem[off:off + size])), 'big'), ('K', self.kser))
                elif op == 0x30: push(me, ('X', 'ADDRESS'))
                elif op == 0x31: v = pop(); push(self.balances.get(v & ((1 << 160) - 1), 0), ('X', 'BALANCE'))
                elif op == 0x33: push(caller, ('X', 'CALLER'))
                elif op == 0x34: push(value, ('X', 'CALLVALUE'))
                elif op == 0x35:
                    off = pop(); push(int.from_bytes(data[off:off + 32].ljust(32, b'\0'), 'big') if off < len(data) else 0, ('X', 'CALLDATA'))
                elif op == 0x36: push(len(data), ('X', 'CALLDATASIZE'))
                elif op == 0x37:
                    d = pop(); off = pop(); size = pop(); ext(d, size); kill(mt, d, size)
                    if size: mem[d:d + size] = (data[off:off + size] if off < len(data) else b'').ljust(size, b'\0')
                elif op == 0x38: push(n, C)
                elif op == 0x39:
                    d = pop(); off = pop(); size = pop(); ext(d, size); kill(mt, d, size)
                    if size: mem[d:d + size] = (code[off:off + size] if off < n else b'').ljust(size, b'\0')
                elif op == 0x3b: v = pop(); push(len(self.codes.get(v & ((1 << 160) - 1), b'')), ('X', 'EXTCODESIZE'))
                elif op == 0x3d: push(len(rd), ('X', 'RETURNDATASIZE'))
                elif op == 0x3e:
                    d = pop(); off = pop(); size = pop()
                    if off + size > len(rd): raise Halt('return data out of bounds')
                    ext(d, size); kill(mt, d, size)
                    if size: mem[d:d + size] = rd[off:off + size]
                elif op == 0x47: push(self.balances.get(me, 0), ('X', 'SELFBALANCE'))
                elif op == 0x51:
                    off = pop(); ext(off, 32); push(int.from_bytes(mem[off:off + 32], 'big'), tag_of_word(mt, off))
                elif op == 0x52:
                    t = ts[-2]; off = pop(); v = pop(); ext(off, 32); mem[off:off + 32] = v.to_bytes(32, 'big')
                    kill(mt, off, 32); mt[off] = t
                elif op == 0x53:
                    off = pop(); v = pop(); ext(off, 1); mem[off] = v & 0xff; kill(mt, off, 1)
                elif op == 0x54:
                    t = ts[-1]; k = pop(); self.record('SLOAD', pc, t, k, me); push(self.storage.get((me, k), 0), ('X', 'SLOAD'))
                elif op == 0x55:
                    if static: raise Halt('write in static context')
                    t = ts[-1]; k = pop(); self.record('SSTORE', pc, t, k, me); self.storage[(me, k)] = pop()
                elif op == 0x56:
                    d = pop()
                    if d not in jd: raise Halt('bad jump')
                    pc = d; continue
                elif op == 0x57:
                    d = pop(); c = pop()
                    self.branches.setdefault((code_addr, pc), set()).add(bool(c))
                    if c:
                        if d not in jd: raise Halt('bad jump')
                        pc = d; continue
                elif op == 0x58: push(pc, C)
                elif op == 0x59: push(len(mem), ('X', 'MSIZE'))
                elif op == 0x5a: push(10 ** 9, ('X', 'GAS'))
                elif op == 0x5c:
                    t = ts[-1]; k = pop(); self.record('TLOAD', pc, t, k, me); push(self.transient.get((me, k), 0), ('X', 'TLOAD'))
                elif op == 0x5d:
                    if static: raise Halt('write in static context')
                    t = ts[-1]; k = pop(); self.record('TSTORE', pc, t, k, me); self.transient[(me, k)] = pop()
                elif op == 0x5e:
                    d = pop(); src = pop(); size = pop(); ext(max(d, src), size)
                    moved = {k - src + d: v for k, v in mt.items() if k >= src and k + 32 <= src + size}
                    kill(mt, d, size); mt.update(moved)
                    if size: mem[d:d + size] = bytes(mem[src:src + size])
                elif 0xa0 <= op <= 0xa4:
                    if static: raise Halt('log in static context')
                    off = pop(); size = pop(); ext(off, size)
                    for _ in range(op - 0xa0): pop()
                    self.logs += 1
                elif op in (0xf1, 0xfa, 0xf4):
                    pop(); to = pop() & ((1 << 160) - 1)
                    val = pop() if op == 0xf1 else 0
                    io = pop(); isz = pop(); oo = pop(); osz = pop()
                    ext(io, isz); ext(oo, osz)
                    if val and static: raise Halt('value in static context')
                    arg = bytes(mem[io:io + isz])
                    if depth >= 1024: ok, rd = False, b''
                    elif op == 0xf1: ok, rd = self.call(me, to, val, arg, static, depth + 1)
                    elif op == 0xfa: ok, rd = self.call(me, to, 0, arg, True, depth + 1)
                    else: ok, rd = self.call(caller, me, 0, arg, static, depth + 1, code_addr=to, storage_addr=me, apparent=value)
                    k = min(osz, len(rd)); kill(mt, oo, osz)
                    if k: mem[oo:oo + k] = rd[:k]
                    push(int(ok), ('X', 'CALL'))
                elif op == 0xf3:
                    off = pop(); size = pop(); ext(off, size); return True, bytes(mem[off:off + size])
                elif op == 0xfd:
                    off = pop(); size = pop(); ext(off, size); return False, bytes(mem[off:off + size])
                elif op == 0x00: return True, b''
                elif op == 0xfe: raise Halt('invalid')
                else: raise NotImplementedError(f'opcode {op:#x} ({NAMES.get(op, "?")}) at pc {pc} of {code_addr:#x}')
            except IndexError:
                raise Halt('stack underflow')
            if len(st) > 1024: raise Halt('stack overflow')
            assert len(st) == len(ts)
            pc += 1
