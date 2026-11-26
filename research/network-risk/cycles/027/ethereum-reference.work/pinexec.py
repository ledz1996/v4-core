"""Run an opdiff script with chain id 1 = a single-build reference endpoint and chain id 9001 = the Pocket gateway,
where every eth_call to Pocket is retried until web3_clientVersion before and after both name the wanted build.
Then compare both with the stored Ethereum reference hashes. Read-only: eth_call with state overrides only.
Usage: python3 pinexec.py <script.py> <stored ref json> <out.json> <n scripts> <ref url> <build substring> [tries]"""
import sys, os, json, threading
OPD = '/home/user/v4-core/research/network-risk/tools/opdiff'
sys.path.insert(0, OPD)
import evm
script, stored, out, n, refurl, want = sys.argv[1:7]; tries = int(sys.argv[7]) if len(sys.argv) > 7 else 60
POCKET = 'https://eth.api.pocket.network'
NETS = [(1, 'ref', refurl), (9001, 'pocket-pinned', POCKET)]
evm.networks = lambda *a, **k: NETS
_orig = evm.rpc; LOG = {'pinnedCalls': 0, 'gaveUp': 0, 'attempts': 0}; L = threading.Lock()
def cv():
    try: return _orig(POCKET, 'web3_clientVersion', [], 20)
    except Exception as e: return 'ERR ' + str(e)[:40]
def pinned(url, method, params, timeout=60):
    if url != POCKET or method != 'eth_call': return _orig(url, method, params, timeout)
    for t in range(tries):
        with L: LOG['attempts'] += 1
        b = cv()
        if want not in b: continue
        try: r = _orig(url, method, params, timeout)
        except Exception as e:
            if 'execution reverted' in str(e) or 'out of gas' in str(e).lower(): r = e
            else: continue
        a = cv()
        if a == b:
            with L: LOG['pinnedCalls'] += 1
            if isinstance(r, Exception): raise r
            return r
    with L: LOG['gaveUp'] += 1
    raise RuntimeError('not pinned to ' + want)
evm.rpc = pinned
import pmdiff as _P
_P.ETH = refurl
src = open(os.path.join(OPD, script)).read().replace("ETH = 'https://ethereum-rpc.publicnode.com'", "ETH = %r" % refurl)
sys.argv = [script, out, n]
exec(compile(src, os.path.join(OPD, script), 'exec'), {'__name__': '__main__', '__file__': os.path.join(OPD, script)})
res = json.load(open(out)); ref = json.load(open(stored))['referenceHashes']
res['pinLog'] = LOG
res['refVsStored'] = {'identical': sum(1 for a, b in zip(res['referenceHashes'], ref) if a == b and not a.startswith('ERR')),
                      'different': [i for i, (a, b) in enumerate(zip(res['referenceHashes'], ref)) if a != b and not a.startswith('ERR') and not b.startswith('ERR')]}
json.dump(res, open(out, 'w'), indent=1); print(json.dumps({'pinLog': LOG, 'refVsStored': res['refVsStored'], 'results': res['results']}, indent=1))
