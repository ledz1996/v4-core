"""Task 1 (a) and (b): nested write-and-fail probe for transient (TSTORE/TLOAD) and persistent (SSTORE/SLOAD) storage.

One contract P is placed by state override at address PADDR and called through eth_call. Calldata words:
 0 op (unused, 0), 1 level L of this frame, 2 failing level d, 3 kind, 4 stype (0 transient, 1 persistent), 5 base slot.
Level 0 (the parent) writes base+i = 0xAA00+i for i = 1..4, then calls level 1. A frame at level L >= 1 writes
base+L = 0x1000+L and, while L <= d, calls level L+1. Level d is entered by STATICCALL for kind 4 and with 300,000 gas
for kind 3. After its child returns, level d ends by kind: 0 STOP (control), 1 REVERT, 2 INVALID, 3 an endless loop
(runs out of gas), 4 STOP (reached only if the static write was wrongly allowed). Level d+1 writes and returns, so a
successful write inside the failing frame is checked as well. The parent then returns [ok of level 1, base+1..base+4].

The reference is tools/opdiff/pyevm.py on the same code and calldata; it has no gas, so kind 3 is run there as kind 2
(both are exceptional halts that undo the frame). Read-only: eth_call with a code override, nothing is sent.
usage: python3 -I nested.py <out.json> <chainId> <url> [<url> ...]
"""
import sys, json, time, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from rpcu import rpc, version
from evm import assemble
import pyevm as PE

PADDR = 0x00000000000000000000000000000000_7e57_0320
EOA = 0x00000000000000000000000000000000000c0de1
_n = [0]
def lab(s): _n[0] += 1; return f'{s}{_n[0]}'
def cd(i): return [('PUSH', 32 * i), 'CALLDATALOAD']
def write():  # stack: val slot(top) -> ()
    a, b = lab('ss'), lab('wd')
    return cd(4) + [('REF', a), 'JUMPI', 'TSTORE', ('REF', b), 'JUMP', ('LABEL', a), 'SSTORE', ('LABEL', b)]
def read():  # stack: slot -> val
    a, b = lab('sl'), lab('rd')
    return cd(4) + [('REF', a), 'JUMPI', 'TLOAD', ('REF', b), 'JUMP', ('LABEL', a), 'SLOAD', ('LABEL', b)]

def code():
    p = []
    p += cd(1) + [('REF', 'notop'), 'JUMPI']
    for i in range(1, 5): p += [('PUSH', 0xAA00 + i)] + cd(5) + [('PUSH', i), 'ADD'] + write()
    p += [('REF', 'child'), 'JUMP']
    p += [('LABEL', 'notop')] + cd(1) + [('PUSH', 0x1000), 'ADD'] + cd(1) + cd(5) + ['ADD'] + write()
    # if L > d: return
    p += cd(2) + cd(1) + ['GT', ('REF', 'ret'), 'JUMPI']
    p += [('LABEL', 'child'), 'CALLDATASIZE', ('PUSH', 0), ('PUSH', 0), 'CALLDATACOPY', cd(1)[0], cd(1)[1], ('PUSH', 1), 'ADD', ('PUSH', 0x20), 'MSTORE']
    # isfail = (L+1 == d)
    p += cd(1) + [('PUSH', 1), 'ADD'] + cd(2) + ['EQ', ('PUSH', 0x400), 'MSTORE']
    # gas: kind==3 && isfail ? 300000 : GAS
    p += [('PUSH', 0x400), 'MLOAD'] + cd(3) + [('PUSH', 3), 'EQ', 'AND', ('REF', 'lowgas'), 'JUMPI', 'GAS', ('REF', 'gasok'), 'JUMP',
          ('LABEL', 'lowgas'), ('PUSH', 300000), ('LABEL', 'gasok'), ('PUSH', 0x420), 'MSTORE']
    p += [('PUSH', 0x400), 'MLOAD'] + cd(3) + [('PUSH', 4), 'EQ', 'AND', ('REF', 'st'), 'JUMPI']
    p += [('PUSH', 0), ('PUSH', 0), 'CALLDATASIZE', ('PUSH', 0), ('PUSH', 0), 'ADDRESS', ('PUSH', 0x420), 'MLOAD', 'CALL', ('REF', 'called'), 'JUMP']
    p += [('LABEL', 'st'), ('PUSH', 0), ('PUSH', 0), 'CALLDATASIZE', ('PUSH', 0), 'ADDRESS', ('PUSH', 0x420), 'MLOAD', 'STATICCALL']
    p += [('LABEL', 'called'), ('PUSH', 0x500), 'MSTORE']
    # parent: output
    p += cd(1) + [('REF', 'inner'), 'JUMPI']
    for i in range(1, 5): p += cd(5) + [('PUSH', i), 'ADD'] + read() + [('PUSH', 0x500 + 32 * i), 'MSTORE']
    p += [('PUSH', 0xa0), ('PUSH', 0x500), 'RETURN']
    # inner: if L == d end by kind
    p += [('LABEL', 'inner')] + cd(1) + cd(2) + ['EQ', 'ISZERO', ('REF', 'ret'), 'JUMPI']
    p += cd(3) + [('PUSH', 1), 'EQ', ('REF', 'k1'), 'JUMPI'] + cd(3) + [('PUSH', 2), 'EQ', ('REF', 'k2'), 'JUMPI'] + cd(3) + [('PUSH', 3), 'EQ', ('REF', 'k3'), 'JUMPI']
    p += [('LABEL', 'ret'), 'STOP', ('LABEL', 'k1'), ('PUSH', 0), ('PUSH', 0), 'REVERT', ('LABEL', 'k2'), 'INVALID', ('LABEL', 'k3'), ('REF', 'k3'), 'JUMP']
    return assemble(p)

CODE = code()
def w(x): return x.to_bytes(32, 'big')
def data(d, kind, stype, base): return w(0) + w(0) + w(d) + w(kind) + w(stype) + w(base)
def ref(d, kind, stype, base):
    wld = PE.World({PADDR: CODE})
    ok, ret = wld.call(EOA, PADDR, 0, data(d, 2 if kind == 3 else kind, stype, base), False, 0)
    return ok, ret.hex()

def cases():
    for stype in (0, 1):
        for kind in (0, 1, 2, 3, 4):
            for d in (1, 2, 3):
                yield d, kind, stype, 0x5157 + 0x100 * (stype * 100 + kind * 10 + d)

def run(url, chain):
    res = {'url': url, 'chain': chain, 'before': version(url, chain), 'cases': []}
    blk = rpc(url, 'eth_getBlockByNumber', ['latest', False]); res['block'] = (blk.get('result') or {}).get('number')
    bn = res['block'] or 'latest'
    for d, kind, stype, base in cases():
        rok, rret = ref(d, kind, stype, base)
        tx = {'from': '0x%040x' % EOA, 'to': '0x%040x' % PADDR, 'data': '0x' + data(d, kind, stype, base).hex(), 'gas': hex(2_000_000)}
        r = rpc(url, 'eth_call', [tx, bn, {'0x%040x' % PADDR: {'code': '0x' + CODE.hex()}}])
        if 'result' in r: nok, nret = True, r['result'][2:]
        else: nok, nret = False, None
        rec = {'d': d, 'kind': kind, 'stype': stype, 'base': base, 'ref': [rok, rret], 'node': r if 'result' not in r else [nok, nret], 'equal': (nok, nret) == (rok, rret)}
        res['cases'].append(rec)
    res['after'] = version(url, chain)
    res['nEqual'] = sum(c['equal'] for c in res['cases']); res['n'] = len(res['cases'])
    res['mismatch'] = [c for c in res['cases'] if not c['equal']]
    return res

if __name__ == '__main__':
    out = []
    for u in sys.argv[3:]:
        r = run(u, int(sys.argv[2])); out.append(r)
        print(sys.argv[2], u, r['before']['web3_clientVersion'].get('result'), 'equal', r['nEqual'], '/', r['n'], 'after', r['after']['web3_clientVersion'].get('result'))
        for m in r['mismatch'][:3]: print('  MISMATCH', json.dumps(m)[:400])
    json.dump(out, open(sys.argv[1], 'w'), indent=1)
