# Fill the balances the batch run missed. One eth_call per 150 tokens with the DRIVERSEL style stub placed at an unused address.
import sys, json, os
from concurrent.futures import ThreadPoolExecutor
from base import *
# calldata: word0 = holder; then token words. For each token: staticcall balanceOf(holder), 2 words out: ok flag, value.
BALS = assemble('''
0x70a0823100000000000000000000000000000000000000000000000000000000 0 MSTORE
0 CALLDATALOAD 4 MSTORE
0x20 0x400
loop:
DUP2 CALLDATASIZE EQ @end JUMPI
0 0x40 MSTORE
0x20 0x40 0x24 0 DUP6 CALLDATALOAD 0x7a120 STATICCALL
0x1f RETURNDATASIZE GT AND
DUP2 MSTORE
0x40 MLOAD DUP2 0x20 ADD MSTORE
0x40 ADD SWAP1 0x20 ADD SWAP1
@loop JUMP
end:
0x400 DUP2 SUB 0x400 RETURN
''')
STUBADDR = '0x00000000000000000000000000000000000ba1a5'
def bals(cid, toks, holder, per=150, workers=5, block='latest'):
    us = urls2(cid) + ([net(cid)['rpc']] if net(cid)['rpc'] not in urls2(cid) else [])
    out = {}
    def one(ch, depth=0):
        data = '0x' + adr(holder) + ''.join(adr(t) for t in ch)
        for k in range(5):
            r = ecall(cid, STUBADDR, data, {STUBADDR: {'code': BALS}}, gas=45_000_000, rot=k + depth, tries=2, block=block)
            if isinstance(r, str) and len(r) == 2 + 128 * len(ch):
                return {t: (int(r[66 + 128 * j: 130 + 128 * j], 16) if int(r[2 + 128 * j: 66 + 128 * j], 16) else None) for j, t in enumerate(ch)}
            time.sleep(0.5)
        if len(ch) > 1:
            h = len(ch) // 2; o = one(ch[:h], depth + 1); o.update(one(ch[h:], depth + 1)); return o
        return {ch[0]: None}
    with ThreadPoolExecutor(workers) as ex:
        for o in ex.map(lambda i: one(toks[i:i + per]), range(0, len(toks), per)): out.update(o)
    return out
def run(cid):
    fn = os.path.join(RAW7, 'live_%d.json.gz' % cid); d = jz(fn); pm = net(cid)['poolManager'].lower(); pr = prices(cid)
    miss = [t for t, r in d['rows'].items() if r['bal'] is None]
    o = bals(cid, miss, pm)
    for t, b in o.items():
        if b is not None: d['rows'][t]['bal'] = str(b); d['rows'][t]['usd'] = usdv(b, pr[t])
    wz(fn, d)
    rows = d['rows']; v = [r['usd'] for r in rows.values()]
    print(cid, net(cid)['name'], 'priced', len(rows), 'missing before', len(miss), 'nobal', sum(1 for r in rows.values() if r['bal'] is None), 'bal>0', sum(1 for r in rows.values() if int(r['bal'] or 0) > 0),
          '>1000', sum(1 for x in v if x > 1000), '>100', sum(1 for x in v if x > 100), '>10', sum(1 for x in v if x > 10), '>1', sum(1 for x in v if x > 1), 'sum', round(sum(x for x in v if x < 1e12)), flush=True)
if __name__ == '__main__':
    for c in sys.argv[1:]: run(int(c))
