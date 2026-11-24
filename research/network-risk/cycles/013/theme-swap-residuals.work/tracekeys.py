"""Pool keys for zero-amount swaps on pools no other source gave a key for: the PoolManager.swap call in the
transaction's call trace carries the PoolKey as its first five words; the key is accepted only when it hashes to the pool id."""
import sys, json, glob, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import replay2 as R
TRACE = {42161: ['https://arbitrum.drpc.org'], 43114: ['https://avalanche.drpc.org'], 56: ['https://bsc.drpc.org'], 130: ['https://unichain.drpc.org'],
         143: ['https://monad.drpc.org', 'https://rpc3.monad.xyz'], 57073: ['https://ink.drpc.org']}
SWAPSEL = '0x' + R.keccak(b'swap((address,address,uint24,int24,address),(bool,int256,uint160),bytes)')[:4].hex()
out = {}
for f in sorted(glob.glob('raw/r2-*.json')):
    d = json.load(open(f)); c = d['chainId']
    for smp in (d.get('zeroAmount') or {}).get('samples', []):
        if smp['hooks'] is not None: continue
        pm = R.NETS[c]['poolManager'].lower(); res = None
        for u in TRACE.get(c, []):
            try:
                tr = R._rpc(u, 'debug_traceTransaction', [smp['tx'], {'tracer': 'callTracer'}], timeout=60)
            except Exception as e:  # noqa
                res = {'error': str(e)[:120]}; continue
            stack = [tr]; found = None
            while stack:
                x = stack.pop(); stack += x.get('calls', [])
                if x.get('to', '').lower() == pm and x.get('input', '').startswith(SWAPSEL):
                    kb = bytes.fromhex(x['input'][10:10 + 320])
                    if '0x' + R.keccak(kb).hex() == smp['pool']:
                        w = [int.from_bytes(kb[32 * i:32 * i + 32], 'big') for i in range(5)]
                        found = {'fee': w[2], 'spacing': R.s(w[3]), 'hooks': '0x%040x' % w[4], 'beforeSwapReturnsDelta': bool(w[4] & 8), 'amountSpecified': str(R.s(int(x['input'][10 + 384:10 + 448], 16)))}
                        break
            res = found or {'error': 'swap call not found in trace'}; res['url'] = u
            if found: break
        out[smp['tx'] + ':' + smp['pool']] = {'chainId': c, **res}
        print(c, smp['tx'][:12], res, flush=True)
json.dump(out, open('raw/tracekeys.json', 'w'), indent=1)
