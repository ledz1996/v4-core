# Run the targeted.py and battery.py arithmetic vectors through the revm-interpreter 43.0.1 handlers
# over ruint 1.20.0, compiled by rustc 1.97.0 (LLVM 22.1.6) for kona's mips64-unknown-none target spec
# (build/ops.elf) and executed in mips64emu.py with Cannon MIPS64 semantics.
# Usage: python3 -I run_vectors.py <tools/opdiff dir> <out.json> [fault ...]
import sys, os, json, time, collections
from multiprocessing import Pool
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here); sys.path.insert(1, sys.argv[1])
from mips64emu import Emu, Fault
import targeted, battery

MASK = (1 << 256) - 1
FN = {'ADD': 'evm_add', 'SUB': 'evm_sub', 'MUL': 'evm_mul', 'DIV': 'evm_div', 'SDIV': 'evm_sdiv', 'MOD': 'evm_mod',
      'SMOD': 'evm_smod', 'ADDMOD': 'evm_addmod', 'MULMOD': 'evm_mulmod', 'EXP': 'evm_exp', 'SIGNEXTEND': 'evm_signextend',
      'LT': 'evm_lt', 'GT': 'evm_gt', 'SLT': 'evm_slt', 'SGT': 'evm_sgt', 'EQ': 'evm_eq', 'ISZERO': 'evm_iszero',
      'AND': 'evm_and', 'OR': 'evm_or', 'XOR': 'evm_xor', 'NOT': 'evm_not', 'BYTE': 'evm_byte', 'SHL': 'evm_shl',
      'SHR': 'evm_shr', 'SAR': 'evm_sar'}
E = None


def init(faults):
    global E
    E = Emu(os.path.join(here, 'build', 'ops.elf'), faults)


def evm(op, a, b, c):
    if op in FN:
        return E.call(FN[op], a, b, c)
    if op == 'DIVUP':  # mulDivRoundingUp tail: div(a,b) + (mod(a,b) > 0)
        return (E.call('evm_div', a, b, 0) + int(E.call('evm_mod', a, b, 0) > 0)) & MASK
    if op == 'MULDIV512':  # FullMath.mulDiv 512-bit product and remainder words
        mm = E.call('evm_mulmod', a, b, MASK); p0 = E.call('evm_mul', a, b, 0)
        p1 = (mm - p0 - int(mm < p0)) & MASK; r = E.call('evm_mulmod', a, b, c)
        return ((p1 ^ r) + p0) & MASK
    return None


def work(chunk):
    bad = []; per = collections.Counter(); n = 0; err = 0
    for t in chunk:
        op, a, b, c = t[0], t[1], t[2], t[3]
        try:
            got = evm(op, a, b, c)
        except Fault as e:
            got = 'fault:' + str(e); err += 1
        if got is None:
            continue
        exp = battery.reference(op, a, b, c, b'')
        n += 1; per[op] += 1
        if got != exp:
            bad.append([op, hex(a), hex(b), hex(c), str(got) if isinstance(got, str) else hex(got), hex(exp)])
    return n, per, bad, err, E.steps


def run(V, faults, procs):
    chunks = [V[i::procs * 8] for i in range(procs * 8)]
    with Pool(procs, initializer=init, initargs=(faults,)) as p:
        res = p.map(work, chunks)
    n = sum(r[0] for r in res); per = collections.Counter()
    bad = []; err = 0; steps = 0
    for r in res:
        per.update(r[1]); bad += r[2]; err += r[3]
    badper = collections.Counter(x[0] for x in bad)
    return {'faults': list(faults), 'ran': n, 'perOp': dict(per), 'mismatch': len(bad), 'mismatchPerOp': dict(badper),
            'emuFaults': err, 'first': bad[:5]}


if __name__ == '__main__':
    out = sys.argv[2]; fl = sys.argv[3:]
    procs = os.cpu_count() or 4
    VT = targeted.vectors(); VB = battery.vectors()
    VB = [t for t in VB if t[0] not in ('JUMPI', 'KECCAK', 'MCOPY', 'CDLOAD', 'SIGNEXT_CHAIN')]
    res = {'elf': 'build/ops.elf', 'targetedVectors': len(VT), 'batteryArithVectors': len(VB), 'runs': []}
    modes = [[]] + [[f] for f in fl]
    for m in modes:
        t0 = time.time()
        if m:  # planted faults: a sample is enough to show the check can fail
            r1 = run(VT[::20], m, procs); r2 = run(VB[::20], m, procs)
        else:
            r1 = run(VT, m, procs); r2 = run(VB, m, procs)
        res['runs'].append({'targeted': r1, 'battery': r2, 'seconds': round(time.time() - t0)})
        print(m, 'targeted', r1['ran'], r1['mismatch'], 'battery', r2['ran'], r2['mismatch'], round(time.time() - t0), flush=True)
        json.dump(res, open(out, 'w'), indent=1)
