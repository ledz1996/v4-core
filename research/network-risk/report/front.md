# PoolManager network risk report

State on 2026-11-22: cycle 1 is merged and cycle 2 is running. The ledger holds 34 findings, 158 checks that came out safe, and 133 open leads across the 21 networks.

## The question

Can an ordinary account take funds that other users hold in this repository's PoolManager, or stop them from withdrawing, on any of the 21 networks where Uniswap v4 is officially deployed? The attacker has no role: no owner or fee controller key, no token admin key, no sequencer or validator power, no governance vote. The victims are liquidity providers, swappers and holders of ERC-6909 claims who use pools in the normal way.

## Answer so far

Cycle 1 found no such path. The planted weakness has not been identified yet.

Seven findings can be triggered by an ordinary account, and none of them moves or locks another user's funds in a pool that uses ordinary tokens and no hook. In three the loss falls on whoever makes an unusual call: a payout sent to a HyperCore bridge address (F-021), POL paid into the Polygon system token at `0x1010` (F-008), and a payout to a Tempo account whose receive policy rejects the PoolManager (F-033). One is a pricing trap, a Celo predeploy that names itself WETH and wraps CELO (F-025). One strands staking yield on rebasing stETH without touching principal (F-012). Two record places where the source disagrees with its own comments or tests and no funds move (F-006, F-014).

The other 27 findings need a party the threat model excludes. The largest group is the same hazard on many networks: every pool of a currency shares one balance at one address, so a stablecoin issuer who blocklists the PoolManager stops all of them.

## What cycle 1 tested

One balance under two currency ids. On Arc the native asset is USDC with 18 decimals and the same balance is an ERC-20 with 6 decimals. Celo exposes native CELO through the CELO token, Polygon exposes POL through `0x1010`, and Optimism and Zora list a legacy token that mirrors ETH. In each case the researchers walked `sync`, `settle` and `take` across both faces in every order and found no double credit. A native credit needs `settle` with value while no token is synced, and `settle` rejects value while a token is synced (`src/PoolManager.sol:353-356`). On Arc the 12 digit truncation in `balanceOf` gives at most one millionth of a dollar per call, far below the gas cost.

A chain without a native asset. Tempo has none. `CALLVALUE` is always 0 and the client rejects value transfers, so the native branch of `settle` always credits 0.

Transient storage across transaction boundaries. Tempo batch transactions, Arc's Multicall3From, ERC-4337 and World Chain bundles, OP Stack deposits and Flashblocks, Nitro retryables, Monad's parallel execution, and the system transactions on Polygon, BNB Smart Chain and HyperEVM were each checked for an unlock flag, a delta or a stale `sync` reaching another party. No case moves funds. Where two users share one transaction, the earlier one can make the later one's native `settle` revert.

The PoolManager as caller. `take` lets anyone make the PoolManager call any address with `transfer(address,uint256)` or with empty calldata, and `initialize` lets anyone name any address as a hook. On Tempo and Arc every precompile was called this way from the PoolManager address and all of them revert except real tokens. HyperEVM's CoreWriter cannot be reached with these selectors. This sweep was not complete on the other networks, which is the first job of cycle 2.

Gas limits. HyperEVM's 3,000,000 gas blocks, Tempo's 250,000 gas per new storage slot, and the per-transaction caps on Ethereum, Monad, BNB Smart Chain and MegaETH leave room for liquidity removal, and a large swap can be split with a price limit.

The source itself. Two readers went through `src/` line by line. They recomputed the transient slot constants, the TickMath and BitMath tables and the packing masks, checked the sign and rounding of every delta, and ran a Python transcription of the pool math through random sequences of adds, removals, swaps and donations. They found one way to lock a position, which needs a token with more than 1.7e38 base units of supply (F-005), and the fact that a pool's own hook can block removals from that pool (F-004). Both depend on a token or hook that the victims chose.

## What is open

Cycle 2 repeats the work under the narrowed threat model. Each network family sweeps every precompile, predeploy and system contract with the PoolManager as caller, compares opcode behaviour against the node's source, re-walks the faces of the native asset, and collects known weaknesses of the network. Four more readings of the source run alongside: a swap trace, a liquidity trace, an attempt to break the custody invariants, and a check of every mask, shift and cast.

The cycle 1 critic and verifiers left these leads at high priority:

- Read in client source where Arc, Avalanche, HyperEVM, X Layer and World Chain discard transient storage between two transactions of one block. Cycle 1 relied on documentation for those five.
- Find out which functions of Base's B20 token precompile and policy registry an account with no role can call, and whether any of them changes another holder's balance.
- Replay the concrete expectations in the repository's tests against the source by hand, since no compiler is installed here.
- A verifier reports a Yul optimizer bug announced by the Solidity team on 2026-10-22 and asks whether it affects this build (solc 0.8.26 with `via_ir`). Nobody has checked this yet.
- On five OP Stack chains the protocol fee controller is the zero address, and OP upgrade deposits are sent from the zero address. That path needs the chain operator and reaches protocol fees only, but the cycle 1 clearance of "nobody can call as the zero address" was wrong for those chains.

Two limits apply to everything above. No compiler is available in this environment, so nothing was built or executed, and deployed bytecode was not compared with a build of this repository. The chain facts were read from the live official deployments, which may differ from what the CTF build will be when it is deployed.
