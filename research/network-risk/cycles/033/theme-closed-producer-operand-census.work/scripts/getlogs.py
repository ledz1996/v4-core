"""Collect every PoolManager log in [from, to] in chunks; record the client version before and after. Read-only.
Usage: python3 -I getlogs.py <out.json> <url> <pm> <from> <to> [step]"""
import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rpc30 import R
out, url, pm, a, b = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
step = int(sys.argv[6]) if len(sys.argv) > 6 else 1000
cv0 = R(url, 'web3_clientVersion', [])[0]
logs = []; frm = a; reached = a - 1; errs = []
while frm <= b:
    to = min(frm + step - 1, b)
    try:
        r, _ = R(url, 'eth_getLogs', [{'address': pm, 'fromBlock': hex(frm), 'toBlock': hex(to)}])
    except Exception as e:
        errs.append([frm, to, str(e)[:200]]); step = max(step // 2, 50)
        if len(errs) > 200: break
        continue
    logs += [{'b': int(l['blockNumber'], 16), 'tx': l['transactionHash'], 'i': int(l['logIndex'], 16), 'topics': l['topics'], 'data': l['data']} for l in r]
    reached = to; frm = to + 1
    if len(logs) and (to - a) // step % 50 == 0: print(to, len(logs), flush=True)
json.dump({'url': url, 'pm': pm, 'from': a, 'to': b, 'reached': reached, 'clientBefore': cv0, 'clientAfter': R(url, 'web3_clientVersion', [])[0],
           'errors': errs, 'logs': logs}, open(out, 'w'))
print('done', reached, len(logs))
