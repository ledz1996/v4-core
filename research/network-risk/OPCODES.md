# Opcode behaviour on the 21 networks and what it means for the pool math

State on 2026-11-24. This part of the review asks one question: does any of the 21 networks compute an opcode, or run control flow, differently from Ethereum in a way that changes the arithmetic or the logic of this repository's PoolManager?

## Answer

No difference was found. Four independent checks on the networks agree, and each covers a weakness of the others. A fifth part, added after a compiler became available, works on the bytecode built from this checkout.

1. A battery of 185,529 opcode test vectors gave the specified result on every one of the 21 networks, with no mismatch.
2. The deployed PoolManager bytecode, placed at the same address with the same empty state on every network, answered 550 scripts of about 28,000 calls with the same bytes as on Ethereum. The scripts cover the pool math, hook callbacks, token transfers with unusual return data and revert handling. The only differences, on Polygon, Monad, Tempo, Elysium and HyperEVM, are swaps that ran out of gas.
3. 99,903 swaps that the networks have already mined satisfy the exact relations the source's math fixes. All 99,903 pass the tick relation. Of the 88,576 that could be paired with the swap before them, 85,278 match the single-step formulas to the unit, and 228 of the 229 sampled multi-step swaps replay to the unit.
4. A reading of the node source for the networks whose interpreter is not go-ethereum or stock revm found no opcode that departs from the specification.

One thing came out of the reading that deserves a place in the deployment checklist. The big integer library behind reth based nodes shipped a release on 20 October 2026 that returned wrong `MULMOD` results in one edge case. It was withdrawn three days later. No network on the list runs it or ran it, and the vectors built to hit it pass everywhere. Ethereum's reth nodes and Tempo run the first fixed release, whose arithmetic paths are one month old, and Tempo has no second client to disagree with it.

5. This checkout builds to a PoolManager of 24,009 bytes whose creation code hash equals the one recorded in `snapshots/PoolManagerTest.json`. Run in a reference interpreter written for this review, the bytecode gives the same answer as every one of the 21 networks on 1,287 scripts that execute 95.6 percent of its instructions, apart from scripts a node could not afford. Its step trace equals Tempo's at each of 2.9 million steps, and its swap and liquidity amounts equal the source's formulas on 4,000 random pools.

## What the source asks of the EVM

The assembly blocks in `src/` use 37 opcodes. The table lists the ones whose edge behaviour the math or the logic depends on, with the place that depends on it.

| Opcode | Where the source relies on it | Edge that must hold |
|---|---|---|
| `MULMOD` | `FullMath.mulDiv` and `mulDivRoundingUp` (`src/libraries/FullMath.sol`), `SqrtPriceMath.getAmount1Delta` | Exact remainder of a 512 bit product. The modulus `2^256 - 1` is used on every call to rebuild the high half of the product. |
| `SAR` | `TickMath.getSqrtPriceAtTick` and `SqrtPriceMath.absDiff` (shift by 255 to make a sign mask), `getTickAtSqrtPrice` (shift by 128 of a signed value), `TickBitmap.position`, `BalanceDelta`, `StateLibrary` | Sign fill for negative values. |
| `SIGNEXTEND` | Tick and tick spacing inputs (`TickMath`, `TickBitmap`, `Pool`), `Slot0.tick`, `BalanceDelta.amount1`, `LiquidityMath.addDelta` | Extension from byte 2 and byte 15. |
| `SDIV`, `SMOD`, `SLT` | `TickBitmap.compress` and `flipTick`, `Pool.tickSpacingToMaxLiquidityPerTick` | Truncation toward zero and a remainder with the sign of the dividend. Negative ticks round the wrong way otherwise. |
| `BYTE`, `SHL`, `SHR`, `DIV` | `BitMath.mostSignificantBit` and `leastSignificantBit` (table lookups), all of `TickMath` | Zero for a byte index above 31 and for a shift of 256 or more. |
| `DIV`, `MOD`, `GT` | `UnsafeMath.divRoundingUp`, `TickMath` (`div(not(0), price)`) | Division by a full width divisor. |
| `MUL`, `ADD`, `SUB` | Everywhere, mostly inside `unchecked` | Wrap at 2^256. `FullMath` and `BitMath` depend on the wrap. |
| `KECCAK256` | Pool id, position key, mapping slots, transient delta slots | Standard hash. |
| `TLOAD`, `TSTORE` | Lock, delta count, deltas, synced currency | Covered in `REPORT.md`. |
| `JUMPI` | Every branch. `TickBitmap.flipTick` branches on a signed remainder | Any nonzero bit in the condition word takes the branch. |

`python3 tools/opdiff/v4math.py` runs a transcription of the math libraries, written operation by operation from the text in `src/`, against plain integer arithmetic. `mulDiv` and `mulDivRoundingUp` agree with floor and ceiling division on 200,000 random inputs, the bit scans agree on 100,000, and over the whole tick range the price is strictly increasing and `getTickAtSqrtPrice` returns the tick it was given, and the tick below for a price one unit lower. The source's math is therefore right under the specification, which leaves the question of whether each network follows the specification.

## Check 1: opcode battery

`tools/opdiff/battery.py` and `tools/opdiff/targeted.py`. A dispatcher of 1,287 bytes is placed at an unused address by state override. Its calldata is a list of records, each naming an opcode and up to three operands, and it returns one word per record. The words are compared with the reference semantics in `tools/opdiff/evm.py`. Nothing is deployed and no transaction is sent.

The general battery has 99,985 vectors: 25 arithmetic, bitwise and comparison opcodes on edge values (limb boundaries, the sign bit, the tick and price limits of the source, the constants of `TickMath` and `BitMath`) and on random values, plus `JUMPI` with 209 condition words, `KECCAK256` over 120 offset and length pairs up to 1,023 bytes, `MCOPY` with overlapping ranges, `CALLDATALOAD` past the end of calldata, and three short sequences copied from the source (`divRoundingUp`, the `signextend` and `sar` unpacking of `BalanceDelta` and `Slot0`, and the 512 bit product of `FullMath`).

The targeted set has 85,544 vectors aimed at places where big integer libraries have gone wrong: 8,908 `MULMOD` and `mulDiv` inputs that meet the exact condition of the library bug described below, products that are exact multiples of `2^256 - 1` or one off, `ADDMOD` around overflow, division by powers of two and by full width divisors, and shifts at every limb boundary with both sign patterns.

Result: 21 of 21 networks returned the expected word for all 185,529 vectors. Results are in `opcodes/battery.json` and `opcodes/targeted.json`.

## Check 2: one bytecode, one state, 21 interpreters

`tools/opdiff/pmdiff.py`. The runtime bytecode of the PoolManager deployed on Ethereum (24,009 bytes) is placed at one fixed fresh address on every network by state override, with its single immutable rewritten to that address. A 189 byte driver calls `unlock` and, inside the callback, runs a script of calls: `initialize`, `modifyLiquidity`, `swap`, `donate`, `mint`, `burn`, `clear`, `take`, `settle`, and `extsload` and `exttload` reads of the pool state and the caller's deltas after each step. It records the success flag and the return data of every call and reverts with the record, so nothing settles and nothing persists.

The 250 scripts cover 9 fees, 8 tick spacings, starting prices over the whole range, up to five positions per pool, swaps in both directions with exact input and exact output, amounts from 1 to 2^126 and the extreme values of `int256`, open and tight price limits, removals, donations and claims. At 25 million gas, 243 scripts return a full record on Ethereum: 11,892 calls, of which 11,225 succeed and 667 revert, so error paths are compared as well. The other seven run out of gas as a whole and return nothing, there and on every other network, so they compare nothing.

The same script must give the same bytes everywhere, because code, state and input are the same.

| Result | Networks |
|---|---|
| All 250 scripts of the first set identical to Ethereum | OP Mainnet, Base, Unichain, Zora, World Chain, Ink, Soneium, Celo, X Layer, Arbitrum One, Robinhood Chain, Elysium, BNB Smart Chain, Avalanche, MegaETH, Arc, HyperEVM |
| Identical except where a call ran out of gas | Polygon (231 at 25 million gas), Monad (229), Tempo (240) |

The exceptions are a gas matter. Read with the `GAS` opcode, the Ethereum, Polygon and Tempo endpoints give a simulated call at most 50 million gas and Monad gives 150 million. The scripts that differ contain a swap at tick spacing 1 across most of the price range, which needs 36 to 50 million gas on Ethereum and more on the three networks, where storage reads or new storage slots cost more. Run again with the largest gas each endpoint grants, all but six script and network pairs become identical. In those six the first differing call is the heavy swap, which fails with empty return data on the side that has less gas (Polygon twice, Tempo once, and Ethereum three times against Monad), and every call before it is identical. Details are in `opcodes/pmdiff-gas.json`. That swaps across many ticks cost more gas on some networks is already recorded in `REPORT.md` as a delay without loss.

`tools/opdiff/pmdiff2.py` repeats the method for the call paths, which the first set leaves out because its pools have no hook and its currencies have no code. A hook double and a token double are placed by state override. The hook answers every callback with a selector word and two configured words cut to a configured length, optionally with a flipped selector or as a revert. The token reports a configured balance and answers `transfer` in one of nine shapes: true, nothing, false, 31 bytes, a revert with data, 64 bytes, the number 2, an empty revert, and one byte. This runs the assembly of `Hooks.callHook`, `Currency.transfer` and `CustomRevert.bubbleUpAndRevertWith`, the parsing of hook return deltas and fee overrides, `sync` and `settle` against a moving balance, and native payouts to an account without code and to two precompiles.

The 300 scripts make 16,263 calls. On Ethereum 14,622 succeed and 1,264 fail, with eleven different revert selectors and some empty reverts among the failures, so the wrapped error paths are compared too. Sixteen networks return the same bytes as Ethereum for all 300 scripts. Polygon and Monad differ on 20 scripts each at 25 million gas, Tempo on 6, Elysium and HyperEVM on 1. In every one the first differing call is a swap with an open price limit that runs past the pool's liquidity and walks the rest of the tick range word by word, which is where the gas goes. With the largest gas each endpoint grants, 39 of the 48 become identical and 9 still end at such a swap on the side with less gas (`opcodes/pmdiff2-gas.json`).

Taken together the two sets make 11,000 comparisons of a script on a network against the same script on Ethereum. 10,985 are identical, and the 15 that are not stop at a swap that one side could not afford.

## Check 3: swaps the networks have already mined

`tools/opdiff/swaps.py` and `tools/opdiff/replay.py`. A simulated call can run on a different code path than block production. On Monad the RPC always uses the interpreter, while blocks run frequently used contracts as compiled native code. This check therefore reads results that blocks already contain: the `Swap` events of the deployed PoolManager, most recent first, until about 6,000 logs per network or the endpoint's limit.

Two relations are tested. The tick in the event must equal `getTickAtSqrtPrice` of the price in the event, or sit one below it with the price exactly on the tick boundary, which is what `Pool.swap` leaves after a swap that stops on a tick going down (`src/libraries/Pool.sol:430-431`). And for two consecutive swaps of one pool with no liquidity change between them, the amounts and the end price must follow from the start price, the liquidity and the fee by one of the three single-step outcomes of `SwapMath.computeSwapStep`.

| Network | Swaps read | Tick relation holds | Paired with the swap before | Single step, exact to the unit | Several steps | Crossed liquidity |
|---|---|---|---|---|---|---|
| Ethereum | 38,629 | 38,629 | 35,310 | 32,996 | 2,302 | 12 |
| OP Mainnet | 4,045 | 4,045 | 2,539 | 2,536 | 3 | 0 |
| Base | 3,590 | 3,590 | 2,597 | 2,342 | 215 | 40 |
| Unichain | 6,019 | 6,019 | 5,661 | 5,605 | 56 | 0 |
| Zora | 454 | 454 | 323 | 306 | 9 | 8 |
| World Chain | 221 | 221 | 160 | 159 | 1 | 0 |
| Ink | 4,008 | 4,008 | 3,614 | 3,590 | 24 | 0 |
| Soneium | 840 | 840 | 763 | 761 | 2 | 0 |
| Celo | 79 | 79 | 65 | 60 | 5 | 0 |
| X Layer | 365 | 365 | 324 | 324 | 0 | 0 |
| Arbitrum One | 6,527 | 6,527 | 5,779 | 5,770 | 9 | 0 |
| Robinhood Chain | 5,821 | 5,821 | 4,977 | 4,712 | 264 | 1 |
| Elysium | 4,679 | 4,679 | 4,388 | 4,386 | 2 | 0 |
| Polygon | 937 | 937 | 801 | 799 | 2 | 0 |
| BNB Smart Chain | 8,326 | 8,326 | 7,326 | 7,141 | 185 | 0 |
| Avalanche | 59 | 59 | 29 | 28 | 1 | 0 |
| Monad | 2,176 | 2,176 | 2,085 | 2,072 | 13 | 0 |
| MegaETH | 5,839 | 5,839 | 5,524 | 5,384 | 106 | 34 |
| Tempo | 950 | 950 | 212 | 212 | 0 | 0 |
| Arc | 6,325 | 6,325 | 6,094 | 6,090 | 4 | 0 |
| HyperEVM | 14 | 14 | 5 | 5 | 0 | 0 |
| Total | 99,903 | 99,903 | 88,576 | 85,278 | 3,203 | 95 |

The tick relation exercises the whole of `getTickAtSqrtPrice`: the bit scan, fourteen rounds of squaring, a signed multiplication, two arithmetic shifts and `getSqrtPriceAtTick`. The single-step relation exercises `mulDiv`, `mulDivRoundingUp`, `divRoundingUp` and the price and amount functions of `SqrtPriceMath`.

The last two columns are swaps that took more than one step. A swap rounds once per step, so its amounts land a few units from the single-step values ("several steps"), or far from them when it crossed a position whose liquidity entered and left again ("crossed liquidity"). `replay.py` reruns `Pool.swap` step by step for the newest 25 and 60 of each kind per network, reading the tick bitmap and the net liquidity of every crossed tick from the PoolManager's storage at the block of the swap. Of 229 swaps sampled on Ethereum, Base, Unichain, Zora, Robinhood Chain and MegaETH, 228 reproduce price, tick, liquidity and both amounts to the unit, the longest with 201 steps. The one that does not is on Robinhood Chain, where the endpoint no longer serves the state of that block. Results are in `opcodes/swaps.json` and `opcodes/replay.json`.

Avalanche has only 59 recent swaps, so this check says little about it. HyperEVM, with 14 in the first window, is covered by the longer window described below.

## Check 4: the node source

Three readers went through the interpreters that are not go-ethereum or stock revm, and a fourth traced the big integer library through every reth based client. Each ran its own smaller test set against the live endpoints as well, about 25,000 cases on Monad, 20,000 each on BNB Smart Chain, Polygon and Avalanche, and 4,270 each on Tempo, MegaETH, HyperEVM and Arc, all without a mismatch.

| Network | What runs | What the reading found |
|---|---|---|
| Monad | Own client, v0.16.5, with an interpreter and a compiler that emits x86 code | One 256 bit library serves the interpreter and the compiler's constant folding. Its division, `MULMOD`, signed operations, shifts, `SIGNEXTEND` and `BYTE` match the specification as read, and so do the compiler's special cases for literal operands. Simulated calls always use the interpreter (`rpc/monad_executor.cpp:1296-1300`), so the compiled path was checked by reading and by the mined swaps above. The vector register paths for shifts and the emitted `JUMPI` were not read. |
| BNB Smart Chain | Fork of go-ethereum, v1.8.2 | The interpreter differs from go-ethereum v1.17.3 in three places, none of them arithmetic or jumps. The client carried a feature from v1.6.2 to v1.7.8 that rewrote bytecode into fused instructions. It was off by default and had real faults: a fused comparison that always returned 0 (fixed in v1.7.3), lost write protection inside a static call, which produced a bad block (v1.7.1), and loose stack bounds (v1.7.1). v1.8.0 removed the feature. The PoolManager bytecode would have hit 20 of the 31 fused patterns and does not contain the one behind the comparison fault. |
| Polygon | bor v2.11.1, go-ethereum v1.16.8 with additions | An optional fast dispatch loop, off by default, makes the same library calls as upstream. A cache for 64 byte hash inputs is keyed by the full input. Storage reads and writes are repriced, which changes gas only. |
| Avalanche | avalanchego 1.15.3 | The interpreter files equal go-ethereum's. The C-Chain clears bit 248 of every storage slot index, confirmed on the live node and already recorded as F-040. Transient slots are not folded. |
| Tempo | evm2, a new interpreter, with ruint 1.21.1 | Arithmetic goes through ruint. Signed division and remainder are hand written and correct as read, shift and byte indices are clamped on the whole word, and `JUMPI` tests the whole word. The release build has no compiler stage. The scan for jump destinations uses vector instructions chosen by the CPU at run time, so validators on different hardware run different code for it. Only the endpoint's CPU was tested, with 3,026 jumps into and around push data. |
| MegaETH | mega-evm on revm 40.0.3, ruint 1.19.0 | Every arithmetic and jump instruction is the stock one inside a wrapper that adds gas accounting. The node itself is not public. |
| HyperEVM | Validator closed source | The public replay clients pin stock revm. Nothing about the validator can be read. |
| Arc | reth based, revm 38.0.0, ruint 1.20.0 | The only replaced instruction is `SELFDESTRUCT`. |

### The library fault of October 2026

ruint is the 256 bit integer library under revm and evm2. Release 1.21.0 of 20 October 2026 rewrote `mul_mod`, `add_mod`, division, multiplication and the shifts for speed, and added a fast path for the modulus `2^256 - 1`, which is the modulus `FullMath.mulDiv` uses. The rewritten `mul_mod` skipped the top digit of the quotient when the top two limbs of the normalised product were less than or equal to those of the modulus. With equal limbs the skipped digit can be 1 and the remainder comes out wrong. Release 1.21.1 of 23 October changed the test to strictly less, and 1.21.0 was withdrawn.

| Network | Client | ruint | Has the fault | Runs the rewritten paths |
|---|---|---|---|---|
| Ethereum (reth nodes) | reth v2.11.0 on evm2 | 1.21.1 | no | yes |
| Tempo | v1.19.0 on evm2 | 1.21.1 | no | yes |
| OP Mainnet, Unichain, Ink, Soneium | op-reth v2.8.1 and v2.9.0-rc.1 | 1.20.0 | no | no |
| Zora, World Chain, Celo, Arc | conduit-op-reth v2.5.1, world-chain v2.8.2, celo reth, arc-node | 1.20.0 | no | no |
| Base | base v1.5.6 | 1.19.0 | no | no |
| MegaETH | mega-evm (node closed) | 1.19.0 | no | no |
| X Layer | xlayer v0.0.7 | 1.18.0 | no | no |

No release of these clients published between 20 October and today pinned 1.21.0. Tempo went from 1.20.1 in v1.17.0 straight to 1.21.1 in v1.18.2. The reader built a harness that links 1.19.0, 1.21.0 and 1.21.1 and compared them with Python integers on 1.2 million inputs per operation: 1.21.1 had no failure, and 1.21.0 gave about 4,300 wrong `mul_mod` results per 300,000 on inputs of the right shape, which shows the tests can see the fault.

For the pool math the fault would have been hard to reach even on an affected node. `mulDiv` calls `mulmod(a, b, denominator)` only when the product needs more than 256 bits, and the fault then needs a denominator of four limbs whose top 128 bits equal those of the high half of the product, which means a quotient within 2^129 of 2^256. The prices, amounts and fee growth values that `mulDiv` returns in a pool are far below that. It still matters for deployment, for two reasons. A node operator who built from source in those three days may be running the withdrawn release without knowing. And the fixed release is new code on a path every swap takes, on one network with a single client.

## The build and the bytecode level

`tools/build/compile.js`, `tools/opdiff/pyevm.py`, `bytecode.py`, `trace.py` and `buildcheck.py`.

The build. `src/PoolManager.sol` was compiled with solc 0.8.26 (commit 8a97fa7a, the JavaScript build of the compiler) and the settings of `foundry.toml`: optimizer with 44,444,444 runs, via IR, Cancun, no metadata hash. The runtime bytecode has 24,009 bytes and the creation code 24,194. `snapshots/PoolManagerTest.json` records a bytecode size of 24,009 and a creation code hash, and the keccak of the built creation code equals that hash. The source in this checkout therefore builds to exactly the bytecode its own snapshot describes. The build is stored in `build/PoolManager.json`.

One by-product has to be stated. The scripts print a hash of the bytecode they run. With its one immutable rewritten to the test address, the build has the same hash as the PoolManager bytecode fetched from Ethereum with its immutable rewritten the same way. No source was compared, but the two bytecodes are the same bytes, so every result in checks 2 and 3 holds for this build as it stands.

What is in the bytecode. A linear disassembly gives 10,418 instructions and 112 distinct opcodes. No instruction reads the chain: there is no `TIMESTAMP`, `NUMBER`, `CHAINID`, `BASEFEE`, `GASPRICE`, `ORIGIN`, `BLOCKHASH`, `BALANCE`, `EXTCODESIZE` or `EXTCODEHASH`. What depends on the surroundings is `CALLER` (53 places), `CALLVALUE` (33), `ADDRESS` (2), `SELFBALANCE` (1), `GAS` (5, each feeding a call), four `CALL` and one `STATICCALL`. Storage and hashing are 79 `SLOAD`, 40 `SSTORE`, 20 `TLOAD`, 9 `TSTORE` and 70 `KECCAK256`. The arithmetic the table above singles out appears as 114 `SIGNEXTEND`, 67 `SLT`, 19 `SAR`, 13 `MULMOD`, 13 `SGT`, 4 `SDIV`, 3 `SMOD` and 3 `BYTE`. There are 610 jump destinations and 709 jumps with a constant target, all of which land on a valid destination. Twenty-nine bytes with the value of `JUMPDEST` sit inside push data, and push data crosses a 16, 32 or 64 byte border 609, 430 and 224 times, which is where a vectorised scan for jump destinations would go wrong if it did.

A reference interpreter. `pyevm.py` is an EVM in Python written from the specification for this review, without gas and with no client code. It runs the 550 scripts of check 2 instruction by instruction, 525 million instructions in all. For 512 scripts its output equals the Ethereum node's byte for byte. In the other 38 the node stopped at its gas limit: its record is empty, shorter, or first differs at a call that failed with empty return data (`opcodes/bytecode-gas.json`). The networks were compared with the node, and the node is now compared with the specification, so the chain of evidence no longer rests on any client being right.

Three more script sets, compared with the reference directly. With a reference that needs no node, each network can be compared with the specification itself. Three sets were written to reach the bytecode the first two leave out, and all 21 networks, Ethereum included, were compared with the reference interpreter's answer.

| Set | What it adds | Scripts and calls | Result on the 21 networks |
|---|---|---|---|
| `pmdiff3.py` | Owner and fee controller functions, protocol fees in swaps and their collection, ERC-6909 transfer, approval and operator functions, array reads of storage and transient storage, `settleFor`, hook data, a dynamic fee set by the hook, and 185 callbacks that pay what they owe and return, so that `unlock` completes | 300 scripts, 10,200 calls, 656 of them failing | 19 networks equal on all 300. Arc and HyperEVM equal on 299 |
| `pmdiff4.py` | Malformed calldata on a third of the calls: truncation, appended junk, words with dirty high bits, flipped bytes, wrong offsets, another function's selector | 300 scripts, 10,773 calls, 2,893 failing | 18 networks equal on all 300. Tempo 298, Arc and HyperEVM 299 |
| `pmdiff5.py` | Pools at extreme prices with liquidity up to 2^126: the 512 bit branch of `mulDiv` with denominator 2^96, amounts above 2^160, the overflow branches of the price functions and the SafeCast reverts behind them | 137 scripts compared (12 more were too long for the reference), 5,074 calls, 513 failing | 18 networks equal on all 137. Polygon, Arc and HyperEVM 133 |

Every script that is not equal is a long one, 6 to 12 million instructions in the reference, and the node's record is empty or stops at a call that failed with empty return data. Arc and HyperEVM grant a simulated call 30 million gas, the lowest of the 21.

The 512 bit branch deserves a note. `SqrtPriceMath.getAmount1Delta` goes through it when liquidity times the price difference needs more than 256 bits, which takes liquidity above about 2^100 at a price near the top of the range. In a swap the result is compared with the amount the caller offers and so decides whether the step reaches its target (`src/libraries/SwapMath.sol`, the comparison of `amountRemainingLessFee` with `amountIn`). No ordinary pool gets there, the scripts of the first four sets never did, and it is the one place where a wrong `MULMOD` would steer control flow without first showing up in a paid amount. Set five reaches it on every network.

Coverage. The five sets together execute 9,959 of the 10,418 instructions, 95.6 percent. Of 387 conditional jumps, 255 were taken both ways, 129 one way and 3 never. One real opcode is present and never ran: `SELFBALANCE`, in the native branch of `Currency.balanceOfSelf`, which sits behind a currency check its callers have already made and looks unreachable. The other opcodes that a linear disassembly shows and that never ran (`LOG1`, `ADDMOD`, `EXP`, `INVALID`) are the bytes of the compiler's version trailer at the end of the code. The largest ranges still not executed are the error wrapper for a failed call with long return data, a hook call path, and `mulDivRoundingUp` on an output amount above 2^160, which would need a pool holding more than 2^160 units of a token.

Step traces. Tempo's endpoint is the only one of the 21 that serves `debug_traceCall`. For 92 scripts the trace it returns was compared with the reference interpreter's at every step: call depth, program counter, opcode and the top four stack words, leaving aside words produced by `GAS`. All 2,925,870 steps agree. Twenty heavy scripts were skipped and eight requests failed at the endpoint. Tempo is the network with the newest interpreter and no second client, so this is the strongest single statement the review has about it.

The build against the source. `buildcheck.py` creates 4,000 random pools in the reference interpreter running the built bytecode, with 7,949 liquidity changes and 15,979 swaps, and compares every returned amount and the price, tick and liquidity in storage after every swap with the transcription of the source and a step loop written from `Pool.swap`. There is no mismatch, and the 180 cases the source says must revert do revert. For these paths the compiler's output computes what the source says. This is also the first evidence on the Yul optimizer fault that the Solidity bug list reports for 0.8.26: whatever it affects, it is not the swap or liquidity arithmetic of this build.

A second round of reading covered what the first left open.

| Subject | Result |
|---|---|
| Monad compiler, parts not read before | About 40 percent of the x86 emitter was read line by line. Operand order for the opcodes that are not commutative, the same stack slot used for both operands, comparison results held in CPU flags until the conditional jump, `JUMPI` on all four limbs, dynamic jump targets through a table over every byte offset, and division and remainder by powers of two at the signed edges all match the specification. Block execution runs contracts in the interpreter first and as compiled code once they are hot, and compiled code is tied to the chain revision it was built for. Not read: multiplication code generation, `EXP`, the byte and sign extension helpers per operand location, inline `CALLDATALOAD` and the runtime helpers for memory copies and hashing. Release v0.16.6, which is not on mainnet yet, adds a new compiled path for shifting a constant by a variable amount. `TickBitmap` and `BitMath` use exactly that shape, and no simulated call can reach compiled code, so that path should be read before validators adopt the release. |
| evm2 (Ethereum's reth nodes and Tempo) | The scans for jump destinations for AVX-512, AVX2, SSE4.1 and NEON were transcribed instruction by instruction and compared with the scalar rule on 424,000 random and constructed byte strings without a mismatch. Stack, memory, data, call and transient storage instructions match the specification as read, and 85 probes confirmed the edges on both endpoints. One fix in the revision range changes a result (storage read after a rolled-back creation into an address that already has storage), and Tempo has had it since v1.18.2. |
| Arbitrum One, Robinhood Chain, Elysium | All three report ArbOS 61 and run the Osaka instruction set. The fork of go-ethereum that Nitro v3.12.4 pins differs from upstream v1.17.4 only outside arithmetic, jumps, memory, return data and transient storage. The release the endpoints report (v3.13.0-rc.9) is not public, and Elysium's build names no version. |
| revm releases | No fix between interpreter 35.0.1 and the newest release corrects an arithmetic, jump, memory, return data or transient storage result of the stock interpreter. |
| Second clients | OP Mainnet, Unichain, Ink, Soneium and Zora have run op-reth alone since the Karst upgrade of 8 July 2026, Base runs base-reth-node alone, and Celo has run op-reth alone since 22 July 2026. Most of the 21 networks are therefore single-client in practice. |

Check 3 was also run over a longer window on the six networks that never had a second client: 17,434 swaps on Monad, 39,074 on MegaETH, 39,060 on Arc, 28,496 on Elysium, 12,977 on Tempo and 2,071 on HyperEVM. All 139,112 pass the tick relation, and 127,949 of the 129,093 paired ones match the single-step formulas to the unit (`opcodes/swaps-deep.json`). On Monad these swaps ran as compiled code.

## What this does not cover

- The 4.4 percent of the bytecode the scripts do not execute, and the 129 conditional jumps taken only one way, described under coverage above.
- The repository's own test suite. It needs forge, which is not installed, so whether the tests pass on this build is still open.
- Compiled code on Monad beyond the 17,434 mined swaps, and the parts of its emitter that were not read.
- Validators that run other hardware or other builds than the public endpoints: the vector code for jump destinations in evm2, the optional dispatch loop in bor, and any operator on the withdrawn ruint release.
- The HyperEVM validator and the MegaETH node, which are closed, and the Arc commit behind `arc/v1`.
- Liquidity changes and hook calls in mined blocks. `ModifyLiquidity` events do not carry the amounts, so only the simulated scripts of the second check cover them, and on Monad those run in the interpreter.

## How to run it again

```bash
python3 research/network-risk/tools/opdiff/v4math.py
```

```bash
python3 research/network-risk/tools/opdiff/battery.py research/network-risk/opcodes/battery.json
```

```bash
python3 research/network-risk/tools/opdiff/targeted.py research/network-risk/opcodes/targeted.json
```

```bash
python3 research/network-risk/tools/opdiff/pmdiff.py research/network-risk/opcodes/pmdiff.json 250
```

```bash
python3 research/network-risk/tools/opdiff/pmdiff2.py research/network-risk/opcodes/pmdiff2.json 300
```

```bash
python3 research/network-risk/tools/opdiff/swaps.py research/network-risk/opcodes/swaps.json
```

```bash
python3 research/network-risk/tools/opdiff/replay.py research/network-risk/opcodes/swaps.json research/network-risk/opcodes/replay.json
```

The build and the bytecode-level checks need the compiler package once (`npm install solc@0.8.26` in a directory outside the repository):

```bash
node research/network-risk/tools/build/compile.js <dir>/node_modules/solc . research/network-risk/build/PoolManager.json
```

```bash
PM_BUILD=research/network-risk/build/PoolManager.json python3 research/network-risk/tools/opdiff/buildcheck.py research/network-risk/opcodes/build-check.json 4000
```

```bash
python3 research/network-risk/tools/opdiff/bytecode.py research/network-risk/opcodes/pmdiff.json research/network-risk/opcodes/pmdiff2.json research/network-risk/opcodes/bytecode.json 60000000
```

```bash
python3 research/network-risk/tools/opdiff/trace.py research/network-risk/opcodes/trace-tempo.json 60
```

```bash
PM_BUILD=research/network-risk/build/PoolManager.json python3 research/network-risk/tools/opdiff/pmdiff3.py research/network-risk/opcodes/build-pmdiff3.json 300
```

```bash
PM_BUILD=research/network-risk/build/PoolManager.json python3 research/network-risk/tools/opdiff/pmdiff4.py research/network-risk/opcodes/build-pmdiff4.json 300
```

```bash
PM_BUILD=research/network-risk/build/PoolManager.json python3 research/network-risk/tools/opdiff/pmdiff5.py research/network-risk/opcodes/build-pmdiff5.json
```

```bash
PM_BUILD=research/network-risk/build/PoolManager.json python3 research/network-risk/tools/opdiff/coverage.py research/network-risk/opcodes/build-pmdiff3-coverage.json,research/network-risk/opcodes/build-pmdiff4-coverage.json,research/network-risk/opcodes/build-pmdiff5-coverage.json research/network-risk/opcodes/coverage.json
```

With `PM_BUILD` set, every script runs the built bytecode instead of the deployed one.

Each takes a list of chain ids as further arguments to run on some networks only. The battery and the scripts use fixed seeds, so a rerun after a network upgrade tests the same inputs. A rerun is worth doing after every client release on the single-client networks (Monad, MegaETH, Tempo, HyperEVM, Arc, Robinhood Chain, Elysium) and after any ruint, revm or evm2 upgrade.
