"""Stack edge vectors for the interpreter refactor of Monad v0.16.6/v0.16.7 (StackTop, a one-past
stack pointer, in category/vm/interpreter/stack.hpp, stack_top.hpp, instruction_table.hpp dup/swap,
call_runtime.hpp). Each case is a test contract placed by state override and called from a driver
that returns the success flag and the return data, so failures are compared too.
Cases: DUPn and SWAPn for n = 1..16 at exactly the needed depth and one short; pushes to a depth of
1014..1025 followed by DUP1, DUP16, SWAP16; runtime calls that read stack arguments (MSTORE, MLOAD,
KECCAK256, CALLDATACOPY, RETURNDATACOPY) at the bottom and the top of a deep stack.
Usage: python3 stackedge.py <out.json> [chainId ...]"""
import sys, os, json, random, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools', 'opdiff'))
from evm import rpc, networks, keccak

DRV = '0x00000000000000000000000000000000c0de0d01'
TST = '0x00000000000000000000000000000000c0de0d02'
M = (1 << 256) - 1

def push(v):
    b = v.to_bytes(32, 'big').lstrip(b'\x00') or b'\x00'
    if v == 0: return bytes([0x5f])
    return bytes([0x5f + len(b)]) + b

def ret_top(k):
    out = b''
    for j in range(k):
        out += push(32 * j) + bytes([0x52])  # MSTORE(offset=32j, value=top)
    return out + push(32 * k) + push(0) + bytes([0xf3])

def driver():
    # CALL(gas, TST, 0, 0, calldatasize?, 0, 0); copy returndata; return success || returndata
    c = bytes([0x5f, 0x5f, 0x5f, 0x5f, 0x5f]) + push(int(TST, 16)) + bytes([0x5a, 0xf1])  # success
    c += push(0) + bytes([0x52])  # mstore(0, success)
    c += bytes([0x3d, 0x5f]) + push(32) + bytes([0x3e])  # returndatacopy(32, 0, rds)
    c += bytes([0x3d]) + push(32) + bytes([0x01]) + push(0) + bytes([0xf3])
    return c

def cases(rnd):
    out = []
    vals = lambda n: [rnd.getrandbits(256) for _ in range(n)]
    for n in range(1, 17):
        for d in (n, n - 1):
            v = vals(d)
            code = b''.join(push(x) for x in v) + bytes([0x7f + n]) + ret_top(min(d + 1, 17))
            st = list(v)
            exp = None
            if d >= n:
                st.append(st[-n]); exp = b''.join(x.to_bytes(32, 'big') for x in reversed(st[-(min(d + 1, 17)):]))
            out.append(('DUP%d depth %d' % (n, d), code, exp))
        for d in (n + 1, n):
            v = vals(d)
            code = b''.join(push(x) for x in v) + bytes([0x8f + n]) + ret_top(min(d, 17))
            exp = None
            if d >= n + 1:
                st = list(v); st[-1], st[-1 - n] = st[-1 - n], st[-1]
                exp = b''.join(x.to_bytes(32, 'big') for x in reversed(st[-min(d, 17):]))
            out.append(('SWAP%d depth %d' % (n, d), code, exp))
    for d in list(range(1014, 1026)):
        for op, need, inc in (('DUP1', 1, 1), ('DUP16', 16, 1), ('SWAP16', 17, 0), ('none', 0, 0)):
            v = [(i * 0x9e3779b97f4a7c15 + 1) & M for i in range(d)]
            body = b''.join(push(x) for x in v)
            if op != 'none':
                body += bytes([{'DUP1': 0x80, 'DUP16': 0x8f, 'SWAP16': 0x9f}[op]])
            code = body + ret_top(17)
            st = list(v); exp = None
            ok = d >= need and d + inc + 1 <= 1024  # ret_top pushes one offset word
            if ok:
                if op == 'DUP1': st.append(st[-1])
                if op == 'DUP16': st.append(st[-16])
                if op == 'SWAP16': st[-1], st[-17] = st[-17], st[-1]
                exp = b''.join(x.to_bytes(32, 'big') for x in reversed(st[-17:]))
            out.append(('%s after %d pushes' % (op, d), code, exp))
    # runtime calls reading stack arguments at depth: keccak of memory, mload, calldatacopy, returndatacopy
    for d in (0, 1, 500, 1018, 1019):
        filler = b''.join(push(i + 7) for i in range(d))
        data = bytes(rnd.getrandbits(8) for _ in range(96))
        code = filler
        for j in range(3):
            code += push(int.from_bytes(data[32 * j:32 * j + 32], 'big')) + push(32 * j) + bytes([0x52])
        code += push(96) + push(0) + bytes([0x20])  # keccak(0, 96)
        code += push(32) + bytes([0x51])  # mload(32)
        code += push(5) + push(3) + push(200) + bytes([0x37])  # calldatacopy(200, 3, 5) of empty calldata -> zeros
        code += push(200) + bytes([0x51])
        code += ret_top(3)
        # stack before ret_top: [..filler, keccak, mload32, mload200]; d + 3 <= 1024 always here except d=1019? 1022 ok
        exp = (0).to_bytes(32, 'big') + data[32:64] + keccak(data)
        need_ok = d + 3 <= 1024 and d + 2 + 3 <= 1024  # transient pushes of 3 args for calldatacopy
        out.append(('runtime args after %d pushes' % d, code, exp if need_ok else None))
    return out

def run(url, cs):
    res = []
    for name, code, exp in cs:
        ov = {DRV: {'code': '0x' + driver().hex()}, TST: {'code': '0x' + code.hex()}}
        for k in range(8):
            try:
                r = bytes.fromhex(rpc(url, 'eth_call', [{'to': DRV, 'gas': hex(20_000_000)}, 'latest', ov], timeout=60)[2:]); break
            except Exception:
                time.sleep(2 + 3 * k)
        else:
            raise RuntimeError('rpc failed')
        ok = int.from_bytes(r[:32], 'big'); data = r[32:]
        want_ok = 1 if exp is not None else 0
        match = (ok == want_ok) and (ok == 0 or data == exp)
        res.append({'case': name, 'ok': ok, 'match': match, 'len': len(data)})
    return res

if __name__ == '__main__':
    out = sys.argv[1]; only = set(map(int, sys.argv[2:]))
    cs = cases(random.Random(13_4326))
    summary = {'cases': len(cs), 'results': []}
    for cid, name, url, *_ in networks():
        if only and cid not in only: continue
        r = run(url, cs)
        bad = [x for x in r if not x['match']]
        summary['results'].append({'chainId': cid, 'name': name, 'ran': len(r), 'mismatches': bad})
        print(cid, name, 'ran', len(r), 'mismatches', len(bad), [b['case'] for b in bad][:8], flush=True)
    json.dump(summary, open(out, 'w'), indent=1)
