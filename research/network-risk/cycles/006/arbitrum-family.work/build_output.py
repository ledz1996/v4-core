import json

ARB = "https://arb1.arbitrum.io/rpc"
RH = "https://rpc.mainnet.chain.robinhood.com"
EL = "https://rpc.elysium.kinetiq.xyz"
NITRO = "https://raw.githubusercontent.com/OffchainLabs/nitro/v3.12.4/"
GETH = "https://raw.githubusercontent.com/OffchainLabs/go-ethereum/0e44603/"
DOC_FILTER = "https://docs.arbitrum.io/launch-arbitrum-chain/chain-config/sequencer/compliance-filtering"
AUDITS = "https://docs.arbitrum.io/audit-reports"
Q = "queried 2026-11-23"

profiles = []


def prof(cid, lens, summary, deltas):
    profiles.append({"chainId": cid, "lens": lens, "summary": summary, "deltas": deltas})


def d(delta, source, relevance):
    return {"delta": delta, "source": source, "relevance": relevance}


# ---------------------------------------------------------------- Arbitrum One
prof(42161, "L1",
     "The live node still reports the unpublished build v3.13.0-rc.9 and ArbOS 61, and no upgrade is scheduled. The one new execution fact is how the fork resolves an EIP-7702 delegation that points at a precompile. The audit list of the chain gained five reports since July and none of them describes a change to call semantics.",
     [
         d("At fork commit 0e44603 resolveCode returns no code when an EIP-7702 delegation points at a precompile address and the ArbOS version is 50 or higher (core/vm/evm.go lines 789 to 806). The ArbOS precompiles count as precompiles here. Probe: with the designator 0xef0100 followed by 0x64 (ArbSys), 0x6e (ArbRetryableTx) or 0x02 placed at a test address by state override, and a forwarding stub at the PoolManager address, the calls transfer(address,uint256), balanceOf(address) and empty calldata each return success with zero bytes of return data.",
           GETH + "core/vm/evm.go; " + ARB + " eth_call with state overrides, " + Q, "low"),
         d("Signed transactions that arrive in a parent chain message are rejected when their type is 0x64 or higher or when they are blob transactions (arbos/parse_l2.go lines 161 to 175). Types 0, 1, 2 and 4 are accepted, so a set code transaction can enter through the sequencer and through the delayed inbox.",
           NITRO + "arbos/parse_l2.go", "none"),
         d("The audit report index lists these reports dated after the ArbOS 60 and 61 review: Sequencer Feed Ticketing and Upgrade Action Contract (2026-07-31), Yield Bearing Bridge (2026-08-07), Tip Collection Toggler (2026-08-14), OSP Soundness Guard (2026-09-15), Glamsterdam Gas Parameters (2026-10-19) and Stylus Permissioned Deployer (2026-11-06). I read the Glamsterdam report, which covers a governance payload for two parent chain pricing parameters and reports no issue. I did not open the other four.",
           AUDITS + " and https://docs.arbitrum.io/audit-reports/2026_10_19_trail_of_bits_glamsterdam_gas_parameters_summary_report.pdf, fetched 2026-11-23", "none"),
         d("The Trail of Bits review of ArbOS 50 and 51 (2025-12-01) has six findings. The highest is a medium finding about a possible underflow inside the gas charging hook, and the others concern the block gas limit during an upgrade block, a bounds check on scheduled transactions and error handling. None concerns value transfer, call dispatch or transient storage.",
           "https://docs.arbitrum.io/audit-reports/2025_12_01_trail_of_bits_arbos_50_and_51_security_review.pdf, fetched 2026-11-23", "none"),
     ])

prof(42161, "L2",
     "Every transaction type of the pinned fork was walked again for the sender, the value and the transient map that the PoolManager would see. The walk found one inexact statement in the cycle 2 record and no path that differs from Ethereum for unlock, sync, settle or take.",
     [
         d("The start block internal transaction makes one contract call. ApplyInternalTxUpdate calls core.ProcessParentBlockHash for ArbOS 40 and later (arbos/internal_tx.go lines 73 to 87), which calls the EIP-2935 history contract from the system address 0xfffffffffffffffffffffffffffffffffffffffe. ProcessParentBlockHash calls StateDB.Prepare before that call (core/state_processor.go line 358), so the call runs with an empty transient map. The cycle 2 item said the start hook contains no contract call. The conclusion of that item is unchanged, because the callee is a fixed contract that makes no calls.",
           NITRO + "arbos/internal_tx.go and " + GETH + "core/state_processor.go", "none"),
         d("Unsigned transactions, contract transactions, deposits and retryable submissions take their sender from the Poster field of the parent chain message header, which the Bridge contract records as the aliased caller (arbos/parse_l2.go lines 32, 47, 245 to 264, 292 and 364). A call with msg.sender equal to the zero address would need the parent chain caller 0xeeeeffffffffffffffffffffffffffffffffeeef. That address has no code, nonce 0 and balance 0 on Ethereum.",
           NITRO + "arbos/parse_l2.go; https://ethereum-rpc.publicnode.com eth_getCode, eth_getTransactionCount and eth_getBalance, " + Q, "none"),
         d("A transaction whose hash is on the on-chain filter list executes no contract code. RevertedTxHook raises the sender nonce, consumes all remaining gas and returns an error before the top call (arbos/tx_processor.go lines 1089 to 1105, core/state_transition.go line 964). A filtered deposit is minted and sent to the filtered funds recipient (tx_processor.go lines 247 to 268). The list is empty of writers on Arbitrum One.",
           NITRO + "arbos/tx_processor.go and " + GETH + "core/state_transition.go", "none"),
     ])

prof(42161, "L3",
     "The PoolManager balances of the 845 priced pool currencies were read and ranked. Two of the six largest positions were missing from the issuer finding: Global Dollar (USDG) and the Dinari USD+ token, which is a share based token whose index only the issuer's operator moves. The token that reports the symbol xUSD is the Overnight rebasing token and the PoolManager holds 62 units of it.",
     [
         d("Ranking by value from live balanceOf(PoolManager) reads and the cycle 5 price list: 9.07M USDC, 31.40 WBTC, 1.71M USDG (0x004b506865409877c9fa29bfb1eba929984b9bbc), 1.07M USD+ (0xfc90518d5136585ba45e34ed5e1d108bd3950cfa), 15.22 cbBTC, 0.90M USDT0, 17.7M VSN, 2.81M ARB, 4.24M ESP, 392,004 DOT, 167,872 PENDLE, 41,953 UNI, 13,073 LINK, 51.97 wstETH, 12.5M WOO, 1,027 AAVE, 1,250 wSOL, 5.46M HDN, 48.70 WETH and 907,132 EQB, plus 4,425.84 native ETH. The price list also values 2.06 billion units of a token named Varlamore USDC Growth (0x2ba39e5388ac6c702cb29aea78d52aa66832f1ee) at 4.37M USD and 27,475 EVA at 0.98M USD. I did not confirm those two prices. The list covers 845 of 9,420 pool currencies, the ones that have a price.",
           ARB + " eth_call balanceOf in batches and eth_getBalance, " + Q + "; price list research/network-risk/cycles/005/theme-assigned-balance.work/raw/prices_42161.json.gz", "high"),
         d("USD+ at 0xfc90518d5136585ba45e34ed5e1d108bd3950cfa is an EIP-1967 proxy with implementation 0xff5bff8081eaee966bd74e9c0c059949df2345e1 and publicVersion 6.0.0. totalSupply is 3,113,037.91, balancePerShare is 1.070678e18, sharesOf(PoolManager) is 999,999.89 and balanceOf(PoolManager) is 1,070,677.64, which is 34.4 percent of the supply. transferRestrictor() is 0x2ed5c85d5105abe5d13586c5c3a8f99a837942b4 with owner 0x269e944ad9140fc6e21794e8ea71ce1afbfe38c8, and isBlacklisted(PoolManager) is false. From an ordinary account rebaseAdd(uint128,bytes32) and rebaseSub(uint128,bytes32) revert with AC: unauthorized, and mint(address,uint256) and burn(address,uint256) revert. The token emitted 27 Transfer and 28 Approval logs and no index event in the last 40,000,000 blocks.",
           ARB + " eth_call, eth_getStorageAt and eth_getLogs, " + Q + "; https://raw.githubusercontent.com/dinaricrypto/usdplus-contracts/main/src/UsdPlus.sol", "high"),
         d("USDG at 0x004b506865409877c9fa29bfb1eba929984b9bbc answers isFrozen(PoolManager) with false and paused() with false, has owner 0x6c9e821ade9efc1bcda763f9942dd7822d6e86b4, a total supply of 65.79M and balanceOf(PoolManager) of 1,712,030.85. payoutGroupIdOf(PoolManager) is 0.",
           ARB + " eth_call, " + Q, "high"),
         d("0xe80772Eaf6e2E18B651F160Bc9158b2A5caFCA65 reports name and symbol xUSD, 6 decimals, a total supply of 112,075 and the functions rebasingCreditsPerToken, rebasingCreditsPerTokenHighres and nonRebasingSupply. rebaseState(PoolManager) is 0 and creditsBalanceOf(PoolManager) returns the global credits per token, so the PoolManager balance of 62.35 units follows rebases.",
           ARB + " eth_call, " + Q, "low"),
     ])

prof(42161, "L4",
     "Transaction filtering is switched off on Arbitrum One: no filterer account exists and no filtering start time is set. Tips are collected. The node answers simulated calls that involve a restricted address on Robinhood Chain without applying a filter, so simulation on these chains says nothing about sequencer policy.",
     [
         d("ArbOwnerPublic returns an empty list for getAllTransactionFilterers(), zero for getTransactionFilteringFrom() and getFilteredFundsRecipient(), an empty list for getAllNativeTokenOwners(), zero for getNativeTokenManagementFrom() and true for getCollectTips(). The chain owners are 0x8f59c7a53b883563b34cbbb6ff021b03973e823a, 0x6e031b6e9f667ed6953e627276fbbefa4c28529a and 0x4323dab775cc15e386fdac591a39420db6226a63.",
           ARB + " eth_call to 0x000000000000000000000000000000000000006b, " + Q, "low"),
         d("protocolFeesAccrued(address(0)) on the PoolManager is 0.0109 ETH, and the fee controller and owner are unchanged from state/networks.json.",
           ARB + " eth_call to 0x360e68faccca8ca495c1b759fd9eee466db9fb32, " + Q, "none"),
     ])

# ------------------------------------------------------------- Robinhood Chain
prof(4663, "L1",
     "Same build and ArbOS version as Arbitrum One. The restricted wallet that accounts for most filter entries is an EIP-7702 delegated account, and 405 of the filtered transactions are set code transactions sent through the delayed inbox.",
     [
         d("eth_getCode of 0x42607b2e4fde22e83822d4a86ddac58d847dc289 returns 0xef01008a67b5020ee254ef48e3b6a04927f39baf7e408a, a delegation designator. Of the 1,491 filtered transactions found on chain, 889 have type 0x2, 405 type 0x4, 83 type 0x66, 62 type 0x69, 46 type 0x65, 5 type 0x0 and 1 type 0x64.",
           RH + " eth_getCode, eth_getTransactionByHash for every hash in the filter logs, " + Q, "low"),
         d("The delegation probe described for Arbitrum One gave the same result on this chain: an account delegated to 0x64, 0x6e or 0x02 answers transfer, balanceOf and empty calldata from the PoolManager address with success and no return data.",
           RH + " eth_call with state overrides, " + Q, "low"),
     ])

prof(4663, "L2",
     "The filter list was read from chain in full. Every entry is the hash of a transaction that came through the delayed inbox, one account adds them, and 1,389 of the 1,491 executed entries name one wallet as sender, recipient or calldata argument. No entry targets the PoolManager or its periphery. One retryable submission kept the delayed inbox from advancing for 79 minutes on 2026-07-15.",
     [
         d("Precompile 0x74 emitted 6,234 FilteredTransactionAdded logs and no FilteredTransactionDeleted log between block 591,078 (2026-06-30) and block 118,825,042 (2026-11-20), read up to block 121,401,349. They name 1,493 distinct hashes. 1,491 of the hashes are transactions on chain and each has status 0. gasUsed equals the gas limit for all of them except three retryable submissions. Two hashes never appeared. I read 6,231 of the 6,234 add transactions (three lookups returned nothing) and all were sent by 0xebdc18a1f5c42fc25552ea233facf4054df224b7 with selector 0xcb470491, and getAllTransactionFilterers() returns that one account.",
           RH + " eth_getLogs on 0x0000000000000000000000000000000000000074 in ranges of 500,000 blocks, eth_getTransactionByHash and eth_getTransactionReceipt, eth_call to 0x6b, " + Q, "high"),
         d("The filtered transaction executes a median of 10 blocks after the first add log for its hash, and at least 1 block after. 1,001 filtered transactions were sent by 0x42607b2e4fde22e83822d4a86ddac58d847dc289 or by its alias 0x53717b2e4fde22e83822d4a86ddac58d847dd39a, 244 were sent to that wallet by others, 144 carry it in calldata (for example a token transfer to it from an unrelated account, transaction 0x4b0f7ec4e131005e6e7ac134f83cdfa9652c28bf32e96e1269808f8e30e3fdc5), and 102 show no direct link in sender, recipient or calldata. 27 distinct senders and 43 distinct recipients appear. No filtered transaction has the PoolManager, the PositionManager, a Universal Router, the Quoter or Permit2 as recipient or in calldata. By month: 2 in June, 1,343 in July, 3 in August, 5 in September, 136 in October and 2 in November 2026.",
           RH + " eth_getTransactionByHash for all 1,493 hashes, " + Q, "high"),
         d("The hash 0x158a8b23576e0b0f93ae6ce47fe16185461131fdf0b873ba32e5a3f0f9c736d4, a retryable submission from the alias of the restricted wallet, was added 4,741 times between blocks 10,757,337 and 10,804,648. The block header field that counts delayed messages read stayed at 35,950 from block 10,757,337 (22:34:19 UTC on 2026-07-15) to block 10,804,650 and moved to 35,951 in block 10,804,651 (23:53:37 UTC). The sequencer produced 47,314 blocks in that time. Delayed messages of all users, which include deposits from Ethereum and forced transactions, waited 4,758 seconds behind one filtered message. No other hash was added more than twice.",
           RH + " eth_getLogs on 0x74 and eth_getBlockByNumber (nonce field), " + Q, "low"),
         d("An event rule is selected by the first 4 bytes of topic 0 and marks the addresses in the listed topic positions 1 to 3 as touched (execution/gethexec/eventfilter/eventfilter.go lines 20 to 24 and 212 to 262). The Arbitrum documentation names ERC-20, ERC-721 and ERC-1155 transfers as the events to block and describes a bypass for transfers to the zero address. The first 4 bytes are 0xddf252ad for Transfer(address,address,uint256), 0xc3d58168 for TransferSingle and 0x4a39dc06 for TransferBatch. The claim event of this repository, Transfer(address,address,address,uint256,uint256), starts with 0x1b3d7edb, and OperatorSet and the four argument Approval start with 0xceb576d9 and 0xb3fd5071. A claim mint, transfer or burn at the PoolManager therefore matches none of the documented rules, and it makes no call to the holder. I could not read the rules that the sequencer runs.",
           NITRO + "execution/gethexec/eventfilter/eventfilter.go; " + DOC_FILTER + "; local Keccak of the signatures; src/interfaces/external/IERC6909Claims.sol", "low"),
         d("The filter records as touched: the transaction sender and recipient and the sender with the alias removed (execution/gethexec/executionengine.go lines 133 to 148), the target of CALL, CALLCODE, DELEGATECALL and STATICCALL (core/vm/instructions.go lines 739, 785, 826 and 863), created addresses (core/vm/evm.go line 581), selfdestruct beneficiaries (instructions.go lines 925 and 971), retryable recipients and refund addresses (arbos/tx_processor.go lines 331 to 334, 424 and 787) and event rule addresses (executionengine.go lines 252 to 262). Since v3.11.0-rc.5 the destination of a withdrawal to the parent chain is recorded as well.",
           NITRO + "execution/gethexec/executionengine.go, " + GETH + "core/vm/instructions.go and " + NITRO + "CHANGELOG.md line 351", "low"),
     ])

prof(4663, "L3",
     "Nothing new for tokens or gas on this chain in this cycle. The accrued native protocol fee is small.",
     [
         d("protocolFeesAccrued(address(0)) on the PoolManager is 0.138 ETH.",
           RH + " eth_call to 0x8366a39cc670b4001a1121b8f6a443a643e40951, " + Q, "none"),
     ])

prof(4663, "L4",
     "The filter settings of ArbOS were read from the public owner precompile. The public RPC node does not apply the address filter to simulated calls, so the levers that the open leads name could be judged from the client source and the chain record only.",
     [
         d("ArbOwnerPublic returns one filterer, 0xebdc18a1f5c42fc25552ea233facf4054df224b7, the filtered funds recipient 0xbbbd433db8700d8927faaaaf482e007e293ed568, a filtering start time of 1782295200 (2026-06-24 10:00 UTC), getCollectTips() false, no native token owner, and the chain owners 0x2a153c6a1b66dbc930a8d7017230ab0253005c09 and 0x5eb36fd3a11f3a123c046e3bf84195bb4f5a2690.",
           RH + " eth_call to 0x000000000000000000000000000000000000006b, " + Q, "low"),
         d("On the public endpoint eth_call and eth_estimateGas succeed with the restricted wallet as sender, with it as recipient, and through a stub that calls it. The filter for simulated calls is a node option that is off by default (CHANGELOG.md lines 169, 224 and 383). A wallet or router that simulates before sending sees success for a transaction that the sequencer will reject.",
           RH + " eth_call and eth_estimateGas with state override, " + Q + "; " + NITRO + "CHANGELOG.md", "low"),
     ])

# --------------------------------------------------------------------- Elysium
prof(99901, "L1",
     "Unchanged: a locally built client, ArbOS 61 and no scheduled upgrade on mainnet or on the testnet. The delegation probe gave the same result as on the other two chains.",
     [
         d("web3_clientVersion is nitro/vlocal+unknown-unknown with go1.25.12 on mainnet and on the testnet 99801. arbOSVersion() returns 0x74 on both, which is ArbOS 61.",
           EL + " and https://testnet-rpc.elysium.kinetiq.xyz web3_clientVersion and eth_call to 0x64, " + Q, "none"),
         d("An account delegated to 0x64, 0x6e or 0x02 answers transfer, balanceOf and empty calldata from the PoolManager address with success and no return data.",
           EL + " eth_call with state overrides, " + Q, "low"),
     ])

prof(99901, "L2",
     "The fee controller of the Elysium PoolManager is the zero address, and the critic asked whether any transaction type can call with that sender. None can without a parent chain account that nobody is known to control. No protocol fee has accrued.",
     [
         d("protocolFeeController() is the zero address, owner() is 0xa9ae0c5eb238a519b7f5af27415eb6dd0744da8d and protocolFeesAccrued(address(0)) is 0.",
           EL + " eth_call to 0xE2e105d3F7209A9DA11f83cCf3E7398a753823F1, " + Q, "low"),
         d("The parent chain address that would alias to the zero address, 0xeeeeffffffffffffffffffffffffffffffffeeef, has no code, nonce 0 and balance 0 on HyperEVM. It matches none of the documented HyperEVM system address patterns (0x2222..., 0x2000... token addresses, 0x3333..., 0x5555...).",
           "https://rpc.hyperliquid.xyz/evm eth_getCode, eth_getTransactionCount and eth_getBalance, " + Q, "none"),
     ])

prof(99901, "L3",
     "The quote assets of the 131,786 pools were identified. Native HYPE serves 124,372 of them. The other large balances are wrapped HYPE behind an upgradeable proxy, the governance token, bridged USDC, two wrapped stock tokens from the same bridge token template and one leveraged token with an owner set minter.",
     [
         d("PoolManager balances: 9,964.44 native HYPE, 14,726.09 WHYPE (0xba876237b0f021a6c6d852d6c26e107997cc5e81, an EIP-1967 proxy with implementation 0xf098387f303b6bbfe9da7cb16f70639b76430542, 26.8 percent of supply), 3,321,600 KNTQ (17.5 percent of supply), 193,719 USDC, 175.62 wNVDAx of a supply of 267.10, 4.45 wSPYx of 31.36 and 68,227 xyz:NVDA3L of 172,571. KNTQ, USDC, wNVDAx and wSPYx share one 835 byte code size.",
           EL + " eth_call, eth_getBalance, eth_getCode and eth_getStorageAt, " + Q + "; pool counts from research/network-risk/cycles/004/theme-balance-reconcile.work/raw/currencies_99901.json.gz", "low"),
         d("xyz:NVDA3L at 0xc4be5f25dfaa81ed188db01fee37e2ed4163c8d5 has 4,624 bytes of code with owner(), minter(), setMinter(address), mint(address,uint256), burn(uint256) and burnFrom(address,uint256), and no selector that I could match to a rebase or a transfer fee. Nine of its selectors are unknown to the signature list.",
           EL + " eth_getCode; signature list research/network-risk/cycles/005/theme-assigned-balance.work/raw/signatures.json.gz", "low"),
     ])

prof(99901, "L4",
     "The announced ArbOS upgrade is still not scheduled and the two documentation pages are unchanged. Transaction filtering and native token management are off.",
     [
         d("getScheduledUpgrade() returns version 0 and timestamp 0 on mainnet and on the testnet 99801. The page on trading from Elysium is dated 2026-11-02 and the page on market data 2026-09-21. Both still say the predeploy and the read precompile ship in an upgrade about four weeks after mainnet, and neither gives an address, a selector or the way result callbacks are delivered.",
           EL + " and https://testnet-rpc.elysium.kinetiq.xyz eth_call to 0x6b, " + Q + "; https://elysium.kinetiq.xyz/docs/trading-on-hypercore-from-elysium and https://elysium.kinetiq.xyz/docs/hypercore-market-data, fetched 2026-11-23", "low"),
         d("ArbOwnerPublic returns no filterer, a zero filtering start time, a zero filtered funds recipient, no native token owner, getCollectTips() true and one chain owner, 0xce4ceced412aa9359840c7d52bbd99827a5d42b9.",
           EL + " eth_call to 0x000000000000000000000000000000000000006b, " + Q, "low"),
     ])

# -------------------------------------------------------------------- findings
findings = [
    {
        "ref": "F-036",
        "title": "Issuer controls on USDG and Dinari USD+ cover 2.78M more in the Arbitrum One PoolManager, and the USD+ operator can lower the pooled balance by a rebase",
        "chainIds": [42161],
        "lens": "L3",
        "assumptions": ["A2", "A6"],
        "effect": "both",
        "actor": "issuer",
        "severity": "high",
        "difference": "F-036 lists USDC, USDT0, PYUSD and cbBTC. A ranking of all priced pool currencies shows two more issuer controlled tokens among the six largest positions. Global Dollar (USDG) has a freeze list and a pause. Dinari USD+ keeps balances as shares times an index, checks every transfer against a restrictor contract, and lets the holder of its operator role raise or lower the index.",
        "mechanism": "USDG: the issuer freezes the PoolManager address or pauses the token. transfer then fails with the PoolManager as sender, Currency.transfer reverts, and every take and every fee collection in USDG reverts, as F-036 describes for the other tokens. USD+: step 1, the owner of the restrictor 0x2ed5c85d5105abe5d13586c5c3a8f99a837942b4 lists the PoolManager. checkTransferRestricted runs before every transfer, so payouts and payments in USD+ revert. Step 2, separately, the operator calls rebaseSub. balanceOf(PoolManager) is sharesOf(PoolManager) times balancePerShare, so it falls in proportion while pools, claims and accrued fees keep their recorded amounts. The last withdrawers find less USD+ than the pools record. Step 3, in the other direction rebaseAdd raises the balance. The index stands at 1.0707, so about 70,678 USD+ of the 1,070,678 held came from index growth after deposit, on the assumption that the 999,999.89 shares were deposited near an index of 1. No settle is credited for that growth, because a sync and a settle in one transaction read the same index, and the rebase functions revert for an ordinary account. The surplus belongs to no pool. I read rebaseSub in the public Dinari repository, whose current version takes one argument. The deployed version 6.0.0 takes a second bytes32 argument and rejects ordinary callers with AC: unauthorized. The implementation 0xff5bff8081eaee966bd74e9c0c059949df2345e1 is not verified on Sourcify and the Blockscout API was not reachable, so the deployed body of rebaseSub is unconfirmed.",
        "impact": "All pools and claims in USDG and USD+. The PoolManager holds 1,712,030.85 USDG and 1,070,677.64 USD+, which is 34.4 percent of the USD+ supply. A freeze stops withdrawals in the token. A downward rebase takes a share of the pooled USD+ from the last liquidity providers to withdraw.",
        "preconditions": "The Paxos asset protection role for USDG. For USD+ the owner of the transfer restrictor (0x269e944ad9140fc6e21794e8ea71ce1afbfe38c8) or the holder of the operator role of the token. No ordinary account can act.",
        "mitigations": "Liquidity providers should treat a USD+ pool as exposed to the issuer's index and restrictor. Interfaces can label both tokens as issuer controlled. The deployer cannot remove the exposure in core, because one address holds every pool's balance.",
        "coreRefs": ["src/PoolManager.sol:279-297", "src/PoolManager.sol:349-365", "src/types/Currency.sol:53-87", "src/ProtocolFees.sol:44-57"],
        "sources": [
            {"url": ARB, "supports": "eth_call on 2026-11-23: balanceOf(PoolManager), totalSupply, balancePerShare, sharesOf, transferRestrictor, isBlacklisted, publicVersion and the reverts of rebaseAdd, rebaseSub, mint and burn from an ordinary account on 0xfc90518d5136585ba45e34ed5e1d108bd3950cfa; isFrozen, paused, owner and balanceOf on 0x004b506865409877c9fa29bfb1eba929984b9bbc; eth_getLogs showing no index event in the last 40,000,000 blocks"},
            {"url": "https://raw.githubusercontent.com/dinaricrypto/usdplus-contracts/main/src/UsdPlus.sol", "supports": "rebaseAdd, rebaseMul and rebaseSub are restricted to OPERATOR_ROLE and set balancePerShare; _beforeTokenTransfer calls checkTransferRestricted; setTransferRestrictor and setIssuerLimits are restricted to the admin role; burn(address,uint256) spends an allowance"},
        ],
        "evidence": "primary",
    }
]

# --------------------------------------------------------------------- cleared
cleared = [
    {
        "chainIds": [4663], "lens": "L2",
        "check": "Leads L-117, L-315 and L-400, answered from the filter precompile, its logs and the client source: what an entry identifies, who adds entries and how soon, whether listed transactions share an address, and whether an ordinary account can make a transaction of another user that calls the PoolManager match the filter through a native take of zero or 1 wei to a listed address, a payment of a listed token, or a pool whose hook or currency is a listed contract.",
        "result": "An entry is the hash of one transaction that arrived through the delayed inbox. The only filterer, 0xebdc18a1f5c42fc25552ea233facf4054df224b7, adds it a median of 10 blocks before the transaction executes, and the transaction then fails with all gas consumed and no contract code run. 1,389 of 1,491 executed entries name the wallet 0x42607b2e4fde22e83822d4a86ddac58d847dc289 as sender, recipient or calldata argument, and none names the PoolManager or its periphery. A transaction is judged by the addresses it touches itself while it runs. The three levers leave nothing behind that a later transaction of someone else would touch. A take writes a transient delta and makes one call or one transfer (src/PoolManager.sol:291-297, src/types/Currency.sol:44-80), so a take to a listed address makes the attacker's own transaction touch that address and stores no address in the PoolManager. A payment of a listed token and a pool with a listed hook or currency involve the listed contract only in transactions that use that token or that pool, and the PoolKey names both (src/PoolManager.sol:117-142, src/libraries/Hooks.sol:131-155). A swap or a liquidity change on another pool calls the PoolManager, its two currencies, its hook if any, the caller and the recipient the caller named. The on-chain list holds hashes that only the filterer can add. F-001 stays in the operator class. The public RPC node does not apply the filter to simulated calls, so I could not run the levers against the sequencer's filter, and the restricted list and the event rules are files I cannot read.",
        "source": RH + " eth_getLogs on 0x74, eth_getTransactionByHash and eth_getTransactionReceipt for 1,493 hashes, eth_call to 0x6b, " + Q + "; " + NITRO + "execution/gethexec/executionengine.go lines 133 to 262 and " + GETH + "core/vm/instructions.go lines 739 to 971",
    },
    {
        "chainIds": [4663], "lens": "L2",
        "check": "Whether a claim mint, transfer or burn that names a restricted address can be used to make the filter fail transactions of other users of the PoolManager.",
        "result": "No. mint, burn, transfer and transferFrom write balances and emit the claim Transfer event without calling the holder (src/ERC6909.sol:25-48 and 79-89, src/PoolManager.sol:322-336). The event starts with 0x1b3d7edb, which differs from the selectors of the ERC-20, ERC-721 and ERC-1155 transfer events that the Arbitrum documentation names for event rules. If the sequencer ran a rule for the claim event, a mint to a restricted address would fail the minter's own transaction and no other. The reverse also follows: claim transfers to or from a restricted holder pass the documented rules, which is a matter for the chain operator and takes nothing from other users. I could not read the rules the sequencer runs.",
        "source": NITRO + "execution/gethexec/eventfilter/eventfilter.go lines 212 to 262; " + DOC_FILTER + "; src/interfaces/external/IERC6909Claims.sol",
    },
    {
        "chainIds": [4663], "lens": "L2",
        "check": "Known weakness on this chain: a filtered message halts delayed sequencing until its hash is on the on-chain list. Can an ordinary account use that to keep other users from withdrawing from the PoolManager.",
        "result": "No. The halt stops the reading of delayed inbox messages and nothing else. On 2026-07-15 one retryable submission held the delayed message count at 35,950 for 4,758 seconds while the sequencer produced 47,314 blocks, so transactions sent to the sequencer, which include every take, burn and liquidity removal, went through. The changelog records fixes for a deposit that stalled the delayed sequencer and for a halt on an already finalized message, and no hash has been added more than twice since. Today a filtered message costs its sender a parent chain transaction and delays the messages behind it by the time the filterer needs, a median of 10 blocks. A user who depends on a forced transaction because the sequencer refuses service is in the operator case of F-001. The live build v3.13.0-rc.9 is not public, so the fixes were read at v3.12.4.",
        "source": RH + " eth_getBlockByNumber nonce field at blocks 10,757,337 to 10,804,651 and eth_getLogs on 0x74, " + Q + "; " + NITRO + "CHANGELOG.md lines 194, 294 and 721",
    },
    {
        "chainIds": [42161, 4663, 99901], "lens": "L2",
        "check": "Transaction types, walked for msg.sender, msg.value and transient storage in unlock, sync, settle and take at Nitro v3.12.4 and fork commit 0e44603: legacy, access list, dynamic fee and set code transactions, blob transactions, deposits (0x64), unsigned (0x65) and contract (0x66) transactions, retries (0x68), retryable submissions (0x69), internal transactions (0x6a), transactions on the on-chain filter list, and the message kinds batch, heartbeat, nonmutating call and compressed transaction.",
        "result": "Blob transactions, nonmutating calls, compressed transactions and heartbeats are rejected by the parser. Deposits, retryable submissions and internal transactions end in the start hook: a deposit credits a balance with no call, a submission creates a ticket, and the start block transaction calls only the EIP-2935 history contract after a transient reset. A filtered transaction runs no contract code. Types 0, 1, 2 and 4 and the types 0x65, 0x66 and 0x68 reach StateDB.Prepare, which replaces the transient map, and then one top call whose value the sender's balance pays (a retry is funded from the ticket escrow first). In each of them the PoolManager sees one transaction: Lock, the deltas and the synced currency start at zero (src/libraries/Lock.sol:10-27, src/libraries/CurrencyDelta.sol:28-41, src/libraries/CurrencyReserves.sol:15-38), unlock calls back the direct caller (src/PoolManager.sol:104-114), settle credits msg.value or the balance change since sync (src/PoolManager.sol:349-365) and take debits before it pays (src/PoolManager.sol:291-297). For types 0x65, 0x66 and 0x68 the caller is the aliased parent chain sender. That address holds code on the child chain only if a contract happens to sit at exactly that address, so in practice the callback returns nothing and unlock reverts when the result is decoded, while sync, which needs no unlock, succeeds and its transient values end with the transaction. A set code transaction lets an account with a delegation be the caller and receive the callback, as on Ethereum.",
        "source": NITRO + "arbos/parse_l2.go lines 25 to 190, " + NITRO + "arbos/tx_processor.go lines 197 to 600 and 1066 to 1105, " + GETH + "core/state_transition.go lines 837, 950 and 964, " + GETH + "core/state_processor.go line 358",
    },
    {
        "chainIds": [42161, 4663, 99901], "lens": "L2",
        "check": "Critic gap of cycle 5: can any transaction type, system call or precompile call a contract with msg.sender equal to the zero address, which is the stored protocol fee controller on Elysium (src/ProtocolFees.sol:36 and 48).",
        "result": "No. Signed transactions recover a sender from a signature. Unsigned, contract, deposit and retryable transactions use the aliased caller that the parent chain Bridge recorded, and the zero address would need the caller 0xeeeeffffffffffffffffffffffffffffffffeeef, which has no code, nonce 0 and balance 0 on Ethereum and on HyperEVM. Retries use the sender stored in the ticket. Internal transactions must come from 0xa4b05 and make one call, from the system address to the history contract. The ArbOS precompiles do not call other contracts. A zero sender exists in eth_call and gas estimation only. On Elysium setProtocolFee and collectProtocolFees are therefore unreachable until the owner sets a controller, and protocolFeesAccrued is 0.",
        "source": NITRO + "arbos/parse_l2.go lines 245 to 264, 292 and 364 and " + NITRO + "arbos/tx_processor.go lines 269 to 275; https://ethereum-rpc.publicnode.com and https://rpc.hyperliquid.xyz/evm eth_getCode and eth_getTransactionCount; " + EL + " eth_call, " + Q,
    },
    {
        "chainIds": [42161, 4663, 99901], "lens": "L1",
        "check": "EIP-7702 on Nitro: an account whose delegation points at a precompile, including an ArbOS precompile, used as the currency of a take, as the target of sync, or as the recipient of a native take.",
        "result": "Such an account behaves as an address without code from ArbOS 50 on. From a stub at the PoolManager address, transfer, balanceOf and a plain call each succeed with no return data on all three chains. Currency.transfer accepts an empty return, so take debits the caller and moves nothing (src/types/Currency.sol:64-74, src/PoolManager.sol:294-295). sync reverts, because the balanceOf result cannot be decoded (src/types/Currency.sol:94, src/PoolManager.sol:285), so no credit can arise under that currency id. A native take to the account moves the value to it and debits the caller in full. The delegation does not run the precompile with the PoolManager as caller.",
        "source": GETH + "core/vm/evm.go lines 789 to 806; eth_call with state overrides on " + ARB + ", " + RH + " and " + EL + ", " + Q,
    },
    {
        "chainIds": [42161, 4663, 99901], "lens": "L1",
        "check": "Known weaknesses, items that cycles 2 and 3 did not list: the Security Council emergency actions of 2024-09-25 and 2025-10-13, the Trail of Bits review of ArbOS 50 and 51, the reports added to the audit index since July 2026, the security note of Nitro v3.10.0, and the security considerations of the compliance filtering documentation. Can an ordinary account use any of them against funds in the PoolManager.",
        "result": "None applies. The 2024 action answered a node crash from a crafted Stylus program and a storage opcode that Stylus priced at almost nothing, both availability faults. The 2025 action lowered the WASM stack depth after a divergence between ARM and x86 nodes on the test network, and its report says no funds were at risk. The ArbOS 50 and 51 review has six findings about gas accounting, limits and error handling. The Glamsterdam report covers two pricing parameters and found nothing. The v3.10.0 release note says the release contains security fixes and gives no detail, which I could not resolve further. The compliance filtering page states that a deposit from a restricted address can stay locked in the bridge and that the filter fails forced transactions, which is F-001. None of these changes how CALL, value transfer, TSTORE or return data behave for an EVM contract, and none moves a contract's balance. I did not open the reports on the yield bearing bridge, the tip collection toggler, the one step proof guard and the Stylus permissioned deployer.",
        "source": "https://forum.arbitrum.foundation/t/security-council-emergency-action-transparency-report/26997, https://forum.arbitrum.foundation/t/security-council-emergency-action-10-13-2025/30093, https://docs.arbitrum.io/audit-reports/2025_12_01_trail_of_bits_arbos_50_and_51_security_review.pdf, " + AUDITS + ", https://github.com/OffchainLabs/nitro/releases/tag/v3.10.0 and " + DOC_FILTER + ", read 2026-11-23",
    },
    {
        "chainIds": [42161], "lens": "L3",
        "check": "Lead L-139, unprivileged part: can an ordinary account change balanceOf(PoolManager) of Dinari USD+ or of xUSD without a transfer, so that a settle is credited for it, or burn the PoolManager balance.",
        "result": "USD+: no. rebaseAdd and rebaseSub revert for an ordinary account with AC: unauthorized, mint reverts without an issuer limit, and burn(address,uint256) needs an allowance that the PoolManager never gives, because it sends only transfer and balanceOf to a currency (src/types/Currency.sol:60-73 and 94). The index did not move in the last 40,000,000 blocks. xUSD: the PoolManager balance of 62.35 units follows rebases. I did not establish who can start a rebase of xUSD. The amount at stake is the yield on 62 units and is recorded with F-037.",
        "source": ARB + " eth_call from 0x1234567890abcdef1234567890abcdef12345678 and eth_getLogs, " + Q,
    },
    {
        "chainIds": [42161, 99901], "lens": "L4",
        "check": "Whether the transaction filter of ArbOS 60 and 61, which F-001 records for Robinhood Chain, is active on Arbitrum One or Elysium.",
        "result": "No. Both chains return an empty filterer list, a zero filtering start time and a zero filtered funds recipient. Without a filterer no hash can be added to the on-chain list, and the sequencer side filter is a node option that the Arbitrum documentation says is not intended for Arbitrum One. The owner of either chain could add a filterer, which is a governance action.",
        "source": ARB + " and " + EL + " eth_call to 0x000000000000000000000000000000000000006b, " + Q + "; " + DOC_FILTER,
    },
    {
        "chainIds": [99901], "lens": "L3",
        "check": "Lead L-137: which currencies the Elysium pools use, and whether the larger PoolManager balances belong to tokens whose balance changes without a transfer or that charge a fee on transfer.",
        "result": "Cycle 4 listed 129,516 currencies from 131,786 Initialize logs and compared the balance change of each with its Transfer logs over 127,509 seconds: 129,491 reconcile and 25 have a zero balance. Cycle 5 ran a transfer test on the same list and found 21 tokens with unusual transfer behaviour, of which ELO is recorded in F-059. The quote assets are native HYPE (124,372 pools), WHYPE (4,673), KNTQ (1,484), bridged USDC (783), wNVDAx (159), VOLTA (134) and xyz:NVDA3L (68). Their balances were read in this cycle and none of them shows a rebase or a transfer fee in the reconcile. WHYPE sits behind an upgradeable proxy, the bridged tokens are minted by the bridge (F-035 covers USDC), and the leveraged token has an owner set minter, all of which are issuer matters. The hooks were counted in cycle 5 (0x6b1216a40b65c83e9c9e18a562c446697b8cf8ec serves 104,615 pools) and lead L-258 covers that hook.",
        "source": "research/network-risk/cycles/004/theme-balance-reconcile.work/raw/mismatch_99901.json and currencies_99901.json.gz, research/network-risk/cycles/005/theme-assigned-balance.work/raw/xfer_99901.json.gz; " + EL + " eth_call, " + Q,
    },
]

# ----------------------------------------------------------------------- leads
leads = [
    {"chainIds": [42161], "lens": "L3",
     "question": "Which accounts hold the operator role and the admin role of Dinari USD+ at 0xfc90518d5136585ba45e34ed5e1d108bd3950cfa, and what does rebaseSub(uint128,bytes32) do in the deployed implementation 0xff5bff8081eaee966bd74e9c0c059949df2345e1, whose source I could not obtain?",
     "why": "The PoolManager holds 34.4 percent of the supply. The finding rests on the public repository for the body of the rebase functions, and the deployed version has a different signature. A second bytes32 argument suggests rebases that follow a message from another chain, and the party that can send that message decides whether the hazard stays with the issuer.",
     "priority": "medium"},
    {"chainIds": [42161], "lens": "L3",
     "question": "What are Varlamore USDC Growth at 0x2ba39e5388ac6c702cb29aea78d52aa66832f1ee (2.06 billion units in the PoolManager, symbol USDC, 18 decimals, owner 0xd8454b3787c6aab1cf2846af7882f8c440c3903d), EverValueCoin at 0x45d9831d8751b2325f3dbf48db748723726e1c8c and VSN at 0x6fbbbd8bfb1cd3986b1d05e7861a0f62f87db74b, and do any of them change balances without a transfer or carry owner controls?",
     "why": "The price list puts them at 4.37M, 0.98M and 0.54M USD in the Arbitrum One PoolManager and I did not confirm the prices or read the contracts. A token that copies the USDC symbol with a large pooled balance can mislead users of interfaces that show symbols.",
     "priority": "low"},
    {"chainIds": [4663], "lens": "L2",
     "question": "Does the restricted wallet 0x42607b2e4fde22e83822d4a86ddac58d847dc289, or any other listed account, hold claims or liquidity positions in the PoolManager 0x8366a39cc670b4001a1121b8f6a443a643e40951, and has it set an operator or an allowance for them?",
     "why": "Claim transfers match none of the documented event rules and make no call to the holder. An operator approved before the listing could move such claims out through transferFrom or burn. If that happened, the chain operator's remedies are a new rule or an entry for the PoolManager address, and the second would fail every exit (F-001).",
     "priority": "low"},
]

# ----------------------------------------------------------------- leadResults
lead_results = [
    {"leadId": "L-315", "outcome": "cleared",
     "answer": "Read from precompile 0x74 and its 6,234 logs. An entry is the hash of one delayed inbox transaction. The single filterer 0xebdc18a1f5c42fc25552ea233facf4054df224b7 adds it a median of 10 blocks before the transaction executes as a failure with all gas consumed. 1,389 of 1,491 executed entries name one wallet, 0x42607b2e4fde22e83822d4a86ddac58d847dc289, and none names the PoolManager or its periphery. The filter judges a transaction by the addresses that the transaction itself touches. A native take of zero or 1 wei to a listed address, a payment of a listed token and a pool with a listed hook or currency put the listed address only into transactions that name it, and leave no address in PoolManager storage (src/PoolManager.sol:291-297 and 117-142). No ordinary account can make another user's transaction on another pool match. The levers could not be run against the sequencer, because the public RPC node does not apply the filter to simulated calls."},
    {"leadId": "L-400", "outcome": "cleared",
     "answer": "Same answer as L-315, from chain data. 6,234 add logs, 1,493 distinct hashes, 1,491 executed with status 0, one filterer account, entries follow a rule on touched addresses that the client applies to the delayed transaction itself. The listed transactions share the wallet 0x42607b2e4fde22e83822d4a86ddac58d847dc289 in 1,389 cases. A zero amount take or a 1 wei payment by someone else leaves no state that a later PoolManager transaction would touch: take writes transient deltas only and the recipient is not stored. eth_call and eth_estimateGas on the public endpoint do not apply the filter, and debug_traceCall was not needed for a path that stores nothing."},
    {"leadId": "L-117", "outcome": "cleared",
     "answer": "Each entry identifies one transaction hash, never a sender or a contract. The provider side is automated: the sequencer reports a filtered delayed transaction and the filterer service adds its hash, which matches a median gap of 10 blocks and one hash that a loop added 4,741 times on 2026-07-15. An ordinary account cannot cause an entry or a rule to match transactions of others that call the PoolManager, for the reasons given under L-315. The finding F-001 stays in the operator class."},
    {"leadId": "L-138", "outcome": "inconclusive",
     "answer": "The event rules and the restricted list are files on the sequencer and are not on chain. What can be seen: the documentation names ERC-20, ERC-721 and ERC-1155 transfer events and the opcodes CALL, CREATE, CREATE2 and SELFDESTRUCT; 144 filtered transactions carry the restricted wallet only in calldata, for example as the recipient of a token transfer sent by an unrelated account, which fits a rule on the ERC-20 Transfer event; the filtering start time is 2026-06-24 10:00 UTC and the filtered funds recipient is 0xbbbd433db8700d8927faaaaf482e007e293ed568. No filtered transaction ever had the PoolManager, the PositionManager, a Universal Router, the Quoter or Permit2 as recipient or in calldata, and swaps through them execute daily, so none of them is on the list today. Whether a rule exists for the claim event 0x1b3d7edb, and whether any contract is exempt, cannot be read from outside."},
    {"leadId": "L-134", "outcome": "inconclusive",
     "answer": "Still not answerable on 2026-11-23. getScheduledUpgrade() returns zeros on Elysium mainnet and on the testnet 99801, both report ArbOS 61, and the two documentation pages are unchanged since 2026-11-02 and 2026-09-21. They give no address, selector or funding function for the read precompile or the ElysiumCoreWriter predeploy. The lead should be re-run when getScheduledUpgrade() changes."},
    {"leadId": "L-001", "outcome": "inconclusive",
     "answer": "The upgrade is unscheduled on 2026-11-23 and the documentation still does not say how result callbacks are delivered. It says a keeper signs intents for HyperCore and that outcomes are delivered back to the originating contract with gas refunded from a HYPE escrow on the predeploy. If the delivery is a transaction from a keeper account it is an ordinary transaction with its own transient map. That reading is an inference and no code or address is published."},
    {"leadId": "L-137", "outcome": "cleared",
     "answer": "The pools use 129,516 currencies. Native HYPE is a currency in 124,372 pools, followed by WHYPE, KNTQ, bridged USDC, wNVDAx, VOLTA and xyz:NVDA3L. The cycle 4 reconcile found no currency whose PoolManager balance moved without matching Transfer logs, and the cycle 5 transfer test found 21 tokens with unusual transfers, with ELO recorded in F-059. The larger balances read in this cycle (9,964 HYPE, 14,726 WHYPE, 3.32M KNTQ, 193,719 USDC, 175.6 wNVDAx, 68,227 xyz:NVDA3L) show no rebase or transfer fee. Their issuer side controls (proxy upgrade of WHYPE, bridge minting, the minter of the leveraged token) were not read in depth and belong to the issuer class."},
    {"leadId": "L-139", "outcome": "finding",
     "answer": "Ranking by value from live balances and the cycle 5 price list, which stands in for an indexer and covers the 845 priced currencies: USDC, WBTC, USDG, Dinari USD+, cbBTC, USDT0, VSN, ARB, ESP, DOT, PENDLE, UNI, LINK, wstETH, WOO, AAVE, wSOL, HDN, WETH and EQB, with 4,425.84 native ETH beside them. USDG (1.71M) and Dinari USD+ (1.07M, 34.4 percent of supply, share based with an operator moved index and a transfer restrictor) were missing from F-036 and are added by the finding of this cycle. The token that reports xUSD at 0xe80772Eaf6e2E18B651F160Bc9158b2A5caFCA65 is a rebasing token with credits per token accounting, and the PoolManager holds 62.35 units that follow rebases, which is too little to change the low rating of F-037. Two entries of the price list, Varlamore USDC Growth and EVA, have prices I did not confirm, and a lead covers them."},
]

out = {
    "unit": "arbitrum-family",
    "_lenses": ["L1", "L2", "L3", "L4"],
    "profiles": profiles,
    "findings": findings,
    "cleared": cleared,
    "leads": leads,
    "leadResults": lead_results,
}
path = "/home/user/v4-core/research/network-risk/cycles/006/arbitrum-family.research.json"
json.dump(out, open(path, "w"), indent=1, ensure_ascii=False)
print("written", path, len(json.dumps(out)))
