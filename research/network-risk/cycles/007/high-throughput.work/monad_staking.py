from seq import *
ST='0x0000000000000000000000000000000000001000'; RB='0x0000000000000000000000000000000000001001'
pm=PM[143]
r=rpc('eth_call',[{'to':ST,'data':'0x'+sel('getEpoch()')},'latest'],URL[143],raw=True); print('getEpoch',r)
r=rpc('eth_call',[{'to':ST,'data':'0x'+sel('getValidator(uint64)')+w(1)},'latest'],URL[143],raw=True); print('getValidator(1)',str(r)[:300])
V=10**18
gd=lambda who: sel('getDelegator(uint64,address)')+w(1)+w(int(who,16))
recs=[('CALL getEpoch',rec(0,ST,sel('getEpoch()'))),
 ('CALL getDelegator(1,PM)',rec(0,ST,gd(pm))),
 ('CALL getDelegator(1,A)',rec(0,ST,gd(A))),
 ('STATICCALL getEpoch',rec(1,ST,sel('getEpoch()'))),
 ('DELEGATECALL getEpoch',rec(2,ST,sel('getEpoch()'))),
 ('CALLCODE getEpoch',rec(3,ST,sel('getEpoch()'))),
 ('DELEGATECALL delegate(1) [inherits sender PM, value V]',rec(2,ST,sel('delegate(uint64)')+w(1))),
 ('CALLCODE delegate(1) value V',rec(3,ST,sel('delegate(uint64)')+w(1),V)),
 ('STATICCALL delegate(1)',rec(1,ST,sel('delegate(uint64)')+w(1))),
 ('DELEGATECALL externalReward(1)',rec(2,ST,sel('externalReward(uint64)')+w(1))),
 ('DELEGATECALL claimRewards(1)',rec(2,ST,sel('claimRewards(uint64)')+w(1))),
 ('DELEGATECALL compound(1)',rec(2,ST,sel('compound(uint64)')+w(1))),
 ('DELEGATECALL undelegate(1,1,0)',rec(2,ST,sel('undelegate(uint64,uint256,uint8)')+w(1)+w(1)+w(0))),
 ('DELEGATECALL withdraw(1,0)',rec(2,ST,sel('withdraw(uint64,uint8)')+w(1)+w(0))),
 ('CALLCODE claimRewards(1)',rec(3,ST,sel('claimRewards(uint64)')+w(1))),
 ('CALL getDelegator(1,PM) after',rec(0,ST,gd(pm))),
 ('CALL getDelegator(1,A) after',rec(0,ST,gd(A))),
 ('CALL delegate(1) value V (control)',rec(0,ST,sel('delegate(uint64)')+w(1),V)),
 ('CALL getDelegator(1,A) after control',rec(0,ST,gd(A))),
 ('CALL getDelegator(1,PM) after control',rec(0,ST,gd(pm))),
 ('CALL dippedIntoReserve',rec(0,RB,sel('dippedIntoReserve()'))),
 ('STATICCALL dippedIntoReserve',rec(1,RB,sel('dippedIntoReserve()'))),
 ('DELEGATECALL dippedIntoReserve',rec(2,RB,sel('dippedIntoReserve()'))),
 ('CALLCODE dippedIntoReserve',rec(3,RB,sel('dippedIntoReserve()'))),
]
print('--- frame: EOA -> PoolManager(F) -CALL value 3 MON-> A(M); msg.sender in A is the PoolManager')
bn=rpc('eth_blockNumber',[],URL[143]); print('block',int(bn,16))
res=run(143,[x[1] for x in recs],where='A',v_pm_to_a=3*V,gas=29_000_000,blk=bn,M=M1)
for (n,_),x in zip(recs,res): print(f'{n:58}',x)
print('--- frame: EOA -> PoolManager(M): the PoolManager address itself issues the calls (state override)')
res=run(143,[x[1] for x in recs],where='PM',gas=29_000_000,blk=bn,M=M1)
for (n,_),x in zip(recs,res): print(f'{n:58}',x)
