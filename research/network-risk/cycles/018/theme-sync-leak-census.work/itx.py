"""Copy of cycle 17 mega/itx.py, started at block 31,861,608 (its last state). Pages Blockscout's internal transaction list of the MegaETH PoolManager (every call frame to or from it,
failed ones included) into itx.jsonl. Resumable: restarts from the last saved next_page_params.
Usage: python3 -I itx.py <outdir>"""
import json, sys, os, time, urllib.request, urllib.parse
PM = '0xacb7e78fa05d562e0a5d3089ec896d57d057d38e'
O = sys.argv[1]; F = os.path.join(O, 'itx.jsonl'); S = os.path.join(O, 'itx.state')
nxt = json.load(open(S)) if os.path.exists(S) else {}
base = f'https://megaeth.blockscout.com/api/v2/addresses/{PM}/internal-transactions'
n = 0
while True:
    url = base + ('?' + urllib.parse.urlencode({k: (str(v).lower() if isinstance(v, bool) else v) for k, v in nxt.items()}) if nxt else '')
    for k in range(8):
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={'user-agent': 'review-client'}), timeout=60)); break
        except Exception as e:
            time.sleep(2 + 3 * k)
    else:
        print('giving up at', nxt); sys.exit(1)
    with open(F, 'a') as f:
        for x in d['items']:
            f.write(json.dumps({'b': x['block_number'], 'tx': x['transaction_hash'], 'ty': x.get('type'), 'v': x.get('value'), 'ok': x.get('success'),
                                'from': (x.get('from') or {}).get('hash'), 'to': (x.get('to') or {}).get('hash'), 'err': x.get('error')}) + '\n')
    n += len(d['items']); nxt = d.get('next_page_params')
    json.dump(nxt, open(S, 'w'))
    if n % 5000 < 50: print(n, nxt, flush=True)
    if not nxt: print('done', n); break
