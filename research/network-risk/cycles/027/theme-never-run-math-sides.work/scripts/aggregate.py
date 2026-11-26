"""Merge edges-<cid>-<k>.json shards and refedges-25/26(/27).json into out/edges.json: per arithmetic site of the
build (pc, opcode, source line), the frames-steps per edge class on Monad 143, MegaETH 4326, HyperEVM 999, and the
reference runs of the cycle 25, 26 and 27 cases. Lists the site/edge pairs no mined frame of MegaETH or HyperEVM used.
usage: aggregate.py"""
import sys, os, json, glob
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = HERE + '/../out'
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/024/theme-producer-branch-coverage.work/scripts')
from sites import sites
sys.path.insert(0, HERE)
from edges import OPS
S = {p: (n, f, l, sn) for p, n, f, l, sn in sites() if n in OPS}
src = {}
for cid in (143, 4326, 999):
    e = {}; h = {}; tot = {}
    for fn in glob.glob(OUT + '/edges-%d-*.json' % cid):
        d = json.load(open(fn))
        for k, v in d['edges'].items(): e[k] = e.get(k, 0) + v
        for k, v in d['hits'].items(): h[k] = h.get(k, 0) + v
        for k, v in d['totals'].items(): tot[k] = tot.get(k, 0) + v
    src[str(cid)] = {'edges': e, 'hits': h, 'totals': tot}
for w in ('25', '26', '27'):
    fn = OUT + '/refedges-%s.json' % w
    if os.path.exists(fn):
        d = json.load(open(fn)); src['c' + w] = {'edges': d['edges'], 'first': d['firstCase']}
MATH = ('TickMath', 'BitMath', 'FullMath', 'UnsafeMath', 'SqrtPriceMath', 'SwapMath', 'TickBitmap', 'Position',
        'LiquidityMath', 'libraries/Pool.sol', 'SafeCast', 'LPFeeLibrary', 'ProtocolFeeLibrary', 'BalanceDelta', 'CurrencyDelta',
        'NonzeroDeltaCount', 'CurrencyReserves', 'PoolManager.sol', 'Currency.sol', 'ERC6909', 'Slot0')
keys = set()
for v in src.values(): keys |= set(v['edges'])
rows = []
for k in sorted(keys, key=lambda x: (int(x.split('|')[0]), x)):
    pc = int(k.split('|')[0]); ed = k.split('|', 1)[1]
    n, f, l, sn = S.get(pc, ('?', None, None, ''))
    r = {'pc': pc, 'op': n, 'file': f, 'line': l, 'snippet': (sn or '')[:90], 'edge': ed}
    for c in src: r[c] = src[c]['edges'].get(k, 0)
    r['closedProducers'] = r.get('4326', 0) + r.get('999', 0)
    r['referenceCases'] = r.get('c25', 0) + r.get('c26', 0) + r.get('c27', 0)
    if r['closedProducers'] == 0:
        for c in ('c25', 'c26', 'c27'):
            if c in src and k in src[c].get('first', {}): r['firstCase_' + c] = src[c]['first'][k]
    rows.append(r)
# edges that exist as classes for a site but were hit by nothing (enumerate the natural edges per opcode)
NAT = {'MULMOD': ['product>=2^256', 'rem=0', 'rem!=0'], 'SAR': ['shift=255&neg', 'shift=255&nonneg'], 'SIGNEXTEND': ['b=2&neg', 'b=2&nonneg'],
       'SDIV': ['numNeg', 'numNeg&inexact'], 'SMOD': ['numNeg', 'numNeg&inexact'], 'DIV': ['div>2^128', 'num<den'], 'MOD': ['div>2^128'],
       'MUL': ['wrap'], 'SUB': ['borrow', 'borrow-all-4-limbs'], 'BYTE': ['index=31'], 'SLT': ['opposite-sign'], 'SGT': ['opposite-sign'],
       'SHL': ['bitslost'], 'SHR': [], 'ADD': ['carry-out'], 'LT': [], 'GT': [], 'EXP': [], 'ADDMOD': ['sum>=2^256']}
mathsites = [p for p, (n, f, l, sn) in S.items() if f and any(m in f for m in MATH)]
neverAny = []
for p in sorted(mathsites):
    n, f, l, sn = S[p]
    for ed in NAT.get(n, []):
        k = '%d|%s' % (p, ed)
        if not any(src[c]['edges'].get(k, 0) for c in src):
            neverAny.append({'pc': p, 'op': n, 'file': f, 'line': l, 'snippet': (sn or '')[:90], 'edge': ed})
summ = {'sites': len(S), 'mathOrSettlementSites': len(mathsites), 'totals': {c: src[c].get('totals') for c in ('143', '4326', '999')},
        'edgePairsSeen': len(rows), 'pairsNoClosedProducer': sum(1 for r in rows if r['closedProducers'] == 0),
        'pairsNoClosedProducerButReference': sum(1 for r in rows if r['closedProducers'] == 0 and r['referenceCases'] > 0),
        'pairsNoClosedProducerNoReference': sum(1 for r in rows if r['closedProducers'] == 0 and r['referenceCases'] == 0),
        'naturalEdgesNothingUsed': len(neverAny)}
json.dump({'summary': summ, 'rows': rows, 'naturalEdgesNothingUsed': neverAny}, open(OUT + '/edges.json', 'w'), indent=0)
print(json.dumps(summ, indent=1))
