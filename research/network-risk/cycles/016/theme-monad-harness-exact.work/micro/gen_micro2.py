# Micro programs for the two v0.16.7 memory changes: repeated non-literal offsets (touched_memory_size)
# and MSTORE8 of a value held at a stack offset, register or literal.
import sys
def p1(v): return bytes([0x60,v])
def p32(v): return bytes([0x7f])+v.to_bytes(32,'big')
CD=b'\x35';DUP1=b'\x80';DUP2=b'\x81';SWAP1=b'\x90';ML=b'\x51';MS=b'\x52';MS8=b'\x53';ADD=b'\x01';POP=b'\x50';JUMP=b'\x56';JD=b'\x5b';MSIZE=b'\x59'
RET=p1(0)+MS+MSIZE+p1(0)+MS+p1(0x40)+p1(0)+b'\xf3'   # returns [last value, msize]
OFF=[0,1,31,32,33,1000,(1<<20),(1<<29)-64,(1<<29)-32,(1<<29)-1,1<<29,(1<<30),(1<<32),(1<<64)+32,1<<255,(1<<256)-1]
progs=[]
def jmpblock(code):  # move to a new block so the stack holds stack offsets
    jd=len(code)+4; return code+bytes([0x61])+jd.to_bytes(2,'big')+JUMP+JD
# 1: offset from calldata, MLOAD then MSTORE then MLOAD with the same element (DUPs keep one StackElem)
c=p1(0)+CD+DUP1+DUP1+ML+SWAP1+MS+ML+RET; progs.append(('MEM-B-mload-mstore-mload',c))
c=p1(0)+CD+p1(0x40)+CD+ADD+DUP1+DUP1+ML+SWAP1+MS+ML+RET; progs.append(('MEM-G-mload-mstore-mload',c))
c=jmpblock(p1(0)+CD)+DUP1+DUP1+ML+SWAP1+MS+ML+RET; progs.append(('MEM-S-mload-mstore-mload',c))
# 2: MSTORE8 first (size 1), then MLOAD (size 32) with the same element: the second must still be checked
c=p1(0)+CD+DUP1+p1(0x20)+CD+SWAP1+MS8+ML+RET; progs.append(('MEM-B-mstore8-mload',c))
c=jmpblock(p1(0)+CD+p1(0x20)+CD)+DUP2+MS8+ML+RET; progs.append(('MEM-S-mstore8-mload',c))
# 3: MSTORE8 value shapes: literal, AVX (calldataload), general register (add), stack offset (after jump)
for nm,val in (('A',p32(0x1234567890abcdef)),('B',p1(0x20)+CD),('G',p1(0x20)+CD+p1(0x40)+CD+ADD)):
    c=val+p1(0)+CD+MS8+p1(0)+ML+RET; progs.append((f'MSTORE8-value{nm}-offB',c))
c=jmpblock(p1(0x20)+CD)+p1(0)+CD+MS8+p1(0)+ML+RET; progs.append(('MSTORE8-valueS-offB',c))
c=jmpblock(p1(0x20)+CD+p1(0)+CD)+MS8+p1(0)+ML+RET; progs.append(('MSTORE8-valueS-offS',c))
W=open(sys.argv[1],'w');S=open(sys.argv[2],'w');H=open(sys.argv[3],'w')
for i,(n,c) in enumerate(progs):
    a='%040x'%(0xc0de1000000000+i); W.write(f'code {a} {c.hex()}\n'); H.write(f'{n} {a} {c.hex()}\n'); S.write(f'SCEN {n}\n')
    for o in OFF:
        for v in (0,0xff,0x1ff,(1<<256)-1,0x80<<248):
            for g in (100000,3000000):
                cd=o.to_bytes(32,'big')+v.to_bytes(32,'big')+(0).to_bytes(32,'big')
                S.write(f'TX 00000000000000000000000000000000000a11ce {a} 0 {g} {cd.hex()}\n')
print(len(progs))
