# Print a transaction's value, receipt logs in short form, and a call trace when the endpoint serves one.
import sys, json
from lib import *
from sample_receipts import RCPT, digest
NAMES = {'0x1b3d7edb': '6909Transfer', '0xddf252ad': 'Transfer', '0x40e9cecb': 'Swap', '0xf208f491': 'ModifyLiquidity', '0x29ef05ca': 'Donate', '0xe1fffcc4': 'Deposit', '0x7fcf532c': 'Withdrawal', '0xdd466e67': 'Initialize'}
SEL = {'0x48c89491': 'unlock', '0x91dd7346': 'unlockCallback', '0xa5841194': 'sync', '0x11da60b4': 'settle', '0x80f0b44c': 'settleFor', '0x0b0d9c09': 'take', '0x156e29f6': 'mint', '0xf5298aca': 'burn', '0xa9059cbb': 'transfer', '0x70a08231': 'balanceOf', '0x23b872dd': 'transferFrom', '0xaf14052c': 'rebase', '0x80814588': 'clear', '0xf3cd914c': 'swap', '0x5a6bcfda': 'modifyLiquidity', '0x234266d7': 'donate', '0x8161b874': 'collectProtocolFees'}
TRACE = {1: ['https://eth.drpc.org', 'https://ethereum-rpc.publicnode.com'], 137: ['https://polygon.drpc.org'], 10: ['https://optimism.drpc.org', 'https://mainnet.optimism.io'], 8453: ['https://base.drpc.org'], 42161: ['https://arbitrum.drpc.org', 'https://arb1.arbitrum.io/rpc'], 130: ['https://unichain.drpc.org', 'https://mainnet.unichain.org'], 56: ['https://bsc-mainnet.nodereal.io/v1/64a9df0874fb4a93b9d0a3849de012d3', 'https://bsc.drpc.org'], 43114: ['https://avalanche.drpc.org', 'https://api.avax.network/ext/bc/C/rpc'], 57073: ['https://ink.drpc.org', 'https://rpc-gel.inkonchain.com'], 5042: ['https://arc.drpc.org', 'https://rpc.mainnet.arc.io'], 4663: ['https://robinhood.drpc.org', 'https://rpc.mainnet.chain.robinhood.com'], 99901: ['https://rpc.elysium.kinetiq.xyz'], 143: ['https://monad.drpc.org', 'https://rpc.monad.xyz'], 42220: ['https://celo.drpc.org', 'https://forno.celo.org'], 999: ['https://hyperliquid.drpc.org', 'https://rpc.purroofgroup.com'], 480: ['https://worldchain.drpc.org'], 196: ['https://xlayer.drpc.org', 'https://rpc.xlayer.tech'], 4326: ['https://mainnet.megaeth.com/rpc'], 4217: ['https://rpc.mainnet.tempo.xyz']}
def trace(cid, tx):
    for u in TRACE.get(cid, []) + RCPT[cid]:
        try:
            r = rpc(u, 'debug_traceTransaction', [tx, {'tracer': 'callTracer'}], timeout=90, tries=2)
            if r: return u, r
        except Exception as e: last = str(e)[:150]
    b = SCOUT.get(cid)
    if b:
        try:
            import requests
            j = requests.get(b + '/api/v2/transactions/' + tx + '/raw-trace', timeout=40, headers={'user-agent': 'curl/8'}).json()
            if isinstance(j, list) and j: j = j[0] if 'type' in j[0] else {'type': 'LIST', 'calls': j}
            if isinstance(j, dict) and j.get('type'): return b + '/api/v2/transactions/<tx>/raw-trace', j
        except Exception as e: pass
    return None, None
SCOUT = {57073: 'https://explorer.inkonchain.com', 10: 'https://optimism.blockscout.com', 130: 'https://unichain.blockscout.com', 1868: 'https://soneium.blockscout.com', 42220: 'https://celo.blockscout.com', 480: 'https://worldchain-mainnet.explorer.alchemy.com', 4326: 'https://megaeth.blockscout.com', 1: 'https://eth.blockscout.com', 42161: 'https://arbitrum.blockscout.com', 8453: 'https://base.blockscout.com', 137: 'https://polygon.blockscout.com'}
def walk(c, depth=0, out=None, maxd=7):
    out = out if out is not None else []
    inp = c.get('input', '0x'); s = inp[:10]
    out.append('%s%s %s -> %s %s%s val=%s%s' % ('  ' * depth, c.get('type'), c.get('from', '')[:12], c.get('to', ''), SEL.get(s, s), ('(' + inp[10:10 + 64 * 3] + ')') if len(inp) > 10 and len(inp) < 10 + 64 * 4 else '', int(c.get('value', '0x0'), 16) if c.get('value') else 0, ' ERR=' + c['error'] if c.get('error') else ''))
    if depth < maxd:
        for x in c.get('calls', []) or []: walk(x, depth + 1, out, maxd)
    return out
def show(cid, tx, do_trace=True, maxlogs=60, save=True, maxd=7, maxlines=150):
    u = RCPT[cid][0]; pm = net(cid)['poolManager'].lower()
    t = rpc(u, 'eth_getTransactionByHash', [tx]); r = rpc(u, 'eth_getTransactionReceipt', [tx])
    print('chain', cid, 'tx', tx, 'block', int(r['blockNumber'], 16), 'index', int(r['transactionIndex'], 16), 'from', t['from'], 'to', t['to'], 'value', int(t['value'], 16), 'status', r['status'], 'gasUsed', int(r['gasUsed'], 16), 'input', t['input'][:10], 'type', t.get('type'))
    for l in r['logs'][:maxlogs]:
        tp = l['topics']; nm = NAMES.get(tp[0][:10], tp[0][:10]) if tp else 'anon'
        print('   log', l['address'], nm, [x[-40:] if x[:26] == '0x' + '0' * 24 else x[:18] for x in tp[1:]], l['data'][:2 + 64 * 2] if len(l['data']) > 66 else int(l['data'], 16) if len(l['data']) > 2 else '')
    if do_trace:
        tu, tr = trace(cid, tx)
        if tr:
            lines = walk(tr, maxd=maxd)
            print('  trace from', tu, 'lines', len(lines))
            for x in lines[:maxlines]: print('   ', x[:330])
            if save: json.dump({'chainId': cid, 'tx': tx, 'traceUrl': tu, 'trace': tr}, open('raw/trace_%d_%s.json' % (cid, tx[:12]), 'w'))
        else: print('  no trace served')
    return t, r
if __name__ == '__main__': show(int(sys.argv[1]), sys.argv[2])
