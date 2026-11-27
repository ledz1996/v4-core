"""Cycle 37 theme-native-face-inflows. Read-only survey on all 21 networks of the OP Stack legacy ETH token address
0xDeadDeAddeAddEAddeadDEaDDEAdDeaDDeAD0000: eth_getCode, balanceOf(PoolManager) by eth_call, eth_getBalance(PoolManager),
and PoolManager.sync(legacy) by eth_call (sync has no lock check, so a plain eth_call exercises it).
Bracketed with web3_clientVersion. No randomness, no seed. usage: python3 -I legacy.py <out.json>"""
import sys, json
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/032/theme-unpublished-builds-live-rollback.work/scripts')
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from rpcu import rpc, version
from evm import keccak
L = '0xdeaddeaddeaddeaddeaddeaddeaddeaddead0000'
def sel(s): return keccak(s.encode())[:4].hex()
nets = json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))['networks']
out = {}
for n in nets:
    cid, url, pm = n['chainId'], n['rpc'], n['poolManager'].lower()
    if cid == 143: url = 'https://rpc1.monad.xyz'
    r = {'name': n['name'], 'url': url, 'pm': pm, 'before': version(url, cid)}
    b = rpc(url, 'eth_getBlockByNumber', ['latest', False]); bn = (b.get('result') or {}).get('number', 'latest'); r['block'] = bn
    r['code'] = rpc(url, 'eth_getCode', [L, bn])
    r['balanceOfPM'] = rpc(url, 'eth_call', [{'to': L, 'data': '0x' + sel('balanceOf(address)') + pm[2:].rjust(64, '0')}, bn])
    r['pmNative'] = rpc(url, 'eth_getBalance', [pm, bn])
    r['sync'] = rpc(url, 'eth_call', [{'from': '0x00000000000000000000000000000000000a11ce', 'to': pm, 'data': '0x' + sel('sync(address)') + L[2:].rjust(64, '0')}, bn])
    r['after'] = version(url, cid)
    out[cid] = r
    c = (r['code'].get('result') or '')
    print(cid, n['name'], 'codelen', (len(c) - 2) // 2 if c else r['code'], 'bal', str(r['balanceOfPM'].get('result', r['balanceOfPM']))[:70], 'native', r['pmNative'].get('result'), 'sync', str(r['sync'])[:160], flush=True)
json.dump(out, open(sys.argv[1], 'w'), indent=1)
