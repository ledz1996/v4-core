# L-787: find the opcode dispatch table of the respected kona-client prestate by searching memory for the
# known ADD handler address (cycle 16: 0x12005f77c) as a 64-bit big-endian word, then read the entries.
import sys, struct
pre = sys.argv[1]
d = open(pre, 'rb').read(); npages = struct.unpack('>Q', d[1:9])[0]; o = 9; pages = {}
for k in range(npages):
    idx = struct.unpack('>Q', d[o:o + 8])[0]; pages[idx] = d[o + 8:o + 8 + 4096]; o += 4104
known = {0x01: 0x12005f77c, 0x04: 0x12005f834, 0x0a: 0x12005f920, 0x06: 0x12005ff2c, 0x03: 0x120060018, 0x1d: 0x12006ad6c}
for want_op, addr in known.items():
    pat = struct.pack('>Q', addr)
    for idx, pg in pages.items():
        i = pg.find(pat)
        while i >= 0:
            print('op', hex(want_op), 'handler', hex(addr), 'found at', hex(idx * 4096 + i))
            i = pg.find(pat, i + 1)
base = 0x1203f4778 - 3 * 8
def rd(a):
    pg = pages[a >> 12]; return struct.unpack('>Q', pg[(a & 4095):(a & 4095) + 8])[0]
names = {0:'STOP',1:'ADD',2:'MUL',3:'SUB',4:'DIV',5:'SDIV',6:'MOD',7:'SMOD',8:'ADDMOD',9:'MULMOD',0xa:'EXP',0xb:'SIGNEXTEND',0x10:'LT',0x11:'GT',0x12:'SLT',0x13:'SGT',0x14:'EQ',0x15:'ISZERO',0x16:'AND',0x17:'OR',0x18:'XOR',0x19:'NOT',0x1a:'BYTE',0x1b:'SHL',0x1c:'SHR',0x1d:'SAR',0x1e:'CLZ',0x20:'KECCAK256'}
for op in range(0, 0x21):
    print(hex(op), names.get(op, ''), hex(rd(base + 8 * op)))
