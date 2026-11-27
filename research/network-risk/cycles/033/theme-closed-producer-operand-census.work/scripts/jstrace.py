"""Runs census_tracer.js through debug_traceTransaction for a list of transactions.
Read-only. Usage: jstrace.py <rpc url> <tx list file> <out dir> [threads]
Each batch of 50 is bracketed with web3_clientVersion (written to <out dir>/brackets.jsonl)."""
import json, sys, os, gzip, time, urllib.request, concurrent.futures as cf

url, lst, out = sys.argv[1], sys.argv[2], sys.argv[3]
th = int(sys.argv[4]) if len(sys.argv) > 4 else 4
os.makedirs(out, exist_ok=True)
TR = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'census_tracer.js')).read()


def rpc(method, params, timeout=120):
    req = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    r = urllib.request.urlopen(urllib.request.Request(url, req, {'content-type': 'application/json', 'user-agent': 'census-readonly'}), timeout=timeout)
    return json.loads(r.read())


def one(tx):
    p = os.path.join(out, tx + '.json.gz')
    if os.path.exists(p): return tx, 'cached'
    for attempt in range(4):
        try:
            r = rpc('debug_traceTransaction', [tx, {"tracer": TR, "timeout": "120s"}])
            if 'result' in r:
                json.dump({'tx': tx, 'url': url, 'result': r['result']}, gzip.open(p, 'wt'))
                return tx, 'ok'
            err = r.get('error')
            if attempt == 3: return tx, 'error ' + json.dumps(err)[:300]
        except Exception as e:
            if attempt == 3: return tx, 'exc ' + str(e)[:300]
        time.sleep(2 + 3 * attempt)


txs = [l.split()[0] for l in open(lst) if l.strip() and not l.startswith('#')]
bf = open(os.path.join(out, 'brackets.jsonl'), 'a')
ef = open(os.path.join(out, 'errors.jsonl'), 'a')
for i in range(0, len(txs), 50):
    batch = txs[i:i + 50]
    try: v0 = rpc('web3_clientVersion', [])['result']
    except Exception as e: v0 = 'exc ' + str(e)[:100]
    with cf.ThreadPoolExecutor(th) as ex:
        res = list(ex.map(one, batch))
    try: v1 = rpc('web3_clientVersion', [])['result']
    except Exception as e: v1 = 'exc ' + str(e)[:100]
    bad = [r for r in res if r[1] not in ('ok', 'cached')]
    for r in bad: ef.write(json.dumps({'tx': r[0], 'why': r[1]}) + '\n')
    bf.write(json.dumps({'first': i, 'n': len(batch), 'before': v0, 'after': v1, 'bad': len(bad), 't': time.time()}) + '\n'); bf.flush(); ef.flush()
    print(i, len(batch), v0, v1, 'bad', len(bad), flush=True)
