"""Read-only: how much gas a callee receives when the PoolManager forwards gas() (Hooks.sol:134, Currency.sol:48/73).
Driver at the PoolManager address calls a probe contract with gas = 2**255 (all allowed); the probe returns
the GAS it sees. The driver also returns GAS just before the CALL, so the ratio is child/parent."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools', 'opdiff'))
from evm import assemble, rpc
NETS = {n['chainId']: n for n in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'state', 'networks.json')))['networks']}
PROBE = '0x00000000000000000000000000000000000c0de6'
callee = assemble(['GAS', 'PUSH0', 'MSTORE', ('PUSH', 32), 'PUSH0', 'RETURN'])
drv = assemble(['PUSH0', 'PUSH0', 'PUSH0', 'PUSH0', 'PUSH0', ('PUSH', int(PROBE, 16)), 'GAS', ('PUSH', 0x40), 'MSTORE',
                ('PUSH', 1 << 255), 'CALL', 'POP', ('PUSH', 32), 'PUSH0', 'PUSH0', 'RETURNDATACOPY',
                ('PUSH', 0x40), 'MLOAD', ('PUSH', 32), 'MSTORE', ('PUSH', 64), 'PUSH0', 'RETURN'])
out = {}
for cid in [int(x) for x in sys.argv[2:]]:
    n = NETS[cid]
    try:
        r = bytes.fromhex(rpc(n['rpc'], 'eth_call', [{'from': '0x00000000000000000000000000000000000f0f0f', 'to': n['poolManager'], 'gas': hex(2_000_000)}, 'latest',
                                                       {n['poolManager']: {'code': '0x' + drv.hex()}, PROBE: {'code': '0x' + callee.hex()}}])[2:])
        child, parent = int.from_bytes(r[:32], 'big'), int.from_bytes(r[32:64], 'big')
        out[cid] = {'name': n['name'], 'parentGasBeforeCall': parent, 'childGasAtStart': child, 'ratio': child / parent}
    except Exception as e:
        out[cid] = {'name': n['name'], 'error': str(e)[:200]}
    print(cid, out[cid], flush=True)
json.dump(out, open(sys.argv[1], 'w'), indent=1)
