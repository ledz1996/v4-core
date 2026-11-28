"""Task 4 (Avalanche): runs extstate.partitionStateKeysHook.TransformStateKey of the shipped avalanchego v1.15.3
binaries in the x86-64 and AArch64 models on the storage key shapes of the PoolManager, and lists which libevm
core/state and extstate functions call core/state.transformStateKey (from the disassembly, nothing executed).

Go ABI: the hook takes addr [20]byte and key [32]byte on the stack (arrays are never register-assigned) and returns
the key on the stack. At the entry SP S: addr at S+8, key at S+0x1c, result at S+0x40 on both architectures
(read from the prologue of both builds). The reference clears bit 248 (key[0] &^= 1).
Key shapes: constant slots 0..63, keccak256 of (word, slot) for random words and the PoolManager's mapping slots,
those outputs plus 0..3, words with bit 248 set and clear, edge words. Seed 31_0731_06.
usage: python3 -I avaxkey.py <target> <out.json>"""
import json, os, random, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import goshim as G, models, targets
from models import X64, A64Mem, ACPU, AProg, XProg, rewrite_rip, Stop, SP_TOP
from evm import keccak

TGT, OUT = sys.argv[1], sys.argv[2]
TG = targets.get(TGT); arch = TG['arch']
fns = G.fnlist(TG['fns'])
HOOK = 'github.com/ava-labs/avalanchego/vms/saevm/cchain/libevm/extstate.partitionStateKeysHook.TransformStateKey'
lo, hi = fns[HOOK]
text = G.disasm(TG['bin'], arch, [(lo, hi)])
img = G.Image(TG['bin'])
prog = XProg(rewrite_rip(text)) if arch == 'amd64' else AProg([text])
M = G.M


def run(addr, key):
    if arch == 'amd64':
        cpu = X64(prog, img, {}, {})
        S = 0x7ffff0000000 - 8
        cpu.write(S + 8, 20, addr); cpu.write(S + 0x1c, 32, int.from_bytes(key.to_bytes(32, 'big'), 'little'))
        cpu.write(S + 0x40, 32, G.GUARD)
        cpu.r['r14'] = G.GSTRUCT; cpu.y[15] = 0
        cpu.call(lo, [], maxsteps=10000)
        r = cpu.read(S + 0x40, 32)
        k2 = cpu.read(S + 0x1c, 32)
    else:
        mem = A64Mem(img)
        for a, b in models.OK_RANGES:
            mem.add(a, b - a)
        cpu = ACPU(prog, mem, externs={})
        S = SP_TOP
        mem.write(S + 8, 20, addr); mem.write(S + 0x1c, 32, int.from_bytes(key.to_bytes(32, 'big'), 'little'))
        mem.write(S + 0x40, 32, G.GUARD)
        cpu.x[31] = S; cpu.x[28] = G.GSTRUCT; cpu.x[29] = 0
        cpu.call(lo, [], maxsteps=10000)
        r = mem.read(S + 0x40, 32); k2 = mem.read(S + 0x1c, 32)
    out = int.from_bytes(r.to_bytes(32, 'little'), 'big')
    if int.from_bytes(k2.to_bytes(32, 'little'), 'big') != key:
        raise Stop('argument slot changed')
    return out, cpu.steps


def ref(key):
    return key & ~(1 << 248) & M


def shapes():
    rnd = random.Random(310731_06)
    for s in range(64):
        yield 'const', s
    for s in list(range(16)) + [rnd.getrandbits(256) for _ in range(16)]:
        for i in range(400):
            w = rnd.getrandbits(rnd.choice((160, 256, 24, 64)))
            k = int.from_bytes(keccak(w.to_bytes(32, 'big') + s.to_bytes(32, 'big')), 'big')
            for d in range(4):
                yield 'keccak+%d' % d, (k + d) & M
    for i in range(4000):
        w = rnd.getrandbits(256)
        yield 'bit248-set', w | (1 << 248)
        yield 'bit248-clear', w & ~(1 << 248)
    for w in (0, M, 1 << 248, (1 << 248) - 1, (1 << 249) - 1, M ^ (1 << 248), 1 << 255, 0xff << 248, 0x01 << 248 | 1):
        yield 'edge', w


res = {'target': TGT, 'hook': HOOK, 'range': [hex(lo), hex(hi)], 'seed': 310731_06, 'cases': 0, 'mismatches': 0,
       'changed': 0, 'byTag': {}, 'records': [], 'started': time.time()}
rnd = random.Random(310731_07)
for tag, key in shapes():
    addr = rnd.getrandbits(160)
    got, steps = run(addr, key)
    want = ref(key)
    res['cases'] += 1; res['byTag'][tag] = res['byTag'].get(tag, 0) + 1
    res['changed'] += int(want != key)
    if got != want:
        res['mismatches'] += 1
        res['records'].append({'tag': tag, 'key': hex(key), 'model': hex(got), 'reference': hex(want)})
res['seconds'] = time.time() - res.pop('started')

# callers of transformStateKey and of the hook, found by scanning every core/state, core/vm and extstate function
calls = {}
targ = {fns['github.com/ava-labs/libevm/core/state.transformStateKey'][0]: 'transformStateKey', lo: 'hook'}
hp = fns.get('github.com/ava-labs/avalanchego/vms/saevm/cchain/libevm/extstate.(*partitionStateKeysHook).TransformStateKey')
if hp:
    targ[hp[0]] = 'hook-ptr-wrapper'
pfx = ('github.com/ava-labs/libevm/core/state.', 'github.com/ava-labs/libevm/core/vm.',
       'github.com/ava-labs/avalanchego/vms/saevm/cchain/libevm/extstate.')
names = [n for n in fns if n.startswith(pfx)]
for n in names:
    a, b = fns[n]
    t = G.disasm(TG['bin'], arch, [(a, b)])
    for l in t.splitlines():
        if ('call' in l or '\tbl\t' in l) and any(('%x' % x) in l for x in targ):
            for x, nm in targ.items():
                if ('%x ' % x) in l or ('0x%x' % x) in l or l.rstrip().endswith('%x' % x) or (' %x <' % x) in l:
                    calls.setdefault(nm, set()).add(n)
res['callers'] = {k: sorted(v) for k, v in calls.items()}
res['functionsScanned'] = len(names)
tr = [n for n in names if 'TransientState' in n]
res['transientFunctions'] = tr
json.dump(res, open(OUT, 'w'), indent=1)
print(OUT, {k: res[k] for k in ('cases', 'mismatches', 'changed', 'functionsScanned')}, res['callers'])
