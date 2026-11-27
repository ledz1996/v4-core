"""For each indirect call in a listing, find the load of the called register in the preceding 12 lines and name
the StateDB interface method when the offset matches the *state.StateDB itab (out/itab-<arch>.json).
usage: python3 -I icalls.py <arch> <listing.s>..."""
import sys, re, json
arch = sys.argv[1]
W = '/home/user/v4-core/research/network-risk/cycles/031/theme-nitro-binary-storage-lift.work/out/'
it = json.load(open(W + 'itab-%s.json' % arch))[0]['offsets']
for fn in sys.argv[2:]:
    L = open(fn).read().splitlines()
    seq = []
    for i, l in enumerate(L):
        m = re.search(r'\b(call|blr)\s+([a-z0-9]+)\s*$', l.split(';')[0].strip())
        if m and m.group(2) not in ('0',) and not re.match(r'^[0-9a-f]{6,}$', m.group(2)):
            reg = m.group(2)
            off = None
            for j in range(i - 1, max(0, i - 14), -1):
                k = re.search(r'(?:mov\s+%s,QWORD PTR \[\w+\+(0x[0-9a-f]+)\]|ldr\s+%s, \[x\d+, #(0x[0-9a-f]+)\])' % (reg, reg), L[j])
                if k:
                    off = k.group(1) or k.group(2); break
            seq.append('%s:%s' % (l.split(':')[0].strip(), it.get(off, off)))
        else:
            k = re.search(r';\s*(\S+)', l)
            if k and re.search(r'\b(call|bl)\b', l) and 'morestack' not in k.group(1) and 'panic' not in k.group(1) and 'WriteBarrier' not in k.group(1):
                seq.append(k.group(1).split('/')[-1])
    print('==', fn.split('/')[-1], ' -> '.join(seq))
