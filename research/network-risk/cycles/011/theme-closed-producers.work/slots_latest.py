"""HyperEVM: PoolManager slots touched by the traced removals, fee collections and undone payments,
read at latest from the official endpoint (validator state; it ignores block tags) and from nanoreth.
Read only. Usage: python3 slots_latest.py raw/hyper.json raw/hyper_slots.json"""
import sys, json, time
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import rpc as _rpc

def rpc(*a, **k):
    for i in range(8):
        try: return _rpc(*a, **k)
        except Exception as e:
            if i == 7: raise
            time.sleep(2 * (i + 1))
PM = '0x12D4Fd9C5DeDd00ab8a0bCe2CF0167bbf94b6B1F'
OFF, NR = 'https://rpc.hyperliquid.xyz/evm', 'https://rpc.purroofgroup.com'
d = json.load(open(sys.argv[1]))
hs = [r['tx'] for r in d['stateSamples']]
slots = set()
for h in hs:
    t = rpc(NR, 'debug_traceTransaction', [h, {'tracer': 'prestateTracer', 'tracerConfig': {'diffMode': True}}], timeout=90)
    for part in ('pre', 'post'):
        for a, v in t.get(part, {}).items():
            if a.lower() == PM.lower(): slots |= set((v.get('storage') or {}).keys())
res = {'slots': len(slots), 'equal': 0, 'diff': []}
for s in sorted(slots):
    for k in range(3):
        a = rpc(OFF, 'eth_getStorageAt', [PM, s, 'latest']); b = rpc(NR, 'eth_getStorageAt', [PM, s, 'latest'])
        if int(a, 16) == int(b, 16): res['equal'] += 1; break
        time.sleep(3)
    else:
        res['diff'].append([s, a, b])
json.dump(res, open(sys.argv[2], 'w'), indent=1); print(res['slots'], res['equal'], len(res['diff']))
