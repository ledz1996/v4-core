# Rerun an opdiff tool against Tempo with every eth_call turned into eth_simulateV1 at a block time
# one hour after T14 (1796742000 + 3600). t14probe.py shows the override switches Tempo to T14 rules.
# Usage: python3 t14run.py <tool.py> <args...>   (run from tools/opdiff; read-only)
import sys, json, runpy, os
sys.path.insert(0, os.getcwd())
import evm
T = 1796742000 + 3600
_orig = evm.rpc
def rpc(url, method, params, timeout=60):
    if method != 'eth_call' or 'tempo' not in url:
        return _orig(url, method, params, timeout)
    tx = dict(params[0]); ov = params[2] if len(params) > 2 else None
    bsc = {'calls': [tx], 'blockOverrides': {'time': hex(T)}}
    if ov: bsc['stateOverrides'] = ov
    r = _orig(url, 'eth_simulateV1', [{'blockStateCalls': [bsc], 'validation': False}, params[1] if len(params) > 1 else 'latest'], timeout)
    b = r[0]; assert int(b['timestamp'], 16) == T, b['timestamp']
    c = b['calls'][0]
    if c.get('status') == '0x1': return c.get('returnData', '0x')
    raise RuntimeError(json.dumps({'message': (c.get('error') or {}).get('message', 'reverted'), 'data': c.get('returnData', '0x')})[:300])
evm.rpc = rpc
for mod in ('battery', 'pmdiff', 'pmdiff2', 'targeted'):
    pass
tool = sys.argv[1]; sys.argv = [tool] + sys.argv[2:]
# patch modules that did 'from evm import rpc' after import
import importlib
for name in ('battery', 'pmdiff', 'pmdiff2'):
    try:
        m = importlib.import_module(name); m.rpc = rpc
    except Exception as e: print('import', name, e)
runpy.run_path(tool, run_name='__main__', init_globals={'rpc': rpc})
