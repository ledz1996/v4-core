"""HyperEVM operand-shape census over replica re-execution. Read-only.
Usage: census.py <name> <block list file or a:b range> <threads> <url1> [url2 ...]
Blocks are processed in chunks of 50; each chunk goes to one replica URL (round robin) and is bracketed with
web3_clientVersion. Each block's trace is streamed through shape_tracer.js and only counts are kept: per (op,class)
occurrences, blocks, first/last block and one example; for the PoolManager per (op,class,pc). The replica's header
fields (receiptsRoot, gasUsed, logsBloom digest, tx count) are kept per block for the comparison with the official endpoint.
State is saved to out/<name>.state.json after every chunk, so a rerun resumes."""
import json, sys, os, time, hashlib, threading, urllib.request, concurrent.futures as cf

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
name, spec, th, urls = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4:]
TR = open(os.path.join(W, 'scripts', 'shape_tracer.js')).read()
PM = '0x12d4fd9c5dedd00ab8a0bce2cf0167bbf94b6b1f'
if ':' in spec:
    a, b = map(int, spec.split(':')); blocks = list(range(a, b + 1))
else:
    blocks = sorted({int(l.split()[0]) for l in open(spec) if l.strip() and not l.startswith('#')})
SP = os.path.join(W, 'out', name + '.state.json')
st = json.load(open(SP)) if os.path.exists(SP) else {'done': [], 'failed': {}, 'cls': {}, 'pm': {}, 'hdr': {}, 'brackets': [], 'txs': 0, 'pmBlocks': []}
done = set(st['done'])
lock = threading.Lock()


def rpc(url, method, params, timeout=180):
    req = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    r = urllib.request.urlopen(urllib.request.Request(url, req, {'content-type': 'application/json', 'user-agent': 'census-readonly'}), timeout=timeout)
    return json.loads(r.read())


def ver(url):
    try: return rpc(url, 'web3_clientVersion', [], 30)['result']
    except Exception as e: return 'exc ' + str(e)[:80]


def one(url, bn):
    last = None
    for attempt in range(4):
        try:
            r = rpc(url, 'debug_traceBlockByNumber', [hex(bn), {"tracer": TR, "timeout": "300s"}], 400)
            h = rpc(url, 'eth_getBlockByNumber', [hex(bn), False], 60)
            if 'result' in r and h.get('result'):
                return bn, r['result'], h['result'], None
            last = json.dumps(r.get('error') or h.get('error'))[:300]
        except Exception as e:
            last = 'exc ' + str(e)[:300]
        time.sleep(2 + 4 * attempt)
    return bn, None, None, last


def merge(bn, res, hdr, url):
    pmhit = False
    st['hdr'][str(bn)] = [hdr['receiptsRoot'], hdr['gasUsed'], hashlib.sha256(hdr['logsBloom'].encode()).hexdigest()[:16], len(hdr['transactions']), url.split('/')[2]]
    for i, t in enumerate(res):
        st['txs'] += 1
        tr = t.get('result')
        if not isinstance(tr, dict):
            st['failed'].setdefault(str(bn), []).append('tx %d: %s' % (i, json.dumps(t)[:200])); continue
        txh = hdr['transactions'][i] if i < len(hdr['transactions']) else t.get('txHash')
        seen = set()
        for k, v in tr['m'].items():
            op, cl, ad, pc = k.split(':')
            kk = op + ':' + cl
            e = st['cls'].get(kk)
            if e is None:
                e = st['cls'][kk] = {'occ': 0, 'blocks': 0, 'txs': 0, 'first': bn, 'last': bn, 'firstEx': None, 'lastEx': None, '_lb': -1}
            e['occ'] += v[0]
            if (kk) not in seen: e['txs'] += 1; seen.add(kk)
            if e['_lb'] != bn: e['blocks'] += 1; e['_lb'] = bn
            ex = {'block': bn, 'tx': txh, 'contract': ad, 'pc': int(pc), 'a': v[1], 'b': v[2], 'c': v[3]}
            if bn <= e['first'] or e['firstEx'] is None: e['first'] = bn; e['firstEx'] = ex
            if bn >= e['last'] or e['lastEx'] is None: e['last'] = bn; e['lastEx'] = ex
            if ad == PM:
                pmhit = True
                k3 = op + ':' + cl + ':' + pc
                w = st['pm'].get(k3)
                if w is None: w = st['pm'][k3] = {'occ': 0, 'first': bn, 'last': bn, 'tx': txh, 'a': v[1], 'b': v[2], 'c': v[3]}
                w['occ'] += v[0]; w['first'] = min(w['first'], bn)
                if bn >= w['last']: w['last'] = bn; w['tx'] = txh; w['a'], w['b'], w['c'] = v[1], v[2], v[3]
    if pmhit: st['pmBlocks'].append(bn)


todo = [b for b in blocks if b not in done]
chunks = [todo[i:i + 50] for i in range(0, len(todo), 50)]
print(name, 'blocks', len(blocks), 'todo', len(todo), 'chunks', len(chunks), flush=True)


def run_chunk(ci):
    url = urls[ci % len(urls)]
    ch = chunks[ci]
    v0 = ver(url)
    with cf.ThreadPoolExecutor(4) as ex:
        res = list(ex.map(lambda b: one(url, b), ch))
    v1 = ver(url)
    with lock:
        bad = 0
        for bn, r, h, err in res:
            if r is None: st['failed'][str(bn)] = [err, url]; bad += 1; continue
            st['failed'].pop(str(bn), None)
            merge(bn, r, h, url); st['done'].append(bn)
        st['brackets'].append({'url': url, 'first': ch[0], 'last': ch[-1], 'n': len(ch), 'before': v0, 'after': v1, 'bad': bad, 't': int(time.time())})
        tmp = SP + '.tmp'; json.dump(st, open(tmp, 'w')); os.replace(tmp, SP)
        print(ci, url.split('/')[2], ch[0], ch[-1], v0, v1, 'bad', bad, 'done', len(st['done']), flush=True)


with cf.ThreadPoolExecutor(th) as ex:
    list(ex.map(run_chunk, range(len(chunks))))
print('finished', len(st['done']), 'failed', len(st['failed']), flush=True)
