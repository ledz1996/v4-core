"""Print the handler addresses of the arithmetic opcodes from one 256-entry table. usage: handlers.py <rel> <table hex>"""
import sys, json
rel={}
for l in open(sys.argv[1]):
    a,b=l.split(); rel[int(a,16)]=int(b,16)
t=int(sys.argv[2],16)
OPS = {'ADD': 1, 'MUL': 2, 'SUB': 3, 'DIV': 4, 'SDIV': 5, 'MOD': 6, 'SMOD': 7, 'ADDMOD': 8, 'MULMOD': 9,
       'EXP': 10, 'SIGNEXTEND': 11, 'LT': 0x10, 'GT': 0x11, 'SLT': 0x12, 'SGT': 0x13, 'EQ': 0x14, 'ISZERO': 0x15,
       'AND': 0x16, 'OR': 0x17, 'XOR': 0x18, 'NOT': 0x19, 'BYTE': 0x1a, 'SHL': 0x1b, 'SHR': 0x1c, 'SAR': 0x1d}
print(json.dumps({k: hex(rel[t+8*v]) for k,v in OPS.items()}))
