# Read-only eth_call of StablecoinDEX tickToPrice/priceToTick on Tempo at edge ticks; compares with 100000+tick.
import json, urllib.request, sys
RPC = "https://rpc.mainnet.tempo.xyz"; DEX = "0xdec0000000000000000000000000000000000000"
from hashlib import sha3_256
def rpc(m, p):
    r = urllib.request.Request(RPC, json.dumps({"jsonrpc": "2.0", "id": 1, "method": m, "params": p}).encode(), {"content-type": "application/json"})
    return json.loads(urllib.request.urlopen(r, timeout=30).read())
def sel(sig):
    import subprocess
    return subprocess.check_output(["node", "-e", "const c=require('crypto');"], text=True) if False else None
out = {"client_start": rpc("web3_clientVersion", [])}
blk = rpc("eth_blockNumber", [])["result"]; out["block"] = blk
# selectors computed with keccak in python below
import importlib
def keccak(b):
    # minimal keccak-256
    RC=[0x0000000000000001,0x0000000000008082,0x800000000000808A,0x8000000080008000,0x000000000000808B,0x0000000080000001,0x8000000080008081,0x8000000000008009,0x000000000000008A,0x0000000000000088,0x0000000080008009,0x000000008000000A,0x000000008000808B,0x800000000000008B,0x8000000000008089,0x8000000000008003,0x8000000000008002,0x8000000000000080,0x000000000000800A,0x800000008000000A,0x8000000080008081,0x8000000000008080,0x0000000080000001,0x8000000080008008]
    r=[[0,36,3,41,18],[1,44,10,45,2],[62,6,43,15,61],[28,55,25,21,56],[27,20,39,8,14]]
    M=(1<<64)-1; rot=lambda x,n:((x<<n)|(x>>(64-n)))&M if n else x
    rate=136; b=bytearray(b)+b'\x01'; b+=b'\x00'*((-len(b))%rate); b[-1]|=0x80
    s=[[0]*5 for _ in range(5)]
    for o in range(0,len(b),rate):
        for i in range(rate//8):
            s[i%5][i//5]^=int.from_bytes(b[o+8*i:o+8*i+8],'little')
        for rc in RC:
            C=[s[x][0]^s[x][1]^s[x][2]^s[x][3]^s[x][4] for x in range(5)]
            D=[C[(x-1)%5]^rot(C[(x+1)%5],1) for x in range(5)]
            s=[[s[x][y]^D[x] for y in range(5)] for x in range(5)]
            B=[[0]*5 for _ in range(5)]
            for x in range(5):
                for y in range(5): B[y][(2*x+3*y)%5]=rot(s[x][y],r[x][y])
            s=[[B[x][y]^((~B[(x+1)%5][y])&B[(x+2)%5][y]) for y in range(5)] for x in range(5)]
            s[0][0]^=rc
    return b''.join(s[i%5][i//5].to_bytes(8,'little') for i in range(4))
assert keccak(b'').hex().startswith('c5d2460186f7233c')
S_T = keccak(b"tickToPrice(int16)")[:4].hex(); S_P = keccak(b"priceToTick(uint32)")[:4].hex()
res = []
ticks = [-32760, -10000, -2010, -2000, -1990, -10, 0, 10, 1990, 2000, 2010, 10000, 32760, -1, 1, -32768, 32767]
for t in ticks:
    d = "0x" + S_T + (t % (1 << 256)).to_bytes(32, 'big').hex()
    r = rpc("eth_call", [{"to": DEX, "data": d}, blk])
    got = int(r["result"], 16) if "result" in r and r["result"] != "0x" else None
    res.append({"fn": "tickToPrice", "tick": t, "data": d, "resp": r, "got": got, "expected": 100000 + t, "match": got == 100000 + t})
for p in [0, 1, 67232, 97990, 98000, 100000, 102000, 102010, 2**32 - 1]:
    d = "0x" + S_P + p.to_bytes(32, 'big').hex()
    r = rpc("eth_call", [{"to": DEX, "data": d}, blk])
    got = None
    if "result" in r and len(r["result"]) == 66:
        v = int(r["result"], 16); got = v - (1 << 256) if v >> 255 else v
    exp = p - 100000 if 98000 <= p <= 102000 else "revert"
    res.append({"fn": "priceToTick", "price": p, "data": d, "resp": r, "got": got, "expected": exp})
out["results"] = res
out["client_end"] = rpc("web3_clientVersion", [])
json.dump(out, open(sys.argv[1], "w"), indent=1)
for x in res: print(x["fn"], x.get("tick", x.get("price")), x["got"], x["expected"], (x["resp"].get("error") or {}).get("message", "")[:60])
