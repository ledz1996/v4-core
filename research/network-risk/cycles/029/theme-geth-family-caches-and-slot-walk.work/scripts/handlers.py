"""Extract the bodies of the arithmetic, comparison, shift, keccak, memory, storage, transient storage and jump
handlers from each fork's core/vm/instructions.go and compare them with go-ethereum master bbafd66.
Usage: python3 handlers.py <out.json>"""
import re, sys, json, glob, os
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMES = ['opAdd', 'opSub', 'opMul', 'opDiv', 'opSdiv', 'opMod', 'opSmod', 'opExp', 'opSignExtend', 'opNot', 'opLt', 'opGt', 'opSlt', 'opSgt',
         'opEq', 'opIszero', 'opAnd', 'opOr', 'opXor', 'opByte', 'opAddmod', 'opMulmod', 'opSHL', 'opSHR', 'opSAR', 'opKeccak256',
         'opCallDataLoad', 'opCallDataCopy', 'opReturnDataCopy', 'opMload', 'opMstore', 'opMstore8', 'opSload', 'opSstore', 'opJump', 'opJumpi',
         'opJumpdest', 'opTload', 'opTstore', 'opMcopy', 'opPush0', 'opPush1', 'opPush2', 'opReturn', 'opRevert']
def bodies(path):
    s = open(path).read(); out = {}
    for n in NAMES:
        m = re.search(r'\nfunc ' + n + r'\(pc \*uint64,[^\n]*\{\n(.*?)\n\}\n', s, re.S)
        out[n] = re.sub(r'\s+', ' ', m.group(1)).strip() if m else None
    return out
base = bodies(glob.glob(W + '/dl/x/github.com_ethereum_go-ethereum@v1.17.11*/github.com/ethereum/go-ethereum@*/core/vm/instructions.go')[0])
res = {}
for f in sorted(glob.glob(W + '/dl/forks/*/instructions.go')):
    b = bodies(f); name = f.split('/')[-2]
    res[name] = {n: ('same' if b[n] == base[n] else 'missing' if b[n] is None else 'differs') for n in NAMES}
    res[name + ':diff'] = {n: {'fork': b[n], 'master': base[n]} for n in NAMES if b[n] != base[n] and b[n] is not None}
json.dump(res, open(sys.argv[1], 'w'), indent=1)
for k, v in res.items():
    if not k.endswith(':diff'): print(k, {n: s for n, s in v.items() if s != 'same'})
