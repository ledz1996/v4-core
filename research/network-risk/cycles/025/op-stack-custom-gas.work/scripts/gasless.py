"""Read-only probes of the X Layer gasless whitelist for lead L-1068."""
import json, sys, urllib.request
RPC='https://rpc.xlayer.tech'
def rpc(m,p):
    r=urllib.request.Request(RPC,data=json.dumps({'jsonrpc':'2.0','id':1,'method':m,'params':p}).encode(),headers={'content-type':'application/json','user-agent':'curl/8'})
    return json.load(urllib.request.urlopen(r,timeout=60))
GL='0x19787404b0c70021b4752028f7e3a92313885B27'
SYS='0xdeaddeaddeaddeaddeaddeaddeaddeaddead0001'
def allowance(to,data):
    data=bytes.fromhex(data[2:] if data.startswith('0x') else data)
    words=(len(data)+31)//32
    enc='bad12ebe'+to[2:].lower().rjust(64,'0')+hex(64)[2:].rjust(64,'0')+hex(len(data))[2:].rjust(64,'0')+(data.hex().ljust(words*64,'0'))
    r=rpc('eth_call',[{'from':SYS,'to':GL,'data':'0x'+enc},'latest'])
    return r.get('result',r.get('error'))
if __name__=='__main__':
    out={}
    targets={'PoolManager':'0x360e68faccca8ca495c1b759fd9eee466db9fb32','PositionManager':'0xcf1eafc6928dc385a342e7c6491d371d2871458b',
     'UR':'0xda00ae15d3a71466517129255255db7c0c0956d3','UR211':'0x8b844f885672f333bc0042cb669255f93a4c1e6b','UR212':'0x1cd182C94fcF42277B80DBB9060F88024809E61E',
     'Permit2':'0x000000000022D473030F116dDEE9F6B43aC78BA3','top':'0x7c5bee2a8091c3ef39072f64f18fac913060aeaf'}
    sels=['0x','0x48c89491','0xf3cd914c','0x5a6bcfda','0x234266d7','0x11da60b4','0xa9059cbb','0x095ea7b3','0x3593564c','0xdd46508f','0x24856bc3','0x87517c45']
    for n,a in targets.items():
        out[n]={s:allowance(a,s) for s in sels}
    out['code_top']=len(rpc('eth_getCode',[targets['top'],'latest'])['result'])//2-1
    out['block']=rpc('eth_blockNumber',[])['result']
    print(json.dumps(out,indent=1))
