import sys, json, os
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import rpc, keccak
MOD = '0x' + keccak(b'ModifyLiquidity(bytes32,address,int24,int24,int256,bytes32)').hex()
nets = {n['chainId']: n for n in json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))['networks']}
URLS = {999: ['https://rpc.hyperliquid.xyz/evm', 'https://rpc.hyperlend.finance', 'https://hyperliquid.drpc.org', 'https://rpc.hypurrscan.io'],}
for cid in map(int, sys.argv[1:]):
    n = nets[cid]; pm = n['poolManager']
    for url in URLS.get(cid, [n['rpc']]):
        out = {'url': url}
        try:
            head = int(rpc(url, 'eth_blockNumber', []), 16); out['head'] = head
            for span in (100, 1000, 10000):
                try:
                    L = rpc(url, 'eth_getLogs', [{'address': pm, 'fromBlock': hex(head - span), 'toBlock': hex(head), 'topics': [MOD]}], timeout=60)
                    out[f'logs{span}'] = len(L)
                except Exception as e: out[f'logs{span}'] = 'ERR ' + str(e)[:80]
            for back in (10, 1000, 100000, 1000000):
                try:
                    v = rpc(url, 'eth_getStorageAt', [pm, '0x0', hex(head - back)], timeout=30); out[f'stor-{back}'] = v[-8:]
                except Exception as e: out[f'stor-{back}'] = 'ERR ' + str(e)[:80]
                try:
                    v = rpc(url, 'eth_getBalance', [pm, hex(head - back)], timeout=30); out[f'bal-{back}'] = int(v, 16)
                except Exception as e: out[f'bal-{back}'] = 'ERR ' + str(e)[:80]
            b = rpc(url, 'eth_getBlockByNumber', [hex(head - 5), False]); 
            if b['transactions']:
                for m in ('debug_traceTransaction',):
                    try:
                        rpc(url, m, [b['transactions'][0], {'tracer': 'callTracer'}], timeout=30); out[m] = 'ok'
                    except Exception as e: out[m] = 'ERR ' + str(e)[:80]
        except Exception as e: out['err'] = str(e)[:120]
        print(cid, json.dumps(out), flush=True)
