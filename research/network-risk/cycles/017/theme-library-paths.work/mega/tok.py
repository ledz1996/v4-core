"""Pages Blockscout's etherscan-style tokentx (ERC-20 transfers to or from) for the MegaETH PoolManager by start block into tok.jsonl.
Usage: SSL_CERT_FILE=... python3 -I itx2.py <outdir>"""
import json, sys, os, time, urllib.request
PM = '0xacb7e78fa05d562e0a5d3089ec896d57d057d38e'
O = sys.argv[1]; F = os.path.join(O, 'tok.jsonl')
start = 0; seen = set(); msgs = set()
while True:
    url = f'https://megaeth.blockscout.com/api?module=account&action=tokentx&address={PM}&startblock={start}&endblock=99999999&page=1&offset=10000&sort=asc'
    for k in range(8):
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={'user-agent': 'review-client'}), timeout=180)); break
        except Exception as e:
            print('retry', e, flush=True); time.sleep(3 + 5 * k)
    else: sys.exit(1)
    msgs.add(d.get('message')); r = d['result'] or []
    new = 0
    with open(F, 'a') as f:
        for x in r:
            key = (x['hash'], x.get('logIndex'), x['blockNumber'], x.get('contractAddress'))
            if key in seen: continue
            seen.add(key); new += 1
            f.write(json.dumps({'b': int(x['blockNumber']), 'tx': x['hash'], 'tok': x.get('contractAddress'), 'v': x.get('value'), 'from': x['from'], 'to': x['to'], 'li': x.get('logIndex')}) + '\n')
    last = int(r[-1]['blockNumber']) if r else start
    print(start, len(r), new, last, d.get('message'), flush=True)
    if len(r) < 10000: break
    start = last  # re-read the last block; duplicates are skipped by key
json.dump(sorted(m for m in msgs if m), open(os.path.join(O, 'tok.msgs.json'), 'w'))
print('done', len(seen))
