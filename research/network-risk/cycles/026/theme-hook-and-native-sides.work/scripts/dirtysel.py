"""Selector comparison with dirty low bytes (Hooks.sol:152 with ParseBytes.sol:9-14): run in the reference EVM with the
driver at an address whose upper 16 bytes are nonzero, so the first calldata word of every hook call carries nonzero
bytes after the selector, and with hooks that pad the selector with nonzero bytes. Usage: python3 dirtysel.py <out.json>"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common26 as C
import pyevm26 as P
from cases26 import cases, HSEL, ALLF, pool, add, std_acts, ret  # noqa (rebuilds the list; only used for helpers)
out = {}
pm = 0x000000000004444c5dc75cB358380D2e3dE08A90
for dname, daddr in (('driver low', C.D), ('driver high bytes', 0xFEDCBA9876543210FEDCBA9876543210d0d04000)):
    for pad, tag in ((b'\0' * 28, 'zero pad'), (b'\xff' * 28, 'ff pad')):
        res = {}
        for f, s in HSEL.items():
            c = pool(9000 + len(res), ALLF)
            n = {'beforeSwap': 3, 'afterSwap': 2, 'afterAddLiquidity': 2, 'afterRemoveLiquidity': 2}.get(f, 1)
            body = s.to_bytes(4, 'big') + pad + b''.join(C.w(0) for _ in range(n - 1))
            cc = dict(c); cc['p'] = C.build_p([(0, s, 1, body)], std_acts(c)); cc['id'] = 0
            codes = C.codes_for(pm, [cc]); codes[daddr] = codes.pop(C.D)
            wld = P.World(codes, {pm: C.PM_BAL, daddr: C.D_BAL})
            ok, r = wld.call(C.EOA, daddr, 0, C.enc_run([cc], pm), False, 0)
            (uok, words, rv), = C.dec_run(r)
            d = C.decode_words(words, 5)
            res[f] = [(a['ok'], hex(a['w0'] >> 224)) for a in d['acts']]
        out[f'{dname} / {tag}'] = res
        print(dname, tag, {f: [x[0] for x in v] for f, v in res.items()})
json.dump(out, open(sys.argv[1], 'w'), indent=1)
