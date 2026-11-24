import sys; from lib import *; from targets import *
URL='https://ethereum-rpc.publicnode.com'
def dec_str(h):
    b=bytes.fromhex(h[2:])
    try:
        if len(b)>=64:
            o=int.from_bytes(b[:32],'big'); n=int.from_bytes(b[o:o+32],'big'); return b[o+32:o+32+n].decode('utf8','replace')
        return b.rstrip(b'\0').decode('utf8','replace')
    except Exception: return h[:40]
batch=[]
for i,(c,l,a) in enumerate(T):
    batch.append({'jsonrpc':'2.0','id':i*4,'method':'eth_getCode','params':[a,'latest']})
    for k,s in enumerate(['name()','symbol()','version()']):
        batch.append({'jsonrpc':'2.0','id':i*4+k+1,'method':'eth_call','params':[{'to':a,'data':'0x'+sel(s)},'latest']})
res={}
for i in range(0,len(batch),40):
    r=post(URL,batch[i:i+40])
    for x in r: res[x['id']]=x
for i,(c,l,a) in enumerate(T):
    code=res[i*4].get('result','0x'); n=len(code)//2-1
    extra=''
    if code.startswith('0xef0100'): extra=' DELEGATION->0x'+code[8:]
    vals=[]
    for k in range(3):
        x=res[i*4+k+1]
        vals.append(dec_str(x['result']) if x.get('result','0x')!='0x' and 'result' in x else '-')
    print('%-12s %-32s %s code=%d%s name=%r sym=%r ver=%r'%(c,l,a,n,extra,vals[0][:40],vals[1][:20],vals[2][:20]))
