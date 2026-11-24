"""The PoolManager at the bytecode level.

1. Static facts of the deployed runtime bytecode: which opcodes it contains, its jump
   destinations, 0x5b bytes inside PUSH data, PUSH data that crosses 16, 32 and 64
   byte chunk borders (where vectorised jump destination scans can go wrong), and
   whether every constant jump target is a valid destination.
2. The scripts of pmdiff.py and pmdiff2.py run in the reference interpreter of
   pyevm.py, instruction by instruction, and compared with the answer of the Ethereum
   node that pmdiff recorded. Equal answers mean the node, and with it every network
   that matched the node, computes what the specification says for this bytecode.
3. Coverage: which instructions and which sides of each conditional jump the scripts
   executed.

Usage: python3 bytecode.py <pmdiff.json> <pmdiff2.json> <out.json> [maxStepsPerScript]
"""
import sys, json, random, hashlib, time
from evm import rpc
import pmdiff as P, pmdiff2 as Q
from pyevm import World, NAMES, jumpdests


def static_facts(code):
    hist = {}; i = 0; n = len(code); push_5b = []; cross = {16: 0, 32: 0, 64: 0}; targets = []; prev = None
    instr = 0
    while i < n:
        op = code[i]; instr += 1
        hist[op] = hist.get(op, 0) + 1
        k = op - 0x5f if 0x60 <= op <= 0x7f else 0
        if k:
            dat = code[i + 1:i + 1 + k]
            for j, b in enumerate(dat):
                if b == 0x5b: push_5b.append(i + 1 + j)
            for c in cross:
                if (i // c) != ((i + k) // c): cross[c] += 1
            prev = (op, int.from_bytes(dat, 'big'))
        else:
            if op in (0x56, 0x57) and prev is not None: targets.append((i, prev[1]))
            prev = None
        i += k + 1
    jd = jumpdests(code)
    naive = {p for p, b in enumerate(code) if b == 0x5b}
    return {'bytes': n, 'instructions': instr, 'distinctOpcodes': len(hist),
            'opcodes': {NAMES.get(o, hex(o)): c for o, c in sorted(hist.items(), key=lambda x: -x[1])},
            'unknownOpcodes': sorted(hex(o) for o in hist if o not in NAMES),
            'jumpdests': len(jd), 'bytes5bInsidePushData': len(push_5b), 'bytes5bInsidePushDataAt': push_5b,
            'pushDataCrossingChunk': cross, 'constantJumps': len(targets),
            'constantJumpsToInvalidTarget': [(pc, t) for pc, t in targets if t not in jd],
            'constantJumpsIntoPushData': [(pc, t) for pc, t in targets if t in naive and t not in jd],
            'endsInsidePush': i > n}


def worlds(code):
    pm, drv = int(P.PM, 16), int(P.DRV, 16)
    def w1(): return World({pm: code, drv: P.driver()})
    def w2():
        codes = {pm: code, drv: Q.driver(), Q.TOKEN: Q.token()}
        for f in Q.HOOK_FLAGS: codes[Q.HOOK_BASE | f] = Q.hook()
        return World(codes, {pm: 10 ** 19})
    return w1, w2


if __name__ == '__main__':
    f1, f2, out = sys.argv[1], sys.argv[2], sys.argv[3]
    max_steps = int(sys.argv[4]) if len(sys.argv) > 4 else 3_000_000
    code = P.fetch_code(); pm, drv = int(P.PM, 16), int(P.DRV, 16)
    facts = static_facts(code)
    print('static:', {k: v for k, v in facts.items() if k not in ('opcodes', 'bytes5bInsidePushDataAt')})
    w1, w2 = worlds(code)
    r1 = json.load(open(f1)); r2 = json.load(open(f2))
    rnd = random.Random(7_2026_11_24); s1 = [P.script(rnd) for _ in range(r1['scripts'])]
    rnd = random.Random(11_2026_11_24); s2 = [Q.script(rnd, i) for i in range(r2['scripts'])]
    cover = set(); branches = {}; ops = {}; res = {'equal': 0, 'different': [], 'heavy': 0, 'steps': 0}
    t0 = time.time()
    for name, scripts, ref, mk in (('pmdiff', s1, r1['referenceHashes'], w1), ('pmdiff2', s2, r2['referenceHashes'], w2)):
        for i, (data, kinds, meta) in enumerate(scripts):
            w = mk(); w.max_steps = max_steps
            try:
                ok, ret = w.call(0, drv, 0, data, False, 0)
            except TimeoutError:
                res['heavy'] += 1; ret = None
            res['steps'] += w.steps
            cover |= w.cover.get(pm, set())
            for (a, pc), o in w.branches.items():
                if a == pm: branches.setdefault(pc, set()).update(o)
            for o, c in w.ops.items(): ops[o] = ops.get(o, 0) + c
            if ret is None: continue
            if hashlib.sha256(ret).hexdigest() == ref[i]: res['equal'] += 1
            else: res['different'].append([name, i])
    # coverage over instruction starts
    starts = []; i = 0
    while i < len(code):
        starts.append(i); op = code[i]; i += op - 0x5e if 0x60 <= op <= 0x7f else 1
    jumpis = [p for p in starts if code[p] == 0x57]
    both = sum(1 for p in jumpis if branches.get(p) == {True, False}); one = sum(1 for p in jumpis if len(branches.get(p, ())) == 1)
    res.update({'instructionsExecuted': len(cover & set(starts)), 'instructions': len(starts), 'jumpi': len(jumpis), 'jumpiBothSides': both, 'jumpiOneSide': one,
                'jumpiNever': len(jumpis) - both - one, 'seconds': round(time.time() - t0)})
    present = set(code[p] for p in starts)
    res['opcodesExecuted'] = sorted(NAMES.get(o, hex(o)) for o in ops)
    res['opcodesPresentNotExecuted'] = sorted(NAMES.get(o, hex(o)) for o in present if o not in ops)
    print({k: v for k, v in res.items() if k not in ('opcodesExecuted',)})
    json.dump({'static': facts, 'run': res}, open(out, 'w'), indent=1)
