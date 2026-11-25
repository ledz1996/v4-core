# Bound the routed prefix on Base (B20) and Tempo (TIP-20): flip one byte k of the prefix and see whether
# balanceOf(PM) reverts (routed to native token code) or answers empty success (ordinary account).
import json,sys,time
sys.path.insert(0,'.')
from rpc import rpc
cases={8453:('https://mainnet.base.org/','0x498581ff718922c3f8e6a244956af099b2652b2b','b2'),
       4217:('https://rpc.mainnet.tempo.xyz','0x33620f62c5b9b2086dd6b62f4a297a9f30347029','20c0')}
out={}
for cid,(u,pm,pre) in cases.items():
    rec={'clientVersionBefore':rpc(u,'web3_clientVersion',[]).get('result')}
    rows={}
    for k in range(len(pre)//2,20):
        b=bytearray(bytes.fromhex(pre)+bytes(20-len(pre)//2)); b[k]=0x01; b[19]|=0x01
        a='0x'+b.hex()
        j=rpc(u,'eth_call',[{'from':pm,'to':a,'data':'0x70a08231'+pm[2:].rjust(64,'0')},'latest'])
        rows[a]=j.get('result',j.get('error'))
        print(cid,k,a,str(rows[a])[:90]); time.sleep(0.2)
    rec['rows']=rows; rec['clientVersionAfter']=rpc(u,'web3_clientVersion',[]).get('result')
    out[cid]=rec
json.dump(out,open('raw/prefix_probe.json','w'),indent=1)
