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

## Findings an ordinary account can trigger

### F-012. Rebasing stETH held by the PoolManager gains and loses balance outside pool accounting

Medium severity, confirmed. Effect: degrade. Who can trigger it: any account. Networks: Ethereum.

What differs on the network: stETH balances are recalculated on each Lido oracle report, normally daily, with no transfer. The change is positive on staking rewards and can be negative after slashing or penalties. Lido's integration guide lists Uniswap among applications that are not designed for rebasing tokens and recommends wstETH.

How it meets the code: Pool accounting never reads token balances. Balances are read only in sync and in _settle, and the only credit from a balance is the increase between a sync and the settle that follows in the same transaction (src/PoolManager.sol:279-288, 349-364). A positive rebase raises balanceOf(PoolManager) with no sync and settle around it, so the increase belongs to no pool, no position and no claim. The only outflows are take and collectProtocolFees (src/PoolManager.sol:291-297, src/ProtocolFees.sol:44-57), and both debit an accounted amount, so the surplus cannot be paid out to LPs. Someone who can run sync, the rebase and settle inside one transaction would be credited the whole rebase on the PoolManager's balance. For stETH the rebase happens inside submitReportData, which only an oracle committee member or a SUBMIT_DATA_ROLE holder can call. A negative rebase lowers the balance below the sum of pool and claim accounting, and the last withdrawals of stETH revert in Currency.transfer. Transfer rounding is safe for the PoolManager: a take debits the full amount while stETH moves at most that amount, and settle credits what arrived.

What is at risk: The PoolManager holds 80.4539 stETH at block 26470360. LPs in stETH pools earn no staking yield on it; the yield accumulates as an unclaimable surplus. After a negative rebase the shortfall falls on whoever withdraws stETH last. wstETH (2,295 held) is not affected because its balances do not rebase.

What it takes: A pool must use stETH or another elastic supply token as a currency. The loss case needs a negative Lido report. Capturing the positive rebase needs an oracle committee member acting through a contract or an EIP-7702 delegated account. I derived the rounding argument from the share formula in the Lido guide and did not test it on chain. I did not compute how much of the 80.4539 stETH is surplus.

What can be done: Use wstETH in pools. Interfaces can warn on pools whose currency is stETH or another rebasing token. A hook cannot fix this because the surplus is not reachable through any delta.

Second reviewer's corrections: I raise the severity from low to medium. Low is for hazards with no direct loss path. Here the staking yield on stETH held by the PoolManager is stranded for good, the increase is visible on chain, and the loss is limited to stETH pools and claims, which is the medium definition. The effect is closer to a permanent freeze of the yield than to degrade. The principal shortfall case needs a negative report, which the Lido guide says had not happened when it was written. The same sync, trigger, settle sequence applies to any token whose balance at the PoolManager a third party can raise inside one transaction, which is recorded as a lead.

Code: `src/PoolManager.sol:279-288`, `src/PoolManager.sol:349-364`, `src/PoolManager.sol:291-297`, `src/ProtocolFees.sol:44-57`.

Sources:

- https://raw.githubusercontent.com/lidofinance/docs/main/docs/guides/lido-tokens-integration-guide.md (stETH rebases daily on the oracle report, rebases can be negative, transfers can move 1 to 2 wei less than requested, and Uniswap is named as not designed for rebasing tokens)
- https://raw.githubusercontent.com/lidofinance/docs/main/docs/contracts/accounting-oracle.md (submitReportData reverts with SenderNotAllowed unless the caller holds SUBMIT_DATA_ROLE or is a consensus member, and the rebase is applied within that transaction)
- https://ethereum-rpc.publicnode.com (eth_call at blocks 26470360 and 26470380: stETH.balanceOf(PoolManager) = 80453883612211151739 and sharesOf = 64372946869317648418; wstETH.balanceOf = 2295.05; AMPL.balanceOf = 16 base units)
- https://raw.githubusercontent.com/ampleforth/ampleforth-contracts/master/contracts/Orchestrator.sol (Ampleforth Orchestrator.rebase() in the project repository requires msg.sender == tx.origin, a check that EIP-7702 delegated accounts can satisfy while running code; I did not confirm that the deployed orchestrator matches this file, and the PoolManager holds only dust AMPL)

### F-033. A take to a recipient whose receive policy rejects the PoolManager succeeds and strands the funds in ReceivePolicyGuard

Medium severity, confirmed. Effect: freeze. Who can trigger it: any account. Networks: Tempo.

What differs on the network: Since T6 any Tempo account can set a receive policy in the TIP-403 registry: a sender list, a token filter and a recovery authority. When a TIP-20 transfer fails the recipient's receive policy, the transfer does not revert. The token credits ReceivePolicyGuard at 0xB10C000000000000000000000000000000000000, records a receipt and returns true. Only the recovery authority captured in the receipt can claim the amount. With recovery authority address(0) the claimer is the originator, which is the from address of the transfer. An ERC-20 transfer on Ethereum either credits the recipient or reverts.

How it meets the code: 1. A user or a router calls take(currency, to, amount) (src/PoolManager.sol:291-297). The caller's delta is debited and the PoolManager calls transfer(to, amount) on the TIP-20 (src/types/Currency.sol:60-75). 2. The recipient to has a receive policy that rejects the PoolManager as sender, or filters out the token. The TIP-20 precompile moves the amount from the PoolManager to ReceivePolicyGuard with the PoolManager as originator and returns true. 3. The return value is 32 bytes of 1, so the success test at src/types/Currency.sol:64-74 passes and take completes. The recipient's balance is unchanged. 4. If the recipient's recovery authority is its own address or a third party, that party can claim. If it is address(0), only the originator can claim. The originator is the PoolManager, which has no function that calls the guard, so the receipt can never be claimed. 5. PoolManager accounting stays consistent, because the delta was debited and the balance fell by the same amount. The loss is the withdrawing party's.

What is at risk: The amount of each affected take is lost for good when the recipient's recovery authority is address(0), and delayed until a claim otherwise. This hits LP withdrawals and swap outputs sent to accounts that restrict senders, for example custodial deposit accounts with a sender whitelist. Pool reserves and other users are not affected.

What it takes: The recipient must have set a receive policy that rejects the PoolManager address or the token, and must have chosen address(0) as recovery authority for the loss to be permanent. The party that names the recipient in take must not check the policy first. An attacker cannot set a policy for someone else. receivePolicy(PoolManager) is unset on chain, and the PoolManager cannot set one, so payments into the PoolManager are not redirected.

What can be done: Routers and interfaces on Tempo should call validateReceivePolicy(token, PoolManager, recipient) before a take and refuse or warn when it would block. Account owners who use sender whitelists should add the PoolManager address or set themselves as recovery authority. The deployer can document that withdrawals originate from the PoolManager address.

Second reviewer's corrections: The mechanism holds as written. Two points on reach. First, both accounts that reject all senders today name themselves as recovery authority, so they could claim a redirected amount. Three accounts have chosen address(0) as recovery authority, and all three currently allow every sender and every token. I found no account that is in the permanent loss configuration today. Second, a router that takes to itself and then forwards becomes the originator, and a router has no claim function either. The Universal Router and PositionManager on Tempo were not read. The severity stays medium. No third party can trigger the loss, pool reserves are not in reach, and the amount is limited to takes sent to accounts that set such a policy.

Code: `src/PoolManager.sol:291-297`, `src/types/Currency.sol:60-75`.

Sources:

- https://tempo.com/developers/docs/protocol/tip403/receive-policies.md (a blocked inbound transfer still succeeds, delivery goes to ReceivePolicyGuard, recovery authority table)
- https://tempo.com/developers/docs/protocol/tip403/spec.md (setReceivePolicy is set by the account itself, address(0) gives recovery control to the original sender, claim(to, receipt) is called by the captured authority)
- https://raw.githubusercontent.com/tempoxyz/tempo/main/crates/precompiles/src/tip20/mod.rs (transfer returns Ok(true) when validate_transfer reports a blocked inbound, and validate_inbound_or_block moves funds to the guard with originator set to the transfer's msg.sender)
- https://raw.githubusercontent.com/tempoxyz/tempo/main/crates/precompiles/src/receive_policy_guard/mod.rs (claim reverts with unauthorized_claimer unless msg_sender equals the recovery authority, which is the receipt originator in originator mode)
- https://rpc.mainnet.tempo.xyz (eth_call receivePolicy(PoolManager) on 0x403c000000000000000000000000000000000000 returns all zeros at block 50,260,093)

### F-041. Any account can book a balance increase it triggers at the PoolManager as its own payment, and EIP-7702 removes the origin check that guards Ampleforth's public rebase

Medium severity, confirmed. Effect: siphon. Who can trigger it: any account. Networks: Ethereum.

What differs on the network: Mainnet is the reference chain, so the difference is one that arrived after the Dencun rules the build targets. Since Pectra (EIP-7702) an EOA can run code and still satisfy msg.sender == tx.origin. The Ampleforth Orchestrator on mainnet uses that check as its only guard on the public rebase() function, and its source says the guard exists to protect liquidity providers from flash loan attacks. Mainnet also has reward contracts that pay a holder when any third party asks, such as Compound's claimComp(holder).

How it meets the code: sync has no lock check and records balanceOf(PoolManager) for any currency (src/PoolManager.sol:279-288). _settle credits the named recipient with the whole rise in that balance since the sync (src/PoolManager.sol:349-364). Pool accounting never reads balances, so a rise that comes from a rebase or a reward payment belongs to no pool, position or claim until someone settles it. The steps for AMPL are these. The attacker is an EOA that has delegated to its own contract code and sends a transaction to itself. Its code calls unlock, and the PoolManager calls unlockCallback on the same EOA (src/PoolManager.sol:104-114). Inside the callback the code calls sync(AMPL), then Orchestrator.rebase(), which passes the origin check because the caller is the transaction sender. When the day's supply change is positive, the AMPL balance of every holder grows, including the PoolManager's. The code then calls settle, which credits the attacker with the growth on the PoolManager's entire AMPL balance, and take(AMPL, attacker, growth), which pays it out (src/PoolManager.sol:291-297). All deltas are zero and unlock returns. The attacker paid gas only. The same bracket works for any token where an ordinary account can cause a transfer or a balance increase to the PoolManager: a reward claim on behalf of a holder, an airdrop claim that pays a named account, or a rebase with a public trigger. A negative rebase is never bracketed, so liquidity providers keep the losses and lose the gains. This is the unprivileged form of the stETH finding from cycle 1, where the trigger needs an oracle member.

What is at risk: The gain of each positive rebase or reward payment on the full balance the PoolManager holds in that token, across all pools, claims and accrued protocol fees. The existing mainnet PoolManager holds 16 base units of AMPL, and the public triggers I simulated moved nothing at block 26471590 (0 COMP from claimComp, no sOHM change), so the amount at risk today is close to zero. The new deployment starts empty. The exposure grows with any pool that lists a token of this kind. Without an attacker the same increase stays in the PoolManager as a surplus that core has no function to pay out, so liquidity providers do not receive it in either case; the attacker turns a stranded amount into a taken one.

What it takes: A pool or claim balance in a token whose balanceOf(PoolManager) an ordinary account can raise without paying the same amount: AMPL when a positive rebase is due and the attacker is first in the rebase window, or a token with a public reward or airdrop push to holders. For AMPL the attacker needs an EIP-7702 delegation, which any EOA can set. The rebase window is 1,200 seconds per day (offset 7,200 seconds into each 86,400), and the policy reported inRebaseWindow() = 0 at block 26471631, so my simulated rebase() call reverted. I did not execute the full sequence and did not simulate a delegated EOA; the origin check claim rests on the EIP text and the verified source. I checked 12 rebasing or reward-bearing tokens out of 66,554 token rows the explorer lists for the PoolManager.

What can be done: Liquidity providers and interfaces can avoid or flag pools in elastic supply and reward-pushing tokens and use wrapped, non-rebasing forms. A keeper or a hook can run the same bracket first and pass the proceeds to the pool with donate (src/PoolManager.sol:256-276), which returns the increase to in-range liquidity providers. Token projects cannot rely on msg.sender == tx.origin to keep contracts out. The deployer cannot close this in core without tracking reserves per currency.

Second reviewer's corrections: The actor value unprivileged is right: every step is open to any account, and the pooled token and the pool are not made by the attacker. The assumptions should also list A5, because a take of the pooled balance before the rebase followed by a nominal repayment gives the same gain without a sync before the rebase. A change that only restricted sync would leave that route open. The supports text for the EIP source says the broken invariant is that msg.sender == tx.origin implies an account without code. The EIP words it as the check being true only in the topmost execution frame, and it says the use of the check to ensure that msg.sender is an EOA is unaffected. The conclusion for the Orchestrator guard is the same. The preconditions should say that recent rebases changed supply by zero (block 26467574, and my simulation of the next window), so a gain needs a market rate outside the policy's deviation band as well as a pool that holds AMPL. With 16 base units held, the gain rounds to zero today. The Blockscout row count was 66,563 at my fetch. Severity stays medium on the scale: the loss is limited to pools that hold an elastic supply or reward pushing token, and no such pool holds a material balance today.

Code: `src/PoolManager.sol:279-288`, `src/PoolManager.sol:349-364`, `src/PoolManager.sol:291-297`, `src/PoolManager.sol:104-114`, `src/PoolManager.sol:256-276`.

Sources:

- https://sourcify.dev/server/v2/contract/1/0x6fb00a180781e75f87e2b690af0196baa77c7e7c?fields=sources,compilation (verified source of the Orchestrator at 0x6fb00a180781e75f87e2b690af0196baa77c7e7c: rebase() is external, begins with require(msg.sender == tx.origin) and then calls policy.rebase(); the comment says contracts are guarded from calling to avoid flash loan attacks on liquidity providers)
- https://raw.githubusercontent.com/ethereum/EIPs/master/EIPS/eip-7702.md (a delegated EOA may originate transactions and run its delegated code, and the EIP breaks the invariant that msg.sender == tx.origin implies an account without code (lines 299 to 310))
- https://ethereum-rpc.publicnode.com (eth_call at block 26471525: AMPL.monetaryPolicy() = 0x1b228a749077b8e307c5856ce62ef35d96dca2ea, policy.orchestrator() = 0x6fb00a180781e75f87e2b690af0196baa77c7e7c, AMPL.balanceOf(PoolManager) = 16. eth_call at block 26471631 on the policy: inRebaseWindow() = 0, minRebaseTimeIntervalSec() = 86400, rebaseWindowOffsetSec() = 7200, rebaseWindowLengthSec() = 1200, lastRebaseTimestampSec() = 1795312800; AMPL.totalSupply() = 1,527,834. eth_simulateV1 at blocks 26471565 and 26471590: Comptroller.claimComp(PoolManager) from an unrelated address succeeds and leaves COMP.balanceOf(PoolManager) unchanged; Olympus staking rebase() succeeds and leaves the sOHM balance unchanged; CometRewards.claim for the PoolManager reverts for lack of COMP in the rewards contract; eth_config reports fork id 0x07c9462e, a fork later than Pectra)
- https://eth.blockscout.com/api/v2/addresses/0x000000000004444c5dc75cB358380D2e3dE08A90/token-balances (token rows for the PoolManager address fetched 2026-11-22: 66,554 rows, including the stETH, OUSD, aToken, cToken, sOHM and AMPL balances quoted in the profile)

### F-008. Polygon system token at 0x1010 mirrors the PoolManager native balance and cannot be paid out by take

Low severity, confirmed. Effect: freeze. Who can trigger it: any account. Networks: Polygon.

What differs on the network: Polygon has a genesis contract at 0x0000000000000000000000000000000000001010 that presents native POL as a token. Its balanceOf returns the native balance of the account. Its transfer is payable and returns false unless msg.value equals the amount. Ethereum has no ERC-20 face of ETH at the protocol level.

How it meets the code: 1. sync(0x1010) stores balanceOf(PoolManager) as reserves (src/PoolManager.sol:285-286, src/types/Currency.sol:94). That value is the full native POL balance of the PoolManager, which already backs pools that use address(0). 2. settle with 0x1010 synced credits the caller with any rise in that native balance since sync (src/PoolManager.sol:358-360). msg.value is rejected at src/PoolManager.sol:356 and the PoolManager has no receive function, so the balance can rise only through a forced transfer such as SELFDESTRUCT. 3. take(0x1010, to, amount) calls transfer on 0x1010 with zero value (src/types/Currency.sol:73). The token returns a 32 byte zero. The success test at src/types/Currency.sol:68 fails and the call reverts at src/types/Currency.sol:82-86. collectProtocolFees for this currency reverts the same way (src/ProtocolFees.sol:56). 4. A positive delta in currency 0x1010 can therefore only be cleared, minted as an ERC-6909 claim, or swapped. The POL that paid for it stays in the PoolManager native balance and no account holds a native delta to take it. 5. Double credit was checked and is not possible. A native settle while 0x1010 is synced reverts at src/PoolManager.sol:356, and sync(address(0)) clears the synced currency (src/PoolManager.sol:281-283), so one POL is never credited under both currencies.

What is at risk: POL that a contract pays into a pool or claim denominated in 0x1010 cannot leave the PoolManager as that currency and is not claimable as native POL either. Pools that hold POL under address(0) are not affected. The PoolManager held about 3.1 million native POL at the time of the query. Protocol fees accrued in currency 0x1010 would also be stuck.

What it takes: Someone initializes a pool with 0x1010 as a currency, and a custom contract forces POL into the PoolManager between sync and settle. Standard periphery cannot do this because approve and transferFrom on 0x1010 revert. The actor loses its own funds. No path was found that takes funds from other users.

What can be done: Interfaces, routers and pool indexers on Polygon should refuse 0x0000000000000000000000000000000000001010 as a pool currency and direct users to address(0) or WPOL. Block explorers label 0x1010 as the POL token, so the warning should be explicit in deployment notes.

Second reviewer's corrections: Nothing wrong in the mechanism. One detail to add: a take of amount zero on 0x1010 would see transfer return true, and it changes nothing because a zero delta is ignored (src/PoolManager.sol:369). The frozen funds belong only to a party that chose to fund a 0x1010 position through a forced transfer, so low is the right level.

Code: `src/PoolManager.sol:279-288`, `src/PoolManager.sol:291-297`, `src/PoolManager.sol:349-365`, `src/types/Currency.sol:60-75`, `src/types/Currency.sol:82-86`, `src/types/Currency.sol:90-96`, `src/ProtocolFees.sol:44-57`.

Sources:

- rpc https://polygon.drpc.org, queries at block 97759148 to 97759199 on 2026-11-22 (balanceOf(PoolManager) on 0x1010 equals eth_getBalance(PoolManager); transfer(0xdead, 1) from the PoolManager with zero value returns 0; transfer(PoolManager, 1) with value 1 reverts; a 1 wei call with empty calldata to the PoolManager reverts; approve and transferFrom on 0x1010 revert)
- https://raw.githubusercontent.com/maticnetwork/contracts/main/contracts/child/MRC20.sol (Published source: balanceOf returns account.balance, transfer returns false when msg.value differs from value, deposit and _transfer use address.transfer)

### F-021. Three more recipients on HyperEVM accept a PoolManager payout and strand it: the L1 block number precompile, the ERC-4337 EntryPoints and a system address reached through the stHYPE contract

Low severity, confirmed. Effect: degrade. Who can trigger it: any account. Networks: HyperEVM.

What differs on the network: HyperEVM has a precompile at 0x0809 that answers any call, with or without value, with the L1 block number. The ERC-4337 EntryPoints v0.6 and v0.7 are deployed and book incoming value as a deposit of the sender. HyperCore credits an ERC-20 sent to a token's system address only from the Transfer log of the linked contract, and for STHYPE the linked contract is wstHYPE, one of two contracts that move the same balance.

How it meets the code: take debits the caller and then pays (src/PoolManager.sol:291-297). Read-only calls from the PoolManager address show what three recipients do with the payout. A native payout of 1 wei to 0x0000000000000000000000000000000000000809 returns success, so by the EVM's call rules the value is then held by a precompile address that cannot send it on (src/types/Currency.sol:44-53). A native payout to either EntryPoint succeeds and is booked as the PoolManager's deposit, which only the PoolManager could withdraw. Both EntryPoints answer balanceOf(PoolManager) with that deposit. A caller can therefore sync the EntryPoint address, make the payout and call settle, and is credited the same amount under the EntryPoint address as currency id (src/PoolManager.sol:279-288 and 349-365). That credit can be minted as an ERC-6909 claim and can never be paid out, because the EntryPoints revert on transfer(address,uint256). The caller still owes the native amount. A take of stHYPE to 0x2000000000000000000000000000000000000077 moves shares to the STHYPE system address while the linked contract, wstHYPE, emits no Transfer log, so by the documented rule HyperCore credits nobody. A take of wstHYPE to the same address is credited to the PoolManager's HyperCore account, as F-021 describes. In each case the caller pays the full amount and no other user loses anything.

What is at risk: The loss falls on the caller who chose the recipient, or on the user of a router that lets the user name any recipient. Pool reserves stay whole. Claims under an EntryPoint id are worthless and cannot affect another currency.

What it takes: A caller or a router that passes one of these addresses as recipient. The stHYPE case needs stHYPE in the PoolManager, which holds none today, and the statement that HyperCore credits nothing rests on the docs and was not tested.

What can be done: Routers and interfaces on HyperEVM should refuse recipients in 0x0800 to 0x08ff, the EntryPoint addresses, 0x2222222222222222222222222222222222222222 and addresses that start with 0x20 followed by zeros, unless the payer chose them knowingly. The 0x settler contracts added a similar rule for HyperCore system addresses.

Second reviewer's corrections: The stHYPE part is a consequence of the documented crediting rule and needs stHYPE in the PoolManager, which holds none. The actor value unprivileged is right in the sense that any caller can do it, and the loser is that caller or the user of a router that passes the recipient through. No other user loses funds.

Code: `src/PoolManager.sol:291-297`, `src/types/Currency.sol:44-87`, `src/PoolManager.sol:349-365`.

Sources:

- https://rpc.hyperliquid.xyz/evm eth_call from 0x12D4Fd9C5DeDd00ab8a0bCe2CF0167bbf94b6B1F to 0x0809 with empty calldata and value 1; to both EntryPoints with empty calldata and value 1, balanceOf and transfer (0x0809 and both EntryPoints accept the value call; the EntryPoints return 32 bytes for balanceOf and revert on transfer)
- https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm/hypercore-less-than-greater-than-hyperevm-transfers (EVM to HyperCore credits are based on the Transfer log emitted by the linked contract)
- https://api.hyperliquid.xyz/info spotMeta (STHYPE index 119 is linked to 0x94e8396e0869c9f2200760af0621afd240e1cf38, the wstHYPE contract)
- https://sourcify.dev/server/v2/contract/999/0xe71caf5c1fe56d8897c7b604295d23968049e057?fields=sources (A transfer through stHYPE emits Transfer from the stHYPE contract only)
- https://github.com/0xProject/0x-settler/blob/master/CHANGELOG.md (Another protocol reverts on HyperEVM when a payout names a HyperCore system address as recipient unless the payer funds the transfer)

### F-025. The OP Stack wrapped native predeploy on Celo calls itself Wrapped Ether and WETH but wraps CELO

Low severity, confirmed. Effect: siphon. Who can trigger it: any account. Networks: Celo.

What differs on the network: On OP Stack chains that use ETH for gas, 0x4200000000000000000000000000000000000006 is canonical WETH. On Celo the same address is a live wrapper of the native asset, which is CELO, and it still returns name 'Wrapped Ether' and symbol 'WETH' because the L2 L1Block predeploy reports the gas token as Ether. The bridged ETH token on Celo is a different contract at 0xD221812de1BD094f35587EE8E174B07B6167D9Af.

How it meets the code: The PoolManager accepts any address as a currency and reads no metadata (src/PoolManager.sol:117-142). It learns balances only through balanceOf (src/types/Currency.sol:90-96). Anyone can obtain the predeploy token one for one by depositing CELO. A pool, hook, router table or price source that treats this address as ETH backed WETH values a CELO backed token at the ETH price. Liquidity placed against it at that price is bought with tokens that cost one CELO each, and the paired asset leaves the PoolManager through ordinary swaps. Swappers who buy the token in such a pool receive a claim on CELO.

What is at risk: Funds of LPs and swappers in pools that list 0x4200...0006 as a currency, and integrations that map that address to WETH across OP Stack chains. Pools on the bridged WETH or on CELO are not affected. The PoolManager holds none of this token today, and its total supply is 0.143 CELO.

What it takes: Someone must create or join a pool with the predeploy as a currency while pricing it as ETH, or an integration must hardcode the address as WETH. Any account can do the rest.

What can be done: Interfaces and token lists for Celo should hide or relabel 0x4200...0006 and point to 0xD221...D9Af for ETH. Deployment scripts and routers should take the wrapped native address from Celo specific configuration. Pool creators should check that remoteToken() on a WETH candidate returns the Ethereum WETH address.

Second reviewer's corrections: 1. Severity lowered from medium to low. No path in the PoolManager mishandles the token. A loss needs an LP or an integration to price a CELO backed token as ETH. The PoolManager holds none of it, its whole supply is 0.143 CELO, and the deployed Uniswap periphery on Celo does not reference it. 2. The finding does not say which wrapped native address the periphery uses. PositionManager reports the CELO token itself as WETH9, which is a different question and is listed as a lead.

Code: `src/PoolManager.sol:117-142`, `src/types/Currency.sol:90-96`.

Sources:

- https://forno.celo.org eth_call name(), symbol(), decimals(), version(), totalSupply() on 0x4200000000000000000000000000000000000006 and eth_getBalance of the same address (name is 'Wrapped Ether', symbol is 'WETH', decimals 18, version 1.1.0-beta.3, and totalSupply equals the contract's native balance of 143112547216520198 wei.)
- https://forno.celo.org eth_call deposit() with 1 CELO of value on 0x4200000000000000000000000000000000000006 (simulation only) (deposit() accepts native CELO.)
- https://forno.celo.org eth_call isCustomGasToken(), gasPayingTokenName() on 0x4200000000000000000000000000000000000015 (The L2 L1Block predeploy returns false and 'Ether'.)
- https://forno.celo.org eth_call name(), remoteToken(), bridge() on 0xD221812de1BD094f35587EE8E174B07B6167D9Af (The bridged token is named 'Wrapped Ether (Celo native bridge)', its remote token is 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2 and its bridge is the L2StandardBridge.)
- https://docs.celo.org/operate/specification/native-bridge.md (Native ETH bridging is not supported on Celo and WETH is bridged as a standard ERC-20. The L1 bridge treats L1 CELO as the native token of Celo.)

### F-037. Aave aTokens held by the Arbitrum One PoolManager grow outside pool accounting and the growth cannot be claimed

Low severity, confirmed. Effect: degrade. Who can trigger it: any account. Networks: Arbitrum One.

What differs on the network: This is the rebasing token case that the Ethereum unit recorded for stETH, found here for Aave aTokens. No chain rule is involved. An aToken balance is a stored scaled amount multiplied by the reserve's liquidity index, so balanceOf(PoolManager) rises with time without any transfer.

How it meets the code: Step 1: a liquidity provider adds liquidity in a pool whose currency is an aToken. The pool records a fixed amount and the PoolManager receives the aTokens. Step 2: the index grows with time and balanceOf(PoolManager) grows with it. For aArbUSDT the PoolManager has a scaled balance of 1,214.98 and a balance of 1,504.61. Step 3: a credit exists only for a balance increase between a sync and a settle in the same transaction (PoolManager.sol:279-288 and 358-360). The index does not move inside a transaction as far as I could establish: interest accrues with time and the Aave pool sends the whole flash loan premium to the protocol. I checked the premium setting on chain and did not read the Aave pool code for other paths. A sync therefore always includes the interest accrued so far in the reserve figure, and no settle is ever credited for it. Step 4: take, burn and fee collection pay out only recorded amounts, so the accrued interest stays in the PoolManager balance and belongs to no pool, claim or fee. The provider gets back the recorded amount and the pool fees. I found no way for an ordinary account to collect the surplus, and none to reduce the balance below the recorded amounts.

What is at risk: Liquidity providers in aToken pools lose the lending interest on their deposit for as long as it stays in the pool. Balances today are small: 1,504.6 aArbUSDT, 443.3 aArbUSDCn, 34.9 aArbUSDC and 0.41 aArbWETH. Principal is not affected.

What it takes: A pool must use an aToken or another token whose balance rises without transfers. Nobody has to act. If a future Aave version again added value to the supplier index inside a transaction, an account that calls sync before it and settle after it would be credited the PoolManager's share of that addition.

What can be done: Use a non-rebasing wrapper of the aToken as the pool currency. Interfaces can warn when a pool currency reports a scaled balance that differs from its balance.

Second reviewer's corrections: The actor value unprivileged is acceptable only in the sense that no privilege is needed. No account acts and no account gains. Nothing is taken from the PoolManager and nothing is frozen, so this item is outside the goal of the review and should be reported as lost yield for providers who choose a rebasing currency. The scaled balance of aArbUSDT read 1,214.96 at my query against 1,214.98 in the finding. The warning in the preconditions is the part worth keeping: a token whose balanceOf(PoolManager) can be raised by a call that any account may make inside a transaction would let that account collect the PoolManager's share through sync and settle. Lead 5 of the research file covers the search for such a token and I add what I found on xUSD as a lead.

Code: `src/PoolManager.sol:279-288`, `src/PoolManager.sol:349-364`.

Sources:

- https://arb1.arbitrum.io/rpc eth_call scaledBalanceOf(PoolManager), balanceOf(PoolManager) and POOL() on aArbUSDT 0x6ab707Aca953eDAeFBc4fD23bA73294241490620 and aArbUSDCn 0x724dc807b04555b71ed48a6896b6F41593b8C637, and FLASHLOAN_PREMIUM_TOTAL() and FLASHLOAN_PREMIUM_TO_PROTOCOL() on 0x794a61358D6845594F94dc1DB02A252b5b4814aD, queried 2026-11-22 (The PoolManager holds aTokens whose balance exceeds the scaled balance, and the Aave pool directs 100 percent of the flash loan premium to the protocol.)
- https://aave.com/docs/aave-v3/smart-contracts/tokenization (Yield is distributed to aToken holders by continuously increasing their balance, and balanceOf returns principal plus yield.)
- https://governance.aave.com/t/arfc-bgd-aave-v3-4/21572 (Aave v3.4 removed the part of the flash loan fee that was added to the supplier index, which leaves time based accrual as the only way the index rises.)

### F-038. Any account can fill a boundary tick to the per tick liquidity cap for a dust payment, which blocks later deposits that use that tick

Low severity, confirmed. Effect: degrade. Who can trigger it: any account. Networks: all 21 networks.

What differs on the network: None. The cap and the amount formula are part of the pool math and give the same numbers on every network. Read-only probes against the PoolManager on 20 of the 21 networks returned identical results. Tempo could not be probed with a native payment because the node rejects calls that carry value.

How it meets the code: Pool.modifyLiquidity adds liquidityDelta to liquidityGross of the lower and the upper tick of the range (src/libraries/Pool.sol:160-162, 524-531). For a delta of zero or more it reverts with TickLiquidityOverflow when liquidityGross of either tick is above tickSpacingToMaxLiquidityPerTick (Pool.sol:165-173). The cap is (2^128 - 1) divided by the number of ticks (Pool.sol:565-582): 191757530477355301479181766273477 for spacing 1, 1917559095893846719543856547154045 for spacing 10, 11505354575363080317263139282924270 for spacing 60 and 38345995821606768476828330790147420 for spacing 200, which are the values in test/Tick.t.sol:115-141. A range that lies above the current tick is paid in currency0 only, with getAmount0Delta(sqrtLower, sqrtUpper, liquidity) rounded up (Pool.sol:209-217, src/libraries/SqrtPriceMath.sol:188-211, 261-271). That amount is liquidity times the difference of the inverse sqrt prices, and at the highest usable ticks the sqrt prices are close to 2^160, so the amount is tiny. Filling the highest usable tick to the cap with a range one spacing wide costs 519,766,372 base units of currency0 at spacing 1, 51,993,092,462 at spacing 10, 1,878,783,905,959 at spacing 60 and 20,966,766,746,469 at spacing 200. The mirror case at the lowest usable tick is paid in currency1 and costs 519,766,206, 51,993,074,932, 1,878,783,895,257 and 20,966,766,629,403 base units. The cost does not depend on where the pool trades as long as the range is out of range. After the fill, every add whose range starts or ends on that tick reverts, whoever the owner is and however small the amount. An owner who removes liquidity from that tick can add back at most what it removed. Removals never run the cap check, because the check sits inside the branch for a delta of zero or more (Pool.sol:165), so nothing is locked. The filler can remove its position at any time and gets its payment back, so the fill costs gas and idle dust. Flash accounting does not make it free: the position has to stay, so the debit has to be settled. I confirmed the numbers three ways. A Python transcription of Pool, Position, TickBitmap, SqrtPriceMath and TickMath gives them. An eth_call through the PositionManager on Ethereum for the ETH/USDC 0.05 percent pool (spacing 10) minted 1917559095893846714755826590044058 units of liquidity on the range 887260 to 887270 with a value of 51,993,092,462 wei, reverted with one wei less, and reverted with TickLiquidityOverflow(887270) for one more unit of liquidity. The same three calls on a pool created inside the call gave the same outcome on 20 networks for spacings 1, 60 and 200.

What is at risk: New deposits that use the filled tick stop in that pool. This covers the usual full range position and every position that ends on the lowest or highest usable tick. Principal and fees of existing positions are not touched and can be withdrawn. A liquidity provider can avoid the block by choosing an outer tick further inside, at the price of a position that front ends do not show as full range. A contract that always adds on the filled tick, such as a full range vault or a hook that holds one fixed full range position, cannot take deposits or reinvest fees while the fill stands. If such a contract has to add liquidity on that tick before it can pay out, its withdrawals stop too. I looked for one deployed contract of that kind and did not find it, so the freeze variant is unconfirmed. For a currency with 18 decimals the cost is below 0.00003 of one token for every spacing up to 200. For a currency with 6 decimals it is about 520 tokens at spacing 1 and about 1.88 million tokens at spacing 60, so the attacker fills the end whose currency is cheap per base unit. On the Ethereum ETH/USDC 0.05 percent pool the liquidityGross of tick 887270 was 4788029957109987 at block 26471794, 18 orders of magnitude under the cap, and the fill costs about 0.00000005 ETH.

What it takes: An initialized pool in which at least one of the two currencies is cheap per base unit. Any account can act. No hook, no role and no ordering advantage is needed. The fill lasts until the filler removes its position.

What can be done: Core has no switch for this. Front ends and liquidity providers can fall back to an outer tick one or more spacings inside the usable range when the boundary tick is full. Authors of vaults and hooks should not hard-code the lowest and highest usable ticks in any path that must succeed for a withdrawal, and should let the range be changed. Operators can watch liquidityGross of the two boundary ticks of important pools through extsload and compare it with the cap.

Second reviewer's corrections: The actor is correct: any account can add liquidity to a pool without a hook, and the affected users did nothing unusual. The severity stays low. The medium row of the scale mentions blocked liquidity operations. Here only adds that touch the one filled tick are blocked, removal and fee collection keep working, and a range that ends one spacing further inside is accepted. No funds are taken or frozen. The freeze variant for a contract that must add on that tick in its exit path remains unconfirmed, as the finding says. The finding states that the hazard is the same on every network. It does not follow from a network difference, so it is a general property of this code and does not answer the search for a network-specific weakness. The cap applies to every tick. The finding treats the two boundary ticks because the cost there is dust. The cost rises steeply toward the current price. The side remark about Soneium is out of date: eth_getBalance for the PositionManager 0x1b35d13a2e2528f192637f14b05f0dc0e7deb566 returned 0 at block 31118892, and the one wei less probe reverted there like on the other networks. The source entries call the on-chain probes primary evidence for the formulas. They are primary evidence for the deployed contracts. The link from src/ to the numbers is the transcription, which I rebuilt independently with the same result.

Code: `src/libraries/Pool.sol:159-181`, `src/libraries/Pool.sol:206-237`, `src/libraries/Pool.sol:520-531`, `src/libraries/Pool.sol:565-582`, `src/libraries/SqrtPriceMath.sol:188-211`, `src/libraries/SqrtPriceMath.sol:261-271`, `src/PoolManager.sol:145-184`.

Sources:

- src/libraries/Pool.sol:165-173 (The cap is checked only when liquidityDelta is zero or more, on liquidityGross of both ticks.)
- src/libraries/Pool.sol:209-217 (A range above the current tick is paid in currency0 only, from the sqrt prices of its two ticks.)
- src/libraries/Pool.sol:565-582 (The cap is (2^128 - 1) divided by the number of ticks for the spacing.)
- test/Tick.t.sol:115-141 (The repository tests state the same cap values for spacings 1, 10, 60 and 200 that the cost figures use.)
- https://ethereum-rpc.publicnode.com (extsload on PoolManager 0x000000000004444c5dc75cB358380D2e3dE08A90 at block 26471794: pool id 21c67e77068de97969ba93d4aab21826d33ca12bb9f565d8496e8fda8a82ca27 (ETH/USDC, fee 500, spacing 10) has liquidityGross 4788029957109987 at tick 887270 and 0 at tick 887260. eth_call at the latest block (about 26471905) from an account with an overridden balance to PositionManager 0xbd216513d74c8cf14cf4747e6aaa6420ff64ee9e, modifyLiquidities with MINT_POSITION and SETTLE_PAIR on ticks 887260 to 887270: liquidity 1917559095893846714755826590044058 succeeds with value 51993092462 wei, reverts with 51993092461 wei, and liquidity one unit higher reverts with data 0xb8e3c385 followed by 0xd89e6, which is TickLiquidityOverflow(887270). The ETH/USDC fee 3000 spacing 60 pool gives the same pattern at tick 887220 with 1878783905959 wei.)
- rpc endpoints listed in research/network-risk/state/networks.json (On 20 networks (all except Tempo) an eth_call to the PositionManager multicall that initializes a new native pool and mints on the top one spacing range succeeds with a value of exactly 519766372, 1878783905959 and 20966766746469 wei for spacings 1, 60 and 200, reverts with one wei less, and reverts with TickLiquidityOverflow for one liquidity unit above the cap. On Soneium the PositionManager already holds 176652317140 wei that the settlement draws on, so the lower value was reduced by that balance and the one wei less check could not be made for spacing 1.)

### F-039. The swap loop pays for every bitmap word and every initialized tick on its way, and a HyperEVM small block holds 3,000,000 gas

Low severity, confirmed. Effect: degrade. Who can trigger it: any account. Networks: HyperEVM.

What differs on the network: HyperEVM produces small blocks with a 3,000,000 gas limit every second and big blocks with a 30,000,000 gas limit about once a minute. A sender reaches big blocks only after setting the usingBigBlocks flag on its HyperCore account. I sampled blocks 51958402 to 51958471 through the public RPC: 69 had gasLimit 3,000,000 and one (51958443) had 30,000,000. For comparison, state/networks.json records an Ethereum block gas limit of 59,999,943, and EIP-7825 specifies a cap of 16,777,216 gas per transaction. I did not confirm in this session that the cap is active on Ethereum.

How it meets the code: Pool.swap runs one loop iteration per step (src/libraries/Pool.sol:344-437). Each iteration reads one tick bitmap word from storage (Pool.sol:347-348, src/libraries/TickBitmap.sol:85-121), computes the price of the next tick and runs one swap step. When the step ends on an initialized tick, crossTick reads the tick slot and reads and rewrites both fee growth slots of that tick (Pool.sol:413-428, 602-612). The repository gas snapshots give 2,242 to 2,287 gas for the bitmap search, which includes the cold storage read, and 919 to 1,565 gas for a swap step with liquidity. I use 2,242 gas as the floor for one iteration and leave out the swap step, TickMath and loop bookkeeping. A crossing adds one cold read (2,100) and two read and write pairs. Each pair costs 5,000 gas when the slot changes from one nonzero value to another and 22,100 gas when it is written for the first time. That gives about 14,342 gas per crossing when both fee growth slots change, and about 48,542 when both are written for the first time. With the repository figure of 123,144 gas for a simple swap as fixed cost, a 3,000,000 gas transaction fits at most about 200 crossings, about 59 when the fee growth slots are written for the first time, and about 1,283 empty bitmap words. The real numbers are lower, because the floor leaves out the computation. I did not measure gas on HyperEVM. Three things an ordinary account controls raise the iteration count of other people's swaps. First, modifyLiquidity lets anyone add a position of one liquidity unit on any aligned tick pair of a pool without a hook (src/PoolManager.sol:145-184, Pool.sol:159-181). In my transcription of the source, 200 such positions on [t, t+1) below the price of a pool with tick spacing 1 made every tick initialized, each cost 1 base unit of one currency, and a swap that moved the price by 100, 200 and 400 ticks ran 101, 201 and 401 iterations, each with a crossing. Second, a step with zero liquidity in range consumes nothing and moves the price to the next word boundary (src/libraries/SwapMath.sol:63-75), so a swap that runs past the last position toward its price limit visits every word on the way. From tick 0 to the lower limit that is 3,468 iterations at tick spacing 1, 349 at spacing 10, 60 at spacing 60 and 20 at spacing 200, which is at least 7,775,256 gas at spacing 1 from the bitmap reads alone. Third, initialize has no access control and accepts any price from MIN_SQRT_PRICE up to one unit below MAX_SQRT_PRICE (PoolManager.sol:117-142, Pool.sol:100-107), so a third party can create a pool id at an extreme price before anyone else uses it. The gap to the market price then has to be walked with swaps that take no tokens and still pay for every word.

What is at risk: No funds leave the PoolManager and no position is frozen. Pool.modifyLiquidity has no loop (Pool.sol:146-238), so removals fit in a small block in every case I looked at. The cost falls on swappers and arbitrageurs in pools with tick spacing 1 or other small spacings. In a pool where every tick carries a dust position, one small block transaction can move the price by at most about 59 to 200 ticks, which is 0.6 to 2.0 percent at spacing 1. A larger move needs several transactions with nearer price limits, or a big block. A swap that names the extreme price limit and exceeds the liquidity on its side runs out of gas in a small block where it would otherwise end with a partial fill. A contract that must complete one large swap in one transaction, for example a liquidation, can stall until it is sent to a big block. The dust positions cost the attacker about 161,276 gas each by the repository snapshot for a simple add, plus one base unit, and stay until the attacker removes them.

What it takes: The pool has a small tick spacing, since at spacing 60 a move of 59 crossings is already more than 40 percent. The attacker pays gas for each dust position. The victim sends the swap to a small block, or the swap sits inside a contract that cannot split it. Any account can undo the third case by walking the price in several transactions.

What can be done: Routers and keepers on HyperEVM can pass a price limit close to the expected end price and split large swaps. Contracts that depend on one atomic swap can use pools with a wider tick spacing or send the transaction to a big block. Pool creators can initialize the pool ids they intend to use at the market price before announcing them. Liquidity providers do not need to act, because removal does not loop.

Second reviewer's corrections: The finding says it did not confirm that the EIP-7825 cap is active on Ethereum. It is active since Fusaka on 2025-12-03. The run with 200 dust positions cannot give 401 passes for a 400 tick move: my transcription gives 203 passes (201 crossings of the ticks from 0 down to -200 and two further passes to the word end and to the limit), and 401 passes need about 400 dusted ticks. My pass counts for the empty walk are one lower than the finding's (3,467, 348, 59 and 19), which changes the bitmap floor to 7,773,014 gas and changes no conclusion. The 48,542 gas case needs both fee growth outside slots of a tick to go from zero to nonzero. That happens for a tick above the current price when it is crossed upward for the first time while both global fee growth values are nonzero (Pool.sol:533-539, 608-609). Dust placed below the price starts with both slots equal to the global values, so those crossings fall in the 14,342 gas case or lower. The attacker can bring a tick back to the first time state by removing and adding the dust position again. Refunds for slots set to zero are paid after execution and do not lower the gas limit a swap needs. The evidence grade can move from inferred to primary for the block limits and the cold read cost. The per pass total on HyperEVM stays an upper bound on the number of crossings until someone measures it.

Code: `src/libraries/Pool.sol:344-437`, `src/libraries/Pool.sol:602-612`, `src/libraries/TickBitmap.sol:85-121`, `src/libraries/SwapMath.sol:63-75`, `src/PoolManager.sol:117-142`, `src/PoolManager.sol:145-184`, `src/libraries/Pool.sol:146-238`.

Sources:

- https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm/dual-block-architecture (Fast blocks last 1 second with a 3M gas limit and slow blocks last 1 minute with a 30M gas limit. A sender is directed to big blocks by the HyperCore action evmUserModify with usingBigBlocks true.)
- https://rpc.hyperliquid.xyz/evm eth_getBlockByNumber for blocks 51958402 to 51958471 (69 of the 70 sampled blocks report gasLimit 3,000,000 and block 51958443 reports 30,000,000.)
- https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm (The HyperEVM uses the Cancun hardfork without blobs. That the gas schedule equals Ethereum's Cancun schedule is my inference from this sentence.)
- https://eips.ethereum.org/EIPS/eip-2929 (COLD_SLOAD_COST is 2100 and SSTORE_RESET_GAS becomes 5000 minus COLD_SLOAD_COST, which is 2900.)
- https://eips.ethereum.org/EIPS/eip-2200 (SSTORE_SET_GAS is 20000.)
- https://eips.ethereum.org/EIPS/eip-7825 (The cap of 16,777,216 gas per transaction that I quote for Ethereum as comparison.)
- snapshots/TickBitmapTest.json:5-10 (nextInitializedTickWithinOneWord costs 2,242 to 2,287 gas in the repository snapshots.)
- snapshots/SwapMathTest.json:2-9 (computeSwapStep costs 919 to 1,565 gas in the repository snapshots.)
- snapshots/PoolManagerTest.json:12-16 (A simple add of liquidity costs 161,276 gas and a simple swap 123,144 gas through the test routers.)
- src/libraries/Pool.sol:344-437 (One loop iteration per bitmap word or initialized tick, with the tick crossing at lines 413 to 428.)

### F-042. One transaction can use the whole per-block budget for new state on MegaETH, and the node skips every later candidate of that block

Low severity, confirmed. Effect: degrade. Who can trigger it: any account. Networks: MegaETH.

What differs on the network: MegaETH counts new accounts and new storage slots per transaction and per block, and both limits are 1,000 entries. Ethereum has no such counter. The block limiter admits the transaction that brings the block counter to the limit and then rejects every further candidate before execution, whatever that candidate would do. The base fee has stayed at its floor of 1,000,000 wei in every block sampled.

How it meets the code: A sender submits one transaction that creates 1,000 new state entries, for example a contract creation that writes 999 fresh storage slots. eth_estimateGas accepts that creation at 22,559,525 gas, which at the base fee of 1,000,000 wei is about 0.0000226 ETH, and rejects a creation with 1,000 slots. Storage gas is zero for slots in buckets of minimum size, so the cost is the compute gas of the writes. After this transaction the block counter for state growth equals the block limit. BlockLimiter::pre_execution_check then returns StateGrowthLimit for every later candidate of that block, including a liquidity removal or a take that creates no new state. Those candidates are skipped and can enter a later block. A sender who repeats this in every one second block spends about 1.95 ETH per day. Calls to modifyLiquidity and take on the PoolManager have no path that avoids the block limiter. What the sender achieves depends on where its transaction lands inside each block. Candidates placed before it are included. The ordering rule of the sequencer was not confirmed, so the share of each block that the sender can close was not established.

What is at risk: Removals, swaps and claims on the PoolManager can be delayed block by block while the sender keeps paying. No balance moves and no position changes. The delay ends when the sender stops or when users' transactions are ordered ahead of the sender's.

What it takes: The base fee stays near its floor, and the sender's transaction is ordered early in each block. No role is needed. A full stop of withdrawals would need the sender to be first in every block, which the public record does not show to be possible.

What can be done: Core has no setting for this. Users can resubmit, pay a higher priority fee if the sequencer orders by fee, or use the L1 deposit path, whose transactions are placed at the start of a block in the OP Stack design. That placement was not confirmed in the MegaETH node source. The chain operator can raise the block limit above the transaction limit or price new state entries in minimum-size buckets.

Second reviewer's corrections: The gas figure differs slightly with my own init code (22,559,391 against 22,559,525), which does not change the cost. The specification says later candidates are skipped when they depend on the exhausted resource, while the reference limiter skips every candidate. The finding follows the limiter, and that is the stricter reading. The precondition is stated too narrowly. The finding says a full stop needs the sender to be first in every block. If the sequencer serves pending transactions in arrival order, a run of N such transactions submitted together from several accounts would close N consecutive blocks for every transaction that arrives after the run, at 0.0000226 ETH per block. If the sequencer orders by priority fee, the same run with a priority fee of 1 wei outranks the current traffic, whose median priority fee is zero, until users pay more. This extension follows from the limiter logic and was not observed on chain. The severity stays low for the confirmed part, which is a delay inside one block. It would be medium under the scale if the multi-block case is confirmed, because liquidity operations would be blocked without loss for as long as the sender pays. The operator of the single sequencer can exclude such transactions, so the stall would last until the operator reacts.

Code: `src/PoolManager.sol:145-184`, `src/PoolManager.sol:291-297`.

Sources:

- https://raw.githubusercontent.com/megaeth-labs/mega-evm/main/crates/mega-evm/src/block/limit.rs (pre_execution_check rejects a candidate when block_state_growth_used is at or above block_state_growth_limit, and only the data availability tests are skipped for deposits)
- https://raw.githubusercontent.com/megaeth-labs/mega-evm/main/crates/mega-evm/src/constants.rs (TX_STATE_GROWTH_LIMIT and BLOCK_STATE_GROWTH_LIMIT are both 1000)
- https://docs.megaeth.com/spec/megaevm/resource-limits.md (The first transaction that meets or exceeds a block-level runtime limit is included and later candidates are skipped for the current block)
- https://raw.githubusercontent.com/megaeth-labs/mega-evm/main/crates/mega-evm/src/external/gas.rs (SSTORE storage gas is the base of 20,000 times (multiplier minus 1), which is zero at multiplier 1)
- rpc https://mainnet.megaeth.com/rpc, eth_call with from set to the PoolManager and with state overrides, eth_getCode, eth_getBalance, eth_estimateGas and eth_getBlockByNumber at blocks 32558000 to 32563302 on 2026-11-22 (eth_estimateGas returned 22,559,525 gas for a creation writing 999 new slots, a creation writing 1,000 slots reverts, and five sampled blocks report a base fee of 1,000,000 wei)

### F-044. A HyperCore transfer makes the node call a linked contract with 200,000 gas ahead of every signed transaction in the block

Low severity, confirmed. Effect: degrade. Who can trigger it: any account. Networks: HyperEVM.

What differs on the network: HyperCore credits a spot transfer to the EVM through a system transaction that calls transfer(recipient, amount) on the contract linked to the token, with the token's system address as sender, gas price 0 and 200,000 gas. The docs state that the linked contract may have arbitrary bytecode and give no guarantee about what its transfer function does. Deploying and linking a spot token is open to anyone; the deploy auction stood at 500 on 2026-11-22. System transactions are placed before all signed transactions of the block and their gas does not count toward the block gas limit. On Ethereum only the block builder decides which code runs first.

How it meets the code: An account deploys a spot token on HyperCore, links it to a contract it wrote and sends the token to the token's system address. The node then calls that contract's transfer function at the top of an EVM block, before any signed transaction. Inside the call the contract is an ordinary caller of the PoolManager. It can call unlock, which calls unlockCallback on it (src/PoolManager.sol:104-114), swap, and settle with tokens or ERC-6909 claims it holds (src/PoolManager.sol:187-227 and 322-336). The PoolManager gives the system address and the linked contract no role, and transient state is cleared after the system transaction like after any other, so nothing carries into the signed transactions. What the account gains is position: it reaches every pool before transactions that paid a priority fee, for the price of one HyperCore action. That is the first leg of a sandwich, or first place for arbitrage after a price move. A swapper loses at most what the price limit and slippage setting of the swap allow. Reserves, positions and claims of other users are not reachable this way.

What is at risk: Swappers in any pool can be traded against from the first position of a block by an account without validator rights. The loss per swap is bounded by the swapper's own limits. LP principal and claims are unaffected.

What it takes: The attacker deploys and links one spot token. The pool action must fit in 200,000 gas; I did not measure a complete swap against that limit. I did not confirm how HyperCore orders several system transactions inside one block, which EVM block follows a given HyperCore action, or whether pending EVM transactions are visible to the attacker in time.

What can be done: Swappers and routers should set tight price limits. Routers should not treat a quote from one block as valid at the top of the next. Pools that need protection from first position trading have to add it in a hook.

Second reviewer's corrections: The finding's own open points stay open: I did not measure whether an unlock with a swap and settlement in claims fits in 200,000 gas, and I did not confirm the order of several system transactions or how early a HyperCore action must be sent to land ahead of a given signed transaction. One addition: the exchange API documents a sendToEvmWithData action that calls coreReceiveWithData on the linked contract with a gasLimit and a data field chosen by the sender, so the 200,000 gas figure may not bound what a linked contract can do at the top of a block. The auction field that reads 500.0 is startGas and endGas. This is an ordering hazard for swappers within their own price limits and is no path to funds held for other users.

Code: `src/PoolManager.sol:104-114`, `src/PoolManager.sol:187-227`.

Sources:

- https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm/hypercore-less-than-greater-than-hyperevm-transfers (Credits are made by a system transaction that calls transfer on the linked contract as the system address; the linked contract may have arbitrary bytecode; a transfer from HyperCore costs 200k gas at the base gas price of the next HyperEVM block)
- https://raw.githubusercontent.com/hl-archive-node/nanoreth/master/src/node/types/mod.rs (Lines 83 to 101: the first system_tx_count transactions of a block are the system transactions)
- https://raw.githubusercontent.com/hl-archive-node/nanoreth/master/src/node/evm/executor.rs (Lines 225 to 227: gas of system transactions is not added to the block total)
- https://rpc.hyperliquid.xyz/evm eth_getSystemTxsByBlockNumber for 60 blocks ending near 51,957,680 (Four system transactions from 0x200000000000000000000000000000000000007c called transfer on the linked contract 0x000000000000780555bd0bca3791f89f9542c2d6 with 200,000 gas and gas price 0)
- https://api.hyperliquid.xyz/info spotDeployState (gasAuction currentGas 500.0 on 2026-11-22)

### F-047. A native payout sent to a withdrawal predeploy, a fee vault, an EntryPoint or a Celo core contract is lost to the caller on Celo and X Layer

Low severity, confirmed. Effect: freeze. Who can trigger it: any account. Networks: Celo, X Layer.

What differs on the network: Both chains have contracts that accept a plain native transfer and book it to msg.sender or keep it. On Celo these are L2ToL1MessagePasser (0x4200000000000000000000000000000000000016), the fee vaults at 0x11, 0x19, 0x1a and 0x1b, the L1BlockNumber predeploy at 0x13, the wrapped native predeploy at 0x06, the three ERC-4337 EntryPoints, and the Celo core contracts FeeHandler, MentoFeeHandlerSeller, UniswapFeeHandlerSeller, Reserve and Governance. On X Layer the fee vaults, 0x13, both Wrapped OKB contracts and the EntryPoints accept value. The X Layer L2ToL1MessagePasser refuses value because the chain runs in custom gas token mode.

How it meets the code: 1. take(address(0), to, amount) debits the caller by amount and makes the PoolManager send amount of the native asset to the recipient with empty calldata (src/PoolManager.sol:291-297, src/types/Currency.sol:44-52). The recipient sees the PoolManager as msg.sender. 2. On Celo, L2ToL1MessagePasser.receive() calls initiateWithdrawal(msg.sender, 100000, empty data). The CELO leaves the L2 and the withdrawal names the PoolManager address as L1 target. That address has no code and no balance on Ethereum. 3. An EntryPoint books the amount as a deposit of the PoolManager. The PoolManager cannot call withdrawTo, and the EntryPoint spends a deposit only after the account answers a validation call that src/ does not implement. 4. A fee vault, the Reserve, the FeeHandler contracts and Governance keep the amount as their own balance. 5. The wrapped native contracts mint wrapped tokens to the PoolManager address. A caller who syncs the wrapper first and settles afterwards is credited that amount under the wrapper's currency id, which is an ordinary wrap at one to one. 6. In every case the caller still owes amount in currency address(0) and must pay it before unlock returns (src/PoolManager.sol:112, 349-364). Pool reserves are unchanged in total. 7. A caller who syncs an EntryPoint, takes native value to it and settles is credited amount under the EntryPoint's currency id, because the EntryPoint's balanceOf is the deposit (src/PoolManager.sol:279-288, 358-360). The EntryPoint has no transfer function, so that credit can never be taken (src/types/Currency.sol:60-86).

What is at risk: The loss is the amount of one payout and falls on the account that chose the recipient. No pool reserve, no claim of another user and no protocol fee is reduced, and an attacker gains nothing by doing this on purpose.

What it takes: A user, a router or a front end passes one of these addresses as the recipient of a native take. Core gives no third party a way to choose the recipient of another account's payout. Whether the deployed routers and the PositionManager filter recipients was not read.

What can be done: Routers and front ends can refuse the predeploy range, the EntryPoint addresses and the Celo core contract addresses as recipients of native payouts. Users who want CELO on Ethereum should take to their own account and withdraw from there.

Second reviewer's corrections: No change to actor or severity. The actor value unprivileged is acceptable only in the sense that no role is needed. The one party that loses is the account that named the recipient, so this item is no path to other users' funds and no attacker gains from it. Step 7 should add that the credit under the EntryPoint id has to be cleared or minted before unlock returns. The op-stack-eth unit recorded the same hazard for the ETH chains, and the two entries can be merged.

Code: `src/PoolManager.sol:291-297`, `src/types/Currency.sol:44-52`, `src/PoolManager.sol:279-288`, `src/PoolManager.sol:349-364`, `src/types/Currency.sol:60-86`.

Sources:

- https://raw.githubusercontent.com/celo-org/optimism/celo-rebase-17/packages/contracts-bedrock/src/L2/L2ToL1MessagePasser.sol (receive() calls initiateWithdrawal(msg.sender, RECEIVE_DEFAULT_GAS_LIMIT, empty bytes) with a default gas limit of 100,000.)
- https://forno.celo.org eth_call with from 0x288dc841A52FCA2707c6947B3A777c5E56cd87BC, empty calldata and value 1 wei and 10^18 wei to each listed address; version() on 0x4200000000000000000000000000000000000016 (The value calls succeed for the listed Celo addresses. The message passer reports version 1.1.1-beta.1.)
- https://rpc.xlayer.tech eth_call with from 0x360e68faccca8ca495c1b759fd9eee466db9fb32, empty calldata and value to each listed address; version() on 0x4200000000000000000000000000000000000016 (The value calls succeed for the fee vaults, 0x13, both Wrapped OKB contracts and the EntryPoints. The message passer reports version 1.2.0+custom-gas-token and reverts with 0xcdfaa111 when value is sent.)
- https://forno.celo.org and https://rpc.xlayer.tech eth_call balanceOf(PoolManager) and transfer(address,uint256) on 0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789, 0x0000000071727De22E5E9d8BAf0edAc6f37da032 and 0x4337084D9E255Ff0702461CF8895CE9E3b5Ff108 (Each EntryPoint answers balanceOf with 0 for the PoolManager and reverts on transfer.)
- https://ethereum-rpc.publicnode.com eth_getCode and eth_getBalance of 0x288dc841A52FCA2707c6947B3A777c5E56cd87BC and 0x360e68faccca8ca495c1b759fd9eee466db9fb32 (Neither PoolManager address has code or balance on Ethereum.)

### F-048. A native payout sent to L2ToL1MessagePasser, an ERC-4337 EntryPoint or the L1BlockNumber predeploy is booked to the PoolManager's own address and is lost to the caller

Low severity, confirmed. Effect: freeze. Who can trigger it: any account. Networks: Optimism, Base, Unichain, Zora, Worldchain, Ink, Soneium.

What differs on the network: OP Stack chains have a withdrawal contract, L2ToL1MessagePasser at 0x4200000000000000000000000000000000000016, whose receive() starts a withdrawal to L1 for msg.sender and uses msg.sender as the L1 target. Ethereum has no contract with that behaviour. The legacy L1BlockNumber predeploy at 0x4200000000000000000000000000000000000013 accepts ETH with any calldata and has no function that pays it out. The ERC-4337 EntryPoint, which also exists on Ethereum, credits a plain ETH transfer as a deposit of msg.sender.

How it meets the code: 1. take(address(0), to, amount) debits the caller by amount and then makes the PoolManager send amount of ETH to the recipient with empty calldata and all gas (src/PoolManager.sol:291-297, src/types/Currency.sol:44-52). The recipient sees the PoolManager as msg.sender. 2. If the recipient is L2ToL1MessagePasser, its receive() calls initiateWithdrawal(msg.sender, 100000, empty data). The ETH is taken off the L2 and a withdrawal is recorded with the PoolManager as sender and the PoolManager's address as the L1 target. The PoolManager addresses of all seven chains have no code on Ethereum. If the withdrawal is proven and finalised on L1, the ETH is delivered to that address, where nothing can move it. The value call returned success in eth_call on OP Mainnet, Base and Unichain. 3. If the recipient is an EntryPoint, receive() calls depositTo(msg.sender) and the amount becomes a deposit of the PoolManager. withdrawTo pays out only the deposit of its own caller, and the PoolManager cannot call it. The EntryPoint spends a deposit only after the account answers validateUserOp or validatePaymasterUserOp, and src/ has neither function, so the deposit cannot be spent. 4. If the recipient is L1BlockNumber, the fallback keeps the ETH and returns the L1 block number. 5. In each case the caller still owes amount in currency address(0) and must pay it with msg.value before unlock returns (src/PoolManager.sol:112, 349-364). Pool reserves are unchanged in total: amount left and amount came back in. The caller has paid for a payout that reached nobody. 6. A caller who first calls sync(EntryPoint), then takes native ETH to the EntryPoint and then calls settle is credited amount under the currency id of the EntryPoint, because balanceOf(PoolManager) on the EntryPoint is the deposit (src/PoolManager.sol:279-288, 358-360). That credit can be minted as an ERC-6909 claim and can never be paid out, because the EntryPoint has no transfer function and take reverts (src/types/Currency.sol:60-86). The native debt from step 1 remains and must still be paid in full.

What is at risk: The loss is the amount of one payout and falls on the account that chose the recipient. No pool reserve, no other user's claim and no protocol fee is reduced, and an attacker gains nothing by doing this on purpose. One sign that the L1 twin addresses do receive stray value: the Base PoolManager address holds 0.0588 ETH and no code on Ethereum. How that ETH arrived was not traced.

What it takes: A user, a router or a front end passes one of these addresses as the recipient of a native take, for example in the belief that sending ETH to the message passer bridges it to the user's own L1 address. No third party can choose the recipient of someone else's payout through core. Whether the deployed Universal Router or PositionManager filter recipients was not read.

What can be done: Routers and front ends can refuse the predeploy range 0x4200000000000000000000000000000000000000 to 0x42000000000000000000000000000000000007ff and the EntryPoint addresses as recipients of native payouts. Users who want ETH on L1 should take to their own account and withdraw from there. Nothing in core can be configured to prevent it.

Second reviewer's corrections: No change to actor or severity. The actor value unprivileged is right in the sense that no role is needed, and the reader should note that the only party who loses is the account that named the recipient, so this finding gives no path to funds of other users. Three additions. First, the value call succeeds on all seven chains, where the finding reports results for OP Mainnet, Base and Unichain only. Second, take(address(0), L2ToL1MessagePasser, 0) also succeeds, creates no debt because a zero delta is skipped (src/PoolManager.sol:369), and still makes the PoolManager start a zero value withdrawal and raise the message nonce. It carries empty data and the PoolManager address as target, which has no code on Ethereum, so it gives no authority on L1. Third, L1BlockNumber is a proxied predeploy, so the statement that no function pays the ETH out holds for the current implementation, and the chain's proxy admin could change that.

Code: `src/PoolManager.sol:291-297`, `src/types/Currency.sol:44-52`, `src/PoolManager.sol:279-288`, `src/PoolManager.sol:349-364`, `src/types/Currency.sol:60-86`.

Sources:

- https://raw.githubusercontent.com/ethereum-optimism/optimism/develop/packages/contracts-bedrock/src/L2/L2ToL1MessagePasser.sol (receive() calls initiateWithdrawal(msg.sender, RECEIVE_DEFAULT_GAS_LIMIT, bytes('')) with RECEIVE_DEFAULT_GAS_LIMIT = 100000)
- https://raw.githubusercontent.com/eth-infinitism/account-abstraction/v0.7.0/contracts/core/StakeManager.sol (EntryPoint receive() calls depositTo(msg.sender), balanceOf(account) returns deposits[account].deposit, and withdrawTo debits deposits[msg.sender])
- https://raw.githubusercontent.com/eth-infinitism/account-abstraction/v0.7.0/contracts/core/EntryPoint.sol (the EntryPoint debits a sender or paymaster deposit only in the validation step that calls validateUserOp or validatePaymasterUserOp on that address)
- https://raw.githubusercontent.com/ethereum-optimism/optimism/develop/packages/contracts-bedrock/src/legacy/L1BlockNumber.sol (L1BlockNumber receive() and fallback() are payable and return the L1 block number as one 32 byte word)
- https://mainnet.optimism.io (eth_call with the PoolManager as msg.sender and a separate tx.origin: a 0.001 ETH value call with empty calldata succeeds at L2ToL1MessagePasser, at the EntryPoint v0.6, v0.7 and v0.8, at L1BlockNumber and at the fee vaults, and reverts at L2StandardBridge. The same results were read on Base and Unichain.)
- https://ethereum-rpc.publicnode.com (eth_getCode at the seven L2 PoolManager addresses returns empty code on Ethereum, and eth_getBalance at 0x498581ff718922c3f8e6a244956af099b2652b2b returns 58773641109313318 wei)

### F-049. A payout sent to an EntryPoint, a precompile address or a protocol custody address is lost to the caller on Arc and Tempo

Low severity, confirmed. Effect: degrade. Who can trigger it: any account. Networks: Arc, Tempo.

What differs on the network: Arc and Tempo carry addresses that accept a payment from the PoolManager and book it to nobody the caller controls. On Arc the three ERC-4337 EntryPoint contracts accept native USDC with empty calldata and record it as a deposit of the sender. Precompile addresses 0x01 to 0x08 and 0x100, the codeless addresses 0x12 and 0x13 and the system log emitter 0xfffffffffffffffffffffffffffffffffffffffe accept value, and the USDC face accepts a transfer to the Native Coin Authority address and to its own implementation. On Tempo the FeeManager, StablecoinDEX and TIP20ChannelReserve precompile addresses hold TIP-20 balances for their own bookkeeping and accept a plain transfer without crediting an internal account.

How it meets the code: 1. A caller inside unlock calls take(currency, to, amount) (src/PoolManager.sol:291-297). The PoolManager debits the caller's delta by amount and then pays: for address(0) with a value call and empty calldata (src/types/Currency.sol:44-52), for a token with transfer(to, amount) (src/types/Currency.sol:55-86). 2. On Arc, if to is an EntryPoint, the EntryPoint credits a deposit to the PoolManager address. The PoolManager can never call withdrawTo and answers no validation call, so the deposit stays there. If to is 0x01, 0x12, the log emitter or the Native Coin Authority address, the USDC sits at an address without a spending path. 3. On Tempo, if to is 0xfeec..., 0xdec0... or 0x4d5050..., the TIP-20 balance of that precompile address rises by amount and no internal balance of any user is credited. I simulated each of the three with 1 unit of OUSD. I did not find a function that returns such a surplus and did not read the three precompiles in full. 4. In every case the caller still owes amount and must settle it before unlock returns (src/PoolManager.sol:112, 349-364). Pool reserves are whole: amount left and amount came back. 5. A caller who first calls sync(EntryPoint) on Arc, then takes native USDC to the EntryPoint and then calls settle is credited amount under the EntryPoint's address as currency id, because EntryPoint.balanceOf(PoolManager) is the deposit (src/PoolManager.sol:279-288, 358-360). An eth_call of sync(EntryPoint v0.7) on the deployed PoolManager succeeds. The EntryPoint has no transfer(address,uint256), so that credit can become an ERC-6909 claim and can never be taken.

What is at risk: The amount of each such payout is lost to the party that named the recipient. Other users, pool reserves and claims are not affected. The hazard is real for routers or scripts that let a user name any recipient, and for anyone who accepts ERC-6909 claims under the EntryPoint id.

What it takes: The caller, or a router acting for the caller, must name one of these addresses as recipient. No third party can redirect someone else's payout. On Tempo the native variant does not exist because value transfers fail.

What can be done: Routers and front ends on these two chains can refuse recipients in the precompile ranges, the EntryPoint addresses and the Tempo custody precompiles. Users should not accept ERC-6909 claims whose id is one of these addresses.

Second reviewer's corrections: The TIP20Factory address 0x20fc000000000000000000000000000000000000 also accepts a plain OUSD transfer from the PoolManager and its balance rises by the amount, so it belongs in the Tempo list. I tested value calls on 0x01, 0x04, 0x12, 0x100 and the log emitter and did not repeat 0x02, 0x03, 0x05 to 0x08 and 0x13. The actor value needs no change because no role is required. The only party that loses is the caller who names the recipient, or a person who accepts a claim under an EntryPoint id, so this item is no path to funds of other users.

Code: `src/PoolManager.sol:291-297`, `src/types/Currency.sol:44-52`, `src/types/Currency.sol:55-86`, `src/PoolManager.sol:279-288`, `src/PoolManager.sol:349-364`.

Sources:

- https://rpc.mainnet.arc.io (eth_call with from set to the PoolManager at blocks 32,582,357 to 32,584,426: empty calldata with 10^12 wei succeeds on 0x01 to 0x08, 0x12, 0x13, 0x100, the log emitter and the three EntryPoints; EntryPoint.balanceOf(PoolManager) returns 0; USDC.transfer of 1 unit to 0x1800...0000, 0xffff...fffe, 0x01, the EntryPoint v0.7 and the USDC implementation returns true)
- https://rpc.mainnet.tempo.xyz (eth_simulateV1 with from set to the PoolManager at block 50,287,321: OUSD.transfer of 1 unit to FeeManager, StablecoinDEX and TIP20ChannelReserve returns true and raises balanceOf of that address by 1 unit while the PoolManager balance falls by 1 unit)
- https://tempo.com/developers/docs/quickstart/predeployed-contracts.md (addresses and roles of FeeManager, StablecoinDEX and the other Tempo system contracts)

### F-050. The USDC implementation address on Arc mirrors the PoolManager's USDC balance, so a third currency id can be credited and never paid out

Low severity, confirmed. Effect: degrade. Who can trigger it: any account. Networks: Arc.

What differs on the network: On Arc the USDC proxy at 0x3600000000000000000000000000000000000000 delegates to NativeFiatTokenV2_2 at 0xc6ad664ac6679f4ce74e10e91449c93ec1ae3ca6. The implementation computes balanceOf from the account's native balance divided by 10^12, with no use of its own storage, so a direct call to the implementation returns the same figure as the proxy. Its transfer function calls the Native Coin Authority precompile, which accepts only the proxy address as caller, so a direct transfer on the implementation reverts. An ordinary ERC-20 implementation called directly reports a zero balance.

How it meets the code: 1. sync(X) accepts any address and stores X.balanceOf(PoolManager) (src/PoolManager.sol:279-288). With X set to the implementation address the stored figure is the PoolManager's real USDC balance in 6 decimals, 2,445,327.82 USDC at block 32,584,426. 2. Any USDC that reaches the PoolManager while X is synced, through USDC.transfer on the proxy or through a forced native send, raises X.balanceOf. settle then credits the difference to the caller under currency id X (src/PoolManager.sol:349-364). settle with msg.value reverts in that state (src/PoolManager.sol:356). 3. take(X, to, amount) calls transfer on the implementation (src/types/Currency.sol:55-86). The precompile rejects the call because its caller is the implementation and the take reverts with ERC20TransferFailed. 4. A positive delta in X can be minted as an ERC-6909 claim, cleared, or used as liquidity in a pool that names X as a currency (src/PoolManager.sol:310-336). None of these turns it back into USDC. 5. The same payment cannot also be credited under 0x3600 or address(0): one sync slot exists, a native credit needs that slot to be zero, and each inflow is counted in one settle. The USDC that was paid in stays in the PoolManager and backs no claim under address(0) or 0x3600.

What is at risk: USDC paid in under the implementation's id is stranded for the payer, and claims or pool positions denominated in that id can never be redeemed. Reserves of address(0) and 0x3600 pools are not reduced. The loss falls on whoever pays into that id or accepts claims in it. A proxy upgrade changes the implementation address and the behaviour of the old one.

What it takes: Someone must sync the implementation address and pay USDC before settling, or accept claims or a pool in that id. An attacker cannot make another user's router sync a different currency than the one it pays.

What can be done: Interfaces on Arc should list address(0) and 0x3600 as the only USDC currency ids and warn on pools or claims whose currency is 0xc6ad664ac6679f4ce74e10e91449c93ec1ae3ca6 or any later implementation address.

Second reviewer's corrections: The failed take surfaces as WrappedError with ERC20TransferFailed as its context (src/libraries/CustomRevert.sol:83-119, src/types/Currency.sol:82-86). As with finding 0, the loss falls on the party that pays into this id or accepts a claim or a pool in it. No other user is affected.

Code: `src/PoolManager.sol:279-288`, `src/PoolManager.sol:349-364`, `src/types/Currency.sol:55-86`, `src/types/Currency.sol:90-96`, `src/PoolManager.sol:322-336`.

Sources:

- https://sourcify.dev/server/v2/contract/5042/0xc6ad664ac6679f4ce74e10e91449c93ec1ae3ca6?fields=sources,abi,compilation (verified source of NativeFiatTokenV2_2: _balanceOf returns account.balance divided by 10^12 and _transfer calls NATIVE_COIN_AUTHORITY.transfer)
- https://raw.githubusercontent.com/circlefin/arc-node/main/crates/precompiles/src/native_coin_authority.rs (transfer, mint and burn revert unless the caller is the native fiat token address)
- https://rpc.mainnet.arc.io (eth_call at block 32,584,426 with from set to the PoolManager: balanceOf(PoolManager) on 0xc6ad664ac6679f4ce74e10e91449c93ec1ae3ca6 returns the proxy's figure, transfer(address,uint256) on it reverts, and eth_call of sync(0xc6ad...) and of sync(0x3600...) on the PoolManager succeeds while the manager is locked)

### F-006. Source disagrees with two interface comments and two test conditions, and none of the four changes who can move funds

Info severity, confirmed. Effect: degrade. Who can trigger it: any account. Networks: all 21 networks.

What differs on the network: None. These are differences inside the repository, between src and its own comments and tests.

How it meets the code: First, src/interfaces/IProtocolFees.sol:40 says collectProtocolFees reverts if the contract is unlocked. The code checks only the caller and whether the currency is the synced ERC-20 (src/ProtocolFees.sol:48-52). _isUnlocked is declared at ProtocolFees.sol:60 and implemented at src/PoolManager.sol:391-394 and nothing calls it. The tests agree with the code: they expect ProtocolFeeCurrencySynced in both lock states (test/PoolManager.t.sol:1001-1039). Second, src/interfaces/IPoolManager.sol:111 says only initialize and updateDynamicLPFee can be called without unlocking. sync has no onlyWhenUnlocked modifier (src/PoolManager.sol:279) and test/Sync.t.sol:36-41 calls it while locked. Third, test/libraries/Pool.t.sol:129 expects InvalidFeeForExactOut when amountSpecified >= 0 at a 100 percent fee, while src/libraries/Pool.sol:311-316 reverts only for amountSpecified > 0 and line 320 returns a zero delta for amountSpecified == 0. Fourth, Pool.t.sol:143 treats a zeroForOne price limit below MIN_SQRT_PRICE as out of bounds, while Pool.sol:328 also rejects a limit equal to MIN_SQRT_PRICE. I traced each one for a fund effect. Fee collection inside an unlock changes protocolFeesAccrued and the balance by the same amount and touches no delta. A sync outside an unlock only sets two transient slots that the next sync overwrites. The zero amount swap changes no state. The stricter limit keeps slot0.tick from reaching MIN_TICK - 1.

What is at risk: No loss or freeze found. A reader who trusts the two interface comments gets the wrong picture of when sync and fee collection can run. The fuzz test at Pool.t.sol:129 would fail on an input with amountSpecified equal to zero and a 100 percent fee if the fuzzer produces one.

What it takes: None for the mismatch itself. I could not run forge in this environment, so I do not know whether the current fuzz seed reaches the failing input.

What can be done: The deployer can correct the two comments, decide whether collectProtocolFees should use _isUnlocked or drop it, and align the two test conditions with the source.

Second reviewer's corrections: The fourth item cannot make the test fail. When the limit equals MIN_SQRT_PRICE the test takes neither branch and makes no swap call (test/libraries/Pool.t.sol:135-146), and test/utils/Deployers.sol:43 defines MIN_PRICE_LIMIT as MIN_SQRT_PRICE + 1, which matches the source. The third item is a failing input for the fuzz test whenever the fuzzer picks an LP fee of 1,000,000 together with amountSpecified 0. The setter setIsUnlocked in src/test/ProtocolFeesImplementation.sol:27-29 is also unused by any test, which is a further sign that a lock check on fee collection was planned or removed. ASSUMPTIONS.md A12 words the guard as unlocked and synced. The code applies it whenever the ERC-20 is synced, in both lock states.

Code: `src/ProtocolFees.sol:44-60`, `src/PoolManager.sol:279-288`, `src/PoolManager.sol:391-394`, `src/libraries/Pool.sol:311-330`.

Sources:

- src/interfaces/IProtocolFees.sol:40 (interface comment says collectProtocolFees reverts if the contract is unlocked)
- src/ProtocolFees.sol:48-52 (the only checks are the caller and the synced ERC-20 currency)
- src/interfaces/IPoolManager.sol:111 (interface comment lists initialize and updateDynamicLPFee as the only functions callable while locked)
- test/Sync.t.sol:36-41 (the test calls sync directly while the manager is locked and expects the synced currency to be set)
- test/libraries/Pool.t.sol:129 (test expects InvalidFeeForExactOut for amountSpecified >= 0 at 100 percent fee)
- test/libraries/Pool.t.sol:143 (test uses a strict less than comparison against MIN_SQRT_PRICE)

### F-014. sync runs while the manager is locked and fee collection ignores the lock, and the mainnet fee controller lets anyone trigger collection

Info severity, confirmed. Effect: degrade. Who can trigger it: any account. Networks: Ethereum.

What differs on the network: On mainnet the protocol fee controller is a V4FeeAdapter contract whose collect and triggerFeeUpdate functions have no access check. Any account can therefore make the PoolManager execute collectProtocolFees and setProtocolFee at a moment it chooses, including inside its own unlock callback. Mainnet also lets several users' operations share one transaction through ERC-4337 bundles and EIP-7702 batches.

How it meets the code: sync has no onlyWhenUnlocked modifier (src/PoolManager.sol:279-288), so anyone can set the synced currency and reserves at any point of a transaction, and the value stays until a settle or another sync in that transaction. collectProtocolFees checks the caller and then reverts only if the currency is an ERC-20 equal to the synced currency (src/ProtocolFees.sol:48-52). It never calls _isUnlocked, which is declared at src/ProtocolFees.sol:60 and implemented at src/PoolManager.sol:391-394 with no caller. ASSUMPTIONS.md A12 describes the guard as depending on the unlocked state; the code does not. I walked the fund-moving paths for a gain and found none. Collection of the synced ERC-20 is blocked regardless of lock state, so the balance cannot fall between a sync and its settle through this path. Native settlement uses msg.value and no balance (src/PoolManager.sol:353-354). Collection is bounded by protocolFeesAccrued with checked subtraction (src/ProtocolFees.sol:54-55) and the adapter fixes the recipient. A sync left behind by an earlier operation in a bundle is overwritten by the next sync and cleared by the next ERC-20 settle (src/PoolManager.sol:361). What remains is that a stale sync makes a later native settle with value revert with NonzeroNativeValue if its caller did not sync first (src/PoolManager.sol:356), and makes collection of that currency revert for the rest of the transaction.

What is at risk: No loss or lasting freeze found. Within one transaction, a party that runs earlier can make a later native settle or a fee collection revert.

What it takes: For the revert cases the two parties must share a transaction, for example an ERC-4337 bundle, and the later party must settle native currency without calling sync first. This is my own reading of the code and has not been checked by a second reviewer.

What can be done: Integrators should call sync immediately before every settle, including native, as the comment at src/PoolManager.sol:348 says. The deployer can decide whether sync should require the unlocked state and whether collectProtocolFees should check it, and can correct the A12 text either way.

Second reviewer's corrections: The code facts hold on every network. Only the permissionless controller is specific to mainnet. The repository's own tests expect the present behaviour, so the disagreement is between the code and two texts: the comment at src/interfaces/IProtocolFees.sol:40 and assumption A12. The synced check as written rejects collection in more situations than a check tied to the lock would, so the difference removes no protection.

Code: `src/PoolManager.sol:279-288`, `src/ProtocolFees.sol:44-57`, `src/ProtocolFees.sol:60`, `src/PoolManager.sol:391-394`, `src/PoolManager.sol:349-364`.

Sources:

- https://sourcify.dev/server/v2/contract/1/0x89a5d5bf00a27d55c02951e49078a5c5771051db?fields=sources,abi,compilation (V4FeeAdapter source (exact match): collect(CollectParams[]) and triggerFeeUpdate(PoolKey) have no access modifier and call POOL_MANAGER.collectProtocolFees(TOKEN_JAR, currency, amount) and POOL_MANAGER.setProtocolFee(poolKey, fee))
- https://ethereum-rpc.publicnode.com (eth_call at block 26470380: PoolManager.protocolFeeController() = 0x89a5d5bf00a27d55c02951e49078a5c5771051db; adapter TOKEN_JAR() = 0xf38521f130fccf29db1961597bc5d2b60f995f85; adapter owner() and feeSetter() = timelock)
- https://sourcify.dev/server/v2/contract/1/0xf38521f130fccf29db1961597bc5d2b60f995f85?fields=sources,compilation (TokenJar has an empty receive function and a release function restricted to the releaser, so native fee collection does not hand control to an arbitrary party)
- https://raw.githubusercontent.com/ethereum/ERCs/master/ERCS/erc-4337.md (a bundle is one transaction and transient storage persists across the UserOperations in it)

## Findings that need a privileged party

These are outside the threat model and are listed for reference. Full text is in `FINDINGS.md`.

| ID | Needs | Severity | Status | Networks | Finding |
|---|---|---|---|---|---|
| F-003 | author of a hook or token the victims use | medium | confirmed | Arbitrum One | A Stylus program used as a hook or token stops answering calls on expiry or a Stylus version change, and activation is blocked |
| F-004 | author of a hook or token the victims use | medium | confirmed | all 21 networks | A pool's hook can block or reprice every liquidity removal in that pool, and core has no path that skips the hook |
| F-005 | author of a hook or token the victims use | medium | confirmed | all 21 networks | Uncollected fees above the int128 maximum make every later update of a liquidity position revert |
| F-013 | author of a hook or token the victims use | medium | confirmed | Ethereum | EIP-7702 lets the code behind a hook address be replaced or removed after a pool is created |
| F-018 | author of a hook or token the victims use | low | confirmed | MegaETH | On MegaETH a caller can make every block field and oracle read revert inside hook and token sub-calls, and one such read caps the rest of the transaction at 20 million compute gas |
| F-040 | author of a hook or token the victims use | low | confirmed | Avalanche | Avalanche C-Chain folds two storage slot indexes into one, which lets a hook author hide a write path that Ethereum does not have |
| F-051 | author of a hook or token the victims use | low | confirmed | Tempo | A delegated session credential with a TIP-20 spending limit on Tempo can move the account's ERC-6909 claims and pool positions without limit |
| F-002 | token issuer or admin | high | confirmed | Robinhood Chain | Robinhood Stock Tokens and USDG let the issuer block, pause, burn or upgrade the tokens held by the PoolManager |
| F-011 | token issuer or admin | high | confirmed | Ethereum | One issuer blocklist entry on the PoolManager address freezes or wipes a stablecoin for every pool |
| F-015 | token issuer or admin | high | confirmed | Monad | Role holders on GHO, syrupUSDC, apxUSD, shMON and mUSD can pause, burn, move or replace balances that the Monad PoolManager holds |
| F-019 | token issuer or admin | high | confirmed | HyperEVM | USDC and USDT0 issuers can block the PoolManager address, which stops every pool in that currency, and USDT0's owner can burn the blocked balance |
| F-027 | token issuer or admin | high | confirmed | Base | B20 precompile tokens on Base give the issuer seize, pause and policy control over the PoolManager balance, and their rules change at hard forks |
| F-028 | token issuer or admin | high | confirmed | Optimism, Base, Unichain, Worldchain, Ink, Soneium | Blacklist and freeze roles on the pooled stablecoins can stop every pool that holds them, because one address holds all balances |
| F-031 | token issuer or admin | high | confirmed | Tempo | TIP-20 issuer roles can burn, freeze or pause the PoolManager balance of a Tempo stablecoin |
| F-032 | token issuer or admin | high | confirmed | Arc | A pause of the USDC token on Arc stops the ERC-20 face and leaves native transfers open over the same PoolManager balance |
| F-036 | token issuer or admin | high | confirmed | Arbitrum One | Issuer block lists on USDC, USDT0, PYUSD and cbBTC cover the single PoolManager address on Arbitrum One |
| F-007 | token issuer or admin | medium | confirmed | BNB Smart Chain | Scheduled Jenner fork adds protocol-native tokens whose issuer can seize, pause or block the PoolManager balance |
| F-043 | token issuer or admin | medium | confirmed | HyperEVM | stHYPE and wstHYPE are two currency ids over one share balance, so a loss in the rebasing face is paid from the shares of pools in the other face |
| F-035 | token issuer or admin | low | confirmed | Elysium | Elysium USDC is a bridge representation whose backing on HyperEVM sits at one address that the issuer can block |
| F-001 | sequencer, validator or bridge committee | high | confirmed | Robinhood Chain | Operator transaction filtering on Robinhood Chain can fail any exit from the PoolManager, including force-included ones |
| F-046 | sequencer, validator or bridge committee | high | confirmed | X Layer | X Layer voids blacklisted L1 deposits at the execution layer, so forced inclusion is no guaranteed exit from the PoolManager |
| F-020 | sequencer, validator or bridge committee | medium | plausible | HyperEVM | The AQAv2 treasury address that HyperCore sends unsigned transfers from has no HyperCore account, so it was named by a deployer and is a different address from the signer |
| F-009 | sequencer, validator or bridge committee | low | confirmed | BNB Smart Chain, Avalanche | Thirteen Wormhole guardians can act as PoolManager owner on BNB Smart Chain and Avalanche |
| F-010 | sequencer, validator or bridge committee | low | confirmed | Polygon | Polygon state sync path lets the Heimdall validator set act as PoolManager owner |
| F-016 | sequencer, validator or bridge committee | low | confirmed | Monad, MegaETH | Thirteen Wormhole guardians can act as PoolManager owner on Monad and MegaETH |
| F-017 | sequencer, validator or bridge committee | low | confirmed | MegaETH | MegaETH has one sequencer, so an exit from the PoolManager that it refuses to include depends on L1 forced inclusion with a 12 hour bound |
| F-022 | sequencer, validator or bridge committee | low | confirmed | HyperEVM | The owner on HyperEVM is a Wormhole message receiver, so a guardian quorum can exercise the owner role |
| F-024 | sequencer, validator or bridge committee | low | plausible | X Layer | X Layer block builder can exclude PoolManager transactions through a rule driven risk control filter, which leaves L1 deposits as the exit |
| F-030 | sequencer, validator or bridge committee | low | confirmed | Soneium | Soneium restricts listed contracts at its own RPC and sequencer, which leaves L1 forced inclusion as the exit for pools that touch a listed token or hook |
| F-034 | sequencer, validator or bridge committee | low | confirmed | Tempo, Arc | PoolManager ownership on Tempo and Arc is exercised through Wormhole guardian signatures |
| F-023 | owner, fee controller or chain governance | high | confirmed | Celo | Celo governance can move native CELO out of the PoolManager through the CELO token proxy and the transfer precompile |
| F-026 | owner, fee controller or chain governance | medium | confirmed | Celo, X Layer | PoolManager ownership on Celo and X Layer rests on the upgradeable L2CrossDomainMessenger, and on X Layer a 2 of 3 Safe of EOAs can upgrade it |
| F-029 | owner, fee controller or chain governance | medium | confirmed | Optimism, Base, Unichain, Zora, Worldchain, Ink, Soneium | PoolManager ownership rests on an upgradeable messenger predeploy on five chains and on the portal alias on two, and a takeover reaches protocol fees only |
| F-045 | owner, fee controller or chain governance | low | confirmed | HyperEVM | The MRB hard fork raised the price of seven precompiles by 5 to 40 times, which can push a hook past the 3,000,000 gas fast block |
| F-052 | owner, fee controller or chain governance | low | confirmed | Arc | Arc keeps a denylist contract whose owner can keep transactions that name a listed sender or target out of the mempool |

## The 21 networks as read from chain

| Network | Chain ID | PoolManager | Code size | Code group | Block gas limit | Fee controller set |
|---|---|---|---|---|---|---|
| Ethereum | 1 | `0x000000000004444c5dc75cB358380D2e3dE08A90` | 24009 | A | 59,999,943 | yes |
| Optimism | 10 | `0x9a13f98cb987694c9f086b1f5eb990eea8264ec3` | 24009 | A | 40,000,000 | yes |
| Base | 8453 | `0x498581ff718922c3f8e6a244956af099b2652b2b` | 24009 | A | 40,000,000 | yes |
| Unichain | 130 | `0x1f98400000000000000000000000000000000004` | 24050 | B | 60,000,000 | no |
| Zora | 7777777 | `0x0575338e4c17006ae181b47900a84404247ca30f` | 24009 | A | 30,000,000 | no |
| Worldchain | 480 | `0xb1860d529182ac3bc1f51fa2abd56662b7d13f33` | 24009 | A | 280,000,000 | no |
| Ink | 57073 | `0x360e68faccca8ca495c1b759fd9eee466db9fb32` | 24009 | A | 30,000,000 | no |
| Soneium | 1868 | `0x360e68faccca8ca495c1b759fd9eee466db9fb32` | 24009 | A | 40,000,000 | no |
| Celo | 42220 | `0x288dc841A52FCA2707c6947B3A777c5E56cd87BC` | 24009 | A | 30,000,000 | no |
| X Layer | 196 | `0x360e68faccca8ca495c1b759fd9eee466db9fb32` | 24009 | A | 210,000,000 | no |
| Arbitrum One | 42161 | `0x360e68faccca8ca495c1b759fd9eee466db9fb32` | 24009 | A | 1,125,899,906,842,624 | yes |
| Robinhood Chain | 4663 | `0x8366a39cc670b4001a1121b8f6a443a643e40951` | 24009 | A | 1,125,899,906,842,624 | yes |
| Elysium | 99901 | `0xE2e105d3F7209A9DA11f83cCf3E7398a753823F1` | 24009 | A | 1,125,899,906,842,624 | no |
| Polygon | 137 | `0x67366782805870060151383f4bbff9dab53e5cd6` | 24009 | A | 160,000,000 | yes |
| BNB Smart Chain | 56 | `0x28e2ea090877bf75740558f6bfb36a5ffee9e9df` | 24009 | A | 80,000,000 | yes |
| Avalanche | 43114 | `0x06380c0e0912312b5150364b9dc4542ba0dbbc85` | 24009 | A | 80,000,000 | no |
| Monad | 143 | `0x188d586ddcf52439676ca21a244753fa19f9ea8e` | 24009 | A | 150,000,000 | no |
| MegaETH | 4326 | `0xacb7e78fa05d562e0a5d3089ec896d57d057d38e` | 24009 | A | 10,000,000,000 | no |
| Tempo | 4217 | `0x33620f62c5b9b2086dd6b62f4a297a9f30347029` | 24009 | A | 500,000,000 | no |
| Arc | 5042 | `0x8366a39CC670B4001A1121B8F6A443A643e40951` | 24009 | A | 30,000,000 | yes |
| HyperEVM | 999 | `0x12D4Fd9C5DeDd00ab8a0bCe2CF0167bbf94b6B1F` | 24009 | A | 3,000,000 | no |

Code group compares the deployed bytecode after blanking the contract's own address. Networks in the same group run the same code.

## Where the evidence is

- `FINDINGS.md`: every finding in full, including the out-of-scope ones.
- `CLEARED.md`: the 332 checks that came out safe, with the reason for each.
- `STATUS.md`: coverage per network and lens, open leads, cycle history.
- `cycles/NNN/`: the raw research and verdict files of each cycle.
