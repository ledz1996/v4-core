"""Stability of web3_clientVersion over 20 requests and support for eth_call with a code override. Read-only."""
import sys, json, collections
sys.path.insert(0,'/home/user/v4-core/research/network-risk/tools/opdiff')
import evm
U=['https://eth.api.pocket.network','https://public-eth.nownodes.io','https://ethereum.public.blockpi.network/v1/rpc/public','https://eth-pokt.nodies.app','https://eth.blockrazor.xyz','https://eth-mainnet.public.blastapi.io','https://rpc.flashbots.net','https://eth.rpc.blxrbdn.com','https://eth.drpc.org']
# code: PUSH1 0x2a PUSH0 MSTORE PUSH1 32 PUSH0 RETURN (PUSH0 tests Shanghai) + MCOPY not needed
code=bytes.fromhex('602a5f5260205ff3')
out={}
for u in U:
    c=collections.Counter()
    for i in range(20):
        try: c[evm.rpc(u,'web3_clientVersion',[],20)]+=1
        except Exception as e: c['ERR '+str(e)[:60]]+=1
    try: r=evm.call_code(u,code,b'',retries=1).hex()
    except Exception as e: r='ERR '+str(e)[:120]
    try: g=evm.rpc(u,'eth_call',[{'to':evm.STUB,'data':'0x'},'latest',{evm.STUB:{'code':'0x5a5f5260205ff3'}}],30)
    except Exception as e: g='ERR '+str(e)[:100]
    out[u]={'versions':dict(c),'override':r,'gasWord':g}
    print(u,dict(c),r[-4:],g)
json.dump(out,open('probe.json','w'),indent=1)
