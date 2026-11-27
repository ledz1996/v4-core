"""Probe: with a live EIP-7928 construction access list at StateDB+0xe0, does a write made in a reverted frame stay
recorded there? Prints the access list map contents after snap, SSTORE, revert, SLOAD (Nitro b72783f binaries)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stnitro as N
SG, T = N.SG, N.T
m = N.NModel('bal-' + sys.argv[1])
b = N.NBin(m, {(SG.PM, SG.SLOTS[0]): 5}, {SG.PM, SG.OTHER})
b.snap(); b.sst(SG.PM, SG.SLOTS[0], 7); b.rev(); print('after revert SLOAD', hex(b.sld(SG.PM, SG.SLOTS[0])))
h = m.rd(b.c, N.BALOBJ, 8)
for k, v in b.w.maps[h].items():
    acc = m.rd(b.c, v, 8)
    print('account', k.hex())
    for i in range(5):
        hh = m.rd(b.c, acc + 8 * i, 8)
        d = b.w.maps.get(hh, {})
        print('  map', i, {kk.hex()[:16]: m.rbytes(b.c, vv, 8).hex() for kk, vv in d.items()})
