# Walk unlock, sync, settle and take with a delegated EOA (EIP-7702 designator placed by state override) as transaction sender.
# Read only. The deployed PoolManager is used, so the result shows how mainnet executes the call pattern.
import json; from lib import *; from stubs import RUNNER, designator
URL='https://ethereum-rpc.publicnode.com'; PM='0x000000000004444c5dc75cB358380D2e3dE08A90'
E='0x'+keccak256(b'cycle-008-delegated-eoa')[12:].hex(); R='0x'+keccak256(b'cycle-008-runner')[12:].hex()
ORIGINP=assemble_src='' 
from asm import assemble
# probe target: returns ORIGIN, CALLER
WHO='0x'+keccak256(b'cycle-008-who')[12:].hex()
WHOCODE=assemble('ORIGIN 0 MSTORE CALLER 0x20 MSTORE 0x40 0 RETURN')
items=[item(WHO,''),
       item(PM,cd('sync(address)',0)),
       item(PM,sel('settle()'),1000),
       item(PM,cd('exttload(bytes32)',delta_slot(E,0))),
       item(PM,cd('take(address,address,uint256)',0,E,1000)),
       item(PM,cd('exttload(bytes32)',NONZERO)),
       item(PM,cd('exttload(bytes32)',IS_UNLOCKED))]
inner=script(0,items)
ov={E:{'code':designator(R),'balance':hex(10**18)},R:{'code':RUNNER},WHO:{'code':WHOCODE}}
r=rpc(URL,'eth_call',[{'from':E,'to':PM,'data':'0x'+unlock(inner),'gas':hex(3_000_000)},'latest',ov])
print(json.dumps(r)[:300])
if 'result' in r:
    b=bytes.fromhex(r['result'][2:]); n=int.from_bytes(b[32:64],'big'); recs=records(b[64:64+n].hex())
    for (name,rec) in zip(['who(origin,caller)','sync(0)','settle{1000}','delta(E,native)','take(native,E,1000)','nonzeroCount','isUnlocked'],recs): print(name, short(*rec))
print('E',E,'R',R)
# control: same call but E has plain (non delegated) empty code -> unlock must fail because the callback target has no code
r2=rpc(URL,'eth_call',[{'from':E,'to':PM,'data':'0x'+unlock(inner),'gas':hex(3_000_000)},'latest',{E:{'balance':hex(10**18)}}])
print('control without delegation:',json.dumps(r2)[:300])
