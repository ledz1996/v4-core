import json, urllib.request, hashlib
exec(open('arc_nca2.py').read().split("for url in")[0])
NCC="1800000000000000000000000000000000000001"
# selectors computed offline: blocklist(address)=0x-- need keccak; use a tiny pure python keccak
def keccak256(data: bytes) -> bytes:
    RC=[0x0000000000000001,0x0000000000008082,0x800000000000808A,0x8000000080008000,0x000000000000808B,0x0000000080000001,0x8000000080008081,0x8000000000008009,0x000000000000008A,0x0000000000000088,0x0000000080008009,0x000000008000000A,0x000000008000808B,0x800000000000008B,0x8000000000008089,0x8000000000008003,0x8000000000008002,0x8000000000000080,0x000000000000800A,0x800000008000000A,0x8000000080008081,0x8000000000008080,0x0000000080000001,0x8000000080008008]
    R=[[0,36,3,41,18],[1,44,10,45,2],[62,6,43,15,61],[28,55,25,21,56],[27,20,39,8,14]]
    M=(1<<64)-1
    rol=lambda x,n:((x<<n)|(x>>(64-n)))&M if n else x
    rate=136; p=bytearray(data); p.append(1); 
    while len(p)%rate: p.append(0)
    p[-1]|=0x80
    A=[[0]*5 for _ in range(5)]
    for off in range(0,len(p),rate):
        for i in range(rate//8):
            A[i%5][i//5]^=int.from_bytes(p[off+8*i:off+8*i+8],'little')
        for rnd in range(24):
            C=[A[x][0]^A[x][1]^A[x][2]^A[x][3]^A[x][4] for x in range(5)]
            D=[C[(x-1)%5]^rol(C[(x+1)%5],1) for x in range(5)]
            A=[[A[x][y]^D[x] for y in range(5)] for x in range(5)]
            B=[[0]*5 for _ in range(5)]
            for x in range(5):
                for y in range(5): B[y][(2*x+3*y)%5]=rol(A[x][y],R[x][y])
            A=[[B[x][y]^((~B[(x+1)%5][y])&B[(x+2)%5][y]) for y in range(5)] for x in range(5)]
            A[0][0]^=RC[rnd]
    out=b''.join(A[i%5][i//5].to_bytes(8,'little') for i in range(4))
    return out
assert keccak256(b"transfer(address,uint256)").hex()[:8]=="a9059cbb"
assert keccak256(b"transfer(address,address,uint256)").hex()[:8]=="beabacc8"
sel=keccak256(b"blocklist(address)").hex()[:8]; isb=keccak256(b"isBlocklisted(address)").hex()[:8]
bl=sel+pad(PM); q=isb+pad(PM)
print("selectors",sel,isb)
for url in ["https://rpc.mainnet.arc.io"]:
    print("==",url, rpc(url,"web3_clientVersion",[]).get("result"), int(rpc(url,"eth_blockNumber",[]).get("result","0x0"),16))
    ovc=dict(base); ovc[TOKEN]={"code":CALL_STUB}
    ovs=dict(base); ovs[TOKEN]={"code":STATIC_STUB}
    tests=[("isBlocklisted(PoolManager), plain call                    ",{}, "0x"+NCC, "0x"+q),
           ("A control: stub at token address CALLs blocklist          ",ovc,TOKEN,"0x"+pad(NCC)+bl),
           ("B stub at token CALLs helper, helper DELEGATECALLs        ",ovc,TOKEN,"0x"+pad(S2[2:])+pad(NCC)+bl),
           ("C stub at token CALLs helper, helper uses CALLCODE        ",ovc,TOKEN,"0x"+pad(S4[2:])+pad(NCC)+bl),
           ("E stub at token address STATICCALLs blocklist             ",ovs,TOKEN,"0x"+pad(NCC)+bl),
           ("G ordinary account calls blocklist                        ",{}, "0x"+NCC, "0x"+bl)]
    for name,ov,to,data in tests:
        params=[{"from":V,"to":to,"data":data},"latest"]+([ov] if ov else [])
        print("  ",name,":",show(rpc(url,"eth_call",params)))
