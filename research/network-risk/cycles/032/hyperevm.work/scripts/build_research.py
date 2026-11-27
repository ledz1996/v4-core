"""Build cycles/032/hyperevm.research.json from the outputs in ../out."""
import json, os
H = os.path.dirname(os.path.abspath(__file__))
W = 'research/network-risk/cycles/032/hyperevm.work'
OUT = os.path.join(H, '..', '..', 'hyperevm.research.json')
OFF = 'https://rpc.hyperliquid.xyz/evm'; R1 = 'https://rpc.purroofgroup.com'; R2 = 'https://rpc.hyperlend.finance/archive'
TN = 'https://rpc.hyperliquid-testnet.xyz/evm'
C = [999]

profiles = [
    {"chainId": 999, "lens": "L1",
     "summary": "No arithmetic, jump or memory result differs from the specification. The official node passed the battery, the targeted set and both PoolManager script sets again at head 52,371,152, and 112 new edge vectors on jump destination analysis, RETURNDATACOPY bounds, zero length memory operations at huge offsets, long KECCAK256 inputs and EXP with high exponents return the specified result on the official mainnet node, both replicas, the testnet node and an Ethereum reth node. The two public replicas run different revm generations: f0cad31 pins revm 29.0.1, revm-interpreter 25.0.3 and ruint 1.16.0, while b92ad36 pins revm 43.0.3, revm-interpreter 43.0.2 and ruint 1.20.1, the same as nanoreth master.",
     "deltas": [
         {"delta": "112 new vectors (scripts/edges32.py): jumps into PUSH1 and PUSH32 data, into the data of a PUSH2 and a PUSH32 truncated at the end of the code, past the end of the code, to offset 0 when it holds a PUSH, and to valid JUMPDEST offsets plus 2^16, 2^32, 2^64, 2^128 and 2^255 for JUMP and taken JUMPI; a not-taken JUMPI with a bad destination and a loop back to a JUMPDEST at offset 0; RETURNDATACOPY with offset 1 and length 0 on empty return data, offset 33 length 0 and offset 0 length 33 after a 32 byte return, and offset plus length overflowing; MCOPY, KECCAK256, CALLDATACOPY and RETURNDATACOPY of length 0 at offsets 2^64, 2^200 and 2^256-1 with MSIZE unchanged; MLOAD at those offsets failing; MSIZE after MLOAD, MSTORE8 and MCOPY expansion by source and by destination; KECCAK256 over 135 to 8,191 bytes at unaligned offsets around the 136 byte rate; 42 EXP cases with exponents of 2^255 and above. 0 mismatches on all five endpoints.",
          "source": W + "/out/edges32.json (eth_call with code overrides on " + OFF + ", " + R1 + ", " + R2 + ", " + TN + " and https://ethereum-rpc.publicnode.com, 2026-11-27)",
          "relevance": "none"},
         {"delta": "The replica rpc.purroofgroup.com (reth/v0.1.0-f0cad31) is built from a nanoreth commit whose Cargo.lock pins revm 29.0.1, revm-interpreter 25.0.3 and ruint 1.16.0; rpc.hyperlend.finance/archive (b92ad36) pins revm 43.0.3, revm-interpreter 43.0.2 and ruint 1.20.1 with a Cargo.lock byte equal to master (sha256 e8cc9611370d). Every comparison that uses both replicas therefore compares two revm and ruint generations with each other and with the official node.",
          "source": "https://raw.githubusercontent.com/hl-archive-node/nanoreth/f0cad31/Cargo.lock and https://raw.githubusercontent.com/hl-archive-node/nanoreth/b92ad36/Cargo.lock (fetched 2026-11-27, copies in " + W + "/docs)",
          "relevance": "low"},
         {"delta": "Battery 99,985 of 99,985, targeted 85,544 of 85,544, pmdiff set 1 250 of 250 and pmdiff set 2 299 of 300 on the official node; the one set 2 difference is the known full range swap cut by the 30,000,000 gas cap of eth_call. Mined swap window: 1 swap, tick relation exact.",
          "source": W + "/out/battery-official.log, targeted-official.log, pmdiff-official.log, pmdiff2-official.log, swaps-official.log (runs of tools/opdiff against " + OFF + ", 2026-11-27)",
          "relevance": "none"}]},
    {"chainId": 999, "lens": "L2",
     "summary": "The PoolManager emitted one Swap after block 52,134,672, in block 52,363,132: a swap of zero amounts in a pool with no liquidity that moved its price. The one PoolManager slot it wrote reads the same on the official endpoint and both replicas at that block and at head. The 23 multi-transaction scenarios of cycle 28 return the reference on 137 of 137 calls on both replicas; the official endpoint has no eth_simulateV1.",
     "deltas": [
         {"delta": "Transaction 0xc127cb9d563b4df5c0eb9ddc8fc1f1a6d863024a455450727e5c6dbb77cea194 from 0xa0783c5658f4d6cd90d89023f9dd2cc54cacaf0a through contract 0xbaf9961ba462abee6d4f86d9509c0bdd15f9a044 emitted Swap with amount0 0, amount1 0, liquidity 0, tick 157,206, fee 0 for pool 0x96e48e91...ce69. It wrote slot 0x3560a660...0687 to 0x...0266160000000000000a1f6506b24422b6facf1c92ce14. The trace post value, both replicas at the block, the official endpoint at the block and all three at head hold that word. getTickAtSqrtPrice of the stored price is 157,206 in the transcription of TickMath.",
          "source": W + "/out/l1231.json and l1231-tx.json (debug_traceTransaction prestateTracer on " + R1 + ", eth_getStorageAt on " + OFF + ", " + R1 + ", " + R2 + ", 2026-11-27)",
          "relevance": "none"},
         {"delta": "cycle 28 scen28 scenarios through eth_simulateV1 with a 30,000,000 gas block override: 23 scenarios, 137 calls, 0 differences on f0cad31 and on b92ad36. Without the block gas override f0cad31 answers 'Block gas limit exceeded' and both answer 'Client adjustable limit reached' to blocks above their cap. " + OFF + " returns Method not found for eth_simulateV1.",
          "source": W + "/out/scen28-purroof-30m.json, scen28-hyperlend-30m.json, scen28-purroof.log (scripts/scen_rpc_hl.py, 2026-11-27)",
          "relevance": "low"},
         {"delta": "eth_getLogs for the PoolManager from 52,134,673 to 52,371,152: 70 Initialize and 1 Swap. Nonce 0x1, native balance 0x9d908ef23bc0864f and code sha256 907b85e610ad5dab on all three endpoints at head; the testnet has no code at the address.",
          "source": W + "/out/logs-since-52134673.json (" + R1 + ") and pm-state.txt",
          "relevance": "none"}]},
    {"chainId": 999, "lens": "L4",
     "summary": "Blocks 52,351,401 to 52,371,000 hold 10,731 gas price 0 transactions from 47 senders, all in the known system set, and none to or as the PoolManager. The aligned quote assets page, the exchange endpoint page and the HyperCore and HyperEVM transfers page are byte identical to the cycle 30 copies.",
     "deltas": []},
    {"chainId": 999, "lens": "L6",
     "summary": "No HyperEVM upgrade is announced or staged. The announcements channel has no post after 2026-11-16, the HyperEVM pages are unchanged, both mainnet and testnet still answer CLZ with NotActivated and refuse type 4 transactions, and the mainnet hl-visor binary is byte equal to the cycle 17 and 22 copies.",
     "deltas": [
         {"delta": "binaries.hyperliquid.xyz serves Mainnet/hl-visor with sha256 89338207c793d80a (unchanged) and Testnet/hl-visor with sha256 f2b5e7da38cd130a; Mainnet/hl-node returns HTTP 403.",
          "source": "https://binaries.hyperliquid.xyz/Mainnet/hl-visor and https://binaries.hyperliquid.xyz/Testnet/hl-visor (fetched 2026-11-27, hashes in " + W + "/out/binaries.txt)",
          "relevance": "none"}]},
]

cleared = [
    {"chainIds": C, "lens": "L1", "check": "Jump destination analysis on the official node, both replicas and testnet: jumps into PUSH data, into the data of a PUSH truncated at the end of the code, past the code, to offset 0 holding a PUSH, and to valid JUMPDEST offsets with bits set at 2^16, 2^32, 2^64, 2^128 or 2^255.",
     "result": "Every invalid destination halts the frame and every valid one is taken, as the specification and the Ethereum control node require, so no destination is truncated to a low limb and no push data is treated as code. Every branch in src/ goes through JUMP or JUMPI, including the signed remainder branch of TickBitmap.flipTick (src/libraries/TickBitmap.sol) and the overflow branches of FullMath.mulDiv (src/libraries/FullMath.sol).",
     "source": W + "/out/edges32.json"},
    {"chainIds": C, "lens": "L1", "check": "RETURNDATACOPY bounds after empty and 32 byte return data, including offset beyond the size with length 0 and offset plus length overflowing.",
     "result": "In bounds copies succeed and every out of bounds copy halts the frame on all four HyperEVM endpoints and on Ethereum. The PoolManager copies exactly returndatasize() from offset 0 when it wraps a failed transfer or hook call (src/libraries/CustomRevert.sol:91-117), which is always in bounds.",
     "source": W + "/out/edges32.json and src/libraries/CustomRevert.sol:83-119"},
    {"chainIds": C, "lens": "L1", "check": "Zero length MCOPY, KECCAK256, CALLDATACOPY and RETURNDATACOPY at offsets 2^64, 2^200 and 2^256-1, CALLDATALOAD at those offsets, MSIZE after expansion, and KECCAK256 over 135 to 8,191 bytes at unaligned offsets.",
     "result": "Zero length operations do not expand memory and return the empty hash, CALLDATALOAD returns 0, MLOAD at those offsets fails, expansion rounds to the word, and every hash equals Keccak-256 of the bytes. Pool ids, position keys and delta slots hash 0xa0, 0x3a and 0x40 bytes (src/types/PoolId.sol:14, src/libraries/Position.sol:60, src/libraries/CurrencyDelta.sol:14).",
     "source": W + "/out/edges32.json"},
    {"chainIds": C, "lens": "L1", "check": "Standard battery, targeted set, pmdiff sets 1 and 2 and the mined swap check rerun on the official node at head 52,371,152 (2026-11-27).",
     "result": "185,529 of 185,529 vectors and 549 of 550 scripts equal; the one script that differs is the full range swap that runs past the 30,000,000 gas cap of eth_call, as in every cycle since 17.",
     "source": W + "/out/battery-official.log, targeted-official.log, pmdiff-official.log, pmdiff2-official.log"},
    {"chainIds": C, "lens": "L1", "check": "Interpreter and integer library pins of the public replay clients and of nanoreth tags since cycle 30.",
     "result": "nanoreth master Cargo.toml, Cargo.lock and src/evm/spec.rs have the same sha256 as in cycle 30 (db57f890b46c, e8cc9611370d, 4635eb9d52d8). No tag after nb-20261125-2 exists. ruint 1.20.1 and 1.16.0 predate the faulty 1.21.0 release of October 2026, so neither replica carries that MULMOD fault.",
     "source": "https://raw.githubusercontent.com/hl-archive-node/nanoreth/master/Cargo.lock, " + W + "/out/tags-probe.txt"},
    {"chainIds": C, "lens": "L2", "check": "The 23 multi-transaction scenarios of cycle 28 (tick flips on removal, extsload and exttload arrays, sync then exttload, owner and controller flows, int128 donations, malformed calldata and delegatecall, protocol fee swaps) as one simulated block on both replicas.",
     "result": "137 of 137 calls return the reference status and bytes on f0cad31 and on b92ad36, so state and transient storage carried between transactions of one block behave as on Ethereum in both revm generations. The official endpoint cannot run this test because it does not serve eth_simulateV1.",
     "source": W + "/out/scen28-purroof-30m.json and scen28-hyperlend-30m.json"},
    {"chainIds": C, "lens": "L2", "check": "L-1231: PoolManager Swap or ModifyLiquidity logs after block 52,134,672 and the slots written by them on three endpoints.",
     "result": "One Swap in block 52,363,132 wrote one slot (slot0 of the pool); trace, both replicas and the official endpoint agree at the block and at head, and the stored tick equals getTickAtSqrtPrice of the stored price (src/libraries/TickMath.sol).",
     "source": W + "/out/l1231.json"},
    {"chainIds": C, "lens": "L4", "check": "Senders of gas price 0 transactions in blocks 52,351,401 to 52,371,000.",
     "result": "10,731 of 106,429 transactions, from 47 senders, all in the known system set (0x2222..2222, 0x6b9e..0a24, 0xc206..3c00 and 0x20 prefixed token addresses); none to or from the PoolManager.",
     "source": W + "/out/zerogas.json (eth_getBlockByNumber on " + R1 + ")"},
    {"chainIds": C, "lens": "L6", "check": "Upcoming forks over the next six months: announcements, documentation, staged opcodes and precompiles on mainnet and testnet, validator binary.",
     "result": "Nothing is announced or staged. CLZ is not activated, type 4 transactions are refused, 0x100 and 0x0b have no precompile, and the documentation still says Cancun without blobs. If a later move to Prague or Osaka rules shipped, the new items an ordinary account would gain are EIP-7702 delegation of its own account and new precompiles; the PoolManager keys every balance on msg.sender and calls only transfer, balanceOf, hook selectors and empty calldata with value (src/types/Currency.sol:44-94, src/libraries/Hooks.sol), so a delegated account used as a hook is a pool-creator hazard already recorded and a payout to a new precompile strands only the caller's own debit.",
     "source": "https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm.md, https://t.me/s/hyperliquid_announcements, " + W + "/out/forkprobe.json"},
]

leads = [
    {"chainIds": C, "lens": "L2", "question": "Can any endpoint that answers as the official node (hyperliquid evm Mainnet) run a multi-transaction block simulation, through eth_simulateV1, eth_callMany or debug_traceCallMany, so that the 23 scen28 scenarios run there and not only on the two replicas?",
     "why": "The closed validator's handling of state and transient storage across transactions of one block is only known through mined blocks and the replicas.", "priority": "low"},
]

leadResults = [
    {"leadId": "L-1231", "outcome": "cleared", "answer": "Yes, one: a Swap of zero amounts in an empty pool in block 52,363,132 (tx 0xc127cb9d...a194). Its single written slot holds the same word in the trace, on rpc.purroofgroup.com, rpc.hyperlend.finance/archive and the official endpoint at the block and at head, read about 8,000 blocks after it; a comparison inside the same minute was not possible because the block was found after it was mined."},
    {"leadId": "L-1201", "outcome": "inconclusive", "answer": "The reminder appears in the weekly update of 2026-11-16 and names no build or rule change. hl-node is not served (HTTP 403), hl-visor is byte equal to earlier copies, nanoreth master and b92ad36 pin revm 43.0.3 and ruint 1.20.1 as before, and no new tag exists. Both replicas and the official node agree on 112 new edge vectors and all earlier sets, so no execution rule visible through eth_call moved."},
    {"leadId": "L-1130", "outcome": "inconclusive", "answer": "Operator or issuer level, out of scope. The aligned quote assets and exchange endpoint pages are byte identical to cycle 30, so authorizeAqav2Role still names no address; the census of blocks 52,351,401 to 52,371,000 shows only the 47 known system senders and nothing to or as the PoolManager."},
    {"leadId": "L-1118", "outcome": "inconclusive", "answer": "Operator level ordering question with no loss path; the dual block architecture page is byte identical to cycle 30 and says nothing about pending nonces across a usingBigBlocks change."},
    {"leadId": "L-1098", "outcome": "inconclusive", "answer": "Not repeated. The testnet still has no code at the mainnet PoolManager address and the 1,000 block range limit still prevents a full Initialize search."},
]

d = {"unit": "hyperevm", "_lenses": ["L1", "L2", "L4", "L6"], "profiles": profiles, "findings": [], "cleared": cleared,
     "leads": leads, "leadResults": leadResults}
json.dump(d, open(OUT, 'w'), indent=1)
print('wrote', os.path.abspath(OUT))
