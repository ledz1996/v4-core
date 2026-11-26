"""Fetch a CREATE2-deployer transaction, split salt and init code, recompute the CREATE2 address, disassemble init code for ORIGIN/CALLER/CHAINID/SLOAD/SSTORE/CALL use. usage: tx.py url txhash. Read only."""
import sys, json
sys.path.insert(0, '.')
from rpcu import rpc
from kk import keccak, c2
from evmdis import dis
u, th = sys.argv[1], sys.argv[2]
cv = rpc(u, 'web3_clientVersion', [])
t = rpc(u, 'eth_getTransactionByHash', [th]); rc = rpc(u, 'eth_getTransactionReceipt', [th])
inp = bytes.fromhex(t['input'][2:]); salt, init = inp[:32], inp[32:]
addr = c2(t['to'], salt, init) if t['to'] else None
d = dis(init)
ops = {}
for pc, n, a in d:
    if n in ('ORIGIN', 'CALLER', 'CHAINID', 'SLOAD', 'SSTORE', 'CALL', 'STATICCALL', 'DELEGATECALL', 'CREATE', 'CREATE2', 'CODECOPY', 'TIMESTAMP', 'NUMBER', 'ADDRESS', 'SELFBALANCE', 'BALANCE', 'EXTCODESIZE'): ops.setdefault(n, []).append(pc)
r = {'url': u, 'client': [cv, rpc(u, 'web3_clientVersion', [])], 'tx': th, 'from': t['from'], 'to': t['to'], 'nonce': int(t['nonce'], 16), 'chainIdField': t.get('chainId'), 'type': t.get('type'), 'v': t.get('v'),
     'block': int(t['blockNumber'], 16), 'status': rc['status'], 'salt': '0x' + salt.hex(), 'initLen': len(init), 'initHash': '0x' + keccak(init).hex(), 'create2Address': addr, 'initOps': {k: v[:40] for k, v in ops.items()}, 'logs': len(rc['logs'])}
json.dump(r, open('raw/tx_%s.json' % th[:12], 'w'), indent=1)
open('raw/init_%s.hex' % th[:12], 'w').write(inp.hex())
print(json.dumps(r)[:3000])
