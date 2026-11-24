# Lead L-155, one candidate class: does the implementation address behind a pooled proxy token answer balanceOf(PoolManager)
# with a nonzero figure when it is called directly? A nonzero answer means the address is a second currency id on some ledger.
# Read-only eth_call with a state override stub. Proxy lists come from cycles/006/theme-currency-lists.work/raw/proxies_<chain>.json.gz.
import sys, os, json, gzip
T6 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '006', 'theme-currency-lists.work')
sys.path.insert(0, T6)
from common import *
from asm import assemble
from concurrent.futures import ThreadPoolExecutor
BALS = assemble('''
0x70a0823100000000000000000000000000000000000000000000000000000000 0 MSTORE
0 CALLDATALOAD 4 MSTORE
0x20
loop:
DUP1 CALLDATASIZE EQ @end JUMPI
0 0x40 MSTORE
0x20 0x40 0x24 0 DUP5 CALLDATALOAD 0x493e0 STATICCALL
0x20 RETURNDATASIZE LT ISZERO AND 0x40 MLOAD MUL 0x20 DUP3 SUB 0x400 ADD MSTORE
0x20 ADD
@loop JUMP
end:
POP
0x20 CALLDATASIZE SUB 0x400 RETURN
''')
def run(cid, per=120):
    pm = net(cid)['poolManager']
    d = json.load(gzip.open(os.path.join(T6, 'raw', 'proxies_%d.json.gz' % cid)))['impl']
    impls = {}
    for tok, lst in d.items():
        for kind, im in lst: impls.setdefault(im.lower(), []).append(tok)
    L = sorted(impls)
    def one(chunk, depth=0):
        r = ecall(cid, STUB, '0x' + adr(pm) + ''.join(adr(t) for t in chunk), {STUB: {'code': BALS}}, gas=40_000_000, rot=depth + len(chunk))
        if isinstance(r, str) and len(r) == 2 + 64 * len(chunk):
            return {t: int(r[2 + 64 * j: 66 + 64 * j], 16) for j, t in enumerate(chunk)}
        if len(chunk) > 1:
            h = len(chunk) // 2; o = one(chunk[:h], depth + 1); o.update(one(chunk[h:], depth + 1)); return o
        return {chunk[0]: None}
    out = {}
    with ThreadPoolExecutor(4) as ex:
        for res in ex.map(lambda i: one(L[i:i + per]), range(0, len(L), per)): out.update(res)
    nz = {k: v for k, v in out.items() if v}
    fail = [k for k, v in out.items() if v is None]
    # control: the same stub on three proxies must return their real balances
    res = {'chainId': cid, 'proxies': len(d), 'implementations': len(L), 'answered': len(out) - len(fail), 'failed': len(fail),
           'nonzero': {k: {'balanceOf': str(v), 'proxies': impls[k][:5], 'nproxies': len(impls[k])} for k, v in nz.items()}}
    json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'raw', 'impl_face_%d.json' % cid), 'w'), indent=1)
    print(cid, 'proxies', len(d), 'implementations', len(L), 'answered', len(out) - len(fail), 'failed', len(fail), 'nonzero', len(nz), flush=True)
    for k, v in list(nz.items())[:12]: print('   ', k, v, impls[k][:2], len(impls[k]))
if __name__ == '__main__':
    for c in sys.argv[1:]: run(int(c))
