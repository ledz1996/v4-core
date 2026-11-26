"""Run a CREATE2-deployer init code in the reference EVM (tools/opdiff/pyevm.py) as the stranger's replay would run it:
code address = the CREATE2 address, CALLER = 0x4e59b448 (the deployer contract), no value. Prints the storage it writes and
whether the returned runtime equals the runtime on chain. A constructor that reads ORIGIN, CHAINID, TIMESTAMP or makes a call
raises or is reported. usage: ctor.py <raw/init_*.hex with salt prefix> <hook> <runtime json chain>"""
import sys, json
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import pyevm
inp = bytes.fromhex(open(sys.argv[1]).read()); init = inp[32:]; H = int(sys.argv[2], 16)
D = 0x4e59b44847b379578588920ca78fbf26c0b4956c
w = pyevm.World({H: init})
ok, ret = w.call(D, H, 0, b'', False, 1)
seen = {pyevm.NAMES.get(o, hex(o)): c for o, c in w.ops.items() if o in (0x32, 0x33, 0x46, 0x42, 0x43, 0xf1, 0xfa, 0xf4, 0x31, 0x3b, 0x47)}
st = {hex(s): hex(v) for (a, s), v in w.storage.items() if a == H}
out = {'ok': ok, 'runtimeLen': len(ret), 'storage': st, 'envOpsExecuted': seen}
if len(sys.argv) > 3:
    rt = json.load(open('raw/runtimes.json'))
    import hashlib
    out['runtimeSha256'] = hashlib.sha256(ret).hexdigest(); out['matchesChain'] = {c: v['sha256'] == out['runtimeSha256'] for c, v in rt['hooks'][sys.argv[2]].items()}
    open('raw/ctor_runtime_%s.hex' % sys.argv[2][:10], 'w').write(ret.hex())
json.dump(out, open('raw/ctor_%s.json' % sys.argv[2][:10], 'w'), indent=1)
print(json.dumps(out))
