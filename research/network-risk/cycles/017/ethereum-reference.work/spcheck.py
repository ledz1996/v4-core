import re,sys
# (pops, pushes) per opcode, Osaka
T={'STOP':(0,0),'ADD':(2,1),'MUL':(2,1),'SUB':(2,1),'DIV':(2,1),'SDIV':(2,1),'MOD':(2,1),'SMOD':(2,1),'ADDMOD':(3,1),'MULMOD':(3,1),'EXP':(2,1),'SIGNEXTEND':(2,1),
'LT':(2,1),'GT':(2,1),'SLT':(2,1),'SGT':(2,1),'EQ':(2,1),'ISZERO':(1,1),'AND':(2,1),'OR':(2,1),'XOR':(2,1),'NOT':(1,1),'BYTE':(2,1),'SHL':(2,1),'SHR':(2,1),'SAR':(2,1),'CLZ':(1,1),
'KECCAK256':(2,1),'ADDRESS':(0,1),'BALANCE':(1,1),'ORIGIN':(0,1),'CALLER':(0,1),'CALLVALUE':(0,1),'CALLDATALOAD':(1,1),'CALLDATASIZE':(0,1),'CALLDATACOPY':(3,0),'CODESIZE':(0,1),'CODECOPY':(3,0),
'RETURNDATASIZE':(0,1),'RETURNDATACOPY':(3,0),'POP':(1,0),'MLOAD':(1,1),'MSTORE':(2,0),'MSTORE8':(2,0),'SLOAD':(1,1),'SSTORE':(2,0),'JUMP':(1,0),'JUMPI':(2,0),'PC':(0,1),'MSIZE':(0,1),'GAS':(0,1),'JUMPDEST':(0,0),
'TLOAD':(1,1),'TSTORE':(2,0),'MCOPY':(3,0),'PUSH0':(0,1),'RETURN':(2,0),'REVERT':(2,0),'CALLVALUE':(0,1),'SELFBALANCE':(0,1),'CHAINID':(0,1),'BASEFEE':(0,1),'GASPRICE':(0,1),'TIMESTAMP':(0,1),'NUMBER':(0,1)}
for i in range(1,33): T['PUSH%d'%i]=(0,1)
for i in range(1,17): T['DUP%d'%i]=(i,i+1); T['SWAP%d'%i]=(i+1,i+1)
for i in range(5): T['LOG%d'%i]=(2+i,0)
src=open(sys.argv[1]).read()
cases=re.split(r'\n\t\tcase ',src)[1:]
bad=0;n=0
for c in cases:
  name=c.split(':')[0].strip()
  if name not in T: print('unknown',name); continue
  n+=1
  pops,push=T[name]
  req=re.search(r'sp < (\d+)',c); lim=re.search(r'sp > (\d+)',c)
  d=re.findall(r'sp ([+-])= (\d+)',c)
  delta=sum((int(v) if s=='+' else -int(v)) for s,v in d)
  if 'opUndefined' in c and not d: pass
  wantreq=pops; wantlim=1024-(push-pops) if push>pops else None
  r=int(req.group(1)) if req else 0
  l=int(lim.group(1)) if lim else None
  okd = (delta==push-pops) or (not d and push==pops)
  okr = (r==wantreq) or (r==0 and wantreq==0)
  okl = (l==wantlim) if wantlim else (l is None)
  if not (okd and okr and okl): bad+=1; print('MISMATCH',name,'req',r,wantreq,'lim',l,wantlim,'delta',delta,push-pops)
print('cases',n,'mismatch',bad)
