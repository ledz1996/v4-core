"""Task 3: native take and settle probes by eth_call with state overrides at the real PoolManager address.
A driver at a fresh address (code and balance by override) calls unlock; in the callback it runs a list of items, each
[2 byte length][20 byte target][32 byte value][20 byte watch][calldata], records (success, return data, balance of the
PoolManager, balance of watch) after each, and ends by reverting with the record, so nothing persists and nothing is
settled. The outer frame returns the record. Read-only: eth_call only. usage: probe.py <out.json>"""
import sys, os, json, time
HERE = os.path.dirname(os.path.abspath(__file__)); NR = '/home/user/v4-core/research/network-risk'
sys.path.insert(0, os.path.join(NR, 'tools', 'opdiff')); sys.path.insert(0, HERE)
from evm import assemble, keccak
from rpc import batch, call
def sel(s): return keccak(s.encode())[:4]
def w(x): return (x % (1 << 256)).to_bytes(32, 'big')
DRV = 0x00000000000000000000000000000000d21fe0aa
NETS = {'arc-official': ('https://rpc.mainnet.arc.io', 0x8366a39CC670B4001A1121B8F6A443A643e40951),
        'arc-drpc': ('https://arc.drpc.org', 0x8366a39CC670B4001A1121B8F6A443A643e40951),
        }

def driver(pm):
    p = [('PUSH', 0), 'CALLDATALOAD', ('PUSH', 224), 'SHR', ('PUSHN', 4, int.from_bytes(sel('unlockCallback(bytes)'), 'big')), 'EQ', ('REF', 'cb'), 'JUMPI',
         ('PUSHN', 4, int.from_bytes(sel('unlock(bytes)'), 'big')), ('PUSH', 224), 'SHL', ('PUSH', 0), 'MSTORE',
         ('PUSH', 0x20), ('PUSH', 4), 'MSTORE', 'CALLDATASIZE', ('PUSH', 36), 'MSTORE',
         'CALLDATASIZE', ('PUSH', 0), ('PUSH', 68), 'CALLDATACOPY',
         ('PUSH', 0), ('PUSH', 0), 'CALLDATASIZE', ('PUSH', 100), 'ADD', ('PUSH', 0), ('PUSH', 0), ('PUSHN', 20, pm), 'GAS', 'CALL',
         'POP', 'RETURNDATASIZE', ('PUSH', 0), ('PUSH', 0), 'RETURNDATACOPY', 'RETURNDATASIZE', ('PUSH', 0), 'RETURN',
         ('LABEL', 'cb'), ('PUSH', 0x4000), ('PUSH', 68),  # ptr, outp
         ('LABEL', 'loop'), 'DUP1', 'CALLDATALOAD', ('PUSH', 240), 'SHR',  # len, ptr, outp
         'DUP1', 'ISZERO', ('REF', 'end'), 'JUMPI',
         'DUP1', 'DUP3', ('PUSH', 74), 'ADD', ('PUSH', 0), 'CALLDATACOPY',  # calldatacopy(0, ptr+74, len)
         ('PUSH', 0), ('PUSH', 0), 'DUP3', ('PUSH', 0),  # 0 len 0 0 | len ptr outp  -> argsOff=0 argsLen=len retOff=0 retLen=0
         'DUP6', ('PUSH', 22), 'ADD', 'CALLDATALOAD',  # value
         'DUP7', ('PUSH', 2), 'ADD', 'CALLDATALOAD', ('PUSH', 96), 'SHR',  # target
         ('PUSHN', 3, 3_000_000), 'CALL',  # ok, len, ptr, outp (3,000,000 gas per item, so a callee that burns its gas cannot starve later items)
         'DUP4', 'MSTORE',
         'RETURNDATASIZE', 'DUP4', ('PUSH', 32), 'ADD', 'MSTORE',
         ('PUSHN', 20, pm), ('RAW', b'\x31'), 'DUP4', ('PUSH', 64), 'ADD', 'MSTORE',
         'DUP2', ('PUSH', 54), 'ADD', 'CALLDATALOAD', ('PUSH', 96), 'SHR', ('RAW', b'\x31'), 'DUP4', ('PUSH', 96), 'ADD', 'MSTORE',
         'RETURNDATASIZE', ('PUSH', 0), 'DUP5', ('PUSH', 128), 'ADD', 'RETURNDATACOPY',
         'SWAP2', ('PUSH', 128), 'ADD', 'RETURNDATASIZE', 'ADD', 'SWAP2',
         ('PUSH', 74), 'ADD', 'ADD',
         ('REF', 'loop'), 'JUMP',
         ('LABEL', 'end'), 'POP', 'POP',
         ('PUSH', 0x4000), 'SWAP1', 'SUB', ('PUSH', 0x4000), 'REVERT']
    return assemble(p)

def item(target, value, watch, data): return len(data).to_bytes(2, 'big') + target.to_bytes(20, 'big') + w(value)[:32] + watch.to_bytes(20, 'big') + data
def parse(buf):
    out = []; i = 0
    while i + 128 <= len(buf):
        ok, n, bpm, bw = (int.from_bytes(buf[i + k:i + k + 32], 'big') for k in (0, 32, 64, 96))
        out.append({'ok': ok, 'ret': '0x' + buf[i + 128:i + 128 + n].hex(), 'pmBal': bpm, 'watchBal': bw}); i += 128 + n
    return out
S_TAKE = sel('take(address,address,uint256)'); S_SETTLE = sel('settle()'); S_SYNC = sel('sync(address)')
def take(to, amt): return S_TAKE + w(0) + w(to) + w(amt)
PLAIN = 0xc0ffee0000000000000000000000000000000001; REV = 0xc0ffee0000000000000000000000000000000002
BURN = 0xc0ffee0000000000000000000000000000000003; LISTED = 0xc0ffee0000000000000000000000000000000004
SD = 0xc0ffee0000000000000000000000000000000005; BENEF = 0xc0ffee0000000000000000000000000000000006
NCC = (0x18 << 152) + 1
def blslot(a): return '0x' + keccak(a.to_bytes(32, 'big') + (2).to_bytes(32, 'big')).hex()
TARGETS = [('plain', PLAIN), ('reverts', REV), ('burns-gas', BURN), ('blocklisted-by-override', LISTED), ('zero', 0),
           ('ecrecover', 1), ('sha256', 2), ('identity', 4), ('p256verify-0x100', 0x100), ('arc-0x1800..00', 0x18 << 152),
           ('arc-0x1800..01', NCC), ('arc-0x1800..02', (0x18 << 152) + 2), ('arc-0x1800..03', (0x18 << 152) + 3),
           ('arc-usdc-0x3600', 0x36 << 152), ('poolmanager-itself', None), ('selfdestructed-in-tx', SD)]

def scripts(pm, full):
    out = []
    for name, t in TARGETS:
        t = pm if t is None else t
        its = []
        if name == 'selfdestructed-in-tx': its.append(item(SD, 0, SD, b'\x01'))  # SD's code self-destructs to BENEF when called
        for amt in (0, 1, full - 1):
            its.append(item(pm, 0, t, take(t, amt)))
        out.append((name, b''.join(its) + b'\0\0'))
    # settle paths with value: settle{1}, sync(0) then settle{1}, settle{0}
    its = [item(pm, 1, DRV, S_SETTLE), item(pm, 1, DRV, S_SYNC + w(0)), item(pm, 1, DRV, S_SETTLE), item(pm, 0, DRV, S_SETTLE),
           item(pm, 1, DRV, take(PLAIN, 2))]
    out.append(('settle-with-value', b''.join(its) + b'\0\0'))
    return out

def run(net, blk):
    url, pm = NETS[net]
    full = int(call(url, 'eth_getBalance', ['0x%040x' % pm, hex(blk)]), 16)
    drv = driver(pm)
    ov = {'0x%040x' % DRV: {'code': '0x' + drv.hex(), 'balance': hex(10 ** 24)},
          '0x%040x' % REV: {'code': '0x5f5ffd'}, '0x%040x' % BURN: {'code': '0x5b5f56'},
          '0x%040x' % SD: {'code': '0x73' + '%040x' % BENEF + 'ff'}}
    if net.startswith('arc'): ov['0x%040x' % NCC] = {'stateDiff': {blslot(LISTED): '0x' + '0' * 63 + '1'}}
    sc = scripts(pm, full)
    res = {'net': net, 'url': url, 'block': blk, 'pmBalance': full, 'scripts': {}}
    for name, data in sc:
        reqs = [('web3_clientVersion', [])] + ([('arc_getVersion', [])] if net.startswith('arc') else []) + \
               [('eth_call', [{'from': '0x%040x' % DRV, 'to': '0x%040x' % DRV, 'data': '0x' + data.hex(), 'gas': hex(25_000_000)}, hex(blk), ov]),
                ('eth_blockNumber', [])] + [('web3_clientVersion', [])]
        try:
            r = batch(url, reqs)
            raw = r[-3]
            res['scripts'][name] = {'client': r[0], 'arcVersion': r[1] if net.startswith('arc') else None, 'block': int(r[-2], 16), 'clientAfter': r[-1], 'items': parse(bytes.fromhex(raw[2:]))}
        except Exception as e:
            res['scripts'][name] = {'error': str(e)[:300]}
        time.sleep(0.5)
    return res

if __name__ == '__main__':
    a = int(call(NETS['arc-official'][0], 'eth_blockNumber', []), 16); b = int(call(NETS['arc-drpc'][0], 'eth_blockNumber', []), 16)
    pin = {'arc-official': min(a, b) - 10, 'arc-drpc': min(a, b) - 10}
    out = {n: run(n, pin[n]) for n in NETS}
    json.dump(out, open(sys.argv[1], 'w'), indent=1)
    for name, _ in TARGETS + [('settle-with-value', 0)]:
        row = []
        for n in NETS:
            s = out[n]['scripts'].get(name, {})
            row.append('ERR' if 'error' in s else ''.join(str(x['ok']) for x in s['items']))
        print(f'{name:26}', row)
