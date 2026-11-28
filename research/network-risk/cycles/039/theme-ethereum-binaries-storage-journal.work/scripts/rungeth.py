"""usage: python3 -I rungeth.py <nseq> <out.json> [fault] [shard nshard]
Runs seqs.py sequences on the geth v1.17.10 amd64 binary model (gethj.py)."""
import json, sys, time, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gethj as G, seqs as S
from x86emu import Stop
N, OUT = int(sys.argv[1]), sys.argv[2]
FAULT = sys.argv[3] if len(sys.argv) > 3 else 'none'
SH, NSH = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (0, 1)
import faults_geth as F
patch = F.FAULTS[FAULT] if FAULT != 'none' else None
g = G.Geth(text_patch=patch)

def mk(db):
    g.new(); g.db.update(db); return g

res = {'binary': G.BIN, 'fault': FAULT, 'seed': S.SEED, 'shard': [SH, NSH], 'sequences': 0, 'steps': 0, 'reads': 0, 'writes': 0,
       'origChecks': 0, 'reverts': 0, 'commits': 0, 'mismatches': [], 'errors': [], 'started': time.time()}
for qi, (seq, db) in enumerate(S.sequences(N)):
    if qi % NSH != SH: continue
    res['sequences'] += 1
    try:
        r = S.run_seq(mk, seq, db, res, qi)
        if r:
            res['mismatches'].append(r)
            if FAULT != 'none' and len(res['mismatches']) >= 3: break
    except Stop as e:
        res['errors'].append({'seq': qi, 'error': str(e)})
        if len(res['errors']) > 20: break
res['functionsRun'] = sorted({g.prog.names[lo] for lo in g.prog.names if any(lo <= pc < lo + 0x10000 for pc in [])} | set(g.prog.names.values()))
res['instructionsVisited'] = len(g.visited)
res['stubbed'] = sorted(g.stubbed)
res['faultHits'] = g.fault_hits
res['elapsed'] = time.time() - res['started']
json.dump(res, open(OUT, 'w'), indent=1)
print(FAULT, 'seqs', res['sequences'], 'reads', res['reads'], 'orig', res['origChecks'], 'reverts', res['reverts'],
      'faultHits', g.fault_hits, 'mismatches', len(res['mismatches']), 'errors', len(res['errors']), '%.0fs' % res['elapsed'])
