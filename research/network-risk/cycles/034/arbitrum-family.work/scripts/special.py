"""Calls from each PoolManager address, at latest, to the EIP-2935 history contract and the
ArbOS sender address 0x...a4b05 in the four shapes the PoolManager can produce for an
ordinary caller: empty calldata with and without value (take of address(0)), transfer(to,1)
(take of a token), balanceOf(PoolManager) (sync). Read-only eth_call with 'from'."""
import json, subprocess, sys
def rpc(u, m, p):
    o = subprocess.run(['curl','-s','--max-time','40','-X','POST','-H','content-type: application/json','--data',json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}),u],capture_output=True,text=True).stdout
    return json.loads(o)
N = {42161:('https://arb1.arbitrum.io/rpc','0x360e68faccca8ca495c1b759fd9eee466db9fb32'),4663:('https://rpc.mainnet.chain.robinhood.com','0x8366a39cc670b4001a1121b8f6a443a643e40951'),99901:('https://rpc.elysium.kinetiq.xyz','0xe2e105d3f7209a9da11f83ccf3e7398a753823f1')}
T = ['0x0000f90827f1c53a10cb7a02335b175320002935','0x00000000000000000000000000000000000a4b05']
out = {}
for c,(u,pm) in N.items():
    for t in T:
        code = rpc(u,'eth_getCode',[t,'latest']).get('result')
        shapes = {'empty': {'from':pm,'to':t,'data':'0x'}, 'emptyValue1': {'from':pm,'to':t,'data':'0x','value':'0x1'},
                  'transfer': {'from':pm,'to':t,'data':'0xa9059cbb'+'00'*12+'11'*20+'%064x'%1},
                  'balanceOf': {'from':pm,'to':t,'data':'0x70a08231'+'00'*12+pm[2:]}}
        r = {'codeLen': (len(code)-2)//2 if code else None}
        for k,tx in shapes.items():
            x = rpc(u,'eth_call',[tx,'latest']); r[k] = x.get('result', x.get('error'))
        out[f'{c}:{t}'] = r; print(c, t, json.dumps(r))
json.dump(out, open(sys.argv[1],'w'), indent=1)
