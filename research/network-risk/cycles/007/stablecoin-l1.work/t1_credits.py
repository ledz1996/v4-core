# L-264: StorageCredits precompile as a currency on Tempo. Read-only eth_call with state overrides; nothing is sent.
import json
from lib import *
from harness import *
from show import dump
cid=4217; n=net(cid); u=n['rpc']; pm=n['poolManager']
SC='0x1060000000000000000000000000000000000000'; PATH='0x20c0000000000000000000000000000000000000'
H='0x50995539e4afaca479bb59b0d795d94e0efea0cc'   # holds 230765 pathUSD claims; RUNNER code is placed here by override
blk=rpc(u,'eth_blockNumber',[])['result']
amt=int(rpc(u,'eth_call',[{'to':pm,'data':'0x'+cd('balanceOf(address,uint256)',H,int(PATH,16))},blk])['result'],16)
print('block',int(blk,16),'claims of H',amt)
def run(mode):
    inner_items=[
        item(pm, cd('burn(address,uint256,uint256)', H, int(PATH,16), amt)),      # 0 clears H's claim slot
        item(SC, cd('balanceOf(address)', pm)),                                    # 1 credits seen inside the transaction
        item(pm, cd('take(address,address,uint256)', PATH, SINK, amt)),            # 2
        item(pm, cd('settle()')),                                                  # 3 credit under currency 0x1060
        tl(pm, delta_slot(H, SC)),                                                 # 4
        item(pm, cd('take(address,address,uint256)', SC, SINK, 1)),                # 5 expect revert: no transfer function
        tl(pm, delta_slot(H, SC)),                                                 # 6
        item(pm, cd('take(address,address,uint256)', SC, SINK, 0)),                # 7 zero amount shape
        item(pm, cd('mint(address,uint256,uint256)', H, int(SC,16), 1)),           # 8 only way to close a positive delta
        item(SC, cd('balanceOf(address)', pm)),                                    # 9
        tl(pm, delta_slot(H, SC)), tl(pm, NONZERO),                                # 10 11
        item(SC, cd('transfer(address,uint256)', SINK, 1)),                        # 12 direct call shape from an ordinary caller
        item(SC, cd('transferFrom(address,address,uint256)', pm, SINK, 1)),        # 13
        item(SC, cd('approve(address,uint256)', SINK, 1)),                         # 14
    ]
    inner=script(mode, inner_items)
    outer=script(0,[
        item(SC, cd('balanceOf(address)', pm)),            # 0
        item(pm, cd('sync(address)', SC)),                 # 1
        tl(pm, CURRENCY), tl(pm, RESERVES),                # 2 3
        item(pm, unlock(inner)),                           # 4
        item(SC, cd('balanceOf(address)', pm)),            # 5
        item(pm, cd('balanceOf(address,uint256)', H, int(SC,16))),   # 6
    ])
    ov={H:{'code':RUNNER}}
    return rpc(u,'eth_call',[{'from':FROM,'to':H,'data':'0x'+outer,'gas':hex(20_000_000)},blk,ov])
out={}
for mode in (0,1):
    r=run(mode); out[mode]=r
    print('== mode',mode)
    print('\n'.join(dump(r['result'])) if 'result' in r else r)
json.dump({'block':blk,'res':out},open('raw/t1_credits.json','w'),indent=1)
