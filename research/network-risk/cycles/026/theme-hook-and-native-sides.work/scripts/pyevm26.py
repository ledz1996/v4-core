# Copy of cycles/025/theme-unexecuted-sides.work/scripts/pyevm_cov.py with empty-input precompile answers added (cycle 26).
"""Copy of tools/opdiff/pyevm.py with two hooks added for cycle 24 (branch counts per side, operand watch points).
A small reference EVM in Python, written from the Ethereum execution specification
for the Cancun instruction set, without gas. It exists so that the PoolManager
bytecode can be run instruction by instruction under the specified semantics, with
no client involved, and compared with what the networks return (bytecode.py).

Not implemented: gas (GAS returns a constant and nothing runs out), CREATE, CREATE2,
SELFDESTRUCT, EXTCODECOPY, BLOCKHASH, blob opcodes and the precompiles other than
ecrecover on malformed input (empty result), SHA-256 and identity. Reaching anything
else raises, so a run cannot silently depend on it."""
import hashlib
import sys; sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
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
        self.bcount = {}; self.watch = set(); self.watch_addr = None; self.watch_cb = None

    def snapshot(self): return (dict(self.storage), dict(self.transient), dict(self.balances), self.logs)
    def restore(self, snap): self.storage, self.transient, self.balances, self.logs = snap

    def call(self, caller, to, value, data, static, depth, code_addr=None, storage_addr=None, apparent=None):
        """Returns (success, returndata). apparent is the CALLVALUE a DELEGATECALL frame inherits; nothing is transferred for it."""
        snap = self.snapshot()
        if value:
            if self.balances.get(caller, 0) < value: return False, b''
            self.balances[caller] -= value; self.balances[to] = self.balances.get(to, 0) + value
        code_addr = to if code_addr is None else code_addr
        code = self.codes.get(code_addr)
        if code is None:
            if code_addr == 2: return True, hashlib.sha256(data).digest()
            if code_addr == 4: return True, bytes(data)
            if code_addr == 1:
                if int.from_bytes(bytes(data[:128]).ljust(128, b'\0')[32:64], 'big') in (27, 28): raise NotImplementedError('ecrecover with a well formed input')
                return True, b''
            # cycle 26: precompiles on empty or short input, as Ethereum (Prague and Osaka rules) answers them. Only
            # success and returned length matter to the PoolManager's native payout (Currency.sol:48-52).
            if code_addr in (3, 5, 0x100): return True, b''
            if code_addr == 6 or code_addr == 7:
                if len(data) == 0: return True, bytes(64)
                raise NotImplementedError(f'precompile {code_addr:#x} with input')
            if code_addr == 8:
                if len(data) == 0: return True, (1).to_bytes(32, 'big')
                raise NotImplementedError('pairing with input')
            if 9 <= code_addr <= 0x11:
                if len(data) == 0:
                    self.balances[to] = self.balances.get(to, 0)
                    self.restore(snap); return False, b''
                raise NotImplementedError(f'precompile {code_addr:#x} with input')
            return True, b''
        try:
            ok, ret = self.run(code_addr, to if storage_addr is None else storage_addr, caller, value if apparent is None else apparent, data, static, depth)
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
            if code_addr == self.watch_addr and pc in self.watch: self.watch_cb(pc, op, st)
            if trace is not None: trace.append((depth, pc, op, tuple(st[-self.trace_stack:]) if self.trace_stack else None))
            try:
                if 0x60 <= op <= 0x7f:
                    k = op - 0x5f; st.append(int.from_bytes(code[pc + 1:pc + 1 + k].ljust(k, b'\0'), 'big')); pc += k + 1
                    if len(st) > 1024: raise Halt('stack overflow')
                    continue
                if 0x80 <= op <= 0x8f:
                    st.append(st[-(op - 0x7f)]); pc += 1
                    if len(st) > 1024: raise Halt('stack overflow')
                    continue
                if 0x90 <= op <= 0x9f:
                    k = op - 0x8e; st[-1], st[-k] = st[-k], st[-1]; pc += 1; continue
                if op == 0x5b: pc += 1; continue
                if op == 0x50: st.pop(); pc += 1; continue
                if op == 0x5f:
                    st.append(0); pc += 1
                    if len(st) > 1024: raise Halt('stack overflow')
                    continue
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
                    k_=(code_addr, pc, bool(c)); self.bcount[k_] = self.bcount.get(k_, 0) + 1
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
                    for _ in range(op - 0xa0): st.pop()
                    self.logs += 1
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
                    else: ok, rd = self.call(caller, me, 0, arg, static, depth + 1, code_addr=to, storage_addr=me, apparent=value)
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
