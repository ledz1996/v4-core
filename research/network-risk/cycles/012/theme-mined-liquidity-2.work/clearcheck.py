"""For transactions whose payout differs from the source's owed amount, sum the clear(currency, amount) frames
(src/PoolManager.sol clear) and the ERC-20 transfers into the PoolManager that no settle credited, from the
call tracer, and compare with the difference. Usage: clearcheck.py <chainId> <an.json> <traceUrl> <out.json>"""
import sys, json
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import rpc
cid, f, url, out = int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
NETS = {n['chainId']: n for n in json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))['networks']}
PM = NETS[cid]['poolManager'].lower()
res = []
for r in json.load(open(f))['results']:
    if r.get('result') in (None, 'exact'): continue
    t = rpc(url, 'debug_traceTransaction', [r['tx'], {'tracer': 'callTracer'}], timeout=90)
    clears = {}
    def walk(c, ok):
        ok = ok and not c.get('error')
        if ok and (c.get('to') or '').lower() == PM and (c.get('input') or '').startswith('0x80f0b44c'):
            inp = c['input']; cur = '0x' + inp[10 + 24:74]; amt = int(inp[74:138], 16)
            clears[cur] = clears.get(cur, 0) + amt
        for k in c.get('calls') or []: walk(k, ok)
    walk(t, True)
    expl = {c: (int(v['diff']) == -clears.get(c, 0)) for c, v in r['currencies'].items() if v['diff'] != '0'}
    res.append({'tx': r['tx'], 'block': r['block'], 'diffs': {c: v['diff'] for c, v in r['currencies'].items() if v['diff'] != '0'}, 'clears': {c: str(v) for c, v in clears.items()}, 'explainedByClear': expl, 'native': r.get('native')})
    print(res[-1], flush=True)
json.dump(res, open(out, 'w'), indent=1)
