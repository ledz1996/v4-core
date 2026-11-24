"""Read-only probe: gas a special address consumes when the PoolManager calls it.

A small driver is placed by state override at each network's PoolManager address
(so the callee sees msg.sender == PoolManager). The driver makes one CALL or
STATICCALL with a fixed gas allowance and returns (success, gas used across the
call, returndatasize, returndata). Nothing is deployed, no transaction is sent.
Usage: python3 calleegas.py out.json [chainId ...]
"""
import json, sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools', 'opdiff'))
from evm import assemble, rpc  # noqa

NETS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'state', 'networks.json')))['networks']

DRV = assemble([
    ('PUSH', 128), 'CALLDATASIZE', 'SUB',
    'DUP1', ('PUSH', 128), 'PUSH0', 'CALLDATACOPY',
    'PUSH0', 'CALLDATALOAD', ('PUSH', 1), 'EQ', ('REF', 'st'), 'JUMPI',
    'GAS', 'PUSH0', 'PUSH0', 'DUP4', 'PUSH0', ('PUSH', 96), 'CALLDATALOAD', ('PUSH', 32), 'CALLDATALOAD',
    ('PUSH', 64), 'CALLDATALOAD', 'CALL', 'GAS', ('REF', 'done'), 'JUMP',
    ('LABEL', 'st'),
    'GAS', 'PUSH0', 'PUSH0', 'DUP4', 'PUSH0', ('PUSH', 32), 'CALLDATALOAD',
    ('PUSH', 64), 'CALLDATALOAD', 'STATICCALL', 'GAS',
    ('LABEL', 'done'),
    'SWAP1', ('PUSH', 0x1000), 'MSTORE', 'SWAP1', 'SUB', ('PUSH', 0x1020), 'MSTORE',
    'RETURNDATASIZE', ('PUSH', 0x1040), 'MSTORE',
    'RETURNDATASIZE', 'PUSH0', ('PUSH', 0x1060), 'RETURNDATACOPY',
    'RETURNDATASIZE', ('PUSH', 0x60), 'ADD', ('PUSH', 0x1000), 'RETURN',
])

FWD = 1_000_000
VICTIM = 0x00000000000000000000000000000000000beef1
FROM = '0x00000000000000000000000000000000000f0f0f'


def w(x):
    return x.to_bytes(32, 'big')


def payloads(pm):
    pmi = int(pm, 16)
    sel = lambda s: bytes.fromhex(s)
    return {
        'call_empty_v0': (0, 0, b''),
        'call_empty_v1': (0, 1, b''),
        'call_transfer': (0, 0, sel('a9059cbb') + w(VICTIM) + w(1)),
        'static_balanceOf': (1, 0, sel('70a08231') + w(pmi)),
        'call_beforeSwap': (0, 0, sel('575e24b4') + b'\0' * 0x1e0),
    }


R = lambda a, b: [hex(x) for x in range(a, b + 1)]
H = lambda h: '0x' + h.rjust(40, '0')
COMMON = [H(hex(i)[2:]) for i in range(1, 0x12)] + [H('100'), H('dead00000000000000000000000000000000beef')]
OPS = [H('42' + '0' * 36 + hex(i)[2:].rjust(2, '0')) for i in list(range(0, 0x31)) + [0x42, 0xff]] + [H('4200000000000000000000000000000000000' + '7ff')]
FAM = {
    'op': OPS,
    'base': OPS + [H('8130' + '0' * 32 + 'aa0' + str(i)) for i in range(4)],
    'celo': OPS + [H('fd'), H('fc'), H('fe'), H('ff')],
    'arb': [H(hex(i)[2:]) for i in list(range(0x64, 0x74)) + [0xc8, 0xff]] + [H('a4b05')],
    'bor': [H(hex(i)[2:]) for i in list(range(0x1000, 0x1009)) + list(range(0x2000, 0x2007)) + [0x3000, 0x1010]],
    'avax': ['0x0100' + '0' * 34 + hex(i)[2:].rjust(2, '0') for i in range(3)] + ['0x0200' + '0' * 34 + hex(i)[2:].rjust(2, '0') for i in range(6)],
    'monad': [H('1000'), H('1001'), H('1002'), H('1003')],
    'mega': ['0x6342' + '0' * 34 + hex(i)[2:].rjust(2, '0') for i in range(6)],
    'tempo': ['0xfeec000000000000000000000000000000000000', '0x403c000000000000000000000000000000000000',
              '0x20fc000000000000000000000000000000000000', '0xdec0000000000000000000000000000000000000',
              '0x4e4f4e4345000000000000000000000000000000', '0xcccccccc00000000000000000000000000000000',
              '0xaaaaaaaa00000000000000000000000000000000', '0xcccccccc00000000000000000000000000000001',
              '0xfdc0000000000000000000000000000000000000', '0x5165300000000000000000000000000000000000',
              '0xb10c000000000000000000000000000000000000', '0x1060000000000000000000000000000000000000',
              '0xc077e00000000000000000000000000000000000', '0xaacc000000000000000000000000000000000000',
              '0x20c0000000000000000000000000000000000000'],
    'arc': ['0x18' + '0' * 37 + str(i) for i in range(10)] + ['0x3600000000000000000000000000000000000000'],
    'hyper': [H(hex(i)[2:]) for i in range(0x800, 0x814)] + ['0x' + '22' * 20, '0x' + '33' * 20, '0x' + '55' * 20],
}
CHAINFAM = {10: 'op', 8453: 'base', 130: 'op', 7777777: 'op', 480: 'op', 57073: 'op', 1868: 'op', 42220: 'celo', 196: 'op',
            42161: 'arb', 4663: 'arb', 99901: 'arb', 137: 'bor', 56: 'bor', 43114: 'avax', 143: 'monad', 4326: 'mega',
            4217: 'tempo', 5042: 'arc', 999: 'hyper', 1: None}


def probe(url, pm, target, mode, value, data, txgas=3_000_000):
    cd = w(mode) + w(int(target, 16)) + w(FWD) + w(value) + data
    tx = {'from': FROM, 'to': pm, 'data': '0x' + cd.hex(), 'gas': hex(txgas)}
    ov = {pm: {'code': '0x' + DRV.hex()}}
    if value:
        ov[pm]['balance'] = hex(10 ** 18)
    for k in range(3):
        try:
            r = bytes.fromhex(rpc(url, 'eth_call', [tx, 'latest', ov])[2:])
            return {'ok': int.from_bytes(r[0:32], 'big'), 'used': int.from_bytes(r[32:64], 'big'),
                    'rds': int.from_bytes(r[64:96], 'big'), 'rd': r[96:96 + 68].hex()}
        except Exception as e:  # noqa
            err = str(e)[:200]; time.sleep(1.5 * (k + 1))
    return {'error': err}


def main():
    out = sys.argv[1]
    want = [int(x) for x in sys.argv[2:]] or [n['chainId'] for n in NETS]
    res = json.load(open(out)) if os.path.exists(out) else {}
    for n in NETS:
        cid = n['chainId']
        if cid not in want:
            continue
        fam = CHAINFAM.get(cid)
        targets = COMMON + (FAM[fam] if fam else [])
        pl = payloads(n['poolManager'])
        rows = {}
        for t in targets:
            rows[t] = {k: probe(n['rpc'], n['poolManager'], t, *v) for k, v in pl.items()}
        res[str(cid)] = {'name': n['name'], 'rpc': n['rpc'], 'pm': n['poolManager'], 'fwd': FWD, 'rows': rows}
        json.dump(res, open(out, 'w'), indent=1)
        heavy = [(t, k, r.get('used'), r.get('ok')) for t, rr in rows.items() for k, r in rr.items()
                 if r.get('used', 0) > 100_000 or 'error' in r]
        print(cid, n['name'], 'targets', len(targets), 'heavy/err', heavy[:40], flush=True)


if __name__ == '__main__':
    main()
