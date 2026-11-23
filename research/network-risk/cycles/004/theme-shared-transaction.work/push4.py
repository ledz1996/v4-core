# List the PUSH4 constants of a contract's runtime code and name those that are PoolManager or ERC-20 selectors.
import sys
from lib import *
K='(address,address,uint24,int24,address)'
sigs=['unlock(bytes)',f'initialize({K},uint160)',f'modifyLiquidity({K},(int24,int24,int256,bytes32),bytes)',f'swap({K},(bool,int256,uint160),bytes)',f'donate({K},uint256,uint256,bytes)','sync(address)','take(address,address,uint256)','settle()','settleFor(address)','clear(address,uint256)','mint(address,uint256,uint256)','burn(address,uint256,uint256)','extsload(bytes32)','extsload(bytes32,uint256)','extsload(bytes32[])','exttload(bytes32)','exttload(bytes32[])','transfer(address,uint256)','transferFrom(address,address,uint256)','balanceOf(address)','unlockCallback(bytes)','transferFrom(address,address,uint160,address)','deposit()','withdraw(uint256)','approve(address,uint256)','lockAcquired(bytes)','lock(bytes)','vault()','settleAndMintRefund(address,address)','settle(address)','lock(address,bytes)']
M={sel(s):s for s in sigs}
def push4(code):
    b=bytes.fromhex(code[2:]); i=0; out={}
    while i<len(b):
        op=b[i]
        if 0x60<=op<=0x7f:
            n=op-0x5f
            if n==4: out[b[i+1:i+5].hex()]=out.get(b[i+1:i+5].hex(),0)+1
            if n==32 and b[i+5:i+33]==bytes(28): out[b[i+1:i+5].hex()]=out.get(b[i+1:i+5].hex(),0)+1
            i+=n
        i+=1
    return out
if __name__=='__main__':
    cid=int(sys.argv[1]); a=sys.argv[2]
    c=rpc(net(cid)['rpc'],'eth_getCode',[a,'latest']); p=push4(c)
    print(cid,a,'len',len(c)//2-1,'push4 count',len(p))
    print('  known:',{M[k]:v for k,v in p.items() if k in M})
    if len(sys.argv)>3: print('  all:',sorted(p))
