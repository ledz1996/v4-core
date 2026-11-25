"""Explain each call that differs between a network's real-address record and Ethereum's (raw/alldiffs?.json).

A differing call counts as explained by state when both sides succeeded with return data of the same length and every
32 byte word that differs is, on the network side, the value of some piece of the PoolManager's own on-chain state, and
on the Ethereum side the value of the same piece of Ethereum's PoolManager state. The pieces are read here with
eth_getStorageAt and eth_call at the real address: storage slots 0 to 6 and 2^256-2, 2^256-1, protocolFeesAccrued for
the currencies the scripts use, and the native balance. Calls that failed on one side are listed with the network's
native balance so that native payouts can be checked by hand. Everything else is printed as unexplained.

Usage: python3 explain.py <out.json>
"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, '..', '..', '..', '..', 'tools', 'opdiff')
sys.path.insert(0, TOOLS)
from evm import rpc, keccak  # noqa

NWS = {n['chainId']: n for n in json.load(open(os.path.join(TOOLS, '..', '..', 'state', 'networks.json')))['networks']}
W = os.path.join(HERE, '..', 'raw')
M = (1 << 256) - 1
CUR = {'0': 0, 'T0': 0xC0FFEE01, 'T1': 0xC0FFEE02, 'BT': 0xC0FFEE05}
ACC = keccak(b'protocolFeesAccrued(address)')[:4]


def w(x): return (x & M).to_bytes(32, 'big')


def q(url, m, p):
    for k in range(5):
        try: return rpc(url, m, p, timeout=60)
        except Exception as e: last = str(e)  # noqa
    return 'ERR ' + last


def roles(cid):
    n = NWS[cid]; url = n['rpc']; pm = n['poolManager']
    r = {}
    for s in list(range(7)) + [M - 1, M]:
        r[f'slot{s if s < 7 else ("max-1" if s == M - 1 else "max")}'] = int(q(url, 'eth_getStorageAt', [pm, hex(s), 'latest']), 16)
    for k, c in CUR.items():
        r[f'accrued{k}'] = int(q(url, 'eth_call', [{'to': pm, 'data': '0x' + (ACC + w(c)).hex()}, 'latest']), 16)
    r['nativeBalance'] = int(q(url, 'eth_getBalance', [pm, 'latest']), 16)
    return r


def main(outp):
    R = {cid: roles(cid) for cid in NWS}
    out = {'roles': {str(k): {a: hex(b) for a, b in v.items()} for k, v in R.items()}, 'sets': {}}
    for s in ('2', '6'):
        d = json.load(open(os.path.join(W, f'alldiffs{s}.json')))
        res = {}
        for cid, scr in d.items():
            E, X = R[1], R[int(cid)]
            for i, v in scr.items():
                if isinstance(v, str): res.setdefault(cid, {})[i] = {'unexplained': v}; continue
                ex, fail, un = [], [], []
                for k, xo, xr, eo, er in v['diffs']:
                    xb, eb = bytes.fromhex(xr), bytes.fromhex(er)
                    if xo and eo and len(xb) == len(eb):
                        ok = True; used = set()
                        for j in range(0, len(xb), 32):
                            a, b = int.from_bytes(xb[j:j + 32], 'big'), int.from_bytes(eb[j:j + 32], 'big')
                            if a == b: continue
                            hit = [r for r in X if X[r] == a and E[r] == b]
                            if not hit: ok = False; break
                            used.update(hit)
                        (ex if ok else un).append([k, sorted(used)] if ok else [k, xo, xr[:300], eo, er[:300]])
                    else:
                        fail.append([k, xo, xr[:140], eo, er[:140]])
                res.setdefault(cid, {})[i] = {'explainedByState': ex, 'failedOnOneSide': fail, 'unexplained': un}
        out['sets'][s] = res
    json.dump(out, open(outp, 'w'), indent=1)
    for s, res in out['sets'].items():
        for cid, scr in res.items():
            for i, v in scr.items():
                if v.get('unexplained') or v.get('failedOnOneSide'):
                    print('set', s, 'chain', cid, 'script', i, 'explained', len(v.get('explainedByState', [])), 'failed', [(f[0], f[1], f[3], f[2][:72]) for f in v.get('failedOnOneSide', [])],
                          'UNEXPLAINED', v.get('unexplained'))
    for cid in NWS: print(cid, NWS[cid]['name'], 'native balance', R[cid]['nativeBalance'], 'accrued0', R[cid]['accrued0'])


if __name__ == '__main__':
    main(sys.argv[1])
