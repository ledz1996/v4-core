# Read-only. Fetch eth_getProof for a contract with candidate storage slots and check whether the
# storage trie holds any leaf other than the candidates. usage: storage_trie.py <rpc> <address> <block> <slot>...
import sys, json, urllib.request
from keccak import keccak256
def post(u, body):
    req=urllib.request.Request(u, data=json.dumps(body).encode(), headers={'content-type':'application/json','user-agent':'curl/8'})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())
def rlp_dec(b, i=0):
    p=b[i]
    if p<0x80: return b[i:i+1], i+1
    if p<0xb8:
        l=p-0x80; return b[i+1:i+1+l], i+1+l
    if p<0xc0:
        ll=p-0xb7; l=int.from_bytes(b[i+1:i+1+ll],'big'); return b[i+1+ll:i+1+ll+l], i+1+ll+l
    if p<0xf8:
        l=p-0xc0; end=i+1+l; j=i+1; out=[]
        while j<end:
            x,j=rlp_dec(b,j); out.append(x)
        return out, end
    ll=p-0xf7; l=int.from_bytes(b[i+1:i+1+ll],'big'); j=i+1+ll; end=j+l; out=[]
    while j<end:
        x,j=rlp_dec(b,j); out.append(x)
    return out, end
u,addr,block=sys.argv[1:4]; slots=sys.argv[4:]
r=post(u,{'jsonrpc':'2.0','id':1,'method':'eth_getProof','params':[addr,slots,block]})
if 'result' not in r: print(r); sys.exit(1)
r=r['result']
print('storageHash',r['storageHash'],'nonce',r['nonce'],'balance',r['balance'])
nodes={}
for sp in r['storageProof']:
    print('slot',sp['key'],'value',sp['value'],'proofLen',len(sp['proof']))
    for n in sp['proof']:
        raw=bytes.fromhex(n[2:]); nodes[keccak256(raw)]=raw
root=bytes.fromhex(r['storageHash'][2:])
leaves=[]; unknown=[]
def walk(ref, path):
    if isinstance(ref,list): node=ref
    else:
        if len(ref)==0: return
        if len(ref)==32:
            if ref not in nodes: unknown.append(path); return
            node,_=rlp_dec(nodes[ref])
        else:
            node,_=rlp_dec(ref)
    if len(node)==17:
        for k in range(16):
            c=node[k]
            if isinstance(c,list) or len(c)>0: walk(c, path+'%x'%k)
        if len(node[16])>0: leaves.append((path,'branch-value'))
    else:
        hp=node[0]; flag=hp[0]>>4
        nib=hp.hex()[2:] if flag in (0,2) else hp.hex()[1:]
        if flag>=2: leaves.append((path+nib, node[1].hex()))
        else: walk(node[1], path+nib)
walk(root,'')
print('leaves reached',len(leaves))
want={keccak256(bytes.fromhex(s[2:].rjust(64,'0'))).hex():s for s in slots}
for p,v in leaves: print('  leaf',p,'value',v,'slot',want.get(p,'UNKNOWN SLOT'))
print('subtrees not covered by the proofs',len(unknown),unknown)
