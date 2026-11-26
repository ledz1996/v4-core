"""Task 1: which public endpoints of the six networks serve call traces. Read-only.
Writes raw/probe.json. For each endpoint: web3_clientVersion before and after, eth_blockNumber,
debug_traceTransaction(callTracer), trace_transaction, trace_block, debug_traceBlockByNumber(callTracer)
on one recent PoolManager transaction found through eth_getLogs on the reference endpoint."""
import json, sys, os, time
sys.path.insert(0, os.path.dirname(__file__))
from rpcu import call
W = os.path.join(os.path.dirname(__file__), '..', 'raw')
NETS = {
    999: ('0x12D4Fd9C5DeDd00ab8a0bCe2CF0167bbf94b6B1F', ['https://rpc.hyperliquid.xyz/evm', 'https://rpc.purroofgroup.com', 'https://hyperliquid.drpc.org', 'https://hyperliquid-json-rpc.stakely.io', 'https://rpc.hypurrscan.io']),
    5042: ('0x8366a39CC670B4001A1121B8F6A443A643e40951', ['https://rpc.mainnet.arc.io', 'https://arc.drpc.org', 'https://arc-rpc.publicnode.com', 'https://5042.rpc.thirdweb.com', 'https://arc.gateway.tenderly.co']),
    4326: ('0xacb7e78fa05d562e0a5d3089ec896d57d057d38e', ['https://mainnet.megaeth.com/rpc', 'https://megaeth.drpc.org', 'https://4326.rpc.thirdweb.com']),
    143: ('0x188d586ddcf52439676ca21a244753fa19f9ea8e', ['https://rpc.monad.xyz', 'https://rpc1.monad.xyz', 'https://rpc2.monad.xyz', 'https://rpc3.monad.xyz', 'https://rpc4.monad.xyz', 'https://rpc-mainnet.monadinfra.com', 'https://monad.drpc.org']),
    43114: ('0x06380c0e0912312b5150364b9dc4542ba0dbbc85', ['https://api.avax.network/ext/bc/C/rpc', 'https://avax.api.pocket.network', 'https://avalanche-c-chain-rpc.publicnode.com', 'https://avalanche.drpc.org', 'https://1rpc.io/avax/c', 'https://avalanche.gateway.tenderly.co']),
    99901: ('0xE2e105d3F7209A9DA11f83cCf3E7398a753823F1', ['https://rpc.elysium.kinetiq.xyz']),
}
RANGE = {999: 1000, 5042: 2000, 4326: 5000, 143: 100, 43114: 2000, 99901: 5000}


def find_tx(cid, pm, urls):
    for u in urls:
        head, e = call(u, 'eth_blockNumber', [])
        if e:
            continue
        h = int(head, 16)
        lo = h - 20
        for step in range(60):
            fr = max(0, lo - RANGE[cid])
            logs, e = call(u, 'eth_getLogs', [{'address': pm, 'fromBlock': hex(fr), 'toBlock': hex(lo)}])
            if e:
                break
            if logs:
                lg = logs[-1]
                return lg['transactionHash'], int(lg['blockNumber'], 16), u
            lo = fr - 1
    return None, None, None


def main():
    only = [int(x) for x in sys.argv[1:]] or list(NETS)
    out = {}
    pth = os.path.join(W, 'probe.json')
    if os.path.exists(pth):
        out = json.load(open(pth))
    for cid in only:
        pm, urls = NETS[cid]
        tx, blk, src = find_tx(cid, pm, urls)
        rec = {'pm': pm, 'sampleTx': tx, 'sampleBlock': blk, 'sampleFrom': src, 'endpoints': {}, 'time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
        for u in urls:
            r = {}
            r['clientVersionBefore'] = call(u, 'web3_clientVersion', [])
            r['blockNumber'] = call(u, 'eth_blockNumber', [])
            if tx:
                for name, m, p in [('debug_traceTransaction_callTracer', 'debug_traceTransaction', [tx, {'tracer': 'callTracer'}]),
                                   ('trace_transaction', 'trace_transaction', [tx]),
                                   ('trace_block', 'trace_block', [hex(blk)]),
                                   ('debug_traceBlockByNumber_callTracer', 'debug_traceBlockByNumber', [hex(blk), {'tracer': 'callTracer'}]),
                                   ('eth_getBalance_at_sample_minus_1', 'eth_getBalance', [pm, hex(blk - 1)])]:
                    res, err = call(u, m, p, timeout=60)
                    if err:
                        r[name] = {'ok': False, 'err': err}
                    else:
                        s = json.dumps(res)
                        r[name] = {'ok': True, 'bytes': len(s), 'head': s[:160]}
            r['clientVersionAfter'] = call(u, 'web3_clientVersion', [])
            rec['endpoints'][u] = r
            print(cid, u, {k: (v['ok'] if isinstance(v, dict) else (v[1] is None)) for k, v in r.items()}, flush=True)
        out[str(cid)] = rec
        json.dump(out, open(pth, 'w'), indent=1)


main()
