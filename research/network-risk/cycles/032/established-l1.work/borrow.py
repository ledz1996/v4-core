"""Cycle 28 hyperevm, lead L-1143: scripts that make getFeeGrowthInside (src/libraries/Pool.sol:498-509) borrow in
each of its three unchecked subtractions, run in the reference interpreter (pyevm) and on the given endpoints by
eth_call with state overrides only (pmdiff6 driver, tokens and world). The PoolManager bytecode is the one deployed
on HyperEVM (PM_FROM=999), with its own address replaced by the test address as pmdiff.fetch_code does.
Usage: python3 borrow.py <out.json> <url> [<url> ...]"""
import sys, os, json, hashlib
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
os.environ.setdefault('PM_FROM', '999')
import pmdiff6 as D, pmdiff as P, v4math as m
from evm import keccak, rpc, MASK

w = D.w
def sp(t): return m.get_sqrt_price_at_tick(t)
K = D.key(D.T0, D.T1, 3000, 60, 0)
BASE = int.from_bytes(keccak(D.pid(K) + w(6)), 'big')
def tslot(t, j): return (int.from_bytes(keccak(w(t & MASK) + w(BASE + 4)), 'big') + j) & MASK
def possl(lo, hi, j, salt=0):
    pk = keccak(D.DRV.to_bytes(20, 'big') + (lo & 0xffffff).to_bytes(3, 'big') + (hi & 0xffffff).to_bytes(3, 'big') + w(salt))
    return (int.from_bytes(keccak(pk + w(BASE + 6)), 'big') + j) & MASK
def reads(ticks, pos):
    r = [D.ext((BASE + j) & MASK) for j in (0, 1, 2, 3)]
    for t in ticks: r += [D.ext(tslot(t, j)) for j in (1, 2)]
    for lo, hi in pos: r += [D.ext(possl(lo, hi, j)) for j in (0, 1, 2)]
    return r
BIG = 10 ** 30
def S(items): return b''.join(items) + D.end(0)
I = lambda x: D.it(D.PMI, x)
scripts = {
    # line 499-500: current below the range, lower tick new (outside 0), upper tick crossed downward (outside > 0)
    'below-range borrow (Pool.sol:499-500)': S([I(D.init(K, 1 << 96)), I(D.mod(K, -600, 600, 10 ** 20)),
        I(D.swap(K, False, -BIG, sp(200))), I(D.mod(K, 120, 180, 10 ** 18)), I(D.swap(K, True, -BIG, sp(-100))),
        I(D.mod(K, 60, 120, 10 ** 18))] + reads((60, 120, 180), ((60, 120),)) + [
        I(D.swap(K, True, -BIG, sp(-300))), I(D.swap(K, False, -BIG, sp(-150))), I(D.mod(K, 60, 120, -(10 ** 18)))]
        + reads((60, 120), ((60, 120),))),
    # line 502-503: current above the range, lower tick new at a later global (outside large), upper crossed upward earlier
    'above-range borrow (Pool.sol:502-503)': S([I(D.init(K, 1 << 96)), I(D.mod(K, -600, 600, 10 ** 20)),
        I(D.mod(K, 120, 180, 10 ** 18)), I(D.swap(K, False, -BIG, sp(240))), I(D.mod(K, 60, 120, 10 ** 18))]
        + reads((60, 120, 180), ((60, 120),)) + [I(D.swap(K, False, -BIG, sp(400))), I(D.swap(K, True, -BIG, sp(300))),
        I(D.mod(K, 60, 120, -(10 ** 18)))] + reads((60, 120), ((60, 120),))),
    # line 505-508: the first position of script 1, then the price is moved into its range and it is poked and removed
    'in-range wrap (Pool.sol:505-508)': S([I(D.init(K, 1 << 96)), I(D.mod(K, -600, 600, 10 ** 20)),
        I(D.swap(K, False, -BIG, sp(200))), I(D.mod(K, 120, 180, 10 ** 18)), I(D.swap(K, True, -BIG, sp(-100))),
        I(D.mod(K, 60, 120, 10 ** 18)), I(D.swap(K, False, -BIG, sp(90))), I(D.swap(K, True, -BIG, sp(70))),
        I(D.mod(K, 60, 120, 0)), I(D.swap(K, False, -BIG, sp(110))), I(D.mod(K, 60, 120, -(10 ** 18)))]
        + reads((60, 120), ((60, 120),))),
}

def main():
    out, urls = sys.argv[1], sys.argv[2:]
    code = P.fetch_code(); ov = D.overrides(code); res = {'scripts': {}, 'urls': {}}
    for name, data in scripts.items():
        wd = D.world(code); wd.max_steps = 40_000_000
        ok, ret = wd.call(0, D.DRV, 0, data, False, 0)
        rec = D.P.parse(D.unwrap(ret))
        br = {str(pc): sorted(o) for (a, pc), o in wd.branches.items() if a == D.PMI}
        res['scripts'][name] = {'refHash': hashlib.sha256(ret).hexdigest(), 'calls': len(rec),
                                'failed': [i for i, (k, _) in enumerate(rec) if not k],
                                'words': [r.hex() for k, r in rec[-40:]], 'ops': wd.ops.get(0x03, 0)}
        print(name, 'reference calls', len(rec), 'failed', res['scripts'][name]['failed'], flush=True)
        for url in urls:
            cv = rpc(url, 'web3_clientVersion', [], 20)
            r = rpc(url, 'eth_call', [{'to': '0x' + D.DRV.to_bytes(20, 'big').hex(), 'data': '0x' + data.hex(), 'gas': hex(29_000_000)}, 'latest', ov], timeout=120)
            h = hashlib.sha256(bytes.fromhex(r[2:])).hexdigest()
            res['urls'].setdefault(url, {})[name] = {'clientVersion': cv, 'equal': h == res['scripts'][name]['refHash']}
            print('  ', url, cv, 'equal' if h == res['scripts'][name]['refHash'] else 'DIFFERENT', flush=True)
    json.dump(res, open(out, 'w'), indent=1)

if __name__ == '__main__': main()
