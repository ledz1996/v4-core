"""Nested-frame transient and persistent storage sequences over the PoolManager's slot shapes, run in the reference
EVM (tools/opdiff/pyevm.py) and by eth_call with code overrides on an endpoint. Read-only. Seed 3204.
Four frames F0..F3 at fixed addresses; each frame stores, loads, calls the next frame by CALL, DELEGATECALL or
STATICCALL and ends by RETURN, REVERT or INVALID. F0 records every load, every call flag and the keccak of every
return buffer, then reads all slots of the pool and returns its record.
usage: python3 -I journal_seq.py <url> <n> <out.json> [batch]"""
import json, random, sys, time, urllib.request
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import pyevm
from evm import keccak
URL, N, OUT = sys.argv[1], int(sys.argv[2]), sys.argv[3]; BATCH = int(sys.argv[4]) if len(sys.argv) > 4 else 25
F = [0xc0de0000 + i for i in range(4)]
def kw(*ws):
    k = keccak(b''.join(w.to_bytes(32, 'big') for w in ws)); return int.from_bytes(k, 'big') if isinstance(k, (bytes, bytearray)) else k
CUR = [0, 0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48, 0xb2000000000000000000002feb517dfec7415344]
TGT = [F[0], 0x66a9893cc07d91d95644aedd05d03f95e1dba8af, 0x1234]
SLOTS = [0xc090fc4683624cfc3884e9d8de5eca132f2d0ec062aff75d43c0465d5ceeab23,  # Lock.sol:8
         0x7d4b3164c6e45b97e7d87b7125a44c5828d005af88f9d751cfd78729c5d99a0b,  # NonzeroDeltaCount.sol:9-10
         0x1e0745a7db1623981f0b2a5d4232364c00787266eb75ad546f190e6cebe9bd95,  # CurrencyReserves.sol:11
         0x27e098c505d44ec3574004bca052aabf76bd35004c182099d8c575fb238593b9]  # CurrencyReserves.sol:13
SLOTS += [kw(t, c) for t in TGT for c in CUR]  # CurrencyDelta.sol:10-17
pk = kw(0x1111, 6); SLOTS += [pk, pk + 1, pk + 2, pk + 3, 6, 0]  # pool state shapes (StateLibrary POOLS_SLOT 6)
def push(v):
    b = v.to_bytes(max(1, (v.bit_length() + 7) // 8), 'big'); return bytes([0x5f + len(b)]) + b if v else b'\x5f'
class Gen:
    def __init__(s, rnd): s.r = rnd
    def frame(s, depth, rec_base):
        r = s.r; c = bytearray(); off = rec_base
        def rec_top():  # store stack top at off
            nonlocal off; c.extend(push(off) + b'\x52'); off += 32
        slots = r.sample(SLOTS, 5)
        for _ in range(r.randint(2, 7)):
            a = r.random(); sl = r.choice(slots)
            val = r.choice([0, 1, r.getrandbits(256), (1 << 255) | r.getrandbits(64), r.getrandbits(128)])
            if a < .3: c.extend(push(val) + push(sl) + b'\x5d')
            elif a < .45: c.extend(push(val) + push(sl) + b'\x55')
            elif a < .65: c.extend(push(sl) + b'\x5c'); rec_top()
            elif a < .75: c.extend(push(sl) + b'\x54'); rec_top()
            elif depth < 3:
                kind = r.choice([0xf1, 0xf4, 0xfa])
                tgt = F[depth + 1]
                gas = push([4_000_000, 800_000, 200_000][depth])  # fixed gas so a halting callee cannot starve the caller
                if kind == 0xf1: c.extend(b'\x5f\x5f\x5f\x5f\x5f' + push(tgt) + gas + b'\xf1')
                else: c.extend(b'\x5f\x5f\x5f\x5f' + push(tgt) + gas + bytes([kind]))
                rec_top()
                # keccak of the return buffer: RETURNDATACOPY(0x4000, 0, size); KECCAK256(0x4000, size)
                c.extend(b'\x3d\x5f' + push(0x4000) + b'\x3e' + b'\x3d' + push(0x4000) + b'\x20'); rec_top()
        return c, off
    def program(s):
        r = s.r; codes = {}
        for d in range(3, 0, -1):
            body, off = s.frame(d, 0)
            end = r.choice(['ret', 'ret', 'rev', 'inv', 'stop'])
            if end == 'ret': body.extend(push(off) + b'\x5f\xf3')
            elif end == 'rev': body.extend(push(off) + b'\x5f\xfd')
            elif end == 'inv': body.extend(b'\xfe')
            else: body.extend(b'\x00')
            codes[F[d]] = bytes(body)
        body, off = s.frame(0, 0)
        for sl in SLOTS:
            body.extend(push(sl) + b'\x5c' + push(off) + b'\x52'); off += 32
            body.extend(push(sl) + b'\x54' + push(off) + b'\x52'); off += 32
        body.extend(push(off) + b'\x5f\xf3')
        codes[F[0]] = bytes(body)
        return codes
def ref(codes):
    w = pyevm.World(codes)
    ok, ret = w.call(0xca11e4, F[0], 0, b'', False, 0)
    return ok, bytes(ret)
def rpc(payload):
    for attempt in range(5):
        try:
            r = urllib.request.Request(URL, json.dumps(payload).encode(), {'Content-Type': 'application/json', 'User-Agent': 'curl/8'})
            return json.load(urllib.request.urlopen(r, timeout=90))
        except Exception as e:
            err = str(e); time.sleep(3 + 5 * attempt)
    return {'error': err}
res = {'url': URL, 'seed': 3204, 'n': N, 'clientVersionBefore': rpc({'jsonrpc': '2.0', 'id': 0, 'method': 'web3_clientVersion', 'params': []}),
       'cases': 0, 'equal': 0, 'mismatches': [], 'rpcErrors': 0, 'refFailures': 0}
rnd = random.Random(3204); g = Gen(rnd)
progs = [g.program() for _ in range(N)]
for i in range(0, N, BATCH):
    chunk = progs[i:i + BATCH]
    payload = [{'jsonrpc': '2.0', 'id': i + j, 'method': 'eth_call', 'params': [
        {'from': '0x' + '%040x' % 0xca11e4, 'to': '0x%040x' % F[0], 'gas': hex(20_000_000)}, 'latest',
        {('0x%040x' % a): {'code': '0x' + c.hex()} for a, c in p.items()}]} for j, p in enumerate(chunk)]
    ans = rpc(payload); time.sleep(float(__import__('os').environ.get('PAUSE', '1.2')))
    if isinstance(ans, dict): ans = [ans] * len(chunk)
    byid = {a.get('id'): a for a in ans if isinstance(a, dict)}
    for j, p in enumerate(chunk):
        res['cases'] += 1
        ok, ret = ref(p)
        if not ok: res['refFailures'] += 1
        a = byid.get(i + j, {})
        if 'result' not in a:
            res['rpcErrors'] += 1
            if res['rpcErrors'] <= 5: res.setdefault('rpcErrorSamples', []).append(a)
            continue
        if bytes.fromhex(a['result'][2:]) == ret: res['equal'] += 1
        else: res['mismatches'].append({'index': i + j, 'codes': {hex(k): v.hex() for k, v in p.items()}, 'node': a['result'], 'reference': ret.hex()})
res['clientVersionAfter'] = rpc({'jsonrpc': '2.0', 'id': 0, 'method': 'web3_clientVersion', 'params': []})
json.dump(res, open(OUT, 'w'))
print(OUT, res['clientVersionBefore'].get('result'), 'cases', res['cases'], 'equal', res['equal'], 'mismatch', len(res['mismatches']), 'rpcErrors', res['rpcErrors'], 'refFail', res['refFailures'])
