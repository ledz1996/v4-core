"""callTracer over every PoolManager transaction of one network; records every call into the PoolManager by selector,
and every clear(address,uint256) frame with caller, arguments, error and output. Read only.
Usage: clearscan.py <chainId> <url> <threads> <out.jsonl> <txlist.json>"""
import sys, os, json, time, collections, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rpcu import rpc
cid, url, th, out, lst = int(sys.argv[1]), sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5]
PM = {4326: '0xacb7e78fa05d562e0a5d3089ec896d57d057d38e', 999: '0x12d4fd9c5dedd00ab8a0bce2cf0167bbf94b6b1f'}[cid]
txs = json.load(open(lst))
done = set()
if os.path.exists(out):
    for line in open(out):
        try: done.add(json.loads(line)['tx'])
        except Exception: pass
todo = [t for t in txs if t not in done]
def walk(fr, acc, depth=0, rev=False):
    to = (fr.get('to') or '').lower(); inp = fr.get('input', '0x'); err = fr.get('error'); r = rev or bool(err)
    if to == PM:
        sel = inp[:10]; acc['sel'][sel] += 1
        if sel == '0x80f0b44c':
            acc['clear'].append({'from': fr.get('from', '').lower(), 'currency': '0x' + inp[34:74], 'amount': int(inp[74:138] or '0', 16),
                                 'error': err, 'revertedAncestor': rev, 'output': fr.get('output'), 'depth': depth})
    for c in fr.get('calls', []) or []: walk(c, acc, depth + 1, r)
def one(h):
    for k in range(8):
        try:
            t = rpc(url, 'debug_traceTransaction', [h, {'tracer': 'callTracer'}], timeout=120, tries=2)
            acc = {'sel': collections.Counter(), 'clear': []}; walk(t, acc)
            return {'tx': h, 'sel': acc['sel'], 'clear': acc['clear'], 'topErr': t.get('error')}
        except Exception as e:
            last = str(e)[:200]; time.sleep(2 + k)
    return {'tx': h, 'fail': last}
f = open(out, 'a'); n = 0; t0 = time.time()
with cf.ThreadPoolExecutor(th) as ex:
    for r in ex.map(one, todo):
        f.write(json.dumps(r) + '\n'); n += 1
        if n % 500 == 0: f.flush(); print(n, len(todo), round(time.time() - t0), flush=True)
print('finished', n, flush=True)
