import json
from rpc import *
from keccak import keccak256
def sel(s): return keccak256(s.encode()).hex()[:8]
def w(x): return (x if isinstance(x,str) else hex(x))[2:].rjust(64,'0') if not isinstance(x,str) else x.lower().replace('0x','').rjust(64,'0')
EOA='0x00000000000000000000000000000000000c0ffe'
out={}
# Arc
ARC='https://rpc.mainnet.arc.io'; PM='0x8366a39CC670B4001A1121B8F6A443A643e40951'
USDC='0x3600000000000000000000000000000000000000'
CF='0x1800000000000000000000000000000000000003'; MEMO='0x5294E9927c3306DcBaDb03fe70b92e01cCede505'; M3F='0x522fAf9A91c41c443c66765030741e4AaCe147D0'
inner='0x'+sel('transfer(address,uint256)')+w(EOA)+w(hex(1))
ib=inner[2:]
cf='0x'+sel('callFrom(address,address,bytes)')+w(PM)+w(USDC)+w(hex(96))+w(hex(len(ib)//2))+ib.ljust(((len(ib)+63)//64)*64,'0')
a={'client_start':rpc(ARC,'web3_clientVersion',[])}
a['codeLen_CallFrom']=len(rpc(ARC,'eth_getCode',[CF,'latest']))//2-1
a['codeLen_Memo']=len(rpc(ARC,'eth_getCode',[MEMO,'latest']))//2-1
a['codeLen_M3F']=len(rpc(ARC,'eth_getCode',[M3F,'latest']))//2-1
a['EOA_calls_CallFrom_naming_PM']=call(ARC,CF,cf,frm=EOA)
a['PM_balance_USDC_native']=rpc(ARC,'eth_getBalance',[PM,'latest'])
# Memo from an EOA: child sender is the EOA, so a transfer of 1 from an empty EOA fails inside
memo='0x'+sel('memo(address,bytes,bytes32,bytes)')+w(USDC)+w(hex(128))+w('0x0')+w(hex(128+32+((len(ib)+63)//64)*32))+w(hex(len(ib)//2))+ib.ljust(((len(ib)+63)//64)*64,'0')+w('0x0')
a['EOA_calls_Memo_transfer1']=call(ARC,MEMO,memo,frm=EOA)
a['client_end']=rpc(ARC,'web3_clientVersion',[])
out['5042']=a
# Avalanche nativeAssetCall
AV='https://api.avax.network/ext/bc/C/rpc'
v={'client_start':rpc(AV,'web3_clientVersion',[])}
data='0x'+'06380c0e0912312b5150364b9dc4542ba0dbbc85'+'00'*32+'00'*32+sel('transfer(address,uint256)')+w(EOA)+w(hex(1))
v['nativeAssetCall_0x0100..02']=call(AV,'0x0100000000000000000000000000000000000002',data,frm=EOA)
v['nativeAssetBalance_0x0100..01']=call(AV,'0x0100000000000000000000000000000000000001','0x'+'06380c0e0912312b5150364b9dc4542ba0dbbc85'+'00'*32,frm=EOA)
v['client_end']=rpc(AV,'web3_clientVersion',[])
out['43114']=v
print(json.dumps(out,indent=1))
json.dump(out,open('../raw/onchain_tests.json','w'),indent=1)
