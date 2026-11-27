"""Side-by-side diff of two functions: matched on normalised text, printed with real addresses and operands.
usage: python3 -I sidediff.py <binA> <fdeA> <hexA> <binB> <fdeB> <hexB> [all]"""
import bisect, difflib, re, subprocess, sys
def body(binf, fdes, a):
    f = sorted(tuple(int(x, 16) for x in re.split(r'\.\.+', l.strip())) for l in open(fdes)); s = [x for x, y in f]
    lo, hi = f[bisect.bisect_right(s, a) - 1]
    out = subprocess.run(['objdump', '-d', '--no-show-raw-insn', '-M', 'intel', '--start-address=%#x' % lo, '--stop-address=%#x' % hi, binf], capture_output=True, text=True).stdout
    r = []; raw = []
    for l in out.splitlines():
        m = re.match(r'^\s*([0-9a-f]+):\s+(.*)$', l)
        if not m: continue
        t0 = m.group(2).strip(); t = re.sub(r'<[^>]*>', '', t0).split('#')[0].strip()
        n = re.sub(r'\b(0x)?[0-9a-f]{6,}\b', 'ADDR', t); n = re.sub(r'\[rip[+-]0x[0-9a-f]+\]', '[RIP]', n)
        r.append(n); raw.append(m.group(1) + ': ' + t0[:90])
    return r, raw
A, RA = body(sys.argv[1], sys.argv[2], int(sys.argv[3], 16)); B, RB = body(sys.argv[4], sys.argv[5], int(sys.argv[6], 16))
allx = len(sys.argv) > 7
for op, i1, i2, j1, j2 in difflib.SequenceMatcher(a=A, b=B, autojunk=False).get_opcodes():
    if op == 'equal' and not allx:
        # print rip/absolute operand pairs in equal blocks (they carry the relocated constants)
        for i, j in zip(range(i1, i2), range(j1, j2)):
            if 'ADDR' in A[i] or '[RIP]' in A[i]: print('   =', RA[i], ' || ', RB[j])
        continue
    for k in range(max(i2 - i1, j2 - j1)):
        a = RA[i1 + k] if i1 + k < i2 else ''; b = RB[j1 + k] if j1 + k < j2 else ''
        print(' %s %-70s || %s' % ('!' if op != 'equal' else ' ', a, b))
