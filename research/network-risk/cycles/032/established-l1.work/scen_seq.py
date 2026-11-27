"""Cycle 29 stablecoin-l1, lead L-1179, for endpoints that serve neither eth_simulateV1 nor eth_callMany
(rpc.mainnet.arc.io): each scen28.py scenario is sent as one eth_call to a sequencer stub placed by state override, which
makes the scenario's transactions one after another as sub-calls (same order, same targets, same calldata) and returns
(success, return length, return bytes) of each. The same stub runs in tools/opdiff/pyevm.py on the same state, and the two
outputs are compared byte for byte. Differences from scen_rpc.py: the caller of each step is the stub instead of the EOA,
and transient storage is not cleared between steps; both runs share these differences, so the comparison stays exact.
Read-only. Usage: python3 scen_seq.py <out.json> <url> [names...]"""
import sys, os, json, hashlib
S28 = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '028',
                                   'theme-monad-native-unentered-blocks.work', 'scripts'))
sys.path.insert(0, S28)
import scen28 as X  # noqa: E402
from evm import rpc, assemble  # noqa: E402

SEQ = 0x0000000000000000000000000000000000005e95
VIN, VOUT, BUF = 0x40000, 0x40020, 0x40040
NOT31 = ((1 << 256) - 1) ^ 31
P = lambda v: ('PUSH', v)  # noqa: E731
STUB = assemble([
    ('LABEL', 'loop'),
    'CALLDATASIZE', P(VIN), 'MLOAD', 'LT', 'ISZERO', ('REF', 'end'), 'JUMPI',
    P(VIN), 'MLOAD', P(32), 'ADD', 'CALLDATALOAD',
    'DUP1', P(VIN), 'MLOAD', P(64), 'ADD', P(BUF), 'CALLDATACOPY',
    P(0), P(0), 'DUP3', P(BUF), P(0), P(VIN), 'MLOAD', 'CALLDATALOAD', 'GAS', 'CALL',
    P(VOUT), 'MLOAD', 'MSTORE',
    'RETURNDATASIZE', P(VOUT), 'MLOAD', P(32), 'ADD', 'MSTORE',
    'RETURNDATASIZE', P(0), P(VOUT), 'MLOAD', P(64), 'ADD', 'RETURNDATACOPY',
    'RETURNDATASIZE', P(31), 'ADD', P(NOT31), 'AND', P(64), 'ADD', P(VOUT), 'MLOAD', 'ADD', P(VOUT), 'MSTORE',
    P(31), 'ADD', P(NOT31), 'AND', P(64), 'ADD', P(VIN), 'MLOAD', 'ADD', P(VIN), 'MSTORE',
    ('REF', 'loop'), 'JUMP',
    ('LABEL', 'end'), P(VOUT), 'MLOAD', P(0), 'RETURN'])


def w(x): return (x % (1 << 256)).to_bytes(32, 'big')


def enc(sc):
    b = b''
    for t in sc['txs']:
        d = bytes.fromhex(t['data'])
        b += w(X.addr(t['to'])) + w(len(d)) + d + b'\0' * ((-len(d)) % 32)
    return b


def split(ret):
    out = []; i = 0
    while i < len(ret):
        ok = int.from_bytes(ret[i:i + 32], 'big'); n = int.from_bytes(ret[i + 32:i + 64], 'big')
        out.append((ok, ret[i + 64:i + 64 + n].hex())); i += 64 + n + ((-n) % 32)
    return out


def main():
    out, url = sys.argv[1], sys.argv[2]; names = sys.argv[3:] or list(X.SCEN)
    res = {'url': url, 'stub': STUB.hex(), 'clientBefore': rpc(url, 'web3_clientVersion', [], 20),
           'block': int(rpc(url, 'eth_blockNumber', [], 20), 16), 'scenarios': {}}
    tot = {'scen': 0, 'same': 0, 'diff': 0, 'err': 0, 'steps': 0, 'stepsOk': 0}
    for nm in names:
        sc = X.SCEN[nm]
        cs = X.codes_for(X.PM, [sc['key']]); cs.update({int(a, 16): bytes.fromhex(b) for a, b in sc.get('codes', {}).items()})
        cs[SEQ] = STUB
        wd = X.P.World(cs)
        for k, v in sc['storage'].items(): wd.storage[(X.PM, int(k, 16))] = int(v, 16)
        data = enc(sc)
        rok, rret = wd.call(X.EOA, SEQ, 0, data, False, 0)
        so = {'0x%040x' % a: {'code': '0x' + b.hex()} for a, b in cs.items()}
        if sc['storage']:
            so['0x%040x' % X.PM]['stateDiff'] = {'0x%064x' % int(k, 16): '0x%064x' % int(v, 16) for k, v in sc['storage'].items()}
        r = {'ntx': len(sc['txs']), 'refOk': bool(rok), 'refHash': hashlib.sha256(rret).hexdigest()}
        steps = split(rret); r['refSteps'] = [s[0] for s in steps]
        tot['scen'] += 1; tot['steps'] += len(steps); tot['stepsOk'] += sum(s[0] for s in steps)
        try:
            got = rpc(url, 'eth_call', [{'from': '0x%040x' % X.EOA, 'to': '0x%040x' % SEQ, 'data': '0x' + data.hex(),
                                         'gas': hex(150_000_000)}, 'latest', so], timeout=180)
            g = bytes.fromhex(got[2:])
            r['same'] = g == rret
            if not r['same']:
                gs = split(g)
                r['firstDiff'] = next((i for i, (a, b) in enumerate(zip(steps, gs)) if a != b), min(len(steps), len(gs)))
                r['gotSteps'] = [s[0] for s in gs]
            tot['same' if r['same'] else 'diff'] += 1
        except Exception as e:  # noqa
            r['error'] = str(e)[:300]; tot['err'] += 1
        res['scenarios'][nm] = r
        print(nm, r.get('same'), r['refSteps'], r.get('error', '')[:150], r.get('firstDiff', ''), flush=True)
    res['clientAfter'] = rpc(url, 'web3_clientVersion', [], 20); res['totals'] = tot
    print('TOTAL', tot, flush=True)
    json.dump(res, open(out, 'w'), indent=1)


if __name__ == '__main__':
    main()
