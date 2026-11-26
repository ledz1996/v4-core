"""Run the cycle 23 to 25 vectors through the x86 model of the package's uint256 runtime routines.

usage: python3 -I runvec.py <disasm dir> <out.json> [limit]
The disassembly files are objdump text of the package routines (data only).
"""
import sys, os, json, random, glob, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = '/home/user/v4-core/research/network-risk'
sys.path.insert(1, ROOT + '/tools/opdiff')
sys.path.insert(2, ROOT + '/cycles/025/stablecoin-l1.work')
import x86emu
from x86emu import CPU, Prog, Stop

M = 2 ** 256 - 1
SIGN = 1 << 255

def s(x): return x - (1 << 256) if x >> 255 else x
def u(x): return x & M
def r_sdiv(a, b):
    if b == 0: return 0
    sa, sb = s(a), s(b)
    q = abs(sa) // abs(sb)
    return u(-q if (sa < 0) != (sb < 0) else q)
def r_smod(a, b):
    if b == 0: return 0
    sa, sb = s(a), s(b)
    r = abs(sa) % abs(sb)
    return u(-r if sa < 0 else r)
REF = {
    'DIV': lambda a, b, c: a // b if b else 0,
    'MOD': lambda a, b, c: a % b if b else 0,
    'SDIV': lambda a, b, c: r_sdiv(a, b),
    'SMOD': lambda a, b, c: r_smod(a, b),
    'ADDMOD': lambda a, b, c: (a + b) % c if c else 0,
    'MULMOD': lambda a, b, c: (a * b) % c if c else 0,
    'EXP': lambda a, b, c: pow(a, b, 1 << 256),
    'MUL': lambda a, b, c: (a * b) & M,
    'MUL192': lambda a, b, c: ((a % (1 << 192)) * (b % (1 << 192))) % (1 << 192),
}

def load(d):
    text = ''.join(open(f).read() + '\n' for f in sorted(glob.glob(d + '/*.s')))
    p = Prog(text)
    sym = {}
    for name, addr in p.labels.items():
        sym[name] = addr
    return p, sym

def find(sym, frag):
    c = [a for n, a in sym.items() if frag in n]
    assert len(c) == 1, (frag, c)
    return c[0]

class Runner:
    def __init__(self, d):
        self.p, self.sym = load(d)
        ent = {
            'DIV': '7runtime4udiv', 'MOD': '7runtime4umod', 'SDIV': '7runtime4sdiv', 'SMOD': '7runtime4smod',
            'ADDMOD': '7runtime6addmod', 'MULMOD': '7runtime6mulmod', 'EXP': '7runtime3exp', 'MUL': 'monad_vm_runtime_mul',
        }
        self.ent = {k: find(self.sym, v) if k != 'MUL' else self.sym['monad_vm_runtime_mul'] for k, v in ent.items()}
        self.hits = {}
        self.track = set()

    def run(self, op, a, b, c):
        def boom(name):
            def f(cpu): raise Stop('called ' + name)
            return f
        ext = {}
        for n, addr in []:
            pass
        cpu = CPU(self.p, externs=ext)
        R, A, B, N, CTX = 0x100000, 0x100100, 0x100200, 0x100300, 0x100400
        cpu.write(A, 32, a); cpu.write(B, 32, b); cpu.write(N, 32, c)
        cpu.write(R, 32, 0xdeadbeef * (1 + (1 << 200)))
        gas0 = 10 ** 12
        cpu.write(CTX + 0x10, 8, gas0)
        if op in ('ADDMOD', 'MULMOD'):
            cpu.call(self.ent[op], [R, A, B, N])
        elif op == 'EXP':
            cpu.call(self.ent[op], [CTX, R, A, B])
        elif op == 'MUL':
            cpu.call(self.ent[op], [R, A, B])
        elif op == 'MUL192':
            cpu.call(self.sym['monad_vm_runtime_mul_192'], [R, A, B])
            return cpu.read(R, 24), None, cpu
        else:
            cpu.call(self.ent[op], [R, A, B])
        res = cpu.read(R, 32)
        extra = None
        if op == 'EXP':
            used = gas0 - cpu.read(CTX + 0x10, 8)
            extra = used
        for t in self.track:
            pass
        return res, extra, cpu

def gen_all():
    import battery, targeted, maxmod, maxmod2
    sets = {}
    V = [v for v in battery.vectors() if v[0] in REF or v[0] in ('MULDIV512', 'DIVUP')]
    sets['battery'] = V
    sets['targeted'] = [v for v in targeted.vectors() if v[0] in REF or v[0] in ('MULDIV512', 'DIVUP')]
    sets['maxmod'] = [('MULMOD', a, b, n) for (a, b, n) in maxmod.vecs()] + [('ADDMOD', a, b, n) for (a, b, n) in maxmod.vecs.__globals__['vecs']()][:0]
    return sets

def expand(v):
    op, a, b, c = v
    if op == 'MULDIV512':
        return [('MULMOD', a, b, c), ('MULMOD', a, b, M), ('MUL', a, b, 0), ('MUL192', a, b, 0)]
    if op == 'MUL':
        return [v, ('MUL192', a, b, 0)]
    if op == 'DIVUP':
        return [('DIV', a, b, 0), ('MOD', a, b, 0)]
    return [v]

def main():
    d, out = sys.argv[1], sys.argv[2]
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else None
    import battery, targeted, maxmod, maxmod2
    sets = {}
    sets['battery'] = [x for v in battery.vectors() if v[0] in REF or v[0] in ('MULDIV512', 'DIVUP') for x in expand(v)]
    sets['targeted'] = [x for v in targeted.vectors() if v[0] in REF or v[0] in ('MULDIV512', 'DIVUP') for x in expand(v)]
    mm = maxmod.vecs()
    sets['maxmod'] = [(op, a, b, n) for (a, b, n) in mm for op in ('MULMOD', 'ADDMOD')] + [('MULMOD', a, b, M) for (a, b, n) in mm]
    mm2 = maxmod2.vecs()
    sets['maxmod2'] = [(op,) + tuple(t[:3]) for t in mm2 for op in ('MULMOD', 'ADDMOD')]
    extra_path = os.path.join(os.path.dirname(out), 'extra-vectors.json')
    if os.path.exists(extra_path):
        for k, L in json.load(open(extra_path)).items():
            sets[k] = [(op, int(a, 16), int(b, 16), int(c, 16)) for op, a, b, c in L]
    runner = Runner(d)
    res = {'disasm': d, 'sets': {}}
    t0 = time.time()
    allm = []
    blockhits = {}
    for name, V in sets.items():
        if limit: V = V[:limit]
        per = {}
        mism = []
        for v in V:
            op, a, b, c = v
            exp = REF[op](a, b, c)
            try:
                got, extra, cpu = runner.run(op, a, b, c)
                err = None
            except Stop as e:
                got, extra, err = None, None, str(e)
            ok = (got == exp) and err is None
            if op == 'EXP' and ok:
                want_gas = 50 * ((b.bit_length() + 7) // 8)
                if extra != want_gas:
                    ok = False; err = 'gas %d want %d' % (extra, want_gas)
            pe = per.setdefault(op, [0, 0])
            pe[0] += 1
            if not ok:
                pe[1] += 1
                rec = {'set': name, 'op': op, 'a': hex(a), 'b': hex(b), 'c': hex(c), 'want': hex(exp), 'got': None if got is None else hex(got), 'err': err}
                mism.append(rec)
        res['sets'][name] = {'perOp': per, 'n': sum(x[0] for x in per.values()), 'mismatches': mism}
        allm += mism
        print(name, res['sets'][name]['n'], 'mismatch', len(mism), '%.0fs' % (time.time() - t0), flush=True)
    res['total'] = sum(x['n'] for x in res['sets'].values())
    res['totalMismatch'] = len(allm)
    cov = {}
    for name, addr in runner.p.labels.items():
        insns = [a for a in runner.p.order if a >= addr and (a in runner.p.ins)]
        # instructions of this function: up to the next label
        nxt = min([x for x in runner.p.labels.values() if x > addr] or [1 << 62])
        insns = [a for a in insns if a < nxt]
        body = [a for a in insns if not runner.p.ins[a].split()[0] in ('nop', 'cs', 'data16')]
        unv = [a for a in body if a not in x86emu.VISITED]
        cov[name] = {'insns': len(body), 'visited': len(body) - len(unv),
                     'unvisited': ['%x: %s' % (a, runner.p.ins[a]) for a in unv]}
    res['coverage'] = cov
    json.dump(res, open(out, 'w'), indent=1)

if __name__ == '__main__':
    main()
