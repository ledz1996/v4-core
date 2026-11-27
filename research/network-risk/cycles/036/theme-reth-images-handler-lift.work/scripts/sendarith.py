"""Send 2,000 of the arithmetic model vectors (the arith.py 'all' set: battery, targeted, maxmod, v4math shapes) by
eth_call to one endpoint per network. Each call carries 100 vectors as straight-line code in a state override
(PUSH32 c, PUSH32 b, PUSH32 a, OP, MSTORE at 32*k, RETURN) and is bracketed by web3_clientVersion. No transaction.
Sampling seed 3601: 20 vectors per opcode first, then a uniform sample of the rest.
usage: python3 -I sendarith.py <out.json> chainId=url ..."""
import json, random, sys, time
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/036/theme-reth-images-handler-lift.work/scripts')
from evm import call_code, rpc
OPS = {'ADD': 1, 'MUL': 2, 'SUB': 3, 'DIV': 4, 'SDIV': 5, 'MOD': 6, 'SMOD': 7, 'ADDMOD': 8, 'MULMOD': 9,
       'EXP': 10, 'SIGNEXTEND': 11, 'LT': 0x10, 'GT': 0x11, 'SLT': 0x12, 'SGT': 0x13, 'EQ': 0x14, 'ISZERO': 0x15,
       'AND': 0x16, 'OR': 0x17, 'XOR': 0x18, 'NOT': 0x19, 'BYTE': 0x1a, 'SHL': 0x1b, 'SHR': 0x1c, 'SAR': 0x1d}
ARITY = {'ISZERO': 1, 'NOT': 1, 'ADDMOD': 3, 'MULMOD': 3}
M = (1 << 256) - 1


def vectors():
    import battery, targeted, v4shapes
    for op, a, b, c in battery.vectors():
        if op in OPS: yield 'battery', op, a, b, c
        elif op == 'MULDIV512':
            yield 'battery-muldiv', 'MULMOD', a, b, c; yield 'battery-muldiv', 'MULMOD', a, b, M
            yield 'battery-muldiv', 'MUL', a, b, 0
        elif op == 'DIVUP':
            yield 'battery-divup', 'DIV', a, b, 0; yield 'battery-divup', 'MOD', a, b, 0
    for op, a, b, c in targeted.vectors():
        if op in OPS: yield 'targeted', op, a, b, c
        elif op == 'MULDIV512':
            yield 'targeted-muldiv', 'MULMOD', a, b, c; yield 'targeted-muldiv', 'MULMOD', a, b, M
    base = '/home/user/v4-core/research/network-risk/cycles/025/stablecoin-l1.work/'
    for name in ('maxmod', 'maxmod2'):
        g = {'__file__': base + name + '.py', '__name__': name + '_vectors'}
        exec(open(base + name + '.py').read().split("\nif __name__")[0], g)
        for a, b, n in g['vecs']():
            yield name, 'MULMOD', a, b, n; yield name, 'ADDMOD', a, b, n; yield name + '-prod1', 'MULMOD', a, b, M
    for tag, op, a, b, c in v4shapes.vectors(): yield tag, op, a, b, c


def s(x): return x - (1 << 256) if x >> 255 else x
def ref(op, a, b, c):
    import importlib
    if op == 'ADD': return (a + b) & M
    if op == 'MUL': return (a * b) & M
    if op == 'SUB': return (a - b) & M
    if op == 'DIV': return a // b if b else 0
    if op == 'MOD': return a % b if b else 0
    if op == 'SDIV':
        if b == 0: return 0
        q = abs(s(a)) // abs(s(b)); return (-q if (s(a) < 0) != (s(b) < 0) else q) & M
    if op == 'SMOD':
        if b == 0: return 0
        r = abs(s(a)) % abs(s(b)); return (-r if s(a) < 0 else r) & M
    if op == 'ADDMOD': return (a + b) % c if c else 0
    if op == 'MULMOD': return (a * b) % c if c else 0
    if op == 'EXP': return pow(a, b, 1 << 256)
    if op == 'SIGNEXTEND':
        if a >= 31: return b
        bit = 8 * a + 7
        return (b | (M ^ ((1 << bit) - 1))) if (b >> bit) & 1 else b & ((1 << bit) - 1)
    if op == 'LT': return int(a < b)
    if op == 'GT': return int(a > b)
    if op == 'SLT': return int(s(a) < s(b))
    if op == 'SGT': return int(s(a) > s(b))
    if op == 'EQ': return int(a == b)
    if op == 'ISZERO': return int(a == 0)
    if op == 'AND': return a & b
    if op == 'OR': return a | b
    if op == 'XOR': return a ^ b
    if op == 'NOT': return a ^ M
    if op == 'BYTE': return 0 if a >= 32 else (b >> (8 * (31 - a))) & 0xff
    if op == 'SHL': return (b << a) & M if a < 256 else 0
    if op == 'SHR': return b >> a if a < 256 else 0
    if op == 'SAR': return s(b) >> min(a, 256) & M
    raise KeyError(op)


def p32(x): return bytes([0x7f]) + (x & M).to_bytes(32, 'big')


def code(batch):
    out = b''
    for k, (tag, op, a, b, c) in enumerate(batch):
        ar = ARITY.get(op, 2)
        for x in reversed([a, b, c][:ar]): out += p32(x)
        out += bytes([OPS[op]]) + bytes([0x61]) + (32 * k).to_bytes(2, 'big') + bytes([0x52])
    return out + bytes([0x61]) + (32 * len(batch)).to_bytes(2, 'big') + bytes([0x5f, 0xf3])


allv = list(vectors())
rnd = random.Random(3601)
V, used = [], set()
for op in OPS:
    idx = [i for i, v in enumerate(allv) if v[1] == op]
    for i in rnd.sample(idx, min(20, len(idx))): V.append(allv[i]); used.add(i)
rest = [i for i in range(len(allv)) if i not in used]
for i in rnd.sample(rest, 2000 - len(V)): V.append(allv[i])
EP = {}
for a in sys.argv[2:]:
    c, u = a.split('=', 1); EP[int(c)] = u
def cv(url):
    try: return rpc(url, 'web3_clientVersion', [])
    except Exception as e: return 'error ' + str(e)[:160]
res = {'seed': 3601, 'population': len(allv), 'vectors': len(V), 'byOp': {}, 'chains': {}}
for v in V: res['byOp'][v[1]] = res['byOp'].get(v[1], 0) + 1
B = 100
for cid, url in EP.items():
    ch = {'url': url, 'batches': [], 'mismatches': [], 'errors': [], 'done': 0}
    for i in range(0, len(V), B):
        batch = V[i:i + B]
        before = cv(url)
        try:
            r = call_code(url, code(batch), b'', gas=30_000_000)
        except Exception as e:
            r = None; ch['errors'].append({'batch': i // B, 'error': str(e)[:300]})
        after = cv(url)
        ch['batches'].append({'batch': i // B, 'before': before, 'after': after})
        if r is None: continue
        if len(r) != 32 * len(batch):
            ch['errors'].append({'batch': i // B, 'error': 'answer %d bytes' % len(r)}); continue
        for k, (tag, op, a, b, c) in enumerate(batch):
            got = int.from_bytes(r[32 * k:32 * k + 32], 'big'); want = ref(op, a, b, c)
            if got != want:
                ch['mismatches'].append({'tag': tag, 'op': op, 'a': hex(a), 'b': hex(b), 'c': hex(c), 'got': hex(got), 'want': hex(want)})
        ch['done'] += len(batch)
        time.sleep(0.3)
    ch['clientVersions'] = sorted(set(b['before'] for b in ch['batches']) | set(b['after'] for b in ch['batches']))
    res['chains'][cid] = ch
    print(cid, url, 'done', ch['done'], 'mismatches', len(ch['mismatches']), 'errors', len(ch['errors']), ch['clientVersions']); sys.stdout.flush()
json.dump(res, open(sys.argv[1], 'w'), indent=1)
