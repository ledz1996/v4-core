import json,urllib.request,sys
sys.argv=['x']
exec(open('limits.py').read().split("for n in [int(x)")[0])
loopc=bytes.fromhex('5b600056')  # JUMPDEST PUSH1 0 JUMP
ov={C:{'code':'0x'+loopc.hex()},P:{'code':'0x'+parent.hex()}}
r=rpc('eth_call',[{'from':'0x'+'a1'*20,'to':P,'data':'0x%064x'%0,'gas':hex(9_000_000_000)},'latest',ov])
print(str(r)[:400])
if 'result' in r:
    o=bytes.fromhex(r['result'][2:]); print('child success',int.from_bytes(o[:32],'big'),'revert',o[64:].hex())
