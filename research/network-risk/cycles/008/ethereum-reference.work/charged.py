# Round trip test for tokens whose transfer from the PoolManager lowers its balance by more than the amount (stored sweep cycles/005/theme-assigned-balance.work/raw/third_1.json.gz).
# eth_simulateV1 with forwarding stubs at the PoolManager address and at an ordinary account A. Read only.
import json,sys; from sweep import *
A='0x'+keccak256(b'cycle-008-account-A')[12:].hex()
TOK=['0xed4794d6c7f397f8e07922187074843d472abe2e','0xb9b1a183ec897b91e7ff7e2b17165d4c88da1c91','0xfe514f155a4f044de535a038b0adbb51c66026c9','0x195ddbbc102e43da6b52015b35ba78396a9ab2c1','0x61d4f395d1523dca8d60008acf5e98733220669e','0xe84a3439449e59a8428f70e6f8a3114b6f36822b','0x66e09f1642ae12a54f076d0c15f7089b8d9d9d94','0xcf85a3a10637f4d19f93f221b50489009f937cf1','0x05876894a17d10f5cd033894211dbea9faf38f13','0x25b9c651258433d18673df2dd3766d9ada2807c5']
def dec_str(h):
    b=bytes.fromhex(h[2:])
    try:
        if len(b)>=64:
            o=int.from_bytes(b[:32],'big'); n=int.from_bytes(b[o:o+32],'big'); return b[o+32:o+32+n].decode('utf8','replace')
        return b.rstrip(b'\0').decode('utf8','replace')
    except Exception: return '?'
blk=hex(int(rpc(URL,'eth_blockNumber',[])['result'],16)-2)
out=[]
for t in TOK:
    sym=dec_str(rpc(URL,'eth_call',[{'to':t,'data':'0x'+sel('symbol()')},blk]).get('result','0x'))
    dec=rpc(URL,'eth_call',[{'to':t,'data':'0x'+sel('decimals()')},blk]).get('result','0x12'); dec=int(dec,16) if dec not in('0x',None) else 18
    b0=int(rpc(URL,'eth_call',[{'to':t,'data':'0x'+cd('balanceOf(address)',PM)},blk])['result'],16)
    amt=b0//3
    def bal(x): return {'to':t,'data':'0x'+cd('balanceOf(address)',x)}
    def fwd(frm_stub,to,a): return {'from':ORIGIN,'to':frm_stub,'data':'0x'+t[2:]+w(0)+cd('transfer(address,uint256)',to,a),'gas':hex(3_000_000)}
    row={'token':t,'symbol':sym,'decimals':dec,'b0':b0,'amt':amt}
    for back_name,back in (('same',None),):
        calls=[bal(PM),fwd(PM,A,amt),bal(PM),bal(A)]
        req={'blockStateCalls':[{'stateOverrides':{PM:{'code':FWD_CALL},A:{'code':FWD_CALL}},'calls':calls}],'validation':False}
        x=rpc(URL,'eth_simulateV1',[req,blk])
        if 'result' not in x: row['err']=json.dumps(x)[:200]; break
        c=x['result'][0]['calls']; v=[int(k['returnData'],16) if k.get('returnData','0x')!='0x' and len(k['returnData'])==66 else None for k in c]
        ok1=int(c[1]['returnData'][2:66],16) if c[1].get('returnData','0x')!='0x' else 0
        pm1=v[2]; a1=v[3]
        row.update({'outOk':ok1,'pmFall':b0-pm1,'aGot':a1})
        # second simulation: A returns exactly what it received
        calls=[bal(PM),fwd(PM,A,amt),bal(PM),bal(A),fwd(A,PM,a1),bal(A),bal(PM), fwd(A,PM,(a1*9)//10)]
        # variant: return 90 percent instead (separate run)
        calls1=calls[:7]
        x=rpc(URL,'eth_simulateV1',[{'blockStateCalls':[{'stateOverrides':{PM:{'code':FWD_CALL},A:{'code':FWD_CALL}},'calls':calls1}],'validation':False},blk])
        c=x['result'][0]['calls']; ok2=int(c[4]['returnData'][2:66],16) if c[4].get('returnData','0x')!='0x' else 0
        a2=int(c[5]['returnData'],16); pm2=int(c[6]['returnData'],16)
        row.update({'backAllOk':ok2,'aAfterBackAll':a2,'pmAfterBackAll':pm2})
        calls2=[bal(PM),fwd(PM,A,amt),bal(PM),bal(A),fwd(A,PM,(a1*9)//10),bal(A),bal(PM)]
        x=rpc(URL,'eth_simulateV1',[{'blockStateCalls':[{'stateOverrides':{PM:{'code':FWD_CALL},A:{'code':FWD_CALL}},'calls':calls2}],'validation':False},blk])
        c=x['result'][0]['calls']; ok3=int(c[4]['returnData'][2:66],16) if c[4].get('returnData','0x')!='0x' else 0
        a3=int(c[5]['returnData'],16); pm3=int(c[6]['returnData'],16)
        row.update({'back90':(a1*9)//10,'back90Ok':ok3,'aFallBack90':a1-a3,'pmRiseBack90':pm3-pm1})
    out.append(row)
    u=10**dec
    print('%s %-10s bal=%.4f amt=%.4f | out ok=%s pmFall/amt=%.6f aGot/amt=%.6f | backAll ok=%s | back90 ok=%s aFall/back=%.6f pmRise/back=%.6f'%(t,sym[:10],b0/u,amt/u,row.get('outOk'),row['pmFall']/amt if amt else 0,row['aGot']/amt if amt else 0,row.get('backAllOk'),row.get('back90Ok'),row['aFallBack90']/row['back90'] if row.get('back90') else 0,row['pmRiseBack90']/row['back90'] if row.get('back90') else 0),flush=True)
json.dump({'block':blk,'rows':out},open('raw_charged.json','w'),indent=0)
