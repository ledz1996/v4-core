"""Run cases through the reference EVM (pyevm_cov, a copy of cycle 24's counting copy of tools/opdiff/pyevm.py).

Usage: python3 refrun.py <cases.json> <out.json> [pm address hex] [batch]
Each batch of cases is one driver run(bytes[]) call from a fresh, empty world (the same thing one eth_call does with
fresh token addresses), so results do not depend on batch size. Records results, steps and per-side JUMPI counts in
the PoolManager code.
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import enc_run, dec_run, codes_for, D, EOA, enc_bytes_array, SEL_OUTSIDE, dec_outside
import pyevm_cov as P

def run_batch(pm, cases):
    w = P.World(codes_for(pm, cases))
    for c in cases:
        for k, v in c.get('storage', {}).items(): w.storage[(pm, int(k, 16))] = int(v, 16)
    ok, ret = w.call(EOA, D, 0, enc_run(cases), False, 0)
    res = dec_run(ret) if ok else None
    bc = {}
    for (addr, pc, side), n in w.bcount.items():
        if addr == pm: bc['%d:%d' % (pc, int(side))] = bc.get('%d:%d' % (pc, int(side)), 0) + n
    return ok, ret, res, bc, w.steps

if __name__ == '__main__':
    cases = json.load(open(sys.argv[1]))['cases']
    pm = int(sys.argv[3], 16) if len(sys.argv) > 3 else 0x000000000004444c5dc75cB358380D2e3dE08A90
    bs = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    out = {'pm': hex(pm), 'results': {}, 'sides': {}, 'perCaseSides': {}}
    t = time.time()
    for i in range(0, len(cases), bs):
        chunk = cases[i:i + bs]
        ok, ret, res, bc, steps = run_batch(pm, chunk)
        if not ok:
            for c in chunk: out['results'][c['id']] = {'topFail': ret.hex()}
            continue
        for c, (uok, words, rv) in zip(chunk, res):
            out['results'][c['id']] = {'ok': uok, 'w': [hex(x) for x in words] if words else None, 'revert': rv.hex()}
        for k, n in bc.items(): out['sides'][k] = out['sides'].get(k, 0) + n
        if bs == 1: out['perCaseSides'][chunk[0]['id']] = sorted(bc)
        if (i // bs) % 50 == 0: print(i, len(cases), round(time.time() - t), steps, flush=True)
    od = json.load(open(sys.argv[1])).get('outside')
    if od:
        w = P.World(codes_for(pm, []))
        ok, ret = w.call(EOA, D, 0, enc_bytes_array(SEL_OUTSIDE, [bytes.fromhex(x['data']) for x in od]), False, 0)
        out['outside'] = {'ok': ok, 'res': dec_outside(ret) if ok else ret.hex()}
        for (addr, pc, side), n in w.bcount.items():
            if addr == pm: out['sides']['%d:%d' % (pc, int(side))] = out['sides'].get('%d:%d' % (pc, int(side)), 0) + n
        out['perCaseSides']['outside'] = sorted('%d:%d' % (pc, int(sd)) for (a, pc, sd) in w.bcount if a == pm)
    json.dump(out, open(sys.argv[2], 'w'))
