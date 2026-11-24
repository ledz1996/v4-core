"""Arc: native USDC value transfers emit a Transfer(from, to, value) log at 0xffff...fffe. For every Arc
transaction checked with a native currency leg, sum those logs from and to the PoolManager in the receipt
(written by block production) and compare with what the source says was owed."""
import sys, json
from lib import *
NAT = '0xfffffffffffffffffffffffffffffffffffffffe'; PM = NETS[5042]['poolManager'].lower()
d = json.load(open('raw/an2-5042.json')); out = []
from collections import Counter
c = Counter()
for r in d['results']:
    if 'native' not in r: continue
    rc = rpc(5042, 'eth_getTransactionReceipt', [r['tx']], urls=STATE_URLS[5042])
    o = i_ = 0
    for x in rc['logs']:
        if x['address'].lower() == NAT and x['topics'][0] == TRANSFER:
            v = int(x['data'][2:66], 16)
            if '0x' + x['topics'][1][26:] == PM: o += v
            if '0x' + x['topics'][2][26:] == PM: i_ += v
    leg = r['currencies']['0x' + '0' * 40]; diff = (o - i_) - int(leg['owed'])
    rec = {'tx': r['tx'], 'block': r['block'], 'otherPmTxInBlock': r['native']['otherPmTxInBlock'], 'owed': leg['owed'], 'out': str(o), 'in': str(i_), 'diff': str(diff),
           'balanceDiff': r['native']['balanceDiff']}
    out.append(rec); c[('exact' if diff == 0 else 'differs', r['native']['otherPmTxInBlock'])] += 1
json.dump(out, open('raw/arc-native.json', 'w'), indent=1)
print(dict(c))
