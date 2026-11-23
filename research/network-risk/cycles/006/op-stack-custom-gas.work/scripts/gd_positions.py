# Read-only. For every G$ pool of the Celo PoolManager: read slot0 and liquidity through StateView,
# collect ModifyLiquidity logs through Blockscout, net them per position and estimate the G$ held.
import json, urllib.request, math, sys, time
from keccak import keccak256
PM='0x288dc841A52FCA2707c6947B3A777c5E56cd87BC'; SV='0xbc21f8720babf4b20d195ee5c6e99c52b76f2bfb'; POSM='0xf7965f3981e4d5bc383bfbcb61501763e9068ca9'
G='0x62b8b11039fcfe5ab0c56e502b1c372a3d2a9c7a'
ML='0x'+keccak256(b'ModifyLiquidity(bytes32,address,int24,int24,int256,bytes32)').hex()
def get(url):
    for i in range(6):
        try:
            req=urllib.request.Request(url, headers={'user-agent':'curl/8'})
            return json.loads(urllib.request.urlopen(req, timeout=90).read())
        except Exception as e: time.sleep(2+i)
    raise SystemExit('fail '+url)
def call(to,data):
    body={'jsonrpc':'2.0','id':1,'method':'eth_call','params':[{'to':to,'data':data},'latest']}
    req=urllib.request.Request('https://forno.celo.org', data=json.dumps(body).encode(), headers={'content-type':'application/json','user-agent':'curl/8'})
    return json.loads(urllib.request.urlopen(req, timeout=60).read()).get('result')
def sel(s): return '0x'+keccak256(s.encode())[:4].hex()
def s256(x): return x-(1<<256) if x>>255 else x
pools=[]
for f in ('init_c0.json','init_c1.json'):
    for l in json.load(open(f))['result']:
        t=l['topics']; d=l['data'][2:]
        pools.append(dict(id=t[1],c0='0x'+t[2][-40:],c1='0x'+t[3][-40:],fee=int(d[0:64],16),ts=int(d[64:128],16),block=int(l['blockNumber'],16)))
out=[]
for p in pools:
    r=call(SV, sel('getSlot0(bytes32)')+p['id'][2:])
    sqrtP=int(r[2:66],16); tick=s256(int(r[66:130],16))
    liq=int(call(SV, sel('getLiquidity(bytes32)')+p['id'][2:]),16)
    logs=[]; frm=p['block']
    while True:
        j=get(f"https://celo.blockscout.com/api?module=logs&action=getLogs&fromBlock={frm}&toBlock=latest&address={PM}&topic0={ML}&topic1={p['id']}&topic0_1_opr=and")
        res=j.get('result') or []
        new=[l for l in res if (l['transactionHash'],l['logIndex']) not in {(x['transactionHash'],x['logIndex']) for x in logs}]
        logs+=new
        if len(res)<1000 or not new: break
        frm=int(res[-1]['blockNumber'],16)
    pos={}
    for l in logs:
        d=l['data'][2:]; sender='0x'+l['topics'][2][-40:]
        tl=s256(int(d[0:64],16)); tu=s256(int(d[64:128],16)); dl=s256(int(d[128:192],16)); salt=d[192:256]
        k=(sender,tl,tu,salt); pos[k]=pos.get(k,0)+dl
    sp=sqrtP/2**96; gd0=(p['c0']==G)
    rows=[]
    for (sender,tl,tu,salt),L in pos.items():
        if L<=0: continue
        sa=math.sqrt(1.0001**tl); sb=math.sqrt(1.0001**tu)
        if sp<=sa: a0=L*(sb-sa)/(sa*sb); a1=0
        elif sp>=sb: a0=0; a1=L*(sb-sa)
        else: a0=L*(sb-sp)/(sp*sb); a1=L*(sp-sa)
        rows.append(dict(sender=sender,tickLower=tl,tickUpper=tu,salt=salt,liquidity=L,gd=(a0 if gd0 else a1)/1e18,otherRaw=(a1 if gd0 else a0)))
    rows.sort(key=lambda r:-r['gd'])
    tot=sum(r['gd'] for r in rows)
    print('pool',p['id'],'c0',p['c0'],'c1',p['c1'],'fee',p['fee'],'ts',p['ts'],'tick',tick,'liq',liq,'logs',len(logs),'openPositions',len(rows),'G$ in positions %.2f'%tot)
    for r in rows[:6]:
        owner=None
        if r['sender']==POSM.lower():
            o=call(POSM, sel('ownerOf(uint256)')+r['salt'])
            owner='0x'+o[-40:] if o else None
        print('    G$ %.2f'%r['gd'],'other raw %.0f'%r['otherRaw'],'ticks',r['tickLower'],r['tickUpper'],'sender',r['sender'],'tokenId',int(r['salt'],16),'owner',owner)
    out.append(dict(pool=p,tick=tick,liquidity=liq,logs=len(logs),positions=rows[:50],gdTotal=tot))
json.dump(out,open(sys.argv[1],'w'),indent=1)
bal=int(call(G, sel('balanceOf(address)')+PM[2:].lower().rjust(64,'0')),16)/1e18
print('G$ balanceOf(PoolManager) %.2f'%bal, 'sum over pools %.2f'%sum(o['gdTotal'] for o in out))
