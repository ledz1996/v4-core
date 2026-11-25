"""L-587 part 2: values placed in the backing state by override (storage of one account, balances of many
accounts whose addresses differ in several bits), read back with SLOAD and BALANCE, so the read goes
through the node's state lookup and not only the in-call journal. Read-only eth_call."""
import sys, json, random, urllib.request, time
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import evm
from evm import assemble, MASK
evm.OPC['BALANCE'] = 0x31
ns = {}; exec(open('/home/user/v4-core/research/network-risk/cycles/017/hyperevm.work/foldprobe.py').read().split('K = keys()')[0], ns)
K = ns['keys']()[:300]
A = '0x00000000000000000000000000000000000f01d0'
def rpc(u, m, p):
    for i in range(4):
        r = urllib.request.Request(u, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": m, "params": p}).encode(), headers={'content-type': 'application/json', 'user-agent': 'probe'})
        try:
            j = json.load(urllib.request.urlopen(r, timeout=60))
            return j['result'] if 'result' in j else {'error': j['error']}
        except Exception as e: err = str(e); time.sleep(3)
    return {'err': err}
def reader(op):
    p = [('PUSH', 0), ('LABEL', 'r'), 'DUP1', 'CALLDATASIZE', 'GT', 'ISZERO', ('REF', 'end'), 'JUMPI', 'DUP1', 'CALLDATALOAD', op, 'DUP2', 'MSTORE', ('PUSH', 32), 'ADD', ('REF', 'r'), 'JUMP', ('LABEL', 'end'), 'POP', 'CALLDATASIZE', ('PUSH', 0), 'RETURN']
    return '0x' + assemble(p).hex()
h = lambda x: '0x' + x.to_bytes(32, 'big').hex()
R = random.Random(5872); addrs = []
for _ in range(30):
    b = R.getrandbits(160)
    for v in (b, b ^ ((1 << 160) - 1 ^ ((1 << 64) - 1)), b ^ (((1 << 64) - 1) << 96), b ^ (0xff << 152 | 0xff), b ^ ((1 << 32) - 1) << 128 ^ ((1 << 32) - 1), int.from_bytes(b.to_bytes(20, 'big')[::-1], 'big')):
        if v not in addrs and v > 0x10000: addrs.append(v)
res = {}
for u in sys.argv[2:]:
    ov = {A: {'code': reader('SLOAD'), 'stateDiff': {h(k): h(i + 1) for i, k in enumerate(K)}}}
    out = rpc(u, 'eth_call', [{'to': A, 'data': '0x' + b''.join(k.to_bytes(32, 'big') for k in K).hex(), 'gas': '0x1c9c380'}, 'latest', ov])
    s_bad = [i for i in range(len(K)) if not isinstance(out, str) or int(out[2 + 64 * i:66 + 64 * i], 16) != i + 1]
    ov2 = {A: {'code': reader('BALANCE')}}
    for i, a in enumerate(addrs): ov2['0x' + a.to_bytes(20, 'big').hex()] = {'balance': hex(10 ** 6 + i)}
    out2 = rpc(u, 'eth_call', [{'to': A, 'data': '0x' + b''.join(a.to_bytes(32, 'big') for a in addrs).hex(), 'gas': '0x1c9c380'}, 'latest', ov2])
    b_bad = [i for i in range(len(addrs)) if not isinstance(out2, str) or int(out2[2 + 64 * i:66 + 64 * i], 16) != 10 ** 6 + i]
    res[u] = {'storageKeys': len(K), 'storageMismatch': len(s_bad), 'storageErr': None if isinstance(out, str) else out, 'addresses': len(addrs), 'balanceMismatch': len(b_bad), 'balanceErr': None if isinstance(out2, str) else out2}
    print(u, res[u], flush=True)
json.dump(res, open(sys.argv[1], 'w'), indent=1)
