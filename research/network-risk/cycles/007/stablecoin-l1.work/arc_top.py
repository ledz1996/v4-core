import json,gzip
from rpc import *
c=5042; pm=PM[c]
d=json.load(gzip.open('../../004/theme-balance-reconcile.work/raw/currencies_5042.json.gz'))
cur=d['currencies']
top=[t for t,n in sorted(cur.items(), key=lambda x:-x[1])[:120] if int(t,16)!=0]
extra=['0x8a5D989Bbb96929F689B0200f435f53dA42bF490','0xc6ad664ac6679f4ce74e10e91449c93ec1ae3ca6']
toks=top+[e.lower() for e in extra]
def dec_str(h):
    try:
        b=bytes.fromhex(h[2:])
        if len(b)>=64:
            n=int.from_bytes(b[32:64],'big'); return b[64:64+n].decode('utf8','replace')
        return b.rstrip(b'\0').decode('utf8','replace')
    except Exception as e: return '?'
calls=[]
for t in toks:
    calls+= [('eth_call',[{'to':t,'data':'0x70a08231'+pad(pm)},'latest']),('eth_call',[{'to':t,'data':'0x95d89b41'},'latest']),('eth_call',[{'to':t,'data':'0x313ce567'},'latest']),('eth_getCode',[t,'latest']),('eth_call',[{'to':t,'data':'0x18160ddd'},'latest'])]
r=batch(c,calls)
out=[]
for i,t in enumerate(toks):
    b,s,dc,code,ts=r[5*i:5*i+5]
    f=lambda v:(int(v,16) if isinstance(v,str) and len(v)>2 else None)
    out.append(dict(token=t,pools=cur.get(t),bal=f(b),sym=dec_str(s) if isinstance(s,str) else '?',dec=f(dc),codeLen=(len(code)-2)//2 if isinstance(code,str) else None,ts=f(ts)))
json.dump(out,open('arc_top.json','w'),indent=0)
for o in out: print(o['token'],o['pools'],o['sym'][:14],o['dec'],o['codeLen'], (o['bal'] or 0)/10**(o['dec'] or 0), 'share=%.4f'%((o['bal'] or 0)/o['ts'] if o['ts'] else 0))
print('native', int(rpc(c,'eth_getBalance',[pm,'latest']),16))
