import json, glob
S = {}
for fn in sorted(glob.glob('raw/gap/*.json')):
    d = json.load(open(fn))
    for u in d['urls']:
        w_ok = w_err = logs = sb = sbl = gaps = short = 0; errs = set(); ranges = []
        for W in d.get('windows', []):
            g = W['getLogs'].get(u)
            if isinstance(g, int): w_ok += 1; logs += g; ranges.append([W['from'], W['to']])
            else: w_err += 1; errs.add(str(g)[:90])
            for s in W['samples']:
                rc = s['receipts'].get(u); gl = s['getLogs'].get(u)
                if isinstance(rc, int):
                    sb += 1; sbl += rc > 0
                    if isinstance(gl, int) and gl != rc: gaps += 1
                    tc = s['txCount'].get(u)
                    if tc and tc[0] != tc[1]: short += 1
        S[fn.split('/')[-1] + ' ' + u] = {'chainId': d['chainId'], 'deploy': d.get('deployBlock'), 'windowsAnswered': w_ok, 'windowsError': w_err, 'answeredRanges': ranges, 'windowLogs': logs,
             'sampledBlocks': sb, 'sampledBlocksWithLogs': sbl, 'logsVsReceiptsMismatch': gaps, 'receiptCountShort': short, 'errors': sorted(errs), 'clientVersion': d['clientVersion'], 'finished': 'finished' in d}
json.dump(S, open('raw/gap-summary.json', 'w'), indent=1)
for k, v in S.items(): print(k, {x: v[x] for x in ('windowsAnswered', 'windowsError', 'windowLogs', 'sampledBlocks', 'logsVsReceiptsMismatch', 'receiptCountShort', 'finished')}, v['errors'][:1])
