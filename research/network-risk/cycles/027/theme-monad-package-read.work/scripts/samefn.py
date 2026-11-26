"""Compare functions by name between two disassembly texts after removing addresses and symbol offsets."""
import sys, re
def funcs(path, want):
    F = {}; cur = None
    for line in open(path, errors='replace'):
        m = re.match(r'^[0-9a-f]+ <(.*)>:\s*$', line)
        if m:
            cur = m.group(1) if m.group(1) in want else None
            if cur: F[cur] = []
            continue
        if cur is None: continue
        m = re.match(r'^\s+[0-9a-f]+:\s+(.*)$', line)
        if not m: continue
        t = m.group(1)
        t = re.sub(r'\b[0-9a-f]{4,} <([^>+]*)(\+0x[0-9a-f]+)?>', lambda x: '<' + x.group(1) + ('+off' if x.group(2) else '') + '>', t)
        t = re.sub(r'\[rip\+0x[0-9a-f]+\]\s*#.*', '[rip+X]', t)
        t = re.sub(r'(call|jmp)\s+[0-9a-f]+ ', r'\1 ', t)
        F[cur].append(t.strip())
    return F
want = set(l.strip() for l in open(sys.argv[3]) if l.strip())
A, B = funcs(sys.argv[1], want), funcs(sys.argv[2], want)
for w in sorted(want):
    a, b = A.get(w), B.get(w)
    print('%-5s %4s %4s %s' % ('SAME' if a == b and a else ('MISSING' if not a or not b else 'DIFF'), len(a or []), len(b or []), w[:120]))
