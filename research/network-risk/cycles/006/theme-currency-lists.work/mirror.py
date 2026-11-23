# One balance under two ids: group pool currencies by equal balanceOf(PoolManager), then, for every group, let the PoolManager address
# (measuring stub, state override, eth_call) send one third of its balance of token A and read the balance of every other token of
# the group before and after. A token whose balance moves with A shares A's balance. The native balance is compared as well.
# usage: python3 mirror.py <chainId>
import sys, json, gzip, collections, random
from concurrent.futures import ThreadPoolExecutor
from common import *
from asm import assemble
MIRROR = assemble('''
0x70a0823100000000000000000000000000000000000000000000000000000000 0 MSTORE
ADDRESS 4 MSTORE
0x40
loop1:
DUP1 CALLDATASIZE EQ @mid JUMPI
0 0x40 MSTORE
0x20 0x40 0x24 0 DUP5 CALLDATALOAD 0x493e0 STATICCALL POP
0x40 MLOAD 0x40 DUP3 SUB 2 MUL 0x400 ADD MSTORE
0x20 ADD
@loop1 JUMP
mid:
POP
0 0x40 MSTORE
0x20 0x40 0x24 0 0x20 CALLDATALOAD 0x493e0 STATICCALL POP
0xa9059cbb00000000000000000000000000000000000000000000000000000000 0x80 MSTORE
0 CALLDATALOAD 0x84 MSTORE
3 0x40 MLOAD DIV 0xa4 MSTORE
0 0x100 MSTORE
0x20 0x100 0x44 0x80 0 0x20 CALLDATALOAD 0x1e8480 CALL POP
0x40
loop2:
DUP1 CALLDATASIZE EQ @end JUMPI
0 0x40 MSTORE
0x20 0x40 0x24 0 DUP5 CALLDATALOAD 0x493e0 STATICCALL POP
0x40 MLOAD 0x40 DUP3 SUB 2 MUL 0x420 ADD MSTORE
0x20 ADD
@loop2 JUMP
end:
0x40 CALLDATASIZE SUB 2 MUL 0x400 RETURN
''')
SINK = '0x00000000000000000000000000000000005111c0'
def run(cid):
    pm = net(cid)['poolManager']; bal = json.load(gzip.open('raw/bal_%d.json.gz' % cid))
    g = collections.defaultdict(list)
    for t, b in bal.items():
        if b != 'fail' and int(b) > 2: g[b].append(t)
    groups = {b: sorted(ts) for b, ts in g.items() if len(ts) > 1}
    nat = ecall(cid, pm, '0x', None); natbal = rpc(urls2(cid)[0], 'eth_getBalance', [pm, 'latest'])
    natbal = int(natbal, 16); same_native = [t for t, b in bal.items() if b != 'fail' and natbal > 0 and int(b) == natbal]
    print(cid, 'tokens with balance', sum(1 for b in bal.values() if b != 'fail' and int(b) > 0), 'groups of equal balance', len(groups), 'tokens in groups', sum(len(v) for v in groups.values()),
          'largest', sorted((len(v) for v in groups.values()), reverse=True)[:8], 'equal to native balance', same_native, flush=True)
    random.seed(6); jobs = []
    for b, ts in groups.items():
        As = ts if len(ts) <= 12 else random.sample(ts, 12)
        for a in As:
            others = [t for t in ts if t != a]
            if len(others) > 300: others = random.sample(others, 300)
            jobs.append((b, a, others))
    def job(j):
        b, a, others = j
        r = ecall(cid, pm, '0x' + adr(SINK) + adr(a) + ''.join(adr(t) for t in others), {pm: {'code': MIRROR}}, gas=45_000_000, rot=int(a[-3:], 16))
        if not isinstance(r, str) or len(r) != 2 + 128 * len(others): return (a, None, [])
        hits = []
        for k, t in enumerate(others):
            x = int(r[2 + 128 * k: 66 + 128 * k], 16); y = int(r[66 + 128 * k: 130 + 128 * k], 16)
            if x != y: hits.append((t, str(x), str(y)))
        return (a, True, hits)
    pairs = []; fail = 0
    with ThreadPoolExecutor(6) as ex:
        for a, ok, hits in ex.map(job, jobs):
            if ok is None: fail += 1
            for t, x, y in hits: pairs.append([a, t, x, y])
    json.dump(dict(chainId=cid, groups=len(groups), tokensInGroups=sum(len(v) for v in groups.values()), sizes=sorted((len(v) for v in groups.values()), reverse=True)[:50], trials=len(jobs), failedTrials=fail,
                   nativeBalance=str(natbal), equalToNative=same_native, mirrors=pairs), open('raw/mirror_%d.json' % cid, 'w'), indent=0)
    print(cid, 'trials', len(jobs), 'failed', fail, 'mirror pairs', len(pairs), pairs[:20], flush=True)
if __name__ == '__main__':
    for c in sys.argv[1:]: run(int(c))
