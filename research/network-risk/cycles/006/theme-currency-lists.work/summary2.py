# Joins the census files with the classified rows and applies two refinements that need no new reads:
#  fees      rows without a trace where protocolFeesAccrued of the token fell and the excess is within 2 percent of the fall
#            (fees accrued earlier in the same block make the collected amount slightly larger than the counter one block before)
#  accrual   rows with no outflow where settle credited a few units more than the Transfer log carries (interest bearing tokens)
# Writes raw/census_summary.json.
import json, gzip, os, collections
from lib import NETS
CEN = {1: '_w', 10: '_w', 8453: '_w', 130: '_w', 7777777: '_full', 480: '', 57073: '_w', 1868: '_w', 42220: '_full', 196: '_w', 42161: '_w', 4663: '_w', 99901: '_w', 137: '_w', 56: '_w',
       43114: '_w', 143: '_w', 4326: '_full', 4217: '_full', 5042: '_w', 999: '_full'}
RR = {1: '_c2', 10: '_c2', 42161: '_c2', 8453: '_w', 5042: '_w', 4663: '_w', 137: '_w', 43114: '_w', 56: '_w', 99901: '_w'}
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
out = {}
for n in NETS:
    cid = n['chainId']; fn = 'raw/census2_%d%s.json.gz' % (cid, CEN[cid])
    if not os.path.exists(fn): out[cid] = dict(name=n['name'], missing=True); continue
    d = json.load(gzip.open(fn)); C = d['counts']; bt = d.get('blockTime')
    e = dict(name=n['name'], B1=d['B1'], B2=d['B2'], blocks=d['B2'] - d['B1'] + 1, days=round((d['B2'] - d['B1']) * bt / 86400, 1) if bt else None, txs=d['txs'], rows=C.get('rows', 0), ok=C.get('ok', 0),
             skippedLiquidity=C.get('skipped-liquidity', 0), skippedUnknownPool=C.get('skipped-unknown-pool', 0), nativeNoLogs=C.get('native-no-logs', 0), flagged=C.get('flagged', 0),
             flaggedPoolTx=C.get('flagged-pooltx', 0), flaggedNoPool=C.get('flagged-nopool', 0), full=CEN[cid] == '_full' or cid == 99901, file=fn, partial=d.get('partial', False))
    rf = 'raw/reread_%d%s.json.gz' % (cid, RR.get(cid, '_x'))
    if e['flagged'] and os.path.exists(rf):
        rows = json.load(gzip.open(rf))['rows']; cl = collections.Counter(); toks = collections.defaultdict(lambda: collections.Counter()); eg = {}
        for r in rows:
            k = refine(r, cid); cl[k] += 1; toks[k][r['token']] += 1; eg.setdefault((k, r['token']), r['tx'])
        e['classes'] = dict(cl); e['classified'] = len(rows)
        e['tokens'] = {k: [[t, c, eg[(k, t)]] for t, c in v.most_common(40)] for k, v in toks.items() if k not in ('fees',)}
        e['tokenCounts'] = {k: len(v) for k, v in toks.items()}
    out[cid] = e
json.dump(out, open('raw/census_summary.json', 'w'), indent=0)
for cid, e in out.items():
    if e.get('missing'): print(cid, e['name'], 'MISSING'); continue
    print(cid, e['name'], 'blocks', e['B1'], e['B2'], 'days', e['days'], 'full' if e['full'] else '', 'txs', e['txs'], 'rows', e['rows'], 'flagged', e['flagged'], e.get('classes', ''), e.get('tokenCounts', ''))
