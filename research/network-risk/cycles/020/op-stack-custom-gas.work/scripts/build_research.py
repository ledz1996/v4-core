"""Builds cycles/020/op-stack-custom-gas.research.json from the outputs in ../out. Usage: python3 build_research.py"""
import json, os
W = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
O = os.path.join(W, 'out')
R = os.path.abspath(os.path.join(W, '..', 'op-stack-custom-gas.research.json'))
WD = 'research/network-risk/cycles/020/op-stack-custom-gas.work'
fm = json.load(open(os.path.join(O, 'failedmsgs-celo.json')))
sh = json.load(open(os.path.join(O, 'ruint120_shifts.json')))
DATE = '2026-11-25'
U_CK = 'https://github.com/celo-org/celo-kona/releases'
U_XR = 'https://github.com/okx/xlayer-reth/releases'
U_NI_A = 'https://raw.githubusercontent.com/okx/reth/81573d2c7d806d5df9ff2d512dd000c2bf542b1b/crates/trie/trie/src/node_iter.rs'
U_NI_B = 'https://raw.githubusercontent.com/okx/reth/f60420aaac6457295a38b66bd544bab28ab6ec5d/crates/trie/trie/src/node_iter.rs'
U_LK_A = 'https://raw.githubusercontent.com/okx/xlayer-reth/v0.0.7.3/Cargo.lock'
U_LK_B = 'https://raw.githubusercontent.com/okx/xlayer-reth/v0.0.7.3-rc.1/Cargo.lock'
U_RU = 'https://static.crates.io/crates/ruint/ruint-1.20.0.crate'
U_RU18 = 'https://static.crates.io/crates/ruint/ruint-1.18.0.crate'
U_RI = 'https://static.crates.io/crates/revm-interpreter/revm-interpreter-35.0.1.crate'
U_ADV = 'https://raw.githubusercontent.com/rustsec/advisory-db/main/crates/ruint/RUSTSEC-2026-0220.md'
U_ADV2 = 'https://raw.githubusercontent.com/rustsec/advisory-db/main/crates/ruint/RUSTSEC-2025-0137.md'
U_KS = 'https://specs.optimism.io/protocol/karst/overview.html'
U_U19 = 'https://docs.optimism.io/notices/upgrade-19'
U_CF = 'https://forum.celo.org/t/h1-2026-engineering-retro-h2-2026-roadmap/13528'
U_XS = 'https://status.xlayer.tech/maintenance'
U_XC = 'https://raw.githubusercontent.com/okx/xlayer-reth/v0.0.7.3-rc.1/crates/chainspec/src/lib.rs'
U_BP_C = 'https://eth.blockscout.com/api/v2/smart-contracts/0x2c431080fc733e259654f3b91e39468d9a85ac9b'
U_BP_O = 'https://eth.blockscout.com/api/v2/smart-contracts/0xb20b23af6071405c37ddda0c0640e8ebb7899645'
U_SAFE_C = 'https://safe-transaction-mainnet.safe.global/api/v1/safes/0x4092A77bAF58fef0309452cEaCb09221e556E112/'
U_SAFE_X = 'https://safe-transaction-mainnet.safe.global/api/v1/safes/0xC290bE56089BCC83c6993583ce2cF51a7951D45A/'
U_GOMOD = 'https://raw.githubusercontent.com/celo-org/op-geth/c7ed55b8/go.mod'
RPC_C = 'eth_call and eth_getBlockByNumber on https://forno.celo.org, ' + DATE
RPC_X = 'eth_call on https://rpc.xlayer.tech, ' + DATE
RPC_E = 'eth_call and eth_getStorageAt on https://ethereum-rpc.publicnode.com at block 26,494,156 (0x19444cc), ' + DATE

profiles = [
 {"chainId": 42220, "lens": "L1", "summary": "Unchanged builds: forno still answers reth/v2.2.0-74cc8bb (celo-reth v1.0.10, released 20 November 2026) and, on some requests, Geth/v0.1.0-untagged-c7ed55b8. The new fast paths that ruint 1.20.0 adds for 256 bit shifts and bit counts were transcribed and agree with the EVM definition on " + format(sh['checks'], ',') + " checks; the battery, targeted set, two script sets and 144 mined swaps match on both backends.",
  "deltas": [
   {"delta": "celo-reth v1.0.9 (5 November 2026) bumps celo-org/reth for a trie seek-boundary fix, and v1.0.10 (20 November 2026) patches revm only for a SELFDESTRUCT tracing bug (bluealloy/revm#3805) and states that block execution and state are not affected. No release from celo-kona main exists yet.", "source": U_CK, "relevance": "low"},
   {"delta": "ruint 1.20.0, the integer library under celo-reth, computes U256 wrapping_shl, wrapping_shr (and so arithmetic_shr), leading_zeros and trailing_ones through new branch-free u128 pair code with a saturating u32 shift amount (src/bits.rs, shift_amount and the as_primitives u256 arms). ruint 1.18.0 on X Layer uses the generic limb loop. revm-interpreter 35.0.1 reaches this code from SHL, SHR, SAR and SIGNEXTEND.", "source": U_RU, "relevance": "low"}
  ]},
 {"chainId": 42220, "lens": "L2", "summary": "The op-geth backend behind forno did not stop at block 75,046,581. Pinned to each backend, blocks 75,046,580 to 75,046,582, 76,000,000, 80,000,000 and 83,000,000 have the same hash on op-geth, celo-reth, Ankr and Stakely, and op-geth's head was within two blocks of celo-reth's.",
  "deltas": [
   {"delta": "forno's op-geth c7ed55b8 backend follows the canonical chain at head (block 83,732,724 on 2026-11-25) and agrees on the hash of block 75,046,581, the block op-geth pull request 509 says it once rejected.", "source": RPC_C, "relevance": "low"}
  ]},
 {"chainId": 42220, "lens": "L3", "summary": "Karst, which brings the EIP-7825 cap of 16,777,216 gas per transaction, is planned for Celo in Q4 2026 with no date; CLZ is still refused today. No change to CELO or fee currencies.",
  "deltas": [
   {"delta": "Celo's H2 2026 roadmap lists the Karst hardfork for Q4 2026, pending readiness, without a date.", "source": U_CF, "relevance": "low"}
  ]},
 {"chainId": 42220, "lens": "L4", "summary": "The Celo portal implementation 0x2c431080 (OptimismPortal2 5.1.1) now has verified source on Blockscout. It emits TransactionDeposited in _depositTransaction (reached from depositTransaction and depositERC20Transaction) and in setGasPayingToken, which only SystemConfig can call.",
  "deltas": [
   {"delta": "Verified source of OptimismPortal2 5.1.1 at 0x2c431080fc733e259654f3b91e39468d9a85ac9b on Ethereum: the deposit sender is msg.sender for an EOA or a 23 byte EIP-7702 delegation, and the L1 to L2 alias otherwise (lines 745-748).", "source": U_BP_C, "relevance": "low"}
  ]},
 {"chainId": 196, "lens": "L1", "summary": "The endpoint still reports reth/v2.3.0-f60420a xlayer/v0.0.7. The okx/reth revision f60420aa differs from 81573d2c, which the final tag v0.0.7.3 pins, by a fix to the state root walk in the trie node iterator; the EVM crates are the same. The battery, targeted set, two script sets and 2,151 mined swaps match.",
  "deltas": [
   {"delta": "xlayer-reth v0.0.7.3-rc.1 (5 November 2026), published after the final v0.0.7.3 (30 October), is the mandatory release with the trie correctness fix, and pins okx/reth f60420aa. In crates/trie/trie/src/node_iter.rs the seek skip changes from key.starts_with(seek_prefix) to key == seek_prefix. Lock files of the two tags differ only in the okx/reth revision.", "source": U_NI_B, "relevance": "low"}
  ]},
 {"chainId": 196, "lens": "L2", "summary": "The X Layer mainnet hard fork of 10 November 2026 (op-node xlayer/v0.1.7 with xlayer-reth v0.0.7.3) left the EVM fork list ending at Jovian; CLZ is refused today.",
  "deltas": [
   {"delta": "X Layer status lists a mainnet hard fork completed on 10 November 2026; the v0.0.7.3-rc.1 chain spec still lists forks up to Jovian (timestamp 1764691201) and no Karst.", "source": U_XS, "relevance": "low"}
  ]},
 {"chainId": 196, "lens": "L3", "summary": "Nothing new on OKB as gas token. The gasless path was changed in v0.0.7 to isolate the base fee bypass per transaction; it concerns fee charging, not PoolManager balances.", "deltas": []},
 {"chainId": 196, "lens": "L4", "summary": "The X Layer portal upgrade path is a 2 of 3 Safe of EOAs with no module, no guard and no pending transaction in the Safe service on 2026-11-25.",
  "deltas": [
   {"delta": "Safe 0xC290bE56089BCC83c6993583ce2cF51a7951D45A, owner of the portal ProxyAdmin: threshold 2 of 3, nonce 3, modules empty, guard slot zero, no queued multisig transaction.", "source": U_SAFE_X, "relevance": "low"}
  ]},
]

findings = [
 {"ref": "new", "title": "X Layer final release tag v0.0.7.3 lacks the trie seek fix that the public endpoint and the later rc.1 tag carry",
  "chainIds": [196], "lens": "L1", "assumptions": ["A14"], "effect": "degrade", "actor": "operator", "severity": "info",
  "difference": "X Layer published the trie correctness fix as v0.0.7.3-rc.1, five days after the final v0.0.7.3. The final tag pins okx/reth 81573d2c, whose node_iter.rs skips a seek whenever the walker key starts with the seek prefix; rc.1 pins f60420aa, which skips only at the exact prefix.",
  "mechanism": "The change sits in the state root walk, not in the EVM. A node built from the final tag may skip hashed entries between a seek prefix and a deeper stored branch, compute a different state root for a block that touches such a storage layout, and reject or fork from the canonical chain. The PoolManager's arithmetic, storage writes and settlement are computed by the same revm 40.0.3 and ruint 1.18.0 in both builds, so balances and pool state come out the same. The endpoint runs f60420aa. Which revision the sequencer runs is not public.",
  "impact": "No PoolManager funds move. A follower or RPC node on the final tag could stall or serve a fork, so users reading it would see stale pool state.",
  "preconditions": "An operator runs v0.0.7.3 instead of v0.0.7.3-rc.1.",
  "mitigations": "Integrators that read X Layer pool state should use nodes that report f60420a in web3_clientVersion.",
  "coreRefs": ["src/PoolManager.sol:104-114"],
  "sources": [{"url": U_XR, "supports": "v0.0.7.3 (30 October) is synced to okx/reth 81573d2; v0.0.7.3-rc.1 (5 November) is a mandatory patch that integrates the trie correctness fix"},
              {"url": U_NI_A, "supports": "81573d2c node_iter.rs line 284 uses key.starts_with(&seek_prefix)"},
              {"url": U_NI_B, "supports": "f60420aa node_iter.rs line 282 uses key == &seek_prefix and adds a regression test for an inserted leaf before a deeper stored branch"},
              {"url": U_LK_A, "supports": "lock file of v0.0.7.3 pins okx/reth 81573d2c7d806d5df9ff2d512dd000c2bf542b1b; all other packages equal those of rc.1"}],
  "evidence": "primary"},
 {"ref": "F-140", "title": "OP Stack portal upgraders can emit a deposit whose sender is the PoolManager, and on Celo and X Layer nothing on chain delays such an upgrade",
  "chainIds": [42220, 196], "lens": "L2", "assumptions": ["A8", "A12"], "effect": "siphon", "actor": "governance", "severity": "high",
  "difference": "The portal ProxyAdmin owners on Ethereum are plain Safes. Celo's is a 2 of 2 Safe whose owners are two 6 of 8 Safes; X Layer's is a 2 of 3 Safe of EOAs. None of the four Safes has a module or a guard, so an upgrade executes as soon as it is signed.",
  "mechanism": "As recorded in F-140, the ProxyAdmin owner can replace the portal implementation with one that emits TransactionDeposited with the PoolManager as sender, and the L2 then runs a transfer whose msg.sender is the PoolManager without entering unlock (src/PoolManager.sol:104-114). The deployed implementations today cannot do this: the verified source of 0x2c431080 (Celo, version 5.1.1) emits the event only in _depositTransaction, where from is msg.sender or its alias, and in setGasPayingToken, which only SystemConfig may call and which fixes the sender to the depositor account. New here is the warning time: there is none on chain. The Safe transaction service lists no pending transaction for the Celo or X Layer owner Safe on 2026-11-25; the two inner Celo Safes each hold one stale proposal with a nonce below the current one.",
  "impact": "Every balance the PoolManager holds on Celo and X Layer, with no time for LPs to withdraw after a malicious upgrade is signed.",
  "preconditions": "Signers of the Celo or X Layer upgrade Safes act. No ordinary account can.",
  "mitigations": "LPs on these chains carry signer risk without a delay. A deployer can watch the owner Safes and the portal proxy for upgrades.",
  "coreRefs": ["src/PoolManager.sol:104-114", "src/PoolManager.sol:291-297"],
  "sources": [{"url": U_BP_C, "supports": "Celo portal 5.1.1 emits TransactionDeposited only at lines 757 and 771; sender rule at lines 745-748; setGasPayingToken restricted to SystemConfig at line 763"},
              {"url": U_SAFE_C, "supports": "Celo owner Safe: threshold 2, owners 0xC031... and 0x9Eb4..., modules empty"},
              {"url": U_SAFE_X, "supports": "X Layer owner Safe: threshold 2 of 3, modules empty"},
              {"url": "https://safe-transaction-mainnet.safe.global/api/v1/safes/0x4092A77bAF58fef0309452cEaCb09221e556E112/multisig-transactions/?executed=false", "supports": "no pending multisig transaction for the Celo owner Safe"},
              {"url": RPC_E, "supports": "guard slot 0x4a204f62... is zero on all four Safes; getModulesPaginated returns an empty list"}],
  "evidence": "primary"},
]

cleared = [
 {"chainIds": [42220, 196], "lens": "L1", "check": "Opcode battery (99,985 vectors) and targeted set (85,544 vectors) rerun on " + DATE + " for 42220 and 196, plus the battery pinned to each forno backend with pin.py (167 batches kept on reth/v2.2.0-74cc8bb and 167 on Geth/v0.1.0-untagged-c7ed55b8).",
  "result": "0 mismatches and 0 errors on both networks and on both pinned Celo backends. Outputs in " + WD + "/out/battery.json, battery-celo-reth.json, battery-celo-geth.json and targeted.json.",
  "source": "eth_call with state override on https://forno.celo.org and https://rpc.xlayer.tech, " + DATE},
 {"chainIds": [42220, 196], "lens": "L1", "check": "PoolManager script sets rerun: pmdiff.py (250 scripts) and pmdiff2.py (300 scripts, 16,263 calls) against Ethereum.",
  "result": "pmdiff2: 300 of 300 identical on both chains. pmdiff: 249 of 250 identical and none different; the one script left out failed on the Ethereum reference endpoint, so it had nothing to compare with. Outputs in " + WD + "/out/pmdiff.json and pmdiff2.json.",
  "source": "eth_call with state override on https://forno.celo.org, https://rpc.xlayer.tech and https://ethereum-rpc.publicnode.com, " + DATE},
 {"chainIds": [42220, 196], "lens": "L1", "check": "Recent mined swaps checked with swaps.py and replayed with replay.py.",
  "result": "Celo 144 swaps and X Layer 2,151: every tick relation exact; Celo 16 multi-step and 1 other swap replayed through the swap loop with no failure (up to 39 steps). Outputs in " + WD + "/out/swaps.json and replay.json.",
  "source": "eth_getLogs and eth_getStorageAt on https://forno.celo.org and https://rpc.xlayer.tech, " + DATE},
 {"chainIds": [42220], "lens": "L1", "check": "The u256 fast paths of ruint 1.20.0 (src/bits.rs: wrapping_shl and wrapping_shr built from two u128 halves with a branch-free mask and the saturating shift_amount, arithmetic_shr on top of them, leading_zeros, trailing_ones) together with the revm-interpreter 35.0.1 SHL, SHR, SAR and SIGNEXTEND handlers that call them. These feed TickBitmap.sol:38, 67, 73, 97 and 110, BitMath.sol:16-45, TickMath.sol:61-63, 111 and 142-150, and BalanceDelta.sol:24-27 and 63-69.",
  "result": "Transcribed into Python (" + WD + "/scripts/ruint120_shifts.py) and checked on " + format(sh['checks'], ',') + " cases: every shift amount 0 to 519 plus 2^32 and 2^64 neighbours and 2^255 and 2^256-1, on " + str(sh['values']) + " words (all powers of two and their neighbours, limb and half boundaries, random words), SIGNEXTEND for indexes 0 to 39, and the raw library shifts for amounts up to 4,095 and around 2^32. No mismatch. Planted faults were caught (127 for 128 in the cross term: 165,420 mismatches; a truncating shift amount: 1,790; a wrong leading_zeros branch: 7). The handlers only pass amounts below 256 to the library, so the u32 saturation never matters for the EVM. A native build of the crate was not run.",
  "source": U_RU},
 {"chainIds": [196], "lens": "L1", "check": "ruint 1.18.0 (X Layer) shift and SAR code against RUSTSEC-2026-0220, read from the crate.",
  "result": "1.18.0 has no primitive fast path: wrapping_shl and wrapping_shr call the generic overflowing loop, which returns zero once rhs / 64 reaches 4 (src/bits.rs lines 329-346 and 412-429), and arithmetic_shr fills with MAX.wrapping_shl(256 - rhs) (lines 467-478). The advisory's truncation modulo 2^32 is in the 1.19 fast paths, and its wrong flags are never read by revm-interpreter 37.0.3, which shifts only when the amount is below 256 (bitwise.rs lines 120-158). RUSTSEC-2025-0137 affects releases before 1.17.1 only.",
  "source": U_ADV},
 {"chainIds": [42220, 196], "lens": "L1", "check": "Jump destination analysis of revm-bytecode 10.0.0 and 11.0.1 for any code the PoolManager calls, including the DUPN, SWAPN and EXCHANGE padding logic.",
  "result": "The two crates have the same analyze_legacy. It marks every 0x5b outside PUSH data and pads with STOP; it does not skip immediates of DUPN, SWAPN or EXCHANGE, which are not active on either chain. The deployed PoolManager code on both chains has no CLZ, DUPN, SWAPN, EXCHANGE or SELFDESTRUCT in executable position and does not end inside PUSH data (" + WD + "/out/opscan.json).",
  "source": "https://static.crates.io/crates/revm-bytecode/revm-bytecode-10.0.0.crate"},
 {"chainIds": [42220], "lens": "L1", "check": "Critic note of cycle 19 that Celo's op-geth c7ed55b8 was not in the Go compiler fault scan.",
  "result": "It was scanned in cycle 18: cycles/018/theme-go-toolchain-shapes.work/out/scan-celo-op-geth-c7ed55b8.json holds 28 candidates, 21 of tier A3u and 7 of tier B4, none of shape A, B1 or B3; 141 files were fetched. Its go.mod pins holiman/uint256 v1.3.2, one of the two library versions scanned. Today's battery pinned to that backend also matches.",
  "source": U_GOMOD},
 {"chainIds": [42220, 196], "lens": "L1", "check": "Karst opcode change for the deployed bytecode (CLZ, EIP-7939), with Karst assumed live on both chains within six months.",
  "result": "CLZ is refused today on both chains (EVM error NotActivated for code 0x60011e). The PoolManager code has no 0x1e in executable position, so activation changes no result it computes; a new opcode only replaces an invalid one and does not change jump analysis.",
  "source": RPC_X},
 {"chainIds": [42220, 196], "lens": "L3", "check": "Karst EIP-7825 cap of 16,777,216 gas per transaction, assumed live: can an ordinary account push another user's exit above it?",
  "result": "Removing liquidity touches the position and two ticks (src/libraries/Pool.sol:146 onward, updateTick at 520) and settlement is a fixed number of calls (src/PoolManager.sol:291-307, 332), so its gas does not depend on what others do. Only a swap loops over ticks (src/libraries/Pool.sol:344-348), and the swapper can set a closer sqrtPriceLimitX96 and split the swap. An attacker who fills ticks raises the gas of large swaps only. Deposits are exempt from the cap per the Karst notice. The hook gas of a pool is a pool-creator matter.",
  "source": U_U19},
 {"chainIds": [42220], "lens": "L2", "check": "Lead L-895: is forno's op-geth backend stalled or on another chain?",
  "result": "No. Pinned batches gave identical block hashes from op-geth and celo-reth at blocks 75,046,580, 75,046,581, 75,046,582, 76,000,000, 80,000,000 and 83,000,000, identical to Ankr (reth/v2.2.0-74cc8bb) and Stakely (reth/v2.2.0-7680d6d); op-geth's latest block was 83,732,724 against 83,732,722 on celo-reth (" + WD + "/out/fornogeth.json, fornoheads.json).",
  "source": RPC_C},
 {"chainIds": [42220, 10, 130, 57073, 1868], "lens": "L2", "check": "Lead L-899: verified source of the portal implementations 0x2c431080 (Celo) and 0xb20b23af (OP Mainnet, Unichain, Ink, Soneium).",
  "result": "Both are verified on Blockscout as OptimismPortal2 compiled with solc 0.8.15. 0xb20b23af (version 6.1.0) emits TransactionDeposited once, in depositTransaction, with from = msg.sender when EOA.isSenderEOA() holds (tx.origin or a 23 byte 0xef0100 delegation) and the alias otherwise (lines 781-794). 0x2c431080 (version 5.1.1) emits it in _depositTransaction with the same rule (lines 745-757), reached from depositTransaction and depositERC20Transaction, and in setGasPayingToken, which reverts unless msg.sender is SystemConfig and uses the fixed depositor account as sender (lines 762-783). No function lets a caller choose the sender.",
  "source": U_BP_C},
]

hits = fm['withPoolManager']
l790 = ("Celo only (the other eight chains are outside this unit). FailedRelayedMessage logs of the L2CrossDomainMessenger 0x4200...0007 from the L2 migration block " + format(fm['from'], ',') + " to " + format(fm['to'], ',') +
        " in " + str(fm['ranges']) + " windows of 5,000 blocks: " + str(fm['failedRelays']) + " failed relays, " + str(len(fm['unrecovered'])) + " windows unrecovered, and " + str(len(hits)) +
        " whose relaying transaction input contains the PoolManager address 0x288dc841. ")
if hits:
    l790 += "Hits: " + "; ".join(h['tx'] + " at block " + str(h['block']) for h in hits[:5]) + "."
    l790_out = 'finding'
else:
    l790 += "No failed message on Celo pays the PoolManager, so there is nothing to replay into a sync and settle. Output in " + WD + "/out/failedmsgs-celo.json."
    l790_out = 'cleared' if not fm['unrecovered'] else 'inconclusive'
if not hits:
    cleared.append({"chainIds": [42220], "lens": "L4", "check": "Lead L-790 on Celo: failed L2CrossDomainMessenger messages whose recipient is the PoolManager.", "result": l790, "source": "eth_getLogs and eth_getTransactionByHash on https://forno.celo.org, " + DATE})

leads = [
 {"chainIds": [42220], "lens": "L1", "question": "Run a release build of ruint 1.20.0 and 1.18.0 natively against the shift, division and mulmod vectors, since this cycle could only transcribe the new u128 fast paths into Python (a native build was refused in this session).", "why": "A compiler fault in the branch-free u128 code would not show in a transcription; the endpoints pass all vectors, so this matters only for inputs not yet tried.", "priority": "low"},
 {"chainIds": [196], "lens": "L1", "question": "Which okx/reth revision does the X Layer sequencer run: 81573d2c from the final v0.0.7.3 tag or f60420aa from the later rc.1?", "why": "A sequencer without the trie seek fix could produce a state root that followers with the fix reject.", "priority": "low"},
 {"chainIds": [42220], "lens": "L1", "question": "When Celo sets a Karst time, which celo-reth release carries it, and do the battery, targeted set and script sets still match on it with CLZ active?", "why": "Karst is Celo's next EVM fork and its client release does not exist yet.", "priority": "low"},
]

leadResults = [
 {"leadId": "L-899", "outcome": "cleared", "answer": "Verified source exists on Blockscout for both. 0xb20b23af (OptimismPortal2 6.1.0) emits TransactionDeposited only in depositTransaction; 0x2c431080 (OptimismPortal2 5.1.1, Celo) only in _depositTransaction (via depositTransaction and depositERC20Transaction) and in setGasPayingToken, which only SystemConfig may call and which fixes the sender to the depositor account. The sender is msg.sender for an EOA or 7702 delegation and its alias otherwise. No function takes a caller-chosen sender."},
 {"leadId": "L-895", "outcome": "cleared", "answer": "forno's op-geth backend is at head and on the canonical chain: pinned per backend, block hashes at 75,046,580 to 75,046,582, 76,000,000, 80,000,000 and 83,000,000 equal celo-reth's, Ankr's and Stakely's, and its head was two blocks from celo-reth's. It did not stop at 75,046,581."},
 {"leadId": "L-857", "outcome": "inconclusive", "answer": "No celo-reth release from celo-kona main yet: the newest releases are v1.0.9 (trie seek-boundary fix) and v1.0.10 (20 November 2026, revm patched for a SELFDESTRUCT tracing bug only). Today's battery, targeted set and scripts pass on the current backend."},
 {"leadId": "L-858", "outcome": "cleared", "answer": "v0.0.7.3-rc.1 was published on 5 November, after the final v0.0.7.3 of 30 October, as the mandatory trie correctness patch. Its only lock file change is okx/reth 81573d2c to f60420aa, and in crates/trie/trie/src/node_iter.rs the seek skip changes from starts_with to exact equality; walker, cursors, sparse trie, payload processor, executor and revm cache files are identical. The EVM result is the same; recorded as an operator-level info finding."},
 {"leadId": "L-831", "outcome": "inconclusive", "answer": "Operator level. The deps/optimism gitlink still cannot be read without the GitHub API; both tag lock files pin the same op-revm and alloy-op-evm path crates and revm 40.0.3."},
 {"leadId": "L-915", "outcome": "inconclusive", "answer": "Answered for Celo and X Layer only. Celo's ProxyAdmin owner 0x4092a77b is a 2 of 2 Safe of two 6 of 8 Safes, X Layer's 0xc290be56 a 2 of 3 Safe; none of the four has a module or a guard, so no on-chain delay applies, and the Safe service lists no pending transaction for either owner Safe on 2026-11-25. The seven other chains are outside this unit."},
 {"leadId": "L-084", "outcome": "finding", "answer": "Governance level, covered by F-140: the X Layer Safe can upgrade the portal, the derivation accepts the deposit, and this cycle found no delay or guard in front of it. Re-reported as F-140 for Celo and X Layer."},
 {"leadId": "L-790", "outcome": l790_out, "answer": l790},
 {"leadId": "L-733", "outcome": "inconclusive", "answer": "Operator level. No new public information on the Base or Celo sequencer flags; F-132 stays info."},
]

doc = {"unit": "op-stack-custom-gas", "_lenses": ["L1", "L2", "L3", "L4"], "profiles": profiles, "findings": findings,
       "cleared": cleared, "leads": leads, "leadResults": leadResults}
json.dump(doc, open(R, 'w'), indent=1)
print('wrote', R, len(findings), 'findings', len(cleared), 'cleared')
