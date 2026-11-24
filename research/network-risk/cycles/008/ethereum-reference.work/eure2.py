import json,sys,collections; from lib import *
from decimal import Decimal, getcontext
getcontext().prec=60
URL='https://mainnet.gateway.tenderly.co'; PM='0x000000000004444c5dc75cB358380D2e3dE08A90'; SV='0x7ffe42c4a5deea5b0fec41c94c136cf115597227'
V1='0x3231cb76718cdef2155fc47b5286d82e6eda273f'; V2='0x39b8b6385416f4ca36a20319f70d28621895279d'
pools=json.load(open('raw_eure_pools.json'))
TML='0x'+keccak256(b'ModifyLiquidity(bytes32,address,int24,int24,int256,bytes32)').hex()
TSW='0x'+keccak256(b'Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)').hex()
head=int(rpc(URL,'eth_blockNumber',[])['result'],16)
def s(x,bits=256):
    return x-(1<<bits) if x>>(bits-1) else x
def sqrt_at(tick): return Decimal('1.0001')**(Decimal(tick)/2)
tot=collections.defaultdict(Decimal); rows=[]
for p in pools:
    r=rpc(URL,'eth_getLogs',[{'address':PM,'topics':[TML,p['id']],'fromBlock':hex(p['block']),'toBlock':hex(head)}],timeout=90)
    pos=collections.defaultdict(int)
    for l in r['result']:
        d=bytes.fromhex(l['data'][2:]); tl=s(int.from_bytes(d[0:32],'big')); tu=s(int.from_bytes(d[32:64],'big')); ld=s(int.from_bytes(d[64:96],'big')); salt=d[96:128].hex()
        pos[(l['topics'][2],tl,tu,salt)]+=ld
    rs=rpc(URL,'eth_getLogs',[{'address':PM,'topics':[TSW,p['id']],'fromBlock':hex(p['block']),'toBlock':hex(head)}],timeout=90)
    nsw=len(rs.get('result',[]))
    g=rpc(URL,'eth_call',[{'to':SV,'data':'0x'+cd('getSlot0(bytes32)',p['id'])},'latest'])['result']
    b=bytes.fromhex(g[2:]); sqrtX=int.from_bytes(b[0:32],'big'); tick=s(int.from_bytes(b[32:64],'big'))
    sp=Decimal(sqrtX)/Decimal(2**96)
    is0 = p['c0'] in (V1,V2)
    amt=Decimal(0); live=0
    for (o,tl,tu,salt),L in pos.items():
        if L<=0: continue
        live+=1
        sa=sqrt_at(tl); sb=sqrt_at(tu)
        if is0:
            a = L*(1/sa-1/sb) if sp<=sa else (L*(1/sp-1/sb) if sp<sb else Decimal(0))
        else:
            a = Decimal(0) if sp<=sa else (L*(sp-sa) if sp<sb else L*(sb-sa))
        amt+=a
    tot[p['ver']]+=amt
    rows.append({'ver':p['ver'],'id':p['id'],'other':p['c1'] if is0 else p['c0'],'fee':p['fee'],'hooks':p['hooks'],'livePositions':live,'modifyEvents':len(r['result']),'swaps':nsw,'tick':tick,'eurePrincipal':float(amt/Decimal(10**18))})
    print(p['ver'],p['id'][:12],'other',rows[-1]['other'][:10],'fee',p['fee'],'hook',p['hooks'][:8],'live',live,'mods',len(r['result']),'swaps',nsw,'EURe principal %.4f'%rows[-1]['eurePrincipal'],flush=True)
print({k:float(v/Decimal(10**18)) for k,v in tot.items()})
for name,a in (('V1',V1),('V2',V2)):
    bal=int(rpc(URL,'eth_call',[{'to':a,'data':'0x'+cd('balanceOf(address)',PM)},'latest'])['result'],16)
    pf=int(rpc(URL,'eth_call',[{'to':PM,'data':'0x'+cd('protocolFeesAccrued(address)',a)},'latest'])['result'],16)
    print(name,'balanceOf(PM)',bal/1e18,'protocolFeesAccrued',pf/1e18)
json.dump({'head':head,'rows':rows,'totals':{k:float(v/Decimal(10**18)) for k,v in tot.items()}},open('raw_eure_owed.json','w'),indent=0)
