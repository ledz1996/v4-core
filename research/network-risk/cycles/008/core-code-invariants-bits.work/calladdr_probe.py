# Read-only eth_call creation payload: does CALL / STATICCALL / EXTCODESIZE use only the low 160 bits of the address word?
import json,concurrent.futures as cf
from width_probe import rpc,W,NET
PAT=0x1122334455667788990011223344556677889900aabbccddeeff00112233aabb
DIRTY=(0xdeadbeef<<200)|(1<<160)|4          # identity precompile 0x04 with bits above 160 set
code ='7f'+W(PAT)+'5f52'                                   # mstore(0, PAT)
code+='6020'+'6020'+'6020'+'5f'+'5f'+'7f'+W(DIRTY)+'5a'+'f1'   # call(gas, DIRTY, 0, 0, 32, 32, 32)
code+='604052'+'3d'+'606052'                               # mem[0x40]=success, mem[0x60]=returndatasize
code+='6020'+'6080'+'6020'+'5f'+'7f'+W(DIRTY)+'5a'+'fa'    # staticcall(gas, DIRTY, 0, 32, 0x80, 32)
code+='60a052'                                             # mem[0xa0]=success
code+='7f'+W(DIRTY)+'3b'+'60c052'                          # mem[0xc0]=extcodesize(DIRTY)
code+='7f'+W((1<<160)|0)+'31'+'60e052'                     # mem[0xe0]=balance(address 0 with bit 160 set)
code+='5f31'+'61010052'                                    # mem[0x100]=balance(0)
code+='610120'+'5f'+'f3'
def run(n):
    r=rpc(n['rpc'],'eth_call',[{'from':'0x00000000000000000000000000000000b1750aaa','data':'0x'+code},'latest'])
    if 'result' not in r or len(r['result'])<2+64*9: return n['chainId'],{'err':str(r)[:160]}
    x=r['result'][2:]; w=[int(x[64*i:64*i+64],16) for i in range(9)]
    return n['chainId'],{'call_echo':w[1]==PAT,'call_ok':w[2],'rds':w[3],'static_echo':w[4]==PAT,'static_ok':w[5],'extcodesize':w[6],'bal_dirty_eq_bal0':w[7]==w[8]}
with cf.ThreadPoolExecutor(8) as ex: res=dict(ex.map(run,NET))
json.dump(res,open('calladdr_probe.out.json','w'),indent=1)
for k,v in res.items(): print(k,v)
