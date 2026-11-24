import json
from common import *
b = json.load(open('/home/user/v4-core/research/network-risk/build/PoolManager.json'))
rt = b['runtime']; rt = rt['object'] if isinstance(rt, dict) else rt
rt = bytes.fromhex(rt[2:] if rt.startswith('0x') else rt)
print('build', len(rt), b['immutableReferences'])
for cid in (143, 4326, 999, 1):
    urls = URLS.get(cid, [NETS[cid]['rpc']])
    c = bytes.fromhex(rpc(urls, 'eth_getCode', [NETS[cid]['poolManager'], 'latest'])[2:])
    diff = [i for i in range(min(len(c), len(rt))) if c[i] != rt[i]]
    print(cid, len(c), 'diffbytes', len(diff), diff[:5], diff[-5:] if diff else '')
