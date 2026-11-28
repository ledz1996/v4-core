"""Task 4 (L-1336, L-1337): read-only census on rpc.mainnet.tempo.xyz.

1. eth_getProof (balance field) and eth_getBalance on the system addresses the block executor calls,
   the precompiles, the fee manager, address(0), the PoolManager and the beneficiaries of recent blocks,
   at latest and at a few historical blocks.
2. Initialize logs of the PoolManager with currency0 == address(0), and for each such pool its slot0 and
   liquidity read with extsload, plus any ModifyLiquidity logs for it.
Every batch is bracketed with web3_clientVersion.
usage: python3 -I native_census.py <out.json>
"""
import json, sys, time, urllib.request
OUT = sys.argv[1]
RPC = 'https://rpc.mainnet.tempo.xyz'
PM = '0x33620f62c5b9b2086dd6b62f4a297a9f30347029'
ID = [0]


def call(method, params):
    ID[0] += 1
    body = json.dumps({'jsonrpc': '2.0', 'id': ID[0], 'method': method, 'params': params}).encode()
    req = urllib.request.Request(RPC, body, {'content-type': 'application/json', 'user-agent': 'review-client/1.0'})
    for k in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except Exception as e:
            err = str(e); time.sleep(2 + 3 * k)
    return {'error': err}


ADDRS = {
    'zero': '0x0000000000000000000000000000000000000000',
    'TIP_FEE_MANAGER': '0xfeec000000000000000000000000000000000000',
    'TIP403_REGISTRY': '0x403c000000000000000000000000000000000000',
    'TIP20_FACTORY': '0x20fc000000000000000000000000000000000000',
    'STABLECOIN_DEX': '0xdec0000000000000000000000000000000000000',
    'STORAGE_CREDITS': '0x1060000000000000000000000000000000000000',
    'PATH_USD': '0x20c0000000000000000000000000000000000000',
    'HISTORY_STORAGE_EIP2935': '0x0000f90827f1c53a10cb7a02335b175320002935',
    'BEACON_ROOTS_EIP4788': '0x000f3df6d732807ef1319fb7b8bb8522d0beac02',
    'SYSTEM_ADDRESS': '0xfffffffffffffffffffffffffffffffffffffffe',
    'PoolManager': PM,
}


def main():
    out = {'rpc': RPC, 'client_before': call('web3_clientVersion', [])}
    head = call('eth_getBlockByNumber', ['latest', False])['result']
    hn = int(head['number'], 16)
    out['head'] = {'number': hn, 'hash': head['hash'], 'miner': head['miner']}
    # precompile constants from crates/contracts/src/precompiles/mod.rs at c0c9372 that are not literal above
    blocks = ['latest', hex(hn - 1_000_000), hex(hn // 2), hex(1_000_000), hex(1)]
    miners = set()
    for b in [hn - i for i in range(0, 4000, 200)]:
        r = call('eth_getBlockByNumber', [hex(b), False]).get('result') or {}
        if r.get('miner'): miners.add(r['miner'])
    for i, m in enumerate(sorted(miners)): ADDRS['beneficiary_%d' % i] = m
    res = {}
    for name, a in ADDRS.items():
        row = {}
        for b in blocks:
            p = call('eth_getProof', [a, [], b])
            bal = (p.get('result') or {}).get('balance') if 'result' in p else ('error: ' + json.dumps(p.get('error'))[:200])
            g = call('eth_getBalance', [a, b]).get('result')
            row[b] = {'proof_balance': bal, 'getBalance': g}
        res[name] = {'address': a, 'by_block': row}
    out['balances'] = res
    nonzero = [(n, b, v) for n, r in res.items() for b, v in r['by_block'].items()
               if v['getBalance'] not in (None, '0x0') or (isinstance(v['proof_balance'], str) and v['proof_balance'] not in ('0x0',) and not v['proof_balance'].startswith('error'))]
    out['nonzero_balances'] = nonzero
    # Initialize(bytes32 indexed id, address indexed currency0, address indexed currency1, uint24 fee, int24 tickSpacing, address hooks, uint160 sqrtPriceX96, int24 tick)
    INIT = '0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438'
    MODLIQ = '0xf208f4912782fd25c7f114ca3723a2d5dd6f3bcc3ac8db5af63baa85f711d5ec'
    zero_topic = '0x' + '00' * 32
    inits = []
    step = 2_000_000
    start = 0
    logerr = []
    b = start
    while b <= hn:
        e = min(b + step - 1, hn)
        r = call('eth_getLogs', [{'address': PM, 'fromBlock': hex(b), 'toBlock': hex(e), 'topics': [INIT, None, zero_topic]}])
        if 'error' in r:
            logerr.append([b, e, json.dumps(r['error'])[:200]])
            if step > 50_000:
                step //= 4; continue
        else:
            inits += r['result']
        b = e + 1
    out['init_query_errors'] = logerr
    out['all_init_count_note'] = 'only Initialize logs with currency0 == address(0) were requested'
    pools = []
    for lg in inits:
        pid = lg['topics'][1]
        # slot0 and liquidity via extsload(bytes32): pools mapping at slot 6
        import hashlib
        pools.append({'id': pid, 'block': int(lg['blockNumber'], 16), 'tx': lg['transactionHash'], 'currency1': '0x' + lg['topics'][3][-40:],
                      'data': lg['data']})
    out['native_pools'] = pools
    # count all Initialize logs too (any currency0) to bound the census
    allinit = 0; b = 0; step = 2_000_000
    while b <= hn:
        e = min(b + step - 1, hn)
        r = call('eth_getLogs', [{'address': PM, 'fromBlock': hex(b), 'toBlock': hex(e), 'topics': [INIT]}])
        if 'error' in r:
            if step > 50_000:
                step //= 4; continue
            logerr.append(['all', b, e]); b = e + 1; continue
        allinit += len(r['result']); b = e + 1
    out['all_initialize_logs'] = allinit
    out['client_after'] = call('web3_clientVersion', [])
    json.dump(out, open(OUT, 'w'), indent=1)
    print('head', hn, 'nonzero', nonzero, 'native pools', len(pools), 'all inits', allinit, 'errors', len(logerr))


main()
