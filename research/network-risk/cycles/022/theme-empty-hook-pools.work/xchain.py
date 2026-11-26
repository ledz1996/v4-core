"""EXTCODESIZE, nonce and code prefix of every hook address that is empty or delegated on some network, on all 21 networks. Read only."""
import json, glob, time
from ep import rpc, NETS
T = 'gateway.tenderly.co'
SU = {1: 'https://mainnet.' + T, 10: 'https://optimism.' + T, 8453: 'https://base.' + T, 130: 'https://unichain.' + T, 7777777: 'https://rpc.zora.energy/',
      480: 'https://worldchain-mainnet.g.alchemy.com/public', 57073: 'https://ink.' + T, 1868: 'https://soneium.' + T, 42220: 'https://celo.' + T,
      196: 'https://rpc.xlayer.tech', 42161: 'https://arbitrum.' + T, 4663: 'https://rpc.mainnet.chain.robinhood.com', 99901: 'https://rpc.elysium.kinetiq.xyz',
      137: 'https://polygon.' + T, 56: 'https://rpc-bsc.48.club', 43114: 'https://avalanche.' + T, 143: 'https://rpc.monad.xyz', 4326: 'https://mainnet.megaeth.com/rpc',
      4217: 'https://rpc.mainnet.tempo.xyz', 5042: 'https://arc.' + T, 999: 'https://rpc.purroofgroup.com'}
hooks = set()
for fn in glob.glob('raw/census_*.json'):
    for p in json.load(open(fn))['hookPools']: hooks.add(p['hook'])
hooks = sorted(hooks)
CODE = '0x5f5b3681101560145780353b8152602001600156' + '5b365ff3'; HELP = '0x00000000000000000000000000000000c0de5122'
out = {'hooks': hooks, 'chains': {}}
for cid, u in SU.items():
    r = {'url': u}
    try:
        r['clientStart'] = rpc(u, 'web3_clientVersion', []); b = hex(int(rpc(u, 'eth_blockNumber', []), 16) - 10); r['block'] = int(b, 16)
        x = rpc(u, 'eth_call', [{'to': HELP, 'data': '0x' + ''.join(h[2:].rjust(64, '0') for h in hooks), 'gas': hex(20_000_000)}, b, {HELP: {'code': CODE}}])
        r['size'] = {h: int(x[2 + 64 * i:66 + 64 * i], 16) for i, h in enumerate(hooks)}
        r['nonce'] = {}; r['codePrefix'] = {}
        for h in hooks:
            r['nonce'][h] = int(rpc(u, 'eth_getTransactionCount', [h, b]), 16)
            if r['size'][h]: r['codePrefix'][h] = rpc(u, 'eth_getCode', [h, b])[:50]
        r['clientEnd'] = rpc(u, 'web3_clientVersion', [])
    except Exception as e: r['error'] = str(e)[:200]
    out['chains'][cid] = r; print(cid, r.get('error') or sum(1 for v in r['size'].values() if v), flush=True)
json.dump(out, open('raw/xchain.json', 'w'), indent=1)
