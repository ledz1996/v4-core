"""Copy of cycle 25 compare.py with the networks.json path made absolute. Task 2 comparison: each network's eth_call words against the Ethereum endpoint's words and against the reference
EVM run at the same PoolManager address (ref-<chainId>.json, or ref-eth.json while that is missing).
Usage: python3 compare.py <outdir> <out.json>"""
import sys, os, json
od = sys.argv[1]
nets = json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))['networks']
eth = json.load(open(os.path.join(od, 'chain-1.json')))
summary = []; mism = []
for n in nets:
    p = os.path.join(od, f'chain-{n["chainId"]}.json')
    if not os.path.exists(p): summary.append({'chainId': n['chainId'], 'name': n['name'], 'missing': True}); continue
    c = json.load(open(p))
    rp = os.path.join(od, f'ref-{n["chainId"]}.json')
    ref = json.load(open(rp if os.path.exists(rp) else os.path.join(od, 'ref-eth.json')))
    vs_ref = vs_eth = err = 0
    for k, v in c['results'].items():
        if 'error' in v: err += 1; mism.append({'chainId': n['chainId'], 'case': k, 'kind': 'error', 'chain': v}); continue
        r = ref['results'][k]
        if v != r: vs_ref += 1; mism.append({'chainId': n['chainId'], 'case': k, 'kind': 'vs reference', 'chain': v, 'ref': r})
        e = eth['results'].get(k)
        if e is not None and v != e: vs_eth += 1
    outside_same = c.get('outside', {}).get('res') == [list(x) for x in ref['outside']['res']] if 'outside' in ref else None
    clients = sorted({b.get('clientBefore', '') for b in c['batches']} | {b.get('clientAfter', '') for b in c['batches']})
    blocks = [b['block'] for b in c['batches'] if 'block' in b]
    summary.append({'chainId': n['chainId'], 'name': n['name'], 'rpc': c['rpc'], 'cases': len(c['results']), 'errors': err,
                    'diffVsReference': vs_ref, 'diffVsEthereum': vs_eth, 'outsideSame': outside_same,
                    'refFile': os.path.basename(rp if os.path.exists(rp) else 'ref-eth.json'),
                    'clients': clients, 'blocks': [min(blocks), max(blocks)] if blocks else None, 'batches': len(c['batches']),
                    'splitBatches': sum(1 for b in c['batches'] if b.get('split'))})
for s in summary: print(s)
json.dump({'summary': summary, 'mismatches': mism}, open(sys.argv[2], 'w'), indent=1)
