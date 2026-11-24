import json,time; from lib import *
URL='https://ethereum-rpc.publicnode.com'; PM='0x000000000004444c5dc75cB358380D2e3dE08A90'
FOLD='0xe172e9b6cfbeeb5593bdce3f077356fdb33af904'; CCA='0x687cc38d8279df3352b64cf3ec1fe8e033933595'; MC3='0xcA11bde05977b3631167028862bE2a173976CA11'
def call(to,sig,*a):
    r=rpc(URL,'eth_call',[{'to':to,'data':'0x'+cd(sig,*a)},'latest']); return r.get('result') or json.dumps(r)[:120]
for s in ['NO_MORE_LOCKS()','CLAIM_SOURCE()','tgeTimestamp()','owner()']: print('FOLD',s,call(FOLD,s))
for s,a in [('claimLockExempt(address)',PM),('lockedBalanceOf(address)',PM),('transferableBalanceOf(address)',PM),('balanceOf(address)',PM),('lockCount(address)',PM),('queuedLockCount(address)',PM)]:
    v=call(FOLD,s,a); print('FOLD',s,int(v,16) if v.startswith('0x') and len(v)==66 else v)
for s in ['nextBidId()','endBlock()','claimBlock()','token()','isGraduated()']: print('CCA',s,call(CCA,s))
blk=rpc(URL,'eth_getBlockByNumber',['latest',False])['result']; print('now',int(blk['number'],16),int(blk['timestamp'],16))
n=int(call(CCA,'nextBidId()'),16)
def agg(calls):
    head=sel('aggregate3((address,bool,bytes)[])')+w(0x20)+w(len(calls)); offs=[];body=''; base=32*len(calls)
    for t,d in calls:
        offs.append(base+len(body)//2); db=bytes.fromhex(d); pad=(32-len(db)%32)%32
        body+=w(t)+w(1)+w(0x60)+w(len(db))+d+'00'*pad
    r=rpc(URL,'eth_call',[{'to':MC3,'data':'0x'+head+''.join(w(o) for o in offs)+body,'gas':hex(50_000_000)},'latest'],timeout=90)['result']
    b=bytes.fromhex(r[2:]); k=int.from_bytes(b[32:64],'big'); out=[]
    for i in range(k):
        o=64+int.from_bytes(b[64+32*i:96+32*i],'big'); ok=int.from_bytes(b[o:o+32],'big'); do=o+int.from_bytes(b[o+32:o+64],'big'); ln=int.from_bytes(b[do:do+32],'big'); out.append((ok,b[do+32:do+32+ln]))
    return out
owners={}; notexit=[]; unclaimed=[]; pmbids=[]
for i in range(0,n,400):
    res=agg([(CCA,cd('bids(uint256)',j)) for j in range(i,min(n,i+400))])
    for j,(ok,b) in zip(range(i,min(n,i+400)),res):
        if not ok or len(b)<224: continue
        exited=int.from_bytes(b[64:96],'big'); owner='0x'+b[128+12:160].hex(); filled=int.from_bytes(b[192:224],'big')
        if exited==0: notexit.append((j,owner))
        if filled>0: unclaimed.append((j,owner,filled))
        if owner.lower()==PM.lower(): pmbids.append(j)
print('bids',n,'notExited',len(notexit),notexit[:20]); print('with tokensFilled>0 (unclaimed)',len(unclaimed),[(j,o,f/1e18) for j,o,f in unclaimed[:12]]); print('bids owned by PM',pmbids)
