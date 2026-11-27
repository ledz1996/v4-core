"""Operand classes of the census, in plain Python integers (same rules as build/revm-interpreter/src/census.rs
and scripts/census_tracer.js), and a classifier for struct-log traces."""
M = 1 << 256; MAX = M - 1; H = 1 << 255
OPS = {4: 'DIV', 5: 'SDIV', 6: 'MOD', 7: 'SMOD', 8: 'ADDMOD', 9: 'MULMOD', 11: 'SIGNEXTEND', 18: 'SLT', 19: 'SGT',
       26: 'BYTE', 27: 'SHL', 28: 'SHR', 29: 'SAR'}
NAMES = {
    (4, 1): 'DIV by zero', (6, 1): 'MOD by zero',
    (5, 1): 'SDIV negative dividend', (5, 2): 'SDIV negative divisor', (5, 3): 'SDIV by zero', (5, 4): 'SDIV -2^255 by -1',
    (7, 1): 'SMOD negative dividend', (7, 2): 'SMOD negative divisor', (7, 3): 'SMOD by zero',
    (8, 1): 'ADDMOD sum >= 2^256', (8, 2): 'ADDMOD modulus 2^256-1', (8, 3): 'ADDMOD modulus 0',
    (9, 1): 'MULMOD modulus 2^256-1, product >= 2^256', (9, 2): 'MULMOD other nonzero modulus, product >= 2^256',
    (9, 3): 'MULMOD modulus 0', (9, 4): 'MULMOD four-limb modulus (>= 2^192, not 2^256-1), product >= 2^256',
    (9, 5): 'MULMOD modulus < 2^128, product >= 2^256',
    (11, 1): 'SIGNEXTEND from byte 0-2, sign bit set', (11, 2): 'SIGNEXTEND from byte 3-30, sign bit set',
    (11, 3): 'SIGNEXTEND index >= 31', (11, 4): 'SIGNEXTEND from byte 0-2, sign clear, dirty high bits',
    (11, 5): 'SIGNEXTEND from byte 0-2, sign set, high bits not already all ones',
    (18, 1): 'SLT operands of different sign', (18, 2): 'SLT both negative',
    (19, 1): 'SGT operands of different sign', (19, 2): 'SGT both negative',
    (26, 1): 'BYTE index < 32', (26, 2): 'BYTE index >= 32',
    (27, 1): 'SHL shift >= 256', (28, 1): 'SHR shift >= 256',
    (29, 1): 'SAR negative value, shift < 256', (29, 2): 'SAR negative value, shift >= 256', (29, 3): 'SAR non-negative value, shift >= 256',
}
for _o in OPS: NAMES[(_o, 0)] = OPS[_o] + ' executed'


def classes(op, a, b, c=0):
    out = [0]
    na, nb = a >= H, b >= H
    if op in (4, 6):
        if b == 0: out.append(1)
    elif op == 5:
        if na: out.append(1)
        if nb: out.append(2)
        if b == 0: out.append(3)
        if a == H and b == MAX: out.append(4)
    elif op == 7:
        if na: out.append(1)
        if nb: out.append(2)
        if b == 0: out.append(3)
    elif op == 8:
        if a + b >= M: out.append(1)
        if c == MAX: out.append(2)
        if c == 0: out.append(3)
    elif op == 9:
        wide = a * b >= M
        if wide and c == MAX: out.append(1)
        if wide and c != MAX and c != 0: out.append(2)
        if c == 0: out.append(3)
        if wide and c != MAX and c >= 1 << 192: out.append(4)
        if wide and c != 0 and c < 1 << 128: out.append(5)
    elif op == 11:
        if a < 31:
            bi = 8 * a + 7; bit = (b >> bi) & 1; hi = b >> (bi + 1); ones = MAX >> (bi + 1)
            if a <= 2 and bit: out.append(1)
            if a > 2 and bit: out.append(2)
            if a <= 2 and not bit and hi: out.append(4)
            if a <= 2 and bit and hi != ones: out.append(5)
        else: out.append(3)
    elif op == 26:
        out.append(1 if a < 32 else 2)
    elif op in (27, 28):
        if a >= 256: out.append(1)
    elif op == 29:
        if nb and a < 256: out.append(1)
        if nb and a >= 256: out.append(2)
        if not nb and a >= 256: out.append(3)
    elif op in (18, 19):
        if na != nb: out.append(1)
        if na and nb: out.append(2)
    return out


OPNUM = {v: k for k, v in OPS.items()}


def structlog_census(trace, to):
    """trace: debug_traceTransaction struct-log result; to: the transaction's recipient.
    Returns {(op, class, code address, pc): count}. Code address follows CALL targets; DELEGATECALL and CALLCODE run the callee's code."""
    res = {}
    frames = [to.lower()]
    pending = None
    for s in trace['structLogs']:
        d = s['depth']
        if pending is not None and d == len(frames) + 1:
            frames.append(pending)
        while d < len(frames): frames.pop()
        pending = None
        op = s['op']; st = s.get('stack') or []
        if op in ('CALL', 'STATICCALL', 'DELEGATECALL', 'CALLCODE') and len(st) >= 2:
            pending = '0x%040x' % (int(st[-2], 16) & ((1 << 160) - 1))
        elif op in ('CREATE', 'CREATE2'):
            pending = 'create'
        n = OPNUM.get(op)
        if n is None: continue
        a = int(st[-1], 16); b = int(st[-2], 16); c = int(st[-3], 16) if n in (8, 9) else 0
        for k in classes(n, a, b, c):
            key = (n, k, frames[-1], s['pc'])
            res[key] = res.get(key, 0) + 1
    return res
