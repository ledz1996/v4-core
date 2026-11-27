"""Find the itab(s) of the Nitro b72783f binary whose method table holds (*state.StateDB).SetTransientState and
print the method order, to tie the interface call offsets of opTload/opTstore/opSload/opSstore to concrete methods.
Reads the ELF file as bytes only. usage: python3 -I itab.py <arch>"""
import sys, struct, json
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/030/theme-nitro-binary-arith-lift.work/scripts')
import goshim as G
arch = sys.argv[1]
D = '/home/user/v4-core/research/network-risk/cycles/030/theme-nitro-binary-arith-lift.work/dl/'
fns = G.fnlist(D + 'build/all-%s.txt' % arch)
byaddr = {v[0]: k for k, v in fns.items()}
img = G.Image(D + '%s/usr/local/bin/nitro' % arch)
f = img.f
S = 'github.com/ethereum/go-ethereum/core/state.'
targets = {fns[S + '(*StateDB).SetTransientState'][0]}
out = []
for lo, hi, off in img.secs:
    data = f[off: off + (hi - lo)]
    for t in targets:
        pat = struct.pack('<Q', t)
        i = data.find(pat)
        while i >= 0:
            if i % 8 == 0:
                # walk back over consecutive function pointers to find the start of fun[]
                j = i
                while j >= 8 and struct.unpack_from('<Q', data, j - 8)[0] in byaddr:
                    j -= 8
                k = i
                while struct.unpack_from('<Q', data, k)[0] in byaddr:
                    k += 8
                meths = [byaddr[struct.unpack_from('<Q', data, x)[0]] for x in range(j, k, 8)]
                out.append({'funStartVA': hex(lo + j), 'itabVA': hex(lo + j - 0x18), 'n': len(meths),
                            'offsets': {hex(0x18 + 8 * n): m.split('.')[-1] for n, m in enumerate(meths)}})
            i = data.find(pat, i + 1)
print(json.dumps(out, indent=1))
