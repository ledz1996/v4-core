"""Find 256-entry instruction tables (fn pointer + static gas, 16 bytes) among RELATIVE relocations.
usage: python3 -I find_tables.py <bin> <rel list> ; reads the static gas words from the file."""
import sys, struct
binf, relf = sys.argv[1:3]
fb = open(binf,'rb').read()
# map vaddr->file offset via program headers
import subprocess
e_phoff = struct.unpack_from('<Q', fb, 0x20)[0]; n = struct.unpack_from('<H', fb, 0x38)[0]
segs=[]
for i in range(n):
    p_type,p_flags,p_off,p_va,p_pa,p_fs,p_ms,p_al = struct.unpack_from('<IIQQQQQQ', fb, e_phoff+56*i)
    if p_type==1: segs.append((p_va,p_off,p_fs))
def rd(va,n=8):
    for v,o,s in segs:
        if v<=va<v+s: return int.from_bytes(fb[o+va-v:o+va-v+n],'little')
    return None
rel={}
for l in open(relf):
    a,b=l.split(); rel[int(a,16)]=int(b,16)
keys=sorted(rel)
ks=set(keys)
# want gas: ADD(1)=3 MUL(2)=5 SUB=3 DIV=5 ... 
for a in keys:
    if all((a+16*i) in ks for i in (1,2,3,4,0x10,0x1b,0x56,0x57,0x5b)) and (a-16) not in ks or False:
        pass
cands=[]
for a in keys:
    if a in ks and (a+16) in ks and (a+32) in ks:
        g=[rd(a+16*i+8) for i in range(0x20)]
        if g[1]==3 and g[2]==5 and g[3]==3 and g[4]==5 and g[0x10]==3 and g[0xa]==10:
            cands.append(a)
for a in cands:
    fns=[rel.get(a+16*i) for i in range(256)]
    print(hex(a), 'distinct fns', len(set(fns)), 'gas[0x1b..0x1d]',[rd(a+16*i+8) for i in (0x1b,0x1c,0x1d)], 'tload/tstore', hex(fns[0x5c] or 0), hex(fns[0x5d] or 0), 'jumpdest gas', rd(a+16*0x5b+8))
