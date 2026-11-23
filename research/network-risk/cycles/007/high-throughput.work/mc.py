from lib import *
MC3='0xcA11bde05977b3631167028862bE2a173976CA11'
def agg3(chain,calls,blk='latest',frm=None,gas=None,chunk=250):
    """calls: list of (target, datahex) -> list of (ok, bytes)"""
    out=[]
    for i in range(0,len(calls),chunk):
        part=calls[i:i+chunk]
        # aggregate3((address,bool,bytes)[])
        head=sel('aggregate3((address,bool,bytes)[])')+w(0x20)+w(len(part))
        offs=[];body=''
        base=32*len(part)
        for t,d in part:
            offs.append(base+len(body)//2)
            db=bytes.fromhex(d)
            pad=(32-len(db)%32)%32
            body+=w(int(t,16))+w(1)+w(0x60)+w(len(db))+d+'00'*pad
        data='0x'+head+''.join(w(o) for o in offs)+body
        p={'to':MC3,'data':data}
        if frm: p['from']=frm
        if gas: p['gas']=hex(gas)
        r=rpc('eth_call',[p,blk],URL[chain])
        b=bytes.fromhex(r[2:])
        n=int.from_bytes(b[32:64],'big'); assert n==len(part)
        for k in range(n):
            o=64+int.from_bytes(b[64+32*k:96+32*k],'big')
            ok=int.from_bytes(b[o:o+32],'big'); do=o+int.from_bytes(b[o+32:o+64],'big')
            ln=int.from_bytes(b[do:do+32],'big'); out.append((ok,b[do+32:do+32+ln]))
    return out
