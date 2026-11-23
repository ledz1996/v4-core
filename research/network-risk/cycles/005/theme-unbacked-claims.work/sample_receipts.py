# For each (caller, id) pair of claim mints on one network, fetch the receipts of sample transactions
# (first, last, and evenly spaced ones for large pairs) and test whether the receipt explains the credit:
#   in    = ERC-20 Transfer logs of the currency with to = PoolManager
#   out   = ERC-20 Transfer logs of the currency with from = PoolManager
#   burn  = ERC-6909 Transfer logs to the zero address with the same id
#   pool  = Swap, ModifyLiquidity or Donate logs of the PoolManager in the transaction
# A mint is "unexplained" when the transaction has no pool event and mint + out > in + burn for that id.
# Native id 0 has no Transfer logs; those rows are marked "native" and checked for tx value separately.
# usage: python3 sample_receipts.py <chainId> [perPair]
import sys, json, gzip, os, threading, collections, random, concurrent.futures as cf
from lib import *
from stats import load
T6909 = '0x1b3d7edb2e9c0b0e7c525b20aaaef0f5940d2ed71663c7d39266ecafac728859'
SWAP = '0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f'
MODL = '0xf208f4912782fd25c7f114ca3723a2d5dd6f3bcc3ac8db5af63baa85f711d5ec'
DON = '0x29ef05caaff9404b7cb6d1c0e9bbae9eaa7ab2541feba1a9c4248594c08156cb'
DEPOSIT = '0xe1fffcc4923d04b559f4d29a8bfc6cda04eb5b0d3c460751c2402c5c5cc9109c'
WITHDRAWAL = '0x7fcf532c15f0a6db0bd6d0e038bea71d30d808c7d98cb3bf7268a95bf5081b65'
Z = '0x' + '0' * 64
T = 'gateway.tenderly.co'
RCPT = {1: ['https://mainnet.' + T, 'https://ethereum-rpc.publicnode.com'], 10: ['https://optimism.' + T, 'https://mainnet.optimism.io'], 8453: ['https://base.' + T, 'https://mainnet.base.org/'],
 130: ['https://unichain.' + T, 'https://mainnet.unichain.org'], 480: ['https://sparkling-autumn-dinghy.worldchain-mainnet.quiknode.pro', 'https://worldchain-mainnet.g.alchemy.com/public'],
 57073: ['https://ink.' + T, 'https://rpc-gel.inkonchain.com'], 42220: ['https://celo.' + T, 'https://forno.celo.org'], 196: ['https://rpc.xlayer.tech', 'https://xlayerrpc.okx.com'],
 42161: ['https://arbitrum.' + T, 'https://arb1.arbitrum.io/rpc'], 4663: ['https://rpc.mainnet.chain.robinhood.com', 'https://robinhood.drpc.org'], 99901: ['https://rpc.elysium.kinetiq.xyz'],
 137: ['https://polygon.' + T], 56: ['https://bsc-dataseed1.bnbchain.org', 'https://bsc-mainnet.public.blastapi.io', 'https://bsc-dataseed2.defibit.io', 'https://bsc-dataseed3.bnbchain.org'], 43114: ['https://avalanche.' + T, 'https://api.avax.network/ext/bc/C/rpc'],
 143: ['https://rpc2.monad.xyz', 'https://rpc.monad.xyz'], 4326: ['https://mainnet.megaeth.com/rpc'], 4217: ['https://rpc.mainnet.tempo.xyz'], 5042: ['https://arc.' + T, 'https://rpc.mainnet.arc.io'], 999: ['https://rpc.purroofgroup.com', 'https://rpc.hyperliquid.xyz/evm']}
def digest(r, pm):
    pm = pm.lower(); pmt = pad_addr(pm)
    d = {'tx': r['transactionHash'], 'block': int(r['blockNumber'], 16), 'from': r['from'], 'to': r.get('to'), 'status': r.get('status'), 'nLogs': len(r['logs']), 'pool': 0, 'ids': {}}
    def e(i): return d['ids'].setdefault(i, {'mint': 0, 'burn': 0, 'in': 0, 'out': 0})
    for l in r['logs']:
        t = l['topics']; a = l['address'].lower()
        if not t: continue
        if a == pm:
            if t[0] in (SWAP, MODL, DON): d['pool'] += 1
            elif t[0] == T6909 and len(t) == 4:
                amt = int(l['data'][2:][64:128] or '0', 16)
                if t[1] == Z: e(t[3][-40:])['mint'] += amt
                elif t[2] == Z: e(t[3][-40:])['burn'] += amt
        elif t[0] == DEPOSIT and len(t) == 2 and t[1] == pmt and len(l['data']) >= 66:
            e(a[2:])['in'] += int(l['data'][2:66], 16); d['wrapDeposit'] = d.get('wrapDeposit', 0) + 1  # wrapper credited the PoolManager for native value it received
        elif t[0] == WITHDRAWAL and len(t) == 2 and len(l['data']) >= 66:
            d['unwrap'] = str(int(d.get('unwrap', '0')) + int(l['data'][2:66], 16))
        elif t[0] == TRANSFER and len(t) == 3 and len(l['data']) >= 66:
            amt = int(l['data'][2:66], 16)
            if t[2] == pmt: e(a[2:])['in'] += amt
            if t[1] == pmt: e(a[2:])['out'] += amt
    for i, v in d['ids'].items():
        if v['mint'] == 0: v['cls'] = '-'
        elif d['pool']: v['cls'] = 'pool'
        elif int(i, 16) == 0: v['cls'] = 'native' if v['mint'] > v['burn'] else 'ok'
        elif v['mint'] + v['out'] > v['in'] + v['burn']: v['cls'] = 'unexplained'
        else: v['cls'] = 'ok'
    d['ids'] = {i: {k: (str(x) if isinstance(x, int) else x) for k, x in v.items()} for i, v in d['ids'].items() if v['mint']}
    return d
def fetch_receipts(cid, txs, workers=6, keep_raw=None):
    urls = RCPT[cid]; pm = net(cid)['poolManager']; out = {}; lock = threading.Lock()
    def one(a):
        k, tx = a
        for attempt in range(5):
            u = urls[(k + attempt) % len(urls)]
            try:
                r = rpc(u, 'eth_getTransactionReceipt', [tx], timeout=40, tries=3)
                if r:
                    dg = digest(r, pm)
                    with lock:
                        out[tx] = dg
                        if keep_raw is not None and any(v['cls'] in ('unexplained',) for v in dg['ids'].values()): keep_raw[tx] = r
                    return
            except Exception as ex: time.sleep(1 + attempt)
        with lock: out[tx] = {'tx': tx, 'err': 'no receipt'}
    with cf.ThreadPoolExecutor(workers) as ex: list(ex.map(one, list(enumerate(txs))))
    return out
def main():
    # Rule: every mint transaction of an id that has at most SMALL mints in total; for larger ids, PER evenly spaced
    # transactions per (caller, id) pair plus 5 random ones. Digests already stored are reused.
    cid = int(sys.argv[1]); per = int(sys.argv[2]) if len(sys.argv) > 2 else 10; workers = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    SMALL = int(sys.argv[4]) if len(sys.argv) > 4 else 300
    # Memory bound: a pair keeps every mint up to CAP entries; beyond that it keeps the first, the last and a
    # uniform reservoir of CAP entries, from which the evenly spaced picks are then drawn.
    CAP = 400; random.seed(5)
    pairs = {}; idn = collections.Counter(); seen = collections.Counter()
    for b, tx, li, caller, to, i, amt in load(cid):
        k = (caller, i[-40:]); idn[k[1]] += 1; seen[k] += 1; v = pairs.get(k)
        if v is None: v = pairs[k] = {'first': (b, tx), 'last': (b, tx), 'r': []}
        if (b, tx) < v['first']: v['first'] = (b, tx)
        if (b, tx) > v['last']: v['last'] = (b, tx)
        if len(v['r']) < CAP: v['r'].append((b, tx))
        else:
            j = random.randrange(seen[k])
            if j < CAP: v['r'][j] = (b, tx)
    want = {}
    for k, vv in pairs.items():
        v = sorted(set(vv['r'] + [vv['first'], vv['last']])); n = len(v)
        if (idn[k[1]] <= SMALL and seen[k] <= CAP) or n <= per: pick = v
        else:
            idx = sorted(set([0, n - 1] + [round(j * (n - 1) / (per - 1)) for j in range(per)]))
            pick = [v[j] for j in idx] + random.sample(v, 5)
        for b, tx in pick: want[tx] = 1
    fn = 'raw/sample_%d.json.gz' % cid; old = {}
    if os.path.exists(fn):
        for d in json.load(gzip.open(fn, 'rt'))['digests']:
            if 'err' not in d and 'v2' in d: old[d['tx']] = d
    txs = [t for t in want if t not in old]; print(cid, 'pairs', len(pairs), 'ids', len(idn), 'wanted', len(want), 'to fetch', len(txs), flush=True)
    raw = {}
    out = fetch_receipts(cid, txs, workers=workers, keep_raw=raw)
    for d in out.values(): d['v2'] = 1
    out.update(old)
    json.dump({'chainId': cid, 'perPair': per, 'small': SMALL, 'pairs': len(pairs), 'digests': list(out.values())}, gzip.open(fn, 'wt'))
    json.dump(raw, gzip.open('raw/sample_%d_unexplained_receipts.json.gz' % cid, 'wt'))
    c = collections.Counter()
    for d in out.values():
        if 'err' in d: c['err'] += 1; continue
        for v in d['ids'].values(): c[v['cls']] += 1
    print(cid, dict(c), flush=True)
if __name__ == '__main__': main()
