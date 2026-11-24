"""Calls into the PoolManager by selector, from call frames that Monad nodes stored at block execution
(debug_traceTransaction, callTracer). Usage: python3 selscan.py <logs.jsonl> <ntx> <out.json> [seed]"""
import sys, json, random, time, collections, concurrent.futures as cf
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import rpc
PM = '0x188d586ddcf52439676ca21a244753fa19f9ea8e'
URLS = ['https://rpc.monad.xyz', 'https://rpc1.monad.xyz', 'https://rpc2.monad.xyz', 'https://rpc-mainnet.monadinfra.com', 'https://monad-mainnet.gateway.tatum.io']
WATCH = {'0x80f0b44c': 'clear', '0xfe99049a': 'transferFrom', '0x426a8493': 'approve', '0x234266d7': 'donate', '0xf5298aca': 'burn',
         '0x156e29f6': 'mint', '0x558a7297': 'setOperator', '0x095bcdb6': 'transfer', '0x3dd45adb': 'settleFor'}
def walk(f):
    yield f
    for c in f.get('calls') or []: yield from walk(c)
def job(a):
    i, h = a
    for k in range(8):
        try: return h, rpc(URLS[(i + k) % len(URLS)], 'debug_traceTransaction', [h, {'tracer': 'callTracer'}], timeout=60)
        except Exception: time.sleep(0.5 * (k + 1))
    return h, None
hs = set()
for line in open(sys.argv[1]):
    for l in json.loads(line)['logs'] or []:
        if l['a'] == PM: hs.add(l['h'])
hs = sorted(hs); random.Random(int(sys.argv[4]) if len(sys.argv) > 4 else 7).shuffle(hs); hs = hs[:int(sys.argv[2])]
res = {'txPool': None, 'traced': 0, 'failed': 0, 'pmCalls': collections.Counter(), 'pmCallsOk': collections.Counter(), 'callers': collections.defaultdict(collections.Counter), 'samples': collections.defaultdict(list), 'burnBySpender': 0}
with cf.ThreadPoolExecutor(6) as ex:
    for h, tr in ex.map(job, enumerate(hs)):
        if tr is None: res['failed'] += 1; continue
        res['traced'] += 1
        for f in walk(tr):
            if (f.get('to') or '').lower() != PM: continue
            sel = (f.get('input') or '')[:10]; name = WATCH.get(sel, sel)
            res['pmCalls'][name] += 1
            if not f.get('error'): res['pmCallsOk'][name] += 1
            if sel in WATCH:
                res['callers'][name][f['from'].lower()] += 1
                if len(res['samples'][name]) < 5: res['samples'][name].append(h)
                if name == 'burn' and not f.get('error'):
                    frm = '0x' + f['input'][10 + 24:10 + 64]
                    if frm.lower() != f['from'].lower(): res['burnBySpender'] += 1
res['txPool'] = len(hs)
json.dump({k: (dict(v) if isinstance(v, (collections.Counter, collections.defaultdict)) else v) for k, v in res.items()}, open(sys.argv[3], 'w'), indent=1, default=dict)
print(res['traced'], res['failed'], dict(res['pmCalls']), res['burnBySpender'])
