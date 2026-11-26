# Probes of jump destination analysis around the bytes EIP-8024 assigns (e6, e7, e8), by eth_call with a state override. Read-only.
import json, sys, urllib.request
NETS={143:'https://rpc.monad.xyz',4326:'https://mainnet.megaeth.com/rpc'}
A='0x00000000000000000000000000000000c0de8024'
cases=[]
for op in ('e6','e7','e8'):
    cases.append((f'{op}5b valid target',   '600456'+op+'5b600160005260206000f3', True))   # PUSH1 4 JUMP op JUMPDEST -> return 1
    cases.append((f'{op}605b push masks',   '600556'+op+'605b600160005260206000f3', False)) # jump into PUSH1 data must fail
    cases.append((f'{op}805b dupn imm',     '600556'+op+'805b600160005260206000f3', True))  # byte 5 is 0x5b after 0x80 -> valid target
    cases.append((f'{op} executed',         op+'00', False))                                  # undefined before Amsterdam: must fail
cases.append(('clz 0x1e executed', '6001'+'1e'+'60005260206000f3', None))
import time
def rpc(u,m,p):
  for k in range(8):
    try: return rpc1(u,m,p)
    except urllib.error.HTTPError as e:
        if e.code!=429: raise
        time.sleep(3*(k+1))
  raise RuntimeError('rate limited')
def rpc1(u,m,p):
    rq=urllib.request.Request(u,data=json.dumps({'jsonrpc':'2.0','id':1,'method':m,'params':p}).encode(),headers={'content-type':'application/json','user-agent':'curl/8.5.0'})
    return json.load(urllib.request.urlopen(rq,timeout=60))
out={}
for cid,u in NETS.items():
    res=[]
    for name,code,expect in cases:
        r=rpc(u,'eth_call',[{'to':A,'gas':'0x100000'},'latest',{A:{'code':'0x'+code}}])
        ok='result' in r
        res.append({'case':name,'code':code,'success':ok,'result':r.get('result'),'error':(r.get('error') or {}).get('message'),'expectSuccess':expect,'asExpected':(expect is None or ok==expect)})
    out[cid]=res
    print(cid, sum(x['asExpected'] for x in res),'/',len(res), [ (x['case'],x['success'],x['result']) for x in res if x['expectSuccess'] is None or not x['asExpected']])
json.dump(out,open(sys.argv[1],'w'),indent=1)
