"""Compares the ruint harness output with Python integers (EVM yellow paper semantics).
Usage: python3 -I compare.py <vectors.bin> <out.bin> [--plant N]  (--plant flips one output word to prove the comparison sees it)"""
import sys, json
MASK = (1 << 256) - 1; SIGN = 1 << 255
def s(x): return x - (1 << 256) if x & SIGN else x
def ref(op, a, b, c):
    if op == 0: return a // b if b else 0
    if op == 1: return a % b if b else 0
    if op == 2:
        if b == 0: return 0
        q = abs(s(a)) // abs(s(b)); return (q if (s(a) < 0) == (s(b) < 0) else -q) & MASK
    if op == 3:
        if b == 0: return 0
        r = abs(s(a)) % abs(s(b)); return (-r if s(a) < 0 else r) & MASK
    if op == 4: return (a + b) % c if c else 0
    if op == 5: return (a * b) % c if c else 0
    if op == 6:
        p = a * b; r = p % c if c else 0; return (((p >> 256) ^ r) + (p & MASK)) & MASK
    if op == 7: return (a // b + (a % b > 0)) if b else 0
V = open(sys.argv[1], 'rb').read(); O = bytearray(open(sys.argv[2], 'rb').read())
if '--plant' in sys.argv: O[32 * int(sys.argv[sys.argv.index('--plant') + 1])] ^= 1
n = len(V) // 97; assert len(O) == 32 * n, (len(O), n)
bad = []
for i in range(n):
    r = V[97 * i:97 * i + 97]; op = r[0]
    a, b, c = (int.from_bytes(r[1 + 32 * k:33 + 32 * k], 'big') for k in range(3))
    got = int.from_bytes(O[32 * i:32 * i + 32], 'big')
    if got != ref(op, a, b, c): bad.append({'i': i, 'op': op, 'a': hex(a), 'b': hex(b), 'c': hex(c), 'got': hex(got), 'want': hex(ref(op, a, b, c))})
print(json.dumps({'vectors': n, 'mismatches': len(bad), 'first': bad[:5]}))
