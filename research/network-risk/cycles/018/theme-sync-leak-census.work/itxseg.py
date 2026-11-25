"""Samples Blockscout's v2 internal transaction list of the MegaETH PoolManager (every frame to or from it, zero-value
and failed ones included) in segments: segment s starts at the end of block starts[s] and pages backwards until it
reaches starts[s-1] or has read <pages> pages. Read only. Usage: python3 -I itxseg.py <outdir> <pages> <threads> <b0> <b1> ..."""
import json, sys, os, time, urllib.request, urllib.parse, concurrent.futures as cf
PM = '0xacb7e78fa05d562e0a5d3089ec896d57d057d38e'
O, PAGES, TH = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); starts = sorted(int(x) for x in sys.argv[4:])
base = f'https://megaeth.blockscout.com/api/v2/addresses/{PM}/internal-transactions'
PAIRS = json.loads(os.environ['PAIRS']) if os.environ.get('PAIRS') else None  # optional [[top, floor], ...]
if PAIRS: starts = [p[0] for p in PAIRS]
def seg(s):
    top = starts[s]; floor = starts[s - 1] if s else 0
    if PAIRS: top, floor = PAIRS[s]
    nxt = {'index': 99999, 'block_number': top, 'transaction_index': 99999, 'include_zero_value': 'true'}
    rows = []; low = top; pages = 0; complete = False; msg = None
    while pages < PAGES:
        url = base + '?' + urllib.parse.urlencode(nxt)
        for k in range(8):
            try:
                d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={'user-agent': 'review-client'}), timeout=90)); break
            except Exception as e:
                msg = str(e)[:100]; time.sleep(2 + 3 * k)
        else: break
        pages += 1
        for x in d['items']:
            if x['block_number'] <= floor: complete = True; break
            rows.append({'b': x['block_number'], 'tx': x['transaction_hash'], 'ty': x.get('type'), 'v': x.get('value'), 'ok': x.get('success'),
                         'from': ((x.get('from') or {}).get('hash') or '').lower(), 'to': ((x.get('to') or {}).get('hash') or '').lower(), 'err': x.get('error')})
            low = x['block_number']
        if complete: break
        nxt = d.get('next_page_params')
        if not nxt: complete = True; break
        nxt = {k: (str(v).lower() if isinstance(v, bool) else v) for k, v in nxt.items()}
    with open(os.path.join(O, f'itxseg-{top}%s.jsonl' % ('-p2' if PAIRS else '')), 'w') as f:
        for r in rows: f.write(json.dumps(r) + '\n')
    return {'top': top, 'floor': floor, 'lowestReached': low, 'pages': pages, 'items': len(rows), 'reachedFloor': complete, 'lastError': msg}
with cf.ThreadPoolExecutor(TH) as ex: res = list(ex.map(seg, range(len(starts))))
json.dump({'started': starts, 'pagesPerSegment': PAGES, 'segments': res}, open(os.path.join(O, 'itxseg-summary%s.json' % ('-pass2' if PAIRS else '')), 'w'), indent=1)
print(json.dumps(res))
