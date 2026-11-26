"""Classify every flagged row of a census3 file with cycles/006/theme-currency-lists.work/rule.classify (unchanged),
then apply the refine() rules of cycles/006/theme-currency-lists.work/summary2.py (copied below without change of logic,
chain-specific lines kept). Read-only: receipts, eth_getLogs on one block, eth_call at two blocks, debug_traceTransaction.
usage: reclass.py <chainId> <census3 file> <out file> [workers]"""
import sys, os, json, gzip, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '006', 'theme-currency-lists.work'))
import rule
from concurrent.futures import ThreadPoolExecutor
ARCFEE = '0x93967536028c0a57c8d66ab01ac889f270364a548b5f361d9a1210fc4d127c5b'
def refine(r, cid):
    c = r['cls']; ex = int(r.get('excess') or 0); out = int(r.get('out') or 0); mint = int(r.get('mint') or 0)
    if c == 'pool' and r['tx'] == ARCFEE: return 'fees'
    if cid == 56 and r.get('poolCurrency') is False and c == 'open': return 'tracker'
    if cid == 42161 and r['token'] == '0xb8894e9b133c97bf2c34365ff803cebbfeb467da': return 'nopool'
    if cid == 137 and r['token'] == '0xe0aea583266584dafbb3f9c3211d5588c73fea8d' and c in ('open', 'spoof'): return 'alias'
    if c in ('open', 'spoof') and r.get('trace') is None and r.get('feesAccrued'):
        f0, f1 = int(r['feesAccrued'][0]), int(r['feesAccrued'][1])
        if f0 > f1 and ex > 0 and abs(ex - (f0 - f1)) <= max(2, ex // 50): return 'fees'
    if c in ('open', 'spoof') and out == 0 and mint == 0 and ex > 0 and r.get('resid') is not None and int(r['resid']) >= ex: return 'accrual'
    if c == 'surplus' and out == 0 and mint == 0: return 'accrual'
    if cid == 5042 and r['token'] == '0xece5ca8bf9220718e5727754026757512212cb3c' and c == 'open': return 'sender-charge'
    if cid == 56 and r['token'] == '0x4ef42e4cf51cd779e9947db65b629ecd8c92b1da' and c == 'open': return 'sender-charge'
    if c == 'open' and 0 < ex and (ex <= 10 or ex * 10 ** 6 <= max(int(r.get('in') or 0), out)): return 'dust'
    if c == 'open' and r.get('kind') == 'sender-charge': return 'sender-charge'
    if c == 'open' and r.get('trace') is not None and not r['trace']['takes'] and mint == 0: return 'token-moved'
    if c == 'open' and r.get('trace') is None and r.get('poolEvents') == 0 and r.get('b0') and r.get('b1') and int(r['b1']) < int(r['b0']) and not r.get('feesAccrued', ['0', '0'])[0] != '0': return 'token-moved?'
    return c
cid = int(sys.argv[1]); out = sys.argv[3]; W = int(sys.argv[4]) if len(sys.argv) > 4 else 4
rows = []
for fn in sys.argv[2].split(','):
    rows += json.load(gzip.open(fn))['flagged']
pairs = sorted({(u['tx'], u['token'], int(u.get('owed') or 0)) for u in rows})
keep = {}
if os.path.exists(out):
    for r in json.load(gzip.open(out))['rows']:
        if r['cls'] not in ('unread', 'error'): keep[(r['tx'], r['token'])] = r
def one(x):
    if (x[0], x[1]) in keep: return keep[(x[0], x[1])]
    try: r = rule.classify(cid, x[0], x[1], owed=x[2])
    except Exception as e: r = dict(tx=x[0], token=x[1], cls='error', why=repr(e)[:200])
    r['refined'] = refine(r, cid) if 'cls' in r and r['cls'] not in ('unread', 'error') else r['cls']; return r
with ThreadPoolExecutor(W) as ex: res = list(ex.map(one, pairs))
json.dump(dict(chainId=cid, source=sys.argv[2], rows=res), gzip.open(out, 'wt'))
print(cid, 'rows', len(res), dict(collections.Counter(r['refined'] for r in res)), flush=True)
by = collections.defaultdict(collections.Counter)
for r in res: by[r['token']][r['refined']] += 1
for t, c in sorted(by.items(), key=lambda x: -sum(x[1].values()))[:40]: print('  ', t, dict(c))
