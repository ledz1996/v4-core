"""Short form of monadpage.py (which timed out on log queries): page 0 of the PoolManager on Monad, read with
extsload(0,128) in the EVM and eth_getStorageAt for slots 0..9 and 120..129, no override. Usage: monadpage0.py <out.json>"""
import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'tools', 'opdiff'))
from evm import keccak, rpc
U, PM = 'https://rpc.monad.xyz', '0x188d586ddcf52439676ca21a244753fa19f9ea8e'
rec = {'clientBefore': rpc(U, 'web3_clientVersion', [])}
blk = rpc(U, 'eth_blockNumber', []); rec['block'] = int(blk, 16)
d = keccak(b'extsload(bytes32,uint256)')[:4] + (0).to_bytes(32, 'big') + (130).to_bytes(32, 'big')
o = bytes.fromhex(rpc(U, 'eth_call', [{'to': PM, 'data': '0x' + d.hex()}, blk])[2:])
w = [int.from_bytes(o[64 + 32 * i:96 + 32 * i], 'big') for i in range(130)]
g = {}
for i in list(range(10)) + list(range(120, 130)):
    g[i] = int(rpc(U, 'eth_getStorageAt', [PM, hex(i), blk]), 16); time.sleep(0.3)
rec['nonzeroExtsload'] = {hex(i): hex(v) for i, v in enumerate(w) if v}
rec['mismatches'] = [hex(i) for i in g if g[i] != w[i]]
rec['clientAfter'] = rpc(U, 'web3_clientVersion', [])
print(json.dumps(rec)[:800]); json.dump(rec, open(sys.argv[1], 'w'), indent=1)
