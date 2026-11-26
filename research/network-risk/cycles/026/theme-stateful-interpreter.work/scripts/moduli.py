"""Profile of the MULMOD moduli the PoolManager frames execute in each sequence (reference interpreter, trace on), and
what two planted memo faults would do to them: a memo keyed on limb 3 only, and one keyed on limb 0 only, each with
the bor rule that only moduli with limb 3 nonzero use the memo (core/vm/mulmod_memo.go:55-64 at v2.12.0-beta).
Usage: python3 -I moduli.py <out.json> <pm hex> [names...]"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seqlib as S
import pyevm as P
M = (1 << 256) - 1
L = lambda v, i: (v >> (64 * i)) & ((1 << 64) - 1)

def main():
    out = sys.argv[1]; pm = int(sys.argv[2], 16); names = sys.argv[3:] or ['a64', 'a512', 'b']
    salt = json.load(open(os.path.join(S.WORK, 'build', 'salt.json')))['salt']
    seqs = S.sequences(salt); res = {}
    for n in names:
        wd = P.World(S.codes(pm)); wd.trace = []; wd.trace_stack = 3
        ok, _ = wd.call(S.EOA, S.D, 0, S.enc_run(seqs[n]), False, 0)
        mm = [t[3] for t in wd.trace if t[2] == 0x09]
        ops = [(x[2], x[1], x[0]) for x in mm]   # (a, b, m)
        full = [m for _, _, m in ops if L(m, 3)]
        prev = None; sw = top = bot = 0
        for m in full:
            if prev is not None and m != prev:
                sw += 1
                if L(m, 3) == L(prev, 3): top += 1
                if L(m, 0) == L(prev, 0): bot += 1
            prev = m
        faults = {}
        for name, kf in (('limb3', lambda m: L(m, 3)), ('limb0', lambda m: L(m, 0))):
            memo = None; wrong = 0
            for a, b, m in ops:
                if not L(m, 3):
                    continue
                if memo is None or kf(memo) != kf(m):
                    memo = m
                # a stale reciprocal of memo used for m gives Barrett reduction with the wrong modulus estimate; count
                # cases where the stale modulus differs, which is when a wrong word can appear
                if memo != m:
                    wrong += 1
            faults[name] = wrong
        res[n] = {'ok': ok, 'mulmod': len(ops), 'fullWidth': len(full), 'distinctFullWidth': len(set(full)),
                  'notZeroModulus': sum(1 for m in full if m == M), 'switches': sw, 'switchesSameLimb3': top,
                  'switchesSameLimb0': bot, 'plantedFaultExposures': faults}
        print(n, res[n], flush=True)
    json.dump(res, open(out, 'w'), indent=1)

if __name__ == '__main__':
    main()
