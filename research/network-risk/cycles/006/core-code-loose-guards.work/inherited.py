# Inherited caller test: the runner sits at the PoolManager address (state override), calls a stub, and the stub forwards
# transfer(sink, 1) to an enshrined token by DELEGATECALL or CALLCODE. Does the token act for the PoolManager? Read-only eth_call.
import json, os
from lib import *
from asm import assemble, OPS
from stubs import RUNNER
OPS['CALLCODE'] = 0xf2
def fwd(token, op):
    args = '0 0 CALLDATASIZE 0 %s GAS DELEGATECALL' % token if op == 'DELEGATECALL' else '0 0 CALLDATASIZE 0 0 %s GAS CALLCODE' % token
    return assemble('CALLDATASIZE 0 0 CALLDATACOPY\n' + args + '\nRETURNDATASIZE 0 0 RETURNDATACOPY\n@ok JUMPI\nRETURNDATASIZE 0 REVERT\nok:\nRETURNDATASIZE 0 RETURN')
C1 = '0x7e57000000000000000000000000000000000c11'; C2 = '0x7e57000000000000000000000000000000000c12'
SINK = '0x7e57000000000000000000000000000000000505'; FROM = '0x7e57000000000000000000000000000000000a00'
CASES = [(4217, '0x20c0000000000000000000000000000000000000'), (8453, '0xb2000000000000000000002feb517dfec7415344'), (8453, '0xb2000000000000000000000d8ce462e99ee7a47b')]
out = []
for cid, T in CASES:
    n = net(cid); u = n['rpc']; pm = n['poolManager']
    b = lambda a: item(T, cd('balanceOf(address)', a))
    x = cd('transfer(address,uint256)', SINK, 1)
    sc = script(0, [b(pm), b(SINK), item(C1, x), b(pm), b(SINK), item(C2, x), b(pm), b(SINK), item(C1, cd('balanceOf(address)', pm)), item(C2, cd('balanceOf(address)', pm)), item(T, x), b(pm), b(SINK)])
    blk = rpc(u, 'eth_blockNumber', [])['result']
    r = rpc(u, 'eth_call', [{'from': FROM, 'to': pm, 'data': '0x' + sc}, blk, {pm: {'code': RUNNER}, C1: {'code': fwd(T, 'DELEGATECALL')}, C2: {'code': fwd(T, 'CALLCODE')}}])
    recs = [short(ok, d) for ok, d in records(r['result'])] if 'result' in r else [json.dumps(r)[:300]]
    names = ['bal PM', 'bal sink', 'DELEGATECALL transfer(sink,1)', 'bal PM', 'bal sink', 'CALLCODE transfer(sink,1)', 'bal PM', 'bal sink', 'DELEGATECALL balanceOf(PM)', 'CALLCODE balanceOf(PM)', 'direct transfer(sink,1)', 'bal PM', 'bal sink']
    row = {'chainId': cid, 'token': T, 'block': int(blk, 16), 'records': dict(zip(['%02d %s' % (i, s) for i, s in enumerate(names)], recs)) if len(recs) == len(names) else recs}
    out.append(row); print(json.dumps(row, indent=1))
json.dump(out, open(os.path.join(HERE, 'raw', 'inherited.json'), 'w'), indent=1)
