"""Second read-only probe. Checks on the deployed PoolManagers the two statements that the repository's tests
pin only when a test runs as one transaction: the lock is closed when unlock returns (PoolManager.sol:113) and
settle resets the synced currency (PoolManager.sol:361). eth_call with a state override only."""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import probe as p

IS_UNLOCKED = int('c090fc4683624cfc3884e9d8de5eca132f2d0ec062aff75d43c0465d5ceeab23', 16)
CURRENCY_SLOT = int('27e098c505d44ec3574004bca052aabf76bd35004c182099d8c575fb238593b9', 16)

def stub2_code(manager):
    M = int(manager, 16)
    P = lambda v, n=None: ('push', v, n) if n else ('push', v)
    ext = int.from_bytes(p.sel('exttload(bytes32)'), 'big')
    take0 = p.cd('take(address,address,uint256)', p.CUR, p.STUB, 0)   # 100 bytes
    prog = [
        P(M, 20), 'CALLER', 'EQ', P('cb'), 'JUMPI',
        # entry: 1) forward calldata (an unlock call)
        'CALLDATASIZE', P(0), P(0x1000, 2), 'CALLDATACOPY',
        P(0), P(0), 'CALLDATASIZE', P(0x1000, 2), P(0), P(M, 20), 'GAS', 'CALL',
        P(0), 'MSTORE',
        # 2) exttload(IS_UNLOCKED_SLOT) after unlock returned; result word to mem[0x20]
        P(ext << 224, 32), P(0x800, 2), 'MSTORE',
        P(IS_UNLOCKED, 32), P(0x804, 2), 'MSTORE',
        P(0x20), P(0x20), P(0x24), P(0x800, 2), P(0), P(M, 20), 'GAS', 'CALL', 'POP',
        # 3) take(CUR, STUB, 0) after unlock returned; success to mem[0x40], first return word to mem[0x60]
    ]
    for i in range(0, 128, 32):
        chunk = (take0 + b'\x00' * 28)[i:i + 32]
        prog += [P(int.from_bytes(chunk, 'big'), 32), P(0x900 + i, 2), 'MSTORE']
    prog += [
        P(0x20), P(0x60), P(100), P(0x900, 2), P(0), P(M, 20), 'GAS', 'CALL',
        P(0x40), 'MSTORE',
        P(0x80), P(0), 'RETURN',
        ('label', 'cb'),
    ]
    # callback part identical to probe.stub_code: reuse by assembling the same loop
    prog += [
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
        P(0x20), P(0x200, 2), 'DUP3', P(0), P(0), P(M, 20), 'GAS', 'CALL',
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

ext = lambda slot: p.cd('exttload(bytes32)', slot)
# The stub answers balanceOf(address) from the manager with the word 0x20, so it can stand in as a currency for sync.
R_SEQ = [ext(IS_UNLOCKED), p.cd('sync(address)', p.STUB), ext(CURRENCY_SLOT), p.cd('settle()'), ext(CURRENCY_SLOT), p.cd('settle()')]

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    nets = json.load(open(os.path.join(here, '..', '..', '..', 'state', 'networks.json')))
    if isinstance(nets, dict): nets = nets.get('networks', nets)
    res = {}
    for n in nets:
        url, pm = n['rpc'], n['poolManager']
        blk = p.rpc(url, 'eth_blockNumber', []).get('result') or 'latest'
        o = {'name': n['name'], 'block': blk}
        # A: sequence R through the first stub, records returned through unlock
        r = p.rpc(url, 'eth_call', [{'from': p.FROM, 'to': p.STUB, 'data': '0x' + p.unlock_call(R_SEQ).hex()}, blk,
                                    {p.STUB: {'code': '0x' + p.stub_code(pm).hex()}}])
        o['R'] = r.get('result') if 'result' in r else {'error': r.get('error')}
        # B: empty unlock through the second stub, then lock flag and a take after unlock returned
        r = p.rpc(url, 'eth_call', [{'from': p.FROM, 'to': p.STUB, 'data': '0x' + p.unlock_call([]).hex()}, blk,
                                    {p.STUB: {'code': '0x' + stub2_code(pm).hex()}}])
        o['afterUnlock'] = r.get('result') if 'result' in r else {'error': r.get('error')}
        res[str(n['chainId'])] = o
        print(n['chainId'], n['name'], blk, flush=True)
    json.dump(res, open(os.path.join(here, 'raw', 'probe2_results.json'), 'w'), indent=1)

if __name__ == '__main__':
    main()
