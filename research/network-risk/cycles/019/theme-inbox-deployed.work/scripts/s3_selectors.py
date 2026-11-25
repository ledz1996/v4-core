import json,glob,os,re
from keccak import keccak256
def selectors(code):
    b=bytes.fromhex(code[2:]); i=0; sels=[]
    # dispatcher: PUSH4 x  (followed within 3 bytes by EQ 0x14 or GT 0x11)
    while i<len(b):
        op=b[i]
        if op==0x63:
            s=b[i+1:i+5].hex(); nxt=b[i+5:i+8]
            if 0x14 in nxt[:2] or 0x11 in nxt[:2] or (len(nxt)>1 and nxt[0]==0x81 and nxt[1]==0x14): sels.append(s)
        if 0x60<=op<=0x7f: i+=op-0x5f
        i+=1
    return sorted(set(sels))
if __name__=='__main__':
    out={}
    for f in sorted(glob.glob('../raw/code/*.hex')):
        if 'portal' in f or 'temp' in f: continue
        k=os.path.basename(f)
        a=k.split('_')[-1][:-4]; cid='999' if k.startswith('ely') else '1'
        abi=json.load(open(f'../dl/sourcify/{cid}_{a}.json'))['abi'] if os.path.exists(f'../dl/sourcify/{cid}_{a}.json') else []
        names={}
        for e in abi:
            if e['type']=='function':
                sig=e['name']+'('+','.join(x['type'] if not x['type'].startswith('tuple') else '?' for x in e['inputs'])+')'
                names[keccak256(sig.encode()).hex()[:8]]=(sig,e.get('stateMutability'))
        s=selectors(open(f).read().strip())
        out[k]={'bytecode_selectors':len(s),'abi_functions':len(names),'in_code_not_abi':[x for x in s if x not in names],'in_abi_not_code':[names[x][0] for x in names if x not in s],
                'functions':{x:names.get(x,('?',''))[0]+' '+str(names.get(x,('',''))[1]) for x in s}}
    json.dump(out,open('../raw/selectors.json','w'),indent=1)
    for k,v in out.items():
        print(k,v['bytecode_selectors'],v['abi_functions'],'extra',v['in_code_not_abi'],'missing',v['in_abi_not_code'])
    for k in ('arb1_inbox_0x7c058ad1d0ee415f7e7f30e62db1bcf568470a10.hex',):
        for x,n in out[k]['functions'].items(): print(' ',x,n)
