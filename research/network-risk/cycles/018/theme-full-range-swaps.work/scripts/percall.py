"""Per-call gas of one script: debug_traceCall with callTracer, the frames below the unlock callback (the driver's
calls into the PoolManager) are listed with selector, gasUsed and error. Usage: python3 percall.py <set> <url> <gas> <out.json> <idx,...>"""
import sys, os, json, time
HERE = os.path.dirname(os.path.abspath(__file__))
R17 = os.path.join(HERE, '..', '..', '..', '017', 'theme-real-address-runs.work', 'scripts')
S, URL, GAS, OUT, IDX = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], [int(x) for x in sys.argv[5].split(',')]
sys.argv = ['realrun.py', S, 'fresh', '1', '/dev/null', '1']; sys.path.insert(0, R17)
import realrun as RR  # noqa
from evm import rpc  # noqa
_CODE_CACHE = os.path.join(HERE, '..', 'raw', 'pm-fresh-code.hex')  # deployed Ethereum PoolManager runtime, immutable rewritten to the fresh address (sha256 a7aaa3ba...)
RR.P.fetch_code = lambda: bytes.fromhex(open(_CODE_CACHE).read())
datas, kinds, drv, ov = RR.build()
res = json.load(open(OUT)) if os.path.exists(OUT) else {}
res.setdefault('_clientVersion', []).append(rpc(URL, 'web3_clientVersion', []))
for i in IDX:
    for k in range(4):
        try:
            t = rpc(URL, 'debug_traceCall', [{'to': drv, 'data': '0x' + datas[i].hex(), 'gas': hex(GAS)}, 'latest', {'stateOverrides': ov, 'tracer': 'callTracer'}], timeout=300); break
        except Exception as e: t = None; time.sleep(5)
    un = t['calls'][0]  # unlock
    cb = un['calls'][0]  # unlockCallback into the driver
    rows = [[c['input'][:10], int(c['gasUsed'], 16), c.get('error')] for c in cb.get('calls', [])]
    res[f'{S}-{i}'] = {'kinds': kinds[i], 'calls': rows}
    hv = sorted(rows, key=lambda r: -r[1])[:3]
    print(S, i, 'calls', len(rows), 'kinds', len(kinds[i]), 'heaviest', hv, flush=True)
res['_clientVersion'].append(rpc(URL, 'web3_clientVersion', []))
json.dump(res, open(OUT, 'w'), indent=1)
