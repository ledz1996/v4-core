"""Live jump destination probe for HyperEVM (cycle 10, angle 1). Read only: one eth_call per batch with two
contracts placed by state override, nothing deployed, nothing sent.

Target contract T: PUSH1 0 CALLDATALOAD JUMP, then a generated body. The body mixes
  - real JUMPDESTs, each followed by RET1 (return the word 1),
  - PUSHn (n = 1..32) whose data holds 0x5b at chosen positions; where room allows the 0x5b is followed inside the
    push data by RET1, so a node that wrongly accepted the jump would return success,
  - filler bytes (non push opcodes), so that push data crosses 16, 32 and 64 byte borders at every phase,
  - a PUSH32 truncated by the end of code whose missing data would contain the jump target.
Driver D: for each calldata word w, CALL(T, gas 60000, calldata w) and store the success flag; return the flags.
Expected (specification): success exactly for the real JUMPDEST offsets; failure for 0x5b inside push data, for
offsets at or past the end of code and for every non JUMPDEST byte.

Usage: python3 jdlive.py <out.json> [layouts]
"""
import sys, os, json, random, hashlib
sys.path.insert(0, __file__.rsplit('/', 4)[0] + '/tools/opdiff')
from evm import rpc

URL = json.load(open(__file__.rsplit('/', 4)[0] + '/state/networks.json'))
URL = [n for n in URL['networks'] if n['chainId'] == 999][0]['rpc']
T = '0x00000000000000000000000000000000c0de0a01'
D = '0x00000000000000000000000000000000c0de0a02'
RET1 = bytes([0x60, 0x01, 0x60, 0x00, 0x52, 0x60, 0x20, 0x60, 0x00, 0xf3])
FILL = [0x01, 0x02, 0x03, 0x10, 0x16, 0x19, 0x50, 0x80, 0x90, 0x00, 0xfe, 0x5a, 0x58, 0x30]


def reference(code):
    ok = set(); i = 0
    while i < len(code):
        op = code[i]
        if op == 0x5b: ok.add(i)
        i += 1 + (op - 0x5f if 0x60 <= op <= 0x7f else 0)
    return ok


def layout(rnd):
    c = bytearray([0x60, 0x00, 0x35, 0x56])
    c += bytes(rnd.choice(FILL) for _ in range(rnd.randrange(0, 64)))
    while len(c) < rnd.choice([300, 700, 1500, 3000]):
        k = rnd.random()
        if k < 0.25:
            c += b'\x5b' + RET1
        elif k < 0.8:
            n = rnd.randrange(1, 33); data = bytearray(rnd.choice(FILL) for _ in range(n))
            for _ in range(rnd.randrange(1, 4)):
                p = rnd.randrange(n); data[p] = 0x5b
                if p + 1 + len(RET1) <= n: data[p + 1:p + 1 + len(RET1)] = RET1
            c += bytes([0x5f + n]) + data
        else:
            c += bytes(rnd.choice(FILL) for _ in range(rnd.randrange(1, 70)))
    if rnd.random() < 0.5:  # truncated PUSH32 at the end, data would hold 0x5b
        c += bytes([0x7f]) + b'\x5b' * rnd.randrange(1, 31)
    return bytes(c)


def driver():
    # i = 0; loop: if i >= cds jump end; mstore(0, calldataload(i)); s = call(60000, T, 0, 0, 32, 0, 0);
    # mstore8(0x1000 + i/32, s); i += 32; jump loop; end: return(0x1000, cds/32)
    t = bytes.fromhex(T[2:])
    c = bytearray()
    c += bytes([0x5f])                                    # i
    loop = len(c)
    c += bytes([0x5b, 0x36, 0x81, 0x10, 0x61, 0, 0, 0x57])  # jumpdest; cds; dup2; lt -> i<cds ; push2 body; jumpi
    jb = len(c) - 3
    c += bytes([0x36, 0x60, 0x20, 0x90, 0x04, 0x61, 0x10, 0x00, 0xf3])  # cds/32 , 0x1000 return
    body = len(c)
    c += bytes([0x5b, 0x80, 0x35, 0x5f, 0x52])            # jumpdest; mstore(0, calldataload(i))
    c += bytes([0x5f, 0x5f, 0x60, 0x20, 0x5f, 0x5f, 0x73]) + t + bytes([0x62, 0x00, 0xea, 0x60, 0xf1])  # call
    c += bytes([0x81, 0x60, 0x05, 0x1c, 0x61, 0x10, 0x00, 0x01, 0x53])  # mstore8(0x1000 + i>>5, s)
    c += bytes([0x60, 0x20, 0x01, 0x61, 0, loop, 0x56])  # i += 32; jump loop
    c[jb:jb + 2] = body.to_bytes(2, 'big')
    return bytes(c)


def run(code, targets):
    data = b''.join(t.to_bytes(32, 'big') for t in targets)
    r = rpc(URL, 'eth_call', [{'to': D, 'data': '0x' + data.hex(), 'gas': hex(29_000_000)}, 'latest',
                              {D: {'code': '0x' + driver().hex()}, T: {'code': '0x' + code.hex()}}], timeout=120)
    return bytes.fromhex(r[2:])


if __name__ == '__main__':
    out = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    rnd = random.Random(10_999)
    total = 0; bad = []; cases = {'realJumpdest': 0, 'inPushData': 0, 'other': 0, 'pastEnd': 0}
    for li in range(n):
        code = layout(rnd); ref = reference(code)
        in_push = [i for i, b in enumerate(code) if b == 0x5b and i not in ref]
        others = rnd.sample([i for i in range(len(code)) if code[i] != 0x5b], 40)
        targets = sorted(ref) + in_push + others + [len(code), len(code) + 1, len(code) + 31, 2 ** 32, 2 ** 255]
        for i in range(0, len(targets), 400):
            part = targets[i:i + 400]
            got = run(code, part)
            for t, g in zip(part, got):
                exp = 1 if t in ref else 0
                kind = 'realJumpdest' if t in ref else 'inPushData' if t in in_push else 'pastEnd' if t >= len(code) else 'other'
                cases[kind] += 1; total += 1
                if g != exp: bad.append({'layout': li, 'target': t, 'expected': exp, 'got': g, 'kind': kind})
        print(li, len(code), len(ref), len(in_push), 'bad so far', len(bad), flush=True)
    res = {'chainId': 999, 'endpoint': URL, 'layouts': n, 'targets': total, 'cases': cases, 'mismatches': bad,
           'driverHex': driver().hex()}
    print(json.dumps({k: v for k, v in res.items() if k != 'driverHex'})[:1500])
    json.dump(res, open(out, 'w'), indent=1)
