import json,sys,urllib.request,time
W='/home/user/v4-core/research/network-risk/'
nets=json.load(open(W+'state/networks.json'))
nets=nets['networks'] if isinstance(nets,dict) else nets
USDC={1:'0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',10:'0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85',8453:'0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913',130:'0x078D782b760474a361dDA0AF3839290b0EF57AD6',480:'0x79A02482A880bCe3F13E09da970dC34dB4cD24D1',57073:'0x2D270e6886d130D724215A266106e6832161EAEd',42220:'0xcebA9300f2b948710d2653dD7B07f33A8B32118C',42161:'0xaf88d065e77c8cC2239327C5EDb3A432268e5831',137:'0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359',43114:'0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E',143:'0x754704Bc059F8C67012fEd69BC8A327a5aafb603',999:'0xb88339CB7199b77E23DB6E890353E22632Ba630f',5042:'0x3600000000000000000000000000000000000000',196:'0xB6CEceAB302E2E4948951eE7843FC24E92933061'}
TM='0x28b5a0e9C621a5BadaA536219b3a228C8168cf5d'; MT='0x81D40F21F12A8F0E3252Bccb954D722d4c464B64'
TRANSFER='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
MAW2='0x50c55e915134d457debfa58eb6f4342956f8b0616d51a89a3659360178e1ab63'
def rpc(url,m,p):
    r=urllib.request.Request(url,data=json.dumps({'jsonrpc':'2.0','id':1,'method':m,'params':p}).encode(),headers={'content-type':'application/json','user-agent':'curl/8'})
    try: return json.load(urllib.request.urlopen(r,timeout=40))
    except Exception as e: return {'error':str(e)}
out={}
for n in nets:
    cid=n['chainId']; u=n['rpc']; pm=n['poolManager'].lower()
    o={'name':n['name']}
    o['tmv2Code']=len(rpc(u,'eth_getCode',[TM,'latest']).get('result','0x'))//2-1
    o['mtv2Code']=len(rpc(u,'eth_getCode',[MT,'latest']).get('result','0x'))//2-1
    bn=int(rpc(u,'eth_blockNumber',[])['result'],16); o['block']=bn
    pmt='0x'+'0'*24+pm[2:]
    if o['tmv2Code']>0:
        r=rpc(u,'eth_getLogs',[{'address':TM,'topics':[MAW2,pmt],'fromBlock':'0x0','toBlock':hex(bn)}])
        o['maw2_full']=r.get('result',r.get('error'))
    if cid in USDC:
        r=rpc(u,'eth_getLogs',[{'address':USDC[cid],'topics':[TRANSFER,'0x'+'0'*64,pmt],'fromBlock':'0x0','toBlock':hex(bn)}])
        o['usdcMintToPM_full']=r.get('result',r.get('error'))
        bal=rpc(u,'eth_call',[{'to':USDC[cid],'data':'0x70a08231'+pmt[2:]},'latest'])
        o['usdcBalPM']=int(bal['result'],16) if 'result' in bal and bal['result']!='0x' else bal
    out[cid]=o; print(cid,json.dumps(o)[:600],flush=True)
json.dump(out,open(sys.argv[1],'w'),indent=1)
