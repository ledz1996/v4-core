"""Aggregates the JS-tracer census of HyperEVM transactions (replica re-execution) and checks each transaction's last
SSTORE per slot against the mined state diff saved by cycle 23 (raw/999/tx/<hash>.json.gz, prestateTracer diff mode).
A write that a reverted frame undid shows up as a difference; those are listed in full.
Usage: agg999.py <js dir> <out json>"""
import json, gzip, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from classes import NAMES
js, out = sys.argv[1], sys.argv[2]
RAW = '/home/user/v4-core/research/network-risk/cycles/023/theme-state-replay.work/raw/999/tx'
PM = '0x12d4fd9c5dedd00ab8a0bce2cf0167bbf94b6b1f'
cls = {}; pmk = {}; ntx = 0; wr_eq = wr_ne = wr_unk = 0; tx_ok = 0; tx_bad = []; blocks = set()
def norm(h): return int(h, 16)
for f in sorted(os.listdir(js)):
    if not f.endswith('.json.gz'): continue
    d = json.load(gzip.open(os.path.join(js, f))); tx = d['tx']; r = d['result']
    raw = json.load(gzip.open(os.path.join(RAW, tx + '.json.gz')))
    bn = raw['block']; blocks.add(bn); ntx += 1
    post = raw['diff'].get('post', {}); dpre = raw['diff'].get('pre', {}); pre = raw['pre']
    bad = []
    for k, v in r['w'].items():
        ad, slot = k.split(':'); slot = int(slot, 16); val = int(v, 16)
        ps = {norm(s): norm(x) for s, x in post.get(ad, {}).get('storage', {}).items()}
        pr = {norm(s): norm(x) for s, x in pre.get(ad, {}).get('storage', {}).items()}
        dp = {norm(s) for s in dpre.get(ad, {}).get('storage', {})}
        if slot in ps: exp = ps[slot]
        elif slot in dp: exp = 0  # diff mode lists a slot cleared to zero in pre only
        elif slot in pr: exp = pr[slot]
        else: exp = None
        if exp is None: wr_unk += 1
        elif exp == val: wr_eq += 1
        else: wr_ne += 1; bad.append({'addr': ad, 'slot': hex(slot), 'traceLast': hex(val), 'mined': hex(exp)})
    if bad: tx_bad.append({'tx': tx, 'block': bn, 'diffs': bad})
    else: tx_ok += 1
    for k, v in r['m'].items():
        op, c, ad, pc = k.split(':'); op, c, pc = int(op), int(c), int(pc)
        kk = '%d:%d' % (op, c)
        e = cls.get(kk)
        if e is None: e = cls[kk] = {'occ': 0, 'txs': 0, 'contracts': set(), 'first': bn, 'last': bn, 'example': None}
        e['occ'] += v[0]; e['txs'] += 1; e['contracts'].add(ad); e['first'] = min(e['first'], bn)
        if bn >= e['last'] or e['example'] is None:
            e['last'] = max(e['last'], bn); e['example'] = {'tx': tx, 'block': bn, 'contract': ad, 'pc': pc, 'a': v[1], 'b': v[2], 'c': v[3]}
        if ad == PM:
            k3 = '%d:%d:%d' % (op, c, pc)
            w = pmk.get(k3)
            if w is None: w = pmk[k3] = {'occ': 0, 'txs': 0, 'first': bn, 'last': bn, 'exampleTx': tx}
            w['occ'] += v[0]; w['txs'] += 1; w['first'] = min(w['first'], bn)
            if bn >= w['last']: w['last'] = bn; w['exampleTx'] = tx
for e in cls.values(): e['ncontracts'] = len(e['contracts']); del e['contracts']
res = {'txs': ntx, 'blocks': len(blocks), 'firstBlock': min(blocks), 'lastBlock': max(blocks), 'txsAllWritesMatch': tx_ok,
       'writesEqual': wr_eq, 'writesDiffer': wr_ne, 'writesNoReference': wr_unk, 'txsWithDifferences': tx_bad,
       'classes': {k: dict(v, name=NAMES[tuple(map(int, k.split(':')))]) for k, v in cls.items()}, 'pm': pmk}
json.dump(res, open(out, 'w'), indent=0)
print(ntx, len(blocks), tx_ok, wr_eq, wr_ne, wr_unk, len(tx_bad))
