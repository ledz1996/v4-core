import json,gzip
from rpc import *
d=json.load(gzip.open('../../004/theme-balance-reconcile.work/raw/reconcile_4217.json.gz'))
toks=[r['token'] for r in d['rows']]
c=4217; pm=PM[c]
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
    try: bal=int(b,16)
    except: bal=None
    try: de=int(dc,16)
    except: de=None
    try: tsv=int(ts,16)
    except: tsv=None
    out.append(dict(token=t,bal=bal,sym=dec_str(s) if isinstance(s,str) else '?',dec=de,codeLen=(len(code)-2)//2 if isinstance(code,str) else None,ts=tsv))
json.dump(out,open('tempo_bal.json','w'),indent=0)
out.sort(key=lambda x:-(x['bal'] or 0)/10**(x['dec'] or 0))
for o in out: print(o['token'],o['sym'],o['dec'],o['codeLen'], (o['bal'] or 0)/10**(o['dec'] or 0), 'share=%.4f'%((o['bal'] or 0)/o['ts'] if o['ts'] else 0))
