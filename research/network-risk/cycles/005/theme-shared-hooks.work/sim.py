# eth_simulateV1 helper: run a list of calls in one simulated block (state carries from call to call). Read-only.
import json
from lib import *
from keccak import keccak256
from probe import key, w, a, SEL, cd, dec_err, EOA
def pool_id(c0, c1, fee, ts, hook): return '0x' + keccak256(bytes.fromhex(key(c0, c1, fee, ts, hook))).hex()
def simulate(u, calls, block='latest', overrides=None):
    bs = {'calls': calls}
    if overrides: bs['stateOverrides'] = overrides
    j = post(u, {'jsonrpc': '2.0', 'id': 1, 'method': 'eth_simulateV1', 'params': [{'blockStateCalls': [bs], 'validation': False}, block]})
    if 'error' in j: raise Exception(json.dumps(j['error'])[:300])
    out = []
    for c in j['result'][0]['calls']:
        ok = c.get('status') == '0x1'
        rd = c.get('returnData', '0x')
        out.append((ok, rd if ok else dec_err(rd) + ' | ' + str((c.get('error') or {}).get('message'))[:60], c.get('logs', []), int(c.get('gasUsed', '0x0'), 16)))
    return out
