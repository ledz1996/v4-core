"""Attach to each JUMPI that is still one-sided after set 6 what it decides and why the other side is not reached."""
import json
R = {}
for pc in (1378, 2396, 3087, 5298, 10926, 11947):
    R[pc] = ('revert', 'ABI decoder bound for a second static struct of the same function; an earlier JUMPI of the same function already reverts when calldata is shorter than the whole head (e.g. pc 1327 before 1378), so this side is unreachable')
for pc in (5583, 11761, 11789, 11817, 11882, 19089):
    R[pc] = ('revert', 'Panic 0x41 when a memory struct allocation moves the free memory pointer above 2^64 or backwards; the pointer is a small constant offset here, so unreachable')
R[9048] = ('revert', 'second test of the success flag of the unlockCallback CALL (PoolManager.sol:110); the failure side already left at pc 9042, so the condition is always true')
R[15094] = ('revert', 'second test of the success flag of the balanceOf STATICCALL (Currency.sol:94); the failure side already left at pc 15088 (now covered), so always true')
R[15021] = ('credit (dead)', 'native branch of Currency.balanceOfSelf (SELFBALANCE, Currency.sol:91-92); both callers, sync (PoolManager.sol:281-285) and _settle (PoolManager.sol:353-359), only call it for a nonzero currency')
R[16370] = ('revert', 'bytes4(data) for hook calldata shorter than 4 bytes in the HookCallFailed wrapper (Hooks.sol:137); hook calldata is always an abi.encodeCall of at least 4 bytes')
R[12293] = ('revert', 'Panic 0x11 of a checked uint256 addition (ERC6909 balances, ERC6909.sol:147,162,199); balances move by amounts below 2^127 per call, so overflow needs about 2^129 calls')
R[19792] = ('revert', 'Panic 0x11 of the checked int256 subtraction amountCalculated -= (amountIn + fee) (Pool.sol:375); both terms are below 2^200, unreachable')
for pc in (17660, 17698, 19752, 19780, 20339, 20353):
    R[pc] = ('revert', 'SafeCast.toInt256 of an amount at or above 2^255 (SafeCast.sol:50, called from Pool.sol:373-381 and SqrtPriceMath.sol:268-286); amounts from getAmount0Delta and getAmount1Delta are below 2^225, unreachable')
R[16750] = ('revert', 'InvalidTick in getSqrtPriceAtTick (TickMath.sol:70); every caller passes a tick already bounded by checkTicks (Pool.sol:94-98) or by the clamp at Pool.sol:351-356, unreachable')
R[18728] = ('revert', 'Panic 0x12 for mulmod by liquidity 0 in getNextSqrtPriceFromAmount1RoundingDown; computeSwapStep only calls it when the step does not reach its target, which needs nonzero liquidity')
R[23677] = R[18728]
for pc in (20420, 20741):
    R[pc] = ('revert', 'InvalidPriceOrLiquidity (SqrtPriceMath.sol:135-143,164-172); with liquidity 0 the amount to the target is 0, so the step always reaches its target and never calls these functions')
R[20840] = ('payout price', 'NotEnoughLiquidity (SqrtPriceMath.sol:109-114); the output is less than the output to the target, so the quotient is below the price difference, unreachable')
R[20776] = ('payout price', 'amount > type(uint160).max in the subtract branch of getNextSqrtPriceFromAmount1RoundingDown (SqrtPriceMath.sol:102-106): an exact-output step of more than 2^160 currency1 that stops short of its target. The output to the target is bounded by what the positions in that range deposited, each deposit is capped below 2^127 by toInt128 (Pool.sol:212-235), so it needs about 2^33 positions; not reached by any script')
for pc in (20942, 20963, 20971):
    R[pc] = ('payout price', 'inside the branch of pc 20776 (mulDivRoundingUp(amount, Q96, liquidity)); never reached for the same reason')
for pc in (21212, 22353, 22468, 22618, 22741, 22912):
    R[pc] = ('revert', 'require(denominator > prod1) of a constant-denominator copy of FullMath.mulDiv (FullMath.sol:139); the operands of these copies are bounded so that the quotient fits, unreachable; 21212 is require(x > 0) of leastSignificantBit after masked != 0 (TickBitmap.sol:114-117)')
R[21212] = ('revert', 'require(x > 0) of BitMath.leastSignificantBit (BitMath.sol:154) after masked != 0 was tested (TickBitmap.sol:114-117), unreachable')
R[23521] = ('revert', 'require(x > 0) of BitMath.mostSignificantBit (BitMath.sol:135) on price << 32 with price >= MIN_SQRT_PRICE (TickMath.sol:127-134), unreachable')
R[23695] = ('revert', 'require(++result > 0) of mulDivRoundingUp (FullMath.sol:221-223); the result would have to be 2^256 - 1, unreachable for the bounded operands')
R[22746] = ('payout price', 'prod1 == 0 in the copy of mulDiv(amount, Q96, liquidity) used only for amount > 2^160 (SqrtPriceMath.sol:97); amount * 2^96 >= 2^256 there, so prod1 is never 0 by construction')
for pc in (23217, 23399):
    R[pc] = ('payout', 'swap of the two prices in getAmount0Delta (SqrtPriceMath.sol:194); every caller passes them in order (SwapMath.sol:293-327, Pool.sol:212-235), so the swap is never needed')
for pc in (23248, 23430):
    R[pc] = ('revert', 'InvalidPrice for a zero lower price (SqrtPriceMath.sol:197-202); prices are at least MIN_SQRT_PRICE, unreachable')
R[23705] = ('payout price', 'amount == 0 in the copy of getNextSqrtPriceFromAmount0RoundingUp used by getNextSqrtPriceFromOutput; exact-output steps that stop short pass amountRemaining > 0, unreachable (the copy used by getNextSqrtPriceFromInput, pc 23823, is covered both ways)')
R[23781] = ('revert', 'PriceOverflow in the subtract branch (SqrtPriceMath.sol:59-69); the output is less than the output to the target, so numerator1 > amount * price, unreachable')
R[23994] = ('revert', 'toUint160 of the subtract branch result (SqrtPriceMath.sol:71); the result is at most the target price, unreachable')
a = json.load(open('jumpmap-after.json'))
for x in a['oneSided'] + a['neverReached']:
    d, why = R.get(x['pc'], ('?', '?')); x['decides'] = d; x['why'] = why
miss = [x['pc'] for x in a['oneSided'] + a['neverReached'] if x['why'] == '?']
json.dump(a, open('jumpmap-after.json', 'w'), indent=1); print('unexplained', miss)
