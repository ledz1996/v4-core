"""Unmodified copy of cycles/019/theme-census-endpoints.work/gapsum2.py.
Summarise raw/gap/<chain>.json of gapcheck2.py: per endpoint, window getLogs totals and errors, and every sampled
block where the endpoint's getLogs count differs from the receipts of any endpoint, or where receipts do not cover
every transaction of the block. Usage: gapsum2.py <out.json> <in.json>..."""
import json, sys
out = {}
for fn in sys.argv[2:]:
    R = json.load(open(fn)); cid = R['chainId']; E = {}
    for W in R['windows']:
        for u, c in W['getLogs'].items():
            e = E.setdefault(u, {'windowsAnswered': 0, 'windowsError': 0, 'windowLogs': 0, 'sampledBlocks': 0, 'sampledBlocksWithLogs': 0, 'sampledReceiptLogs': 0, 'sampledGetLogs': 0,
                                 'receiptMethods': set(), 'short': [], 'receiptGaps': [], 'errors': set()})
            if isinstance(c, int): e['windowsAnswered'] += 1; e['windowLogs'] += c
            else: e['windowsError'] += 1; e['errors'].add(c[:120])
        for s in W['samples']:
            rec = {u: v for u, v in s['receipts'].items() if isinstance(v, int)}
            for u, (n, ntx) in s['txCount'].items():
                E.setdefault(u, {'receiptGaps': [], 'receiptMethods': set()})
                if n != ntx: E[u]['receiptGaps'].append({'block': s['block'], 'receipts': n, 'txs': ntx})
            for u, m in s['method'].items(): E[u]['receiptMethods'].add(m)
            if not rec: continue
            ref = max(rec.values())
            for u, c in s['getLogs'].items():
                e = E[u]; e['sampledBlocks'] += 1; e['sampledReceiptLogs'] += ref; e['sampledGetLogs'] += c
                if ref: e['sampledBlocksWithLogs'] += 1
                if any(c != v for v in rec.values()): e['short'].append({'block': s['block'], 'getLogs': c, 'receipts': rec})
    for e in E.values():
        e['errors'] = sorted(e.get('errors', [])); e['receiptMethods'] = sorted(e['receiptMethods'])
    out[fn.split('/')[-1]] = {'chainId': cid, 'deployBlock': R.get('deployBlock'), 'deploySource': R.get('deploySource'), 'head': R.get('head'), 'windows': [[W['from'], W['to'], W['extra']] for W in R['windows']],
                'done': 'finished' in R, 'clientVersion': R['clientVersion'], 'endpoints': E}
    print(cid, R.get('deployBlock'), len(R['windows']), 'finished' in R)
    for u, e in E.items(): print('  ', u, {k: (v if k not in ('short', 'receiptGaps') else len(v)) for k, v in e.items()})
json.dump(out, open(sys.argv[1], 'w'), indent=1)
