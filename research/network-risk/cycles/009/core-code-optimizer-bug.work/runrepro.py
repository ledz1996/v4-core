"""Run the Solidity team's reproducer of SOL-2026-7 in the reference interpreter for three builds."""
import sys, json
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from pyevm import World
from evm import keccak
out = {}
for name in ['default', 'noLE', 'legacy']:
    d = json.load(open(f'repro.{name}.json'))['contracts']['C']
    code = bytes.fromhex(d['runtime']); sel = bytes.fromhex(d['ids']['g(uint256,uint256,uint256,uint256)'])
    res = {}
    for args in [(0, 2, 0xaaaa, 0xbbbb), (1, 3, 0xaaaa, 0xbbbb), (0, 1, 0xaaaa, 0xbbbb)]:
        w = World({0xC0: code}, {})
        ok, ret = w.call(0x1111, 0xC0, 0, sel + b''.join(x.to_bytes(32, 'big') for x in args), False, 0)
        res[str(args)] = (ok, ret.hex())
    out[name] = res
    print(name, res)
json.dump(out, open('repro.results.json', 'w'), indent=1)
