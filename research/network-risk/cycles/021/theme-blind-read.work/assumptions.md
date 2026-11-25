# theme-blind-read: chain assumptions read from src/ alone (Steps 1 and 2)

Written before opening OPCODES.md, ASSUMPTIONS.md, findings or cleared. Sources: src/ only.

## Step 1. Assumptions the code makes about the chain

### T. Transient storage (EIP-1153)
- T1 TLOAD of an unwritten slot returns 0 at the start of every transaction. Lock.sol:25 (IS_UNLOCKED), NonzeroDeltaCount.sol:14, CurrencyDelta.sol:21,35, CurrencyReserves.sol:17,36.
- T2 TSTORE is undone when the frame that wrote it reverts (journalled like SSTORE). Lock.sol:13,19; NonzeroDeltaCount.sol:22,32; CurrencyDelta.sol:39; CurrencyReserves.sol:23,29-30.
- T3 Transient storage is discarded at the end of each transaction, whether it succeeded or reverted, and is never visible to the next transaction in the block, to another transaction executed in parallel, or across sub-transactions of a batched/system transaction type.
- T4 Transient storage is per contract address and shared by all frames of that address in one transaction (unlock frame and nested take/settle frames see the same IS_UNLOCKED and deltas). PoolManager.sol:104-114.
- T5 TSTORE in a STATICCALL context faults; TLOAD is allowed (Exttload.sol:12,32).
- Safety consequence: the only end-of-unlock check is PoolManager.sol:112 (NonzeroDeltaCount==0). take/mint/burn/settle/clear (PoolManager.sol:291-336) are gated only by IS_UNLOCKED (PoolManager.sol:96-99). If IS_UNLOCKED were 1 at the start of any frame outside an unlock, take() would transfer out with no settlement check.

### S. Storage
- S1 SSTORE/SLOAD exact 256-bit round trip, reverted with frame. Pool.sol:547-556 packs liquidityGross|liquidityNet; TickBitmap.sol:73 xor-flip; Slot0 packing Slot0.sol:41-93.
- S2 Mapping slot = keccak256(key . slot) (Solidity layout); TickBitmap.sol:67-70 computes it in assembly.

### K. KECCAK256
- K1 Correct Keccak-256 over memory ranges of 0x40 (CurrencyDelta.sol:14, TickBitmap.sol:70), 0x3a from an unaligned start (Position.sol:60), 0xa0 (PoolId.sol:14).

### A. Arithmetic opcodes (all in assembly or unchecked blocks)
- A1 MUL wraps mod 2^256: FullMath.sol:21 (prod0), SqrtPriceMath.sol:42,55 (overflow detected by DIV back, lines 43,62), TickMath.sol:82-100 (products < 2^256 by construction), TickMath.sol:142-220 (r<2^129 so r*r<2^258? r is < 2^128 after normalisation, product < 2^256).
- A2 MULMOD(a,b,not(0)) and MULMOD(a,b,d) exact 512-bit intermediate: FullMath.sol:24,48,112; SqrtPriceMath.sol:252.
- A3 DIV/MOD by zero return 0 (no trap): UnsafeMath.sol:14,26; FullMath.sol:30 relies on require(denominator>prod1) to reject d=0; FullMath.sol:62,67,73 (div by twos, and div(0-twos, twos) with twos power of two; twos=0 impossible when d>0).
- A4 SUB wraps: FullMath.sol:25,52-53,59 ((0-d)&d), 73; SqrtPriceMath.sol:217 absDiff; NonzeroDeltaCount.sol:31 (sub(count,1) wraps to 2^256-1 if count==0).
- A5 SDIV/SMOD semantics with negative operands, truncation toward zero, sign of SMOD = sign of dividend: TickBitmap.sol:24,26,57,64; Pool.sol:577-578.
- A6 SIGNEXTEND(2,x), SIGNEXTEND(15,x): TickMath.sol:61, TickBitmap.sol:20-21,38,54-55, Pool.sol:576, LiquidityMath.sol:12, BalanceDelta.sol:25-27,39-41,69, BeforeSwapDelta.sol:35, Slot0.sol:49, CustomRevert.sol:34,53-54.
- A7 SAR(255,x) all-ones mask for negatives: TickMath.sol:63, SqrtPriceMath.sol:219; SAR(128,x): BalanceDelta.sol:24,63, BeforeSwapDelta.sol:27; SAR(8,x): TickBitmap.sol:38,67.
- A8 SHL/SHR with shift >= 256 give 0; SHR(shift, value) operand order: BitMath.sol:16-22 (shr(shr(r,x), constant) uses value as shift), TickMath.sol:111,142-222, LiquidityMath.sol:13 (shr(128,z) overflow test), TickBitmap.sol:73 (shl(bit,1)).
- A9 BYTE(i,x) index from the most significant byte, i>=32 gives 0: BitMath.sol:22, BitMath.sol:45.
- A10 LT/GT/SLT/EQ/ISZERO exact: BitMath.sol:16-20, SwapMath.sol:33, SqrtPriceMath.sol:60-63,110, ProtocolFeeLibrary.sol:28-29, TickBitmap.sol:26, Pool.sol:577.
- A11 XOR/AND/OR exact: SwapMath.sol:33-35 (branch-free min/max), TickMath.sol:67,80.
- A12 ADD wraps: LiquidityMath.sol:12 (relies on add of uint128 and sign-extended int128 giving a value whose bit 128+ is set on under/overflow), SqrtPriceMath.sol:44-45 (denominator overflow detected by comparison).
- A13 DIV(not(0), price): TickMath.sol:104 (price>0).
- A14 Solidity checked arithmetic reverts on overflow (0.8.26): CurrencyDelta.sol:37 (previous + delta), ERC6909.sol:26-43, ProtocolFees.sol:55, PoolManager.sol:360.

### C. Calls, return data, value
- C1 CALL to an account with no code succeeds with empty return data. Currency.sol:68 accepts empty return as success for ERC20 transfer; Currency.sol:48 native send.
- C2 RETURNDATASIZE/RETURNDATACOPY reflect the last call; CALL writes min(returndatasize, outSize) bytes at the out pointer and leaves the rest of memory untouched. Currency.sol:68,73 (mload(0) after call with out 0..32); Hooks.sol:134-148; CustomRevert.sol:91-117 (bubbling).
- C3 Arguments of and(...) evaluated right to left so CALL runs before RETURNDATASIZE (Currency.sol:64-74). This is a compiler property.
- C4 call(gas(), ...) forwards all but 1/64 (EIP-150): Currency.sol:48,73, Hooks.sol:134. A call that runs out of gas returns 0 and is turned into a revert, never a silent success.
- C5 CALLVALUE equals the value actually debited from the caller and credited to PoolManager. PoolManager.sol:354 credits msg.value as native payment with no balance check.
- C6 SELFBALANCE/BALANCE of PoolManager only rises by real deposits; the ERC20 path uses token balanceOf (Currency.sol:90-95, PoolManager.sol:285,358-360). PoolManager has no receive/fallback, so native arrives only via settle/settleFor, SELFDESTRUCT beneficiaries, block rewards or chain-specific mints.
- C7 Native currency is address(0) (Currency.sol:38,106). A token whose ERC20 balance is the native balance (dual representation) breaks the separation of native and ERC20 accounting.
- C8 Custom errors bubbled via REVERT with arbitrary data (CustomRevert.sol:15-117).
- C9 msg.sender is the immediate caller: delta accounting per caller (PoolManager.sol:294,326,334,364,183,226), hook self-call skip (Hooks.sol:171-175,217,253,293), updateDynamicLPFee auth (PoolManager.sol:340), owner/feeController auth (ProtocolFees.sol:36,48).

### D. Addresses and code
- D1 ADDRESS is fixed; NoDelegateCall compares to an immutable written at deploy (NoDelegateCall.sol:19,25).
- D2 Hook permissions are the low 14 bits of the hook address (Hooks.sol:27-47,337-339). CREATE2 addresses are keccak-derived (EIP-1014) so mining flags costs ~2^14 tries; nothing in src checks code at the hook address.
- D3 Currencies ordered by uint160 value (PoolManager.sol:121).
- D4 No EXTCODESIZE/EXTCODEHASH checks in src; Solidity's high-level balanceOf call (Currency.sol:94) reverts on empty return data via ABI decoding.
- D5 Contract size 24,009 bytes must deploy (EIP-170).

### B. Block and transaction context
- B1 chainid, timestamp, number, coinbase, basefee, gasprice, prevrandao, blobhash are not read anywhere in src (grep). Only gas() is used.

### M. Memory
- M1 Memory at and above the free pointer is zero when Solidity allocates; Position.sol:55-65 and Currency.sol:57-79 write past fmp and clean it; CustomRevert.sol:51-55,62-66,73-77,94-117 write past fmp then revert.
- M2 MSTORE at unaligned offsets (Position.sol:56-59) overwrites exactly 32 bytes.

## Step 2. Which network is most likely to break each assumption, and how it would be used

Ranked by plausibility times damage.

1. T3 transient storage leaks past the end of a transaction (reverted transaction, out-of-gas top-level frame, parallel or speculative execution, mini-blocks, multi-call transaction types). Damage: if IS_UNLOCKED=1 leaks, any later caller runs take() outside unlock and drains every currency (PoolManager.sol:96-99,291-297,112). Most likely: Monad (own C++ execution with optimistic parallel re-execution), MegaETH (custom revm with mini-blocks and its own state handling), HyperEVM (custom revm node, small and big blocks), Tempo (reth fork with batched multi-call transactions and fee AMM system calls), Arbitrum One/Robinhood/Elysium (ArbOS runs retryable submit and redeem as separate transactions inside geth; Stylus), Avalanche (coreth/libevm atomic txs).
2. T2 TSTORE not undone on frame revert. Damage: attacker settles inside a sub-call that later reverts; the token transfer is undone but the credit (CurrencyDelta.sol:39) and NonzeroDeltaCount changes remain, then take() pays the credit out of other users' funds. Same networks as 1, plus any revm/evmone build with a journal bug.
3. C5 CALLVALUE nonzero without a real debit. Damage: settle{value} credits native for free (PoolManager.sol:354), then swap the credit into the other side of a native pool, or take native. Most likely: Tempo (no native token; value transfers and BALANCE behave differently), Arc (native USDC, 18 decimals native vs 6 decimals ERC20 interface), Celo, HyperEVM.
4. T4 transient storage not shared between frames of one address (e.g. a per-frame implementation). Effect would be freeze (unlock never sees deltas) rather than loss. Monad, MegaETH.
5. C7 dual native/ERC20 representation (token class; recorded in one line, not swept): Celo CELO, Polygon 0x...1010, Arc USDC, X Layer, HyperEVM.
6. A2 MULMOD/A1 MUL edge results from a non-reference 256-bit library (ruint, intx, evmone, Go uint256, monad's own). Damage: FullMath.mulDiv wrong at prod1 != 0 gives wrong swap outputs (SwapMath.sol:65,74,104) or fee claims (Position.sol:94-96) to the attacker's favour. Monad (intx/own), MegaETH/HyperEVM/Tempo/Arc (ruint via revm), Avalanche/BNB/Polygon/Celo (holiman/uint256).
7. A5/A6/A7 signed opcode edges (SDIV of -2^255 by -1, SMOD by negative, SIGNEXTEND with byte index >= 31, SAR by >=256). Used in TickBitmap.compress and tickSpacingToMaxLiquidityPerTick; a wrong result picks a wrong next tick and lets a swap skip liquidityNet changes (Pool.sol:347-428), corrupting pool liquidity. Same networks as 6.
8. A3 DIV/MOD by zero returning 0. UnsafeMath.sol:14,26 rely on it only where the divisor is proven nonzero; FullMath.sol:30 relies on it for d=0. A trap would only revert. Low damage.
9. C2 CALL output semantics: if a client zero-fills the out buffer beyond returndatasize, or writes nothing when returndatasize < outSize, Currency.sol:68 (eq(mload(0),1) with gt(returndatasize,31)) stays safe; a client that reports RETURNDATASIZE from a previous call would break Hooks.sol:140-148 parsing. Monad, MegaETH.
10. K1 keccak over unaligned or 58-byte ranges (Position.sol:60); a cached or JIT keccak with a wrong length would merge positions of different owners (siphon of fees and principal). Monad (JIT/native compilation), MegaETH (JIT/AOT compiler), HyperEVM.
11. JUMPDEST analysis or code cache keyed by code hash only, or a bytecode rewriting cache (Monad compiler, MegaETH/revmc AOT). A miscompiled JUMPI on one of the security checks in PoolManager.sol:96-99,112,356 or SafeCast reverts. Monad, MegaETH, Arbitrum (Stylus only for WASM).
12. C4 63/64 and gas schedule differences (MegaETH multi-dimensional gas, HyperEVM 2M/30M blocks, Monad charges full gas limit): affects only the caller's own transaction because modifyLiquidity and take are O(1); a swap loops per tick (Pool.sol:344-437) but withdrawals do not depend on swaps. Freeze risk low.
13. C9/D1 msg.sender/ADDRESS changes by native account abstraction (Tempo AA transactions, EIP-7702): msg.sender keyed deltas stay consistent within one frame. Low.
14. C1 empty-code success for ERC20 transfer: only hits pools whose currency has no code (pool-creator/token class).
15. B1 none used, so block time, number and fee-market differences cannot change results.

## Step 3. The top fifteen against what the review tested (read after Steps 1 and 2)

| # | Item | Tested by the review | Does the evidence exercise this scenario |
|---|---|---|---|
| 1 | T3 transient storage leaking into the next transaction | Source readings (Arbitrum StateDB.Prepare with an eth_simulateV1 TSTORE/TLOAD pair, Avalanche libevm Prepare, Monad and MegaETH per-transaction clearing, Tempo nested execution callers); synced currency census on MegaETH, Monad, Unichain, BNB | Partly. Only Arbitrum had a two-transaction simulation, with a generic contract. Step 4 probe A now runs it at the real PoolManager on 16 networks after success, INVALID, REVERT and completed-unlock-then-INVALID transactions. Avalanche, Monad, MegaETH, Arc and HyperEVM endpoints have no eth_simulateV1 (lead). |
| 2 | T2 TSTORE undone on frame revert | callsem.py (generic helper, 21 networks), mined rollback census and 31 reruns, Monad state3 reading, MegaETH validator re-execution | Yes for REVERT and INVALID in generic frames and mined PoolManager frames. Probe C adds the real PoolManager on 21 networks. |
| 3 | C5 CALLVALUE without a real debit | callsem.py value tests (internal calls), Arc frame hook F-125, BNB system-address call F-058 | Internal calls yes. Probe B adds top-level value from a zero balance sender on 21 networks. |
| 4 | T4 transient shared across frames | Every completed unlock in pmdiff3 and mined transactions | Yes, directly. |
| 5 | C7 dual native/ERC20 faces | F-008, F-050, F-023, F-032, F-043, F-075 and cleared A3 walks | Yes (token class, not swept here). |
| 6 | A1/A2 MUL/MULMOD | battery, targeted (8,908 mulmod), ruint release harness, pmdiff5 512-bit branch | Yes. |
| 7 | A5-A7 signed opcodes | battery edges, bytecode map of 66 signed/div instructions, full tick range | Yes. |
| 8 | A3 div by zero | battery and divRoundingUp sequence | Yes. |
| 9 | C2 CALL output buffer and returndata | pmdiff2 nine transfer shapes (31 bytes, 1 byte, 64 bytes), callsem return data tests | Yes. |
| 10 | K1 keccak lengths and offsets | battery 120 offset/length pairs up to 1,023 bytes, every script that creates positions | Yes. |
| 11 | JUMPDEST analysis and compiled code | 29 JUMPDEST bytes in push data, Tempo SIMD kernels transcribed, Monad x86 emitter built and run, BNB fused opcodes history | Yes, with the open items listed in OPCODES.md (MegaETH closed JIT, HyperEVM validator). |
| 12 | C4 gas and 63/64 | pmdiff gas differences, exits under mined cap (cycle 20) | Yes. |
| 13 | C9/D1 sender spoofing | cycle 20 senders without signature, F-138, F-140, F-020 | Yes (privileged actors only). |
| 14 | C1 empty-code success | pmdiff2 native payouts to accounts without code, callsem | Yes (pool-creator class for tokens). |
| 15 | T5 TSTORE in a static context | callsem static write test, which writes TSTORE and SSTORE together | No: the SSTORE would fail the frame by itself. Probe C isolates it with PoolManager.sync, which writes only transient storage. |
