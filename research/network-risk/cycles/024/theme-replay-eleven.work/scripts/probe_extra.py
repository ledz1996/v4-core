"""Second endpoint probe (cycle 24): further public candidates for the networks the first probe left without a trace endpoint.
Read-only: web3_clientVersion, eth_getLogs, debug_traceTransaction prestateTracer diffMode, trace_replayTransaction stateDiff."""
import json, sys
from rpcu import call
from eps import NETS
EX = {
 7777777: ['https://rpc.zora.energy', 'https://zora.gateway.tenderly.co', 'https://zora-mainnet.g.alchemy.com/public', 'https://7777777.rpc.thirdweb.com', 'https://zora.rpc.thirdweb.com'],
 480: ['https://worldchain.gateway.tenderly.co', 'https://worldchain-mainnet.gateway.tenderly.co', 'https://worldchain-mainnet.public.blastapi.io', 'https://worldchain-rpc.publicnode.com', 'https://worldchain.drpc.org'],
 1868: ['https://soneium.gateway.tenderly.co', 'https://soneium-rpc.publicnode.com', 'https://soneium.rpc.scs.startale.com', 'https://soneium.drpc.org'],
 196: ['https://xlayer.drpc.org', 'https://endpoints.omniatech.io/v1/xlayer/mainnet/public', 'https://xlayer-rpc.publicnode.com', 'https://rpc.ankr.com/xlayer', 'https://196.rpc.thirdweb.com'],
 4663: ['https://robinhood.drpc.org', 'https://4663.rpc.thirdweb.com'],
 99901: ['https://elysium.drpc.org', 'https://99901.rpc.thirdweb.com'],
 5042: ['https://arc-mainnet.drpc.org', 'https://5042.rpc.thirdweb.com', 'https://rpc.arc.network'],
 10: ['https://optimism.drpc.org', 'https://optimism-mainnet.public.blastapi.io'],
}
TX = {int(k): v for k, v in (json.loads(a) for a in sys.argv[2:3])} if False else {}
for f in __import__('glob').glob('../raw/probe-*.json'):
    for k, v in json.load(open(f)).items(): TX[int(k)] = v.get('tx')
out = {}
for cid in [int(x) for x in sys.argv[1:]] or EX:
    pm = NETS[cid]['poolManager']; tx = TX.get(cid)
    if not tx:
        u = NETS[cid]['rpc']; bn, e = call(u, 'eth_blockNumber', [], 30)
        if bn:
            bn = int(bn, 16); hi = bn
            for k in range(60):
                lg, e = call(u, 'eth_getLogs', [{'address': pm, 'fromBlock': hex(hi - 9999), 'toBlock': hex(hi)}], 60)
                if lg: tx = lg[-1]['transactionHash']; break
                hi -= 10000
    r = {'tx': tx}
    for u in EX[cid]:
        d = {'cvBefore': call(u, 'web3_clientVersion', [], 30)}
        d['prestateDiff'] = (lambda a: ('ok %d' % len(json.dumps(a[0]))) if a[0] is not None else a[1])(call(u, 'debug_traceTransaction', [tx, {'tracer': 'prestateTracer', 'tracerConfig': {'diffMode': True}}], 60))
        d['replay'] = (lambda a: ('ok %d' % len(json.dumps(a[0]))) if a[0] is not None else a[1])(call(u, 'trace_replayTransaction', [tx, ['stateDiff']], 60))
        d['cvAfter'] = call(u, 'web3_clientVersion', [], 30)
        r[u] = d; print(cid, u, json.dumps(d)[:400], flush=True)
    out[cid] = r
json.dump(out, open('../raw/probe-extra-%s.json' % ('-'.join(sys.argv[1:]) or 'all'), 'w'), indent=1)
