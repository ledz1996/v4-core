"""Runs the Part B transient storage probe of tprobe.py in the reference interpreter pyevm.py, as built and
with two planted faults, to show that the probe's expected words catch a client that keeps transient writes
of a reverted frame ('norollback') or that hashes only the first 32 bytes of a KECCAK256 input ('keccak32',
which aliases the CurrencyDelta slots of one target). usage: python3 -I tprobe_ref.py <out.json>"""
import json, sys
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
sys.argv_out = sys.argv[1]
sys.argv = [sys.argv[0], '/dev/null']  # tprobe parses argv at import; no chain ids means no RPC call
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import tprobe as T
import pyevm
res = {}
for fault in ('none', 'norollback', 'keccak32'):
    orig_restore, orig_k = pyevm.World.restore, pyevm.keccak
    if fault == 'norollback':
        def restore(self, snap):
            t = self.transient; orig_restore(self, snap); self.transient = t
        pyevm.World.restore = restore
    if fault == 'keccak32':
        pyevm.keccak = lambda d: orig_k(bytes(d[:32]))
    PROBE = 0xabcd0029
    W = pyevm.World({PROBE: T.probe()})
    ok, ret = W.call(0x1234, PROBE, 0, T.w(0), False, 0)
    wd = [int.from_bytes(ret[32 * i:32 * i + 32], 'big') for i in range(len(ret) // 32)]
    got = {'slot0': wd[0], 'slot1': wd[1], 'slot2': wd[2], 'slot3': wd[3], 'child1ok': wd[16], 'child2ok': wd[17]}
    res[fault] = {'got': {k: hex(v) for k, v in got.items()}, 'matchesExpected': got == T.expect_b()}
    pyevm.World.restore, pyevm.keccak = orig_restore, orig_k
    print(fault, res[fault])
json.dump(res, open(sys.argv_out, 'w'), indent=1)
