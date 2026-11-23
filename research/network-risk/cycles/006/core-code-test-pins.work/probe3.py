"""Third read-only probe (eth_call with state override only). Walks the checks of lead L-217 on every deployed
PoolManager: native value guard after a token sync, native credit after sync(address(0)), exact clear, mint and burn
moving delta and claim by the same amount, and the synced-currency guard of collectProtocolFees.
Each item of a sequence is [2-byte length][32-byte call value][calldata]."""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import probe as p
p.OP['SWAP1'] = 0x90
NONZERO = int('7d4b3164c6e45b97e7d87b7125a44c5828d005af88f9d751cfd78729c5d99a0b', 16)

def stub3_code(manager):
    M = int(manager, 16)
    P = lambda v, n=None: ('push', v, n) if n else ('push', v)
    prog = [
        P(M, 20), 'CALLER', 'EQ', P('cb'), 'JUMPI',
        'CALLDATASIZE', P(0), P(0), 'CALLDATACOPY',
        P(0), P(0), 'CALLDATASIZE', P(0), P(0), P(M, 20), 'GAS', 'CALL',
        P(0), 'MSTORE',
        'RETURNDATASIZE', P(0), P(0x20), 'RETURNDATACOPY',
        'RETURNDATASIZE', P(0x20), 'ADD', P(0), 'RETURN',
        ('label', 'cb'),
        P(0x44), P(0x300, 2), 'MSTORE',
        P(0x24), 'CALLDATALOAD', P(0x44), 'ADD', P(0x320, 2), 'MSTORE',
        P(0x440, 2), P(0x340, 2), 'MSTORE',
        ('label', 'loop'),
        P(0x320, 2), 'MLOAD', P(0x300, 2), 'MLOAD', 'LT', 'ISZERO', P('done'), 'JUMPI',
        P(0x300, 2), 'MLOAD', 'CALLDATALOAD', P(0xf0), 'SHR',
        P(0x300, 2), 'MLOAD', P(2), 'ADD', P(0x300, 2), 'MSTORE',
        'DUP1', P(0x300, 2), 'MLOAD', P(0), 'CALLDATACOPY',
        'DUP1', P(0x300, 2), 'MLOAD', 'ADD', P(0x300, 2), 'MSTORE',
        P(0), P(0x200, 2), 'MSTORE',
        # call(gas, M, mload(0), 0x20, L-0x20, 0x200, 0x20)
        P(0x20), P(0x200, 2), 'DUP3', P(0x20), 'SWAP1', 'SUB', P(0x20), P(0), 'MLOAD', P(M, 20), 'GAS', 'CALL',
        P(0x340, 2), 'MLOAD', 'MSTORE',
        'POP',
        P(0x200, 2), 'MLOAD', P(0x340, 2), 'MLOAD', P(0x20), 'ADD', 'MSTORE',
        P(0x340, 2), 'MLOAD', P(0x40), 'ADD', P(0x340, 2), 'MSTORE',
        P('loop'), 'JUMP',
        ('label', 'done'),
        P(0x20), P(0x400, 2), 'MSTORE',
        P(0x440, 2), P(0x340, 2), 'MLOAD', 'SUB', P(0x420, 2), 'MSTORE',
        P(0x400, 2), P(0x340, 2), 'MLOAD', 'SUB', P(0x400, 2), 'RETURN',
    ]
    return p.assemble(prog)

def unlock3(items):
    data = b''.join((len(c) + 32).to_bytes(2, 'big') + p.w(v) + c for v, c in items)
    return p.sel('unlock(bytes)') + p.w(0x20) + p.w(len(data)) + data + b'\x00' * ((-len(data)) % 32)

def dslot(target, cur):
    return int.from_bytes(p.k(p.w(target) + p.w(cur)), 'big')
ext = lambda s: p.cd('exttload(bytes32)', s)

def seq_main(stub):
    bal = lambda: p.cd('balanceOf(address,uint256)', stub, p.CUR)
    return [
        (0, p.cd('sync(address)', stub)),                          # 0 stub stands in as a token, balanceOf answers 0x20
        (1, p.cd('settle()')),                                     # 1 expect NonzeroNativeValue
        (0, p.cd('sync(address)', 0)),                             # 2
        (1, p.cd('settle()')),                                     # 3 expect ok, returns 1
        (0, ext(dslot(stub, 0))),                                  # 4 expect 1
        (0, p.cd('clear(address,uint256)', 0, 2)),                 # 5 expect MustClearExactPositiveDelta
        (0, p.cd('take(address,address,uint256)', 0, stub, 1)),    # 6 expect ok
        (0, ext(dslot(stub, 0))),                                  # 7 expect 0
        (0, p.cd('mint(address,uint256,uint256)', stub, p.CUR, 5)),# 8
        (0, bal()),                                                # 9 expect 5
        (0, ext(dslot(stub, p.CUR))),                              # 10 expect -5
        (0, ext(NONZERO)),                                         # 11 expect 1
        (0, p.cd('burn(address,uint256,uint256)', stub, p.CUR, 5)),# 12
        (0, bal()),                                                # 13 expect 0
        (0, ext(dslot(stub, p.CUR))),                              # 14 expect 0
        (0, ext(NONZERO)),                                         # 15 expect 0
    ]
def seq_fee(stub):
    return [
        (0, p.cd('sync(address)', stub)),
        (0, p.cd('collectProtocolFees(address,address,uint256)', p.VICT, stub, 0)),   # expect ProtocolFeeCurrencySynced
        (0, p.cd('sync(address)', 0)),
    ]

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    nets = json.load(open(os.path.join(here, '..', '..', '..', 'state', 'networks.json')))
    if isinstance(nets, dict): nets = nets.get('networks', nets)
    res = {}
    for n in nets:
        url, pm = n['rpc'], n['poolManager']
        blk = p.rpc(url, 'eth_blockNumber', []).get('result') or 'latest'
        o = {'name': n['name'], 'block': blk}
        code = '0x' + stub3_code(pm).hex()
        r = p.rpc(url, 'eth_call', [{'from': p.FROM, 'to': p.STUB, 'data': '0x' + unlock3(seq_main(p.STUB)).hex()}, blk,
                                    {p.STUB: {'code': code, 'balance': hex(10**18)}}])
        o['main'] = r.get('result') if 'result' in r else {'error': r.get('error')}
        pfc = (n.get('protocolFeeController') or '').lower()
        o['pfc'] = pfc
        if pfc and int(pfc, 16) != 0:
            r = p.rpc(url, 'eth_call', [{'from': p.FROM, 'to': pfc, 'data': '0x' + unlock3(seq_fee(pfc)).hex()}, blk,
                                        {pfc: {'code': code}}])
            o['fee'] = r.get('result') if 'result' in r else {'error': r.get('error')}
        res[str(n['chainId'])] = o
        print(n['chainId'], n['name'], blk, flush=True)
    json.dump(res, open(os.path.join(here, 'raw', 'probe3_results.json'), 'w'), indent=1)

if __name__ == '__main__':
    main()
