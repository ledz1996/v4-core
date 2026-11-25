"""L-669 probe: does the node reuse jump destination analysis keyed by the code hash of an address when the
code is replaced by state override? The real PoolManager code is first executed (warming any cache), then
the PoolManager address is overridden with code whose valid jump targets differ from the real code's.
Read-only eth_call."""
import sys, json, urllib.request, time
PM = '0x12D4Fd9C5DeDd00ab8a0bCe2CF0167bbf94b6B1F'
def rpc(u, m, p):
    for i in range(5):
        r = urllib.request.Request(u, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": m, "params": p}).encode(), headers={'content-type': 'application/json', 'user-agent': 'probe'})
        try:
            j = json.load(urllib.request.urlopen(r, timeout=60))
            return j['result'] if 'result' in j else {'error': j['error'].get('message')}
        except Exception as e: err = str(e); time.sleep(2)
    return {'err': err}
u0 = sys.argv[2]
real = bytes.fromhex(rpc(u0, 'eth_getCode', [PM, 'latest'])[2:])
# real jump destinations
jd = set(); i = 0
while i < len(real):
    op = real[i]
    if op == 0x5b: jd.add(i)
    i += 1 + (op - 0x5f if 0x60 <= op <= 0x7f else 0)
T = sorted(t for t in jd if 40 < t < 2000)[0]  # a real JUMPDEST of the PoolManager
ret1 = bytes.fromhex('600160005260206000f3')  # return 1
# code A: jump to T where T lies inside PUSH32 data in the new code (must fail: InvalidJump)
a = bytearray(b'\x61' + T.to_bytes(2, 'big') + b'\x56')
while len(a) < T + 40: a += b'\x7f' + b'\x5b' * 32
codeA = bytes(a) + b'\x5b' + ret1
# code B: jump to 4, which is not a JUMPDEST in the real code, and is one in the new code (must succeed)
codeB = bytes.fromhex('600456fe5b') + ret1
out = {'realJumpdest': T, 'realIsJumpdest4': 4 in jd, 'endpoints': {}}
for u in sys.argv[2:]:
    o = {}
    o['warm_real'] = rpc(u, 'eth_call', [{'to': PM, 'data': '0x8da5cb5b'}, 'latest'])  # owner()
    o['A_override_pm'] = rpc(u, 'eth_call', [{'to': PM, 'data': '0x'}, 'latest', {PM: {'code': '0x' + codeA.hex()}}])
    o['B_override_pm'] = rpc(u, 'eth_call', [{'to': PM, 'data': '0x'}, 'latest', {PM: {'code': '0x' + codeB.hex()}}])
    o['A_fresh_addr'] = rpc(u, 'eth_call', [{'to': '0x00000000000000000000000000000000000a11ce', 'data': '0x'}, 'latest', {'0x00000000000000000000000000000000000a11ce': {'code': '0x' + codeA.hex()}}])
    o['B_fresh_addr'] = rpc(u, 'eth_call', [{'to': '0x00000000000000000000000000000000000a11ce', 'data': '0x'}, 'latest', {'0x00000000000000000000000000000000000a11ce': {'code': '0x' + codeB.hex()}}])
    out['endpoints'][u] = o; print(u, o, flush=True)
json.dump(out, open(sys.argv[1], 'w'), indent=1)
