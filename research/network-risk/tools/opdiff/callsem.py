"""Call, value and rollback semantics on every network, by one eth_call with a state override.

The PoolManager's custody logic rests on a few rules outside arithmetic: a reverted call undoes its transient and
persistent writes, a static call cannot write (also through a nested call), return data has the size the callee
gave and a copy past its end fails, and a call with value moves exactly that many wei or fails without moving any.
A probe contract runs one small test per rule against two helper contracts and returns one word per test.

Usage: python3 callsem.py <out.json> [chainId ...]
"""
import sys, json, time, concurrent.futures as cf
from evm import assemble, rpc, networks, OPC

OPC.setdefault('BALANCE', 0x31)
PROBE = 0x00000000000000000000000000000000c0ffee0b
H = 0x00000000000000000000000000000000c0ffee0c
H2 = 0x00000000000000000000000000000000c0ffee0d
EOA = 0x00000000000000000000000000000000c0ffee0e      # no code, no balance
FROM = '0x00000000000000000000000000000000000a11ce'
START = 10 ** 18
A = lambda x: '0x%040x' % x


def helper():
    return assemble([
        ('PUSH', 0), 'CALLDATALOAD', 'DUP1', ('REF', 'set'), 'JUMPI', 'POP',
        ('PUSH', 1), 'TLOAD', ('PUSH', 0), 'MSTORE', ('PUSH', 1), 'SLOAD', ('PUSH', 0x20), 'MSTORE',
        'CALLVALUE', ('PUSH', 0x40), 'MSTORE', 'CALLER', ('PUSH', 0x60), 'MSTORE', ('PUSH', 0x80), ('PUSH', 0), 'RETURN',
        ('LABEL', 'set'), 'DUP1', ('PUSH', 0xbad), 'EQ', ('REF', 'bad'), 'JUMPI', 'DUP1', ('PUSH', 0xdead), 'EQ', ('REF', 'inv'), 'JUMPI',
        'DUP1', ('PUSH', 1), 'TSTORE', 'DUP1', ('PUSH', 1), 'SSTORE', ('PUSH', 0), 'MSTORE',
        ('PUSH', 0x20), 'CALLDATALOAD', ('REF', 'rev'), 'JUMPI', ('PUSH', 0x20), ('PUSH', 0), 'RETURN',
        ('LABEL', 'rev'), ('PUSH', 5), ('PUSH', 0), 'REVERT',
        ('LABEL', 'bad'), ('PUSH', 1), ('PUSH', 0), ('PUSH', 0), 'RETURNDATACOPY', 'STOP',
        ('LABEL', 'inv'), 'INVALID'])


def forwarder():
    return assemble(['CALLDATASIZE', ('PUSH', 0), ('PUSH', 0), 'CALLDATACOPY',
                     ('PUSH', 0), ('PUSH', 0), 'CALLDATASIZE', ('PUSH', 0), ('PUSH', 0), ('PUSHN', 20, H), 'GAS', 'CALL',
                     ('PUSH', 0), 'MSTORE', ('PUSH', 0x20), ('PUSH', 0), 'RETURN'])


def probe():
    p = []; labels = []; exp = []

    def out(label, expected):
        p.extend([('PUSH', 0x400 + 32 * len(labels)), 'MSTORE']); labels.append(label); exp.append(expected)

    def call(op, to, w0=0, w1=0, value=0, gas=None, insize=0x40):
        for off in (0x100, 0x120, 0x140, 0x160): p.extend([('PUSH', 0), ('PUSH', off), 'MSTORE'])
        p.extend([('PUSH', w0), ('PUSH', 0), 'MSTORE', ('PUSH', w1), ('PUSH', 0x20), 'MSTORE'])
        p.extend([('PUSH', 0x80), ('PUSH', 0x100), ('PUSH', insize), ('PUSH', 0)])
        if op == 'CALL': p.append(('PUSH', value))
        p.extend([('PUSHN', 20, to), ('PUSH', gas or 300000), op])   # a fixed allowance: a failing callee burns all the gas it was given

    rds = lambda: p.append('RETURNDATASIZE')
    mem = lambda off: p.extend([('PUSH', off), 'MLOAD'])

    p.extend(['SELFBALANCE']); out('balance of the probe at the start', START)
    call('CALL', H, 5); out('call that writes 5 succeeds', 1)
    call('CALL', H); out('read call succeeds', 1); rds(); out('its return data size', 0x80)
    mem(0x100); out('transient word after the write', 5); mem(0x120); out('storage word after the write', 5)
    mem(0x140); out('value seen by the callee', 0); mem(0x160); out('caller seen by the callee', PROBE)
    call('CALL', H, 9, 1); out('call that writes 9 and reverts fails', 0); rds(); out('return data size of the revert', 5)
    mem(0x100); out('first word of the revert data, 5 bytes copied', (9 >> 216) << 216)
    call('CALL', H); 'POP' and p.append('POP'); mem(0x100); out('transient word after the reverted write', 5); mem(0x120); out('storage word after the reverted write', 5)
    call('STATICCALL', H, 3); out('static call that writes fails', 0); rds(); out('its return data size', 0)
    call('STATICCALL', H); out('static read succeeds', 1); mem(0x100); out('transient word after the static write', 5)
    call('STATICCALL', H2, 8); out('static call to the forwarder succeeds', 1); mem(0x100); out('nested write under a static call fails', 0)
    call('CALL', H); p.append('POP'); mem(0x100); out('transient word after the nested static write', 5)
    call('CALL', H2, 8); p.append('POP'); mem(0x100); out('nested write under a plain call succeeds', 1)
    call('CALL', H); p.append('POP'); mem(0x100); out('transient word after the nested write', 8); mem(0x160); out('caller seen directly', PROBE)
    call('CALL', H, 0xbad); out('copy of return data past its end fails', 0); rds(); out('return data size after that failure', 0)
    call('CALL', H, 0xdead, gas=60000); out('invalid instruction with 60,000 gas fails', 0); rds(); out('return data size after it', 0)
    call('CALL', H); p.append('POP'); mem(0x100); out('transient word after the two failures', 8)
    call('DELEGATECALL', H, 4); out('delegate call that writes 4 succeeds', 1)
    p.extend([('PUSH', 1), 'TLOAD']); out('transient word of the probe after the delegate call', 4)
    p.extend([('PUSH', 1), 'SLOAD']); out('storage word of the probe after the delegate call', 4)
    call('CALL', H); p.append('POP'); mem(0x100); out('transient word of the helper is untouched', 8)
    call('CALL', EOA, value=12345, insize=0); out('value call to an empty account succeeds', 1); rds(); out('its return data size', 0)
    p.extend([('PUSHN', 20, EOA), 'BALANCE']); out('balance of the empty account after 12,345 wei', 12345)
    p.extend(['SELFBALANCE']); out('balance of the probe after paying 12,345 wei', START - 12345)
    call('CALL', EOA, value=2 * START, insize=0); out('value call above the balance fails', 0); rds(); out('its return data size', 0)
    p.extend(['SELFBALANCE']); out('balance of the probe after the failed payment', START - 12345)
    call('CALL', H, value=7); out('value call to the helper succeeds', 1); mem(0x140); out('value seen by the helper', 7)
    p.extend([('PUSHN', 20, H), 'BALANCE']); out('balance of the helper after 7 wei', 7)
    call('CALL', H, 6, 1, value=11); out('value call that reverts fails', 0)
    p.extend([('PUSHN', 20, H), 'BALANCE']); out('balance of the helper after the reverted payment', 7)
    p.extend(['SELFBALANCE']); out('balance of the probe at the end', START - 12345 - 7)
    call('CALL', 4, 0x1122, 0x3344, insize=37); out('identity precompile call succeeds', 1); rds(); out('its return data size', 37)
    mem(0x100); out('identity returns the input', 0x1122)
    call('CALL', PROBE + 0x100, insize=0); out('call to an address without code succeeds', 1); rds(); out('its return data size', 0)
    p.extend([('PUSH', 32 * len(labels)), ('PUSH', 0x400), 'RETURN'])
    return assemble(p), labels, exp


def run(nw):
    cid, name, url = nw; code, labels, exp = probe()
    ov = {A(PROBE): {'code': '0x' + code.hex(), 'balance': hex(START)}, A(H): {'code': '0x' + helper().hex()}, A(H2): {'code': '0x' + forwarder().hex()}}
    last = None
    for k in range(5):
        try:
            r = bytes.fromhex(rpc(url, 'eth_call', [{'from': FROM, 'to': A(PROBE), 'gas': hex(5_000_000)}, 'latest', ov], timeout=60)[2:]); break
        except Exception as e:  # noqa
            last = str(e)[:200]; time.sleep(3 * (k + 1))
    else:
        return cid, name, None, last
    got = [int.from_bytes(r[32 * i:32 * i + 32], 'big') for i in range(len(labels))]
    return cid, name, got, None


if __name__ == '__main__':
    out = sys.argv[1]; only = set(map(int, sys.argv[2:]))
    code, labels, exp = probe(); results = {}
    with cf.ThreadPoolExecutor(8) as ex:
        for cid, name, got, err in ex.map(run, [n for n in networks() if not only or n[0] in only]):
            diff = [] if got is None else [{'test': labels[i], 'expected': hex(exp[i]), 'got': hex(got[i])} for i in range(len(labels)) if got[i] != exp[i]]
            results[cid] = {'name': name, 'error': err, 'different': diff}
            print(f'{cid:>8} {name:16} {"ERR " + err if err else str(len(labels) - len(diff)) + "/" + str(len(labels)) + " as specified"}', flush=True)
            for d in diff: print('           ', d)
    json.dump({'tests': labels, 'expected': [hex(e) for e in exp], 'results': results}, open(out, 'w'), indent=1)
