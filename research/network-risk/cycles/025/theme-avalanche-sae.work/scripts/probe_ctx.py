"""Task 2 probe for theme-avalanche-sae (cycle 25). Read-only.
eth_call of a creation payload (no 'to') that returns BASEFEE, NUMBER, TIMESTAMP, COINBASE, PREVRANDAO, BLOBBASEFEE,
GASPRICE and BLOCKHASH(NUMBER-1) at an explicit block number, then the header of that block and the next one, and the
receipts of the block's transactions (effectiveGasPrice), to compare what the EVM sees with what the header says.
The payload only reads the block context and returns 256 bytes; it is a read, it sends nothing.
usage: probe_ctx.py <out.json> [n_blocks]"""
import json, sys, time, ssl, urllib.request
CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
URLS = ['https://api.avax.network/ext/bc/C/rpc', 'https://avax.api.pocket.network']
CODE = '0x' + '485f52' + '43602052' + '42604052' + '41606052' + '44608052' + '4a60a052' + '3a60c052' + '60014303' + '4060e052' + '6101005ff3'
def rpc(u, m, p):
    rq = urllib.request.Request(u, json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(), {'content-type': 'application/json', 'user-agent': 'rpc-client'})
    try:
        r = json.loads(urllib.request.urlopen(rq, timeout=60, context=CTX).read())
    except Exception as e:
        return {'exc': str(e)[:200]}
    return r.get('result', {'error': r.get('error')})
names = ['BASEFEE', 'NUMBER', 'TIMESTAMP', 'COINBASE', 'PREVRANDAO', 'BLOBBASEFEE', 'GASPRICE', 'BLOCKHASH(NUMBER-1)']
out = []
nb = int(sys.argv[2]) if len(sys.argv) > 2 else 6
for u in URLS:
    cb = rpc(u, 'web3_clientVersion', [])
    head = rpc(u, 'eth_getBlockByNumber', ['latest', False])
    n0 = int(head['number'], 16)
    for n in range(n0 - nb, n0):
        h = rpc(u, 'eth_getBlockByNumber', [hex(n), False]); hp = rpc(u, 'eth_getBlockByNumber', [hex(n - 1), False])
        for gp in (None, '0x0', hex(10 ** 10)):
            call = {'data': CODE, 'gas': '0x100000'}
            if gp: call['gasPrice'] = gp
            r = rpc(u, 'eth_call', [call, hex(n)])
            vals = {}
            if isinstance(r, str):
                b = bytes.fromhex(r[2:])
                for i, k in enumerate(names): vals[k] = '0x' + b[32 * i:32 * i + 32].hex().lstrip('0') if b[32 * i:32 * i + 32].strip(b'\0') else '0x0'
            else:
                vals = r
            rec = {'url': u, 'block': n, 'gasPriceArg': gp, 'evm': vals,
                   'header': {k: h.get(k) for k in ('hash', 'baseFeePerGas', 'timestamp', 'miner', 'mixHash', 'stateRoot', 'parentHash', 'excessBlobGas', 'blobGasUsed')},
                   'parentHash_from_header_of_n_minus_1': hp.get('hash')}
            if gp is None:
                rc = []
                for t in h.get('transactions', [])[:5]:
                    x = rpc(u, 'eth_getTransactionReceipt', [t]); tx = rpc(u, 'eth_getTransactionByHash', [t])
                    rc.append({'tx': t, 'effectiveGasPrice': x.get('effectiveGasPrice'), 'maxFeePerGas': tx.get('maxFeePerGas'), 'maxPriorityFeePerGas': tx.get('maxPriorityFeePerGas'), 'gasPrice': tx.get('gasPrice'), 'type': tx.get('type'), 'gasUsed': x.get('gasUsed'), 'status': x.get('status')})
                rec['receipts'] = rc
            out.append(rec)
            print(u, n, gp, vals.get('BASEFEE') if isinstance(vals, dict) else vals, h.get('baseFeePerGas'), flush=True)
    out.append({'url': u, 'clientBefore': cb, 'clientAfter': rpc(u, 'web3_clientVersion', [])})
json.dump(out, open(sys.argv[1], 'w'), indent=1)
