"""Cycle 33 ethereum-reference. Runs the battery, targeted and cycle 27 edge vectors on one endpoint that refuses
JSON-RPC batches, one eth_call per 600 vectors, and records web3_clientVersion before and after.
Usage: python3 single.py <out.json> <url>"""
import sys, json
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/027/ethereum-reference.work')
import evm, battery, targeted, pinrun
out, url = sys.argv[1], sys.argv[2]
V = battery.vectors() + targeted.vectors() + pinrun.extra()
before = evm.rpc(url, 'web3_clientVersion', [])
done, bad, errors = battery.run(url, battery.dispatcher(), V)
after = evm.rpc(url, 'web3_clientVersion', [])
r = {'url': url, 'vectors': len(V), 'ran': done, 'mismatchCount': len(bad), 'mismatches': bad[:100], 'errors': errors[:20], 'versionBefore': before, 'versionAfter': after}
json.dump(r, open(out, 'w'), indent=1); print(json.dumps({k: v for k, v in r.items() if k != 'mismatches'}))
