"""Classify the cases that differed in the batched runs, rerun one case per eth_call (out/single), against the unbatched
reference (ref-<chainId>.json). Usage: python3 single26.py <outdir> <out.json>"""
import sys, os, json, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'compare26.py')).read().split("eth = json.load")[0].replace("od = sys.argv[1]", "od = sys.argv[1]"))
from common26 import decode_words
out = {}
for p in sorted(glob.glob(os.path.join(od, 'single', 'chain-*.json'))):
    c = json.load(open(p)); cid = c['chainId']; ref = json.load(open(os.path.join(od, f'ref-{cid}.json')))
    rows = []
    for k, v in c['results'].items():
        cc = cases[k]; r = ref['results'][k]
        same = masked(v, cc) == masked(r, cc)
        row = {'case': int(k), 'tag': cc['tag'], 'sameAsReferenceAlone': same, 'chainUnlockOk': v.get('ok'), 'refUnlockOk': r.get('ok'),
               'chainRevert': v.get('revert', '')[:200], 'clients': sorted({b.get('clientBefore') for b in c['batches']})}
        if not same and v.get('w') and r.get('w'):
            dv = decode_words([int(x, 16) for x in v['w']], cc['nact']); dr = decode_words([int(x, 16) for x in r['w']], cc['nact'])
            row['actsChain'] = [(a['ok'], hex(a['w0'] >> 224) if a['w0'] >> 224 else hex(a['w0'])) for a in dv['acts']]
            row['actsRef'] = [(a['ok'], hex(a['w0'] >> 224) if a['w0'] >> 224 else hex(a['w0'])) for a in dr['acts']]
            row['balChain'] = [hex(x) for x in dv['bal1']]; row['balRef'] = [hex(x) for x in dr['bal1']]
        rows.append(row)
    out[cid] = rows
    print(cid, c['name'], len(rows), 'still differ alone:', sum(1 for x in rows if not x['sameAsReferenceAlone']))
json.dump(out, open(sys.argv[2], 'w'), indent=1)
