RC=[0x0000000000000001,0x0000000000008082,0x800000000000808A,0x8000000080008000,0x000000000000808B,0x0000000080000001,0x8000000080008081,0x8000000000008009,0x000000000000008A,0x0000000000000088,0x0000000080008009,0x000000008000000A,0x000000008000808B,0x800000000000008B,0x8000000000008089,0x8000000000008003,0x8000000000008002,0x8000000000000080,0x000000000000800A,0x800000008000000A,0x8000000080008081,0x8000000000008080,0x0000000080000001,0x8000000080008008]
ROT=[[0,36,3,41,18],[1,44,10,45,2],[62,6,43,15,61],[28,55,25,21,56],[27,20,39,8,14]]
M=(1<<64)-1
def rol(x,n): return ((x<<n)|(x>>(64-n)))&M if n else x
def f(A):
    for rc in RC:
        C=[A[x][0]^A[x][1]^A[x][2]^A[x][3]^A[x][4] for x in range(5)]
        D=[C[(x-1)%5]^rol(C[(x+1)%5],1) for x in range(5)]
        A=[[A[x][y]^D[x] for y in range(5)] for x in range(5)]
        B=[[0]*5 for _ in range(5)]
        for x in range(5):
            for y in range(5):
                B[y][(2*x+3*y)%5]=rol(A[x][y],ROT[x][y])
        A=[[B[x][y]^((~B[(x+1)%5][y])&B[(x+2)%5][y]) for y in range(5)] for x in range(5)]
        A[0][0]^=rc
    return A
def keccak256(data: bytes) -> bytes:
    rate=136; p=bytearray(data); p.append(0x01)
    while len(p)%rate: p.append(0)
    p[-1]|=0x80
    A=[[0]*5 for _ in range(5)]
    for off in range(0,len(p),rate):
        for i in range(rate//8):
            A[i%5][i//5]^=int.from_bytes(p[off+8*i:off+8*i+8],'little')
        A=f(A)
    out=b''.join(A[i%5][i//5].to_bytes(8,'little') for i in range(4))
    return out
if __name__=='__main__':
    assert keccak256(b'').hex()=='c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470'
    assert keccak256(b'transfer(address,uint256)')[:4].hex()=='a9059cbb'
    K='(address,address,uint24,int24,address)'
    sigs=['unlock(bytes)',f'initialize({K},uint160)',f'modifyLiquidity({K},(int24,int24,int256,bytes32),bytes)',f'swap({K},(bool,int256,uint160),bytes)',f'donate({K},uint256,uint256,bytes)','sync(address)','take(address,address,uint256)','settle()','settleFor(address)','clear(address,uint256)','mint(address,uint256,uint256)','burn(address,uint256,uint256)',f'updateDynamicLPFee({K},uint24)','setProtocolFeeController(address)',f'setProtocolFee({K},uint24)','collectProtocolFees(address,address,uint256)','protocolFeesAccrued(address)','protocolFeeController()','owner()','transferOwnership(address)','isOperator(address,address)','balanceOf(address,uint256)','allowance(address,address,uint256)','transfer(address,uint256,uint256)','transferFrom(address,address,uint256,uint256)','approve(address,uint256,uint256)','setOperator(address,bool)','supportsInterface(bytes4)','extsload(bytes32)','extsload(bytes32,uint256)','extsload(bytes32[])','exttload(bytes32)','exttload(bytes32[])']
    own={keccak256(s.encode())[:4].hex():s for s in sigs}
    out=['transfer(address,uint256)','balanceOf(address)','unlockCallback(bytes)',f'beforeInitialize(address,{K},uint160)',f'afterInitialize(address,{K},uint160,int24)',f'beforeAddLiquidity(address,{K},(int24,int24,int256,bytes32),bytes)',f'afterAddLiquidity(address,{K},(int24,int24,int256,bytes32),int256,int256,bytes)',f'beforeRemoveLiquidity(address,{K},(int24,int24,int256,bytes32),bytes)',f'afterRemoveLiquidity(address,{K},(int24,int24,int256,bytes32),int256,int256,bytes)',f'beforeSwap(address,{K},(bool,int256,uint160),bytes)',f'afterSwap(address,{K},(bool,int256,uint160),int256,bytes)',f'beforeDonate(address,{K},uint256,uint256,bytes)',f'afterDonate(address,{K},uint256,uint256,bytes)']
    for s in sigs: print(keccak256(s.encode())[:4].hex(), s)
    print('--- selectors the PoolManager sends')
    for s in out:
        h=keccak256(s.encode())[:4].hex(); print(h, s, 'COLLIDES with '+own[h] if h in own else '')
    print('ManagerLocked()', keccak256(b'ManagerLocked()')[:4].hex())
