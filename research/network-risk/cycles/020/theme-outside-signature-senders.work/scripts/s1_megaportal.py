import json,os
from rpc import *
from keccak import keccak256
def sel(s): return '0x'+keccak256(s.encode()).hex()[:8]
IMPL='0x'+hex(int.from_bytes(keccak256(b'eip1967.proxy.implementation'),'big')-1)[2:]
ADMIN='0x'+hex(int.from_bytes(keccak256(b'eip1967.proxy.admin'),'big')-1)[2:]
portal='0x7f82f57F0Dd546519324392e408b01fcC7D709e8'
PM='0xacb7e78fa05d562e0a5d3089ec896d57d057d38e'
out={'client_start':rpc(ETH,'web3_clientVersion',[]),'block':rpc(ETH,'eth_blockNumber',[])}
d={'portal':portal}
d['impl']=addr(rpc(ETH,'eth_getStorageAt',[portal,IMPL,'latest']))
d['admin']=addr(rpc(ETH,'eth_getStorageAt',[portal,ADMIN,'latest']))
d['adminCode']=len(rpc(ETH,'eth_getCode',[d['admin'],'latest']))//2-1
d['adminOwner']=addr(call(ETH,d['admin'],sel('owner()')))
d['adminOwnerCodeLen']=len(rpc(ETH,'eth_getCode',[d['adminOwner'],'latest']))//2-1
for f in ['getOwners()','getThreshold()']:
    d['adminOwner.'+f]=call(ETH,d['adminOwner'],sel(f))
v=call(ETH,portal,sel('version()'))
try: d['version']=bytes.fromhex(v[2:])[64:64+int(v[66:130],16)].decode()
except Exception: d['version']=v
for f in ['paused()','systemConfig()','superchainConfig()','guardian()','anchorStateRegistry()','proxyAdminOwner()','proxyAdmin()']:
    d[f]=call(ETH,portal,sel(f))
c=rpc(ETH,'eth_getCode',[d['impl'],'latest'])
open('../raw/megaportal_impl.hex','w').write(c)
b=bytes.fromhex(c[2:])
d['implCodeLen']=len(b)
d['implCodeKeccak']='0x'+keccak256(b).hex()
d['has_alias_offset_1111']=b.find(bytes.fromhex('1111000000000000000000000000000000001111'))
d['has_ef0100']=b.find(bytes.fromhex('ef0100'))
d['has_ORIGIN_op_0x32']=b.count(b'\x32')
d['selector_depositTransaction']=b.find(bytes.fromhex(sel('depositTransaction(address,uint256,uint64,bool,bytes)')[2:]))
d['PM_on_eth_code']=rpc(ETH,'eth_getCode',[PM,'latest'])
d['PM_on_eth_nonce']=rpc(ETH,'eth_getTransactionCount',[PM,'latest'])
pre=(int(PM,16)-0x1111000000000000000000000000000000001111)%(1<<160)
d['alias_preimage']='0x%040x'%pre
d['alias_preimage_code']=rpc(ETH,'eth_getCode',[d['alias_preimage'],'latest'])
d['alias_preimage_nonce']=rpc(ETH,'eth_getTransactionCount',[d['alias_preimage'],'latest'])
out['d']=d
out['client_end']=rpc(ETH,'web3_clientVersion',[])
print(json.dumps(out,indent=1))
json.dump(out,open('../raw/megaportal.json','w'),indent=1)
