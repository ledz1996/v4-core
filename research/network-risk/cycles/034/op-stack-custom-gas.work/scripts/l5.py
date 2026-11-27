"""Cycle 34 L5 reread: PoolManager code hash, owner, protocolFeeController and their code lengths. Read-only."""
import json, ssl, urllib.request, hashlib, sys
ctx = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
def rpc(u, m, p):
    r = urllib.request.Request(u, data=json.dumps({'jsonrpc':'2.0','id':1,'method':m,'params':p}).encode(), headers={'content-type':'application/json','user-agent':'curl/8'})
    return json.load(urllib.request.urlopen(r, timeout=30, context=ctx))['result']
out = {}
for cid, u, pm in [(42220,'https://forno.celo.org','0x288dc841A52FCA2707c6947B3A777c5E56cd87BC'),(196,'https://rpc.xlayer.tech','0x360e68faccca8ca495c1b759fd9eee466db9fb32')]:
    bn = rpc(u,'eth_blockNumber',[])
    code = bytes.fromhex(rpc(u,'eth_getCode',[pm,bn])[2:])
    own = '0x'+rpc(u,'eth_call',[{'to':pm,'data':'0x8da5cb5b'},bn])[-40:]
    pfc = '0x'+rpc(u,'eth_call',[{'to':pm,'data':'0xf02de3b2'},bn])[-40:]
    oc = (len(rpc(u,'eth_getCode',[own,bn]))-2)//2
    pc = (len(rpc(u,'eth_getCode',[pfc,bn]))-2)//2
    out[cid] = {'block': int(bn,16), 'codeLen': len(code), 'codeSha256': hashlib.sha256(code).hexdigest()[:16], 'owner': own, 'ownerCodeLen': oc, 'pfc': pfc, 'pfcCodeLen': pc,
                'ownerCodeSha256': hashlib.sha256(bytes.fromhex(rpc(u,'eth_getCode',[own,bn])[2:])).hexdigest()[:16]}
json.dump(out, open(sys.argv[1],'w'), indent=1); print(json.dumps(out, indent=1))
