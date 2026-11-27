#!/usr/bin/env python3
"""PoolManager scripts of tools/opdiff/pmdiff.py (seed 7_2026_11_24) and pmdiff2.py
(seed 11_2026_11_24) run through tools/opdiff/pyevm.py on the bytecode built from this
checkout (PM_BUILD=research/network-risk/build/PoolManager.json), once with pyevm's own
DIV and MOD, and once per variant of revdiv.py with DIV and MOD replaced by the
transcription. Every script's full return data is compared with the baseline.
It also counts how many DIV and MOD instructions execute with a zero divisor and with a
divisor whose top limb is nonzero, so it is known which planted faults the PoolManager
can reach at all.
Usage: PM_BUILD=... python3 -I pmrev.py <outdir> [n1] [n2]
"""
import sys, os, json, random, hashlib, types, time

HERE = os.path.dirname(os.path.abspath(__file__))
OPD = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'tools', 'opdiff'))
sys.path.insert(0, OPD); sys.path.insert(0, HERE)
import pmdiff as P, pmdiff2 as Q  # noqa: E402
import revdiv  # noqa: E402

SRC = open(os.path.join(OPD, 'pyevm.py')).read()
OLD_DIV = "elif op == 0x04: a = st.pop(); b = st[-1]; st[-1] = a // b if b else 0"
OLD_MOD = "elif op == 0x06: a = st.pop(); b = st[-1]; st[-1] = a % b if b else 0"
assert SRC.count(OLD_DIV) == 1 and SRC.count(OLD_MOD) == 1
NEW_DIV = "elif op == 0x04: a = st.pop(); b = st[-1]; _STAT(0x04, b); st[-1] = _DIV(a, b)"
NEW_MOD = "elif op == 0x06: a = st.pop(); b = st[-1]; _STAT(0x06, b); st[-1] = _MOD(a, b)"
PATCHED = SRC.replace(OLD_DIV, NEW_DIV).replace(OLD_MOD, NEW_MOD)


def load(div, rem, stats):
    mod = types.ModuleType('pyevm_variant'); mod.__dict__['__file__'] = os.path.join(OPD, 'pyevm.py')
    mod.__dict__['_DIV'] = div; mod.__dict__['_MOD'] = rem

    def stat(op, b):
        k = ('DIV' if op == 4 else 'MOD') + ('_zero' if b == 0 else '_topLimb' if b >> 192 else '_other')
        stats[k] = stats.get(k, 0) + 1
    mod.__dict__['_STAT'] = stat
    exec(compile(PATCHED, 'pyevm_variant', 'exec'), mod.__dict__)
    return mod


def worlds(World, code):
    pm, drv = int(P.PM, 16), int(P.DRV, 16)
    def w1(): return World({pm: code, drv: P.driver()})
    def w2():
        codes = {pm: code, drv: Q.driver(), Q.TOKEN: Q.token()}
        for f in Q.HOOK_FLAGS: codes[Q.HOOK_BASE | f] = Q.hook()
        return World(codes, {pm: 10 ** 19})
    return w1, w2


def run_all(World, code, s1, s2, max_steps=3_000_000):
    w1, w2 = worlds(World, code); drv = int(P.DRV, 16); outs = []
    for scripts, mk in ((s1, w1), (s2, w2)):
        for data, kinds, meta in scripts:
            w = mk(); w.max_steps = max_steps
            try:
                ok, ret = w.call(0, drv, 0, data, False, 0); outs.append((ok, ret.hex()))
            except TimeoutError:
                outs.append(('heavy', ''))
    return outs


if __name__ == '__main__':
    out = sys.argv[1]; n1 = int(sys.argv[2]) if len(sys.argv) > 2 else 200; n2 = int(sys.argv[3]) if len(sys.argv) > 3 else 200
    code = P.fetch_code()
    rnd = random.Random(7_2026_11_24); s1 = [P.script(rnd) for _ in range(n1)]
    rnd = random.Random(11_2026_11_24); s2 = [Q.script(rnd, i) for i in range(n2)]
    import pyevm
    t0 = time.time(); base = run_all(pyevm.World, code, s1, s2); tb = time.time() - t0
    res = {'poolManagerRuntimeBytes': len(code), 'poolManagerSha256': hashlib.sha256(code).hexdigest(),
           'scripts': {'pmdiff': n1, 'pmdiff2': n2}, 'seeds': {'pmdiff': 7_2026_11_24, 'pmdiff2': 11_2026_11_24},
           'baselineSeconds': round(tb), 'baselineHeavy': sum(1 for o in base if o[0] == 'heavy'), 'variants': {}}
    print('baseline', len(base), 'scripts', round(tb), 's', flush=True)
    for vn, (div, rem) in revdiv.VARIANTS.items():
        stats = {}; mod = load(div, rem, stats)
        got = run_all(mod.World, code, s1, s2)
        diff = [i for i, (a, b) in enumerate(zip(got, base)) if a != b]
        res['variants'][vn] = {'differentScripts': len(diff), 'differentIndices': diff[:50],
                               'mismatchRecords': [{'index': i, 'set': 'pmdiff' if i < n1 else 'pmdiff2', 'baseline': base[i], 'variant': got[i]} for i in diff[:5]],
                               'divModOperandClasses': stats}
        print(vn, len(diff), stats, flush=True)
    json.dump(res, open(os.path.join(out, 'pmrev.json'), 'w'), indent=1)
