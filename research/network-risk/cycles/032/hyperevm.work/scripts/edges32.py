"""Cycle 32 hyperevm: edge vectors not in the battery. Jump destination analysis (push data, truncated
PUSH at code end, high-limb destinations), RETURNDATACOPY bounds, zero-length memory operations at huge offsets,
KECCAK256 over long and rate-boundary lengths, CALLDATALOAD far past the end, EXP with high exponents.
Each vector is a child contract placed by state override; a harness CALLs every child and records the success
flag and the first returned word. Read-only eth_call. Usage: edges32.py <out.json> <url> [<url> ...]"""
import sys, os, json, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'tools', 'opdiff'))
from evm import assemble, keccak, rpc, MASK  # noqa

RET = ['PUSH0', 'MSTORE', ('PUSH', 32), 'PUSH0', 'RETURN']  # return top of stack
V = []  # (name, code bytes, expected success, expected word)


def add(name, code, ok, word=0):
    V.append((name, code, ok, word if ok else 0))


# A. jump destination analysis
add('jump-into-push1-data', bytes.fromhex('600456605b00'), 0)
c = bytearray([0x7f]) + b'\x5b' * 32 + bytes([0x60, 0x24, 0x56]) + b'\x5b' + assemble([('PUSH', 7)] + RET)
add('jump-over-push32-of-5b', bytes(c), 1, 7)
c = bytearray([0x60, 0x10, 0x56]) + bytes([0x7f]) + b'\x5b' * 32
add('jump-into-push32-data', bytes(c), 0)
add('jump-into-truncated-push2', bytes.fromhex('600656000061' + '5b'), 0)
add('jump-into-truncated-push32-tail', bytes.fromhex('600856000000007f5b5b'), 0)
add('jump-past-code-end', bytes.fromhex('60ff56'), 0)
for hi, nm in ((1 << 255, '2^255'), (1 << 64, '2^64'), (1 << 128, '2^128'), (1 << 32, '2^32'), (1 << 16, '2^16')):
    jd = 34  # PUSH32 (33 bytes), JUMP, then JUMPDEST at 34
    code = assemble([('PUSHN', 32, hi + jd), 'JUMP', 'JUMPDEST', ('PUSH', 9)] + RET)
    add(f'jump-highlimb-{nm}', code, 0)
    jd2 = 36  # PUSH1 1, PUSH32, JUMPI, JUMPDEST at 36
    assert code[jd] == 0x5b
    code = assemble([('PUSH', 1), ('PUSHN', 32, hi + jd2), 'JUMPI', 'JUMPDEST', ('PUSH', 9)] + RET)
    add(f'jumpi-taken-highlimb-{nm}', code, 0)
    code = assemble([('PUSH', 0), ('PUSHN', 32, hi + 0xffff), 'JUMPI', ('PUSH', 5)] + RET)
    add(f'jumpi-not-taken-baddest-{nm}', code, 1, 5)
add('jump-control-push32-dest34', assemble([('PUSHN', 32, 34), 'JUMP', 'JUMPDEST', ('PUSH', 9)] + RET), 1, 9)
add('jumpi-control-push32-dest36', assemble([('PUSH', 1), ('PUSHN', 32, 36), 'JUMPI', 'JUMPDEST', ('PUSH', 9)] + RET), 1, 9)
code = assemble([('PUSHN', 2, 0), 'JUMP'])  # offset 0 is a PUSH opcode, not JUMPDEST
add('jump-to-offset0-push', code, 0)
code = bytes.fromhex('5b') + assemble([('PUSH', 1), 'PUSH0', 'TLOAD', 'ADD', 'DUP1', 'PUSH0', 'TSTORE', ('PUSH', 3), 'GT', ('PUSH', 0), 'JUMPI', 'PUSH0', 'TLOAD'] + RET)
add('jumpi-loop-to-offset0-jumpdest', code, 1, 3)
# B. RETURNDATACOPY bounds
add('rdc-0-0-0-no-call', assemble([('PUSH', 0), ('PUSH', 0), ('PUSH', 0), 'RETURNDATACOPY', ('PUSH', 1)] + RET), 1, 1)
add('rdc-off1-len0-size0', assemble([('PUSH', 0), ('PUSH', 1), ('PUSH', 0), 'RETURNDATACOPY', ('PUSH', 1)] + RET), 0)
CALL4 = [('PUSH', 0x11), 'PUSH0', 'MSTORE', ('PUSH', 32), ('PUSH', 0x40), ('PUSH', 32), 'PUSH0', ('PUSH', 4), 'GAS', 'STATICCALL', 'POP']
add('rdc-after-identity-0-0-32', assemble(CALL4 + [('PUSH', 32), ('PUSH', 0), ('PUSH', 0x80), 'RETURNDATACOPY', ('PUSH', 0x80), 'MLOAD'] + RET), 1, 0x11)
add('rdc-after-identity-0-0-33', assemble(CALL4 + [('PUSH', 33), ('PUSH', 0), ('PUSH', 0x80), 'RETURNDATACOPY', ('PUSH', 1)] + RET), 0)
add('rdc-after-identity-off32-len0', assemble(CALL4 + [('PUSH', 0), ('PUSH', 32), ('PUSH', 0x80), 'RETURNDATACOPY', ('PUSH', 1)] + RET), 1, 1)
add('rdc-after-identity-off33-len0', assemble(CALL4 + [('PUSH', 0), ('PUSH', 33), ('PUSH', 0x80), 'RETURNDATACOPY', ('PUSH', 1)] + RET), 0)
add('rdc-overflow-offMAX-len2', assemble(CALL4 + [('PUSH', 2), ('PUSH', MASK), ('PUSH', 0x80), 'RETURNDATACOPY', ('PUSH', 1)] + RET), 0)
add('rdc-overflow-off1-lenMAX', assemble(CALL4 + [('PUSH', MASK), ('PUSH', 1), ('PUSH', 0x80), 'RETURNDATACOPY', ('PUSH', 1)] + RET), 0)
add('rdsize-after-identity', assemble(CALL4 + ['RETURNDATASIZE'] + RET), 1, 32)
# C. zero-length operations at huge offsets do not expand memory
for off, nm in ((1 << 200, '2^200'), (MASK, 'MAX'), (1 << 64, '2^64')):
    add(f'mcopy-len0-{nm}', assemble([('PUSH', 0), ('PUSH', off), ('PUSH', off), 'MCOPY', 'MSIZE'] + RET), 1, 0)
    add(f'keccak-len0-{nm}', assemble([('PUSH', 0), ('PUSH', off), 'KECCAK256'] + RET), 1, int.from_bytes(keccak(b''), 'big'))
    add(f'cdcopy-len0-{nm}', assemble([('PUSH', 0), ('PUSH', off), ('PUSH', off), 'CALLDATACOPY', 'MSIZE'] + RET), 1, 0)
    add(f'rdc-len0-dst-{nm}', assemble([('PUSH', 0), ('PUSH', 0), ('PUSH', off), 'RETURNDATACOPY', 'MSIZE'] + RET), 1, 0)
    add(f'cdload-{nm}', assemble([('PUSH', off), 'CALLDATALOAD'] + RET), 1, 0)
    add(f'mload-{nm}-fails', assemble([('PUSH', off), 'MLOAD'] + RET), 0)
add('msize-after-mload-1f', assemble([('PUSH', 0x1f), 'MLOAD', 'POP', 'MSIZE'] + RET), 1, 64)
add('msize-after-mstore8-40', assemble([('PUSH', 1), ('PUSH', 0x40), 'MSTORE8', 'MSIZE'] + RET), 1, 0x60)
add('mcopy-expands-dst', assemble([('PUSH', 1), ('PUSH', 0), ('PUSH', 0x100), 'MCOPY', 'MSIZE'] + RET), 1, 0x120)
add('mcopy-expands-src', assemble([('PUSH', 1), ('PUSH', 0x100), ('PUSH', 0), 'MCOPY', 'MSIZE'] + RET), 1, 0x120)
# D. KECCAK256 over long inputs and rate boundaries (136 bytes), pattern words written first
rnd = random.Random(32999)
for L, O in ((1024, 0), (1087, 1), (1088, 0), (1089, 31), (2048, 5), (4095, 0), (4096, 1), (8191, 33), (135, 0), (136, 0), (137, 0), (271, 1), (272, 0), (273, 7)):
    mem = bytearray(O + L + 64)
    prog = []
    for k in range(0, O + L, 136):
        w = rnd.getrandbits(256)
        prog += [('PUSH', w), ('PUSH', k), 'MSTORE']
        mem[k:k + 32] = w.to_bytes(32, 'big')
    prog += [('PUSH', L), ('PUSH', O), 'KECCAK256'] + RET
    add(f'keccak-L{L}-O{O}', assemble(prog), 1, int.from_bytes(keccak(bytes(mem[O:O + L])), 'big'))
# E. EXP with high exponents
for i in range(40):
    b = rnd.choice([2, 3, MASK, MASK - 1, 1 << 128, rnd.getrandbits(256), rnd.getrandbits(64), (1 << 255) + 1])
    e = rnd.choice([1 << 255, (1 << 255) + rnd.getrandbits(8), (1 << 64) + 1, (1 << 128) + 3, MASK, rnd.getrandbits(256), 256, 255, 0])
    add(f'exp-{i}', assemble([('PUSH', e), ('PUSH', b), 'EXP'] + RET), 1, pow(b, e, 1 << 256))
add('exp-0-0', assemble([('PUSH', 0), ('PUSH', 0), 'EXP'] + RET), 1, 1)
add('exp-0-MAX', assemble([('PUSH', MASK), ('PUSH', 0), 'EXP'] + RET), 1, 0)
V[:] = [v for v in V if v[0] != 'x']


def harness(n):
    # for i in 0..n-1: addr = 0xc0de0000 + i; success = CALL(gas=200_000, addr, 0, 0,0, 0,32); out[2i]=success, out[2i+1]=mload(0)
    p = [('PUSH', 0), ('LABEL', 'loop'), 'DUP1', ('PUSH', n), 'GT', 'ISZERO', ('REF', 'done'), 'JUMPI',
         'PUSH0', 'PUSH0', 'MSTORE',
         ('PUSH', 32), 'PUSH0', 'PUSH0', 'PUSH0', 'PUSH0', 'DUP6', ('PUSH', 0xc0de0000), 'ADD', ('PUSH', 200000), 'CALL',
         'DUP2', ('PUSH', 64), 'MUL', ('PUSH', 0x1000), 'ADD', 'MSTORE',
         'PUSH0', 'MLOAD', 'DUP2', ('PUSH', 64), 'MUL', ('PUSH', 0x1020), 'ADD', 'MSTORE',
         ('PUSH', 1), 'ADD', ('REF', 'loop'), 'JUMP',
         ('LABEL', 'done'), 'POP', ('PUSH', 64 * n), ('PUSH', 0x1000), 'RETURN']
    return assemble(p)


def run(url):
    ov = {'0x00000000000000000000000000000000000f0b01': {'code': '0x' + harness(len(V)).hex()}}
    for i, (_, code, _, _) in enumerate(V):
        ov['0x%040x' % (0xc0de0000 + i)] = {'code': '0x' + code.hex()}
    res = rpc(url, 'eth_call', [{'to': '0x00000000000000000000000000000000000f0b01', 'gas': hex(29_000_000)}, 'latest', ov], 120)
    b = bytes.fromhex(res[2:])
    out = []
    for i, (nm, _, ok, w) in enumerate(V):
        gs = int.from_bytes(b[64 * i:64 * i + 32], 'big'); gw = int.from_bytes(b[64 * i + 32:64 * i + 64], 'big')
        if not gs: gw = 0
        out.append({'name': nm, 'expOk': ok, 'expWord': hex(w), 'gotOk': gs, 'gotWord': hex(gw), 'match': gs == ok and gw == w})
    return out


if __name__ == '__main__':
    allres = {}
    for url in sys.argv[2:]:
        try:
            cv = rpc(url, 'web3_clientVersion', [], 30); bn = rpc(url, 'eth_blockNumber', [], 30)
            r = run(url)
            mm = [x for x in r if not x['match']]
            allres[url] = {'clientVersion': cv, 'block': bn, 'vectors': len(r), 'mismatches': len(mm), 'mismatchList': mm, 'results': r}
            print(url, cv, bn, 'vectors', len(r), 'mismatches', len(mm), [x['name'] for x in mm])
        except Exception as e:
            allres[url] = {'error': str(e)[:400]}; print(url, 'ERROR', str(e)[:400])
    json.dump(allres, open(sys.argv[1], 'w'), indent=1)
