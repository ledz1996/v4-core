"""Reads the map type descriptors used by the transient storage map in both Nitro b72783f binaries (bytes only).
Swiss-map abi.MapType: Type (0x30 bytes), Key @0x30, Elem @0x38, Group @0x40, Hasher @0x48, GroupSize @0x50,
SlotSize @0x58, ElemOff @0x60, Flags @0x68. Type: Size_ @0, PtrBytes @8, Hash @0x10, TFlag @0x14, Align @0x15,
FieldAlign @0x16, Kind @0x17, Equal @0x18."""
import sys, json
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/031/theme-nitro-binary-storage-lift.work/scripts')
import tsmodel as T
out = {}
for arch, mt, zero in (('amd64', 0x69d2ec8, 0x7151a60), ('arm64', 0x6170ea8, None)):
    m = T.Model(arch)
    r = m.img.read
    byaddr = {v[0]: k for k, v in m.fns.items()}
    key, el = r(mt + 0x30, 8), r(mt + 0x38, 8)
    hasher_fv = r(mt + 0x48, 8)
    hasher = r(hasher_fv, 8)
    keq_fv = r(key + 0x18, 8)
    out[arch] = {'mapType': hex(mt), 'keySize': r(key, 8), 'keyPtrBytes': r(key + 8, 8), 'keyKind': r(key + 0x17, 1) & 0x1f,
                 'elemSize': r(el, 8), 'hasher': byaddr.get(hasher, hex(hasher)), 'keyEqual': byaddr.get(r(keq_fv, 8), hex(r(keq_fv, 8))),
                 'slotSize': r(mt + 0x58, 8), 'elemOff': r(mt + 0x60, 8),
                 'itabStateDB': hex(m.itab_statedb)}
    if zero:
        out[arch]['zeroCompareGlobalInBss'] = any(lo <= zero < hi for lo, hi in m.img.bss)
print(json.dumps(out, indent=1))
