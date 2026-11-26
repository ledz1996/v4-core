"""Code size of the CREATE2 deployer 0x4e59b448 and CreateX 0xba5Ed099 on all 21 networks. Read only."""
import json
from ep import rpc
from xchain_urls import SU
F = {'create2Deployer': '0x4e59b44847b379578588920ca78fbf26c0b4956c', 'createX': '0xba5ed099633d3b313e4d5f7bdc1305d3c28ba5ed'}
out = {}
for c, u in SU.items():
    out[c] = {'url': u, 'client': rpc(u, 'web3_clientVersion', [])}
    for k, a in F.items(): out[c][k] = (len(rpc(u, 'eth_getCode', [a, 'latest'])) - 2) // 2
    print(c, out[c])
json.dump(out, open('raw/factories.json', 'w'), indent=1)
