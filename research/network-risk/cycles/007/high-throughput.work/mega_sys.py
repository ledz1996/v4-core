from seq import *
AC='0x6342000000000000000000000000000000000004'; LC='0x6342000000000000000000000000000000000005'; OR='0x6342000000000000000000000000000000000001'; KD='0x6342000000000000000000000000000000000003'; SR='0x6342000000000000000000000000000000000006'; HP='0x6342000000000000000000000000000000000002'
T='0x7157000000000000000000000000000000007157'
Tcode=asm(['TIMESTAMP',0,'MSTORE',32,0,'RETURN'])
ext={T:{'code':Tcode}}
dis=sel('disableVolatileDataAccess()'); en=sel('enableVolatileDataAccess()'); isd=sel('isVolatileDataAccessDisabled()'); rcg=sel('remainingComputeGas()')
print('selectors',dis,en,isd,rcg)
chain=4326
def show(title,names,res):
    print('---',title)
    for n,x in zip(names,res): print(f'  {n:62}',x if 'ok' not in x else (x['ok'],x['rds'],x['ret'][:72]))
# 1. inside A (called by the PoolManager): each kind of call to the interceptors
for kind in range(4):
    recs=[('T.timestamp before',rec(0,T)),
          (KINDS[kind]+' AC.isVolatileDataAccessDisabled',rec(kind,AC,isd)),
          (KINDS[kind]+' AC.disableVolatileDataAccess',rec(kind,AC,dis)),
          ('CALL AC.isVolatileDataAccessDisabled',rec(0,AC,isd)),
          ('T.timestamp after',rec(0,T)),
          (KINDS[kind]+' LC.remainingComputeGas',rec(kind,LC,rcg)),
          (KINDS[kind]+' AC.enableVolatileDataAccess',rec(kind,AC,en)),
          ('T.timestamp after enable',rec(0,T)),
          (KINDS[kind]+' OR.sendHint',rec(kind,OR,sel('sendHint(bytes32,bytes)')+w(1)+w(0x40)+w(0))),
          (KINDS[kind]+' KD.keylessDeploy',rec(kind,KD,sel('keylessDeploy(bytes,uint256)')+w(0x40)+w(100000)+w(0))),
          (KINDS[kind]+' SR.currentSystemAddress',rec(kind,SR,sel('currentSystemAddress()'))),
          (KINDS[kind]+' HP.timestamp',rec(kind,HP,sel('timestamp()'))),
          ]
    res=run(chain,[r[1] for r in recs],where='A',v_pm_to_a=0,extra=ext,M=M1,gas=30_000_000)
    show('frame A called by PoolManager, kind '+KINDS[kind],[r[0] for r in recs],res)
# 2. scope: the PoolManager frame (M) calls A, A disables and returns; then the PoolManager frame calls T
inner=''.join([rec(0,AC,dis),rec(0,AC,isd),rec(0,T)])
recs=[('PM: T.timestamp before',rec(0,T)),
      ('PM: CALL A {disable; isDisabled; T.timestamp}',rec(0,A,inner)),
      ('PM: CALL AC.isVolatileDataAccessDisabled after A returned',rec(0,AC,isd)),
      ('PM: T.timestamp after A returned',rec(0,T)),
      ('PM: DELEGATECALL A {disable ...} (A code in PM context)',rec(2,A,inner)),
      ('PM: CALL AC.isVolatileDataAccessDisabled',rec(0,AC,isd)),
      ('PM: T.timestamp',rec(0,T))]
pm=PM[chain]
ov={pm:{'code':M1},A:{'code':M1},EOA:{'balance':hex(10**21)},T:{'code':Tcode}}
r=rpc('eth_call',[{'from':EOA,'to':pm,'data':'0x'+''.join(x[1] for x in recs),'gas':hex(30_000_000)},'latest',ov],URL[chain],raw=True)
show('scope after the callee returns',[x[0] for x in recs],seq_parse(r,'PM'))
