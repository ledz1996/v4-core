from lib import *
import time
TEST='https://rpc.hyperliquid-testnet.xyz/evm'
EOA='0xe0a0000000000000000000000000000000000e0a'
res={}
def bt(calls,u):
    for i in range(6):
        try: return batch(calls,url=u)
        except Exception as e: print('retry',str(e)[:120]); time.sleep(8*(i+1))
    raise
for name,u in (('mainnet',OFF),('testnet',TEST)):
    blk=rpc('eth_getBlockByNumber',['latest',False],url=u)
    print(name,'block',int(blk['number'],16),'fields',len(blk.keys()),'requestsHash' in blk,'gasLimit',int(blk['gasLimit'],16),'basefee',int(blk['baseFeePerGas'],16))
    addrs=list(range(0,0x120))+list(range(0x7f0,0x900))+list(range(0x1000,0x1010))+[0x2222222222222222222222222222222222222222,0x3333333333333333333333333333333333333333,0x4444444444444444444444444444444444444444,0x5555555555555555555555555555555555555555,0x0000F90827F1C53a10cb7A02335B175320002935,0x000F3df6D732807Ef1319fB7B8bB8522d0Beac02,0x00000961Ef480Eb55e80D19ad83579A64c007002,0x0000BBdDc7CE488642fb579F8B00f3a590007251]
    out={}
    for i in range(0,len(addrs),10):
        chunk=addrs[i:i+10]
        calls=[]
        for a in chunk:
            ah='0x'+hex(a)[2:].rjust(40,'0')
            calls.append(('eth_call',[{'from':EOA,'to':ah,'data':'0x','gas':hex(500000)},'latest']))
            calls.append(('eth_getCode',[ah,'latest']))
        js=bt(calls,u)
        for j,a in enumerate(chunk):
            e,c=js[2*j],js[2*j+1]
            f=lambda x:('ERR:'+x['error']['message'][:40]) if 'error' in x else x['result'][:74]
            out[hex(a)]=(f(e),(len(c.get('result','0x'))-2)//2)
        time.sleep(1.2)
    res[name]=out
json.dump(res,open('raw/lowaddr_main_vs_test.json','w'))
m,t=res['mainnet'],res['testnet']
def cls(x): return ('E' if x[0].startswith('ERR') else ('0' if x[0]=='0x' else 'D'),x[1]>0)
print('addresses with any activity on mainnet:',{k:cls(m[k]) for k in m if cls(m[k])!=('0',False)})
print('class differs mainnet vs testnet:',{k:(m[k],t[k]) for k in m if cls(m[k])!=cls(t[k])})
