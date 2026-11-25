"""L-587: does the node fold storage or transient slot keys (or account addresses) by a rule that needs
more than one changed bit? Writes value i+1 to each key of a list in one call, reads all back, and expects
each key to return its own value. Read-only eth_call with state override."""
import sys, json, random
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import assemble, call_code, MASK, keccak
R = random.Random(587999)
def prog(st, ld):
    p = [('PUSH', 0), ('LABEL', 'w'), 'DUP1', ('PUSH', 32), 'MUL', 'DUP1', 'CALLDATASIZE', 'GT', 'ISZERO', ('REF', 'r0'), 'JUMPI',
         'DUP2', ('PUSH', 1), 'ADD', 'SWAP1', 'CALLDATALOAD', st, ('PUSH', 1), 'ADD', ('REF', 'w'), 'JUMP',
         ('LABEL', 'r0'), 'POP', 'POP', ('PUSH', 0),
         ('LABEL', 'r'), 'DUP1', 'CALLDATASIZE', 'GT', 'ISZERO', ('REF', 'end'), 'JUMPI',
         'DUP1', 'CALLDATALOAD', ld, 'DUP2', 'MSTORE', ('PUSH', 32), 'ADD', ('REF', 'r'), 'JUMP',
         ('LABEL', 'end'), 'POP', 'CALLDATASIZE', ('PUSH', 0), 'RETURN']
    return assemble(p)
def keys():
    K = []
    for _ in range(40):
        b = R.getrandbits(256)
        K += [b, b ^ (MASK ^ ((1 << 64) - 1)), b ^ (MASK ^ ((1 << 128) - 1)), b ^ (MASK ^ ((1 << 160) - 1)), b ^ (MASK ^ ((1 << 192) - 1)),
              b ^ ((1 << 64) - 1) << 192 ^ ((1 << 64) - 1) << 128,  # two limbs flipped: xor of limbs unchanged
              b ^ (0xff << 248 | 0xff),  # top and bottom byte
              b ^ (b & ((1 << 128) - 1)) << 128 ^ (b >> 128),  # halves swapped
              int.from_bytes(int(b).to_bytes(32, 'big')[::-1], 'big'),  # byte reversed
              (b + (1 << 64)) & MASK, (b - (1 << 64) + 1) & MASK]  # limb sums shifted
    for v in (0, 1, MASK, 1 << 255, (1 << 64) - 1, 1 << 64, 1 << 128, 1 << 192, (1 << 128) - 1):
        K.append(v)
    # mapping-style keys: keccak of (k, slot) for pool ids that differ in several bits
    for _ in range(40):
        a = R.getrandbits(256); K += [int.from_bytes(keccak(a.to_bytes(32, 'big') + (6).to_bytes(32, 'big')), 'big'), a ^ 0x0101]
    out = []
    for k in K:
        k &= MASK
        if k not in out: out.append(k)
    return out
K = keys(); data = b''.join(k.to_bytes(32, 'big') for k in K)
res = {'keys': len(K), 'endpoints': {}}
for url in sys.argv[2:]:
    r = {}
    for name, st, ld in (('storage', 'SSTORE', 'SLOAD'), ('transient', 'TSTORE', 'TLOAD')):
        out = call_code(url, prog(st, ld), data, gas=0x1c9c380)
        got = [int.from_bytes(out[32 * i:32 * i + 32], 'big') for i in range(len(K))]
        bad = [(hex(K[i]), got[i], i + 1) for i in range(len(K)) if got[i] != i + 1]
        r[name] = {'returned': len(out) // 32, 'mismatch': len(bad), 'examples': bad[:5]}
    res['endpoints'][url] = r
    print(url, r, flush=True)
json.dump(res, open(sys.argv[1], 'w'), indent=1)
