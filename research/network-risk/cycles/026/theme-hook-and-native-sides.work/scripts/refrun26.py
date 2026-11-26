"""Run cases through the reference EVM (pyevm26.py). Usage: python3 refrun26.py <cases.json> <out.json> <pm hex> [prague 1|0]
Each case runs alone from a fresh world (driver run(bytes[]) with one case), like one eth_call per case. Records results and
per-side JUMPI counts in the PoolManager code."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common26 import enc_run, dec_run, codes_for, balances_for, D, EOA
import pyevm26 as P

def run_one(pm, c):
    w = P.World(codes_for(pm, [c]), balances_for(pm))
    try:
        ok, ret = w.call(EOA, D, 0, enc_run([c], pm), False, 0)
    except NotImplementedError as e:
        return {'notImplemented': str(e)}, {}
    if not ok: return {'topFail': ret.hex()}, {}
    (uok, words, rv), = dec_run(ret)
    bc = {}
    for (addr, pc, side), n in w.bcount.items():
        if addr == pm: bc['%d:%d' % (pc, int(side))] = bc.get('%d:%d' % (pc, int(side)), 0) + n
    return {'ok': uok, 'w': [hex(x) for x in words] if words else None, 'revert': rv.hex()}, bc

if __name__ == '__main__':
    cases = json.load(open(sys.argv[1]))['cases']
    pm = int(sys.argv[3], 16)
    out = {'pm': hex(pm), 'results': {}, 'sides': {}, 'perCaseSides': {}}
    t = time.time()
    for k, c in enumerate(cases):
        r, bc = run_one(pm, c)
        out['results'][str(c['id'])] = r
        for s, n in bc.items(): out['sides'][s] = out['sides'].get(s, 0) + n
        out['perCaseSides'][str(c['id'])] = sorted(bc)
        if k % 100 == 0: print(k, len(cases), round(time.time() - t), flush=True)
    json.dump(out, open(sys.argv[2], 'w'))
