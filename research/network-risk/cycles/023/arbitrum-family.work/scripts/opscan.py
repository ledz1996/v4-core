# Walk bytecode linearly and count opcodes at instruction positions (not inside PUSH data).
import json, sys, collections
code = bytes.fromhex(json.load(open(sys.argv[1]))['result'][2:])
c = collections.Counter(); pos = collections.defaultdict(list)
i = 0
while i < len(code):
    op = code[i]; c[op] += 1; pos[op].append(i)
    i += 1 + (op - 0x5f if 0x60 <= op <= 0x7f else 0)
print('len', len(code))
for op in [0x1e, 0x4b, 0xe6, 0xe7, 0xe8, 0xfe, 0x5c, 0x5d, 0x5e, 0x5f, 0xf0, 0xff]:
    print(hex(op), c[op], pos[op][:10])
undefined = [hex(o) for o in c if o in range(0x0c,0x10) or o in range(0x1e,0x20) or o in range(0x21,0x30) or o in range(0x4b,0x50) or o in range(0xa5,0xf0) or o in (0xf6,0xf7,0xf8,0xf9,0xfb,0xfc)]
print('opcodes currently undefined or newly defined, at instruction positions:', undefined, [(h, c[int(h,16)], pos[int(h,16)][:5]) for h in undefined])
