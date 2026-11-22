# What this PoolManager assumes about the chain it runs on

Every item is something the code in `src/` relies on the network to provide. A network that breaks one of them is a candidate for frozen or siphoned pool funds. Line numbers refer to this repository. Read the code as it is here; do not compare it with any other copy of v4-core.

## Threat model

The attacker is an ordinary account with no special role: it can deploy contracts, tokens and hooks, create pools, and send any transaction the network accepts from the public. The victims are ordinary users of pools: liquidity providers, swappers and holders of ERC-6909 claims. Actions that need the PoolManager owner, the protocol fee controller, a token issuer's admin keys, a sequencer, a validator set or chain governance are out of scope and are recorded only for reference.

The build targets `evm_version = cancun`, solc 0.8.26, `via_ir`, `optimizer_runs = 44444444`, `bytecode_hash = none` (`foundry.toml`). The contract deployed on the 21 networks is 24,009 bytes (24,050 on Unichain), against the 24,576 byte EIP-170 limit.

## A1. Transient storage lives for exactly one transaction

`Lock.sol:13-25`, `CurrencyDelta.sol:21-39`, `CurrencyReserves.sol:17-36` and `NonzeroDeltaCount.sol:14-32` keep the unlock flag, every caller's currency deltas, the synced currency and the synced reserves in transient storage (`TSTORE`/`TLOAD`). The code never clears the synced currency on its own unless `settle` runs, and it trusts the EVM to wipe everything at the end of the transaction and to roll it back on revert. A chain where the wipe boundary is something other than one user transaction (protocol-level batches, bundled or system transactions, account-abstraction frames, parallel execution with speculative state) can leak an unlock flag, a delta, or a stale `sync` into someone else's execution.

## A2. Token balances change only through transfers

`sync(currency)` records `balanceOf(PoolManager)` (`PoolManager.sol:279-288`). `_settle` later credits the caller with `balanceOf(PoolManager) - syncedReserves` (`PoolManager.sol:349-364`). Whatever raises the PoolManager's balance between those two calls is treated as a payment by the settler: a rebase, an airdrop, a protocol-level mint, a fee refund credited by the chain, a bridge or system contract that moves balances outside normal execution. Whatever lowers the balance without a `take` leaves pools undercollateralised.

## A3. The native asset is `address(0)`, moves only by value transfer, and has no second face

Native payments are `msg.value` (`PoolManager.sol:352-354`). Native payouts are `call(gas(), to, amount, 0, 0, 0, 0)` (`Currency.sol:48`). The native balance is `address(this).balance` (`Currency.sol:92`). The code assumes that the native asset cannot also be reached as an ERC-20 at some address (one balance, two currencies, so pools `address(0)/X` and `token/X` draw on the same funds), that native value transfers cannot be blocked for particular senders or recipients, that `msg.value` and `balance` use the same unit, and that the chain has a native asset at all. The only guard is `NonzeroNativeValue` at `PoolManager.sol:356`, which rejects `msg.value` when an ERC-20 is synced. `src/test/NativeERC20.sol` models a native asset with an ERC-20 face.

## A4. ERC-20 calls behave like calls to ordinary contracts

`Currency.sol:60-75` calls `transfer(address,uint256)` and accepts either empty return data or a 32 byte `true`. There is no code-size check: a call to an address with no code returns success with empty return data, so a `take` of a currency that has no code "succeeds" and moves nothing. `Currency.sol:94` calls `balanceOf`. Tokens implemented as precompiles, tokens whose code can appear or disappear, and tokens with transfer policies enforced by the chain all sit outside what this code was written for.

## A5. Everything the PoolManager holds can be borrowed for free inside one transaction

`take` (`PoolManager.sol:291-297`) pays out before anything is paid in. The only requirement is that deltas net to zero when `unlock` returns (`PoolManager.sol:104-114`). On a chain where holding a balance for part of one transaction has value (paying gas in that token, voting, staking, collateral in a system contract, balance-based precompile reads), every pooled token is available to anyone for that purpose.

## A6. One address holds the funds of every pool

All pools, all ERC-6909 claims and all accrued protocol fees for a currency sit in one balance at the PoolManager address. A freeze, blocklist entry, seizure or transfer policy applied to that one address for one currency stops every pool that uses the currency.

## A7. Code at a hook address stays what it was

Hook permissions are the low 14 bits of the hook address (`Hooks.sol:27`, `Hooks.sol:109-124`). Hooks are called with all remaining gas (`Hooks.sol:134`) and their return data is parsed (`Hooks.sol:140-160`, `Hooks.sol:256-320`). The model assumes CREATE2 address derivation as on Ethereum, that code at an address does not change after pool creation (SELFDESTRUCT rules, EIP-7702 delegated accounts, chain-specific upgradeable or WASM contracts), and the 63/64 gas forwarding rule.

## A8. `address(this)` identifies the contract

`NoDelegateCall.sol:19-25` compares `address(this)` with an immutable. ERC-6909 and all delta accounting key on `msg.sender` (`PoolManager.sol:110`, `294`, `301`, `326`, `334`). Address aliasing for cross-domain messages, system callers and privileged transaction types change who `msg.sender` is.

## A9. Gas limits leave room for the worst swap

`Pool.swap` loops over initialized ticks until the price limit or the amount is reached. `modifyLiquidity` touches two ticks and the bitmap. A per-block or per-transaction gas cap far below Ethereum's, a different storage price, or gas charged on the limit instead of on use can make large swaps or liquidity removal impossible to include, which freezes funds without any bug in the code.

## A10. Opcodes used by the bytecode exist and cost roughly what they cost on Ethereum

The bytecode uses `PUSH0`, `MCOPY`, `TLOAD`, `TSTORE`, `SELFBALANCE`, `RETURNDATACOPY`, `STATICCALL` and `CALL` with value. It does not use `SELFDESTRUCT`, `BLOCKHASH`, `TIMESTAMP`, `NUMBER`, `PREVRANDAO`, `COINBASE`, `BASEFEE`, `CHAINID` or `CREATE`. Core has no dependence on block time or block number.

## A11. Raw storage reads are harmless

`Extsload.sol` and `Exttload.sol` expose every persistent and transient slot to any caller.

## A12. The owner and the protocol fee controller are who Uniswap governance says they are

`ProtocolFees.sol:29-57`: the owner sets the controller; the controller sets protocol fees (capped at 0.1% per direction) and withdraws accrued fees to any recipient. `collectProtocolFees` reverts when the currency is an ERC-20 that is currently synced, whatever the lock state (`ProtocolFees.sol:44-56`); `_isUnlocked` is declared but never called. On several chains the owner is `0x2BAD8182C09F50c8318d769245beA52C32Be46CD`, the L1-to-L2 alias of the Ethereum timelock `0x1a9C8182C09F50C8318d769245beA52c32BE35BC`, an address with no code that can only act through the chain's cross-domain message path. Who can produce a call from that address is a property of the chain.

## A13. The same address on another chain is the same contract

Four networks share PoolManager address `0x360e68fa…fb32` and two share `0x8366a39c…0951`. Unichain's PoolManager is a genesis predeploy at `0x1f98400000000000000000000000000000000004` with different bytecode. Integrations that hardcode an address or assume CREATE2 parity across chains inherit that assumption.

## A14. Blocks do not get rewritten after funds leave

Settlement is atomic inside a transaction, so core is indifferent to ordering. Reorg depth, sequencer equivocation and preconfirmation schemes matter where pool funds meet bridges and fast withdrawals.

## What an ordinary caller can make the PoolManager do

These are the levers an unprivileged account has. For each network the question is what the chain's special addresses (precompiles, predeploys, system contracts, faces of the native asset, wrapped native, bridges, staking and fee contracts) do when the PoolManager is the `msg.sender` of these calls, and whether any combination moves value that belongs to pools without an equal debit to the caller.

- P1, native take. `take(address(0), to, amount)` makes the PoolManager execute `CALL(to, value = amount, empty calldata)` with all gas (`PoolManager.sol:291-297`, `Currency.sol:44-52`). The caller is debited `amount` of currency `address(0)`. With `amount = 0` nothing is owed and the PoolManager still calls `to` with empty calldata.
- P2, token take. `take(X, to, amount)` makes the PoolManager call `X.transfer(to, amount)` for any address `X` the caller names (`Currency.sol:53-80`). The call counts as successful when it does not revert and returns nothing or a 32 byte `true`. The caller is debited `amount` of currency id `X`. With `amount = 0` nothing is owed. `amount` is capped at `type(int128).max` by the cast at `PoolManager.sol:294`.
- P3, sync. `sync(X)` makes the PoolManager staticcall `X.balanceOf(PoolManager)` for any `X` and stores the result in transient storage. It needs no unlock and no permission (`PoolManager.sol:279-288`).
- P4, settle. `settle` and `settleFor` credit `msg.value` when no currency is synced, or the rise in `X.balanceOf(PoolManager)` since `sync(X)` (`PoolManager.sol:349-364`).
- P5, hook calls. `initialize` accepts any address as the hook when its low 14 bits form a valid flag combination (`Hooks.sol:109-124`). The PoolManager then calls that address with the `IHooks` selectors and caller-supplied arguments, including arbitrary `hookData`, and accepts the call when the return data is at least 32 bytes and starts with the same selector (`Hooks.sol:131-160`). `swap`, `modifyLiquidity` and `donate` do the same for their hooks.
- P6, claims. `mint` and `burn` move ERC-6909 claims whose id is `uint160(currency)` for any address (`PoolManager.sol:322-336`).
- P7, callback. `unlock` calls `unlockCallback` on the caller itself (`PoolManager.sol:104-114`).
- P8, reads. `extsload` and `exttload` return any slot.
