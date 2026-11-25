import json
from rpc import *
from keccak import keccak256
def sel(s): return keccak256(s.encode()).hex()[:8]
def w(x): return x.lower().replace('0x','').rjust(64,'0')
ARC='https://rpc.mainnet.arc.io'; PM='0x8366a39CC670B4001A1121B8F6A443A643e40951'
USDC='0x3600000000000000000000000000000000000000'; MEMO='5294E9927c3306DcBaDb03fe70b92e01cCede505'
EOA='0x00000000000000000000000000000000000c0ffe'; STUB='0x000000000000000000000000000000000057ab00'
pre='366000600037'+'60006000366000600073'+MEMO.lower()+'5af1'+'3d600060003e'
jd=len(pre)//2+3+5   # PUSH1 x JUMPI (3) + revert block 3d6000fd (4) -> adjust
body_rev='3d6000fd'
code=pre+'60'+'%02x'%(len(pre)//2+3+len(body_rev)//2)+'57'+body_rev+'5b'+'3d6000f3'
ib=(sel('transfer(address,uint256)')+w(EOA)+w('0x1'))
pad=ib.ljust(((len(ib)+63)//64)*64,'0')
memo='0x'+sel('memo(address,bytes,bytes32,bytes)')+w(USDC)+w(hex(128))+w('0x0')+w(hex(128+32+len(pad)//2))+w(hex(len(ib)//2))+pad+w('0x0')
o={'client_start':rpc(ARC,'web3_clientVersion',[]),'stubCode':'0x'+code}
o['stub_calls_Memo']=rpc(ARC,'eth_call',[{'from':EOA,'to':STUB,'data':memo},'latest',{STUB:{'code':'0x'+code}}])
o['client_end']=rpc(ARC,'web3_clientVersion',[])
print(json.dumps(o,indent=1))
json.dump(o,open('../raw/arc_stub_memo.json','w'),indent=1)
