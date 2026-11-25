import sys, json
sys.path.insert(0,'.')
import lazyreplay as L
D=json.load(open('raw/txs.json'))
h=sys.argv[1]; tx,rec=D['tx'][h]['tx'],D['tx'][h]['rec']; blk=D['blocks'][str(int(tx['blockNumber'],16))]
orig=L.W._call; depthlog=[]
def spy(self, caller, to, value, data, static, depth, code_addr=None, storage_addr=None):
    ok, ret = orig(self, caller, to, value, data, static, depth, code_addr, storage_addr)
    depthlog.append((depth, '%x'%caller, '%x'%to, value, bytes(data[:4]).hex(), ok, ret[:68].hex()))
    return ok, ret
L.W._call=spy
base,w,ok,ret,err,rounds=L.replay('https://rpc.mainnet.arc.io',tx,rec,blk)
for x in depthlog[-60:]: print(x)
print(err, ok, ret[:200].hex() if ret else ret, 'gas', int(tx['gas'],16), 'used', int(rec['gasUsed'],16), 'type', tx['type'])
