"""Compare two functions instruction by instruction after replacing absolute code and data addresses (6 or more hex
digits) by a placeholder. Prints the count of equal and different lines and the first differences.
usage: python3 -I normdiff.py <binA> <fdeA> <hexA> <binB> <fdeB> <hexB>"""
import bisect, difflib, re, subprocess, sys
def body(binf, fdes, a):
    f = sorted(tuple(int(x, 16) for x in re.split(r'\.\.+', l.strip())) for l in open(fdes)); s = [x for x, y in f]
    lo, hi = f[bisect.bisect_right(s, a) - 1]
    out = subprocess.run(['objdump', '-d', '--no-show-raw-insn', '-M', 'intel', '--start-address=%#x' % lo, '--stop-address=%#x' % hi, binf], capture_output=True, text=True).stdout
    r = []
    for l in out.splitlines():
        m = re.match(r'^\s*[0-9a-f]+:\s+(.*)$', l)
        if not m: continue
        t = re.sub(r'<[^>]*>', '', m.group(1)).split('#')[0].strip()
        t = re.sub(r'\b(0x)?[0-9a-f]{6,}\b', 'ADDR', t); t = re.sub(r'\[rip[+-]0x[0-9a-f]+\]', '[RIP]', t)
        r.append(t)
    return lo, hi, r
la, ha, A = body(sys.argv[1], sys.argv[2], int(sys.argv[3], 16))
lb, hb, B = body(sys.argv[4], sys.argv[5], int(sys.argv[6], 16))
sm = difflib.SequenceMatcher(a=A, b=B, autojunk=False)
eq = sum(b.size for b in sm.get_matching_blocks())
print('A %x %d bytes %d ins | B %x %d bytes %d ins | equal %d' % (la, ha - la, len(A), lb, hb - lb, len(B), eq))
n = 0
for op, i1, i2, j1, j2 in sm.get_opcodes():
    if op != 'equal' and n < int(sys.argv[7] if len(sys.argv) > 7 else 12):
        print(op, A[i1:i2][:4], '->', B[j1:j2][:4]); n += 1
