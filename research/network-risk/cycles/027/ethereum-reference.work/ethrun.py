"""Run an opdiff script with chain id 1 mapped to the given single-build Ethereum endpoints (first one is the
in-script reference), then compare every endpoint's result hashes with the stored Ethereum reference hashes of
research/network-risk/opcodes/<name>.json. Read-only: eth_call with state overrides only.
Usage: python3 ethrun.py <script.py> <stored ref json> <out.json> <n scripts> <url,url,...>"""
import sys, os, runpy, json, hashlib
OPD = '/home/user/v4-core/research/network-risk/tools/opdiff'
sys.path.insert(0, OPD)
import evm
script, stored, out, n, urls = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5].split(',')
NETS = [(1 if i == 0 else 9000 + i, u.split('//')[1].split('/')[0][:16], u) for i, u in enumerate(urls)]
evm.networks = lambda *a, **k: NETS
src = open(os.path.join(OPD, script)).read()
src = src.replace("ETH = 'https://ethereum-rpc.publicnode.com'", "ETH = %r" % urls[0])
sys.argv = [script, out, n]
g = {'__name__': '__main__', '__file__': os.path.join(OPD, script)}
import importlib
exec(compile(src, os.path.join(OPD, script), 'exec'), g)
res = json.load(open(out)); ref = json.load(open(stored))['referenceHashes']
cmp = {'storedRef': stored, 'endpoints': {}}
cmp['endpoints'][urls[0]] = {'identicalToStored': sum(1 for a, b in zip(res['referenceHashes'], ref) if a == b and not a.startswith('ERR')),
                              'errors': sum(1 for a in res['referenceHashes'] if a.startswith('ERR')),
                              'differentFromStored': [i for i, (a, b) in enumerate(zip(res['referenceHashes'], ref)) if a != b and not a.startswith('ERR') and not b.startswith('ERR')]}
for r in res['results']:
    cmp['endpoints'][NETS[r['chainId'] - 9000][2]] = {'vsInScriptRef': {k: r[k] for k in r if k in ('identical', 'different', 'errors')}}
res['storedComparison'] = cmp
json.dump(res, open(out, 'w'), indent=1); print(json.dumps(cmp, indent=1))
