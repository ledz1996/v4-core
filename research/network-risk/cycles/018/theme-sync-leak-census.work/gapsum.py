"""Summarise raw/gap/<chain>.json: per endpoint, window getLogs totals, sampled-block agreement with receipts."""
import json, sys, glob
out = {}
for fn in sorted(glob.glob('raw/gap/*.json')):
    R = json.load(open(fn)); cid = R['chainId']; E = {}
    for W in R['windows']:
        for u, c in W['getLogs'].items():
            e = E.setdefault(u, {'windowsAnswered': 0, 'windowsError': 0, 'logs': 0, 'sampledBlocks': 0, 'sampledReceiptLogs': 0, 'sampledGetLogs': 0, 'short': [], 'errors': set()})
            if isinstance(c, int): e['windowsAnswered'] += 1; e['logs'] += c
            else: e['windowsError'] += 1; e['errors'].add(c[:90])
        for s in W['samples']:
            if not isinstance(s.get('receipts'), int): continue
            for u, c in s['getLogs'].items():
                e = E[u]; e['sampledBlocks'] += 1; e['sampledReceiptLogs'] += s['receipts']; e['sampledGetLogs'] += c
                if c != s['receipts']: e['short'].append({'block': s['block'], 'getLogs': c, 'receipts': s['receipts'], 'ownReceipts': s.get('ownReceipts', {}).get(u)})
    for e in E.values(): e['errors'] = sorted(e['errors'])
    out[cid] = {'deployBlock': R.get('deployBlock'), 'head': R.get('head'), 'windows': [[W['from'], W['to']] for W in R['windows']], 'done': 'finished' in R, 'clientVersion': R['clientVersion'], 'endpoints': E}
    print(cid, R.get('deployBlock'), len(R['windows']), 'finished' in R)
    for u, e in E.items(): print('  ', u, {k: (v if k != 'short' else len(v)) for k, v in e.items()})
json.dump(out, open('raw/gap-summary.json', 'w'), indent=1)
