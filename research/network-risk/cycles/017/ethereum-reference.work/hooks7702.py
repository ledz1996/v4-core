"""L-046: hooks of mainnet pools whose code is an EIP-7702 delegation indicator or empty, and their liquidity."""
import json, gzip, sys, urllib.request, time
SRC = '/home/user/v4-core/research/network-risk/cycles/005/theme-shared-hooks.work/raw/init_1.json.gz'
RPCS = ['https://eth.api.pocket.network', 'https://eth.nodely.dev', 'https://eth-mainnet.nodereal.io/v1/1659dfb40aa24bbb8153a677b98064d7', 'https://ethereum.public.blockpi.network/v1/rpc/public']
RPC = ','.join(RPCS)
CTR = [0]
out = sys.argv[1]
d = json.load(gzip.open(SRC)); rows = d['rows']
hooks = {}
for r in rows:
    h = r[6].lower()
    if h != '0x' + '0' * 40: hooks.setdefault(h, []).append(r)
print('pools', len(rows), 'with hook', sum(len(v) for v in hooks.values()), 'distinct hooks', len(hooks))
def batch(calls):
    body = json.dumps([{'jsonrpc': '2.0', 'id': i, 'method': m, 'params': p} for i, (m, p) in enumerate(calls)]).encode()
    for k in range(12):
        CTR[0] += 1; url = RPCS[CTR[0] % len(RPCS)]
        try:
            req = urllib.request.Request(url, body, {'content-type': 'application/json', 'user-agent': 'review-client'})
            res = json.load(urllib.request.urlopen(req, timeout=60))
            res = sorted(res, key=lambda x: x['id'])
            return [x.get('result') for x in res]
        except Exception as e:
            time.sleep(1 + k); err = e
    raise err
HB = 'latest'
blk = hex(int(batch([('eth_blockNumber', [])])[0], 16) - 5)
codes = {}
hs = list(hooks)
for i in range(0, len(hs), 20):
    res = batch([('eth_getCode', [h, blk]) for h in hs[i:i + 20]])
    for h, c in zip(hs[i:i + 20], res): codes[h] = c
deleg = {h: c for h, c in codes.items() if c and c.lower().startswith('0xef0100')}
empty = {h: c for h, c in codes.items() if c in ('0x', None, '')}
print('block', int(blk, 16), 'delegated', len(deleg), 'empty', len(empty))
# liquidity via StateView.getLiquidity(bytes32) 0xfa6793d5 and slot0 0xc815641c
SV = '0x7ffe42c4a5deea5b0fec41c94c136cf115597227'
res_rows = []
sel = [(h, r) for h in list(deleg) + list(empty) for r in hooks[h]]
for i in range(0, len(sel), 50):
    part = sel[i:i + 50]
    res = batch([('eth_call', [{'to': SV, 'data': '0xfa6793d5' + r[7][2:]}, blk]) for h, r in part])
    for (h, r), x in zip(part, res):
        res_rows.append({'hook': h, 'kind': 'delegated' if h in deleg else 'empty', 'delegate': ('0x' + codes[h][8:48]) if h in deleg else None,
                         'poolId': r[7], 'currency0': r[2], 'currency1': r[3], 'fee': r[4], 'tickSpacing': r[5], 'initBlock': r[0],
                         'liquidity': int(x, 16) if x else None})
json.dump({'block': int(blk, 16), 'rpc': RPC, 'pools': len(rows), 'distinctHooks': len(hooks), 'delegatedHooks': len(deleg), 'emptyHooks': len(empty),
           'pools7702': res_rows}, open(out, 'w'), indent=1)
live = [x for x in res_rows if x['liquidity']]
print('pools on such hooks', len(res_rows), 'with nonzero in-range liquidity', len(live))
for x in sorted(live, key=lambda x: -x['liquidity'])[:20]: print(x['kind'], x['hook'], x['delegate'], x['currency0'], x['currency1'], x['liquidity'])
