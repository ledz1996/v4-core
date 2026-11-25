import json,urllib.request,sys
def rpc(url,m,p):
    r=urllib.request.Request(url,data=json.dumps({'jsonrpc':'2.0','id':1,'method':m,'params':p}).encode(),headers={'content-type':'application/json','user-agent':'curl/8'})
    try: return json.load(urllib.request.urlopen(r,timeout=40))
    except Exception as e: return {'error':str(e)}
def sel(s):
    return rpc('https://ethereum-rpc.publicnode.com','web3_sha3',['0x'+s.encode().hex()])['result'][:10]
out={}
checks=[('xlayer_bridge','https://rpc.xlayer.tech','0x2a3DD3EB832aF982ec71669E178424b10Dca2EDe','networkID()'),
('eth_lxly_bridge','https://ethereum-rpc.publicnode.com','0x2a3DD3EB832aF982ec71669E178424b10Dca2EDe','networkID()'),
('avax_teleporter','https://api.avax.network/ext/bc/C/rpc','0x253b2784c75e510dD0fF1da844684a1aC0aa5fcf','blockchainID()'),
('pol_statereceiver_replay','https://polygon-bor-rpc.publicnode.com','0x0000000000000000000000000000000000001001','lastStateId()')]
for name,u,a,s in checks:
    code=rpc(u,'eth_getCode',[a,'latest']).get('result','0x')
    sc=sel(s); r=rpc(u,'eth_call',[{'to':a,'data':sc},'latest'])
    out[name]={'rpc':u,'addr':a,'codeLen':len(code)//2-1,'call':s,'selector':sc,'result':r.get('result',r.get('error'))}
    print(name,out[name])
ep='0x0000000071727De22E5E9d8BAf0edAc6f37da032'
nets=json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))['networks']
for n in nets:
    c=rpc(n['rpc'],'eth_getCode',[ep,'latest']).get('result','0x')
    out['ep07_'+str(n['chainId'])]=len(c)//2-1
print({k:v for k,v in out.items() if k.startswith('ep07')})
json.dump(out,open(sys.argv[1],'w'),indent=1)
