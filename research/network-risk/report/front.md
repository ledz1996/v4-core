# PoolManager network risk report

State on 2026-11-22: cycles 1 and 2 are merged. The ledger holds 52 findings, 332 checks that came out safe, and 200 open leads across the 21 networks. Forty-six agents have worked on it so far, half of them as independent verifiers.

## The question

Can an ordinary account take funds that other users hold in this repository's PoolManager, or stop them from withdrawing, on any of the 21 networks where Uniswap v4 is officially deployed? The attacker has no role: no owner or fee controller key, no token admin key, no sequencer or validator power, no governance vote. The victims are liquidity providers, swappers and holders of ERC-6909 claims who use pools in the normal way.

## Answer so far

No critical or high finding exists for an ordinary attacker. The planted weakness has not been identified. Every verifier in cycle 2 was asked whether its unit contained it, and each answered no.

Seventeen findings can be triggered by an ordinary account. They fall into five groups.

Rebase capture, the only one where an attacker gains (F-041, medium, confirmed on Ethereum). Any account can call `sync`, cause the PoolManager's balance of a token to rise, and call `settle` to be credited the rise. Taking the pooled balance first and repaying the nominal amount works as well. For Ampleforth the public rebase is guarded by `msg.sender == tx.origin`, and an EIP-7702 delegated account passes that check while running code; the verifier simulated this on mainnet. The gain is the positive rebase on whatever the PoolManager holds of that token. Today that is 16 base units of AMPL, and the method reaches only pools in elastic or reward-pushing tokens.

Yield that nobody can withdraw (F-012 stETH on Ethereum, F-037 Aave aTokens on Arbitrum One). The balance grows outside pool accounting and core has no function that pays the growth out. Principal is untouched.

Payouts to a recipient that swallows them. On every network family some address accepts a payout from the PoolManager and books it to the PoolManager itself, or holds it: HyperCore bridge addresses and the L1 block number precompile on HyperEVM (F-021), `L2ToL1MessagePasser`, the ERC-4337 EntryPoints and `L1BlockNumber` on the seven OP Stack chains (F-048), withdrawal predeploys, fee vaults and Celo core contracts on Celo and X Layer (F-047), EntryPoints, precompiles and custody addresses on Arc and Tempo (F-049), and Tempo accounts whose receive policy rejects the PoolManager (F-033). The caller is debited in full each time, so the only loser is the caller, or the user of a router that passes a recipient through unchecked.

Currency ids that take credit and cannot pay out: Polygon's system token at `0x1010` (F-008) and the USDC implementation address on Arc (F-050). Only someone who pays into such an id loses. The Celo predeploy that names itself WETH and wraps CELO (F-025) is a pricing trap of the same kind.

Delay without loss. One cheap transaction on MegaETH uses a block's whole budget for new state and the node skips the rest of that block (F-042). A HyperEVM small block holds 3,000,000 gas, which fits about 200 tick crossings in one swap (F-039). A HyperCore transfer runs a linked contract ahead of every signed transaction in the block (F-044). Any account can fill one tick to the liquidity cap for dust and block later deposits on that tick, on every network (F-038). Withdrawals keep working in all four.

The remaining two (F-006, F-014) record places where the source disagrees with its own comments, with no funds involved.

The other 35 findings need a party the threat model excludes: a token issuer, a chain operator, governance, or the author of a hook or token that the victims chose. They are listed near the end.

## What has been tested

One balance under two currency ids. Arc (native USDC with 18 decimals and an ERC-20 face with 6), Celo (CELO token), Polygon (`0x1010`), the legacy ETH token on Optimism and Zora, and stHYPE with wstHYPE on HyperEVM, which share one share balance. In each case `sync`, `settle` and `take` were walked across both faces in every order, twice by network researchers and once in a Python model of the settlement code. No order credits one deposit twice. A native credit needs `settle` with value while no token is synced, `settle` rejects value while a token is synced (`src/PoolManager.sol:353-356`), and only one currency can be synced at a time. On Arc the 12 digit truncation gives at most 0.000001 USDC per round against a 20 gwei minimum base fee.

The PoolManager as caller of special addresses. `take` lets anyone make the PoolManager call any address with `transfer(address,uint256)` or with empty calldata, and `initialize` lets anyone name any address as a hook. Cycle 2 ran these call shapes from the PoolManager address against every precompile, predeploy and system contract the researchers could list: all 2,048 predeploy slots on each of the seven OP Stack chains, 122 special addresses on Polygon, BNB Smart Chain and Avalanche, and the full precompile sets of Tempo, Arc, Monad, MegaETH, HyperEVM and the Arbitrum family. Where a call succeeds, the caller owes the full amount, which is the payout-stranding group above.

Opcodes. A verifier deployed nothing and used `eth_call` with init code to run 60 arithmetic, shift, hash, transient storage, `MCOPY` and `PUSH0` vectors on each of the 21 networks, and a second verifier repeated it in cycle 2. All agree with Ethereum. Avalanche differs in one place: the C-Chain clears bit 248 of every storage slot index, so two indexes map to one slot (F-040). The PoolManager writes only to slots 0 to 6 and to hash outputs, so core is unaffected; a hook with hand-picked slots is not.

Transient storage across transactions. Read in client source for the OP Stack (op-revm, Base), Bor, BSC, AvalancheGo, Nitro, X Layer and Arc, and tested with `eth_simulateV1` on six OP Stack chains, Polygon and BNB Smart Chain. A second transaction always starts with an empty map. Batch transactions on Tempo and helper contracts on Arc share transient storage only among one sender's own calls.

A chain without a native asset. On Tempo `CALLVALUE` is always 0 and value transfers are rejected, so the native branch of `settle` credits 0.

The source itself. Six readings so far: two line by line, a swap trace, a liquidity trace, an attempt to break the custody invariants with a search over call sequences, and a check of every mask, shift, cast and `unchecked` block. Three independent Python transcriptions of the pool math stayed solvent across about 27,000 random operation sequences. The slot constants, error selectors, TickMath and BitMath tables were recomputed from the text.

## What is open

Three high-priority leads from the cycle 2 critic head the queue.

- A nested execution context with its own transient storage. `sync` needs no lock. If any network can run caller-chosen code inside a transaction under a fresh transient map while keeping its token transfers, one payment could be credited twice. Candidates named for checking: Tempo zones and the T14 account type due on 8 December 2026, Base transactions of type 0x79, Stylus host calls and retryable redeems, HyperEVM system calls with data, World Chain bundles, and Celo's fee currency calls. MegaETH's keyless deploy sandbox was checked and is safe.
- A call that carries value without a matching balance debit. `settle` credits `msg.value` as paid. go-ethereum and BNB Smart Chain skip the balance check for the system caller address; whether anything an ordinary account sends can run with that caller is unchecked.
- The repository's own tests, comments and test doubles that no reader has yet replayed against `src/`.

Two limits apply to everything above. No compiler is installed here, so nothing was built, and one question depends on that: the Solidity team's bug list marks solc 0.8.26, which `foundry.toml` pins, as affected by a Yul optimizer bug published on 22 October 2026, and the readers found none of its source patterns but could not inspect the optimized output. Second, the chain facts were read from the live official deployments, which may differ from the CTF build once it is deployed.
