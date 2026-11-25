# Copy, load and hash opcodes with operand offsets around 2^31, 2^32, 2^63 and 2^64, where index arithmetic in
# the node (Go slices on amd64 and arm64) could be wrong. Each vector is one eth_call of a small program by state override.
import sys, os, json, time
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import assemble, call_code, keccak, rpc, OPC
OPC['CODECOPY'] = 0x39
M = 1 << 256
ONLY = set(int(x) for x in sys.argv[2:])
NETS = {137: 'https://rpc-mainnet.matic.quiknode.pro', 56: 'https://bsc-dataseed1.bnbchain.org', 5600: 'https://rpc-bsc.48.club', 5601: 'https://bsc-rpc.publicnode.com', 43114: 'https://api.avax.network/ext/bc/C/rpc'}  # 5600 is the BSC 48.club build, 5601 is reth-bsc
CD = bytes((i * 37 + 11) & 0xff for i in range(100))
OFFS = [0, 1, 31, 36, 68, 99, 100, 2**31 - 1, 2**31, 2**32 - 64, 2**32 - 33, 2**32 - 32, 2**32 - 1, 2**32, 2**32 + 1,
        2**33, 2**63 - 1, 2**63, 2**64 - 64, 2**64 - 1, 2**64, 2**64 + 1, 2**128, M - 64, M - 1]
def ret(n):  # return n bytes from memory 0
    return [('PUSH', n), ('PUSH', 0), 'RETURN']
def prog(kind, o):
    if kind == 'cdload':   return [('PUSH', o), 'CALLDATALOAD', ('PUSH', 0), 'MSTORE'] + ret(32)
    if kind == 'cdcopy':   return [('PUSH', 64), ('PUSH', o), ('PUSH', 0), 'CALLDATACOPY'] + ret(64)
    if kind == 'codecopy': return [('PUSH', 64), ('PUSH', o), ('PUSH', 0), 'CODECOPY'] + ret(64)
    if kind == 'sha0':     return [('PUSH', 0), ('PUSH', o), 'KECCAK256', ('PUSH', 0), 'MSTORE'] + ret(32)
    if kind == 'mcopy0':   return [('PUSH', 0), ('PUSH', o), ('PUSH', (o * 3 + 7) % M), 'MCOPY', ('PUSH', 1), ('PUSH', 0), 'MSTORE'] + ret(32)
    if kind == 'cdcopy0':  return [('PUSH', 0), ('PUSH', 5), ('PUSH', o), 'CALLDATACOPY', ('PUSH', 1), ('PUSH', 0), 'MSTORE'] + ret(32)
    # return data: staticcall identity with 40 bytes of calldata, then copy
    pre = [('PUSH', 40), ('PUSH', 0), ('PUSH', 0), 'CALLDATACOPY',
           ('PUSH', 0), ('PUSH', 0), ('PUSH', 40), ('PUSH', 0), ('PUSH', 4), 'GAS', 'STATICCALL', 'POP',
           ('PUSH', 0), ('PUSH', 0), 'MSTORE', ('PUSH', 0), ('PUSH', 32), 'MSTORE']
    if kind == 'rdcopy8':  return pre + [('PUSH', 8), ('PUSH', o), ('PUSH', 0), 'RETURNDATACOPY'] + ret(64)
    if kind == 'rdcopy0':  return pre + [('PUSH', 0), ('PUSH', o), ('PUSH', 0), 'RETURNDATACOPY', ('PUSH', 1), ('PUSH', 63), 'MSTORE8'] + ret(64)
KINDS = ['cdload', 'cdcopy', 'codecopy', 'sha0', 'mcopy0', 'cdcopy0', 'rdcopy8', 'rdcopy0']
def expect(kind, o, code):
    pad = lambda b, s, n: (b[s:s + n] if s < len(b) else b'') .ljust(n, b'\0')
    if kind == 'cdload': return pad(CD, o, 32) if o < M else None
    if kind == 'cdcopy': return pad(CD, o, 64)
    if kind == 'codecopy': return pad(code, o, 64)
    if kind == 'sha0': return keccak(b'')
    if kind in ('mcopy0', 'cdcopy0'): return (1).to_bytes(32, 'big')
    rd = CD[:40]
    if kind == 'rdcopy8':
        if o + 8 > 40: return 'FAIL'
        return rd[o:o + 8] + b'\0' * 56
    if kind == 'rdcopy0':
        if o > 40: return 'FAIL'
        return b'\0' * 63 + b'\1'
out = {}; bad = 0; n = 0
for cid, url in NETS.items():
    if ONLY and cid not in ONLY: continue
    res = []
    for kind in KINDS:
        for o in OFFS:
            code = assemble(prog(kind, o))
            exp = expect(kind, o, code)
            try:
                got = call_code(url, code, CD, gas=1_000_000).hex()
            except Exception as e:
                got = 'FAIL' if 'out of bounds' in str(e) or 'revert' in str(e).lower() or 'invalid' in str(e).lower() else 'ERR:' + str(e)[:120]
            e = exp if isinstance(exp, str) else exp.hex()
            ok = got == e
            n += 1; bad += (not ok)
            res.append(dict(kind=kind, offset=hex(o), ok=ok, got=got[:140], expected=e[:140]))
            time.sleep(0.15 if cid == 99901 else 0.02)
    out[cid] = res
    print(cid, 'vectors', len(res), 'mismatches', sum(not r['ok'] for r in res), [ (r['kind'], r['offset'], r['got'][:60]) for r in res if not r['ok']][:6])
json.dump(out, open(sys.argv[1], 'w'), indent=0)
print('total', n, 'mismatches', bad)
