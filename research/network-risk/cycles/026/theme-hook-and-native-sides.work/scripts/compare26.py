"""Compare each network's words with the reference EVM at the same PoolManager address (ref-<chainId>.json) and with the
Ethereum endpoint (chain-1.json). Usage: python3 compare26.py <outdir> <out.json>"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common26 import decode_words
od = sys.argv[1]


def masked(v, c):
    """Mask the native balance of address(0) (the 'hook' column of a hookless native case), which is real chain state."""
    if not v.get('w') or c.get('hooks') or c.get('t0') != 0: return v
    w = [int(x, 16) for x in v['w']]
    d = decode_words(w, c['nact'])
    nh = min(len(d['hres']), 24)
    i1 = 8 + 6 * c['nact'] + 6 + 1 + nh + 6 + 2
    w[4] = 0; w[i1 + 4] = 0
    return dict(v, w=[hex(x) for x in w])
nets = json.load(open(os.path.join(od, '..', '..', '..', '..', 'state', 'networks.json')))['networks']
cases = {str(c['id']): c for c in json.load(open(os.path.join(od, 'cases.json')))['cases']}
eth = json.load(open(os.path.join(od, 'chain-1.json')))
summary = []; mism = []
for n in nets:
    cid = n['chainId']; p = os.path.join(od, f'chain-{cid}.json')
    if not os.path.exists(p): summary.append({'chainId': cid, 'name': n['name'], 'missing': True}); continue
    c = json.load(open(p)); rp = os.path.join(od, f'refb-{cid}.json')
    ref = json.load(open(rp))
    vs_ref = vs_eth = err = 0; groups = {}
    for k, v in c['results'].items():
        if 'error' in v:
            err += 1; mism.append({'chainId': cid, 'case': int(k), 'tag': cases[k]['tag'], 'kind': 'error', 'chain': v}); continue
        cc = cases[k]; v = masked(v, cc); r = masked(ref['results'][k], cc)
        e = eth['results'].get(k); e = masked(e, cc) if e else e
        if v != r:
            vs_ref += 1; groups[cases[k]['group']] = groups.get(cases[k]['group'], 0) + 1
            mism.append({'chainId': cid, 'case': int(k), 'tag': cases[k]['tag'], 'kind': 'vs reference', 'chain': v, 'ref': r, 'sameAsEthereum': v == e})
        if e is not None and v != e: vs_eth += 1
    clients = sorted({b.get('clientBefore', '') for b in c['batches']} | {b.get('clientAfter', '') for b in c['batches']})
    blocks = [b['block'] for b in c['batches'] if 'block' in b]
    summary.append({'chainId': cid, 'name': n['name'], 'rpc': c['rpc'], 'cases': len(c['results']), 'errors': err,
                    'diffVsReference': vs_ref, 'diffVsReferenceByGroup': groups, 'diffVsEthereum': vs_eth,
                    'clients': clients, 'blocks': [min(blocks), max(blocks)] if blocks else None, 'batches': len(c['batches']),
                    'splitBatches': sum(1 for b in c['batches'] if b.get('split'))})
for s in summary: print({k: s.get(k) for k in ('chainId', 'name', 'cases', 'errors', 'diffVsReference', 'diffVsReferenceByGroup', 'diffVsEthereum', 'missing')})
json.dump({'summary': summary, 'mismatches': mism}, open(sys.argv[2], 'w'), indent=1)
