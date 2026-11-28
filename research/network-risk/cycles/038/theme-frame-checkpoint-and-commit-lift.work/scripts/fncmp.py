"""Compare two functions of one binary instruction for instruction (objdump text; jump targets inside the function
made relative to its start, call targets and rip-relative data kept absolute). Reads the binary as data only.
usage: python3 -I fncmp.py <profile> <fnA> <fnB>   (function starts; ranges from the profile's FDE list)"""
import bisect, re, subprocess, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bins import BINS
P = BINS[sys.argv[1]]
F = sorted(tuple(int(x, 16) for x in re.split(r'\.\.+', l.strip())) for l in open(P['fde'])); S = [a for a, _ in F]


def rng(a):
    k = bisect.bisect_right(S, a) - 1
    return F[k]


def norm(a):
    lo, hi = rng(a)
    out = subprocess.run(['objdump', '-d', '-M', 'intel', '--no-show-raw-insn', '--start-address=%#x' % lo,
                          '--stop-address=%#x' % hi, P['bin']], capture_output=True, text=True).stdout
    L = []
    for l in out.splitlines():
        m = re.match(r'^\s*([0-9a-f]+):\s+(.*)$', l)
        if not m: continue
        b = re.sub(r'\s*<[^>]*>', '', m.group(2)).split('#')[0].strip()
        b = re.sub(r'\s+', ' ', b)
        mm = re.match(r'^(j\w+) ([0-9a-f]+)$', b)
        if mm and lo <= int(mm.group(2), 16) < hi: b = '%s +%x' % (mm.group(1), int(mm.group(2), 16) - lo)
        L.append(b)
    return (lo, hi), L


ra, A = norm(int(sys.argv[2], 16)); rb, B = norm(int(sys.argv[3], 16))
import difflib
sm = difflib.SequenceMatcher(None, A, B, autojunk=False)
print('A %#x-%#x %d insns, B %#x-%#x %d insns, ratio %.4f, identical %s' % (ra[0], ra[1], len(A), rb[0], rb[1], len(B), sm.ratio(), A == B))
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag != 'equal':
        print(tag, A[i1:i2][:6], '|', B[j1:j2][:6])
