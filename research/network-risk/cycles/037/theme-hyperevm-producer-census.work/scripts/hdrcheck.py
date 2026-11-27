"""Task 2: compare, for every block a census state file holds, the replica's receiptsRoot, gasUsed and logsBloom digest with the
header the official endpoint serves at that height. Read-only; batches of 25, each batch of 40 requests bracketed with
web3_clientVersion. Usage: hdrcheck.py <out json> <official url> <state json> [<state json> ...]"""
import json, sys, time, hashlib, urllib.request
out, url, files = sys.argv[1], sys.argv[2], sys.argv[3:]
hdr = {}
for f in files:
    hdr.update(json.load(open(f))['hdr'])


def post(body, timeout=120):
    r = urllib.request.urlopen(urllib.request.Request(url, json.dumps(body).encode(), {'content-type': 'application/json', 'user-agent': 'census-readonly'}), timeout=timeout)
    return json.loads(r.read())


def ver():
    try: return post({"jsonrpc": "2.0", "id": 1, "method": "web3_clientVersion", "params": []})['result']
    except Exception as e: return 'exc ' + str(e)[:80]


bns = sorted(int(b) for b in hdr)
import os
if os.environ.get('BLOCKS'):
    keep = {int(l) for l in open(os.environ['BLOCKS']) if l.strip()}
    skip = set()
    if os.environ.get('SKIP'):
        for f in os.environ['SKIP'].split(','): d = json.load(open(f)); skip |= set(d['checked'])
    bns = [b for b in bns if b in keep and b not in skip]
res = {'url': url, 'checked': bns, 'blocks': len(bns), 'equal': 0, 'differ': [], 'unfetched': [], 'brackets': []}
B = int(__import__('os').environ.get('BATCH', '25'))
PACE = float(__import__('os').environ.get('PACE', '1.5'))
for i in range(0, len(bns), B * 40):
    v0 = ver()
    for j in range(i, min(i + B * 40, len(bns)), B):
        grp = bns[j:j + B]
        body = [{"jsonrpc": "2.0", "id": k, "method": "eth_getBlockByNumber", "params": [hex(b), False]} for k, b in enumerate(grp)]
        got = None
        for att in range(5):
            try:
                got = post(body)
                if isinstance(got, list) and all('result' in g for g in got): break
                res.setdefault('refusals', []).append([grp[0], str(got)[:120]]); got = None
            except Exception as e:
                res.setdefault('refusals', []).append([grp[0], str(e)[:120]])
            time.sleep(10 + 20 * att)
        if not isinstance(got, list):
            res['unfetched'] += grp; continue
        time.sleep(PACE)
        print('batch', grp[0], len(res.get('refusals', [])), flush=True)
        byid = {g.get('id'): g for g in got}
        for k, b in enumerate(grp):
            h = (byid.get(k) or {}).get('result')
            if not h: res['unfetched'].append(b); continue
            mine = hdr[str(b)]
            o = [h['receiptsRoot'], h['gasUsed'], hashlib.sha256(h['logsBloom'].encode()).hexdigest()[:16]]
            if o == mine[:3]: res['equal'] += 1
            else: res['differ'].append({'block': b, 'replica': mine, 'official': o})
    res['brackets'].append({'from': bns[i], 'before': v0, 'after': ver()})
    print(bns[i], res['equal'], len(res['differ']), len(res['unfetched']), flush=True)
json.dump(res, open(out, 'w'), indent=0)
print('done', res['blocks'], res['equal'], len(res['differ']), len(res['unfetched']))
