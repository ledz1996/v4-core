"""For Polygon script mismatches: fetch the Ethereum answer for the same script and report the first differing call.
Read-only eth_call. Usage: python3 -I firstdiff.py <pin-polygon-pmdiffX.json> <pmdiff|pmdiff2> <out.json> [max]"""
import sys, json, hashlib
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/037/theme-rotating-endpoint-build-pins.work/scripts')
import pinrun as PR
sys.path.insert(0, PR.T)
import pmdiff as P
from evm import rpc
f, which, out = sys.argv[1], sys.argv[2], sys.argv[3]; mx = int(sys.argv[4]) if len(sys.argv) > 4 else 99
d = json.load(open(f)); jobs, _ = PR.script_jobs(which); items = {it[2][1]: it for j in jobs for it in j}
seen = {}; res = []
for m in d['mismatches']:
    if m['script'] in seen or len(seen) >= mx: continue
    seen[m['script']] = 1; tx, ov, meta = items[m['script']]
    kinds = None
    eth = rpc('https://ethereum-rpc.publicnode.com', 'eth_call', [tx, 'latest', ov], 120)
    a = P.parse(bytes.fromhex(m['answer'][2:])); b = P.parse(bytes.fromhex(eth[2:]))
    ethsha = hashlib.sha256(bytes.fromhex(eth[2:])).hexdigest()
    k = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
    res.append({'script': m['script'], 'ethMatchesStoredRef': ethsha == m['refSha256'], 'callsPolygon': len(a), 'callsEthereum': len(b), 'firstDiff': k,
                'polygonAtDiff': [a[k][0], a[k][1].hex()[:80]] if k < len(a) else None, 'ethereumAtDiff': [b[k][0], b[k][1].hex()[:80]] if k < len(b) else None,
                'selectorOfDiffCall': tx['data'][2:][0:0]})
    print(res[-1], flush=True)
json.dump(res, open(out, 'w'), indent=1)
