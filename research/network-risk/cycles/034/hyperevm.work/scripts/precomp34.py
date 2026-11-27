"""Probe 0x0800-0x083f and 0x0100-0x0113 on the official node with one 32 byte zero input, plus code hashes of
the HyperCore system contracts. Read-only eth_call / eth_getCode."""
import json,sys,urllib.request,hashlib
U="https://rpc.hyperliquid.xyz/evm"
def rpc(m,p):
  r=urllib.request.Request(U,data=json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}).encode(),headers={"content-type":"application/json","user-agent":"network-review-client"})
  try: return json.loads(urllib.request.urlopen(r,timeout=60).read())
  except Exception as e: return {"error":str(e)}
out={"precompiles":{},"code":{}}
for a in list(range(0x800,0x840))+list(range(0x1,0x14))+[0x100]:
  addr="0x%040x"%a
  r=rpc("eth_call",[{"to":addr,"data":"0x"+"00"*32,"gas":hex(200000)},"latest"])
  out["precompiles"][addr]=r.get("result",r.get("error"))
for a in ["0x3333333333333333333333333333333333333333","0x2222222222222222222222222222222222222222","0x5555555555555555555555555555555555555555","0x6b9e773128f453f5c2c60935ee2de2cbc5390a24","0xb88339cb7199b77e23db6e890353e22632ba630f"]:
  c=rpc("eth_getCode",[a,"latest"]).get("result") or "0x"
  out["code"][a]={"len":(len(c)-2)//2,"sha256":hashlib.sha256(bytes.fromhex(c[2:])).hexdigest()}
json.dump(out,open(sys.argv[1],"w"),indent=1)
for k,v in out["precompiles"].items(): print(k[-4:], json.dumps(v)[:110])
print(json.dumps(out["code"],indent=0))
