# For every (target, shape) that did not revert in raw_sweep.json: eth_simulateV1 with traceTransfers, list logs and ETH transfers.
import json,sys; from sweep import *
d=json.load(open('raw_sweep.json')); blk=d['block']
rows=[r for r in d['rows'] if r.get('verdict')!='reverts' and 'err' not in r and not r['shape'].startswith('P3')]
S_by={}
TOP={'ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef':'Transfer','e1fffcc4923d04b559f4d29a8bfc6cda04eb5b0d3c460751c2402c5c5cc9109c':'Deposit(WETH)'}
out=[]
for r in rows:
    if r['cat']=='precompile' or r['label'] in ('SystemAddress','ZeroAddress'): continue
    addr=r['addr']; sh={s[0]:s for s in shapes(addr)}[r['shape']]
    name,mode,val,data=sh
    calld='0x'+addr[2:].lower()+w(val)+data
    req={'blockStateCalls':[{'stateOverrides':{PM:{'code':FWD_CALL}},'calls':[{'from':ORIGIN,'to':PM,'data':calld,'gas':hex(12_000_000)}]}],'traceTransfers':True,'validation':False}
    x=rpc(URL,'eth_simulateV1',[req,blk])
    if 'result' not in x: print(r['label'],name,'ERR',json.dumps(x)[:200]); continue
    c=x['result'][0]['calls'][0]
    logs=c.get('logs',[])
    desc=[]
    for l in logs:
        t0=l['topics'][0][2:] if l['topics'] else ''
        if l['address'].lower()=='0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee':
            desc.append('ETH %s -> %s : %d'%('0x'+l['topics'][1][26:],'0x'+l['topics'][2][26:],int(l['data'],16)))
        else:
            desc.append('LOG %s topic0=%s topics=%s data=%s'%(l['address'],t0[:8],[t[26:] if t.startswith('0x000000000000000000000000') else t[2:10] for t in l['topics'][1:]],l['data'][2:130]))
    out.append({'label':r['label'],'addr':addr,'shape':name,'status':c.get('status'),'gasUsed':int(c.get('gasUsed','0x0'),16),'logs':desc})
    print('%-28s %-22s status=%s gas=%d'%(r['label'],name,c.get('status'),int(c.get('gasUsed','0x0'),16)))
    for s in desc: print('      ',s)
json.dump(out,open('raw_followup.json','w'),indent=0)
