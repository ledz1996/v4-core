# Read-only. Sixteen call shapes sent to special addresses from a forwarding stub placed at the
# PoolManager address by state override (Multicall3 runtime code), with an unrelated EOA as tx.origin.
# For every shape the stub reads its own native balance before and after the call.
# usage: stub_sweep.py <chainId> <out.json>
import sys, json, urllib.request, time
from keccak import keccak256
CFG={42220:dict(rpc='https://forno.celo.org',pm='0x288dc841A52FCA2707c6947B3A777c5E56cd87BC'),
     196:dict(rpc='https://rpc.xlayer.tech',pm='0x360e68faccca8ca495c1b759fd9eee466db9fb32')}
cid=int(sys.argv[1]); cfg=CFG[cid]; RPC=cfg['rpc']; PM=cfg['pm']
MC='0xcA11bde05977b3631167028862bE2a173976CA11'; EOA='0x00000000000000000000000000000000000b0b00'; RCPT='0x00000000000000000000000000000000000c0c00'
def post(body):
    for i in range(8):
        try:
            req=urllib.request.Request(RPC, data=json.dumps(body).encode(), headers={'content-type':'application/json','user-agent':'curl/8'})
            return json.loads(urllib.request.urlopen(req, timeout=90).read())
        except Exception as e: time.sleep(2+i)
    raise SystemExit('rpc failed')
def rpc(m,p): return post({'jsonrpc':'2.0','id':1,'method':m,'params':p})
def sel(s): return keccak256(s.encode())[:4]
def w(x): return int(x).to_bytes(32,'big')
def addr(a): return bytes(12)+bytes.fromhex(a[2:])
PK='(address,address,uint24,int24,address)'; MLP='(int24,int24,int256,bytes32)'; SP='(bool,int256,uint160)'
hooks=['beforeInitialize(address,%s,uint160)'%PK,'afterInitialize(address,%s,uint160,int24)'%PK,
 'beforeAddLiquidity(address,%s,%s,bytes)'%(PK,MLP),'afterAddLiquidity(address,%s,%s,int256,int256,bytes)'%(PK,MLP),
 'beforeRemoveLiquidity(address,%s,%s,bytes)'%(PK,MLP),'afterRemoveLiquidity(address,%s,%s,int256,int256,bytes)'%(PK,MLP),
 'beforeSwap(address,%s,%s,bytes)'%(PK,SP),'afterSwap(address,%s,%s,int256,bytes)'%(PK,SP),
 'beforeDonate(address,%s,uint256,uint256,bytes)'%PK,'afterDonate(address,%s,uint256,uint256,bytes)'%PK]
def hookdata(sig):
    # selector plus sixteen words; the last dynamic argument points at an empty bytes value
    n=sig.count(',')+1
    body=bytearray(32*16)
    # put offset of trailing bytes arg at the right head slot when the signature ends with bytes
    if sig.endswith('bytes)'):
        heads=5+ (sig.count(',')-4)  # rough: PoolKey takes five head words
        flat=sig[sig.index('(')+1:-1].replace('(','').replace(')','').split(',')
        nh=len(flat); body=bytearray(32*(nh+1)); body[32*(nh-1):32*nh]=w(32*nh)
    return sel(sig)+bytes(body)
V=10**15
shapes=[('empty,value0',b'',0),('empty,value1e15',b'',V),('transfer(rcpt,0)',sel('transfer(address,uint256)')+addr(RCPT)+w(0),0),
        ('transfer(rcpt,1)',sel('transfer(address,uint256)')+addr(RCPT)+w(1),0),('balanceOf(pm)',sel('balanceOf(address)')+addr(PM),0)]
shapes+=[(h.split('(')[0],hookdata(h),0) for h in hooks]
shapes+=[('unlockCallback',sel('unlockCallback(bytes)')+w(32)+w(0),0)]
assert len(shapes)==16
code=rpc('eth_getCode',[MC,'latest'])['result']
assert len(code)>100
targets=[]
targets+=['0x'+'%040x'%i for i in list(range(1,0x12))+[0x100,0xfd,0xfe,0xff]+list(range(0xf0,0xfd))]
targets+=['0x42000000000000000000000000000000000000%02x'%i for i in range(256)]
extra={42220:['0x471EcE3750Da237f93B8E339c536989b8978a438','0xFeA1B35f1D5f2A58532a70e7A32e6F2D3Bc4F7B1','0x000000000000000000000000000000000000ce10','0x15F344b9E6c3Cb6F0376A36A64928b13F62C6276',
  '0xcD437749E43A154C07F3553504c68fBfD56B8778','0xD533Ca259b330c7A88f74E000a3FaEa2d63B7972','0x0E2A3e05bc9A16F5292A6170456A710cb89C6f72','0x2F25deB3848C207fc8E0c34035B3Ba7fC157602B','0x0357ee22278c922e1d36cfe6b899269b161880c4','0x857bf24e29da0773687e804a743c2e421a394c16',
  '0x765DE816845861e75A25fCA122bb6898B8B1282a','0x6cC083Aed9e3ebe302A6336dBC7c921C9f03349E','0x9380fA34Fd9e4Fd14c06305fd7B6199089eD4eb9','0xefB84935239dAcdecF7c5bA76d8dE40b077B7b33'],
 196:['0x19787404b0c70021b4752028f7e3a92313885B27','0x59055c0ef0be92018b33f877a3eB816355791727','0xe538905cf8410324e03A5A23C1c177a474D59b2b','0x2a3DD3EB832aF982ec71669E178424b10Dca2EDe','0xa40D5f56745a118D0906a34E69aeC8C0Db1cB8fA','0x75231F58b43240C9718Dd58B4967c5114342a86c']}
common=['0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789','0x0000000071727De22E5E9d8BAf0edAc6f37da032','0x4337084D9E255Ff0702461CF8895CE9E3b5Ff108','0x4e59b44847b379578588920cA78FbF26c0B4956C','0x000000000022D473030F116dDEE9F6B43aC78BA3','0xcA11bde05977b3631167028862bE2a173976CA11','0x000F3df6D732807Ef1319fB7B8bB8522d0Beac02','0x0000F90827F1C53a10cb7A02335B175320002935','0x00000000219ab540356cBB839Cbe05303d7705Fa','0x00000961Ef480Eb55e80D19ad83579A64c007002','0x0000BBdDc7CE488642fb579F8B00f3a590007251','0x0000000000000000000000000000000000000000','0xdeaddeaddeaddeaddeaddeaddeaddeaddead0000','0xffffffffffffffffffffffffffffffffffffffff','0xfffffffffffffffffffffffffffffffffffffffe']
targets+=extra[cid]+common
A3V=sel('aggregate3Value((address,bool,uint256,bytes)[])'); GEB=sel('getEthBalance(address)')+addr(PM)
def enc_calls(calls):
    # calls: list of (target, value, data)
    head=b''; tail=b''; n=len(calls); off=32*n
    items=[]
    for t,v,d in calls:
        item=addr(t)+w(1)+w(v)+w(128)+w(len(d))+d+bytes((32-len(d)%32)%32)
        items.append(item)
    for it in items:
        head+=w(off); off+=len(it)
    return A3V+w(32)+w(n)+head+b''.join(items)
def dec(res):
    b=bytes.fromhex(res[2:]); base=32; n=int.from_bytes(b[32:64],'big'); out=[]
    for i in range(n):
        o=int.from_bytes(b[64+32*i:96+32*i],'big')+64
        ok=int.from_bytes(b[o:o+32],'big'); do=int.from_bytes(b[o+32:o+64],'big'); ln=int.from_bytes(b[o+do:o+do+32],'big')
        out.append((ok,b[o+do+32:o+do+32+ln]))
    return out
block=rpc('eth_blockNumber',[])['result']
results=[]
for ti,t in enumerate(targets):
    calls=[]
    for name,data,val in shapes:
        calls+=[(PM,0,GEB),(t,val,data),(PM,0,GEB)]
    tot=sum(c[1] for c in calls)
    body={'jsonrpc':'2.0','id':1,'method':'eth_call','params':[{'from':EOA,'to':PM,'data':'0x'+enc_calls(calls).hex(),'value':hex(tot),'gas':hex(25_000_000)},block,
          {PM:{'code':code,'balance':hex(10**20)},EOA:{'balance':hex(10**20)}}]}
    r=post(body)
    if 'result' not in r:
        results.append(dict(target=t,error=str(r.get('error'))[:200])); print(t,'ERROR',str(r.get('error'))[:150],flush=True); continue
    d=dec(r['result']); row=dict(target=t,shapes=[])
    for k,(name,data,val) in enumerate(shapes):
        b0=int.from_bytes(d[3*k][1],'big'); ok,ret=d[3*k+1]; b1=int.from_bytes(d[3*k+2][1],'big')
        row['shapes'].append(dict(shape=name,ok=ok,retLen=len(ret),ret=ret[:64].hex(),balDelta=b1-b0))
    results.append(row)
    oks=[s['shape']+('/ret%d'%s['retLen'])+('/d%d'%s['balDelta'] if s['balDelta'] else '') for s in row['shapes'] if s['ok']]
    if oks: print(t,oks,flush=True)
json.dump(dict(chainId=cid,block=block,pm=PM,origin=EOA,results=results),open(sys.argv[2],'w'))
print('done',len(results),'targets, block',int(block,16))
