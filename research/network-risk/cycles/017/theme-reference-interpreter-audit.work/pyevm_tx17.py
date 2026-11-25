"""Cycle 17 copy of cycles/016/theme-revert-rollback-mined.work/pyevm_tx.py (theme-reference-interpreter-audit, task 3).
Changes against the cycle 16 file: (1) the stack limit is checked after PUSH, PUSH0 and DUP too; (2) EXTCODEHASH of an
account with no code, zero balance and zero nonce is 0 (ctx["nonces"] holds nonces); (3) a call into an EIP-7702 account
delegated to a precompile runs empty code; (4) modexp fails when a length is above 1024 (EIP-7823, Osaka; ctx["osaka"]);
(6) frames that ran out of gas on the chain are failed at the same (code, input), as pyevm2.py of cycle 13 does;
(5) calls into node-implemented contracts (self.native) are answered from the chain's own call tree (self.oracle,
keyed by callee and input, in order), with that frame's logs, so that every bytecode frame around them, the PoolManager
included, is still executed by the reference. The node contract's own storage is not modelled.

Cycle 16 copy of tools/opdiff/pyevm.py for replaying whole mined transactions (theme-revert-rollback-mined).
Added: block context opcodes, ORIGIN, EXTCODEHASH, EXTCODECOPY, captured logs, a record of every frame
into a watched address, ecrecover and modexp, and EIP-7702 delegation designators. Everything else is the original.

A small reference EVM in Python, written from the Ethereum execution specification
for the Cancun instruction set, without gas. It exists so that the PoolManager
bytecode can be run instruction by instruction under the specified semantics, with
no client involved, and compared with what the networks return (bytecode.py).

Not implemented: gas (GAS returns a constant and nothing runs out), CREATE, CREATE2,
SELFDESTRUCT, EXTCODECOPY, BLOCKHASH, blob opcodes and the precompiles other than
ecrecover on malformed input (empty result), SHA-256 and identity. Reaching anything
else raises, so a run cannot silently depend on it."""
import hashlib
from evm import MASK, SIGN, M, keccak, ref_sdiv, ref_smod, ref_signextend, ref_byte, ref_sar

NAMES = {0x00: 'STOP', 0x01: 'ADD', 0x02: 'MUL', 0x03: 'SUB', 0x04: 'DIV', 0x05: 'SDIV', 0x06: 'MOD', 0x07: 'SMOD', 0x08: 'ADDMOD',
         0x09: 'MULMOD', 0x0a: 'EXP', 0x0b: 'SIGNEXTEND', 0x10: 'LT', 0x11: 'GT', 0x12: 'SLT', 0x13: 'SGT', 0x14: 'EQ', 0x15: 'ISZERO',
         0x16: 'AND', 0x17: 'OR', 0x18: 'XOR', 0x19: 'NOT', 0x1a: 'BYTE', 0x1b: 'SHL', 0x1c: 'SHR', 0x1d: 'SAR', 0x20: 'KECCAK256',
         0x30: 'ADDRESS', 0x31: 'BALANCE', 0x32: 'ORIGIN', 0x33: 'CALLER', 0x34: 'CALLVALUE', 0x35: 'CALLDATALOAD', 0x36: 'CALLDATASIZE',
         0x37: 'CALLDATACOPY', 0x38: 'CODESIZE', 0x39: 'CODECOPY', 0x3a: 'GASPRICE', 0x3b: 'EXTCODESIZE', 0x3d: 'RETURNDATASIZE',
         0x3e: 'RETURNDATACOPY', 0x3f: 'EXTCODEHASH', 0x42: 'TIMESTAMP', 0x43: 'NUMBER', 0x46: 'CHAINID', 0x47: 'SELFBALANCE', 0x48: 'BASEFEE',
         0x50: 'POP', 0x51: 'MLOAD', 0x52: 'MSTORE', 0x53: 'MSTORE8', 0x54: 'SLOAD', 0x55: 'SSTORE', 0x56: 'JUMP', 0x57: 'JUMPI',
         0x58: 'PC', 0x59: 'MSIZE', 0x5a: 'GAS', 0x5b: 'JUMPDEST', 0x5c: 'TLOAD', 0x5d: 'TSTORE', 0x5e: 'MCOPY', 0x5f: 'PUSH0',
         0xa0: 'LOG0', 0xa1: 'LOG1', 0xa2: 'LOG2', 0xa3: 'LOG3', 0xa4: 'LOG4', 0xf1: 'CALL', 0xf3: 'RETURN', 0xf4: 'DELEGATECALL',
         0xfa: 'STATICCALL', 0xfd: 'REVERT', 0xfe: 'INVALID'}
for _i in range(1, 33): NAMES[0x5f + _i] = f'PUSH{_i}'
for _i in range(1, 17): NAMES[0x7f + _i] = f'DUP{_i}'; NAMES[0x8f + _i] = f'SWAP{_i}'


class Halt(Exception):
    """Exceptional halt: the frame fails with empty return data."""


def jumpdests(code):
    """The scalar rule of the specification: 0x5b outside PUSH data."""
    out = set(); i = 0; n = len(code)
    while i < n:
        op = code[i]
        if op == 0x5b: out.add(i)
        i += op - 0x5e if 0x60 <= op <= 0x7f else 1
    return out


class World:
    def __init__(self, codes, balances=None):
        self.codes = dict(codes)  # address int -> bytes
        self.storage = {}  # (address, slot) -> value
        self.transient = {}
        self.balances = dict(balances or {})
        self.jd = {a: jumpdests(c) for a, c in self.codes.items()}
        self.steps = 0
        self.max_steps = None
        self.cover = {}  # address -> set of executed pcs
        self.branches = {}  # (address, pc of JUMPI) -> set of outcomes
        self.ops = {}  # opcode -> count
        self.trace = None  # list of (depth, pc, op) when enabled
        self.trace_stack = False
        self.logs = []
        self.ctx = {}
        self.watch = set()
        self.native = set()  # addresses implemented by the node, not by bytecode
        self.frames = []  # (depth, to, selector, ok) for every call into a watched address, in start order
        self.oracle = None  # (callee, input) -> list of (ok, output, logs) from the chain's call tree
        self.oracled = []
        self.oog = None; self.forced = 0

    def snapshot(self): return (dict(self.storage), dict(self.transient), dict(self.balances), len(self.logs))
    def restore(self, snap):
        self.storage, self.transient, self.balances = snap[0], snap[1], snap[2]; del self.logs[snap[3]:]

    def call(self, caller, to, value, data, static, depth, code_addr=None, storage_addr=None):
        """Returns (success, returndata)."""
        fr = None
        if self.oog is not None:  # gas is not modelled: a frame that ran out of gas on the chain is failed here at the same (code, input), in order
            q = self.oog.get(((code_addr if code_addr is not None else to), bytes(data)))
            if q and q.pop(0):
                self.forced += 1
                if to in self.watch: self.frames.append([depth, to, bytes(data[:4]).hex(), False])
                return False, b''
        if to in self.watch:
            fr = [depth, to, bytes(data[:4]).hex(), None]; self.frames.append(fr)
        ok, ret = self._call(caller, to, value, data, static, depth, code_addr, storage_addr)
        if fr is not None: fr[3] = ok
        return ok, ret

    def _call(self, caller, to, value, data, static, depth, code_addr=None, storage_addr=None):
        snap = self.snapshot()
        if value:
            if self.balances.get(caller, 0) < value: return False, b''
            self.balances[caller] -= value; self.balances[to] = self.balances.get(to, 0) + value
        code_addr = to if code_addr is None else code_addr
        if code_addr == 0x64 and 0x64 in self.native and bytes(data[:4]).hex() == 'a3b1b31d' and 'l2number' in self.ctx:
            return True, self.ctx['l2number'].to_bytes(32, 'big')
        if code_addr in self.native:
            q = (self.oracle or {}).get((code_addr, bytes(data)))
            if not q: raise NotImplementedError(f'chain precompile {code_addr:#x} {bytes(data[:4]).hex()} not in the call tree')
            o_ok, o_ret, o_logs = q.pop(0); self.oracled.append((code_addr, bytes(data[:4]).hex(), o_ok))
            if static and o_logs: raise NotImplementedError('node contract logged inside a static frame')
            if o_ok: self.logs.extend(o_logs)
            else: self.restore(snap)
            return o_ok, o_ret
        code = self.codes.get(code_addr)
        if code is not None and len(code) == 23 and code[:3] == b'\xef\x01\x00':
            code_addr = int.from_bytes(code[3:], 'big'); code = self.codes.get(code_addr)
            if code is None and (0 < code_addr < 0x12 or code_addr == 0x100): return True, b''  # EIP-7702: a precompile is not run through a delegation (empty code)
            if code is not None and code_addr not in self.jd: self.jd[code_addr] = jumpdests(code)
        if code is not None and code_addr not in self.jd: self.jd[code_addr] = jumpdests(code)
        if code is not None and len(code) == 0: code = None
        if code is None:
            if code_addr == 5:
                d = bytes(data); bl, el, ml = (int.from_bytes(d[i:i + 32].ljust(32, b'\0'), 'big') for i in (0, 32, 64))
                if self.ctx.get('osaka') and max(bl, el, ml) > 1024: self.restore(snap); return False, b''
                rest = d[96:].ljust(bl + el + ml, b'\0'); b = int.from_bytes(rest[:bl], 'big'); e = int.from_bytes(rest[bl:bl + el], 'big'); m = int.from_bytes(rest[bl + el:bl + el + ml], 'big')
                return True, (pow(b, e, m) if m else 0).to_bytes(ml, 'big') if ml else b''
            if code_addr == 2: return True, hashlib.sha256(data).digest()
            if code_addr == 4: return True, bytes(data)
            if code_addr == 1:
                return True, ecrecover(bytes(data))
            if 0 < code_addr < 0x12 or code_addr == 0x100: raise NotImplementedError(f'precompile {code_addr:#x}')
            return True, b''
        try:
            if storage_addr is not None: value = self.__dict__.pop('_dv', 0)
            ok, ret = self.run(code_addr, to if storage_addr is None else storage_addr, caller, value, data, static, depth)
        except Halt:
            ok, ret = False, b''
        if not ok: self.restore(snap)
        return ok, ret

    def run(self, code_addr, me, caller, value, data, static, depth):
        code = self.codes[code_addr]; jd = self.jd[code_addr]; n = len(code)
        st = []; mem = bytearray(); pc = 0; rd = b''
        cov = self.cover.setdefault(code_addr, set()); ops = self.ops; trace = self.trace

        def ext(off, size):
            if size == 0: return
            if off + size > (1 << 24): raise Halt('memory too large')  # 16 MB: no call with the gas a node grants gets this far
            need = (off + size + 31) // 32 * 32
            if need > len(mem): mem.extend(bytes(need - len(mem)))

        while True:
            if pc >= n: return True, b''
            op = code[pc]
            self.steps += 1
            if self.max_steps and self.steps > self.max_steps: raise TimeoutError('step limit')
            cov.add(pc); ops[op] = ops.get(op, 0) + 1
            if trace is not None: trace.append((depth, pc, op, tuple(st[-self.trace_stack:]) if self.trace_stack else None))
            try:
                if 0x60 <= op <= 0x7f:
                    if len(st) >= 1024: raise Halt('stack overflow')
                    k = op - 0x5f; st.append(int.from_bytes(code[pc + 1:pc + 1 + k].ljust(k, b'\0'), 'big')); pc += k + 1; continue
                if 0x80 <= op <= 0x8f:
                    if len(st) >= 1024: raise Halt('stack overflow')
                    st.append(st[-(op - 0x7f)]); pc += 1; continue
                if 0x90 <= op <= 0x9f:
                    k = op - 0x8e; st[-1], st[-k] = st[-k], st[-1]; pc += 1; continue
                if op == 0x5b: pc += 1; continue
                if op == 0x50: st.pop(); pc += 1; continue
                if op == 0x5f:
                    if len(st) >= 1024: raise Halt('stack overflow')
                    st.append(0); pc += 1; continue
                if op == 0x01: a = st.pop(); st[-1] = (a + st[-1]) & MASK
                elif op == 0x02: a = st.pop(); st[-1] = (a * st[-1]) & MASK
                elif op == 0x03: a = st.pop(); st[-1] = (a - st[-1]) & MASK
                elif op == 0x04: a = st.pop(); b = st[-1]; st[-1] = a // b if b else 0
                elif op == 0x05: a = st.pop(); st[-1] = ref_sdiv(a, st[-1])
                elif op == 0x06: a = st.pop(); b = st[-1]; st[-1] = a % b if b else 0
                elif op == 0x07: a = st.pop(); st[-1] = ref_smod(a, st[-1])
                elif op == 0x08: a = st.pop(); b = st.pop(); c = st[-1]; st[-1] = (a + b) % c if c else 0
                elif op == 0x09: a = st.pop(); b = st.pop(); c = st[-1]; st[-1] = (a * b) % c if c else 0
                elif op == 0x0a: a = st.pop(); st[-1] = pow(a, st[-1], M)
                elif op == 0x0b: a = st.pop(); st[-1] = ref_signextend(a, st[-1])
                elif op == 0x10: a = st.pop(); st[-1] = int(a < st[-1])
                elif op == 0x11: a = st.pop(); st[-1] = int(a > st[-1])
                elif op == 0x12: a = st.pop(); b = st[-1]; st[-1] = int((a - M if a & SIGN else a) < (b - M if b & SIGN else b))
                elif op == 0x13: a = st.pop(); b = st[-1]; st[-1] = int((a - M if a & SIGN else a) > (b - M if b & SIGN else b))
                elif op == 0x14: a = st.pop(); st[-1] = int(a == st[-1])
                elif op == 0x15: st[-1] = int(st[-1] == 0)
                elif op == 0x16: a = st.pop(); st[-1] &= a
                elif op == 0x17: a = st.pop(); st[-1] |= a
                elif op == 0x18: a = st.pop(); st[-1] ^= a
                elif op == 0x19: st[-1] ^= MASK
                elif op == 0x1a: a = st.pop(); st[-1] = ref_byte(a, st[-1])
                elif op == 0x1b: a = st.pop(); st[-1] = (st[-1] << a) & MASK if a < 256 else 0
                elif op == 0x1c: a = st.pop(); st[-1] = st[-1] >> a if a < 256 else 0
                elif op == 0x1d: a = st.pop(); st[-1] = ref_sar(a, st[-1])
                elif op == 0x20:
                    off = st.pop(); size = st.pop(); ext(off, size); st.append(int.from_bytes(keccak(bytes(mem[off:off + size])), 'big'))
                elif op == 0x30: st.append(me)
                elif op == 0x32: st.append(self.ctx['origin'])
                elif op == 0x3a: st.append(self.ctx['gasprice'])
                elif op == 0x41: st.append(self.ctx['coinbase'])
                elif op == 0x42: st.append(self.ctx['timestamp'])
                elif op == 0x43: st.append(self.ctx['number'])
                elif op == 0x44: st.append(self.ctx['prevrandao'])
                elif op == 0x45: st.append(self.ctx['gaslimit'])
                elif op == 0x46: st.append(self.ctx['chainid'])
                elif op == 0x48: st.append(self.ctx['basefee'])
                elif op == 0x4a: st.append(self.ctx.get('blobbasefee', 1))
                elif op == 0x3f:
                    a = st.pop() & ((1 << 160) - 1); c = self.codes.get(a)
                    empty = not c and self.balances.get(a, 0) == 0 and self.ctx.get('nonces', {}).get(a, 0) == 0
                    st.append(0 if empty else int.from_bytes(keccak(c or b''), 'big'))
                elif op == 0x3c:
                    a = st.pop() & ((1 << 160) - 1); d = st.pop(); off = st.pop(); size = st.pop(); ext(d, size); c = self.codes.get(a, b'')
                    if size: mem[d:d + size] = (c[off:off + size] if off < len(c) else b'').ljust(size, b'\0')
                elif op == 0x31: st.append(self.balances.get(st.pop() & ((1 << 160) - 1), 0))
                elif op == 0x33: st.append(caller)
                elif op == 0x34: st.append(value)
                elif op == 0x35:
                    off = st.pop(); st.append(int.from_bytes(data[off:off + 32].ljust(32, b'\0'), 'big') if off < len(data) else 0)
                elif op == 0x36: st.append(len(data))
                elif op == 0x37:
                    d = st.pop(); off = st.pop(); size = st.pop(); ext(d, size)
                    if size: mem[d:d + size] = (data[off:off + size] if off < len(data) else b'').ljust(size, b'\0')
                elif op == 0x38: st.append(n)
                elif op == 0x39:
                    d = st.pop(); off = st.pop(); size = st.pop(); ext(d, size)
                    if size: mem[d:d + size] = (code[off:off + size] if off < n else b'').ljust(size, b'\0')
                elif op == 0x3b: st.append(len(self.codes.get(st.pop() & ((1 << 160) - 1), b'')))
                elif op == 0x3d: st.append(len(rd))
                elif op == 0x3e:
                    d = st.pop(); off = st.pop(); size = st.pop()
                    if off + size > len(rd): raise Halt('return data out of bounds')
                    ext(d, size)
                    if size: mem[d:d + size] = rd[off:off + size]
                elif op == 0x47: st.append(self.balances.get(me, 0))
                elif op == 0x51:
                    off = st.pop(); ext(off, 32); st.append(int.from_bytes(mem[off:off + 32], 'big'))
                elif op == 0x52:
                    off = st.pop(); v = st.pop(); ext(off, 32); mem[off:off + 32] = v.to_bytes(32, 'big')
                elif op == 0x53:
                    off = st.pop(); v = st.pop(); ext(off, 1); mem[off] = v & 0xff
                elif op == 0x54: st.append(self.storage.get((me, st.pop()), 0))
                elif op == 0x55:
                    if static: raise Halt('write in static context')
                    k = st.pop(); self.storage[(me, k)] = st.pop()
                elif op == 0x56:
                    d = st.pop()
                    if d not in jd: raise Halt('bad jump')
                    pc = d; continue
                elif op == 0x57:
                    d = st.pop(); c = st.pop()
                    self.branches.setdefault((code_addr, pc), set()).add(bool(c))
                    if c:
                        if d not in jd: raise Halt('bad jump')
                        pc = d; continue
                elif op == 0x58: st.append(pc)
                elif op == 0x59: st.append(len(mem))
                elif op == 0x5a:  # gas is not modelled: an approximate, decreasing remaining gas when the replay sets 'gas', else the original constant
                    g = self.ctx.get('gas')
                    st.append(max(1, int(g * (63 / 64) ** depth) - 6 * self.steps) if g else 10 ** 9)
                elif op == 0x5c: st.append(self.transient.get((me, st.pop()), 0))
                elif op == 0x5d:
                    if static: raise Halt('write in static context')
                    k = st.pop(); self.transient[(me, k)] = st.pop()
                elif op == 0x5e:
                    d = st.pop(); src = st.pop(); size = st.pop(); ext(max(d, src), size)
                    if size: mem[d:d + size] = bytes(mem[src:src + size])
                elif 0xa0 <= op <= 0xa4:
                    if static: raise Halt('log in static context')
                    off = st.pop(); size = st.pop(); ext(off, size)
                    tp = tuple(st.pop() for _ in range(op - 0xa0))
                    self.logs.append((me, tp, bytes(mem[off:off + size])))
                elif op in (0xf1, 0xfa, 0xf4):
                    st.pop(); to = st.pop() & ((1 << 160) - 1)
                    val = st.pop() if op == 0xf1 else 0
                    io = st.pop(); isz = st.pop(); oo = st.pop(); osz = st.pop()
                    ext(io, isz); ext(oo, osz)
                    if val and static: raise Halt('value in static context')
                    arg = bytes(mem[io:io + isz])
                    if depth >= 1024: ok, rd = False, b''
                    elif op == 0xf1: ok, rd = self.call(me, to, val, arg, static, depth + 1)
                    elif op == 0xfa: ok, rd = self.call(me, to, 0, arg, True, depth + 1)
                    else:  # DELEGATECALL keeps the caller and the apparent value of this frame and moves no value
                        self._dv = value; ok, rd = self.call(caller, me, 0, arg, static, depth + 1, code_addr=to, storage_addr=me)
                    k = min(osz, len(rd))
                    if k: mem[oo:oo + k] = rd[:k]
                    st.append(int(ok))
                elif op == 0xf3:
                    off = st.pop(); size = st.pop(); ext(off, size); return True, bytes(mem[off:off + size])
                elif op == 0xfd:
                    off = st.pop(); size = st.pop(); ext(off, size); return False, bytes(mem[off:off + size])
                elif op == 0x00: return True, b''
                elif op == 0xfe: raise Halt('invalid')
                else: raise NotImplementedError(f'opcode {op:#x} ({NAMES.get(op, "?")}) at pc {pc} of {code_addr:#x}')
            except IndexError:
                raise Halt('stack underflow')
            if len(st) > 1024: raise Halt('stack overflow')
            pc += 1


# secp256k1 public key recovery for the ecrecover precompile (address 1), written from SEC 1 section 4.1.6
_P = 2**256 - 2**32 - 977
_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
_G = (0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798, 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8)


def _add(p, q):
    if p is None: return q
    if q is None: return p
    if p[0] == q[0] and (p[1] + q[1]) % _P == 0: return None
    if p == q: l = 3 * p[0] * p[0] * pow(2 * p[1], -1, _P) % _P
    else: l = (q[1] - p[1]) * pow(q[0] - p[0], -1, _P) % _P
    x = (l * l - p[0] - q[0]) % _P
    return (x, (l * (p[0] - x) - p[1]) % _P)


def _mul(k, p):
    r = None
    while k:
        if k & 1: r = _add(r, p)
        p = _add(p, p); k >>= 1
    return r


def ecrecover(d):
    d = d[:128].ljust(128, b'\0')
    h, v, r, s = (int.from_bytes(d[i:i + 32], 'big') for i in (0, 32, 64, 96))
    if v not in (27, 28) or not (0 < r < _N) or not (0 < s < _N): return b''
    y2 = (pow(r, 3, _P) + 7) % _P; y = pow(y2, (_P + 1) // 4, _P)
    if y * y % _P != y2: return b''
    if (y & 1) != (v - 27): y = _P - y
    ri = pow(r, -1, _N)
    q = _add(_mul((-h * ri) % _N, _G), _mul(s * ri % _N, (r, y)))
    if q is None: return b''
    return keccak(q[0].to_bytes(32, 'big') + q[1].to_bytes(32, 'big'))[12:].rjust(32, b'\0')
