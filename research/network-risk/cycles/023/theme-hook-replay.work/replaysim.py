"""Read-only check of what a replayed hook does on a network where its address is empty today. The runtime and the storage
that the replayed constructor writes (from ctor.py) are placed at the hook address by eth_call state override, and the
network's own PoolManager calls beforeSwap and afterSwap on it with the key of a pool that exists there. The call from the
PoolManager of the network where the hook has code is run as a control. usage: replaysim.py <chainId> <hook> <poolKeyJson> [ctrlPM]"""
import sys, json
sys.path.insert(0, '.')
from rpcu import rpc
from kk import keccak
X = json.load(open('/home/user/v4-core/research/network-risk/cycles/022/theme-empty-hook-pools.work/raw/xchain.json'))
NETS = {str(n['chainId']): n for n in json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))['networks']}
c, h, key = sys.argv[1], sys.argv[2].lower(), json.loads(sys.argv[3]); ctrl = sys.argv[4] if len(sys.argv) > 4 else None
u = {'56': 'https://bsc-dataseed1.bnbchain.org', '42161': 'https://arb1.arbitrum.io/rpc', '10': 'https://mainnet.optimism.io', '137': 'https://polygon-bor-rpc.publicnode.com'}.get(c, X['chains'][c]['url'])
code = '0x' + open('raw/ctor_runtime_%s.hex' % h[:10]).read()
stor = json.load(open('raw/ctor_%s.json' % h[:10]))['storage']
ov = {h: {'code': code, 'stateDiff': {'0x' + int(k, 16).to_bytes(32, 'big').hex(): '0x' + int(v, 16).to_bytes(32, 'big').hex() for k, v in stor.items()}}}
def w(x): return int(x).to_bytes(32, 'big', signed=int(x) < 0) if int(x) >= 0 else (int(x) % (1 << 256)).to_bytes(32, 'big')
def a(x): return bytes(12) + bytes.fromhex(x[2:])
sel = lambda s: keccak(s.encode())[:4]
K = a(key['currency0']) + a(key['currency1']) + w(key['fee']) + w(key['tickSpacing'] % (1 << 256)) + a(h)
P = w(1) + w(-1000) + w(4295128740)
bs = sel('beforeSwap(address,(address,address,uint24,int24,address),(bool,int256,uint160),bytes)') + a('0x' + '11' * 20) + K + P + w(32 * 10) + w(0)
asw = sel('afterSwap(address,(address,address,uint24,int24,address),(bool,int256,uint160),int256,bytes)') + a('0x' + '11' * 20) + K + P + w(0) + w(32 * 11) + w(0)
out = {'chainId': c, 'url': u, 'client': [rpc(u, 'web3_clientVersion', [])], 'hook': h, 'key': key, 'override': {'codeLen': (len(code) - 2) // 2, 'storage': stor}, 'calls': []}
blk = rpc(u, 'eth_blockNumber', []); out['block'] = int(blk, 16)
froms = [('localPM', NETS[c]['poolManager'])] + ([('ctrlPM', ctrl)] if ctrl else [])
for name, data in (('beforeSwap', bs), ('afterSwap', asw)):
    for fn, f in froms:
        try: r = {'ok': True, 'ret': rpc(u, 'eth_call', [{'from': f, 'to': h, 'data': '0x' + data.hex(), 'gas': hex(5_000_000)}, blk, ov], tries=2)}
        except Exception as e: r = {'ok': False, 'err': str(e)[:400]}
        r.update({'fn': name, 'from': fn + ' ' + f}); out['calls'].append(r); print(r)
out['client'].append(rpc(u, 'web3_clientVersion', []))
json.dump(out, open('raw/replaysim_%s_%s.json' % (h[:10], c), 'w'), indent=1)
