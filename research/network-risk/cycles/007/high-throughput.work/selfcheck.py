from stubs import *
for chain in (143,4326):
    print('chain',chain)
    reqs=[]
    for k in range(4):
        reqs.append(inherited_req(chain,CAL,'',k,v_pm_to_a=10**15,v_a_to_t=7 if k in (0,3) else 0))
    for k in range(4):
        reqs.append(direct_req(chain,CAL,'',k,value=7 if k in (0,3) else 0))
    # callcode with stated value and no balance in A
    reqs.append(inherited_req(chain,CAL,'',3,v_pm_to_a=0,v_a_to_t=7))
    res=batch(reqs,URL[chain])
    for i,r in enumerate(res):
        p=parse(r,i<4 or i==8)
        ret=p.get('ret','')
        print(i,{x:y for x,y in p.items() if x!='ret'},'| callee saw caller',ret[24:64],'value',int(ret[64:128] or '0',16),'address',ret[152:192],'origin',ret[216:256],'selfbal',int(ret[256:320] or '0',16))
