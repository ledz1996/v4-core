import json,sys,time,collections; from lib import *
U='https://eth.drpc.org'; PMl='0x000000000004444c5dc75cb358380d2e3de08a90'
ATT='0x5b89b6fea024655c9d60e77fd841a8f0a19e8c91'
SEL={'f5298aca':'burn(from,id,amount)','fe99049a':'transferFrom(sender,receiver,id,amount)','156e29f6':'mint(to,id,amount)','0b0d9c09':'take(currency,to,amount)','80f0b44c':'settleFor(recipient)','11da60b4':'settle()','48c89491':'unlock','095bcdb6':'transfer(receiver,id,amount)','a5841194':'sync','f3cd914c':'swap','5a6bcfda':'modifyLiquidity','80f0b44c':'settleFor','234266d7':'donate','426a8493':'approve(spender,id,amount)','558a7297':'setOperator','8161b874':'collectProtocolFees'}
def trace(p,blk,ov=None):
    args=[p,hex(blk),{'tracer':'callTracer'}]
    if ov: args[2]['stateOverrides']=ov
    for i in range(5):
        r=rpc(U,'debug_traceCall',args,timeout=60)
        if 'result' in r: return r['result']
        time.sleep(2+i*2)
    return {'error':json.dumps(r)[:200]}
def pmcalls(t,out,depth=0):
    if not isinstance(t,dict): return
    if (t.get('to') or '').lower()==PMl:
        s=t.get('input','0x')[2:10]; inp=t.get('input','0x')[10:]
        args=[inp[i:i+64] for i in range(0,min(len(inp),64*4),64)]
        if s in ('f5298aca','fe99049a','156e29f6','0b0d9c09','80f0b44c','095bcdb6','426a8493','558a7297'):
            out.append((SEL.get(s,s),t.get('from'),[('0x'+a[24:] if a.startswith('0'*24) and int(a,16)>2**64 else hex(int(a,16))) for a in args],'ERR:'+t['error'] if t.get('error') else 'ok'))
    for c in t.get('calls',[]) or []: pmcalls(c,out,depth+1)
if __name__!="__main__": raise SystemExit
res=[]
for a in ['0xbc22993a15e16acbf12873f234510d35948f7a59','0x4531332adecf255c66b5bf6485db73f894ed93d2','0xad445acd8e2446c652fb47b2d4c5ee9973b150c9','0x37bfb8ac7c960e558657871d41ca70e07e7dbfff']:
    it=json.load(open('bs_%s.json'%a))['items']
    seen=collections.Counter()
    for x in it:
        inp=x.get('raw_input') or ''; s=inp[:10]
        if s.startswith('0x6080') or seen[s]>=3 or x.get('status')!='ok': continue
        seen[s]+=1
        blk=int(x['block_number'])-1; frm=x['from']['hash'].lower(); val=hex(int(x.get('value') or 0))
        row={'router':a,'tx':x['hash'],'sel':s,'block':blk,'origSender':frm,'value':val}
        for who,sender in (('orig',frm),('other',ATT)):
            ov={ATT:{'balance':hex(10**21)}} if who=='other' else None
            t=trace({'from':sender,'to':a,'data':inp,'value':val},blk,ov)
            calls=[]; pmcalls(t,calls)
            row[who]={'topError':t.get('error'),'revertReason':t.get('revertReason'),'output':(t.get('output') or '')[:74],'pm':calls}
        res.append(row)
        print(a[:10],s,x['hash'][:12],'blk',blk,'sender',frm[:10],'value',val)
        for who in ('orig','other'):
            print('   %-5s err=%s out=%s'%(who,row[who]['topError'],row[who]['output'][:40]))
            for c in row[who]['pm']: print('        ',c)
        sys.stdout.flush()
json.dump(res,open('raw_routers.json','w'),indent=0)
