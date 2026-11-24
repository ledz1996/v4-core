"""L-644: per-removal check of older Tempo removals and collections that sit alone in their transaction.
Reuses one() of cycles/011/theme-mined-liquidity.work/analyze.py (owed by the source vs Transfer logs that left the PoolManager).
Usage: l644.py <mod.json> <out.json> <max> <threads>"""
import sys, json, random, collections, concurrent.futures as cf
src, out, MAX, TH = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
W11 = '/home/user/v4-core/research/network-risk/cycles/011/theme-mined-liquidity.work'
sys.path[:0] = [W11, '/home/user/v4-core/research/network-risk/tools/opdiff']
sys.argv = ['analyze.py', '4217', src, out]
import analyze as A
logs = json.load(open(src))['logs']
per_tx = collections.Counter(l['transactionHash'] for l in logs)
cand = [l for l in logs if A.s256(int(l['data'][2 + 128:2 + 192], 16)) <= 0 and per_tx[l['transactionHash']] == 1]
random.Random(644).shuffle(cand)
cand = cand[:MAX]
def safe(l):
    try: return A.one(l)
    except Exception as e: return {'tx': l['transactionHash'], 'block': int(l['blockNumber'], 16), 'error': str(e)[:200]}
with cf.ThreadPoolExecutor(TH) as ex: res = list(ex.map(safe, cand))
json.dump({'chainId': 4217, 'source': src, 'candidates': len(cand), 'results': res}, open(out, 'w'), indent=1)
C = collections.Counter
print('n', len(res), C(r.get('aside') or ('error' if 'error' in r else 'checked') for r in res))
chk = [r for r in res if 'result' in r]
print('results', C((r['kind'], tuple(r['result'])) for r in chk).most_common())
fee = [r for r in chk if any(int(x) for x in r['fees'])]
print('fee-bearing checked', len(fee), C(tuple(r['result']) for r in fee), 'blocks', min([r['block'] for r in fee] or [0]), max([r['block'] for r in fee] or [0]))
print('insideMatchesStored', C(r.get('insideMatchesStored') for r in chk), 'liqAfterOk', C(r.get('liqAfterOk') for r in chk))
