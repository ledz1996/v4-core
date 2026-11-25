"""L-896 screen: Swap events of v3 style, Algebra and v4 pools on HyperEVM whose token0 amount is
large enough that the overflow fallback of getNextSqrtPriceFromAmount0RoundingUp could be reached.
The fallback needs amount * sqrtPrice >= 2^256 - 2^224 with sqrtPrice < 2^160, so |amount0| >= 2^95
is a necessary condition. Events that pass the screen are written out with the logged price.
Usage: fbscan.py <out.json> <fromBlock> <toBlock> [rpc]"""
import sys, json, urllib.request, time
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import keccak
def kec(s): return '0x'+keccak(s.encode()).hex()
T={'v3':kec('Swap(address,address,int256,int256,uint160,uint128,int24)'),
   'alg12':kec('Swap(address,address,int256,int256,uint160,uint128,int24,uint24,uint24)'),
   'v4':kec('Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)')}
out, lo, hi = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); U = sys.argv[4] if len(sys.argv) > 4 else 'https://rpc.purroofgroup.com'
def rpc(m,p):
    for k in range(5):
        try:
            r=urllib.request.Request(U,data=json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}).encode(),headers={'content-type':'application/json','user-agent':'curl/8'})
            j=json.load(urllib.request.urlopen(r,timeout=120))
            if 'error' in j: raise RuntimeError(j['error'])
            return j['result']
        except Exception as e: err=e; time.sleep(2*(k+1))
    raise err
def s256(h): v=int(h,16); return v-(1<<256) if v>>255 else v
inv={v:k for k,v in T.items()}
cnt={k:0 for k in T}; hits=[]; maxr=0; maxrec=None; span=2000; b=lo
while b<=hi:
    e=min(hi,b+span-1)
    try: logs=rpc('eth_getLogs',[{'fromBlock':hex(b),'toBlock':hex(e),'topics':[list(T.values())]}])
    except Exception as ex:
        if span>50: span//=2; continue
        raise
    for l in logs:
        kind=inv[l['topics'][0]]; d=l['data'][2:]
        if kind=='v3' and len(d)!=5*64: continue
        if kind=='alg12' and len(d)!=7*64: continue
        if kind=='v4' and len(d)!=6*64: continue
        cnt[kind]+=1
        a0=s256(d[0:64]); p=int(d[128:192],16)
        r=abs(a0)*max(p,1)
        if r>maxr: maxr=r; maxrec=(kind,l['address'],int(l['blockNumber'],16),l['transactionHash'],a0,p)
        if abs(a0)>=1<<95: hits.append({'kind':kind,'pool':l['address'],'block':int(l['blockNumber'],16),'tx':l['transactionHash'],'amount0':a0,'sqrtP':p,'log2prod':(r.bit_length())})
    b=e+1
    if (b-lo)//span%25==0: print(b,cnt,len(hits),flush=True)
json.dump({'range':[lo,hi],'rpc':U,'counts':cnt,'hits':hits,'maxProductLog2':maxr.bit_length(),'maxRecord':maxrec},open(out,'w'),indent=1)
print('done',cnt,len(hits),'max log2(|a0|*p)',maxr.bit_length(),maxrec)
