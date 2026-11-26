"""run27.py on Tempo with every eth_call turned into eth_simulateV1 at a block time one hour after T14
(1796742000 + 3600), as cycle 25's t14run.py did. Read-only.
Usage: python3 -I t14_run27.py <outdir> [names...]"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import run27 as R
T14 = 1796742000 + 3600
_orig = R.T.rpc
def rpc(url, method, params, timeout=60):
    if method != 'eth_call':
        return _orig(url, method, params, timeout)
    bsc = {'calls': [dict(params[0])], 'blockOverrides': {'time': hex(T14)}}
    if len(params) > 2: bsc['stateOverrides'] = params[2]
    r = _orig(url, 'eth_simulateV1', [{'blockStateCalls': [bsc], 'validation': False}, params[1]], timeout)
    b = r[0]; assert int(b['timestamp'], 16) == T14
    c = b['calls'][0]
    if c.get('status') == '0x1': return c.get('returnData', '0x')
    raise RuntimeError(json.dumps({'message': (c.get('error') or {}).get('message', 'reverted'), 'data': c.get('returnData', '0x')})[:300])
R.T.rpc = rpc
sys.argv = ['run27.py', sys.argv[1], '4217', 'https://rpc.mainnet.tempo.xyz'] + sys.argv[2:]
R.main()
