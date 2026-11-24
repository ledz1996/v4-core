"""Shared pieces of the opcode differential: a small assembler, the reference
semantics of the EVM opcodes as the Ethereum specification defines them, and a
JSON-RPC helper. Read-only: everything runs through eth_call with a state
override, nothing is deployed and no transaction is sent."""
import json, ssl, urllib.request, hashlib, time

M = 1 << 256
MASK = M - 1
SIGN = 1 << 255

OPC = {
    'STOP': 0x00, 'ADD': 0x01, 'MUL': 0x02, 'SUB': 0x03, 'DIV': 0x04, 'SDIV': 0x05, 'MOD': 0x06, 'SMOD': 0x07,
    'ADDMOD': 0x08, 'MULMOD': 0x09, 'EXP': 0x0a, 'SIGNEXTEND': 0x0b,
    'LT': 0x10, 'GT': 0x11, 'SLT': 0x12, 'SGT': 0x13, 'EQ': 0x14, 'ISZERO': 0x15, 'AND': 0x16, 'OR': 0x17,
    'XOR': 0x18, 'NOT': 0x19, 'BYTE': 0x1a, 'SHL': 0x1b, 'SHR': 0x1c, 'SAR': 0x1d, 'KECCAK256': 0x20,
    'CALLDATALOAD': 0x35, 'CALLDATASIZE': 0x36, 'CALLDATACOPY': 0x37, 'RETURNDATASIZE': 0x3d,
    'POP': 0x50, 'MLOAD': 0x51, 'MSTORE': 0x52, 'MSTORE8': 0x53, 'SLOAD': 0x54, 'SSTORE': 0x55,
    'JUMP': 0x56, 'JUMPI': 0x57, 'PC': 0x58, 'MSIZE': 0x59, 'GAS': 0x5a, 'JUMPDEST': 0x5b,
    'TLOAD': 0x5c, 'TSTORE': 0x5d, 'MCOPY': 0x5e, 'PUSH0': 0x5f,
    'RETURNDATACOPY': 0x3e, 'ADDRESS': 0x30, 'CALLER': 0x33, 'CALLVALUE': 0x34, 'SELFBALANCE': 0x47,
    'CALL': 0xf1, 'CALLCODE': 0xf2, 'DELEGATECALL': 0xf4, 'STATICCALL': 0xfa,
    'RETURN': 0xf3, 'REVERT': 0xfd, 'INVALID': 0xfe,
}
for i in range(1, 17):
    OPC[f'DUP{i}'] = 0x7f + i
    OPC[f'SWAP{i}'] = 0x8f + i


def assemble(prog):
    """prog: list of mnemonics, ('PUSH', int) / ('PUSHN', n, int), ('LABEL', name), ('REF', name), ('RAW', bytes).
    ('REF', name) becomes PUSH2 <offset>. ('LABEL', name) becomes a JUMPDEST."""
    out = bytearray(); labels = {}; refs = []
    for it in prog:
        if isinstance(it, str):
            out.append(OPC[it])
        elif it[0] == 'PUSH':
            v = it[1] & MASK
            n = max(1, (v.bit_length() + 7) // 8)
            out.append(0x5f + n); out += v.to_bytes(n, 'big')
        elif it[0] == 'PUSHN':
            n, v = it[1], it[2] & MASK
            out.append(0x5f + n); out += v.to_bytes(n, 'big')
        elif it[0] == 'LABEL':
            labels[it[1]] = len(out); out.append(0x5b)
        elif it[0] == 'REF':
            out.append(0x61); refs.append((len(out), it[1])); out += b'\0\0'
        elif it[0] == 'RAW':
            out += it[1]
        else:
            raise ValueError(it)
    for pos, name in refs:
        out[pos:pos + 2] = labels[name].to_bytes(2, 'big')
    return bytes(out)


def s(x):
    return x - M if x & SIGN else x


def u(x):
    return x & MASK


def keccak(data: bytes) -> bytes:
    return _keccak256(data)


# --- reference semantics (Ethereum execution specification) -----------------
def ref_sdiv(a, b):
    if b == 0: return 0
    sa, sb = s(a), s(b)
    q = abs(sa) // abs(sb)
    return u(-q if (sa < 0) != (sb < 0) else q)


def ref_smod(a, b):
    if b == 0: return 0
    sa, sb = s(a), s(b)
    r = abs(sa) % abs(sb)
    return u(-r if sa < 0 else r)


def ref_signextend(i, x):
    if i >= 31: return x
    bit = 8 * i + 7
    m = (1 << bit) - 1
    return (x | (MASK ^ m)) if (x >> bit) & 1 else (x & m)


def ref_byte(i, x):
    return 0 if i >= 32 else (x >> (8 * (31 - i))) & 0xff


def ref_sar(sh, x):
    if sh >= 256: return MASK if x & SIGN else 0
    return u(s(x) >> sh)


REF = {
    'ADD': lambda a, b, c: (a + b) & MASK,
    'MUL': lambda a, b, c: (a * b) & MASK,
    'SUB': lambda a, b, c: (a - b) & MASK,
    'DIV': lambda a, b, c: a // b if b else 0,
    'SDIV': lambda a, b, c: ref_sdiv(a, b),
    'MOD': lambda a, b, c: a % b if b else 0,
    'SMOD': lambda a, b, c: ref_smod(a, b),
    'ADDMOD': lambda a, b, c: (a + b) % c if c else 0,
    'MULMOD': lambda a, b, c: (a * b) % c if c else 0,
    'EXP': lambda a, b, c: pow(a, b, M),
    'SIGNEXTEND': lambda a, b, c: ref_signextend(a, b),
    'LT': lambda a, b, c: int(a < b),
    'GT': lambda a, b, c: int(a > b),
    'SLT': lambda a, b, c: int(s(a) < s(b)),
    'SGT': lambda a, b, c: int(s(a) > s(b)),
    'EQ': lambda a, b, c: int(a == b),
    'ISZERO': lambda a, b, c: int(a == 0),
    'AND': lambda a, b, c: a & b,
    'OR': lambda a, b, c: a | b,
    'XOR': lambda a, b, c: a ^ b,
    'NOT': lambda a, b, c: a ^ MASK,
    'BYTE': lambda a, b, c: ref_byte(a, b),
    'SHL': lambda a, b, c: (b << a) & MASK if a < 256 else 0,
    'SHR': lambda a, b, c: b >> a if a < 256 else 0,
    'SAR': lambda a, b, c: ref_sar(a, b),
}
ARITY = {'ISZERO': 1, 'NOT': 1, 'ADDMOD': 3, 'MULMOD': 3}


# --- keccak-256 (pure python, so the reference needs no extra package) ------
_RC = [0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000, 0x000000000000808B,
       0x0000000080000001, 0x8000000080008081, 0x8000000000008009, 0x000000000000008A, 0x0000000000000088,
       0x0000000080008009, 0x000000008000000A, 0x000000008000808B, 0x800000000000008B, 0x8000000000008089,
       0x8000000000008003, 0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
       0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008]
_ROT = [[0, 36, 3, 41, 18], [1, 44, 10, 45, 2], [62, 6, 43, 15, 61], [28, 55, 25, 21, 56], [27, 20, 39, 8, 14]]
_M64 = (1 << 64) - 1


def _f(a):
    for rc in _RC:
        c = [a[x][0] ^ a[x][1] ^ a[x][2] ^ a[x][3] ^ a[x][4] for x in range(5)]
        d = [c[(x - 1) % 5] ^ (((c[(x + 1) % 5] << 1) | (c[(x + 1) % 5] >> 63)) & _M64) for x in range(5)]
        a = [[a[x][y] ^ d[x] for y in range(5)] for x in range(5)]
        b = [[0] * 5 for _ in range(5)]
        for x in range(5):
            for y in range(5):
                r = _ROT[x][y]; v = a[x][y]
                b[y][(2 * x + 3 * y) % 5] = ((v << r) | (v >> (64 - r))) & _M64 if r else v
        a = [[b[x][y] ^ ((~b[(x + 1) % 5][y]) & b[(x + 2) % 5][y]) for y in range(5)] for x in range(5)]
        a[0][0] ^= rc
    return a


def _keccak256(data: bytes) -> bytes:
    rate = 136
    p = bytearray(data); p.append(0x01)
    while len(p) % rate: p.append(0)
    p[-1] |= 0x80
    a = [[0] * 5 for _ in range(5)]
    for off in range(0, len(p), rate):
        blk = p[off:off + rate]
        for i in range(rate // 8):
            a[i % 5][i // 5] ^= int.from_bytes(blk[8 * i:8 * i + 8], 'little')
        a = _f(a)
    out = b''
    for i in range(4):
        out += a[i % 5][i // 5].to_bytes(8, 'little')
    return out


assert _keccak256(b'').hex() == 'c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470'

# --- JSON-RPC ----------------------------------------------------------------
_ctx = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
STUB = '0x00000000000000000000000000000000000c0de5'


def rpc(url, method, params, timeout=60):
    req = urllib.request.Request(url, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}).encode(),
                                 headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
    with urllib.request.urlopen(req, timeout=timeout, context=_ctx) as r:
        j = json.load(r)
    if 'error' in j:
        raise RuntimeError(json.dumps(j['error'])[:300])
    return j['result']


def call_code(url, code: bytes, data: bytes = b'', gas=None, block='latest', retries=3):
    tx = {'to': STUB, 'data': '0x' + data.hex()}
    if gas: tx['gas'] = hex(gas)
    last = None
    for k in range(retries):
        try:
            return bytes.fromhex(rpc(url, 'eth_call', [tx, block, {STUB: {'code': '0x' + code.hex()}}])[2:])
        except Exception as e:  # noqa
            last = e; time.sleep(1.5 * (k + 1))
    raise last


import os


def networks(path=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'state', 'networks.json')):
    return [(n['chainId'], n['name'], n['rpc']) for n in json.load(open(path))['networks']]
