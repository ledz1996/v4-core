# Generate micro programs that put one instruction in each of the emitter's operand shapes
# (literal, AVX register, general register, stack offset at a block entry) with edge operands,
# and the calldata sets that drive them. Output: a world file and a scenario file for hx.
import random,sys,itertools
random.seed(16)
M=(1<<256)-1
def p32(v): return bytes([0x7f])+v.to_bytes(32,'big')
def p1(v): return bytes([0x60,v])
CD=bytes([0x35]); ADD=bytes([0x01]); JUMP=bytes([0x56]); JD=bytes([0x5b]); SWAP1=bytes([0x90])
SHIFT_E=[0,1,2,7,8,31,32,63,64,65,127,128,129,191,192,193,248,254,255,256,257,511,(1<<64)-1,1<<64,(1<<64)+1,(1<<128)+5,(1<<192)+255,1<<255,M]
VAL_E=[0,1,2,0x7f,0x80,0xff,(1<<63),(1<<64)-1,1<<64,(1<<127),(1<<128)-1,1<<128,(1<<160)-1,(1<<255)-1,1<<255,(1<<255)+1,M-1,M,
       0x8421084210842108cc6318c6db6d54be,0x0706060506020500060203020504000106050205030304010505030400000000,
       random.getrandbits(256),random.getrandbits(256)|(1<<255),random.getrandbits(128),random.getrandbits(64)]
IDX_E=[0,1,2,15,16,29,30,31,32,33,255,256,(1<<64)+1,(1<<64)+31,(1<<128),1<<255,M]
MOD_K=[1,2,63,64,65,96,127,128,129,160,192,255]
def form_code(form,off,lit):
    if form=='A': return p32(lit)
    if form=='B': return p1(off)+CD
    if form=='G': return p1(off)+CD+p1(0xe0)+CD+ADD
    raise Exception
def program(op,forms,lits):
    """forms: list of operand forms from deepest to top of stack; 'S' operands are loaded (as B) before a block boundary"""
    pre=b'';post=b'';nS=sum(1 for f in forms if f=='S')
    code=b''
    offs=[0x00,0x20,0x40]
    # S operands are pushed first (deepest), others after the JUMPDEST; reorder with SWAPs is avoided by
    # requiring S operands to be the deepest ones
    sidx=[i for i,f in enumerate(forms) if f=='S']
    assert sidx==list(range(len(sidx)))
    for i,f in enumerate(forms):
        if f=='S': code+=form_code('B',offs[i],None)
    if sidx:
        jd=len(code)+4
        code+=bytes([0x61])+jd.to_bytes(2,'big')+JUMP+JD
    for i,f in enumerate(forms):
        if f!='S': code+=form_code(f,offs[i],lits[i])
    code+=bytes([op])+p1(0)+bytes([0x52])+p1(0x20)+p1(0)+bytes([0xf3])
    return code
progs=[]
def add(name,op,forms,lits,cds):
    progs.append((name,program(op,forms,lits),cds))
def cdata(vals):
    b=b''.join(v.to_bytes(32,'big') for v in vals)+b'\x00'*(0x100-32*len(vals))
    return b
def combos(sets):
    out=[list(x) for x in itertools.product(*sets)]
    return out
# two-operand ops: stack bottom = second EVM operand, top = first EVM operand
TWO={'SHL':(0x1b,SHIFT_E,VAL_E),'SHR':(0x1c,SHIFT_E,VAL_E),'SAR':(0x1d,SHIFT_E,VAL_E),'BYTE':(0x1a,IDX_E,VAL_E),'SIGNEXTEND':(0x0b,IDX_E,VAL_E),
     'SDIV':(0x05,VAL_E+[3,(1<<255)-3,M-2],VAL_E+[3]),'SMOD':(0x07,VAL_E+[3,M-2],VAL_E+[3])}
for name,(op,E1,E2) in TWO.items():
    # forms: (value form, top form); value is deeper
    for fv in 'ABGS':
        for ft in 'ABGS':
            if fv=='A' and ft=='A': continue
            if ft=='S' and fv!='S': continue
            lv=E2 if fv=='A' else [None]; lt=E1 if ft=='A' else [None]
            for a in lv:
                for b in lt:
                    sets=[]
                    sets.append([a] if fv=='A' else E2)
                    sets.append([b] if ft=='A' else E1)
                    cds=[]
                    for v,t in combos(sets):
                        cv=[v if fv!='A' else 0, t if ft!='A' else 0]
                        cds.append(cdata(cv))
                    add(f'{name}-{fv}{ft}-{a if a is not None else "x"}-{b if b is not None else "x"}',op,[fv,ft],[a,b],cds)
# MULMOD and ADDMOD: modulus deepest; literal modulus powers of two (mul_mod2 / add_mod2) and other literals and non-literal
for name,op in (('MULMOD',0x09),('ADDMOD',0x08)):
    mods=[1<<k for k in MOD_K]+[M,(1<<128)+1,3,0,1]
    for m in mods:
        for fa in 'ABG':
            for fb in 'ABG':
                if fa=='A' and fb=='A': continue
                la=VAL_E if fa=='A' else [None]; lb=VAL_E if fb=='A' else [None]
                for a in la[:8] if fa=='A' else la:
                    for b in lb[:8] if fb=='A' else lb:
                        sets=[[0],[b] if fb=='A' else VAL_E,[a] if fa=='A' else VAL_E]
                        cds=[cdata([0,bb if fb!='A' else 0, aa if fa!='A' else 0]) for _,bb,aa in combos(sets)]
                        add(f'{name}-m{m.bit_length()}-{fb}{fa}-{b if b is not None else "x"}-{a if a is not None else "x"}',op,['A',fb,fa],[m,b,a],cds)
    # non-literal modulus
    sets=[VAL_E[:12],VAL_E[:12],VAL_E[:12]]
    cds=[cdata(list(x)) for x in combos(sets)]
    add(f'{name}-BBB',op,['B','B','B'],[None,None,None],cds)
# CALLDATALOAD: literal offsets and non-literal offsets, calldata of several lengths
CDOFF=[0,1,31,32,33,0xdf,0xe0,0xff,0x100,0x101,(1<<32)-1,1<<32,(1<<64)+1,1<<255,M]
for o in CDOFF:
    code=p32(o)+CD+p1(0)+bytes([0x52])+p1(0x20)+p1(0)+bytes([0xf3])
    cds=[bytes(range(1,256))[:n] for n in (0,1,31,32,33,64,100,255)]
    progs.append((f'CALLDATALOAD-A-{o}',code,cds))
code=p1(0)+CD+CD+p1(0)+bytes([0x52])+p1(0x20)+p1(0)+bytes([0xf3])
cds=[o.to_bytes(32,'big')+bytes(range(1,200)) for o in CDOFF]
progs.append(('CALLDATALOAD-B',code,cds))
code=p1(0)+CD+p1(0x40)+CD+ADD+CD+p1(0)+bytes([0x52])+p1(0x20)+p1(0)+bytes([0xf3])
cds=[o.to_bytes(32,'big')+bytes(32)+bytes(range(1,200)) for o in CDOFF]
progs.append(('CALLDATALOAD-G',code,cds))
# write world and scenarios
W=open(sys.argv[1],'w'); S=open(sys.argv[2],'w'); H=open(sys.argv[3],'w')
for i,(name,code,cds) in enumerate(progs):
    addr='%040x'%(0xc0de0000000000+i)
    W.write(f'code {addr} {code.hex()}\n'); H.write(f'{name} {addr} {code.hex()}\n')
    S.write(f'SCEN {name}\n')
    for cd in cds: S.write(f'TX 00000000000000000000000000000000000a11ce {addr} 0 1000000 {cd.hex()}\n')
print(len(progs),'programs', sum(len(c) for _,_,c in progs),'calls')
