"""Usage: python3 run_big.py <logs.jsonl> <out.json>   (FAULT env plants a MULMOD fault, see bigcheck.py)"""
import sys, os, json, collections, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import bigcheck as B
from evm import rpc, s
import collect as C
PM = '0x188d586ddcf52439676ca21a244753fa19f9ea8e'
URL = 'https://rpc3.monad.xyz'
logs = []; windows = 0; missing = 0; lo = 1 << 60; hi = 0
for line in open(sys.argv[1]):
    x = json.loads(line); windows += 1
    if x['logs'] is None: missing += 1; continue
    lo = min(lo, x['lo']); hi = max(hi, x['hi']); logs += x['logs']
logs.sort(key=lambda l: (l['b'], l['i']))
v3addrs = sorted({l['a'] for l in logs if l['t'][0] == C.V3SWAP})
meta_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'raw', 'v3meta.json')
meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
def getmeta(a):
    out = {}
    for k, sel in (('factory', '0xc45a0155'), ('fee', '0xddca3f43'), ('liquidity', '0x1a686502')):
        try: out[k] = rpc(URL, 'eth_call', [{'to': a, 'data': sel}, 'latest'])
        except Exception as e: out[k] = None
    return a, out
todo = [a for a in v3addrs if a not in meta]
with cf.ThreadPoolExecutor(8) as ex:
    for a, o in ex.map(getmeta, todo): meta[a] = o
json.dump(meta, open(meta_path, 'w'))
res = {'fault': B.FAULT, 'windows': windows, 'windowsMissing': missing, 'blocks': [lo, hi], 'v4': None, 'v3': None}
def summarize(kind):
    return {'swaps': 0, 'pairs': 0, 'modes': collections.Counter(), 'unmatched': 0, 'sites': collections.Counter(), 'sitesBig': collections.Counter(),
            'swapsWithBig': 0, 'bigBySite': collections.defaultdict(list), 'unmatchedSamples': [], 'byFactory': collections.Counter(), 'perFactory': {}}
R = {'v4': summarize('v4'), 'v3': summarize('v3')}
last = {}
for l in logs:
    t0 = l['t'][0]
    if l['a'] == PM and t0 == C.V4MOD: last.pop(('v4', l['t'][1]), None); continue
    if t0 in (C.V3MINT, C.V3BURN): last.pop(('v3', l['a']), None); continue
    d = l['d']
    if l['a'] == PM and t0 == C.V4SWAP:
        kind, key = 'v4', ('v4', l['t'][1])
        a0, a1 = s(B.word(d, 0)), s(B.word(d, 1)); price, liq, fee = B.word(d, 2), B.word(d, 3), B.word(d, 5)
        a0, a1 = -a0, -a1  # v4 emits the swapper's delta: negative paid; flip to pool side
        fac = 'v4'
    elif t0 == C.V3SWAP:
        mt = meta.get(l['a'], {})
        if not mt.get('fee') or not mt.get('factory'): continue
        kind, key = 'v3', ('v3', l['a'])
        a0, a1 = s(B.word(d, 0)), s(B.word(d, 1)); price, liq = B.word(d, 2), B.word(d, 3); fee = int(mt['fee'], 16)
        fac = '0x' + mt['factory'][-40:]
    else:
        continue
    r = R[kind]; r['swaps'] += 1; r['byFactory'][fac] += 1
    prev = last.get(key)
    if prev and prev[1] == liq and liq > 0 and prev[0] != price:
        p0 = prev[0]; zfo = price < p0
        paid, got = (a0, -a1) if zfo else (a1, -a0)
        r['pairs'] += 1
        pf = r['perFactory'].setdefault(fac, {'pairs': 0, 'matched': 0, 'unmatched': 0, 'multi': 0, 'swapsWithBig': 0, 'sitesBig': {}})
        pf['pairs'] += 1
        mode, tr = (None, []) if paid < 0 or got < 0 else B.check(p0, price, liq, paid, got, fee)
        if mode:
            r['modes'][mode] += 1
            big = False
            for site, flag in tr:
                r['sites'][site] += 1
                if flag:
                    r['sitesBig'][site] += 1; big = True
                    if len(r['bigBySite'][site]) < 5: r['bigBySite'][site].append(l['h'])
            r['swapsWithBig'] += big; pf['matched'] += 1; pf['swapsWithBig'] += big
            for site, flag in tr:
                if flag: pf['sitesBig'][site] = pf['sitesBig'].get(site, 0) + 1
        else:
            r['unmatched'] += 1; pf['unmatched'] += 1
            if __import__('swaps').check_amounts(p0, price, liq, -a0, -a1, fee) == 'multi': pf['multi'] += 1
            if len(r['unmatchedSamples']) < 300:
                r['unmatchedSamples'].append({'tx': l['h'], 'block': l['b'], 'pool': key[1], 'factory': fac, 'p0': str(p0), 'p1': str(price), 'liq': str(liq), 'a0': str(a0), 'a1': str(a1), 'fee': fee})
    last[key] = (price, liq)
for k in R:
    R[k] = {a: (dict(b) if isinstance(b, (collections.Counter, collections.defaultdict)) else b) for a, b in R[k].items()}
res.update(R)
json.dump(res, open(sys.argv[2], 'w'), indent=1)
for k in ('v4', 'v3'):
    r = R[k]; print(k, 'swaps', r['swaps'], 'pairs', r['pairs'], 'modes', r['modes'], 'unmatched', r['unmatched'], 'swapsWithBig', r['swapsWithBig']); print('   sitesBig', r['sitesBig']); print('   sites', r['sites'])
