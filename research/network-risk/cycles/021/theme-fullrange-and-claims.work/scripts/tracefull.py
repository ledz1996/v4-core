"""Like runfull.py, but through debug_traceCall with the callTracer, for endpoints whose eth_call cap is too low and
whose debug_traceCall cap is higher. The top frame's output is the driver's answer; gasUsed of the top frame is kept.
The callTracer frame tree is reduced to a count of frames and of failed frames, and the first failed frame's error.
Usage: python3 tracefull.py <set> <url> <gas> <out.json> <idx,...> [label]"""
import sys, os, json, hashlib, time
HERE = os.path.dirname(os.path.abspath(__file__))
R17 = '/home/user/v4-core/research/network-risk/cycles/017/theme-real-address-runs.work/scripts'
S, URL, GAS, OUT, IDX = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], [int(x) for x in sys.argv[5].split(',')]
LABEL = sys.argv[6] if len(sys.argv) > 6 else ''
sys.argv = ['realrun.py', S, 'fresh', '1', '/dev/null', '1']
sys.path.insert(0, R17)
import realrun as RR  # noqa
from evm import rpc  # noqa
_CODE_CACHE = '/home/user/v4-core/research/network-risk/cycles/018/theme-full-range-swaps.work/raw/pm-fresh-code.hex'  # deployed Ethereum PoolManager runtime, immutable rewritten to the fresh address (sha256 a7aaa3ba...)
RR.P.fetch_code = lambda: bytes.fromhex(open(_CODE_CACHE).read())
datas, kinds, drv, ov = RR.build()
res = json.load(open(OUT)) if os.path.exists(OUT) else {'set': S, 'url': URL, 'gas': GAS, 'label': LABEL, 'batches': [], 'scripts': {}}
def q(m, p):
    try: return rpc(URL, m, p, timeout=30)
    except Exception as e: return 'ERR ' + str(e)[:120]
def walk(f, acc):
    acc['frames'] += 1
    if f.get('error'):
        acc['failed'] += 1
        if acc['firstError'] is None: acc['firstError'] = [f.get('error'), f.get('to'), f.get('input', '')[:10], int(f.get('gasUsed', '0x0'), 16), int(f.get('gas', '0x0'), 16)]
    for c in f.get('calls', []) or []: walk(c, acc)
b = {'clientVersionBefore': q('web3_clientVersion', []), 'blockBefore': q('eth_blockNumber', []), 'start': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'idx': IDX}
for i in IDX:
    r = {}; last = None
    for k in range(4):
        try:
            t = rpc(URL, 'debug_traceCall', [{'to': drv, 'data': '0x' + datas[i].hex(), 'gas': hex(GAS)}, 'latest', {'stateOverrides': ov, 'tracer': 'callTracer'}], timeout=300)
            last = None; break
        except Exception as e:
            last = str(e)[:300]; time.sleep(5 * (k + 1))
    if last: r['err'] = last
    else:
        out = t.get('output', '0x')
        r['output'] = out; r['hash'] = hashlib.sha256(bytes.fromhex(out[2:])).hexdigest(); r['gasUsed'] = int(t.get('gasUsed', '0x0'), 16); r['gasGiven'] = int(t.get('gas', '0x0'), 16)
        acc = {'frames': 0, 'failed': 0, 'firstError': None}; walk(t, acc); r.update(acc)
    res['scripts'][str(i)] = r
    print(S, i, r.get('hash', r.get('err', ''))[:16], 'gasUsed', r.get('gasUsed'), 'given', r.get('gasGiven'), 'frames', r.get('frames'), 'failed', r.get('failed'), r.get('firstError'), flush=True)
b['clientVersionAfter'] = q('web3_clientVersion', []); b['blockAfter'] = q('eth_blockNumber', []); b['end'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
res['batches'].append(b)
json.dump(res, open(OUT, 'w'), indent=1)
