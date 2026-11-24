"""Edge vectors where an operand that the EVM treats as a whole word could be
read from its low limb only: shift amounts, BYTE index and SIGNEXTEND size with
nonzero high limbs, plus division and modulus edge pairs. Read-only eth_call
with a state override. Usage: python3 highlimb.py <rpc> <out.json>"""
import json, sys, random, time, urllib.request
M = (1 << 256) - 1
def s(x): return x - (1 << 256) if x >> 255 else x
def u(x): return x & M
def sar(sh, v): return u(s(v) >> min(sh, 256)) if sh < 256 else (M if v >> 255 else 0)
def byte(i, x): return 0 if i >= 32 else (x >> (8 * (31 - i))) & 0xff
def sext(b, x):
    if b >= 31: return x
    bit = 8 * b + 7; m = (1 << (bit + 1)) - 1
    return u(x | ~m) if (x >> bit) & 1 else x & m
def sdiv(a, b):
    if b == 0: return 0
    q = abs(s(a)) // abs(s(b)); return u(q if (s(a) < 0) == (s(b) < 0) else -q)
def smod(a, b):
    if b == 0: return 0
    r = abs(s(a)) % abs(s(b)); return u(-r if s(a) < 0 else r)
OPS = {  # opcode byte, arity, reference(top, second, third)
 'SHL': (0x1b, 2, lambda a, b, c: u(b << a) if a < 256 else 0),
 'SHR': (0x1c, 2, lambda a, b, c: b >> a if a < 256 else 0),
 'SAR': (0x1d, 2, lambda a, b, c: sar(a, b)),
 'BYTE': (0x1a, 2, lambda a, b, c: byte(a, b)),
 'SIGNEXTEND': (0x0b, 2, lambda a, b, c: sext(a, b)),
 'DIV': (0x04, 2, lambda a, b, c: a // b if b else 0),
 'SDIV': (0x05, 2, lambda a, b, c: sdiv(a, b)),
 'MOD': (0x06, 2, lambda a, b, c: a % b if b else 0),
 'SMOD': (0x07, 2, lambda a, b, c: smod(a, b)),
 'ADDMOD': (0x08, 3, lambda a, b, c: (a + b) % c if c else 0),
 'MULMOD': (0x09, 3, lambda a, b, c: (a * b) % c if c else 0),
 'EXP': (0x0a, 2, lambda a, b, c: pow(a, b, 1 << 256)),
}
def code(op):  # push c, b, a from calldata so a is on top; OP; return word
    return bytes([0x60, 0x40, 0x35, 0x60, 0x20, 0x35, 0x60, 0x00, 0x35, op, 0x60, 0, 0x52, 0x60, 0x20, 0x60, 0, 0xf3])
def addr(i): return '0x' + ('00' * 18) + '%04x' % (0xbe00 + i)
def vectors():
    rnd = random.Random(20261124)
    hi = [(1 << 64) + k for k in (0, 1, 5, 31, 255)] + [(1 << 128) + 3, (1 << 192) + 8, (1 << 255) + 1, (1 << 255), M, M - 255, (1 << 64) - 1, (1 << 32) + 1, 256, 255, 257]
    words = [0, 1, M, 1 << 255, (1 << 255) - 1, 0x80, 0xff, 0x7f << 248] + [rnd.getrandbits(256) for _ in range(6)]
    V = []
    for k in ('SHL', 'SHR', 'SAR', 'BYTE', 'SIGNEXTEND'):
        for a in hi:
            for b in words: V.append((k, a, b, 0))
    edge = [0, 1, 2, M, M - 1, 1 << 255, (1 << 255) - 1, (1 << 255) + 1, 1 << 128, (1 << 128) - 1, 1 << 64, (1 << 64) - 1]
    for k in ('DIV', 'SDIV', 'MOD', 'SMOD', 'EXP'):
        for a in edge:
            for b in edge: V.append((k, a, b, 0))
    for k in ('ADDMOD', 'MULMOD'):
        for a in edge[:8]:
            for b in edge[:8]:
                for c in [0, 1, 2, M, 1 << 255, (1 << 128) + 1, (1 << 192) - 1]: V.append((k, a, b, c))
    return V
def rpc(url, batch):
    req = urllib.request.Request(url, json.dumps(batch).encode(), {'content-type': 'application/json', 'user-agent': 'review-client'})
    return json.load(urllib.request.urlopen(req, timeout=120))
def main():
    url, out = sys.argv[1], sys.argv[2]
    names = list(OPS); over = {addr(i): {'code': '0x' + code(OPS[n][0]).hex()} for i, n in enumerate(names)}
    V = vectors(); res = {'rpc': url, 'vectors': len(V), 'mismatch': [], 'errors': 0, 'byOp': {}}
    for i in range(0, len(V), 50):
        chunk = V[i:i + 50]; batch = []
        for j, (k, a, b, c) in enumerate(chunk):
            data = '0x' + ''.join('%064x' % x for x in (a, b, c))
            batch.append({'jsonrpc': '2.0', 'id': j, 'method': 'eth_call', 'params': [{'to': addr(names.index(k)), 'data': data, 'gas': '0x100000'}, 'latest', over]})
        got = rpc(url, batch)
        if not isinstance(got, list):  # endpoint without batch support: one call at a time
            got = []
            for q in batch:
                try: got.append(rpc(url, q))
                except Exception as e: got.append({'id': q['id'], 'error': str(e)})
        ans = {r['id']: r for r in got}
        for j, (k, a, b, c) in enumerate(chunk):
            r = ans.get(j, {}); res['byOp'][k] = res['byOp'].get(k, 0) + 1
            tries = 0
            while 'result' not in r and tries < 4:  # retry calls refused by a rate limit
                time.sleep(3 * (tries + 1)); tries += 1
                try: r = rpc(url, batch[j])
                except Exception as e: r = {'error': str(e)}
            if 'result' not in r: res['errors'] += 1; continue
            exp = OPS[k][2](a, b, c)
            if int(r['result'], 16) != exp: res['mismatch'].append([k, hex(a), hex(b), hex(c), r['result'], hex(exp)])
    json.dump(res, open(out, 'w'), indent=1)
    print(url, 'vectors', len(V), 'mismatches', len(res['mismatch']), 'errors', res['errors'], res['byOp'])
main()
