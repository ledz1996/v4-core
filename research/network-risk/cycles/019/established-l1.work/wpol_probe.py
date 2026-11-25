import json,urllib.request,sys
sys.path.insert(0,'/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import keccak as k
U='https://rpc-mainnet.matic.quiknode.pro'; W='0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270'
H='0x67366782805870060151383f4bbff9dab53e5cd6'; R='0x000000000000000000000000000000000000dEaD'
def rpc(m,p):
    r=urllib.request.Request(U,json.dumps({'jsonrpc':'2.0','id':1,'method':m,'params':p}).encode(),{'content-type':'application/json'})
    return json.load(urllib.request.urlopen(r,timeout=30))
def pad(a): return a[2:].lower().rjust(64,'0')
out={}
for b in (62278655,62278656):
  bh=hex(b)
  for slot in (3,):
    key='0x'+k(bytes.fromhex(pad(H)+hex(slot)[2:].rjust(64,'0'))).hex()
    ov={W:{'stateDiff':{key:'0x'+hex(10**18)[2:].rjust(64,'0')}}}
    res={}
    for name,data,frm in [('name','0x06fdde03',None),('symbol','0x95d89b41',None),('decimals','0x313ce567',None),
        ('balanceOf(holder)','0x70a08231'+pad(H),None),
        ('transfer(R,1e17) from holder','0xa9059cbb'+pad(R)+hex(10**17)[2:].rjust(64,'0'),H),
        ('transfer(R,0) from holder','0xa9059cbb'+pad(R)+'0'*64,H),
        ('transfer(holder,1e17) from holder','0xa9059cbb'+pad(H)+hex(10**17)[2:].rjust(64,'0'),H),
        ('transfer(R,2e18) from holder','0xa9059cbb'+pad(R)+hex(2*10**18)[2:].rjust(64,'0'),H),
        ('withdraw(1e17) from holder','0x2e1a7d4d'+hex(10**17)[2:].rjust(64,'0'),H)]:
      tx={'to':W,'data':data}
      if frm: tx['from']=frm
      r=rpc('eth_call',[tx,bh,ov]); res[name]=r.get('result',r.get('error'))
    out[b]=res
    for n,v in res.items(): print(b,n,v if not isinstance(v,str) or len(v)<140 else v[:140])
json.dump(out,open('raw/wpol_probe.json','w'),indent=1)
