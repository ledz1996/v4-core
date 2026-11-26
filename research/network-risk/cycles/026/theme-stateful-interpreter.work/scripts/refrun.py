"""Reference run of every sequence in tools/opdiff/pyevm.py (Cancun semantics, no gas), one fresh world per sequence,
exactly as one eth_call starts from the network's state plus overrides. Sequence e needs CREATE2 and SELFDESTRUCT, which
the reference interpreter does not implement, so it has no reference run.
Usage: python3 -I refrun.py <out.json> <pm address hex> [names...]"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seqlib as S
import pyevm as P

def main():
    out = sys.argv[1]; pm = int(sys.argv[2], 16); names = sys.argv[3:] or ['a64', 'b', 'c', 'd300', 'a512']
    salt = json.load(open(os.path.join(S.WORK, 'build', 'salt.json')))['salt']
    seqs = S.sequences(salt)
    res = json.load(open(out)) if os.path.exists(out) else {'pm': hex(pm), 'seed': S.SEED, 'results': {}}
    for n in names:
        t = time.time(); wd = P.World(S.codes(pm))
        ok, ret = wd.call(S.EOA, S.D, 0, S.enc_run(seqs[n]), False, 0)
        res['results'][n] = {'ok': ok, 'steps': S.dec_run(ret) if ok else ret.hex(), 'evmSteps': wd.steps}
        print(n, ok, wd.steps, round(time.time() - t), flush=True)
        json.dump(res, open(out, 'w'))

if __name__ == '__main__':
    main()
