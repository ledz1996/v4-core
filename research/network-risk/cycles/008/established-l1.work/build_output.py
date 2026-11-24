# Builds research/network-risk/cycles/008/established-l1.research.json from the facts collected in this directory.
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "established-l1.research.json")
raw = lambda n: json.load(open(os.path.join(HERE, "raw", n)))

snvb = raw("snvb_result.json") if os.path.exists(os.path.join(HERE, "raw", "snvb_result.json")) else None
L464 = json.load(open(os.path.join(HERE, "raw", "l464_text.json"))) if os.path.exists(os.path.join(HERE, "raw", "l464_text.json")) else None

BOR_PP = "https://raw.githubusercontent.com/0xPolygon/bor/v2.11.1/params/protocol_params.go"
BOR_ACL = "https://raw.githubusercontent.com/0xPolygon/bor/v2.11.1/core/vm/operations_acl.go"
BOR_CFG = "https://raw.githubusercontent.com/0xPolygon/bor/master/params/config.go"
SR_SRC = "https://raw.githubusercontent.com/0xPolygon/genesis-contracts/master/contracts/StateReceiver.sol"
BOR_2103 = "https://forum.polygon.technology/t/bor-security-bug-fix-review-v2-10-3/22379"
BOR_259 = "https://forum.polygon.technology/t/bor-security-bug-fix-v2-5-9-review-post/21765"
BOR_2110 = "https://github.com/0xPolygon/bor/releases/tag/v2.11.0"
BOR_2111 = "https://github.com/0xPolygon/bor/releases/tag/v2.11.1"
BSC_PR = "https://github.com/bnb-chain/bsc/pull/3582"
BSC_PP = "https://raw.githubusercontent.com/bnb-chain/bsc/v1.8.2/params/protocol_params.go"
BSC_EVM = "https://raw.githubusercontent.com/bnb-chain/bsc/v1.8.2/core/vm/evm.go"
BSC_CHG = "https://raw.githubusercontent.com/bnb-chain/bsc/master/CHANGELOG.md"
RETH_BSC = "https://github.com/bnb-chain/reth-bsc/releases"
JENNER = "https://www.bnbchain.org/en/blog/jenner-hardfork-changes-upgrade-guide"
DEFIANT = "https://thedefiant.io/news/blockchains/bnb-chain-sets-jenner-date-post-flags-timestamp-risk"
AV = "https://raw.githubusercontent.com/ava-labs/avalanchego/v1.15.3/vms/saevm/"
AV_WC = AV + "worstcase/state.go"
AV_PARAMS = AV + "params/params.go"
AV_EXEC = AV + "saexec/execution.go"
AV_EXT = AV + "cchain/libevm/extstate/statedb.go"
AV_IMP = AV + "cchain/tx/import.go"
AV_REL = "https://github.com/ava-labs/avalanchego/blob/master/RELEASES.md"
AV_CE = "https://docs.avax.network/docs/nodes/architecture/execution/continuous-execution"
WORK = "research/network-risk/cycles/008/established-l1.work/raw/"

profiles = [
 {"chainId": 137, "lens": "L1",
  "summary": "Bor v2.11.1 and v2.11.2 change no execution rule. The source at tag v2.11.1 fixes the transaction gas cap at 2^25 and the PIP-88 storage prices, which this cycle used to bound how many initialized ticks one swap can cross. The Bor review posts of February and October 2026 describe faults in node liveness, in the block number a producer can present and in parallel execution, and the PoolManager bytecode depends on none of them.",
  "deltas": [
   {"delta": "params/protocol_params.go at tag v2.11.1 sets MaxTxGas to 1 << 25 (33,554,432), ColdSloadCostPIP88 to 5460 and ColdSstoreCostPIP88 to 2940. core/vm/operations_acl.go charges a warm write of a non-zero slot 5000 minus 2940, which is 2060, after the cold read. One crossing of an initialized tick therefore costs about 25,000 gas on Polygon against about 16,500 under Ethereum prices.", "source": BOR_PP, "relevance": "low"},
   {"delta": "An eth_call that runs opcode 0x1e (CLZ) returned 0xff on Polygon and on BNB Smart Chain and failed with an undefined opcode on Avalanche. The Osaka opcode set is active on the first two and absent on the C-Chain.", "source": "rpc https://polygon-bor-rpc.publicnode.com, https://bsc-dataseed1.bnbchain.org and https://api.avax.network/ext/bc/C/rpc, eth_call with data 0x60011e5f5260205ff3, 2026-11-23; " + WORK + "fork_gas_probe.json", "relevance": "low"},
   {"delta": "The review post for Bor v2.5.9 (2026-02-25) discloses that consensus and import checks compared block numbers after truncation to 64 bits while the EVM exposed the full integer, so an authorised producer could present a block number far above the parent's. The fix is in v2.5.9. The PoolManager bytecode contains no NUMBER or TIMESTAMP opcode (assumption A10).", "source": BOR_259, "relevance": "none"},
   {"delta": "The review post for Bor v2.10.3 (2026-10-15) discloses two denial of service paths in BlockSTM V2 (an unbounded keccak cache and repeated code hashing) and a hardening fix for balance reads across a self-destruct boundary in parallel execution. Bor runs the serial and the parallel processor together and both must give the same result. The post states that none of the items changes execution results.", "source": BOR_2103, "relevance": "low"}
  ]},
 {"chainId": 137, "lens": "L2",
  "summary": "The StateReceiver that Uburu installed at 0x1001 was read in source. It keeps only a hash of a failed state sync, and any account can replay a failed record later with the original receiver and data. Since Uburu 31 of 6,481 state syncs failed, 6 were replayed and 25 are pending. None of the 25 comes from the Uniswap timelock or names the PoolManager owner contract.",
  "deltas": [
   {"delta": "StateReceiver.commitState calls onStateReceive on the receiver with gas from an oracle (5,000,000 at most, 160,000 when the oracle fails) and stores keccak256(abi.encode(receiver, stateData)) when the call fails. replayFailedStateSyncWithData(stateId, receiver, stateData) has no caller check and no expiry. replayHistoricFailedStateSync replays records under a Merkle root that a fixed rootSetter wrote once. On chain gasOracle() is 0x5e3a5eafd4501332c0bc2acfd38df3ebc5152147, leafCount() is 76 and replayCount() is 9.", "source": SR_SRC, "relevance": "low"},
   {"delta": "From block 96,787,900 to block 97,840,489 the contract at 0x1001 emitted 6,481 StateCommitted logs, 31 with success false, and 6 StateSyncReplay logs. failedStateSyncHashes is still set for 25 state ids. The Ethereum StateSynced logs of these 25 ids name FxChild 0x8397259c983751daf40400790063935a11afa28a as receiver in 23 cases and 0xa6fa4fb5f76172d178d61b04b0ecd319c5d1c0aa in 2. Ten of the FxChild records (ids 3218251 to 3218290) come from one Ethereum account, 0x207ab572e6962060f42498822a66c72d9776ffef, each with a 20 byte payload for a different Polygon contract.", "source": "rpc https://polygon.gateway.tenderly.co eth_getLogs on 0x1001, rpc https://polygon-bor-rpc.publicnode.com eth_call failedStateSyncHashes(uint256), rpc https://mainnet.gateway.tenderly.co eth_getLogs on StateSender 0x28e4F3a7f651294B9564800b2D01f35189A5bfbE, 2026-11-23; " + WORK + "polygon_statesync_since_uburu.json", "relevance": "low"},
   {"delta": "Bor v2.11.0 fetches state sync records page by page and fails the block when a fetch fails. Earlier versions committed such a block without state syncs. v2.11.1 adds header and body checks before execution on the stateless import path. Both change which blocks a node accepts and leave transaction execution as it was.", "source": BOR_2110, "relevance": "none"}
  ]},
 {"chainId": 137, "lens": "L3",
  "summary": "The transfer limit of ViciCoin still applies to the PoolManager. The plugin contract that enforces it serves no other token on Polygon and has no code on BNB Smart Chain or Avalanche.",
  "deltas": [
   {"delta": "At block 97,840,236 getExemptionCount() of VCNT is still 57 and the PoolManager is not in the list. transferLimit() is 6 VCNT, transferLimitAmountRemaining(PoolManager) is 6.165 VCNT and balanceOf(PoolManager) is 11.39 VCNT. All 7,428 logs that the plugin 0xf58fed40fba1ab7aa7ffc160b863bedd998386a7 emitted since its first log at block 83,256,139 carry the VCNT address as an indexed topic.", "source": "rpc https://polygon-bor-rpc.publicnode.com eth_call and rpc https://polygon.gateway.tenderly.co eth_getLogs, 2026-11-23; " + WORK + "l303_vici.json and " + WORK + "l303_plugin_logs.json", "relevance": "low"}
  ]},
 {"chainId": 137, "lens": "L4",
  "summary": "Two special address paths were tested with the PoolManager and its owner contract as targets. The PoolManager reverts on onStateReceive, and the owner contract accepts processMessageFromRoot only from FxChild with the Ethereum timelock as sender. The signature transfer of the native token contract, the function behind the 2021 MRC20 incident, is disabled.",
  "deltas": [
   {"delta": "transferWithSig(bytes,uint256,bytes32,uint256,address) on 0x0000000000000000000000000000000000001010 reverts with the string Disabled feature.", "source": "rpc https://polygon-bor-rpc.publicnode.com eth_call, 2026-11-23; " + WORK + "special_probe.json", "relevance": "none"},
   {"delta": "processMessageFromRoot on the PoolManager owner 0x8a1b966ac46f42275860f905dbc75efbfdc12374 reverts with L1 sender must be the owner when FxChild calls with another sender, and with Can only be called by the state sync child contract when the caller is an ordinary account or 0x1001. It returns without revert only for caller FxChild and sender 0x1a9c8182c09f50c8318d769245bea52c32be35bc.", "source": "rpc https://polygon-bor-rpc.publicnode.com eth_call with from set to each caller, 2026-11-23; " + WORK + "polygon_owner_proxy_auth.json", "relevance": "low"}
  ]},
 {"chainId": 56, "lens": "L1",
  "summary": "The bad block fix of March 2026 shows what the removed superinstruction interpreter got wrong: a STATICCALL frame that reached optimized code lost its write protection. The PoolManager does not rely on that protection for its own accounting. The transaction gas cap in the v1.8.2 source is 2^24.",
  "deltas": [
   {"delta": "Pull request 3582 (merged 2026-03-05, released in v1.7.1) moved the readOnly flag from the interpreter to the EVM. Before the fix a node started with --vm.opcode.optimize kept the flag per interpreter, so a child call inside a STATICCALL that switched to the optimized interpreter could run SSTORE. The pull request says this produced a bad block. Pull requests 3584 and 3627 fixed stack bounds and a comparison in the same interpreter, and v1.8.0-alpha removed the feature (CHANGELOG.md on the master branch, lines 101 to 102, 283 and 333 to 334).", "source": BSC_PR, "relevance": "low"},
   {"delta": "params/protocol_params.go at tag v1.8.2 sets MaxTxGas to 1 << 24 (16,777,216). eth_estimateGas of an endless loop on the public endpoint fails with gas required exceeds allowance (16777216).", "source": BSC_PP, "relevance": "low"},
   {"delta": "core/vm/evm.go at tag v1.8.2, lines 291 to 347: Call skips the balance check and the value transfer when the caller of the frame is params.SystemAddress. This is the code behind finding F-058 and it is unchanged in the Jenner client.", "source": BSC_EVM, "relevance": "low"}
  ]},
 {"chainId": 56, "lens": "L2",
  "summary": "Nothing new on transaction boundaries. One public endpoint runs reth-bsc v0.1.4-hotfix, a release that corrects a state root calculation fault inherited from Reth.",
  "deltas": [
   {"delta": "reth-bsc v0.1.4-hotfix (2026-11-06) carries an upstream Reth fix for a state root that the legacy calculation path could compute wrongly under specific trie conditions. https://bsc-rpc.publicnode.com reports reth-bsc/v0.1.4-hotfix-23b510f. The fault concerns which blocks a node accepts. It gives an ordinary account no way to change PoolManager state.", "source": RETH_BSC, "relevance": "none"}
  ]},
 {"chainId": 56, "lens": "L3",
  "summary": "The four fee and reflection tokens of lead L-331 take their fee from the recipient, so a payout never costs the PoolManager more than the amount. The log endpoint bsc.api.pocket.network again returned an empty list for an old range that holds transfers, which archive state and a second log source both show.",
  "deltas": [
   {"delta": "With Multicall3 code at the PoolManager address, transfers of one thousandth and of one third of the PoolManager balance of ASS, PIT, CATE and GFH to a fresh address and to 0xdead all returned true at block 135,335,118. The PoolManager balance fell by the amount minus a reflection share for ASS, PIT and CATE (11,572, 50,956 and 58 base units less on the small transfers) and by exactly the amount for GFH. The recipient received about 90 percent (ASS), 96 percent (PIT) and 99.99 percent (CATE).", "source": "rpc https://bsc-dataseed1.bnbchain.org (Geth v1.8.2) eth_call with state override, 2026-11-23; " + WORK + "l331_fee_tokens.json", "relevance": "low"},
   {"delta": "eth_getLogs on https://bsc.api.pocket.network for sNVB transfers out of the PoolManager in blocks 50,230,000 to 50,239,999 returned an empty list without an error. A request for the 500 blocks from 50,236,700 was empty as well. Archive eth_call on the same endpoint shows the PoolManager's sNVB balance falling at blocks 50,236,945 and 50,236,952 while the index is unchanged, and the NodeReal endpoint returns 13 such logs for the same 10,000 blocks, two of them in those two blocks. The pocket endpoint answered one 50,000 block request with a range limit of 10,001 blocks and another with a limit of 500.", "source": "rpc https://bsc.api.pocket.network eth_getLogs and eth_call at old blocks, rpc https://bsc-mainnet.nodereal.io eth_getLogs, 2026-11-23; " + WORK + "pocket_vs_nodereal.json and " + WORK + "snvb_bisect.log", "relevance": "high"}
  ]},
 {"chainId": 56, "lens": "L4",
  "summary": "Fifteen days before Jenner the addresses that the fork turns into native code hold no code on mainnet and answer every call with success and empty data. A transfer call to them from the PoolManager therefore succeeds and moves nothing until 2026-12-08.",
  "deltas": [
   {"delta": "At block 135,334,992 (timestamp 1,795,465,723, which is 1,231,277 seconds before JennerTime 1,796,697,000) eth_getCode returned 0x for 0x70, 0x7020000000000000000000000000000000000001, 0x7020000000000000000000000000000000000002, 0xCA5F000000000000000000000000000000000000 and 0xca52000000000000000000000000000000000001. balanceOf(PoolManager) and transfer(0xdead, 1) sent from the PoolManager address returned empty data without revert on all five.", "source": "rpc https://bsc-dataseed1.bnbchain.org (Geth v1.8.2) eth_getCode and eth_call, 2026-11-23; " + WORK + "special_probe.json", "relevance": "low"},
   {"delta": "A forum analysis reported by The Defiant on 2026-11-19 warns that the sample code of BEP-706 accepts a call to 0x70 that succeeds with no return data, which is what the address does before activation. The PoolManager makes no call to 0x70 unless a caller names it as a currency or hook.", "source": DEFIANT, "relevance": "none"}
  ]},
 {"chainId": 43114, "lens": "L1",
  "summary": "The block validity code of the C-Chain accepts legacy, access list and dynamic fee transactions only, so set code transactions and delegated accounts do not exist there. The Osaka opcode CLZ is undefined and no transaction gas cap exists below the block limit, which is ten seconds of gas capacity.",
  "deltas": [
   {"delta": "worstcase/state.go lines 181 to 193: ApplyTx validates each transaction with Accept set to LegacyTxType, AccessListTxType and DynamicFeeTxType. Blob and set code transactions fail validation. This answers the open question of the cycle 6 critic: a 0xef0100 designator placed by state override runs as code because the C-Chain has no rule that resolves it.", "source": AV_WC, "relevance": "low"},
   {"delta": "worstcase/state.go lines 123 to 155 and 295 to 297: the block gas limit is the gas rate times TauSeconds times Lambda (5 times 2), and a transaction is refused only when its gas limit exceeds what is left in the block. The latest block reports a gas limit of 80,000,000. eth_estimateGas of an endless loop with gas 30,000,000 fails with allowance (30000000), where BNB Smart Chain reports 16777216.", "source": AV_WC, "relevance": "low"}
  ]},
 {"chainId": 43114, "lens": "L2",
  "summary": "Two properties of the Continuous Execution engine were read in source. A transaction that consensus accepted and that then fails validation at execution time stops the executor with a fatal error. Imports of assets other than AVAX are rejected at tip, so nothing writes into the asset partition of a contract's storage today.",
  "deltas": [
   {"delta": "saexec/execution.go lines 346 to 364: the executor calls core.ApplyTransaction for each transaction and returns errFatal when it reports an error other than a revert. worstcase/state.go lines 202 to 209 carries a TODO that says a sender that holds code must still be handled during actual execution. The inclusion check rejects such a sender against the worst case state.", "source": AV_EXEC, "relevance": "low"},
   {"delta": "cchain/tx/import.go lines 112 to 129: the sanity check of an import rejects every input and output whose asset is not AVAX (errNonAVAXInput, errNonAVAXOutput). cchain/libevm/extstate/statedb.go lines 45 to 62 keeps contract storage under slot indexes with the lowest bit of the first byte cleared and asset balances under slot indexes with that bit set, and reads asset balances with SkipStateKeyTransformation.", "source": AV_IMP, "relevance": "low"}
  ]},
 {"chainId": 43114, "lens": "L3",
  "summary": "The exit question that cycle 1 left open is answered from source: no per transaction gas cap exists below the block limit of 80,000,000. A new block is refused while the execution queue holds more than two full blocks of gas, and every transaction pays for at least half of its gas limit.",
  "deltas": [
   {"delta": "params/params.go: Lambda is 2, Tau is 5 seconds, MaxFullBlocksInOpenQueue is 2 and MaxFullBlocksInClosedQueue is 3. worstcase/state.go line 124 returns ErrQueueFull when the queue holds more than two full blocks. eth_gasPrice on the public endpoint returned 7.5 gwei on 2026-11-23.", "source": AV_PARAMS, "relevance": "low"}
  ]},
 {"chainId": 43114, "lens": "L4",
  "summary": "Nothing new. No precompile or system contract was added since the sweep of cycle 5, and AvalancheGo v1.15.3 is still the version on the public endpoints.",
  "deltas": []}
]

findings = [
 {"ref": "new",
  "title": "A run of dust positions bounds how far one swap can move the price inside the transaction gas cap, and building it costs a fraction of one BNB or a few POL",
  "chainIds": [56, 137, 43114],
  "lens": "L3",
  "assumptions": ["A9"],
  "effect": "degrade",
  "actor": "unprivileged",
  "severity": "low",
  "difference": "BNB Smart Chain caps one transaction at 16,777,216 gas and Polygon at 33,554,432 gas, and Polygon charges 5460 gas for a cold storage read after PIP-88. The Avalanche C-Chain has no transaction cap below its block limit of 80,000,000 gas and charges at least half of the gas limit. Gas is cheap on all three: eth_gasPrice returned 0.05 gwei on BNB Smart Chain, 278 gwei of POL on Polygon and 7.5 gwei of AVAX on Avalanche on 2026-11-23. Ethereum has the same cap as BNB Smart Chain, and the cost of the attack in native units is what differs.",
  "mechanism": "1. Pool.swap runs one loop step for each initialized tick it reaches (src/libraries/Pool.sol:344-437). A step that ends on an initialized tick calls crossTick, which reads the liquidity word of the tick and reads and writes both fee growth words (src/libraries/Pool.sol:417-421 and 602-611). 2. Under Ethereum gas prices, which the BNB Smart Chain client keeps (cold read 2100, write of a non-zero slot 5000 including the cold read, fresh slot 20,000), that is three cold reads and two writes of non-zero slots, about 12,100 gas, plus the price and step arithmetic, about 16,500 gas in total. The first crossing of a tick whose fee growth words are still zero writes two fresh slots and costs about 51,000 gas. Under the Polygon prices the two figures are about 25,000 and 61,000. These figures are computed from the opcode prices in the client source and from the statements of the loop. They were not measured on chain, and the gas table of the C-Chain was not read in this cycle and is assumed equal to the Ethereum one for these opcodes. 3. One transaction can therefore cross about 1,000 already crossed ticks on BNB Smart Chain (330 on a first crossing), about 1,340 on Polygon (550) and about 4,800 on Avalanche (1,560). 4. Any account can initialize ticks. In a pool with tick spacing 1 it adds positions of one liquidity unit over consecutive ticks through modifyLiquidity (src/PoolManager.sol:145-184, src/libraries/Pool.sol:146-236). Each new tick costs the account about 70,000 gas (one position slot, one tick slot, one bitmap update) and a token amount of a few base units. 1,000 ticks cost about 70 million gas, which is 0.0035 BNB, about 19.5 POL or about 0.53 AVAX at the gas prices above. With tick spacing 1, 1,000 ticks span a price change of 10.5 percent. 5. A swap that has to move the price across more initialized ticks than the cap allows runs out of gas in every transaction. The caller can still swap in pieces, because the loop stops at sqrtPriceLimitX96 (src/libraries/Pool.sol:344 and 364) and each piece is a valid swap. A contract that needs the whole move in one call, such as a liquidation or a multi hop route with a fixed output, fails until it splits the swap. 6. The same bound applies without any attacker to a pool whose price sits far from its liquidity. An empty stretch costs one cold bitmap read and one step per word of 256 tick spacings (src/libraries/TickBitmap.sol:85-119). From MIN_TICK to tick 0 a pool with spacing 1 has 3,466 words, about 17 million gas at 5,000 gas per word, which is above the BNB Smart Chain cap. Finding F-102 records that any account can move the price of an empty pool for free. 7. Liquidity removal is not affected. Pool.modifyLiquidity updates two ticks, at most two bitmap words and one position and contains no loop (src/libraries/Pool.sol:146-236), so its gas does not depend on how many ticks exist.",
  "impact": "No funds are taken and no withdrawal is blocked. Swaps through the affected price range of one pool need several transactions, and integrations that swap in one call across the range revert. The cost to the attacker is a one time payment of gas. The cost to swappers repeats for each traversal. The largest Quoter simulation that cycle 5 ran on BNB Smart Chain used 11,518,424 gas, so real pools already come within a factor of 1.5 of the cap without any attack.",
  "preconditions": "A pool with a small tick spacing. Spacing 1 is the worst case because 1,000 ticks cover only 10.5 percent of price. The attacker needs gas and a few base units of both currencies. The price must have to cross the range, so the attack matters in volatile pairs and has no effect while the price stays on one side.",
  "mitigations": "Routers and liquidators should bound each swap with sqrtPriceLimitX96 and continue in a second transaction when the limit is reached. Pool creators who expect large price moves should choose a wider tick spacing, which raises the price range that a given number of ticks covers. Interfaces can read the tick bitmap through extsload to count initialized ticks on a route before sending a swap.",
  "coreRefs": ["src/libraries/Pool.sol:344-437", "src/libraries/Pool.sol:602-611", "src/libraries/Pool.sol:146-236", "src/libraries/TickBitmap.sol:85-119", "src/PoolManager.sol:145-184"],
  "sources": [
   {"url": BSC_PP, "supports": "MaxTxGas is 1 << 24 (16,777,216) in the BNB Smart Chain client at tag v1.8.2, line 31, and the storage prices are the Ethereum ones: ColdSloadCostEIP2929 2100, SstoreResetGasEIP2200 5000 and SstoreSetGasEIP2200 20000, lines 67 to 72."},
   {"url": BOR_PP, "supports": "MaxTxGas is 1 << 25 (33,554,432) in Bor at tag v2.11.1, line 32, and the PIP-88 constants are ColdSloadCostPIP88 5460 and ColdSstoreCostPIP88 2940, lines 76 and 77."},
   {"url": BOR_ACL, "supports": "gasSLoadPIP88 charges 5460 for a cold slot and gasSStorePIP88 charges 5000 minus 2940 for a write to a warm non-zero slot."},
   {"url": AV_WC, "supports": "On the C-Chain a transaction is refused only when its gas limit exceeds what is left of the block limit, which is the gas rate times ten seconds (lines 123 to 155 and 295 to 297). No Osaka rule applies there."},
   {"url": "rpc https://bsc-dataseed1.bnbchain.org, https://polygon-bor-rpc.publicnode.com and https://api.avax.network/ext/bc/C/rpc, eth_gasPrice, eth_getBlockByNumber and eth_estimateGas on 2026-11-23; " + WORK + "fork_gas_probe.json", "supports": "Block gas limits of 80,000,000, 160,000,000 and 80,000,000, gas prices of 0.05, 278 and 7.5 gwei, and the estimateGas allowance of 16777216 on BNB Smart Chain."}
  ],
  "evidence": "inferred"}
]

cleared = [
 {"chainIds": [137, 56, 43114], "lens": "L3",
  "check": "Exits: can an ordinary account make another user's liquidity removal or claim redemption impossible to include on these networks through gas caps, storage prices or the cost of tick crossings.",
  "result": "No. Removal runs Pool.modifyLiquidity, which has no loop and touches two ticks, at most two bitmap words, one position and the pool liquidity (src/libraries/Pool.sol:146-236). Its gas does not grow with the number of initialized ticks or positions. Under the Polygon storage prices of PIP-88 (cold read 5460, cold write surcharge 2940) the dozen cold slots of a removal add an estimated 40,000 gas to the 85,099 to 130,613 gas that the repository snapshots record for a removal (snapshots/PoolManagerTest.json:10-15). The caps are 16,777,216 gas on BNB Smart Chain, 33,554,432 on Polygon and the block limit of 80,000,000 on Avalanche. burn and take have no loop either (src/PoolManager.sol:291-297 and 331-336). The swap loop is the only part of core whose gas an outsider can raise, and that is filed as a finding of this cycle with effect degrade.",
  "source": BOR_PP + " ; " + BSC_PP + " ; " + AV_WC + " ; src/libraries/Pool.sol:146-236"},
 {"chainIds": [137, 56, 43114], "lens": "L4",
  "check": "Exits: special recipients. Can an outsider make the native payout of another user's take revert, or does any of the three chains refuse value transfers from the PoolManager to particular recipients.",
  "result": "No. The recipient of a take is chosen by the caller, and the native payout forwards all gas (src/types/Currency.sol:48). The earlier sweeps list the addresses that refuse value (system contracts that revert on empty calldata, the Polygon token contract 0x1010, the deprecated C-Chain precompiles), and a user reaches them only by naming them. The BNB Smart Chain client skips the value transfer only when the caller of the frame is the system address (core/vm/evm.go lines 291 to 347 at tag v1.8.2), which the PoolManager never is. The hard coded address filter of BNB Smart Chain applies to the sender and recipient of the top level transaction only, as cycle 1 recorded.",
  "source": BSC_EVM + " ; src/types/Currency.sol:44-52"},
 {"chainIds": [137], "lens": "L4",
  "check": "Known weakness and by design behaviour: the StateReceiver installed by Uburu lets any account replay a failed state sync. Can an ordinary account use the replay paths to make 0x1001 or FxChild call the PoolManager or its owner contract with data of its choice.",
  "result": "No. A replay must match the stored hash of receiver and data, or a leaf under the historic Merkle root, so the caller chooses only the time (StateReceiver.sol lines 85 to 133). The call is onStateReceive(uint256,bytes), which the PoolManager does not implement: an eth_call from 0x1001 to the PoolManager with that selector reverts with empty data. FxChild forwards to processMessageFromRoot on a receiver named in the record, and the PoolManager owner 0x8a1b966ac46f42275860f905dbc75efbfdc12374 reverts unless the caller is FxChild and the sender is the Ethereum timelock 0x1a9c8182c09f50c8318d769245bea52c32be35bc. Any Ethereum account can send a record through FxRoot, and FxRoot writes that account as the sender. Of the 25 failed records pending since Uburu, 23 are for FxChild, and none has the timelock as sender or the owner contract as receiver. The 67 historic leaves that have not been replayed were not enumerated and are a lead.",
  "source": SR_SRC + " ; rpc https://polygon-bor-rpc.publicnode.com eth_call, rpc https://mainnet.gateway.tenderly.co eth_getLogs, 2026-11-23; " + WORK + "polygon_statesync_since_uburu.json ; " + WORK + "polygon_owner_proxy_auth.json"},
 {"chainIds": [137], "lens": "L1",
  "check": "Known weaknesses of Bor disclosed in 2026 that earlier cycles did not judge: the four issues of v2.5.9 (handshake panic, header panic, state sync pagination, truncated block number checks) and the BlockSTM items of v2.10.3.",
  "result": "None gives an ordinary account a lever on PoolManager funds. The two panics and the two BlockSTM items stop or slow nodes. The pagination gap made nodes reject each other's blocks. The block number issue let an authorised producer present a block number far above the parent's, which matters to contracts that read block.number. The PoolManager bytecode has no NUMBER, TIMESTAMP or BLOCKHASH opcode (assumption A10) and its accounting closes inside one transaction (src/PoolManager.sol:104-114). The v2.10.3 post states that execution results are unchanged by its fixes, and the serial and parallel processors must agree on every block.",
  "source": BOR_259 + " ; " + BOR_2103},
 {"chainIds": [137], "lens": "L4",
  "check": "Known weakness: the 2021 fault in transferWithSig of the native token contract 0x1010, which moved POL without a balance check. Is the function live, and could it move the PoolManager's native balance.",
  "result": "The function is disabled. A call reverts with the string Disabled feature. A signature transfer debits the recovered signer, and no signature recovers to a contract address, so the PoolManager balance could not be the source even if the function were live. The mirror of the native balance at 0x1010 stays as finding F-008 describes.",
  "source": "rpc https://polygon-bor-rpc.publicnode.com eth_call to 0x0000000000000000000000000000000000001010 with selector 0x19d27d9c, 2026-11-23; " + WORK + "special_probe.json"},
 {"chainIds": [56], "lens": "L1",
  "check": "Known weakness: the superinstruction interpreter of BNB Smart Chain v1.7.x let SSTORE run inside a STATICCALL frame (pull request 3582). Does any accounting step of the PoolManager rely on the write protection of STATICCALL.",
  "result": "No. The PoolManager makes one kind of static call, balanceOf on a currency, in sync and in _settle (src/types/Currency.sol:94, src/PoolManager.sol:285 and 359). A token that could write or re-enter during that call would gain nothing over calling the PoolManager before or after it: sync stores the currency and the returned balance after the call (src/PoolManager.sol:285-286), and _settle reads the stored reserves before the call, credits only the currency it read at line 350 and then clears the slot (lines 358-364). In both places the returned number is already chosen by the token. A token that is not written by the attacker does not re-enter. The pull request describes the outcome as wrong gas use and a bad block on nodes that ran the optimized interpreter, which was an opt-in flag. The changelog records that v1.8.0-alpha removed the interpreter, and v1.8.2 is mandatory before 2026-12-08.",
  "source": BSC_PR + " ; " + BSC_CHG + " ; src/PoolManager.sol:279-288 and 349-365"},
 {"chainIds": [56], "lens": "L4",
  "check": "The fork boundary of Jenner on 2026-12-08. Until then a transfer call to 0x70 or to a CAS20 address succeeds with empty data. Can an account create a debt, a credit, a claim or pool liquidity in such a currency before the fork that becomes a claim on real tokens after it.",
  "result": "No. Before the fork take of such a currency succeeds and only debits the caller (src/PoolManager.sol:294-295, src/types/Currency.sol:64-74). A positive delta in it can come only from settle, which needs sync, and sync reverts because balanceOf returns no data (src/types/Currency.sol:94). mint adds a debt of the same size as the claim (src/PoolManager.sol:322-329). Pool operations move deltas between the caller, the hook and the pool and add to zero, so no unlock can close while any party owes the currency (src/PoolManager.sol:112). Nothing denominated in the currency can therefore exist in storage when the fork arrives, except pools with zero liquidity. After the fork an uncreated CAS20 address reverts on every call, as cycle 5 saw on Chapel, and a created token is an issuer matter (F-007, F-076).",
  "source": "rpc https://bsc-dataseed1.bnbchain.org eth_getCode and eth_call at block 135,334,992; " + WORK + "special_probe.json ; " + JENNER},
 {"chainIds": [56], "lens": "L3",
  "check": "Lead L-331: do PIT, ASS, CATE and GFH charge the PoolManager more than the amount when it transfers them.",
  "result": "No. Eight simulated transfers per token set (one thousandth and one third of the balance, to a fresh address and to 0xdead) at block 135,335,118 all returned a 32 byte true. For ASS, PIT and CATE the PoolManager balance fell by slightly less than the amount, because the fee is taken from what the recipient receives and part of it is reflected to holders, the PoolManager among them. For GFH it fell by exactly the amount. take debits the caller the requested amount (src/PoolManager.sol:294), so a payout leaves the PoolManager whole or a few thousand base units ahead.",
  "source": "rpc https://bsc-dataseed1.bnbchain.org (Geth v1.8.2) eth_call with Multicall3 code at the PoolManager address, 2026-11-23; " + WORK + "l331_fee_tokens.json"},
 {"chainIds": [56], "lens": "L3",
  "check": "Lead L-160, reflection tokens: can a caller profit by putting its own transfer of a reflection token between sync and settle, so that the reflected fee on the PoolManager balance is credited to it.",
  "result": "No. settle credits the rise of the PoolManager balance since sync (src/PoolManager.sol:358-360). A transfer of one third of the PoolManager's PIT balance (168,336,790 PIT) paid a fee of about 6,733,000 PIT and raised the PoolManager balance by 0.0113 PIT. For ASS the same test paid about 1,604,000 ASS and raised it by 0.0026 ASS. The caller pays the whole fee and can be credited only the PoolManager's share of it, which is about two parts in a billion. Reflection that accrued before the sync is already inside the stored reserves and is credited to nobody.",
  "source": "rpc https://bsc-dataseed1.bnbchain.org (Geth v1.8.2) eth_call with Multicall3 code at the PoolManager address, 2026-11-23; " + WORK + "l331_fee_tokens.json"},
 {"chainIds": [137, 56, 43114], "lens": "L3",
  "check": "Lead L-303, second half: is the transfer limit plugin of ViciCoin used by another pooled token on Polygon, and does it exist on the other two chains.",
  "result": "No. Every one of the 7,428 logs of the plugin 0xf58fed40fba1ab7aa7ffc160b863bedd998386a7 on Polygon names VCNT in an indexed topic, so the contract serves that one token. The plugin address and the VCNT address hold no code on BNB Smart Chain and Avalanche. Another issuer of the same framework would deploy its own plugin, which this check cannot see.",
  "source": "rpc https://polygon.gateway.tenderly.co eth_getLogs from block 40,000,000 to 97,840,247; rpc eth_getCode on the three endpoints, 2026-11-23; " + WORK + "l303_plugin_logs.json"},
 {"chainIds": [43114], "lens": "L1",
  "check": "Open question of the cycle 6 and cycle 7 critics: does the C-Chain accept set code transactions, so that an account can carry a delegation and act as a hook or as a caller with code.",
  "result": "No. The code that decides block validity under Continuous Execution validates each transaction with an accept mask of legacy, access list and dynamic fee types (worstcase/state.go lines 181 to 193) and rejects a sender that holds code (lines 202 to 209). The CLZ opcode of Osaka is undefined on the public endpoint, which matches a rule set without the later Ethereum forks. Code at a hook address on the C-Chain can therefore change only through a contract's own upgrade path, as on Ethereum before EIP-7702 (assumption A7, src/libraries/Hooks.sol:337-339).",
  "source": AV_WC + " ; rpc https://api.avax.network/ext/bc/C/rpc eth_call with data 0x60011e5f5260205ff3, 2026-11-23"},
 {"chainIds": [43114], "lens": "L2",
  "check": "By design behaviour of Continuous Execution: consensus accepts a block before it is executed, includes a transaction when the sender can pay its worst case cost, and treats an execution error as fatal. Does any of this break the atomic settlement that unlock relies on, or let state reach the PoolManager outside a transaction.",
  "result": "No. Execution still applies transactions one by one with core.ApplyTransaction, in block order, each on the state left by the one before (saexec/execution.go lines 346 to 364), and cycle 2 showed that each call resets transient storage. A transaction that reverts is still included and charged, and all PoolManager state it wrote is rolled back with it. The fatal branch concerns a transaction that is invalid at execution time, which the worst case check exists to exclude. It would stop the chain for everyone and gives no account PoolManager funds. Whether an ordinary account can reach that branch is filed as a low lead.",
  "source": AV_EXEC + " ; " + AV_CE},
 {"chainIds": [43114], "lens": "L2",
  "check": "Can a cross-chain import write into the storage of the PoolManager account. The C-Chain keeps balances of other X-Chain assets inside the storage trie of the holder.",
  "result": "No. At tip an import whose inputs or outputs carry an asset other than AVAX is rejected (cchain/tx/import.go lines 112 to 129). Asset balances live under slot indexes with the lowest bit of the first byte set, and contract code can only reach slot indexes with that bit cleared (cchain/libevm/extstate/statedb.go lines 45 to 62 and 124 to 171). An AVAX import raises the native balance, which cycle 2 cleared.",
  "source": AV_IMP + " ; " + AV_EXT},
 {"chainIds": [56], "lens": "L2",
  "check": "Known weaknesses of the BNB Smart Chain clients in the Jenner release line that earlier cycles did not judge: the reth-bsc state root fault fixed in v0.1.4-hotfix, the per byte pricing of precompile 0x68, and the BEP-706 sample code that accepts an empty answer from 0x70.",
  "result": "None reaches PoolManager funds through an ordinary account. The state root fault decides which blocks a reth-bsc node accepts. The pricing change concerns a precompile that the PoolManager never calls and that reverts on its call shapes, as the earlier sweeps showed. The empty answer of 0x70 before activation affects contracts that read the timestamp from it. The PoolManager reaches 0x70 only when a caller names it as currency or hook: sync reverts on the empty answer before the fork and stores a timestamp that is constant inside a block after it, so settle credits zero (src/PoolManager.sol:358-360).",
  "source": RETH_BSC + " ; " + BSC_CHG + " ; " + DEFIANT}
]

leads = [
 {"chainIds": [137], "lens": "L4",
  "question": "Which of the 67 historic failed state syncs that remain replayable under failedStateSyncsRoot of the StateReceiver (leafCount 76, replayCount 9) carry FxChild as receiver, the Ethereum timelock 0x1a9c8182c09f50c8318d769245bea52c32be35bc as sender and the PoolManager owner 0x8a1b966ac46f42275860f905dbc75efbfdc12374 as target, and does that contract execute a message a second time or out of order?",
  "why": "Any account can replay such a record at a time of its choice. A governance message that failed years ago, for example a change of an owner or a fee setter, would then run as PoolManager owner today (src/ProtocolFees.sol:29-32). The author of the message is governance, so this extends F-010 and is outside the unprivileged scope unless such a leaf exists.",
  "priority": "low"},
 {"chainIds": [43114], "lens": "L2",
  "question": "Can an ordinary account get a transaction accepted by consensus that core.ApplyTransaction rejects at execution time, for example a sender that holds code by then, so that the executor of every node stops with errFatal (saexec/execution.go line 363, worstcase/state.go lines 202 to 209)?",
  "why": "A stopped executor halts the C-Chain, and with it every withdrawal from the PoolManager, until a client release. The source marks the sender with code case as not yet handled. Without set code transactions no way to give a signing account code is known, and ACP-209 would add one.",
  "priority": "low"},
 {"chainIds": [56, 137, 43114], "lens": "L3",
  "question": "What is the measured gas of one tick crossing and of one empty bitmap word in Pool.swap on the three deployed PoolManagers, taken from Quoter results on a pool whose initialized ticks are counted from the bitmap through StateView?",
  "why": "The finding on dust positions rests on figures computed from opcode prices (16,500 and 51,000 gas per crossing, 25,000 and 61,000 on Polygon). A measurement would turn the bound on ticks per transaction into a primary fact and would show how close existing pools are to it.",
  "priority": "low"}
]

l464_default = "Partly done. The fault of the endpoint was reproduced on 2026-11-23: eth_getLogs through bsc.api.pocket.network for sNVB transfers out of the PoolManager in blocks 50,230,000 to 50,239,999 returned an empty list without an error, while archive balances from the same endpoint show two outflows at blocks 50,236,945 and 50,236,952 and the NodeReal endpoint returns 16 logs for the 50,000 blocks that start there. The sNVB history was then read again from NodeReal. The 393 rows of cycle 5 and the Initialize census of 78,255 currencies were not repeated."

lead_results = [
 {"leadId": "L-464", "outcome": "inconclusive", "answer": (L464["answer"] if L464 else l464_default)},
 {"leadId": "L-160", "outcome": "finding", "answer": "The ledger already holds the answer for rebases and reward claims, and this unit adds the reflection case. Public rebases: the staked tokens of five Olympus forks on Polygon and BNB Smart Chain (F-066), with payouts or claim mints of the surplus on record for sSAC, sLGNS and sATH (F-091). Reward claims paid to the holder: QI for the qiAVAX balance on Avalanche (F-060). Reflection: a caller that brackets its own transfer of PIT or ASS with sync and settle pays the whole fee and is credited the PoolManager's share of it, about two parts in a billion in the simulation of this cycle, so that route has no gain. No new token of the first two kinds was looked for in this cycle."},
 {"leadId": "L-294", "outcome": "inconclusive", "answer": "Not examined again by this unit. For BNB Smart Chain the ledger holds QANX and seventeen tokens of one generator family (F-078) and FACTR and TC (F-095), found by the full balance transfer test of cycle 5 on 3,369 currencies. No new token list was tested in this cycle, so pooled tokens outside that list are still unchecked."},
 {"leadId": "L-303", "outcome": "inconclusive", "answer": "The first half is an action for the token owner and has not happened: on 2026-11-23 the exemption list of ViciCoin still has 57 entries without the PoolManager, the limit is 6 VCNT per day and the PoolManager holds 11.39 VCNT. The second half is answered for the three chains of this unit: the plugin contract serves only VCNT on Polygon (all 7,428 of its logs name that token) and has no code on BNB Smart Chain or Avalanche. Tokens of the same framework with a plugin instance of their own were not searched for on the other 18 networks."},
 {"leadId": "L-331", "outcome": "cleared", "answer": "For PIT, ASS, CATE and GFH on BNB Smart Chain a transfer of amount a from the PoolManager lowers its balance by a or by slightly less, never by more. The test used Multicall3 code at the PoolManager address, two amounts and two recipients per token, at block 135,335,118. The fee of ASS (about 10 percent), PIT (about 4 percent) and CATE (0.01 percent) is taken from what the recipient receives. The tokens of Ethereum and Base in the lead belong to other units, and cycle 7 tested 13,001 priced currencies on all networks for a charge on top."},
 {"leadId": "L-346", "outcome": "inconclusive", "answer": "Jenner is not active yet. At block 135,334,992 the chain was 1,231,277 seconds before the activation time 1,796,697,000, and the registry 0x7020000000000000000000000000000000000001, the policy registry, the factory address and 0x70 hold no code and answer with empty data. The questions of the lead can be answered from 2026-12-08 on."}
]

doc = {"unit": "established-l1", "_lenses": ["L1", "L2", "L3", "L4"], "profiles": profiles, "findings": findings, "cleared": cleared, "leads": leads, "leadResults": lead_results}
if L464:
    for k in ("profile_delta", "cleared", "lead", "finding"):
        if L464.get(k):
            if k == "profile_delta":
                [p for p in profiles if p["chainId"] == 56 and p["lens"] == "L3"][0]["deltas"].append(L464[k])
            elif k == "cleared": cleared.append(L464[k])
            elif k == "lead": leads.append(L464[k])
            elif k == "finding": findings.append(L464[k])
json.dump(doc, open(OUT, "w"), indent=1, ensure_ascii=False)
print("wrote", OUT, len(findings), "findings", len(cleared), "cleared", len(leads), "leads")
