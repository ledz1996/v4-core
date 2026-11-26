"""Endpoint table for this unit and a probe: web3_clientVersion, head, eth_getLogs of Initialize over the last 500 blocks. Read only."""
import json, sys, time, ssl, urllib.request, urllib.error, os
CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt') if os.path.exists('/root/.ccr/ca-bundle.crt') else None
T = 'gateway.tenderly.co'
EP = {1: ['https://mainnet.' + T, 'https://ethereum-rpc.publicnode.com'], 10: ['https://optimism.' + T, 'https://mainnet.optimism.io'],
 8453: ['https://base.' + T, 'https://mainnet.base.org'], 130: ['https://unichain.' + T, 'https://mainnet.unichain.org'],
 7777777: ['https://rpc.zora.energy/'], 480: ['https://worldchain.' + T, 'https://worldchain-mainnet.g.alchemy.com/public'],
 57073: ['https://ink.' + T, 'https://rpc-gel.inkonchain.com'], 1868: ['https://soneium.' + T, 'https://rpc.soneium.org'],
 42220: ['https://celo.' + T, 'https://forno.celo.org'], 196: ['https://xlayer-mainnet.rpc.sentio.xyz', 'https://rpc.xlayer.tech'],
 42161: ['https://arbitrum.' + T, 'https://arb1.arbitrum.io/rpc'], 4663: ['https://rpc.mainnet.chain.robinhood.com'],
 99901: ['https://rpc.elysium.kinetiq.xyz'], 137: ['https://polygon.' + T, 'https://polygon-bor-rpc.publicnode.com'],
 56: ['https://bsc.' + T, 'https://rpc-bsc.48.club', 'https://bsc-dataseed1.bnbchain.org'], 43114: ['https://avalanche.' + T, 'https://api.avax.network/ext/bc/C/rpc'],
 143: ['https://rpc2.monad.xyz', 'https://rpc.monad.xyz'], 4326: ['https://mainnet.megaeth.com/rpc'], 4217: ['https://rpc.mainnet.tempo.xyz'],
 5042: ['https://arc.' + T, 'https://rpc.mainnet.arc.io'], 999: ['https://rpc.purroofgroup.com', 'https://rpc.hyperliquid.xyz/evm']}
INIT = '0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438'
NETS = {n['chainId']: n for n in json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))['networks']}
def post(u, payload, timeout=90):
    req = urllib.request.Request(u, json.dumps(payload).encode(), {'content-type': 'application/json', 'user-agent': 'rpc-client'})
    return json.loads(urllib.request.urlopen(req, timeout=timeout, context=CTX).read())
def rpc(u, m, p, tries=5, timeout=90):
    last = None
    for k in range(tries):
        try:
            r = post(u, {'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}, timeout)
            if 'error' in r: raise RuntimeError(json.dumps(r['error'])[:2000])
            return r['result']
        except urllib.error.HTTPError as e:
            last = RuntimeError('HTTP %d %s' % (e.code, e.read()[:200].decode(errors='replace')))
            if e.code in (403,): raise last
        except RuntimeError as e:
            last = e
            if any(x in str(e).lower() for x in ('range', 'too many', 'exceed', 'too large', 'limit')) and 'rate' not in str(e).lower(): raise
        except Exception as e: last = e
        time.sleep(1.5 * (k + 1))
    raise last
def batch(u, calls, tries=6, timeout=120):
    last = None
    for k in range(tries):
        try:
            r = post(u, [{'jsonrpc': '2.0', 'id': i, 'method': m, 'params': p} for i, (m, p) in enumerate(calls)], timeout)
            if isinstance(r, dict): raise RuntimeError('batch refused ' + json.dumps(r)[:200])
            out = [None] * len(calls)
            for x in r: out[x['id']] = x['result'] if 'result' in x else {'error': x.get('error')}
            if any(isinstance(o, dict) and 'error' in o and 'rate' in json.dumps(o).lower() for o in out): raise RuntimeError('rate ' + json.dumps(out[0])[:100])
            return out
        except urllib.error.HTTPError as e: last = RuntimeError('HTTP %d' % e.code)
        except Exception as e: last = e
        time.sleep(2 * (k + 1))
    raise last
if __name__ == '__main__':
    out = {}
    for cid, urls in EP.items():
        pm = NETS[cid]['poolManager']
        for u in urls:
            r = {'t': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
            try:
                r['client'] = rpc(u, 'web3_clientVersion', [], tries=2, timeout=30)
                h = int(rpc(u, 'eth_blockNumber', [], tries=2, timeout=30), 16); r['head'] = h
                L = rpc(u, 'eth_getLogs', [{'address': pm, 'topics': [INIT], 'fromBlock': hex(h - 500), 'toBlock': hex(h - 10)}], tries=2, timeout=60)
                r['init500'] = len(L)
            except Exception as e: r['error'] = str(e)[:200]
            out['%d %s' % (cid, u)] = r; print(cid, u, r, flush=True)
    json.dump(out, open('raw/probe.json', 'w'), indent=1)
