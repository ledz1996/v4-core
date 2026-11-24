"""Runs the built PoolManager in the reference interpreter twice: once as pyevm.py has it, and once
with the opcodes that Monad v0.16.5 compiles inline (CALLER, CALLVALUE, CALLDATALOAD,
RETURNDATASIZE, CALLDATASIZE) replaced by the x86 transcriptions of settlejit.py. Operand
locations follow sites.json: an offset the compiler sees as a literal takes the literal path,
any other one takes a general register (live or not), AVX or stack slot path at random.
Compares the bytes every script returns and counts how often each transcribed path ran inside
the settlement functions (Currency.transfer, balanceOfSelf, CurrencyDelta, CurrencyReserves,
PoolManager._settle/sync/take/settle/settleFor/mint/burn/clear/unlock).

The opcodes Monad hands to a runtime helper (KECCAK256, TLOAD, TSTORE, CALLDATACOPY,
RETURNDATACOPY, MCOPY, CALL, STATICCALL, SELFBALANCE) call the same C++ function in the
interpreter and in compiled code, so they are left as pyevm has them; see the research file.

Usage: PM_BUILD=research/network-risk/build/PoolManager.json python3 -I compiled_run.py <out.json> [n2] [n3]
(run from the repository root)"""
import sys, os, json, random, hashlib, time, types
here = os.path.dirname(os.path.abspath(__file__))
root = os.path.abspath(os.path.join(here, '..', '..', '..'))
sys.path.insert(0, os.path.join(root, 'tools', 'opdiff')); sys.path.insert(0, here)
import settlejit as J
import pyevm
import pmdiff as P, pmdiff2 as Q, pmdiff3 as R

SITES = {s['pc']: s for s in json.load(open(os.path.join(here, 'sites.json')))['sites']}
SETTLE_FN = ('CurrencyLibrary.transfer', 'CurrencyLibrary.balanceOfSelf', 'CurrencyDelta', 'CurrencyReserves', 'PoolManager.unlock',
             'NonzeroDeltaCount', 'Lock.', 'CustomRevert.bubbleUpAndRevertWith')
RNG = random.Random(20261124)
COUNT = {}


class H:
    pm = None

    @staticmethod
    def note(addr, pc, op):
        if addr != H.pm: return
        s = SITES.get(pc); fn = (s or {}).get('fn') or ''
        k = (op, 'settlement' if any(t in fn for t in SETTLE_FN) else 'other')
        COUNT[k] = COUNT.get(k, 0) + 1

    @staticmethod
    def caller(addr, pc, c):
        H.note(addr, pc, 'CALLER')
        return J.read_context_address(J.CPU(RNG), c.to_bytes(20, 'big'), RNG.random() < 0.5)

    @staticmethod
    def callvalue(addr, pc, v):
        H.note(addr, pc, 'CALLVALUE')
        return J.read_context_word(J.CPU(RNG), v.to_bytes(32, 'big'), RNG.random() < 0.5)

    @staticmethod
    def rdsize(addr, pc, n):
        H.note(addr, pc, 'RETURNDATASIZE')
        return J.read_context_uint32_to_word(J.CPU(RNG), n)

    @staticmethod
    def cdsize(addr, pc, n):
        H.note(addr, pc, 'CALLDATASIZE')
        return J.read_context_uint32_to_word(J.CPU(RNG), n)

    @staticmethod
    def cdl(addr, pc, data, off):
        H.note(addr, pc, 'CALLDATALOAD')
        s = SITES.get(pc) if addr == H.pm else None
        if s and s['operandsTopFirst'] and s['operandsTopFirst'][0] is not None:
            loc, live = 'lit', None
        else:
            loc = RNG.choice(['gpr', 'gpr', 'avx', 'stack'])
            live = (RNG.random() < 0.5, RNG.randrange(3)) if loc == 'gpr' else (None, RNG.randrange(14))
        return J.calldataload(J.CPU(RNG), bytes(data), off, loc, live)


def compiled_module():
    src = open(pyevm.__file__).read()
    rep = [("elif op == 0x33: st.append(caller)", "elif op == 0x33: st.append(H.caller(code_addr, pc, caller))"),
           ("elif op == 0x34: st.append(value)", "elif op == 0x34: st.append(H.callvalue(code_addr, pc, value))"),
           ("off = st.pop(); st.append(int.from_bytes(data[off:off + 32].ljust(32, b'\\0'), 'big') if off < len(data) else 0)",
            "off = st.pop(); st.append(H.cdl(code_addr, pc, data, off))"),
           ("elif op == 0x36: st.append(len(data))", "elif op == 0x36: st.append(H.cdsize(code_addr, pc, len(data)))"),
           ("elif op == 0x3d: st.append(len(rd))", "elif op == 0x3d: st.append(H.rdsize(code_addr, pc, len(rd)))")]
    for a, b in rep:
        assert src.count(a) == 1, a
        src = src.replace(a, b)
    m = types.ModuleType('pyevm_monad_compiled'); m.__dict__['H'] = H; m.__file__ = pyevm.__file__
    sys.path.insert(0, os.path.dirname(pyevm.__file__))
    exec(compile(src, 'pyevm_monad_compiled', 'exec'), m.__dict__)
    return m


def main():
    out = sys.argv[1]; n2 = int(sys.argv[2]) if len(sys.argv) > 2 else 300; n3 = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    code = P.fetch_code(); H.pm = int(P.PM, 16)
    C = compiled_module()
    t0 = time.time(); res = {'codeSha256': hashlib.sha256(code).hexdigest(), 'sets': {}}
    # pmdiff2: token double with nine transfer shapes, sync and settle against a moving balance, native payouts
    rnd = random.Random(11_2026_11_24); s2 = [Q.script(rnd, i) for i in range(n2)]
    drv2 = int(P.DRV, 16)
    def w2(mod):
        codes = {H.pm: code, drv2: Q.driver(), Q.TOKEN: Q.token()}
        for f in Q.HOOK_FLAGS: codes[Q.HOOK_BASE | f] = Q.hook()
        return mod.World(codes, {H.pm: 10 ** 19})
    rnd = random.Random(3_2026_11_24); s3 = [R.build(rnd, i, code) for i in range(n3)]
    def w3(mod):
        wd = mod.World(R.codes(code), {R.PMI: 10 ** 19}); wd.storage[(R.PMI, 0)] = R.DRV; return wd
    for name, scripts, mk, drv in (('pmdiff2', s2, w2, drv2), ('pmdiff3', s3, w3, R.DRV)):
        eq = 0; diff = []; heavy = 0; calls = 0
        for i, (data, kinds, meta) in enumerate(scripts):
            a = mk(pyevm); b = mk(C); a.max_steps = b.max_steps = 4_000_000
            try:
                ra = a.call(0, drv, 0, data, False, 0); rb = b.call(0, drv, 0, data, False, 0)
            except TimeoutError:
                heavy += 1; continue
            calls += len(kinds)
            if ra == rb and a.storage == b.storage and a.transient == b.transient and a.balances == b.balances: eq += 1
            else: diff.append(i)
        res['sets'][name] = {'scripts': len(scripts), 'equal': eq, 'different': diff, 'skippedHeavy': heavy, 'callsInScripts': calls}
        print(name, res['sets'][name], round(time.time() - t0), 's', flush=True)
    res['executions'] = [{'op': k[0], 'where': k[1], 'count': v} for k, v in sorted(COUNT.items())]
    res['pathCoverage'] = J.COV
    json.dump(res, open(out, 'w'), indent=1)
    print(json.dumps(res['executions'])); print(J.COV)


main()
