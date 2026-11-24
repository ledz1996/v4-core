# Lists 0x5b bytes inside PUSH data of the PoolManager runtime and checks
# whether any PUSH constant in the code equals such an offset (a possible
# jump target), plus the offsets of all valid JUMPDESTs.
import json, sys
j = json.load(open(sys.argv[1]))
rt = j['runtime']
if isinstance(rt, dict):
    rt = rt.get('object') or rt.get('bytecode') or rt.get('hex')
code = bytes.fromhex(rt[2:] if rt.startswith('0x') else rt)
n = len(code)
valid, inpush, consts = set(), [], []
i = 0
while i < n:
    op = code[i]
    if op == 0x5b:
        valid.add(i)
    if 0x60 <= op <= 0x7f:
        k = op - 0x5f
        data = code[i+1:i+1+k]
        for d in range(1, k+1):
            if i+d < n and code[i+d] == 0x5b:
                inpush.append(i+d)
        nxt = code[i+1+k] if i+1+k < n else None
        consts.append((i, int.from_bytes(data, 'big'), nxt))
        i += 1 + k
    else:
        i += 1
cset = {}
for pc, v, nxt in consts:
    cset.setdefault(v, []).append((pc, nxt))
hits = {p: cset.get(p, []) for p in inpush}
print(json.dumps({"runtimeBytes": n, "validJumpdests": len(valid),
  "jumpdestBytesInPushData": inpush,
  "pushConstantsEqualToThoseOffsets": {str(k): v for k, v in hits.items() if v},
  "maxValidJumpdest": max(valid)}, indent=1))
