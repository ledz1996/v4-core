"""Read-only: binary search the blocks where the PoolManager native balance changed, on an archive endpoint.
Usage: python3 -I balsearch.py <rpc> <lo> <hi> <out.json>"""
import sys, json, urllib.request, time
rpc, lo, hi, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
PM='0x12d4fd9c5dedd00ab8a0bce2cf0167bbf94b6b1f'
def bal(b):
    for k in range(6):
        try:
            r=urllib.request.Request(rpc,data=json.dumps({"jsonrpc":"2.0","id":1,"method":"eth_getBalance","params":[PM,hex(b)]}).encode(),headers={'content-type':'application/json','user-agent':'research-client'})
            x=json.load(urllib.request.urlopen(r,timeout=60))
            if 'result' in x: return int(x['result'],16)
        except Exception as e: pass
        time.sleep(2)
    raise SystemExit('fail at %d'%b)
changes=[]
def search(a,b,ba,bb):
    if ba==bb: return
    if b-a==1: changes.append((b,ba,bb)); print(b,ba,bb,bb-ba,flush=True); return
    m=(a+b)//2; bm=bal(m)
    search(a,m,ba,bm); search(m,b,bm,bb)
search(lo,hi,bal(lo),bal(hi))
json.dump({'rpc':rpc,'lo':lo,'hi':hi,'changes':changes},open(out,'w'))
