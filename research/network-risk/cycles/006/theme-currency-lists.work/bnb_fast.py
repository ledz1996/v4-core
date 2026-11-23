# BNB Smart Chain: the 3 day census flags 987 rows. The Initialize list is complete, so rows of tokens that are in no pool are
# read with balanceOf(PoolManager) one block before and at the block only. Rows of pool currencies get the full rule with a trace.
import json, gzip, collections, time
from concurrent.futures import ThreadPoolExecutor
import rule
from lib import *
d = json.load(gzip.open('raw/census2_56_w.json.gz')); cur = set(json.load(gzip.open('raw/currencies_56.json.gz'))['currencies']); pm = net(56)['poolManager'].lower()
rows = sorted({(f['tx'], f['token'], f['block'], int(f.get('owed') or 0), f['out'], f['in'], f['mint'], f['burn'], f['poolTx']) for f in d['flagged']})
def full(x):
    r = None
    for k in range(3):
        try: r = rule.classify(56, x[0], x[1], owed=x[3])
        except Exception as e: r = dict(tx=x[0], token=x[1], cls='error', why=repr(e)[:150])
        if r.get('trace') is not None and r.get('b0') is not None: break
        time.sleep(2)
    r['poolCurrency'] = True; return r
def cheap(x):
    b0 = b1 = None; rev = False
    def rd(blk):
        r = rule.any_rpc(56, 'eth_call', [{'to': x[1], 'data': sel('balanceOf(address)') + adr(pm)}, hex(blk)], 'state', timeout=30)
        if isinstance(r, str) and len(r) >= 66: return int(r[:66], 16), False
        return None, isinstance(r, dict) and bool(r.get('reverted')) or r == '0x'
    for k in range(4):
        b0, rev0 = rd(x[2] - 1); b1, rev1 = rd(x[2]); rev = rev0 or rev1
        if (b0 is not None and b1 is not None) or rev: break
        time.sleep(1)
    r = dict(tx=x[0], token=x[1], block=x[2], out=x[4], mint=x[6], burn=x[7], owed=str(x[3]), excess=str(int(x[4]) + int(x[6]) - int(x[5]) - int(x[7]) - x[3]), poolEvents=1 if x[8] else 0,
             b0=None if b0 is None else str(b0), b1=None if b1 is None else str(b1), trace=None, poolCurrency=False)
    r['in'] = x[5]
    if rev and (b0 is None or b1 is None): r['cls'] = 'nopool'; r['why'] = 'the token is in no pool and its balanceOf reverts or returns nothing for the PoolManager'
    elif b0 is None or b1 is None: r['cls'] = 'unread'; r['why'] = 'balanceOf did not answer at the old block; the token is in no pool'
    elif b1 >= b0: r['cls'] = 'spoof'; r['why'] = 'the token is in no pool and balanceOf(PoolManager) did not fall in the block'
    else: r['cls'] = 'open'; r['why'] = 'the token is in no pool; balanceOf(PoolManager) fell in the block'
    return r
A = [x for x in rows if x[1] in cur]; B = [x for x in rows if x[1] not in cur]
import os
if os.path.exists('raw/bnb_fast_b.json.gz'): rb = json.load(gzip.open('raw/bnb_fast_b.json.gz'))
else:
    with ThreadPoolExecutor(6) as ex: rb = list(ex.map(cheap, B))
    json.dump(rb, gzip.open('raw/bnb_fast_b.json.gz', 'wt'))
print('not pool currencies', len(B), collections.Counter(r['cls'] for r in rb), flush=True)
with ThreadPoolExecutor(3) as ex: ra = list(ex.map(full, A))
print('pool currencies', len(A), collections.Counter(r['cls'] for r in ra), flush=True)
json.dump(dict(chainId=56, rows=ra + rb), gzip.open('raw/reread_56_w.json.gz', 'wt'))
