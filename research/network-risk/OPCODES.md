# Opcode behaviour on the 21 networks and what it means for the pool math

State on 2026-11-24. This part of the review asks one question: does any of the 21 networks compute an opcode, or run control flow, differently from Ethereum in a way that changes the arithmetic or the logic of this repository's PoolManager?

## Answer

No difference was found. Four independent checks on the networks agree, and each covers a weakness of the others. A fifth part, added after a compiler became available, works on the bytecode built from this checkout.

1. A battery of 185,529 opcode test vectors gave the specified result on every one of the 21 networks, with no mismatch.
2. The deployed PoolManager bytecode, placed at the same address with the same empty state on every network, answered 550 scripts of about 28,000 calls with the same bytes as on Ethereum. The scripts cover the pool math, hook callbacks, token transfers with unusual return data and revert handling. The only differences, on Polygon, Monad, Tempo, Elysium and HyperEVM, are swaps that ran out of gas.
3. 99,903 swaps that the networks have already mined satisfy the exact relations the source's math fixes. All 99,903 pass the tick relation. Of the 88,576 that could be paired with the swap before them, 85,278 match the single-step formulas to the unit, and 228 of the 229 sampled multi-step swaps replay to the unit. Cycle 13 then replayed a further 70,053 mined swaps on all 21 networks one by one, 63,848 as a single step and 6,205 through the whole swap loop, and every one matches to the unit.
4. A reading of the node source for the networks whose interpreter is not go-ethereum or stock revm found no opcode that departs from the specification.

One thing came out of the reading that deserves a place in the deployment checklist. The big integer library behind reth based nodes shipped a release on 20 October 2026 that returned wrong `MULMOD` results in one edge case. It was withdrawn three days later. No network on the list runs it or ran it, and the vectors built to hit it pass everywhere. Ethereum's reth nodes and Tempo run the first fixed release, whose arithmetic paths are one month old, and Tempo has no second client to disagree with it.

5. This checkout builds to a PoolManager of 24,009 bytes whose creation code hash equals the one recorded in `snapshots/PoolManagerTest.json`. Run in a reference interpreter written for this review, the bytecode gives the same answer as every one of the 21 networks on 1,993 scripts that execute 98.75 percent of its instructions, apart from scripts a node could not afford. Its step trace equals the traces of Tempo, Ink and the HyperEVM archive client at each of 110.7 million steps, and its swap and liquidity amounts equal the source's formulas on 4,000 random pools.

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

Step traces. Three endpoints serve `debug_traceCall` with a state override: Tempo's, Ink's (`rpc-qnd.inkonchain.com`, an op-reth build without a version) and the HyperEVM archive client nanoreth (`rpc.purroofgroup.com`). For each script the trace the node returns was compared with the reference interpreter's at every step: call depth, program counter, opcode and the top four stack words, leaving aside words produced by `GAS`. No step differs.

| Endpoint | Scripts compared | Steps equal | Not compared |
|---|---|---|---|
| Tempo, sets 1 and 2 | 92 | 2,925,870 | 20 heavy scripts skipped, 8 requests failed at the endpoint |
| Tempo, set 3 | 77 | 1,328,483 | 2 skipped, 1 answer too large |
| Ink, sets 1 and 2 | 100 | 4,880,989 | 20 skipped |
| Ink, set 3 | 78 | 1,703,314 | 2 skipped |
| HyperEVM archive client, sets 1 and 2 | 97 | 3,753,607 | 20 skipped, 3 answers too large |
| HyperEVM archive client, set 3 | 77 | 1,328,483 | 2 skipped, 1 answer too large |
| Tempo, set 6 | 693 | 19,094,085 | 13 heavy scripts skipped |
| Ink, set 6 | 693 | 19,094,085 | 13 skipped |
| HyperEVM archive client, set 6 | 693 | 19,094,085 | 13 skipped |
| Tempo v1.19.1, sets 1 to 3 in full | 692 | 18,359,233 | 850 scripts; 101 heavy skipped, 57 refused by the endpoint (trace size limit or gateway error) |
| Tempo v1.19.1, set 6 | 693 | 19,094,085 | 13 skipped |

That is 110.7 million steps, 37.5 million of them on the Tempo build that replaced v1.19.0 on 24 November 2026. Set 3 holds the hooks that return deltas, dynamic fees, protocol fees and owner calls. Set 6 is the cycle 12 set that takes the sides of 83 conditional jumps no earlier script took (`clear` of an exact credit, allowances, hooks that return deltas or call the PoolManager themselves, the large-number branches of the price and fee math, malformed calldata for every function), so those branches are now checked step by step on three clients as well as by their answers on 21. Tempo has the newest interpreter and no second client, so this is the strongest single statement the review has about it. On HyperEVM the trace comes from the archive client, which is stock revm; the closed validator is not reachable this way.

The build against the source. `buildcheck.py` creates 4,000 random pools in the reference interpreter running the built bytecode, with 7,949 liquidity changes and 15,979 swaps, and compares every returned amount and the price, tick and liquidity in storage after every swap with the transcription of the source and a step loop written from `Pool.swap`. There is no mismatch, and the 180 cases the source says must revert do revert. For these paths the compiler's output computes what the source says. This is also the first evidence on the Yul optimizer fault that the Solidity bug list reports for 0.8.26: whatever it affects, it is not the swap or liquidity arithmetic of this build.

A second round of reading covered what the first left open.

| Subject | Result |
|---|---|
| Monad compiler, parts not read before | About 40 percent of the x86 emitter was read line by line. Operand order for the opcodes that are not commutative, the same stack slot used for both operands, comparison results held in CPU flags until the conditional jump, `JUMPI` on all four limbs, dynamic jump targets through a table over every byte offset, and division and remainder by powers of two at the signed edges all match the specification. Block execution runs contracts in the interpreter first and as compiled code once they are hot, and compiled code is tied to the chain revision it was built for. Not read: multiplication code generation, `EXP`, the byte and sign extension helpers per operand location, inline `CALLDATALOAD` and the runtime helpers for memory copies and hashing. Release v0.16.6, which is not on mainnet yet, adds a new compiled path for shifting a constant by a variable amount. `TickBitmap` and `BitMath` use exactly that shape, and no simulated call can reach compiled code, so that path should be read before validators adopt the release. |
| evm2 (Ethereum's reth nodes and Tempo) | The scans for jump destinations for AVX-512, AVX2, SSE4.1 and NEON were transcribed instruction by instruction and compared with the scalar rule on 424,000 random and constructed byte strings without a mismatch. Stack, memory, data, call and transient storage instructions match the specification as read, and 85 probes confirmed the edges on both endpoints. One fix in the revision range changes a result (storage read after a rolled-back creation into an address that already has storage), and Tempo has had it since v1.18.2. |
| Arbitrum One, Robinhood Chain, Elysium | All three report ArbOS 61 and run the Osaka instruction set. The fork of go-ethereum that Nitro v3.12.4 pins differs from upstream v1.17.4 only outside arithmetic, jumps, memory, return data and transient storage. The release the endpoints report (v3.13.0-rc.9) is not public, and Elysium's build names no version. |
| revm releases | No fix between interpreter 35.0.1 and the newest release corrects an arithmetic, jump, memory, return data or transient storage result of the stock interpreter. |
| Second clients | OP Mainnet, Unichain, Ink, Soneium and Zora have run op-reth alone since the Karst upgrade of 8 July 2026, Base runs base-reth-node alone, and Celo has run op-reth alone since 22 July 2026. Most of the 21 networks are therefore single-client in practice. |

Check 3 was also run over a longer window on the six networks that never had a second client: 17,434 swaps on Monad, 39,074 on MegaETH, 39,060 on Arc, 28,496 on Elysium, 12,977 on Tempo and 2,071 on HyperEVM. All 139,112 pass the tick relation, and 127,949 of the 129,093 paired ones match the single-step formulas to the unit (`opcodes/swaps-deep.json`). On Monad these swaps are the results of RPC nodes, which interpret; cycle 14 showed that such a node only keeps up with the chain while its results equal the ones the validators certified (see "What cycle 14 added").

## What cycle 9 added

Cycle 9 was the first cycle planned for this question. Six units worked on it, each followed by an independent verifier.

| Unit | Result |
|---|---|
| Bytecode map | All 10,418 instructions are assigned to the dispatcher, the 33 external functions, 60 internal functions or data. Each of the 66 `MULMOD`, `SDIV`, `SMOD`, `SAR`, `BYTE`, `DIV` and `MOD` instructions and a sample of 103 sign extension and shift instructions was traced to its source line through the optimized intermediate code, and the internal functions were tested on 64,187 edge cases and on every tick of the range, with no mismatch. The optimizer made constant-denominator copies of `mulDiv` and fused shifts in the logarithm and bit scans; each rewrite is a valid identity. `SELFBALANCE` is dead code. The faulty `MULMOD` of ruint 1.21.0 cannot be reached by any `MULMOD` in this bytecode for any input. |
| Compiler bugs | Eight entries of the Solidity bug list apply to 0.8.26, six of them to a build through the intermediate representation with the optimizer on. None affects this build. The one named SOL-2026-7 sits in two optimizer steps, runs from 0.8.19 to 0.8.37 and is fixed in 0.8.38. The installed compiler reproduces it on the Solidity team's example. For the PoolManager, a build with one of the steps and two of the three runs of the other removed is byte identical to the real build, and the loads that the remaining run replaces all use addresses that are never reassigned. The other five need recursive structs, storage arrays, a `require` with a named custom error or mutual recursion, and the source has none. |
| Monad and MegaETH | The new compiled shift path of Monad v0.16.6 and the inline comparison, sign extension and byte paths of v0.16.5 give the specified results in Python transcriptions on about 2.9 million cases. The verifier found one clearance wrong: the bytecode has `MULMOD` with the constant moduli 2^96 and 2^128, and Monad compiles those through a multiplication path nobody had read. Cycle 10 transcribed it. Mined swaps already speak to one of the two sites: of 3,875 recent Monad swaps, 183 paid token1 with an amount that includes the rounding bit taken from `mulmod(liquidity, priceDifference, 2^96)`, the remainder was nonzero in all 183, and every amount is exact (`opcodes/monad-rounding.json`). |
| Arbitrum One, Robinhood Chain, Elysium | 207,953 vectors and all script sets match on all three, on both the arm64 and the amd64 builds of the node. The Go toolchain that two of the nodes report has a published miscompile, which cycle 10 followed up across all the go-ethereum family clients. |
| Celo, X Layer | Celo's public endpoint is served by two different clients. Both, and X Layer, match the specification on 188,640 vectors and on the scripts run with this build. One of the two Celo backends is a client Celo no longer supports (F-116, operator level, low). |
| Polygon, BNB Smart Chain, Avalanche | All vectors and scripts match on six endpoints, among them a second BNB Smart Chain client and the execution path Avalanche uses today. One tick crossing costs about 17,000 gas on BNB Smart Chain, 27,700 on Polygon and 27,000 to 33,000 on Avalanche. |

## What cycle 10 added

Cycle 10 took the three questions cycle 9 left open and reran the checks on eleven networks. Six units worked on it, each followed by an independent verifier. It found no difference.

| Unit | Result |
|---|---|
| Monad's compiled multiplication | The inline `MULMOD` by 2^128 (program counter 22378) and by 2^96 (22639), the 23 multiplications by a literal that the compiler inlines, and the runtime multiply routines of v0.16.5 were transcribed instruction by instruction. One million cases per path match the specification, and so do all 1,774,545 ticks, which run 62.9 million compiled products. Faults planted in the transcription were caught, so the test can fail. The same functions are unchanged in v0.16.6 and v0.16.7. One correction to cycle 9: the 183 rounding swaps ran the runtime `MULMOD` at program counter 23094. No mined swap reaches the two inline sites, so the transcription is the only evidence for them. |
| MegaETH's executor | The sequencer runs a closed, parallel executor that compiles bytecode. The default public RPC nodes apply its results without running them again, and the public stateless validator runs them again with the stock revm interpreter (F-118, operator level, information). So a simulated call on MegaETH tests a different EVM from the one that writes state. The producer was therefore tested through mined results: all 53,811 swaps pass the tick relation, all 2,885 swaps that crossed ticks or took several steps replay to the unit, and the receipts of 7,627 PoolManager transactions equal a second execution. In 1,333 of those a frame that had entered `unlock` reverted and a later `unlock` completed, so the producer rolled back the lock and the deltas. |
| Go compiler miscompile | Go issue 81863 is real. From go1.26.0 to go1.26.10 and go1.27.0 to go1.27.3 the compiler can drop a store made through a pointer that a branch chose between two local variables. Arbitrum One, Robinhood Chain, Polygon, BNB Smart Chain and Avalanche nodes report an affected toolchain; the fix came out on 10 November 2026. No function of the integer library, the interpreter or the state code of these five clients has the shape that triggers it (F-117, operator level, information). The check is a source reading, because no Go toolchain was available to inspect the compiled code. |
| Tempo, Arc | All scripts match again. Newly read and clean: the process-wide cache in front of `KECCAK256`, the per-processor jump destination code of evm2 (28,014 cases with `0x5b` inside push data), the non-x86 arithmetic of ruint 1.21.1 (200 million cases against the x86 path) and reuse of interpreter frames. The published Tempo binaries are built without the optional compiler. |
| OP Stack chains with ETH gas | 185,529 vectors, 250 scripts on the deployed bytecode, 137 extreme-price scripts on this build and 19,431 mined swaps match on all seven chains. OP Mainnet's endpoint is served by two op-reth builds, one without a version; both match. Base builds the stock instruction table and replaces no instruction. |
| HyperEVM | 185,529 vectors, 21,759 jump targets and 549 of 550 scripts match on the official node; the last one matches with 30 million gas. The whole mined history of 2,284 swaps fits the source math. The official `eth_call` ignores the block tag and reports a timestamp one second off, and the PoolManager reads neither. |

After the cycle, the one deployment with different bytes was run as well. Unichain's PoolManager is a genesis predeploy of 24,050 bytes whose trailer differs. With `PM_FROM=130` the script tools load its bytecode in place of Ethereum's. All 250 and 300 scripts of the first two sets give the same records as the Ethereum bytecode, on the Ethereum node and on the Unichain node, and 400 scripts of the third set equal the reference interpreter on both nodes, the first 300 with the same records as this build (`opcodes/unichain-predeploy.json`).

One more differential was added on the state side. `statekeys.py` writes one storage slot and then reads 762 other slot indexes that differ from it in a single bit, in the top byte, in the low byte or by truncation, for eight base slots, three of them slots the PoolManager really uses. It does the same with transient storage. Of 256,158 reads on the 21 networks, the only ones that returned the written value are on Avalanche, for the index that differs in bit 248 alone. That is the known rule of the C-Chain (F-040), and it shows the check can see a fold. No network folds transient slots, and no other network folds storage slots (`opcodes/statekeys.json`).

The Avalanche rule cannot reach the PoolManager's own storage. Its fixed slots are 0 to 6, and every other slot it writes is a `keccak256` output or one plus an offset below 7, so two slots collide only if two hashes agree in 255 bits, which costs about 2^127 hash evaluations. No function writes to a slot index the caller supplies; `extsload` only reads. The rule matters for contracts whose author picks slot constants by hand, so `avaxslots.py` scanned the bytecode of the ten official v4 contracts on Avalanche and of all 300 hooks that an `Initialize` event names. None holds two 32 byte constants that differ only in bit 248 (`opcodes/avalanche-slot-constants.json`). The scan sees constants only; a slot computed at run time is outside it.

The rules around calls were checked the same way. `callsem.py` runs 50 small tests in one simulated call: a reverted call undoes its transient and persistent writes, a static call cannot write even through a nested plain call, return data has the size the callee gave and a copy past its end fails, a delegate call writes to the caller's slots, and a call with value moves exactly that many wei or fails and moves none, also when the callee reverts. All 21 networks give the specified word on all 50 (`opcodes/callsem.json`). The reference interpreter gives the same 50 words.

## What cycle 11 added

Cycle 11 went after block production, the part a simulated call cannot reach. Six units worked on it, each followed by an independent verifier. No payout, receipt or storage word differs from the source on any network.

| Unit | Result |
|---|---|
| Monad's compiled settlement path | In v0.16.5 `CALLDATALOAD`, `CALLER`, `CALLVALUE`, `RETURNDATASIZE` and `SIGNEXTEND` with a variable index are compiled inline. Their transcriptions match the specification at every operand location (411,200, 159,098 and 896,400 cases), and planted faults were caught. `KECCAK256`, `TLOAD`, `TSTORE`, the copy opcodes, `CALL` and `STATICCALL` call the same C++ functions as the interpreter, and a revert undoes `TSTORE` through the same journal. On Monad `debug_traceTransaction` with the call tracer returns the frames that block execution recorded. In 12,000 mined transactions those frames follow the `settle`, `sync` and `take` rules of the source, and all 13,635 completed unlocks without hooks net to zero per account and currency. A planted over-credit of one unit fails that check. |
| Mined liquidity removals | 1,493 mined removals and fee collections were rerun from the storage of the parent block: Monad 169, MegaETH 413, Tempo 428, Arc 427, HyperEVM 56 (its whole history). Every one paid exactly what the source owes, to the unit, and left the storage the rerun predicts. Native payments were checked against data that block production wrote: balance changes of the PoolManager, and on Arc the Transfer logs of the system emitter. On Monad 69 of the 108 native legs are alone in their block and all 69 match the balance change; 21 in shared blocks rest on the trace alone. 202 transactions were set aside, mostly removals inside transactions that also swap. |
| Closed block producers | Receipts were compared with a second execution on the three networks where the producer is not the code that answers RPC. MegaETH: 43,342 more transactions, 8,481 with a reverted and then completed unlock, 87 with `take`, 2 with `settle` and 1 with `sync` inside a reverted frame, 151 removals and 454 fee collections, 3,861 storage slots equal. HyperEVM: all 2,762 transactions of its history, one with `sync`, `settle` and `take` inside a reverted frame. Polygon: 4,000 transactions, 10 with all three inside a reverted frame, 844 slots equal. bor v2.11.1 resets transient storage and the access list for each transaction and each re-execution. One new finding at operator level: HyperEVM headers carry a zero state root, so the public clients check the validator's receipts but never its storage writes (F-120, information). |
| The cache in front of `KECCAK256` | The cache is on by default in reth v2.11.0, op-reth v2.8.1 and v2.9.0-rc.1, Base v1.5.6 and X Layer v0.0.7. It is off in World Chain and celo-reth, and unknown for Zora's build and the closed MegaETH node. The cache library compares the full key and reads under a lock, so it cannot return the hash of another input. A test built to make inputs share a cache bucket sent 108,177 hashes to each of 14 endpoints, among them the 64 byte and 58 byte shapes the PoolManager hashes, with no mismatch. Polygon's bor has its own cache for 64 byte inputs, keyed by the whole input, which is also clean. |
| Arbitrum One, Robinhood Chain, Elysium | Every opcode and script rerun matches. The state these chains settle on their parent chain is computed by a WebAssembly build made with go1.25.9, which is outside the range of the Go miscompile, and the public nodes run a native go1.27.3 build (F-119, operator level, information). On Arbitrum One 31 confirmed assertions equal the node's block hashes. The same match on Robinhood Chain and Elysium is weaker evidence: their rollups accept assertions only from two and one whitelisted validators, so it shows the operator agreeing with itself. |
| Celo, X Layer | 185,529 vectors, 3,045 new shift-amount vectors, 687 script runs on this build and 654 mined swaps match. The shift advisory for the integer library X Layer pins cannot be reached, because the interpreter clamps the amount first. X Layer's gasless list covers none of the PoolManager, PositionManager or router addresses. |

The critic of this cycle raised one lead that an ordinary account might control, on Polygon: bor v2.11.1 reads a callee's code and its code hash in separate state reads and stores the jump destination map of that code in a cache keyed by the hash, which the parallel workers of a block share. Cycle 12 read it and cleared it (below).

## What cycle 12 added

Cycle 12 took the Polygon cache question, the parts of the bytecode no script had run, liquidity removals on the networks cycle 11 had left out, and the builds that compute the settled state of rollups. Six units, each followed by a verifier. No payout, receipt, storage word or opcode result differs from the source or the specification on any network.

| Unit | Result |
|---|---|
| Code caches (lead L-645) | Cleared. In bor v2.11.1 a parallel worker keeps the first read of each address's code for the whole attempt at a transaction (`core/state/parallel_statedb.go` lines 359-381). The field's comment names this case: an account that changes its delegation between the read of the code and the read of the hash. The hash is the keccak of the bytes that were read, so a map is always stored under the hash of the bytes it describes. The serial path, the witness path, the block producer and the prefetcher each use one state object on one thread. A wrong map could not redirect a jump in the PoolManager in any case: the bytecode has 29 bytes of value `0x5b` inside push data, and no push constant names one of them as a jump target. BNB Smart Chain's process-wide map cache, Nitro's sharded cache, Avalanche's per-transaction map, the jump tables that revm keeps inside the bytecode value, and Monad's lookup of code by hash are all keyed by the content. A call to the PoolManager through a delegated account ran correctly on 20 networks; Avalanche has no delegated accounts. The twelve hex digits in Polygon's version string turned out to be the node's host name, which bor uses as its identity by default, and Polygon states that the private build and the public tag are the same code. |
| Bytecode coverage | A sixth script set (`tools/opdiff/pmdiff6.py`, 706 scripts, 25,681 calls) was written from a map of every conditional jump to its source line. The six sets together now execute 10,288 of 10,418 instructions (98.75 percent, up from 95.6) and take 338 of 387 conditional jumps both ways. 83 of the 132 jumps that had gone one way now go both ways, among them `clear` of an exact credit, finite and infinite allowances, hooks that return deltas, hooks that call the PoolManager themselves, and the two large-number branches of the price and fee math. The 49 left are guards that bounds earlier in the source make unreachable, or repeated tests; `opcodes/jumpmap.json` gives the reason for each. All 21 networks answer as the reference interpreter does. The exceptions are four scripts where a swap across the whole price range ran out of gas, and scripts that name address `0x1000` as a currency, which is a system contract on Polygon and BNB Smart Chain and the staking precompile on Monad. |
| Mined liquidity removals, second round | 3,083 removals and fee collections on eight networks were rerun in a block-level simulator that carries swaps, crossed ticks, fee growth, donations and claims forward inside the block: Polygon 321, BNB Smart Chain 377, Robinhood Chain 322, Elysium 270, Avalanche 275, plus the cases cycle 11 had set aside on Monad, MegaETH and Arc, which are removals inside transactions that also swap. All match the source to the unit. Three groups needed an explanation and have one: 9 Polygon transactions where the caller itself gave up a dust credit through `clear`, native payments that share a block (7 on Elysium, 1 on BNB Smart Chain, reconciled per block), and one Avalanche token that mints interest. On Monad 456 blocks reconcile native flows to the wei and 1,905 unlocks with hooks or burns net to zero. |
| Proof builds | OP Mainnet, Unichain and Ink now settle withdrawals against kona-client 1.9.0, a Rust program on the Cannon MIPS64 machine that no RPC endpoint runs (F-122, operator level, information). World Chain uses op-program 1.9.0 with a permissioned proposer, and Zora and Soneium name no proof program at all (F-123, same level). The Go arithmetic behind the Arbitrum replay (generic code for 64 bit multiply, add, subtract and divide on WebAssembly) and behind op-program on MIPS64 was transcribed and run against 85,544 targeted vectors, 96,224 battery vectors and the pool math checks, with no mismatch, and planted faults were caught. The Rust path of kona on MIPS64 was read and not yet run. |
| Polygon, BNB Smart Chain, Avalanche | 185,529 vectors, 550 scripts and 11,068 newly mined swaps match. BNB Chain's own RPC nodes run a geth commit that is not in the public repository (F-121, operator level, information); it answers every vector and script as the public tag does. The next bor release (v2.12.0-beta, not deployed) puts a one-entry memo in front of `MULMOD` for full-width moduli, which is the call `FullMath.mulDiv` makes on every swap. As read it returns the stock result for every input, and 8,415 sequences built for it are stored as a baseline to rerun when a node runs it. reth-bsc pins an integer library inside the range of the shift advisory, which cannot be reached because the interpreter clamps the amount first. |
| OP Stack chains with ETH gas | 185,529 vectors, 550 scripts and 19,859 mined swaps match on all seven. OP Mainnet's endpoint alternates between a versioned build and one without a version string; requests bracketed by a version query on both sides show the unversioned build giving the same answers. Four Ink swaps that an earlier replay could not reproduce are correct swaps at tick spacing 90, a spacing the replay tool did not try. |

The critic's one high lead of the cycle was read directly, and it is cleared. Monad v0.16.7 carries a comment that reverted state depends on whether code ran compiled or interpreted. The question was whether a credit written inside a frame that later reverts could survive on one of the two paths while the payment is rolled back. It cannot. Monad keeps an account's balance, storage, transient storage, touched flag and warm sets in one object per address, copies that object when a frame first writes to it, and drops the copy when the frame fails (`state3/state.cpp` lines 126-181, `version_stack.hpp`; the files are identical in v0.16.5 and v0.16.7). The comment describes the inside of a failing frame: compiled code checks gas once per basic block and stops before the block, while the interpreter stops part of the way through it. Both discard the partial work. The one thing v0.16.5 kept after a revert was a touch of the address of the ripemd precompile, and v0.16.7 removed that.

## What cycle 13 added

Cycle 13 went after the items cycle 12 left open: the mined swaps no formula had reproduced, mined instances of the newly covered branches on the three networks whose block producer differs from the program that answers a simulated call, the builds that prove rollup state, and what each client does differently around a call. Six units, each followed by a verifier. No swap, receipt, storage word or opcode result differs from the source or the specification on any network.

| Unit | Result |
|---|---|
| Mined swaps, every one replayed (lead L-679) | Closed with nothing unmatched. New windows hold 70,053 mined swaps on all 21 networks. 63,848 match one step of `SwapMath.computeSwapStep`. The other 6,205 were run through the whole loop of `Pool.swap` with the pool's real key, the tick bitmap and `liquidityNet` read at the parent block, and state carried forward inside the block by log index. All 6,205 match to the unit in both amounts, price, tick and liquidity. The fee in the event matches `slot0` on 5,384 swaps, and the change of `feeGrowthGlobal` in storage matches on 780. The 869 residue samples kept from cycles 8 to 12 replay as well, including the Arbitrum, Avalanche and Robinhood cases that earlier endpoints could not serve. The old residue was swaps that take several steps or cross ticks, plus tick spacings the old tool never tried (90 on Ink, 190 on Arc). 451 events with zero amounts come from pools whose hook returns the whole delta. The tool is `cycles/013/theme-swap-residuals.work/replay2.py`. Two limits: the Celo and World Chain windows are small (428 and 944 swaps), and for 104 HyperEVM swaps the tick spacing was found by search and not read from the `Initialize` event. |
| Mined branches on Monad, MegaETH and HyperEVM (lead L-678) | 7,837 mined transactions were rerun in the reference interpreter from the PoolManager's storage before each transaction, and compared with the block's call frames, receipts and committed storage. Monad matches on 3,507 of 3,507, MegaETH on 1,566 of 1,567 and HyperEVM on 2,762 of 2,763. The one left over on each of the last two is the deployment of the PoolManager itself. A planted `MULMOD` fault made 15 of 15 replays fail, so the comparison can see a wrong product. Hooks that return deltas, hooks that call the PoolManager, fee overrides, `settleFor`, `mint` and `burn`, native `take`, exact output swaps and swaps to a price limit all have mined instances that match. Of the 83 jump sides cycle 12 reached for the first time, only 5 (Monad), 7 (MegaETH) and 8 (HyperEVM) occur in mined blocks, all in `Hooks.sol`. |
| Proof builds, second round | The Rust opcode handlers behind kona-client (OP Mainnet, Unichain, Ink) were compiled for kona's MIPS64 target, and the ones behind Base's SP1 range program for RISC-V. Both builds were run in emulators of the two machines and match 85,544 targeted vectors, 96,876 battery vectors and the pool math, and planted faults were caught. One real compiler fault is on record: LLVM issue 235261, where 128 bit shifts by 64 to 127 can be miscompiled on MIPS64. The toolchain that built kona-client 1.9.0 predates the fix. A scan of the program image that settles today finds 66 sites with the instruction in question and none with the faulty shape on a fall-through path (F-126, information). The scan does not follow branches. Base's game type 621 lets any account with a valid SP1 proof challenge a proposal (F-127, information; the proof program computes as the node does). Celo and X Layer run OP Succinct games with allowlisted proposers and challengers. These runs used rebuilds from source, since the published images could not be executed here. The Nitro build that Arbitrum One and Robinhood Chain report is private and could not be read. |
| Callee gas and replaced handlers (leads L-681, L-684) | The PoolManager calls out at four places only: the native payout, the token transfer, the `balanceOf` read of `sync`, and the hook call. In each the target is chosen by the caller of that action or fixed by the pool key, so an address that burns forwarded gas (Monad `0x1000` and `0x1001`, HyperEVM `0x0800` to `0x0813`, the Arbitrum precompiles, Celo `0xfd`, Arc `0x1800..05` to `..09`, Avalanche `0x0200..05`) can only be placed there by the party whose own action then fails. Failing precompiles burn forwarded gas on Ethereum too. Arc v0.8.6 replaces one instruction, `SELFDESTRUCT`, which the bytecode does not contain, and wraps every call that carries value in a check that fails transfers to the zero address, to blocklisted accounts and to accounts destroyed earlier in the transaction (F-125, information, an extension of F-108). MegaETH rebuilds all 256 handlers as gas wrappers around the stock ones and forwards 98/100 of the remaining gas where Ethereum forwards 63/64. None of the replaced handlers on Arc, MegaETH, Tempo or Nitro changes an arithmetic, hashing, memory, return data or transient storage result. |
| Monad and MegaETH | 185,529 vectors and 550 scripts match on both. Monad's endpoint now runs the v0.16.7 interpreter. Four more changes to its compiler between v0.16.5 and v0.16.7 were read, and the block-exit stack write was modelled on 200,000 random states with no difference. One reading changes what earlier Monad results mean: a simulated call on Monad always runs the interpreter (`monad_executor.cpp` lines 1306-1309), so every vector and script ever sent to Monad tested the interpreter and none tested compiled code. The compiled path is covered only by reading and by the mined replays above. F-062 (a MegaETH delay with no loss of funds) stays plausible at low severity. |
| Tempo and Arc | 185,529 vectors, 550 scripts and 6,997 mined swaps match on Tempo v1.19.0 and on Arc v0.8.6-rc1, the build Arc's endpoint now names. Arc nodes from v0.8.0 to v0.8.4 could serve stale storage for an account without code that a block deleted and created again (F-124, operator level, information). The PoolManager, tokens and hooks have code, and for those the cache is cleared as a whole. Tempo's keccak cache hash was rebuilt from the crate and matches the earlier model on 41,710 inputs. |

Tempo changed build while the cycle ran, from v1.19.0 to v1.19.1, so the cycle's Tempo results described a build the endpoint no longer runs. The new build was checked directly afterwards. Its lock moves the interpreter (evm2) from commit 66687c18 to 35aa3280. The change between the two was read file by file: no arithmetic, comparison, shift, jump analysis, memory, copy, return data or transient storage handler changed. Three changes touch execution. The call instructions were refactored so that a precompile can start a call with the same charges as the opcode. Idle call frames now have their memory trimmed before a top-level message starts; a running frame is never in that pool, the last frame is spared, and a returned frame's output is copied before anything else can run, so no live data is affected. The `SSTORE` test that skips a cold load now uses the full cold cost, which gives the same out-of-gas outcome. The release binaries are built without the JIT feature. On v1.19.1 the 185,529 vectors, the 50 call semantics words, 12,198 storage and transient slot reads and all four script sets run on it (1,556 scripts) give the results recorded for v1.19.0, with the same 18 gas-limited scripts differing. Its step traces equal the reference interpreter on 1,385 scripts and 37,453,318 steps, with no step different.

After the cycle the opcode checks were run again on the other 20 networks at the builds their endpoints report on 24 November 2026: 185,529 vectors, 50 call semantics words, 12,198 slot reads, and the first, second and sixth script sets (1,256 scripts). Every result equals the recorded one. The scripts that differ are the same gas-limited ones as before, except on Polygon, where the new endpoint has a higher gas cap and four full-range swaps that used to run out of gas now complete and match. This covers op-reth v2.10.0-rc.4 on Unichain, Ink and Soneium, and Polygon through an endpoint that reports bor v2.11.1.

Tempo v1.19.1 also carries code for a later hardfork (T15) under which a token transfer to a reserved "zone deposit address" is forwarded to a portal contract by a call from inside the token precompile. That is not active on mainnet and is recorded as a lead.

## What cycle 14 added

Cycle 14 took the largest open item, Monad's compiled code, together with producer evidence for the large-number branches on the closed networks, the reth cache fault on the other reth based chains, the proof program images, and fresh runs on HyperEVM, the Arbitrum family and Ethereum. Seven units, each followed by a verifier. No opcode, swap or settlement result differs from the source or the specification on any network.

| Unit | Result |
|---|---|
| Monad's native path | No RPC method on Monad reaches compiled code. Simulated calls, traces, replays and `eth_simulateV1` all use the interpreter, and a node started with call tracing also executes its blocks with the interpreter (`main.cpp` lines 484-488 at v0.16.7). Every receipt, log and trace a public Monad endpoint serves is therefore interpreter output (F-130, operator level, information). 629,293 mined v4 swaps and 53,532 swaps of v3 style pools were checked in blocks 124,719,001 to 125,119,000. 612,273 v4 swaps match one step to the unit, 129,567 of them through the 512 bit branch of `FullMath.mulDiv`, and a replay of the whole swap loop over the newest 40,000 blocks leaves 0 of 53,503 unmatched. Five v3 swaps of other protocols remain unexplained and were not replayed. A planted `MULMOD` fault is caught for even denominators; for odd denominators the high word drops out of `mulDiv`, so such a fault could not change an amount there. Whether the PoolManager is compiled still needs a build of the emitter. |
| Producer operands on Monad, MegaETH, HyperEVM | Mined swaps of v3 style pools go through the 512 bit branch and match the exact formulas: 2,816 on Monad, 3,741 on MegaETH, 493 on HyperEVM. All 324 HyperEVM swaps that need the whole loop replay with pool keys read from the 350 `Initialize` events of the PoolManager's full history. Two Monad swaps that end exactly on an initialized tick replay exactly. Full-history log scans show that `donate`, `approve`, `transferFrom` and operator burns have never been called on the MegaETH or HyperEVM PoolManager, so mined evidence for those branches cannot exist yet. The PoolManager's own 512 bit copy of `mulDiv` in the fee calculation (program counter 22358) always ends in the `SafeCast` revert at `Pool.sol:192` on a correct node. |
| reth execution cache | The fault that Arc fixed is still in the reth code that OP Mainnet's versioned build, Base, Zora, World Chain, Celo, X Layer and reth-bsc pin. It applies only to an account that had no code at the start of a block and that the block destroyed and created again. The PoolManager, and any token, hook or router a pool already uses, have code, so none of their storage can go stale. Only the block builders of Base and Celo read through this cache, and only with a flag that is off by default (F-132, operator level, low, plausible). Elsewhere the fault could stall follower nodes (F-133, low, plausible). Both hang on one unproven link: a read that puts a storage word of a codeless address into the cache first. Ethereum, Unichain, Ink, Soneium, Tempo and Arc have the fix. Between op-reth v2.10.0-rc.1 and rc.4 the engine, cache, prewarm and state root code is identical. |
| Proof program images | The kona image that OP Mainnet, Unichain and Ink respect was scanned again with a control flow graph: on every path the value in question is only tested against zero or shifted down to 0 or 1, never used as a number, so the LLVM fault does not reach it. The image's own `SHL`, `SHR` and `SAR` handlers, run in the Cannon emulator, return the specified word on 92,871 vectors (F-131, information). Arbitrum One, Robinhood Chain and Elysium enforce the consensus-v61 machine, which pins go-ethereum f1c5f02; its jump analysis is identical to the commit read before, and its arithmetic, memory and transient storage code gives the same results. Base's proof toolchain lowers 128 bit shifts correctly. The published Base program image could not be obtained. |
| HyperEVM | 185,529 vectors and 550 scripts match, with the one gas-limited script as before, on the official node and the archive client. Twelve new vectors with nonzero high limbs in shift counts, `BYTE` indexes and `SIGNEXTEND` sizes match. The public replay clients and the validator supervisor binary are unchanged since cycle 10. F-020 stays plausible at operator level. |
| Arbitrum One, Robinhood Chain, Elysium | All reruns match. 21,712 new vectors for the reduction and division routines of the integer library match, and a planted fault is caught. The unpublished Nitro build keys its jump destination cache by code: one address given code with and without a `JUMPDEST` at the same offset in successive simulated blocks jumps, fails and jumps again. Nitro's Stylus and JIT compilers use a Cranelift release inside the range of two October 2026 miscompile advisories. The PoolManager is EVM bytecode and never passes through them, and new Stylus programs cannot be activated on any of the three chains (F-128, governance level, information). |
| Ethereum | 185,529 vectors and the first script set match on three clients: reth v2.11.0, geth v1.16.7 and reth v2.10.0. 30,321 new mined swaps match. The released reth binary carries an LLVM compiler for EVM code that builds and validates blocks when a node's operator turns it on, and no simulated call uses it (F-129, operator level, information). The opcodes the next Ethereum fork defines do not occur in the PoolManager's bytecode. |

The critic's first question after the cycle was read directly: do Monad's RPC nodes, which interpret, check their results against the validators, who may run compiled code? They do. A proposal for block N carries the full header of block N-3 as the proposer executed it: state root, receipts root, logs bloom and gas used. Every node compares that header with the one its own execution wrote, and a block that fails the comparison is never committed (`monad-eth-block-policy/src/lib.rs` lines 1182-1196, `monad-blocktree/src/blocktree.rs` lines 280-308 and 369, `monad-consensus-state/src/lib.rs` lines 1459-1467, at monad-bft v0.16.7). A node outside the validator set runs the same code with its votes filtered out. So an RPC node at the chain tip has matched the validator quorum on every block. If validators run compiled code, it has agreed with the interpreter on every mined transaction, receipts and gas included. What remains without evidence is input no mined transaction has used.

Tempo's release binary does not contain the compiler that reth v2.11 ships: the feature is on by default only for the reth binary itself, and Tempo's own switch for it is off in release builds.

## What this does not cover

What is still open after cycle 14:

- Inputs no mined transaction has used on Monad, MegaETH and HyperEVM. Monad's validators may run compiled code and the other two producers are closed, and for these branches the only evidence is the interpreter and reading: `clear` of an exact credit, `transferFrom`, burns through an allowance or an operator, `approve`, `donate`, the overflow fallback of `getNextSqrtPriceFromAmount0RoundingUp`, and amounts above 2^160.
- Whether Monad compiles the PoolManager at all. That needs a build of the emitter to compare its size estimate with the 778,528 byte bound.
- HyperEVM's validator. It is closed, its EVM library versions are unknown, and it has 493 mined swaps through the 512 bit branch against thousands on the other two networks.
- Compilers that exist and are switched off: the LLVM compiler in reth (Ethereum, off unless an operator enables it) and in evm2 (Tempo, not built into releases). Their code for `MULMOD`, signed division, shifts and `SIGNEXTEND` has not been read.
- The reth execution cache fault on Base and Celo block builders and on follower nodes of seven networks. It cannot reach the PoolManager's storage or that of contracts a pool already uses; whether it can be triggered at all is unproven. MegaETH's reth fork is not public enough to tell.
- Two scheduled forks inside the deployment window: Tempo T14 and BNB Chain Jenner, both on 8 December 2026. The checks have to be rerun after each. Tempo's later T15 fork lets the token precompile call a portal contract during a transfer and has not been walked through. The next upgrades of the OP Stack chains, Arc, Avalanche and Polygon have not been read.
- Celo's endpoint mixes two clients. One is an op-geth build no cycle has tied to a source commit.
- Arc's three public endpoints report three builds and the checks ran on one.
- Proof programs as published for Base, Celo and X Layer. Base's was tested as a rebuild from source.
- The Nitro release that Arbitrum One and Robinhood Chain report is private. The machine that settles their disputes was read; the node build was tested through its answers.
- The MegaETH stateless validator, which checks the sequencer's state commitment, was not run.
- BNB Chain's unpublished commit and the unreleased bor v2.12, both read only through their answers or their beta text.
- The repository's own test suite, which needs `forge`. It is not installed here.
- Other validators' hardware and builds. Every result describes the node behind the endpoint that was asked, and on Monad, by the check above, the validator quorum as well.

## How to run it again

```bash
python3 research/network-risk/tools/opdiff/v4math.py
```

```bash
python3 research/network-risk/tools/opdiff/statekeys.py research/network-risk/opcodes/statekeys.json
```

```bash
python3 research/network-risk/tools/opdiff/callsem.py research/network-risk/opcodes/callsem.json
```

```bash
PM_FROM=130 python3 research/network-risk/tools/opdiff/pmdiff.py /tmp/unichain-pmdiff.json 250 130
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
python3 research/network-risk/tools/opdiff/trace.py research/network-risk/opcodes/trace-ink.json 60 https://rpc-qnd.inkonchain.com
```

```bash
python3 research/network-risk/tools/opdiff/trace.py research/network-risk/opcodes/trace3-hyperevm-nanoreth.json 80 https://rpc.purroofgroup.com 3
# set 6 on the build of this checkout, all 706 scripts
PM_BUILD=research/network-risk/build/PoolManager.json python3 research/network-risk/tools/opdiff/trace.py research/network-risk/opcodes/trace6-tempo.json 706 https://rpc.mainnet.tempo.xyz 6
```

```bash
python3 research/network-risk/tools/opdiff/avaxslots.py research/network-risk/opcodes/avalanche-slot-constants.json research/network-risk/cycles/005/theme-shared-hooks.work/raw/init_43114.json.gz
```

```bash
PM_BUILD=research/network-risk/build/PoolManager.json python3 research/network-risk/tools/opdiff/pmdiff3.py research/network-risk/opcodes/build-pmdiff3.json 300
```

```bash
PM_BUILD=research/network-risk/build/PoolManager.json python3 research/network-risk/tools/opdiff/pmdiff4.py research/network-risk/opcodes/build-pmdiff4.json 300
```

```bash
PM_BUILD=research/network-risk/build/PoolManager.json python3 research/network-risk/tools/opdiff/pmdiff5.py research/network-risk/opcodes/build-pmdiff5.json
# sixth script set (cycle 12): the sides of conditional jumps that sets 1 to 5 never took, on all 21 networks
python3 research/network-risk/tools/opdiff/pmdiff6.py research/network-risk/opcodes/pmdiff6.json
# every mined swap in a window through the whole Pool.swap loop, from parent-block state (cycle 13); first argument is the chain id
python3 research/network-risk/cycles/013/theme-swap-residuals.work/replay2.py 1 /tmp/replay2-1.json --want 3000
```

```bash
PM_BUILD=research/network-risk/build/PoolManager.json python3 research/network-risk/tools/opdiff/coverage.py research/network-risk/opcodes/build-pmdiff3-coverage.json,research/network-risk/opcodes/build-pmdiff4-coverage.json,research/network-risk/opcodes/build-pmdiff5-coverage.json research/network-risk/opcodes/coverage.json
```

With `PM_BUILD` set, every script runs the built bytecode instead of the deployed one.

Each takes a list of chain ids as further arguments to run on some networks only. The battery and the scripts use fixed seeds, so a rerun after a network upgrade tests the same inputs. A rerun is worth doing after every client release on the single-client networks (Monad, MegaETH, Tempo, HyperEVM, Arc, Robinhood Chain, Elysium) and after any ruint, revm or evm2 upgrade.
