"""Cycle 13 copy of tools/opdiff/pyevm.py for whole-transaction reruns of mined transactions.
Added: storage, code and balances read lazily from a base state (prestate of the transaction),
LOG capture with rollback, block and transaction environment opcodes, EXTCODEHASH, EXTCODECOPY,
BLOCKHASH from a supplied table, ecrecover in pure Python, and a record of every frame into a
watched address. The arithmetic, jump and memory semantics are unchanged.

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
        self.logs = 0

    base = None; env = None; watch = None; frames = None; loglist = None; calllog = None; oog = None; forced = 0
    def snapshot(self): return (dict(self.storage), dict(self.transient), dict(self.balances), len(self.loglist) if self.loglist is not None else 0)
    def restore(self, snap):
        self.storage, self.transient, self.balances, n = snap
        if self.loglist is not None: del self.loglist[n:]
    def sload(self, me, k):
        if (me, k) in self.storage: return self.storage[(me, k)]
        return self.base.storage(me, k)
    def bal(self, a):
        if a in self.balances: return self.balances[a]
        return self.base.balance(a)
    def code_of(self, a):
        if a not in self.codes:
            c = self.base.code(a)
            self.codes[a] = c if c else None
            if c: self.jd[a] = jumpdests(c)
        return self.codes[a]

    def call(self, caller, to, value, data, static, depth, code_addr=None, storage_addr=None):
        """Returns (success, returndata)."""
        snap = self.snapshot()
        rec = None
        if self.oog is not None:
            q = self.oog.get(((code_addr if code_addr is not None else to), bytes(data)))
            if q:
                if q.pop(0):
                    self.forced += 1
                    if self.watch is not None and to == self.watch and code_addr is None: self.frames.append({'input': bytes(data), 'value': value, 'ok': False, 'ret': b'', 'forced': True})
                    return False, b''
        if self.watch is not None and to == self.watch and code_addr is None:
            rec = {'input': bytes(data), 'value': value, 'caller': caller, 'depth': depth}; self.frames.append(rec)
        if value:
            if self.bal(caller) < value:
                if rec is not None: rec.update(ok=False, ret=b'')
                return False, b''
            self.balances[caller] = self.bal(caller) - value; self.balances[to] = self.bal(to) + value
        code_addr = to if code_addr is None else code_addr
        code = self.code_of(code_addr)
        if code is not None and len(code) == 23 and code[:3] == b'\xef\x01\x00':
            code_addr = int.from_bytes(code[3:], 'big'); code = self.code_of(code_addr)
        if code is None:
            if code_addr == 1:
                if rec is not None: rec.update(ok=True, ret=b'')
                return True, ecrecover(data)
            if code_addr in (5,) : raise NotImplementedError('modexp')
            if code_addr == 2: return True, hashlib.sha256(data).digest()
            if code_addr == 4: return True, bytes(data)
            if code_addr == 1:
                if len(data) >= 128 and int.from_bytes(data[32:64], 'big') in (27, 28): raise NotImplementedError('ecrecover with a well formed input')
                return True, b''
            if 0 < code_addr < 0x12 or code_addr == 0x100: raise NotImplementedError(f'precompile {code_addr:#x}')
            return True, b''
        try:
            ok, ret = self.run(code_addr, to if storage_addr is None else storage_addr, caller, value, data, static, depth)
        except Halt:
            ok, ret = False, b''
        if not ok: self.restore(snap)
        if rec is not None: rec.update(ok=ok, ret=ret)
        if self.calllog is not None: self.calllog.append((depth, '0x%040x' % to, '0x%040x' % code_addr, bytes(data[:4]).hex(), ok, ret[:68].hex()))
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
                    k = op - 0x5f; st.append(int.from_bytes(code[pc + 1:pc + 1 + k].ljust(k, b'\0'), 'big')); pc += k + 1; continue
                if 0x80 <= op <= 0x8f:
                    st.append(st[-(op - 0x7f)]); pc += 1; continue
                if 0x90 <= op <= 0x9f:
                    k = op - 0x8e; st[-1], st[-k] = st[-k], st[-1]; pc += 1; continue
                if op == 0x5b: pc += 1; continue
                if op == 0x50: st.pop(); pc += 1; continue
                if op == 0x5f: st.append(0); pc += 1; continue
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
                elif op == 0x31: st.append(self.bal(st.pop() & ((1 << 160) - 1)))
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
                elif op == 0x3b: st.append(len(self.code_of(st.pop() & ((1 << 160) - 1)) or b''))
                elif op == 0x3d: st.append(len(rd))
                elif op == 0x3e:
                    d = st.pop(); off = st.pop(); size = st.pop()
                    if off + size > len(rd): raise Halt('return data out of bounds')
                    ext(d, size)
                    if size: mem[d:d + size] = rd[off:off + size]
                elif op == 0x47: st.append(self.bal(me))
                elif op == 0x51:
                    off = st.pop(); ext(off, 32); st.append(int.from_bytes(mem[off:off + 32], 'big'))
                elif op == 0x52:
                    off = st.pop(); v = st.pop(); ext(off, 32); mem[off:off + 32] = v.to_bytes(32, 'big')
                elif op == 0x53:
                    off = st.pop(); v = st.pop(); ext(off, 1); mem[off] = v & 0xff
                elif op == 0x54: st.append(self.sload(me, st.pop()))
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
                elif op == 0x5a: st.append(10 ** 9)
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
                    tps = [st.pop() for _ in range(op - 0xa0)]
                    self.logs += 1
                    if self.loglist is not None: self.loglist.append((me, tuple(tps), bytes(mem[off:off + size])))
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
                    else: ok, rd = self.call(caller, me, 0, arg, static, depth + 1, code_addr=to, storage_addr=me)
                    k = min(osz, len(rd))
                    if k: mem[oo:oo + k] = rd[:k]
                    st.append(int(ok))
                elif op == 0xf3:
                    off = st.pop(); size = st.pop(); ext(off, size); return True, bytes(mem[off:off + size])
                elif op == 0xfd:
                    off = st.pop(); size = st.pop(); ext(off, size); return False, bytes(mem[off:off + size])
                elif op == 0x00: return True, b''
                elif op == 0x32: st.append(self.env['origin'])
                elif op == 0x3a: st.append(self.env['gasprice'])
                elif op == 0x41: st.append(self.env['coinbase'])
                elif op == 0x42: st.append(self.env['timestamp'])
                elif op == 0x43: st.append(self.env['number'])
                elif op == 0x44: st.append(self.env['prevrandao'])
                elif op == 0x45: st.append(self.env['gaslimit'])
                elif op == 0x46: st.append(self.env['chainid'])
                elif op == 0x48: st.append(self.env['basefee'])
                elif op == 0x4a: st.append(self.env.get('blobbasefee', 1))
                elif op == 0x40:
                    bn = st.pop(); h = self.env['blockhash'](bn)
                    st.append(h)
                elif op == 0x3f:
                    a = st.pop() & ((1 << 160) - 1); c = self.code_of(a)
                    if c: st.append(int.from_bytes(keccak(c), 'big'))
                    else: st.append(self.base.exthash_empty(a))
                elif op == 0x3c:
                    a = st.pop() & ((1 << 160) - 1); d = st.pop(); off = st.pop(); size = st.pop(); ext(d, size)
                    c = self.code_of(a) or b''
                    if size: mem[d:d + size] = (c[off:off + size] if off < len(c) else b'').ljust(size, b'\0')
                elif op == 0xfe: raise Halt('invalid')
                else: raise NotImplementedError(f'opcode {op:#x} ({NAMES.get(op, "?")}) at pc {pc} of {code_addr:#x}')
            except IndexError:
                raise Halt('stack underflow')
            if len(st) > 1024: raise Halt('stack overflow')
            pc += 1


# secp256k1 public key recovery, written from SEC 1 section 4.1.6; used only for the ecrecover precompile
_P = 2**256 - 2**32 - 977; _N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
_G = (0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798, 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8)
def _add(p, q):
    if p is None: return q
    if q is None: return p
    if p[0] == q[0]:
        if (p[1] + q[1]) % _P == 0: return None
        l = 3 * p[0] * p[0] * pow(2 * p[1], -1, _P) % _P
    else: l = (q[1] - p[1]) * pow(q[0] - p[0], -1, _P) % _P
    x = (l * l - p[0] - q[0]) % _P
    return (x, (l * (p[0] - x) - p[1]) % _P)
def _mul(p, k):
    r = None
    while k:
        if k & 1: r = _add(r, p)
        p = _add(p, p); k >>= 1
    return r
def ecrecover(data):
    d = bytes(data).ljust(128, b'\0')
    h = int.from_bytes(d[0:32], 'big'); v = int.from_bytes(d[32:64], 'big'); r = int.from_bytes(d[64:96], 'big'); s_ = int.from_bytes(d[96:128], 'big')
    if v not in (27, 28) or not (0 < r < _N) or not (0 < s_ < _N): return b''
    x = r; y2 = (pow(x, 3, _P) + 7) % _P; y = pow(y2, (_P + 1) // 4, _P)
    if y * y % _P != y2: return b''
    if (y & 1) != (v - 27): y = _P - y
    R = (x, y); ri = pow(r, -1, _N)
    Q = _add(_mul(R, s_ * ri % _N), _mul(_G, (-h * ri) % _N))
    if Q is None: return b''
    pub = Q[0].to_bytes(32, 'big') + Q[1].to_bytes(32, 'big')
    return b'\0' * 12 + keccak(pub)[12:]
