"""Opcode battery. One small dispatcher contract is placed at an unused address by
state override. Its calldata is a list of records (opcode id, a, b, c); it runs the
named opcode on the operands, with a on top of the stack, and returns one word per
record. The words are compared with the reference semantics in evm.py.

Usage: python3 battery.py <out.json> [chainId ...]
"""
import sys, json, random, concurrent.futures as cf
from evm import *

BIN = ['ADD', 'MUL', 'SUB', 'DIV', 'SDIV', 'MOD', 'SMOD', 'EXP', 'SIGNEXTEND', 'LT', 'GT', 'SLT', 'SGT', 'EQ',
       'AND', 'OR', 'XOR', 'BYTE', 'SHL', 'SHR', 'SAR']
UNA = ['ISZERO', 'NOT']
TER = ['ADDMOD', 'MULMOD']
SPECIAL = ['JUMPI', 'KECCAK', 'MCOPY', 'CDLOAD', 'SIGNEXT_CHAIN', 'DIVUP', 'MULDIV512']
OPS = BIN + UNA + TER + SPECIAL
ID = {o: i for i, o in enumerate(OPS)}
SLOT = 32  # bytes reserved per handler in the jump table
OUT = 0x800  # results start here; 0..0x7ff is scratch


def dispatcher():
    p = [('PUSH', 0)]  # i
    p += [('LABEL', 'loop'), 'DUP1', ('PUSH', 128), 'MUL',  # off, i
          'DUP1', 'CALLDATASIZE', 'GT', 'ISZERO', ('REF', 'done'), 'JUMPI',
          'DUP1', ('PUSH', 96), 'ADD', 'CALLDATALOAD',  # c, off, i
          'DUP2', ('PUSH', 64), 'ADD', 'CALLDATALOAD',  # b, c, off, i
          'DUP3', ('PUSH', 32), 'ADD', 'CALLDATALOAD',  # a, b, c, off, i
          'DUP4', 'CALLDATALOAD',  # op, a, b, c, off, i
          ('PUSH', SLOT), 'MUL', ('REF', 'table'), 'ADD', 'JUMP']
    # shared tails: leave r on top of off, i
    p += [('LABEL', 'fin3'), ('REF', 'store'), 'JUMP']  # r, off, i
    p += [('LABEL', 'fin2'), 'SWAP1', 'POP', ('REF', 'store'), 'JUMP']  # r, c -> r
    p += [('LABEL', 'fin1'), 'SWAP2', 'POP', 'POP', ('REF', 'store'), 'JUMP']  # r, b, c -> r
    p += [('LABEL', 'store'), 'DUP3', ('PUSH', 32), 'MUL', ('PUSH', OUT), 'ADD', 'MSTORE',  # off, i
          'POP', ('PUSH', 1), 'ADD', ('REF', 'loop'), 'JUMP']
    p += [('LABEL', 'done'), 'POP', ('PUSH', 32), 'MUL', ('PUSH', OUT), 'RETURN']
    # long handlers placed before the table
    # JUMPI: result 1 if a jump with condition a is taken, else 0
    p += [('LABEL', 'h_jumpi'), ('REF', 'taken'), 'JUMPI', ('PUSH', 0), ('REF', 'fin1'), 'JUMP',  # stack after JUMPI: b, c
          ('LABEL', 'taken'), ('PUSH', 1), ('REF', 'fin1'), 'JUMP']
    # KECCAK: mstore(0,a) mstore(32,b); keccak256(c & 0xff, (c >> 8) & 0x3ff) over scratch (rest zero)
    p += [('LABEL', 'h_keccak'), ('PUSH', 0), 'MSTORE', ('PUSH', 32), 'MSTORE',  # c
          'DUP1', ('PUSH', 8), 'SHR', ('PUSH', 0x3ff), 'AND', 'SWAP1', ('PUSH', 0xff), 'AND', 'KECCAK256',
          ('PUSH', 0), ('PUSH', 0), 'MSTORE', ('PUSH', 0), ('PUSH', 32), 'MSTORE', ('REF', 'fin3'), 'JUMP']
    # MCOPY: mstore(0,a) mstore(32,b); mcopy(dst=c&0xff, src=(c>>8)&0xff, len=(c>>16)&0xff); keccak256(0,0x200); wipe
    p += [('LABEL', 'h_mcopy'), ('PUSH', 0), 'MSTORE', ('PUSH', 32), 'MSTORE',  # c
          'DUP1', ('PUSH', 16), 'SHR', ('PUSH', 0xff), 'AND',  # len, c
          'DUP2', ('PUSH', 8), 'SHR', ('PUSH', 0xff), 'AND',  # src, len, c
          'SWAP2', ('PUSH', 0xff), 'AND',  # dst, len, src  -> need dst, src, len
          'SWAP1', 'SWAP2', 'SWAP1',  # dst, src, len
          'MCOPY', ('PUSH', 0x200), ('PUSH', 0), 'KECCAK256',
          ('PUSH', 0x200), 'CALLDATASIZE', ('PUSH', 0), 'CALLDATACOPY', ('REF', 'fin3'), 'JUMP']
    # CDLOAD: calldataload(a) (a may point past the end or be huge)
    p += [('LABEL', 'h_cdload'), 'CALLDATALOAD', ('REF', 'fin1'), 'JUMP']
    # SIGNEXT_CHAIN: sar(128, signextend(15, a)) + signextend(2, shr(b & 0xff, a)), as BalanceDelta and Slot0 do
    p += [('LABEL', 'h_sxc'), 'DUP1', ('PUSH', 15), 'SIGNEXTEND', ('PUSH', 128), 'SAR',  # x, a, b, c
          'SWAP2', ('PUSH', 0xff), 'AND',  # sh, a, x, c
          'SHR', ('PUSH', 2), 'SIGNEXTEND', 'ADD', ('REF', 'fin2'), 'JUMP']
    # DIVUP: add(div(a, b), gt(mod(a, b), 0)), as UnsafeMath.divRoundingUp
    p += [('LABEL', 'h_divup'), 'DUP2', 'DUP2', 'MOD', ('PUSH', 0), 'SWAP1', 'GT',  # gt(mod,0), a, b, c
          'SWAP2', 'SWAP1', 'DIV', 'ADD', ('REF', 'fin2'), 'JUMP']
    # MULDIV512: the two halves of the 512 bit product as FullMath computes them:
    #   prod0 = mul(a,b); mm = mulmod(a,b,not(0)); prod1 = sub(sub(mm, prod0), lt(mm, prod0)); result = xor(prod1, mulmod(a,b,c)) + prod0
    p += [('LABEL', 'h_md512'), 'DUP3', 'DUP3', 'DUP3', 'MULMOD',  # r, a, b, c
          'DUP3', 'DUP3', 'MUL',  # prod0, r, a, b, c
          ('PUSH', 0), 'NOT', 'DUP5', 'DUP5', 'MULMOD',  # mm, prod0, r, a, b, c
          'DUP2', 'DUP2', 'LT',  # lt(mm,prod0), mm, prod0, r, ...
          'DUP3', 'DUP3', 'SUB', 'SUB',  # prod1, mm, prod0, r, a, b, c
          'SWAP1', 'POP',  # prod1, prod0, r, a, b, c
          'SWAP1', 'SWAP2', 'XOR', 'ADD',  # res, a, b, c
          'SWAP3', 'POP', 'POP', 'POP', ('REF', 'fin3'), 'JUMP']
    code = bytearray(assemble(p + [('LABEL', 'table')]))
    # the table: fixed size slots, each starts with JUMPDEST
    labels = {}
    def lab(name):  # recover label offsets by re-assembling with a marker
        q = p + [('LABEL', 'table'), ('REF', name)]
        b = assemble(q)
        return int.from_bytes(b[-2:], 'big')
    table_at = len(code) - 1
    code = code[:-1]
    for o in OPS:
        slot = bytearray([0x5b])
        if o in BIN:
            slot += bytes([OPC[o]]) + b'\x61' + lab('fin2').to_bytes(2, 'big') + b'\x56'
        elif o in UNA:
            slot += bytes([OPC[o]]) + b'\x61' + lab('fin1').to_bytes(2, 'big') + b'\x56'
        elif o in TER:
            slot += bytes([OPC[o]]) + b'\x61' + lab('fin3').to_bytes(2, 'big') + b'\x56'
        else:
            h = {'JUMPI': 'h_jumpi', 'KECCAK': 'h_keccak', 'MCOPY': 'h_mcopy', 'CDLOAD': 'h_cdload',
                 'SIGNEXT_CHAIN': 'h_sxc', 'DIVUP': 'h_divup', 'MULDIV512': 'h_md512'}[o]
            slot += b'\x61' + lab(h).to_bytes(2, 'big') + b'\x56'
        slot += b'\xfe' * (SLOT - len(slot))
        code += slot
    assert lab('table') == table_at
    return bytes(code)


def reference(op, a, b, c, calldata):
    if op in REF: return REF[op](a, b, c)
    if op == 'JUMPI': return int(b != 0)  # stack: dest pushed last, so condition is the old top (a) ... see below
    if op == 'KECCAK':
        mem = a.to_bytes(32, 'big') + b.to_bytes(32, 'big') + bytes(0x400)
        off, ln = c & 0xff, (c >> 8) & 0x3ff
        return int.from_bytes(keccak(mem[off:off + ln]), 'big')
    if op == 'MCOPY':
        mem = bytearray(a.to_bytes(32, 'big') + b.to_bytes(32, 'big') + bytes(0x400))
        dst, src, ln = c & 0xff, (c >> 8) & 0xff, (c >> 16) & 0xff
        mem[dst:dst + ln] = bytes(mem[src:src + ln])
        return int.from_bytes(keccak(bytes(mem[:0x200])), 'big')
    if op == 'CDLOAD':
        return int.from_bytes((calldata[a:a + 32] if a < len(calldata) else b'').ljust(32, b'\0'), 'big')
    if op == 'SIGNEXT_CHAIN':
        x = ref_sar(128, ref_signextend(15, a))
        y = ref_signextend(2, a >> (b & 0xff))
        return (x + y) & MASK
    if op == 'DIVUP':
        if b == 0: return 0
        return a // b + int(a % b > 0)
    if op == 'MULDIV512':
        prod = a * b
        r = prod % c if c else 0
        return (((prod >> 256) ^ r) + (prod & MASK)) & MASK
    raise KeyError(op)


def edge_values():
    E = [0, 1, 2, 3, 7, 8, 15, 16, 31, 32, 33, 63, 64, 65, 127, 128, 129, 255, 256, 257]
    for k in (8, 16, 23, 24, 31, 32, 63, 64, 95, 96, 127, 128, 159, 160, 191, 192, 223, 224, 247, 248, 254, 255):
        E += [(1 << k) - 1, 1 << k, (1 << k) + 1]
    E += [MASK, MASK - 1, SIGN, SIGN + 1, SIGN - 1]
    E += [u(-x) for x in (2, 3, 128, 887272, 887273, 1 << 23, 1 << 127, (1 << 127) + 1, 1 << 128, 1 << 64)]
    E += [887272, 0xF27618, 0x800000, 0x7FFFFF, 10 ** 6, 10 ** 18, 0xFFFFFF, 4295128739,
          1461446703485210103287273052203988822378723970342, 0xfffcb933bd6fad37aa2d162d1a594001,
          0x5555555555555555555555555555555555555555555555555555555555555555,
          0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa,
          0x00ff00ff00ff00ff00ff00ff00ff00ff00ff00ff00ff00ff00ff00ff00ff00ff,
          0x8000000000000000000000000000000000000000000000000000000000000001,
          0xffffffffffffffff, 0xffffffffffffffff << 64, 0xffffffffffffffff << 128, 0xffffffffffffffff << 192,
          (1 << 64) | 1, (1 << 128) | (1 << 64), 0x0706060506020500060203020504000106050205030304010505030400000000]
    seen = []
    for v in E:
        v &= MASK
        if v not in seen: seen.append(v)
    return seen


def vectors(seed=20261124):
    rnd = random.Random(seed)
    E = edge_values()
    core = [0, 1, 2, 3, 31, 32, 255, 256, (1 << 64) - 1, 1 << 64, (1 << 127), (1 << 128) - 1, 1 << 128, (1 << 128) + 1,
            1 << 160, SIGN - 1, SIGN, SIGN + 1, MASK - 1, MASK, u(-2), u(-887272), 887272, u(-(1 << 127)), 4295128739,
            1461446703485210103287273052203988822378723970342, 1 << 96, 10 ** 6, 0xFFFFFF, 0x800000, 1 << 192, (1 << 192) - 1]
    small = list(range(0, 40)) + [63, 64, 65, 127, 128, 129, 191, 192, 248, 254, 255, 256, 257, 511, 1 << 16, 1 << 32,
                                  1 << 63, 1 << 64, (1 << 64) + 1, (1 << 64) + 255, 1 << 128, (1 << 128) + 7, SIGN, MASK, (1 << 255) + 3]

    def rand():
        k = rnd.choice((8, 24, 64, 96, 128, 160, 200, 255, 256))
        v = rnd.getrandbits(k)
        return u(-v) if rnd.random() < 0.3 else v

    V = []
    for op in BIN:
        firsts = small if op in ('SIGNEXTEND', 'BYTE', 'SHL', 'SHR', 'SAR') else core
        seconds = E if op in ('SIGNEXTEND', 'BYTE', 'SHL', 'SHR', 'SAR') else core
        if op == 'EXP':
            firsts = [0, 1, 2, 3, 10, 255, 256, 257, (1 << 64) - 1, 1 << 128, SIGN, MASK, MASK - 1, 0xfffcb933bd6fad37aa2d162d1a594001]
            seconds = [0, 1, 2, 3, 8, 31, 32, 33, 64, 255, 256, 257, 1 << 16, (1 << 64) - 1, 1 << 64, 1 << 128, SIGN, MASK]
        for a in firsts:
            for b in seconds:
                V.append((op, a, b, 0))
        if op != 'EXP':
            for a in E:  # every edge value against itself and its neighbours
                V += [(op, a, a, 0), (op, a, (a + 1) & MASK, 0), (op, (a + 1) & MASK, a, 0), (op, a, a ^ MASK, 0)]
        for _ in range(400):
            a = rnd.choice(small) if op in ('SIGNEXTEND', 'BYTE', 'SHL', 'SHR', 'SAR') and rnd.random() < 0.7 else rand()
            V.append((op, a, rand(), 0))
    for op in UNA:
        for a in E: V.append((op, a, 0, 0))
        for _ in range(200): V.append((op, rand(), 0, 0))
    tcore = [0, 1, 2, 3, (1 << 64) - 1, 1 << 64, (1 << 128) - 1, 1 << 128, (1 << 128) + 1, SIGN - 1, SIGN, SIGN + 1, MASK - 1, MASK,
             1 << 96, 10 ** 6, 1461446703485210103287273052203988822378723970342, (1 << 192) + 1, (1 << 255) + (1 << 128) + 1]
    for op in TER + ['MULDIV512']:
        for a in tcore:
            for b in tcore:
                for c in tcore:
                    V.append((op, a, b, c))
        for _ in range(1500):
            c = rnd.choice([rand(), MASK - rnd.getrandbits(rnd.choice((1, 8, 64, 128))), SIGN + rnd.getrandbits(64),
                            (1 << rnd.choice((64, 128, 192))) + rnd.choice((-1, 0, 1)), rnd.getrandbits(rnd.choice((64, 65, 127, 129, 193))) | 1])
            V.append((op, rand() if rnd.random() < 0.5 else MASK - rnd.getrandbits(70), rand() if rnd.random() < 0.5 else MASK - rnd.getrandbits(130), u(c)))
    for a in E + [rand() for _ in range(100)]:  # condition words for JUMPI
        V.append(('JUMPI', a, 0, 0))
    for off in (0, 1, 31, 32, 33, 63):
        for ln in (0, 1, 31, 32, 33, 55, 56, 64, 65, 135, 136, 137, 200, 271, 272, 273, 408, 409, 512, 1023):
            V.append(('KECCAK', rand(), rand(), off | (ln << 8)))
    for _ in range(300):
        V.append(('MCOPY', rand(), rand(), rnd.randrange(0, 200) | (rnd.randrange(0, 200) << 8) | (rnd.randrange(0, 200) << 16)))
    for dst, src, ln in ((0, 1, 63), (1, 0, 63), (0, 0, 64), (32, 0, 32), (0, 32, 32), (16, 0, 48), (0, 16, 48), (5, 5, 0), (255, 0, 255), (0, 255, 255)):
        V.append(('MCOPY', rand(), rand(), dst | (src << 8) | (ln << 16)))
    V += [('CDLOAD', a, 0, 0) for a in (0, 1, 31, 32, 100, 127, 128, 1 << 16, (1 << 32) - 1, 1 << 32, (1 << 64) - 1, 1 << 64, (1 << 64) + 5, SIGN, MASK, MASK - 31)]
    for a in E + [rand() for _ in range(300)]:
        for sh in (0, 1, 23, 24, 232, 255):
            V.append(('SIGNEXT_CHAIN', a, sh, 0))
    for a in core + [rand() for _ in range(40)]:
        for b in core + [rand() for _ in range(10)]:
            V.append(('DIVUP', a, b, 0))
    return V


def encode(batch):
    return b''.join(ID[o].to_bytes(32, 'big') + a.to_bytes(32, 'big') + b.to_bytes(32, 'big') + c.to_bytes(32, 'big') for o, a, b, c in batch)


def expected(batch, data):
    out = []
    for k, (o, a, b, c) in enumerate(batch):
        if o == 'JUMPI':
            out.append(int(a != 0))
        elif o == 'CDLOAD':
            # the dispatcher reads calldataload(a) of the whole calldata; positions inside the batch are real data
            out.append(int.from_bytes((data[a:a + 32] if a < len(data) else b'').ljust(32, b'\0'), 'big'))
        else:
            out.append(reference(o, a, b, c, data))
    return out


def run(url, code, V, size=600, gas=None):
    bad = []; done = 0; errors = []
    for i in range(0, len(V), size):
        batch = V[i:i + size]; data = encode(batch)
        try:
            res = call_code(url, code, data, gas=gas)
        except Exception as e:  # noqa
            errors.append((i, str(e)[:160])); continue
        exp = expected(batch, data)
        if len(res) != 32 * len(batch):
            errors.append((i, f'short answer {len(res)} bytes')); continue
        for k, (t, e) in enumerate(zip(batch, exp)):
            got = int.from_bytes(res[32 * k:32 * k + 32], 'big')
            if got != e:
                bad.append({'op': t[0], 'a': hex(t[1]), 'b': hex(t[2]), 'c': hex(t[3]), 'got': hex(got), 'want': hex(e)})
        done += len(batch)
    return done, bad, errors


if __name__ == '__main__':
    out = sys.argv[1]; only = set(map(int, sys.argv[2:]))
    code = dispatcher(); V = vectors()
    per_op = {}
    for t in V: per_op[t[0]] = per_op.get(t[0], 0) + 1
    print('dispatcher', len(code), 'bytes;', len(V), 'vectors;', per_op)
    nets = [n for n in networks() if not only or n[0] in only]

    def work(n):
        cid, name, url = n
        done, bad, errors = run(url, code, V)
        if errors and done < len(V):  # second pass with small batches for what failed
            retry = [t for i, _ in errors for t in V[i:i + 600]]
            d2, b2, e2 = run(url, code, retry, size=150)
            done += d2; bad += b2; errors = e2
        return {'chainId': cid, 'name': name, 'rpc': url, 'vectors': len(V), 'ran': done, 'mismatches': bad[:200], 'mismatchCount': len(bad), 'errors': errors[:20]}

    res = []
    with cf.ThreadPoolExecutor(8) as ex:
        for r in ex.map(work, nets):
            print(f"{r['chainId']:>8} {r['name']:16} ran {r['ran']}/{r['vectors']} mismatches {r['mismatchCount']} errors {len(r['errors'])} {r['errors'][:1]}")
            res.append(r)
    json.dump({'vectors': len(V), 'perOp': per_op, 'dispatcherSha256': hashlib.sha256(code).hexdigest(), 'results': res}, open(out, 'w'), indent=1)
