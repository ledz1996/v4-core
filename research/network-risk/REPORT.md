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

### F-021. A payout sent to a HyperCore bridge address is credited to the PoolManager's HyperCore account and cannot be recovered

Low severity, confirmed. Effect: freeze. Who can trigger it: any account. Networks: HyperEVM.

What differs on the network: HyperEVM has bridge addresses where a plain transfer moves funds to HyperCore and credits the sender of the transfer. HYPE sent as value to 0x2222222222222222222222222222222222222222 is credited to msg.sender. A linked ERC-20 sent to its system address (0x20 followed by the token index, for example 0x200000000000000000000000000000000000010c for USDT0) is credited to the from address of the Transfer event. Ethereum has no address where a transfer re-homes funds on another ledger under the sender's name.

How it meets the code: 1. Every payout from pools is sent by the PoolManager itself. take debits the caller's delta and then transfers to the recipient the caller chose (src/PoolManager.sol:291-297). collectProtocolFees does the same for a recipient chosen by the fee controller (src/ProtocolFees.sol:44-57). 2. For the native asset the transfer is a value call with empty calldata (src/types/Currency.sol:48). The code at 0x2222222222222222222222222222222222222222 accepts exactly that shape and emits Received(msg.sender, msg.value), and msg.sender is the PoolManager. For an ERC-20 the PoolManager calls transfer on the token (src/types/Currency.sol:60-75) and the token logs the PoolManager as from. 3. HyperCore credits the PoolManager address in both cases. 4. The PoolManager can never act on HyperCore. It cannot sign, and its only outbound calls are unlockCallback to msg.sender (src/PoolManager.sol:110), hook selectors to the hook address (src/libraries/Hooks.sol:131-155), transfer and balanceOf to a currency address (src/types/Currency.sol:60-75 and 94) and empty calldata value calls (src/types/Currency.sol:48). CoreWriter accepts only selector 0x17938e13 and reverts on anything else. 5. The caller's delta is debited before the transfer, so the caller pays in full for what gets stranded. An attacker gains nothing from doing this on purpose.

What is at risk: The swapper, LP or fee recipient whose payout was directed to a bridge address loses it for good. Pool reserves stay whole. A router or front end that tries to deliver swap output to HyperCore by passing the bridge address as the take recipient would strand every such payout. At the time of the review the PoolManager's HyperCore spot balance list was empty.

What it takes: A caller or an integration passes 0x2222222222222222222222222222222222222222 or a token system address as the recipient of take or collectProtocolFees.

What can be done: Routers and front ends should reject 0x2222222222222222222222222222222222222222 and addresses with the 0x20 system prefix as take recipients. To move output to HyperCore, take to the user or to the router first and bridge from that address. The fee controller should apply the same rule to collectProtocolFees recipients.

Second reviewer's corrections: The statement that a linked ERC-20 is credited to the from address of the Transfer log goes one step beyond the docs page, which says the credit is based on the emitted Transfer log. It is the natural reading and it was not tested. The USDC case differs from USDT0 as described above. The loss falls on the caller who chose the recipient and gives an attacker nothing, so low is the right level.

Code: `src/PoolManager.sol:291-297`, `src/PoolManager.sol:110`, `src/types/Currency.sol:48`, `src/types/Currency.sol:60-75`, `src/ProtocolFees.sol:44-57`, `src/libraries/Hooks.sol:131-155`.

Sources:

- https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm/hypercore-less-than-greater-than-hyperevm-transfers (The address 0x222..2 emits Received(address indexed user, uint256 amount) where user is msg.sender, and linked tokens sent to their system address are credited on HyperCore from the emitted Transfer(from, to, value) event.)
- https://rpc.hyperliquid.xyz/evm eth_getCode 0x2222222222222222222222222222222222222222 (The bridge code emits topic 0x88a5966d370b9919b20f3e2c13ff65706f196a4e32cc2c12bf57088f88525874 with caller and call value when calldata is empty and reverts otherwise.)
- https://rpc.hyperliquid.xyz/evm eth_getCode 0x3333333333333333333333333333333333333333 (CoreWriter dispatches only selector 0x17938e13 (sendRawAction) and reverts on every other selector.)
- https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm/interacting-with-hypercore (CoreWriter actions are sent on behalf of the calling contract's own address on HyperCore.)
- https://api.hyperliquid.xyz/info (POST type spotClearinghouseState for the PoolManager address) (The PoolManager address had no HyperCore spot balances on 22 November 2026.)
- https://api.hyperliquid.xyz/info (POST type spotMeta) (USDT0 has token index 268 and is linked to 0xb8ce59fc3717ada4c02eadf9682a9e934f625ebb, and HYPE has no linked EVM contract.)

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
| F-002 | token issuer or admin | high | confirmed | Robinhood Chain | Robinhood Stock Tokens and USDG let the issuer block, pause, burn or upgrade the tokens held by the PoolManager |
| F-011 | token issuer or admin | high | confirmed | Ethereum | One issuer blocklist entry on the PoolManager address freezes or wipes a stablecoin for every pool |
| F-015 | token issuer or admin | high | confirmed | Monad, MegaETH | Blacklist and freeze roles on pooled stablecoins can stop every pool that holds them on Monad and MegaETH |
| F-019 | token issuer or admin | high | confirmed | HyperEVM | USDC and USDT0 issuers can block the PoolManager address, which stops every pool in that currency, and USDT0's owner can burn the blocked balance |
| F-027 | token issuer or admin | high | confirmed | Base | B20 precompile tokens on Base give the issuer seize, pause and policy control over the PoolManager balance, and their rules change at hard forks |
| F-028 | token issuer or admin | high | confirmed | Optimism, Base, Unichain, Worldchain, Ink, Soneium | Blacklist and freeze roles on the pooled stablecoins can stop every pool that holds them, because one address holds all balances |
| F-031 | token issuer or admin | high | confirmed | Tempo | TIP-20 issuer roles can burn, freeze or pause the PoolManager balance of a Tempo stablecoin |
| F-032 | token issuer or admin | high | confirmed | Arc | Circle's blocklist covers native USDC on Arc, so one entry for the PoolManager freezes native and ERC-20 USDC pools together |
| F-007 | token issuer or admin | medium | confirmed | BNB Smart Chain | Scheduled Jenner fork adds protocol-native tokens whose issuer can seize, pause or block the PoolManager balance |
| F-001 | sequencer, validator or bridge committee | high | confirmed | Robinhood Chain | Operator transaction filtering on Robinhood Chain can fail any exit from the PoolManager, including force-included ones |
| F-009 | sequencer, validator or bridge committee | low | confirmed | BNB Smart Chain, Avalanche | Thirteen Wormhole guardians can act as PoolManager owner on BNB Smart Chain and Avalanche |
| F-010 | sequencer, validator or bridge committee | low | confirmed | Polygon | Polygon state sync path lets the Heimdall validator set act as PoolManager owner |
| F-016 | sequencer, validator or bridge committee | low | confirmed | Monad, MegaETH | Thirteen Wormhole guardians can act as PoolManager owner on Monad and MegaETH |
| F-017 | sequencer, validator or bridge committee | low | confirmed | MegaETH | MegaETH has one sequencer, so an exit from the PoolManager that it refuses to include depends on L1 forced inclusion with a 12 hour bound |
| F-020 | sequencer, validator or bridge committee | low | plausible | HyperEVM | HyperCore sends unsigned system transactions from addresses outside the system range, which moves ERC-20 balances without any call by the holder |
| F-022 | sequencer, validator or bridge committee | low | confirmed | HyperEVM | The owner on HyperEVM is a Wormhole message receiver, so a guardian quorum can exercise the owner role |
| F-024 | sequencer, validator or bridge committee | low | plausible | X Layer | X Layer block builder can exclude PoolManager transactions through a rule driven risk control filter, which leaves L1 deposits as the exit |
| F-030 | sequencer, validator or bridge committee | low | confirmed | Soneium | Soneium restricts listed contracts at its own RPC and sequencer, which leaves L1 forced inclusion as the exit for pools that touch a listed token or hook |
| F-034 | sequencer, validator or bridge committee | low | confirmed | Tempo, Arc | PoolManager ownership on Tempo and Arc is exercised through Wormhole guardian signatures |
| F-023 | owner, fee controller or chain governance | high | confirmed | Celo | Celo governance can move native CELO out of the PoolManager through the CELO token proxy and the transfer precompile |
| F-026 | owner, fee controller or chain governance | medium | confirmed | Celo, X Layer | PoolManager ownership on Celo and X Layer rests on the upgradeable L2CrossDomainMessenger, and on X Layer a 2 of 3 Safe of EOAs can upgrade it |
| F-029 | owner, fee controller or chain governance | medium | confirmed | Optimism, Base, Unichain, Zora, Worldchain, Ink, Soneium | PoolManager ownership rests on an upgradeable messenger predeploy on five chains and on the portal alias on two, and a takeover reaches protocol fees only |

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
- `CLEARED.md`: the 158 checks that came out safe, with the reason for each.
- `STATUS.md`: coverage per network and lens, open leads, cycle history.
- `cycles/NNN/`: the raw research and verdict files of each cycle.
