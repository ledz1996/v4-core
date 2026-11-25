"""Binary search for the largest gas requirement X for which eth_estimateGas still succeeds on a probe
contract (state override at an unused address) that reverts unless GAS >= X at its first instruction.
The estimate then returns about X + 21,000 + a few gas; the boundary is the endpoint's estimation ceiling.
usage: python3 -I estcap.py <out.json> [chainId ...]"""
import sys, json, concurrent.futures as cf
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/020/theme-mined-gas-cap.work/scripts')
from rpc import call, NET
from probe_caps import PROBE, needgas

def ok(url, x):
    res = call(url, 'eth_estimateGas', [{'to': PROBE, 'data': '0x'}, 'latest', {PROBE: {'code': needgas(x)}}])
    v = res.get('result')
    return (int(v, 16) if isinstance(v, str) else None), res

def search(n):
    url = n['rpc']
    lo, hi = 1_000_000, 2**32 - 1
    e, _ = ok(url, lo)
    if e is None:
        return {'chainId': n['chainId'], 'error': _}
    e2, r2 = ok(url, hi)
    if e2 is not None:
        return {'chainId': n['chainId'], 'name': n['name'], 'maxNeed': hi, 'estimateAtMax': e2, 'note': 'no ceiling below 2^32'}
    best = e
    while hi - lo > 1:
        mid = (lo + hi) // 2
        em, _ = ok(url, mid)
        if em is None: hi = mid
        else: lo, best = mid, em
    _, rfail = ok(url, hi)
    return {'chainId': n['chainId'], 'name': n['name'], 'maxNeedOk': lo, 'estimateAtMaxNeedOk': best, 'firstFailNeed': hi,
            'failResponse': rfail}

if __name__ == '__main__':
    ids = [int(a) for a in sys.argv[2:]] or [n['chainId'] for n in NET]
    nets = [n for n in NET if n['chainId'] in ids]
    with cf.ThreadPoolExecutor(7) as ex:
        res = list(ex.map(search, nets))
    json.dump(res, open(sys.argv[1], 'w'), indent=1)
    for r in res: print(json.dumps({k: v for k, v in r.items() if k != 'failResponse'}))
