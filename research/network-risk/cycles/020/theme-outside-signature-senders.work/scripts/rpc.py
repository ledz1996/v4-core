"""Read-only JSON-RPC helper. Logs every call and result to raw/rpc.log."""
import json, subprocess, os, time
WORK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(WORK, 'raw', 'rpc.log')
ETH = 'https://ethereum-rpc.publicnode.com'
HYPER = 'https://rpc.hyperliquid.xyz/evm'
ALLOWED = {'eth_call', 'eth_getCode', 'eth_getStorageAt', 'eth_getBlockByNumber', 'eth_blockNumber',
           'eth_getTransactionCount', 'eth_getLogs', 'web3_clientVersion', 'eth_chainId', 'eth_getBalance',
           'eth_getTransactionByHash', 'eth_getTransactionReceipt', 'debug_traceCall', 'eth_getSystemTxsByBlockNumber'}

FALLBACK = {ETH: [ETH, 'https://eth.drpc.org', 'https://rpc.flashbots.net', 'https://cloudflare-eth.com'],
            HYPER: [HYPER, 'https://rpc.hypurrscan.io', 'https://hyperliquid.drpc.org']}
REFUSALS = os.path.join(WORK, 'raw', 'refusals.log')

def rpc(url, method, params):
    for u in FALLBACK.get(url, [url]):
        for k in range(3):
            r = rpc1(u, method, params)
            if isinstance(r, dict) and ('raw' in r or isinstance(r.get('error'), dict) and (r['error'].get('code') in (-32005, 429, -32001, -32090) or 'limit' in str(r['error']).lower())):
                with open(REFUSALS, 'a') as f: f.write(json.dumps({'t': int(time.time()), 'url': u, 'method': method, 'resp': str(r)[:200]}) + '\n')
                time.sleep(3 * (k + 1)); continue
            return r
    return r

def rpc1(url, method, params):
    assert method in ALLOWED, method
    body = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params})
    for attempt in range(3):
        out = subprocess.run(['curl', '-s', '--max-time', '60', '-X', 'POST', '-H', 'content-type: application/json',
                              '--data', body, url], capture_output=True, text=True).stdout
        try:
            r = json.loads(out)
            break
        except Exception:
            r = {'raw': out[:500]}
            time.sleep(2)
    with open(LOG, 'a') as f:
        f.write(json.dumps({'t': int(time.time()), 'url': url, 'method': method, 'params': params,
                            'result': r.get('result', r.get('error', r))})[:20000] + '\n')
    return r.get('result', r)

def call(url, to, data, block='latest', frm=None):
    o = {'to': to, 'data': data}
    if frm: o['from'] = frm
    return rpc(url, 'eth_call', [o, block])

def addr(word):
    return '0x' + word[-40:] if isinstance(word, str) and word.startswith('0x') and len(word) >= 42 else word
