"""Fetch eth_getTransactionReceipt for collected transactions whose call trace was pruned before nested logs were kept
(files older than raw/prune_fix_time.txt). Used only for the ERC-20 Transfer flow check of Task 3. Read-only."""
import json, os, sys, gzip, glob, time
from rpcu import call
from collect_eps import LOGS
cid = int(sys.argv[1]); D = '../raw/%d' % cid; os.makedirs(D + '/rcpt', exist_ok=True)
fix = int(open('../raw/prune_fix_time.txt').read())
todo = [os.path.basename(f)[:-8] for f in glob.glob(D + '/tx/*.json.gz') if os.path.getmtime(f) < fix]
todo = [h for h in todo if not os.path.exists('%s/rcpt/%s.json.gz' % (D, h))]
urls = LOGS[cid]; k = 0
v = [call(u, 'web3_clientVersion', [], 20) for u in urls]
open(D + '/brackets.jsonl', 'a').write(json.dumps({'tag': 'receipts-start', 'urls': urls, 'client': v, 't': time.time()}) + '\n')
for h in todo:
    for t in range(6):
        u = urls[(k + t) % len(urls)]
        r, e = call(u, 'eth_getTransactionReceipt', [h], 60)
        if r: break
        open(D + '/errors.jsonl', 'a').write(json.dumps({'stage': 'receipt', 'url': u, 'tx': h, 'err': (e or 'null')[:200]}) + '\n'); time.sleep(1 + t)
    k += 1
    if not r: continue
    gzip.open('%s/rcpt/%s.json.gz' % (D, h), 'wt').write(json.dumps({'status': r.get('status'), 'logs': [{'address': l['address'], 'topics': l['topics'], 'data': l['data']} for l in r['logs']]}))
v = [call(u, 'web3_clientVersion', [], 20) for u in urls]
open(D + '/brackets.jsonl', 'a').write(json.dumps({'tag': 'receipts-end', 'urls': urls, 'client': v, 't': time.time()}) + '\n')
print(cid, 'receipts', len(todo))
