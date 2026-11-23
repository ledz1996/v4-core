# Code length, selector set and three getters of the protocol fee controller on the eight networks that have one.
import json, hashlib, re, os
from lib import *
out = {}
for cid in (1, 10, 8453, 42161, 4663, 137, 56, 5042):
    n = net(cid); u = n['rpc']; c = n['protocolFeeController']
    b = bytes.fromhex(rpc(u, 'eth_getCode', [c, 'latest']).get('result', '0x')[2:])
    row = {'controller': c, 'len': len(b), 'sha': hashlib.sha256(b).hexdigest()[:16]}
    for sig in ('owner()', 'POOL_MANAGER()', 'TOKEN_JAR()', 'feeSetter()', 'policy()'):
        r = rpc(u, 'eth_call', [{'to': c, 'data': '0x' + sel(sig)}, 'latest']); row[sig] = r['result'][-40:] if 'result' in r else 'ERR'
    row['selectors'] = sorted(set(m.hex() for m in re.findall(rb'\x63(.{4})\x14', b, flags=re.S)))
    out[cid] = row; print(cid, json.dumps(row))
json.dump(out, open(os.path.join(HERE, 'raw', 'controllers.json'), 'w'), indent=1)
