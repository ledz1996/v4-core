"""Cycle 16, theme-revert-rollback-mined, task 2. Read-only: eth_call with the probe's code placed by state
override at a fresh address, against the deployed PoolManager of each network. No transaction is sent.
Usage: python3 halt.py <out.json> [chainIds...]"""
import sys, json, time, concurrent.futures as cf
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import rpc, keccak
B = json.load(open('/home/user/v4-core/research/network-risk/cycles/016/theme-revert-rollback-mined.work/build/HaltProbe.json'))
CODE = '0x' + B['runtime']; P = '0x00000000000000000000000000000000c0ffee16'
nets = json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))['networks']
ALT = {}
def sel(sig): return keccak(sig.encode())[:4].hex()
def w(x): return x.to_bytes(32, 'big').hex()
def addr(a): return w(int(a, 16))
def call(url, data, gas):
    last = None
    for k in range(5):
        try:
            return rpc(url, 'eth_call', [{'from': '0x00000000000000000000000000000000000a11ce', 'to': P, 'data': data, 'gas': hex(gas)}, 'latest', {P: {'code': CODE}}], timeout=120)
        except Exception as e:
            last = e
            if 'gas' in str(e).lower() and 'cap' in str(e).lower(): raise
            time.sleep(2 * (k + 1))
    raise last
def words(h): b = bytes.fromhex(h[2:]); return [int.from_bytes(b[i:i + 32], 'big') for i in range(0, len(b), 32)]
def go(n):
    url = ALT.get(n['chainId'], n['rpc']); pm = n['poolManager']; res = {'chain': n['chainId'], 'name': n['name'], 'pm': pm}
    try:
        g = 30_000_000
        r = words(call(url, '0x' + sel('kinds(address)') + addr(pm), g))
        arr = r[2:]; rows = []
        for i in range(0, len(arr), 10):
            if arr[i] == 0 and i > 0: break
            rows.append(arr[i:i + 10])
        res['kinds'] = rows
        # a failed attempt leaks when any PoolManager or probe slot it wrote reads back; the reserves slot is
        # compared with the value this attempt would have written (1000 + attempt id), since an earlier successful control leaves its own
        res['kindsLeak'] = [x[0] for x in rows if x[1] == 0 and (any(x[2:6]) or x[6] == 1000 + x[0] or any(x[7:]))]
        res['controlsVisible'] = [x[0] for x in rows if x[1] == 1 and (x[5] or x[8])]
    except Exception as e: res['kindsErr'] = str(e)[:200]
    try:
        res['depth'] = words(call(url, '0x' + sel('depthRun()'), 30_000_000))[0]
    except Exception as e: res['depthErr'] = str(e)[:200]
    sw = []
    def sweep(variant, a, b, st):
        o = words(call(url, '0x' + sel('sweep(address,uint256,uint256,uint256,uint256)') + addr(pm) + w(variant) + w(a) + w(b) + w(st), 29_000_000))
        rec = {'variant': variant, 'range': [a, b, st], 'attempts': o[0], 'fails': o[1], 'leaks': o[2],
               'firstLeakGas': None if o[3] == 2**256 - 1 else o[3], 'successGas': None if o[4] == 2**256 - 1 else o[4], 'afterSuccess': o[6:14]}
        sw.append(rec); return rec
    def chunks(variant, a, b, st, per):
        x = a
        while x < b:
            y = min(b, x + per * st)
            try: r = sweep(variant, x, y, st)
            except Exception as e: sw.append({'variant': variant, 'range': [x, y, st], 'err': str(e)[:160]}); r = {}
            if r.get('successGas'): return r['successGas']
            x = y
        return None
    for variant in (1, 2):
        try:
            gc = chunks(variant, 1, 400001, 500, 60)
            if gc is None: continue
            gs = chunks(variant, max(1, gc - 500), gc + 1, 1, 400)
            lo = max(1, gs - 8000)
            chunks(variant, lo, gs, 1, 400)
            if lo > 1: chunks(variant, 1, lo, 9, 400)
            res.setdefault('successGas', {})[variant] = gs
        except Exception as e: res.setdefault('sweepErr', []).append(str(e)[:160])
    res['sweep'] = sw
    res['sweepAttempts'] = sum(s.get('attempts', 0) for s in sw); res['sweepFails'] = sum(s.get('fails', 0) for s in sw)
    res['sweepLeaks'] = sum(s.get('leaks', 0) for s in sw); res['sweepErrors'] = sum('err' in s for s in sw)
    return res
if __name__ == '__main__':
    out = sys.argv[1]; ids = [int(x) for x in sys.argv[2:]]
    sel_nets = [n for n in nets if not ids or n['chainId'] in ids]
    with cf.ThreadPoolExecutor(7) as ex: R = list(ex.map(go, sel_nets))
    json.dump(R, open(out, 'w'), indent=1)
    for r in R: print(r['chain'], r.get('kindsLeak'), r.get('controlsVisible'), r.get('kindsErr', ''), 'depth', r.get('depth', r.get('depthErr')), 'sweep', r['sweepAttempts'], r['sweepFails'], r['sweepLeaks'], r['sweepErrors'], r.get('successGas'))
