from stubs import *
import sys,time
def req(target,data,kind,v_pm_to_a=0,v_a_to_t=0,gas=3_000_000,blk='latest'):
    inner=bytes([kind]).hex()+target[2:].rjust(40,'0')+w(v_a_to_t)+data
    outer=A[2:]+w(v_pm_to_a)+inner
    ov={PM:{'code':F},A:{'code':K},EOA:{'balance':hex(10**20)},CAL:{'code':C}}
    return ('eth_call',[{'from':EOA,'to':PM,'data':'0x'+outer,'gas':hex(gas)},blk,ov])
def dec(r):
    if 'error' in r: return {'err':json.dumps(r['error'])[:160]}
    b=bytes.fromhex(r['result'][2:]); okF=int.from_bytes(b[:32],'big'); rest=b[32:]
    if not okF or len(rest)<192: return {'pm_call_ok':okF,'raw':rest.hex()[:200]}
    g=lambda i:int.from_bytes(rest[32*i:32*i+32],'big')
    return {'ok':g(0),'A_bal':g(2),'target_bal':g(3),'rds':g(5),'ret':rest[192:].hex()}
def many(reqs,url=OFF,chunk=20,pause=1.0):
    out=[]
    for i in range(0,len(reqs),chunk):
        for attempt in range(5):
            try:
                js=batch(reqs[i:i+chunk],url=url)
                if isinstance(js,dict): raise Exception(str(js)[:200])
                break
            except Exception as e:
                print('retry',str(e)[:100],file=sys.stderr); time.sleep(5*(attempt+1))
        out+=[dec(j) for j in js]; time.sleep(pause)
    return out
if __name__=='__main__':
    url=OFF if len(sys.argv)<2 else sys.argv[1]
    tag='main' if len(sys.argv)<3 else sys.argv[2]
    user='4e5319deb1072b01439ee674db5c321d11fd96f8'
    ad=lambda a:a.rjust(64,'0')
    inputs={'empty':'','pm':ad(PM[2:].lower()),'user':ad(user),'u0':w(0),'u1':w(1),'u150':w(150),'user_0':ad(user)+w(0),'user_150':ad(user)+w(150),'0_user':w(0)+ad(user),'user_user':ad(user)+ad(user),'u10107':w(10107)}
    addrs=['0x'+hex(x)[2:].rjust(40,'0') for x in range(0x800,0x830)]
    reqs=[];keys=[]
    for a in addrs:
        for n,d in inputs.items():
            reqs.append(req(a,d,0)); keys.append((a,n))
    res=many(reqs,url=url)
    live={}
    for (a,n),r in zip(keys,res):
        live.setdefault(a,{})[n]=r
    json.dump(live,open(f'raw/read_sweep_call_{tag}.json','w'))
    for a in addrs:
        s=live[a]
        summ={n:('FAIL' if r.get('ok')==0 else ('E' if 'err' in r or 'raw' in r else r['rds'])) for n,r in s.items()}
        print(a[-4:],summ)
