"""Probe the gas a simulated call is given on public endpoints. A stub (GAS PUSH0 MSTORE PUSH1 32 PUSH0 RETURN) is
placed by state override and called with gas 2e9, 1e9, 5e8, 3e8, 2e8, 1.5e8, 1e8, 6e7, 5e7, 3e7 in turn; the first that is accepted is kept
and the GAS word it returns is recorded. web3_clientVersion is read before and after.
Usage: python3 capprobe.py <out.json> <chainId> <url> [url ...]"""
import sys, os, json, time
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import rpc
STUB = '0x00000000000000000000000000000000ca9e0001'
CODE = '0x5a5f5260205ff3'
out, cid, urls = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
res = json.load(open(out)) if os.path.exists(out) else {}
for url in urls:
    r = {'chainId': cid, 'url': url, 'time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    try: r['clientVersion'] = rpc(url, 'web3_clientVersion', [], timeout=20)
    except Exception as e: r['clientVersion'] = 'ERR ' + str(e)[:150]
    try: r['chainIdRpc'] = int(rpc(url, 'eth_chainId', [], timeout=20), 16)
    except Exception as e: r['chainIdRpc'] = 'ERR ' + str(e)[:150]
    tries = []
    for g in (2_000_000_000, 1_000_000_000, 500_000_000, 300_000_000, 200_000_000, 150_000_000, 100_000_000, 60_000_000, 50_000_000, 30_000_000):
        try:
            v = rpc(url, 'eth_call', [{'to': STUB, 'gas': hex(g)}, 'latest', {STUB: {'code': CODE}}], timeout=30)
            tries.append({'gas': g, 'GAS': int(v, 16)}); break
        except Exception as e:
            tries.append({'gas': g, 'err': str(e)[:200]})
    r['tries'] = tries
    ok = [t for t in tries if 'GAS' in t]
    r['acceptedGas'] = ok[0]['gas'] if ok else None; r['gasSeen'] = ok[0]['GAS'] if ok else None
    try: r['clientVersionAfter'] = rpc(url, 'web3_clientVersion', [], timeout=20)
    except Exception as e: r['clientVersionAfter'] = 'ERR ' + str(e)[:150]
    res[url] = r
    print(cid, url, r['clientVersion'][:60] if isinstance(r['clientVersion'], str) else r['clientVersion'], r['chainIdRpc'], 'accepted', r['acceptedGas'], 'GAS', r['gasSeen'])
    json.dump(res, open(out, 'w'), indent=1)
