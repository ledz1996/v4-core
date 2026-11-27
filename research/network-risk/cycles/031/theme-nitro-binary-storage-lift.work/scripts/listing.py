"""Disassemble named functions of the Nitro b72783f binaries (objdump / llvm-objdump read the file; nothing runs)
and annotate call targets with pclntab names. usage: python3 -I listing.py <arch> <outdir> name..."""
import sys, re, os
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/030/theme-nitro-binary-arith-lift.work/scripts')
import goshim as G
arch, outdir = sys.argv[1], sys.argv[2]
D = '/home/user/v4-core/research/network-risk/cycles/030/theme-nitro-binary-arith-lift.work/dl/'
fns = G.fnlist(D + 'build/all-%s.txt' % arch)
byaddr = {v[0]: k for k, v in fns.items()}
BIN = D + '%s/usr/local/bin/nitro' % arch
os.makedirs(outdir, exist_ok=True)
for name in sys.argv[3:]:
    full = [k for k in fns if k.endswith(name)]
    for k in full:
        lo, hi = fns[k]
        txt = G.disasm(BIN, arch, [(lo, hi)])
        def ann(m):
            a = int(m.group(1), 16)
            return m.group(0) + ('   ; ' + byaddr[a] if a in byaddr else '')
        lines = []
        for l in txt.splitlines():
            if re.search(r'\b(call|bl|b|jmp|cbz|cbnz|tbz|tbnz)\b|\bb\.', l):
                l = re.sub(r'(?:0x|\b)([0-9a-f]{6,8})\b(?= <|$)', ann, l, count=1)
            lines.append(l)
        fn = re.sub(r'[^A-Za-z0-9_.]', '_', k.split('/')[-1])
        open(os.path.join(outdir, fn + '.s'), 'w').write('; %s %#x-%#x\n' % (k, lo, hi) + '\n'.join(lines))
        print(arch, k, hex(lo), hi - lo)
