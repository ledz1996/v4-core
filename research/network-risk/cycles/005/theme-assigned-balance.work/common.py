# Shared helpers for the assigned-balance sweep. Read-only JSON-RPC only.
import json, os, sys, gzip, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lib import post, rpc, batch, sel, u256, adr, NETS
from config import CFG
R4 = os.path.join(HERE, '..', '..', '004', 'theme-balance-reconcile.work', 'raw')
RAW = os.path.join(HERE, 'raw')
STUB = '0x00000000000000000000000000000000000a55e7'
# returns EXTCODEHASH of every 32 byte word of calldata
CODEHASH_STUB = '0x60005b8036146014578035' + '3f' + '815260200160025' + '65b366000f3'
def net(cid): return [n for n in NETS if n['chainId'] == cid][0]
def universe(cid):
    d = json.load(gzip.open(os.path.join(R4, 'reconcile_%d.json.gz' % cid)))
    rows = d['rows'] if 'rows' in d else d['tokens']
    return d, rows
def urls(cid):
    u = [net(cid)['rpc']] + CFG[cid]['state']
    out = []
    for x in u:
        if x not in out: out.append(x)
    return out
def call_override(url, to, data, override, block='latest', frm=None, gas=None, timeout=60):
    tx = {'to': to, 'data': data}
    if frm: tx['from'] = frm
    if gas: tx['gas'] = hex(gas)
    return rpc(url, 'eth_call', [tx, block, override], timeout=timeout)
EXTRA = {1: ['https://eth.drpc.org', 'https://eth-mainnet.public.blastapi.io'], 10: ['https://optimism-rpc.publicnode.com', 'https://optimism.drpc.org'],
         8453: ['https://base-rpc.publicnode.com', 'https://base.drpc.org', 'https://base-mainnet.public.blastapi.io'], 130: ['https://unichain-rpc.publicnode.com', 'https://unichain.drpc.org'],
         42161: ['https://arbitrum-one-rpc.publicnode.com', 'https://arbitrum.drpc.org'], 137: ['https://polygon-bor-rpc.publicnode.com'], 56: ['https://bsc-rpc.publicnode.com', 'https://rpc-bsc.48.club'],
         43114: ['https://avalanche-c-chain-rpc.publicnode.com'], 57073: ['https://rpc-qnd.inkonchain.com', 'https://ink.drpc.org'], 1868: ['https://soneium-rpc.publicnode.com', 'https://soneium.drpc.org'],
         42220: ['https://celo-rpc.publicnode.com', 'https://celo.drpc.org'], 143: ['https://rpc-mainnet.monadinfra.com'], 4663: ['https://robinhood-rpc.publicnode.com'], 5042: ['https://arc.drpc.org'], 196: ['https://xlayer.drpc.org']}
def urls2(cid):
    out = []
    for x in [net(cid)['rpc']] + EXTRA.get(cid, []) + CFG[cid]['state']:
        if x not in out and 'tenderly' not in x and x != 'https://rpc.xlayer.tech': out.append(x)
    return out
def ecall(cid, to, data, override=None, frm=None, gas=None, block='latest', tries=6, timeout=90, rot=0):
    us = urls2(cid); last = None
    for k in range(tries):
        u = us[(rot + k) % len(us)]
        try:
            tx = {'to': to, 'data': data}
            if frm: tx['from'] = frm
            if gas: tx['gas'] = hex(gas)
            p = [tx, block] + ([override] if override else [])
            j = post(u, {'jsonrpc': '2.0', 'id': 1, 'method': 'eth_call', 'params': p}, timeout=timeout, tries=1)
            if 'error' in j:
                m = json.dumps(j['error'])
                if any(s in m.lower() for s in ('rate', 'capacity', 'limit exceeded', 'too many', 'timeout', 'upgrade', 'busy')):
                    last = m[:150]; time.sleep(0.7 * (k + 1)); continue
                return {'error': j['error']}
            return j['result']
        except Exception as e:
            last = str(e)[:150]; time.sleep(0.7 * (k + 1))
    return {'error': {'message': 'transport: ' + str(last)}}
