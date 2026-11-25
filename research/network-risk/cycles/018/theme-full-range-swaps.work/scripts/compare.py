"""Word-for-word comparison of every full-range run with the full Ethereum answer (reth v2.10.0, 500M gas), and of
the full answer with the stored 25M Ethereum answer of cycle 17 (s1-real-1 / s2-real-1, real address, equal to the
fresh-address hashes there), record by record. Writes compare.json with every mismatching record in full."""
import os, sys, json, gzip, glob, hashlib
HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(HERE, '..', 'raw')
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', '..', 'tools', 'opdiff'))
import pmdiff as P  # noqa
ref = {s: {k: bytes.fromhex(v['plain'][2:]) for k, v in json.load(open(f'{RAW}/eth-blast-s{s}.json'))['scripts'].items()} for s in '12'}
C17 = os.path.join(HERE, '..', '..', '..', '017', 'theme-real-address-runs.work', 'raw', 'runs')
st25 = {s: json.load(gzip.open(f'{C17}/s{s}-real-1.json.gz', 'rt'))['results'] for s in '12'}
out = {'runs': [], 'vsStored25M': {}}
def words(b): return [b[i:i + 32] for i in range(0, len(b), 32)]
def cmp(a, b):
    wa, wb = words(a), words(b)
    bad = [i for i in range(max(len(wa), len(wb))) if (wa[i] if i < len(wa) else None) != (wb[i] if i < len(wb) else None)]
    return len(wa), bad
for s in '12':
    for k, full in ref[s].items():
        r25 = bytes.fromhex(st25[s][int(k)][2:]); A = P.parse(full); B = P.parse(r25)
        first = next((j for j in range(min(len(A), len(B))) if A[j] != B[j]), None)
        rec = {'recordsFull': len(A), 'records25M': len(B), 'firstDifferentRecord': first}
        if first is not None:
            rec['full'] = [A[first][0], A[first][1].hex()[:200], len(A[first][1])]; rec['stored25M'] = [B[first][0], B[first][1].hex(), len(B[first][1])]
        out['vsStored25M'][f'{s}-{k}'] = rec
files = sorted(glob.glob(f'{RAW}/*.json'))
for f in files:
    d = json.load(open(f)); name = os.path.basename(f)
    if name.startswith(('eth-blast', 'caps', 'pyref', 'tempo-drpc-percall', 'split-eth-validate', 'split-eth-heavy-auto')): continue
    if 'scripts' not in d: continue
    s = d.get('set') or '1'
    for k, v in d['scripts'].items():
        hx = v.get('plain') or v.get('output')
        if not hx: continue
        b = bytes.fromhex(hx[2:]); n, bad = cmp(b, ref[s][k])
        out['runs'].append({'file': name, 'set': s, 'script': int(k), 'words': n, 'refWords': len(ref[s][k]) // 32, 'differentWords': len(bad), 'equal': not bad,
                            'client': (d.get('batches') or [{}])[-1].get('clientVersionBefore', d.get('url')),
                            'mismatch': None if not bad else {'firstWord': bad[0], 'got': hx[2 + 64 * bad[0]:2 + 64 * bad[0] + 64], 'ref': ref[s][k][32 * bad[0]:32 * bad[0] + 32].hex()}})
json.dump(out, open(f'{RAW}/compare.json', 'w'), indent=1)
by = {}
for r in out['runs']: by.setdefault(r['file'], [0, 0, []]); by[r['file']][0 if r['equal'] else 1] += 1; (by[r['file']][2].append(r['script']) if not r['equal'] else None)
for f, (e, n, l) in by.items(): print(f'{f:32} equal {e} different {n} {l}')
for k, v in out['vsStored25M'].items(): print('stored25M', k, v['recordsFull'], v['records25M'], 'first diff record', v['firstDifferentRecord'], v.get('stored25M', [None])[0:1], 'len', v.get('stored25M', [0, 0, 0])[2])
