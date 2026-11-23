import sys,json,time
from ws import *
dur=float(sys.argv[1]); out=open(sys.argv[2],'w')
ss,rest=connect('mainnet.megaeth.com','/ws'); rd=Reader(ss,rest)
send(ss,json.dumps({'jsonrpc':'2.0','id':1,'method':'eth_subscribe','params':['newPendingTransactions']}))
send(ss,json.dumps({'jsonrpc':'2.0','id':2,'method':'eth_subscribe','params':['miniBlocks']}))
subs={}
t0=time.time(); last=t0; n=0
while time.time()-t0<dur:
    try: m=rd.frame()
    except EOFError as e: out.write(json.dumps({'eof':str(e),'t':time.time()})+'\n'); break
    t=time.time()
    j=json.loads(m)
    if 'id' in j: subs[j.get('result')]=j['id']; out.write(json.dumps({'sub':j,'t':t})+'\n'); continue
    p=j['params']; kind=subs.get(p['subscription'])
    if kind==1: out.write(json.dumps({'k':'p','t':t,'h':p['result']})+'\n')
    else:
        r=p['result']
        txs=[{'h':x.get('hash'),'f':x.get('from'),'ty':x.get('type'),'tip':x.get('maxPriorityFeePerGas'),'gp':x.get('gasPrice'),'n':x.get('nonce'),'g':x.get('gas')} for x in r.get('transactions',[])]
        rc=[{'gu':x.get('gasUsed'),'cg':x.get('cumulativeGasUsed'),'st':x.get('status')} for x in r.get('receipts',[])]
        out.write(json.dumps({'k':'m','t':t,'bn':r.get('block_number'),'i':r.get('index'),'mb':r.get('mini_block_number'),'mt':r.get('mini_block_timestamp'),'txs':txs,'rc':rc})+'\n')
    n+=1
    if t-last>20:
        send(ss,json.dumps({'jsonrpc':'2.0','id':99,'method':'eth_chainId','params':[]})); last=t; out.flush()
out.close()
