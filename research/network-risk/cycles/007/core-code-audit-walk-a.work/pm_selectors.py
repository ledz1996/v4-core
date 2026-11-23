# Selectors of every external function of PoolManager (read from src by hand) against every selector the PoolManager can send.
from keccak import sel
PK='(address,address,uint24,int24,address)'
pm=['unlock(bytes)','initialize(%s,uint160)'%PK,'modifyLiquidity(%s,(int24,int24,int256,bytes32),bytes)'%PK,'swap(%s,(bool,int256,uint160),bytes)'%PK,
'donate(%s,uint256,uint256,bytes)'%PK,'sync(address)','take(address,address,uint256)','settle()','settleFor(address)','clear(address,uint256)','mint(address,uint256,uint256)',
'burn(address,uint256,uint256)','updateDynamicLPFee(%s,uint24)'%PK,'protocolFeesAccrued(address)','protocolFeeController()','setProtocolFeeController(address)',
'setProtocolFee(%s,uint24)'%PK,'collectProtocolFees(address,address,uint256)','owner()','transferOwnership(address)','isOperator(address,address)','balanceOf(address,uint256)',
'allowance(address,address,uint256)','transfer(address,uint256,uint256)','transferFrom(address,address,uint256,uint256)','approve(address,uint256,uint256)','setOperator(address,bool)',
'supportsInterface(bytes4)','extsload(bytes32)','extsload(bytes32,uint256)','extsload(bytes32[])','exttload(bytes32)','exttload(bytes32[])']
ML='(int24,int24,int256,bytes32)'; SW='(bool,int256,uint160)'
sent=['beforeInitialize(address,%s,uint160)'%PK,'afterInitialize(address,%s,uint160,int24)'%PK,'beforeAddLiquidity(address,%s,%s,bytes)'%(PK,ML),
'afterAddLiquidity(address,%s,%s,int256,int256,bytes)'%(PK,ML),'beforeRemoveLiquidity(address,%s,%s,bytes)'%(PK,ML),'afterRemoveLiquidity(address,%s,%s,int256,int256,bytes)'%(PK,ML),
'beforeSwap(address,%s,%s,bytes)'%(PK,SW),'afterSwap(address,%s,%s,int256,bytes)'%(PK,SW),'beforeDonate(address,%s,uint256,uint256,bytes)'%PK,'afterDonate(address,%s,uint256,uint256,bytes)'%PK,
'transfer(address,uint256)','balanceOf(address)','unlockCallback(bytes)']
P={sel(s):s for s in pm}; assert len(P)==len(pm)
for s in sent:
    print(sel(s), s, 'COLLIDES with '+P[sel(s)] if sel(s) in P else '')
