from sweep_read import *
tag=sys.argv[2] if len(sys.argv)>2 else 'main'; url=sys.argv[1] if len(sys.argv)>1 else OFF
live=json.load(open(f'raw/read_sweep_call_{tag}.json'))
user='4e5319deb1072b01439ee674db5c321d11fd96f8'; ad=lambda a:a.rjust(64,'0')
inputs={'empty':'','pm':ad(PM[2:].lower()),'user':ad(user),'u0':w(0),'u1':w(1),'u150':w(150),'user_0':ad(user)+w(0),'user_150':ad(user)+w(150),'0_user':w(0)+ad(user),'user_user':ad(user)+ad(user),'u10107':w(10107)}
blk=rpc('eth_blockNumber',[],url=url)
reqs=[];keys=[]
for a,s in live.items():
    oks=[n for n,r in s.items() if r.get('ok')==1 and r.get('rds',0)>0]
    fails=[n for n,r in s.items() if r.get('ok')==0]
    pick=oks[:2]+fails[:1]
    for n in pick:
        for k in range(4):
            for val in ((0,7) if k in (0,3) else (0,)):
                reqs.append(req(a,inputs[n],k,v_pm_to_a=10**15,v_a_to_t=val,blk=blk)); keys.append((a,n,k,val))
res=many(reqs,url=url)
json.dump([[list(k),r] for k,r in zip(keys,res)],open(f'raw/read_kinds_{tag}.json','w'))
by={}
for k,r in zip(keys,res): by.setdefault((k[0],k[1]),[]).append((k[2],k[3],r))
for (a,n),lst in by.items():
    base=lst[0][2]
    line=[]
    for kind,val,r in lst:
        same = r.get('ret')==base.get('ret') and r.get('ok')==base.get('ok')
        line.append(f"{KINDS[kind][:4]}{'+v' if val else ''}:ok={r.get('ok')}{'=' if same else '!DIFF'} tb={r.get('target_bal')} Ab={r.get('A_bal',0)-10**15 if 'A_bal' in r else r}")
    print(a[-4:],n,'rds',base.get('rds'),' | '.join(line))
