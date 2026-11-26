"""On all 21 networks: eth_call from the PoolManager address, with beforeRemoveLiquidity calldata, to (a) three addresses drawn with
random.Random('theme-empty-hook-pools-022'), (b) the low hook address 0x...20 and 0x...dead0030 used by live pools, and (c) every
hook address that is empty on that network per raw/census_<cid>.json. Expected on Ethereum: success with empty return data. Read only."""
import json, random, os, time
from ep import rpc, NETS
from xchain_urls import SU
rnd = random.Random('theme-empty-hook-pools-022')
R = ['0x' + '%040x' % rnd.getrandbits(160) for _ in range(3)]
FIX = ['0x0000000000000000000000000000000000000020', '0x00000000000000000000000000000000dead0030']
cd = '0x21d0ee70' + '00' * 32 * 10 + '%064x' % 352 + '00' * 32
out = {'seed': 'theme-empty-hook-pools-022', 'random': R, 'chains': {}}
for cid, u in SU.items():
    pm = NETS[cid]['poolManager']; targets = R + FIX
    fn = 'raw/census_%d.json' % cid
    if os.path.exists(fn): targets += sorted({p['hook'] for p in json.load(open(fn))['hookPools'] if p['kind'] == 'empty'} - set(targets))
    r = {'url': u, 'clientStart': rpc(u, 'web3_clientVersion', []), 'block': int(rpc(u, 'eth_blockNumber', []), 16) - 10, 'calls': {}}
    for t in targets:
        try: x = rpc(u, 'eth_call', [{'from': pm, 'to': t, 'data': cd, 'gas': hex(1_000_000)}, hex(r['block'])], tries=3); r['calls'][t] = {'ok': True, 'ret': x}
        except Exception as e: r['calls'][t] = {'ok': False, 'err': str(e)[:200]}
    r['clientEnd'] = rpc(u, 'web3_clientVersion', [])
    bad = {t: v for t, v in r['calls'].items() if not (v['ok'] and v['ret'] == '0x')}
    out['chains'][cid] = r; print(cid, len(targets), 'not empty-success:', bad, flush=True)
json.dump(out, open('raw/emptycall.json', 'w'), indent=1)
