"""Base: list pool ids of PoolManager Swap/ModifyLiquidity/Donate logs in one block window that are in neither
cycles/006 raw/base_init.bin nor raw/initx_8453.json, and look each up by an Initialize log query filtered on topic1
from the deployment block. Read-only eth_getLogs. usage: unknownpools.py <from> <to>"""
import sys, os, json, struct
sys.path.insert(0, '../../006/theme-currency-lists.work')
from lib import rpc
U = 'https://base.gateway.tenderly.co'; pm = '0x498581ff718922c3f8e6a244956af099b2652b2b'
INIT = '0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438'
EV = ['0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f', '0xf208f4912782fd25c7f114ca3723a2d5dd6f3bcc3ac8db5af63baa85f711d5ec', '0x29ef05caaff9404b7cb6d1c0e9bbae9eaa7ab2541feba1a9c4248594c08156cb']
a, b = int(sys.argv[1]), int(sys.argv[2]); ids = set()
for x in range(a, b + 1, 1000):
    for l in rpc(U, 'eth_getLogs', [{'address': pm, 'topics': [EV], 'fromBlock': hex(x), 'toBlock': hex(min(b, x + 999))}]): ids.add(l['topics'][1])
known = set(json.load(open('raw/initx_8453.json'))['rows'])
want = {bytes.fromhex(i[2:]) for i in ids}; found = set()
with open('../../006/theme-currency-lists.work/raw/base_init.bin', 'rb') as f:
    while True:
        h = f.read(8)
        if len(h) < 8: break
        s, n = struct.unpack('>II', h); body = f.read(102 * n)
        for k in range(n):
            r = body[102 * k: 102 * k + 102]
            if r[4:36] in want: found.add('0x' + r[4:36].hex())
unk = sorted(i for i in ids if i not in known and i not in found)
print('ids', len(ids), 'unknown', len(unk))
res = {}
for i in unk[:5]:
    L = []
    try: L = rpc(U, 'eth_getLogs', [{'address': pm, 'topics': [INIT, i], 'fromBlock': hex(25350988), 'toBlock': 'latest'}])
    except Exception as e: L = str(e)[:200]
    res[i] = L if isinstance(L, str) else [(int(l['blockNumber'], 16), l['topics'][2][-40:], l['topics'][3][-40:]) for l in L]
    print(i, res[i])
json.dump(dict(window=[a, b], ids=len(ids), unknown=unk, lookups=res), open('raw/unknownpools_8453.json', 'w'), indent=1)
