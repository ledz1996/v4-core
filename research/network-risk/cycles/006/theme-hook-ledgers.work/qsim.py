# Variant of the in-unlock test for endpoints without debug_traceCall: eth_simulateV1 of the Quoter call with the same state override,
# with traceTransfers. The Quoter reverts internally, so logs are lost; the result is the quoted amount or the revert data.
# Falls back to a plain eth_call with state override. usage: python3 qsim.py <cid> <hook> [maxtok]
import sys, collections
from common import *
import qtr
os.chdir(C5)
import probe as P
from summ import load
os.chdir(HERE)
W = '0x1111111111111111111111111111111111111112'
def quote(cid, hook, c0, c1, fee, ts, zfo, amount):
    n = net(cid); pm = n['poolManager']; q = n['contracts']['Quoter']
    k = P.key(c0, c1, fee, ts, hook); pid = qtr.pool_id(c0, c1, fee, ts, hook)
    data = qtr.SELIN + P.w(32) + k + P.w(zfo) + P.w(amount) + P.w(0x100) + P.w(0)
    slot = keccak256(bytes.fromhex(pid) + (6).to_bytes(32, 'big')).hex()
    slot0 = (1 << 96) | ((fee if fee != 0x800000 else 0) << 208)
    ov = {pm: {'stateDiff': {'0x' + slot: '0x' + P.w(slot0)}}}
    for u in urls(cid):
        j = post(u, {'jsonrpc': '2.0', 'id': 1, 'method': 'eth_call', 'params': [{'from': '0x00000000000000000000000000000000c0ffee03', 'to': q, 'data': '0x' + data}, 'latest', ov]})
        if 'error' in j:
            e = j['error']; d = e.get('data')
            if isinstance(d, str) and d.startswith('0x'): return 'revert ' + P.dec_err(d)[:150]
            last = str(e)[:150]; continue
        r = j['result']; return 'amountOut=%d' % int(r[2:66], 16)
    return 'err ' + last
def main(cid, hook, maxtok=3, amount=10 ** 15):
    hook = hook.lower()
    os.chdir(C5); rows = [r for r in load(cid) if r[6] == hook]; os.chdir(HERE)
    cur = collections.Counter()
    for r in rows: cur[r[2]] += 1; cur[r[3]] += 1
    toks = [c for c, _ in cur.most_common()][:maxtok]
    fee, ts = collections.Counter((r[4], r[5]) for r in rows).most_common(1)[0][0] if rows else (3000, 60)
    print('== %d %s pools %d fee/ts %s' % (cid, hook, len(rows), (fee, ts)))
    for t in toks + ['0x2222222222222222222222222222222222222223']:
        c0, c1 = sorted([W, t], key=lambda x: int(x, 16))
        for zfo in (1, 0): print('   key(%s,%s) zfo=%d: %s' % (c0[:10], c1[:10], zfo, quote(cid, hook, c0, c1, fee, ts, zfo, amount)))
if __name__ == '__main__':
    for h in sys.argv[2:]: main(int(sys.argv[1]), h)
