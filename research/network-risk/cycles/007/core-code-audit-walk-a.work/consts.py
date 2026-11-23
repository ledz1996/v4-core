from keccak import keccak, sel
def slot(s): return hex(int.from_bytes(keccak(s.encode()),'big')-1)
exp = {
 'ReservesOf':'0x1e0745a7db1623981f0b2a5d4232364c00787266eb75ad546f190e6cebe9bd95',
 'Currency':'0x27e098c505d44ec3574004bca052aabf76bd35004c182099d8c575fb238593b9',
 'Unlocked':'0xc090fc4683624cfc3884e9d8de5eca132f2d0ec062aff75d43c0465d5ceeab23',
 'NonzeroDeltaCount':'0x7d4b3164c6e45b97e7d87b7125a44c5828d005af88f9d751cfd78729c5d99a0b'}
for k,v in exp.items(): print(k, slot(k)==v, slot(k))
for sig,want in [('TickMisaligned(int24,int24)','d4d8f3e6'),('SafeCastOverflow()','93dafdf1'),('PriceOverflow()','f5c787f1'),('NotEnoughLiquidity()','4323a555'),('InvalidPriceOrLiquidity()','4f2461b8'),('InvalidPrice()','00bfc921'),('transfer(address,uint256)','a9059cbb'),('supportsInterface(bytes4)','01ffc9a7')]:
    print(sig, sel(sig), sel(sig)==want)
# ERC6909 interface id 0x0f632fb3
ids=['transfer(address,uint256,uint256)','transferFrom(address,address,uint256,uint256)','approve(address,uint256,uint256)','setOperator(address,bool)','balanceOf(address,uint256)','allowance(address,address,uint256)','isOperator(address,address)']
x=0
for s in ids: x^=int(sel(s),16)
print('erc6909 id',hex(x))
# hook selectors vs PoolManager/claims selectors
