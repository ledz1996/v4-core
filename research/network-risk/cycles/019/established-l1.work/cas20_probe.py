import json,urllib.request,ssl
ctx=ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
PM='0x28e2ea090877bf75740558f6bfb36a5ffee9e9df'
EPS=['https://bsc-dataseed1.bnbchain.org','https://rpc-bsc.48.club','https://bsc-rpc.publicnode.com']
TOK=['0xca52000000000000000000000000000000000001','0xca52000000000000000000000000000000000000','0xca520000000000000000000000000000000000ff','0x0000000000000000000000000000000000000070']
def pad(a): return a[2:].lower().rjust(64,'0')
calls={'balanceOf(PM)':'0x70a08231'+pad(PM),'transfer(dead,0)':'0xa9059cbb'+pad('0x000000000000000000000000000000000000dead')+'0'*64,
 'transfer(dead,1)':'0xa9059cbb'+pad('0x000000000000000000000000000000000000dead')+'0'*63+'1','empty':'0x'}
out=[]
for u in EPS:
  for mode,bo in (('pre',None),('jenner',{'time':hex(1796697600)})):
    for t in TOK:
      for n,d in calls.items():
        p=[{'from':PM,'to':t,'data':d},'latest']
        if bo: p+= [{},bo]
        r=urllib.request.Request(u,json.dumps({'jsonrpc':'2.0','id':1,'method':'eth_call','params':p}).encode(),{'content-type':'application/json','user-agent':'curl/8'})
        try: j=json.load(urllib.request.urlopen(r,timeout=30,context=ctx))
        except Exception as e: j={'error':str(e)}
        res=j.get('result',j.get('error'))
        out.append([u,mode,t,n,res]); print(u.split('/')[2][:14],mode,t[:10]+'..'+t[-4:],n,str(res)[:100])
json.dump(out,open('raw/cas20_probe.json','w'),indent=1)
