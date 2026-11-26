"""usage: codematch.py <rpc> <out.json> addr... ; compares eth_getCode with build runtime, immutable set to the address"""
import sys,json,hashlib,time
sys.path.insert(0,'scripts'); from rpc import call
sys.path.insert(0,'/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import keccak
B=json.load(open('/home/user/v4-core/research/network-risk/build/PoolManager.json'))
def code_for(pm):
    c=bytearray(bytes.fromhex(B['runtime'].removeprefix('0x')))
    for r in B['immutableReferences']['1375']:
        c[r['start']:r['start']+32]=int(pm,16).to_bytes(32,'big')
    return bytes(c)
def masked(code):
    c=bytearray(code)
    for r in B['immutableReferences']['1375']:
        if r['start']+32<=len(c): c[r['start']:r['start']+32]=b'\0'*32
    return bytes(c)
U=sys.argv[1]; res={'client':[call(U,'web3_clientVersion',[]).get('result')],'time':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'addrs':{}}
exp=code_for('0x'+'00'*20); expm=masked(exp)
for a in sys.argv[3:]:
    g=bytes.fromhex(call(U,'eth_getCode',[a,'latest'])['result'][2:])
    imm=[g[r['start']+12:r['start']+32].hex() for r in B['immutableReferences']['1375']] if len(g)>=len(exp) else []
    res['addrs'][a]={'len':len(g),'keccak':'0x'+keccak(g).hex(),'equalsBuildWithImmutable':g==code_for(a),'equalsMasked':masked(g)==expm,'immutables':sorted(set(imm))}
    print(a,res['addrs'][a])
res['client'].append(call(U,'web3_clientVersion',[]).get('result'))
json.dump(res,open(sys.argv[2],'w'),indent=1); print(res['client'])
