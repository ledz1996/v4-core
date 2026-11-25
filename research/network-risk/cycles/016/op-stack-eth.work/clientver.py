import json,urllib.request,collections,sys,concurrent.futures as cf
EP={10:'https://mainnet.optimism.io',8453:'https://mainnet.base.org/',130:'https://mainnet.unichain.org',7777777:'https://rpc.zora.energy/',480:'https://worldchain-mainnet.g.alchemy.com/public',57073:'https://rpc-gel.inkonchain.com',1868:'https://rpc.soneium.org','57073-qnd':'https://rpc-qnd.inkonchain.com'}
def one(u):
  try:
    r=urllib.request.Request(u,data=b'{"jsonrpc":"2.0","id":1,"method":"web3_clientVersion","params":[]}',headers={"content-type":"application/json","user-agent":"curl/8.5.0"})
    return json.load(urllib.request.urlopen(r,timeout=15)).get('result')
  except Exception as e: return 'ERR '+type(e).__name__
out={}
for k,u in EP.items():
  with cf.ThreadPoolExecutor(2) as ex: res=list(ex.map(lambda _: one(u), range(50)))
  out[str(k)]={'url':u,'counts':collections.Counter(res)}
  print(k,dict(out[str(k)]['counts']))
json.dump(out,open(sys.argv[1],'w'),indent=1)
