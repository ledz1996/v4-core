"""Fetch PoolManager logs on MegaETH from a start block to head, read-only eth_getLogs. Usage: logs.py <from> <out.json>"""
import json,sys,urllib.request
R='https://mainnet.megaeth.com/rpc'; PM='0xacb7e78fa05d562e0a5d3089ec896d57d057d38e'
def rpc(m,p):
  r=urllib.request.Request(R,data=json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}).encode(),headers={'content-type':'application/json','user-agent':'curl/8'})
  return json.load(urllib.request.urlopen(r,timeout=120))
fr=int(sys.argv[1]); head=int(rpc('eth_blockNumber',[])['result'],16); out=[]
b=fr
while b<=head:
  e=min(b+1999,head); x=rpc('eth_getLogs',[{"address":PM,"fromBlock":hex(b),"toBlock":hex(e)}])
  out+=x['result']; b=e+1
json.dump({"from":fr,"to":head,"logs":out},open(sys.argv[2],'w'))
print(fr,head,len(out),len({l['transactionHash'] for l in out}),len({l['blockNumber'] for l in out}))
