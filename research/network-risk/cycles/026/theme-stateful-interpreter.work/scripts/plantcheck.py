"""Harness check: run sequences in a reference interpreter with a planted per-frame SLOAD cache that nested frames
and reverts do not invalidate (the stale-entry shape of erigon's frameSlots, F-147), and count the words that differ
from the unplanted reference. Usage: python3 -I plantcheck.py <out.json> [names...]"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seqlib as S
import pyevm_plant as P
PM = 0x000000000004444c5dc75cB358380D2e3dE08A90
names = sys.argv[2:] or ['c', 'c2', 'b']
salt = json.load(open(os.path.join(S.WORK, 'build', 'salt.json')))['salt']
seqs = S.sequences(salt); ref = json.load(open(os.path.join(S.WORK, 'out', 'ref-eth.json')))['results']; out = {}
for n in names:
    wd = P.World(S.codes(PM)); ok, ret = wd.call(S.EOA, S.D, 0, S.enc_run(seqs[n]), False, 0)
    got = S.dec_run(ret) if ok else None
    diff = 0
    if got:
        for a, b in zip(got, ref[n]['steps']):
            if a != b:
                diff += max(len(a.get('w', [])), len(b.get('w', []))) if a.get('ok') != b.get('ok') else sum(x != y for x, y in zip(a.get('w', []), b.get('w', [])))
    out[n] = {'ok': ok, 'wordsDiffering': diff, 'stepsDiffering': sum(a != b for a, b in zip(got or [], ref[n]['steps']))}
    print(n, out[n])
json.dump(out, open(sys.argv[1], 'w'), indent=1)
