"""L-821: ModifyLiquidity events of the empty-hook pools that still hold liquidity. Read-only eth_getLogs."""
import sys, json, time
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import rpc, keccak
U = 'https://ethereum.public.blockpi.network/v1/rpc/public'
PM = '0x000000000004444c5dc75cB358380D2e3dE08A90'
T0 = '0x' + keccak(b'ModifyLiquidity(bytes32,address,int24,int24,int256,bytes32)').hex()
IDS = ['0x462175dbedc82a59909309d8d93c8ff5283fc3ce41e9dcbea28aea89709ab870', '0xf6aaf9bdb04a91fb3498859dbdace2c3683b64a17d5e2c03b403f3def39cebd5']
b, head = 25072940, int(rpc(U, 'eth_blockNumber', []), 16); logs = []
while b <= head:
    e = min(b + 4999, head)
    for k in range(6):
        try: logs += rpc(U, 'eth_getLogs', [{'address': PM, 'topics': [T0, IDS], 'fromBlock': hex(b), 'toBlock': hex(e)}]); break
        except Exception: time.sleep(2 * (k + 1))
    else: raise SystemExit('fail %d' % b)
    b = e + 1
M = 1 << 256
out = []
for l in logs:
    d = bytes.fromhex(l['data'][2:])
    w = [int.from_bytes(d[i:i + 32], 'big') for i in range(0, len(d), 32)]
    s = lambda x: x - M if x >= 1 << 255 else x
    out.append({'pool': l['topics'][1], 'sender': '0x' + l['topics'][2][-40:], 'tickLower': s(w[0]), 'tickUpper': s(w[1]), 'liquidityDelta': s(w[2]), 'salt': hex(w[3]), 'block': int(l['blockNumber'], 16), 'tx': l['transactionHash']})
json.dump({'from': 25072940, 'to': head, 'events': out}, open('l821logs.json', 'w'), indent=1)
for o in out: print(o)
