"""Cycle 33. Check that block.py's operand rewriting reaches the edges it aims at: for each whole-block run kind, draw
sets the same way (pyevm.py only, no native run), trace the block again after the rewrite, and count how often the
words compared by the block's LT, GT and EQ are equal, one apart, or equal in the top limb, how often the MULMOD
remainder is zero, and how often each JUMPI side is taken.
usage: python3 -I edgecheck.py <out.json> <n per block>"""
import sys, os, json, random, re
OUT = sys.argv[1]; N = int(sys.argv[2])
sys.argv = [sys.argv[0], '/tmp', '0']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import term
from term import ra, pyevm, CODE, JD, M, M64, STATES
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'block.py')).read().replace('\nmain()\n', '\n')
bk = {'__file__': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'block.py'), '__name__': 'bk'}
exec(compile(src, 'block.py', 'exec'), bk)
rnd = random.Random(3336)
res = {'seed': 3336, 'n': N, 'blocks': {}}
for b in bk['BLOCKS']:
    sts = [s for s in STATES if s['b'] == b]
    e = [s for s in sts if s['w'] == 'e'][0]; t = [s for s in sts if s['w'] == 't'][0]
    lo = e['min']; n_in = e['top'] - lo + 1; depth = t['top'] - lo + 1
    cnt = {}
    def bump(k): cnt[k] = cnt.get(k, 0) + 1
    for i in range(N):
        entry = [ra['words'](rnd, 'X', 0) for _ in range(n_in)]
        if i % 3 == 1:
            pre, bd = bk['evm_block'](b, t['pc'], entry)
            ops = bk['trace_ops'](pre, bd, (0x10, 0x11, 0x14))
            if ops:
                pc_, op, a, bb = rnd.choice(ops)
                which = rnd.randrange(2); srcw = (a, bb)[which]; other = (a, bb)[1 - which]
                if srcw in entry:
                    k = entry.index(srcw)
                    mode = rnd.choice(['eq', 'plus1', 'minus1', 'tophigh', 'zero'])
                    entry[k] = {'eq': other, 'plus1': (other + 1) & M, 'minus1': (other - 1) & M,
                                'tophigh': (other & (M64 << 192)) | rnd.getrandbits(192), 'zero': 0}[mode]
        if i % 3 == 2:
            pre, bd = bk['evm_block'](b, t['pc'], entry)
            code = pre + bd + b'\x00'; w = pyevm.World({0xaa: code}); w.trace = []; w.trace_stack = 3; w.call(1, 0xaa, 0, b'', False, 0)
            mm = [(pc - len(pre), stk) for d, pc, op, stk in w.trace if pc >= len(pre) and op == 0x09]
            if mm:
                pc_, stk = mm[0]; x, y, mod = stk[-1], stk[-2], stk[-3]
                if mod and x in entry: entry[entry.index(x)] = (mod * rnd.choice([0, 1, 2, rnd.getrandbits(64)])) & M
                elif mod and y in entry: entry[entry.index(y)] = (mod * rnd.choice([0, 1, 2, rnd.getrandbits(64)])) & M
        pre, bd = bk['evm_block'](b, t['pc'], entry)
        for pc_, op, a, bb in bk['trace_ops'](pre, bd, (0x10, 0x11, 0x14)):
            nm = {0x10: 'LT', 0x11: 'GT', 0x14: 'EQ'}[op] + '@%x' % (b + pc_)
            if a == bb: bump(nm + ':equal')
            elif (a - bb) & M in (1, M): bump(nm + ':one-apart')
            elif a >> 192 == bb >> 192: bump(nm + ':top-limb-equal')
            else: bump(nm + ':other')
            if a == 0 or bb == 0: bump(nm + ':an-operand-zero')
        code = pre + bd + b'\x00'; w = pyevm.World({0xaa: code}); w.trace = []; w.trace_stack = 3; w.call(1, 0xaa, 0, b'', False, 0)
        for d, pc, op, stk in w.trace:
            if pc >= len(pre) and op == 0x09:
                x, y, mod = stk[-1], stk[-2], stk[-3]
                bump('MULMOD@%x:remainder-%s' % (b + pc - len(pre), 'zero' if mod == 0 or (x * y) % mod == 0 else 'nonzero'))
        ref = bk['run_ref'](pre, bd, depth)
        if term.TERM[t['op'] - 1000] == 'JumpI': bump('JumpI:' + ('taken' if ref[1] else 'fall'))
    res['blocks'][hex(b)] = dict(sorted(cnt.items()))
    print(hex(b), dict(sorted(cnt.items())), flush=True)
json.dump(res, open(OUT, 'w'), indent=1)
