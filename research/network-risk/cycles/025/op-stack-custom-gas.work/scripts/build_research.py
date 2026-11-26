"""Assemble the cycle 25 research file for unit op-stack-custom-gas from the outputs in ../out."""
import json, os
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
O = os.path.join(W, 'out')
OUT = os.path.join(os.path.dirname(W), 'op-stack-custom-gas.research.json')
def j(n):
    try: return json.load(open(os.path.join(O, n)))
    except Exception: return None
alt = open(os.path.join(O, 'targeted-celo-onfinality.log')).read().strip().splitlines()[-1] if os.path.exists(os.path.join(O, 'targeted-celo-onfinality.log')) else ''
CR = 'https://raw.githubusercontent.com/celo-org/celo-kona/refs/tags/celo/reth-v1.0.10/Cargo.lock'
CREVM = 'https://raw.githubusercontent.com/celo-org/revm/bd28f9420c250df2a5c4a6d8103b51ae06b5c222/crates/interpreter/src/instructions/arithmetic.rs'
UPREVM = 'https://raw.githubusercontent.com/bluealloy/revm/v107/crates/interpreter/src/instructions/arithmetic.rs'
XLOCK = 'https://raw.githubusercontent.com/okx/xlayer-reth/refs/tags/v0.0.7.3-rc.1/Cargo.lock'
XTOML = 'https://raw.githubusercontent.com/okx/xlayer-reth/refs/tags/v0.0.7.3-rc.1/Cargo.toml'
XLIB = 'https://raw.githubusercontent.com/okx/optimism/refs/tags/xlayer/v0.1.7/rust/alloy-op-evm/src/lib.rs'
XGL = 'https://raw.githubusercontent.com/okx/optimism/refs/tags/xlayer/v0.1.7/rust/alloy-op-evm/src/block/xlayer_gasless_contract.rs'
XBLK = 'https://raw.githubusercontent.com/okx/optimism/refs/tags/xlayer/v0.1.7/rust/alloy-op-evm/src/block/mod.rs'
XDEPS = 'https://github.com/okx/xlayer-reth/tree/v0.0.7.3-rc.1/deps'
XREL = 'https://github.com/okx/xlayer-reth/releases'
OPNU = 'https://docs.optimism.io/op-stack/protocol/network-upgrades'
OP19 = 'https://docs.optimism.io/notices/archive/upgrade-19'
CELORM = 'https://forum.celo.org/t/h1-2026-engineering-retro-h2-2026-roadmap/13528'
CKMAIN = 'https://raw.githubusercontent.com/celo-org/celo-kona/main/Cargo.lock'
XRPC = 'https://rpc.xlayer.tech'
FORNO = 'https://forno.celo.org'

profiles = [
 {"chainId": 42220, "lens": "L1", "summary": "forno.celo.org still answers reth/v2.2.0-74cc8bb and Geth/v0.1.0-untagged-c7ed55b8 on 2026-11-26, and no celo-reth tag after celo/reth-v1.0.10 could be fetched. The interpreter of that tag is celo-org/revm bd28f942, and its instruction, jump analysis, memory, gas, journal and handler files are byte identical to bluealloy/revm tag v107. A second public provider runs a build named reth/v2.2.0-7680d6d.",
  "deltas": [
   {"delta": "celo/reth-v1.0.10 locks revm-interpreter 35.0.1, revm-bytecode 10.0.0 and revm-handler 18.1.0 from celo-org/revm bd28f942 and ruint 1.20.0 from crates.io. Twenty source files of that fork (arithmetic, bitwise, i256, control, stack, memory, system, host, contract and call helpers, gas, shared memory, the legacy jump analysis, the journal and the handler) have the same sha256 as tag v107.", "source": CR, "relevance": "none"},
   {"delta": "celo-kona main now builds revm 42.0.1 with revm-interpreter 42.0.0 and ruint 1.20.0, so the next Celo client changes the interpreter crate; no tag carries it yet.", "source": CKMAIN, "relevance": "low"},
   {"delta": "celo.api.onfinality.io/public answers web3_clientVersion reth/v2.2.0-7680d6d, a commit string different from forno's 74cc8bb; 7680d6d is the paradigmxyz reth rev that celo/reth-v1.0.10 names for reth-revm. It refuses debug_traceTransaction with internal eth error. The targeted set run against it ran 78,644 of 85,544 vectors with 0 mismatches; the other 6,900 sat in 10 request batches the provider refused (out/targeted-celo-onfinality.log).", "source": "https://celo.api.onfinality.io/public (web3_clientVersion, 2026-11-26)", "relevance": "low"}]},
 {"chainId": 42220, "lens": "L2", "summary": "Nothing new on transaction boundaries or state changes outside execution. The CIP-64 debit reading of cycle 22 holds for the same build.", "deltas": []},
 {"chainId": 42220, "lens": "L3", "summary": "Nothing new. Karst on Celo still has no activation time; the Celo roadmap lists it for Q4 2026 pending readiness.", "deltas": [
   {"delta": "Karst is planned for Q4 2026 on Celo with no date, and brings the EIP-7825 cap of 16,777,216 gas per transaction.", "source": CELORM, "relevance": "low"}]},
 {"chainId": 42220, "lens": "L4", "summary": "The custom gas token v2 predeploys 0x4200..0029 and 0x4200..002A still hold an EIP-1967 implementation slot of zero and a balance of zero at block 83,798,804.", "deltas": []},
 {"chainId": 42220, "lens": "L6", "summary": "First L6 profile since cycle 1. On forno the unsafe head ran about 330 blocks (330 seconds) ahead of safe and about 1,240 blocks (about 21 minutes) ahead of finalized. Both backends served the same latest, safe and finalized numbers and the same hash at 28 heights inside the unsafe window.",
  "deltas": [
   {"delta": "Unsafe minus safe was 328 to 333 blocks and unsafe minus finalized 1,235 to 1,240 blocks, one block per second (eth_getBlockByNumber latest, safe, finalized on forno, 2026-11-26). Only the sequencer, or an L1 reorganisation before batch inclusion, can replace those unsafe blocks.", "source": FORNO + " (eth_getBlockByNumber latest/safe/finalized, out/heads.txt)", "relevance": "low"},
   {"delta": "60 batched samples split 48 reth and 12 Geth; at 28 heights seen by both backends between safe minus 20 and safe plus 320 the block hashes are equal (out/forno_heads.json).", "source": FORNO + " (eth_getBlockByNumber by height, pinned by web3_clientVersion)", "relevance": "none"}]},
 {"chainId": 196, "lens": "L1", "summary": "rpc.xlayer.tech still answers reth/v2.3.0-f60420a xlayer/v0.0.7, and the release page shows no release after v0.0.7.3-rc.1. That tag builds revm 40.0.3 and revm-interpreter 37.0.3 from crates.io with no revm patch, and ruint 1.18.0. Its deps/optimism submodule is okx/optimism a492b62, whose block executor, gasless, EVM and handler files equal tag xlayer/v0.1.7.",
  "deltas": [
   {"delta": "The deps/optimism submodule of xlayer-reth v0.0.7.3-rc.1 is a492b62.", "source": XDEPS, "relevance": "none"},
   {"delta": "The revm dependency enables the optional_balance_check feature. The only cfg flag the X Layer code switches per transaction is disable_base_fee, for gasless transactions, and it is restored on every result path (lib.rs transact_raw, around lines 346-405).", "source": XLIB, "relevance": "none"}]},
 {"chainId": 196, "lens": "L2", "summary": "Nothing new. Karst and the post-execution code behind it are still not scheduled on X Layer.", "deltas": []},
 {"chainId": 196, "lens": "L3", "summary": "The gasless whitelist allows two shared carriers for any non-empty calldata: the ERC-4337 EntryPoint v0.7 with a gas allowance of 30,000,000 and the contract at 0x7c5bee2a with 50,000,000. Both reach the PoolManager, so zero-priced swaps and liquidity changes are already mined on X Layer.",
  "deltas": [
   {"delta": "getGaslessAllowance returns (true, 30,000,000) for EntryPoint v0.7 with handleOps, handleAggregatedOps and any other non-empty prefix, and (true, 50,000,000) for 0x7c5bee2a8091c3ef39072f64f18fac913060aeaf with every prefix tested; it returns false for the PoolManager, PositionManager, Universal Routers, Permit2 and EntryPoints v0.6 and v0.8 (eth_call from 0xdead..0001, out/gasless.json).", "source": XRPC + " (eth_call getGaslessAllowance on 0x19787404b0c70021b4752028f7e3a92313885B27, 2026-11-26)", "relevance": "low"},
   {"delta": "In blocks 76,927,161 to 76,930,160, 3,299 zero-priced transactions came from 202 senders; 101 of them emitted PoolManager logs, 95 through 0x7c5bee2a (82 senders) and 2 through EntryPoint v0.7 (out/gasless_scan.json).", "source": XRPC + " (eth_getBlockByNumber and eth_getTransactionReceipt)", "relevance": "low"}]},
 {"chainId": 196, "lens": "L4", "summary": "Nothing new on system contracts. The two whitelisted carriers are ordinary contracts and hold no PoolManager role.", "deltas": []},
 {"chainId": 196, "lens": "L6", "summary": "First L6 profile since cycle 1. The unsafe head ran 91 to 95 blocks (about 90 seconds) ahead of safe and about 1,350 blocks (about 22 minutes) ahead of finalized.",
  "deltas": [
   {"delta": "Unsafe minus safe 91 to 95 blocks and unsafe minus finalized 1,351 to 1,355 blocks at one block per second (eth_getBlockByNumber latest/safe/finalized, 2026-11-26).", "source": XRPC + " (out/heads.txt)", "relevance": "low"}]},
]

findings = [
 {"ref": "new",
  "title": "X Layer runs PoolManager swaps and liquidity changes at zero gas price through two whitelisted shared carriers",
  "chainIds": [196], "lens": "L3", "assumptions": ["A9"], "effect": "degrade", "actor": "unprivileged", "severity": "info",
  "difference": "X Layer waives the fee of a zero-priced transaction when its gasless whitelist allows the transaction's target and calldata prefix and the gas limit is within the allowance. The whitelist allows EntryPoint v0.7 for any non-empty calldata up to 30,000,000 gas and the contract at 0x7c5bee2a for any non-empty calldata up to 50,000,000 gas. Ethereum has no such rule.",
  "mechanism": "The executor queries getGaslessAllowance(to, input) before each transaction whose max fee per gas is zero and marks it gasless when the answer is true and the gas limit fits; it then executes the transaction normally with only the base fee check relaxed. An ordinary account can submit handleOps to EntryPoint v0.7 carrying its own user operation with zero fees, or a call to 0x7c5bee2a, and so reach the PoolManager without paying gas. In three thousand recent blocks 101 zero-priced transactions from more than 80 senders emitted PoolManager logs. The PoolManager reads neither GASPRICE nor BASEFEE (no use in src/), so every amount it computes and every settlement check in unlock (src/PoolManager.sol:104-114) is the same as in a paid transaction. The effect is cost only: dust tick filling of F-038 and other spam against pools no longer costs gas.",
  "impact": "No funds move and nobody is left unable to withdraw. Griefing that F-038 records loses its gas cost on X Layer; the dust payment it needs still applies.",
  "preconditions": "Whitelist entries as read on 2026-11-26 and a sequencer that admits zero-priced transactions from any sender. The per block gasless budget and any per sender limit of the sequencer were not read, and no transaction was sent to test admission.",
  "mitigations": "None needed for funds. Pool creators who rely on gas cost as a deterrent against tick filling should not do so on X Layer.",
  "coreRefs": ["src/PoolManager.sol:104-114", "src/libraries/Pool.sol:166-171"],
  "sources": [
   {"url": XGL, "supports": "is_gasless requires allowed == true and tx.gas_limit <= returned gasLimit; mainnet whitelist at 0x19787404b0c70021b4752028f7e3a92313885B27"},
   {"url": XLIB, "supports": "a gasless transaction only sets disable_base_fee for its own execution"},
   {"url": XRPC + " (eth_call getGaslessAllowance, out/gasless.json)", "supports": "EntryPoint v0.7 allowed with 30,000,000 gas and 0x7c5bee2a with 50,000,000 gas for any non-empty prefix; PoolManager and periphery not allowed"},
   {"url": XRPC + " (receipts of blocks 76,927,161-76,930,160, out/gasless_scan.json)", "supports": "101 mined zero-priced transactions emitted PoolManager logs, for example 0x14ba5174ce2bf8b682ac926064813eee4a9087bb449346b1500f91659056339d and 0xda396c963d30a6f9774ed5dad69e64ff0b5204432331d4accc2ed88462b42ad8"}],
  "evidence": "primary"}
]

b = j('battery.json'); t = j('targeted.json')
cleared = [
 {"chainIds": [42220, 196], "lens": "L1", "check": "Opcode battery (99,985 vectors) and targeted set (85,544 vectors) rerun on 2026-11-26, with the battery also pinned to each forno backend through pin.py.",
  "result": "0 mismatches and 0 errors on Celo, on X Layer, on Celo pinned to reth/v2.2.0-74cc8bb (167 batches kept) and on Celo pinned to Geth c7ed55b8 (167 batches kept).", "source": "out/battery.log, out/targeted.log, out/battery-celo-reth.log, out/battery-celo-geth.log"},
 {"chainIds": [42220, 196], "lens": "L1", "check": "PoolManager script sets pmdiff.py (250 scripts, 12,322 calls) and pmdiff2.py (300 scripts) against Ethereum, and the mined swap check with replay.",
  "result": "250 of 250 and 300 of 300 identical on both chains. swaps.py matched 89 Celo swaps and 278 X Layer swaps to the unit on tick and amount; 9 Celo multi-step swaps replayed through the full loop without failure.", "source": "out/pmdiff.log, out/pmdiff2.log, out/swaps.log, out/replay.log"},
 {"chainIds": [42220], "lens": "L1", "check": "Whether the Celo revm fork at bd28f942 changes any instruction, the jump destination analysis, memory expansion, gas, the journal or the handler, which would change results of FullMath, TickMath, BitMath, SqrtPriceMath or the settlement code.",
  "result": "No. The twenty files read have the same sha256 as bluealloy/revm v107; the fork's stated change is the SELFDESTRUCT inspector fix, which only touches tracing. Every opcode used by src/libraries therefore runs the upstream handler.", "source": CREVM + " compared with " + UPREVM},
 {"chainIds": [196], "lens": "L1", "check": "Lead L-1022: whether the okx/optimism commit built by xlayer-reth v0.0.7.3-rc.1 matches what cycle 23 read at a492b62.",
  "result": "The submodule is a492b62 itself, and its block/mod.rs, xlayer_gasless_contract.rs, lib.rs and op-revm handler.rs equal tag xlayer/v0.1.7 byte for byte.", "source": XDEPS},
 {"chainIds": [196], "lens": "L3", "check": "Whether a gasless transaction runs with any validation relaxed other than the base fee, in particular the balance check that the optional_balance_check feature makes available.",
  "result": "No. transact_raw sets only cfg.disable_base_fee for a gasless transaction and restores the previous value on every result path; disable_balance_check is never set, so value still needs the sender's balance.", "source": XLIB},
 {"chainIds": [42220, 196], "lens": "L6", "check": "Lead L-1085: how far unsafe runs ahead of safe, who can replace those blocks, and whether forno's op-geth backend serves replaced blocks.",
  "result": "Celo about 330 seconds to safe and 21 minutes to finalized, X Layer about 90 seconds and 22 minutes. Replacing an unsafe block needs the sequencer or an L1 reorganisation before the batch lands, which is operator level. The two forno backends agree on all three tags and on the hash at 28 heights inside the unsafe window. Within one transaction unlock is atomic, so a replaced block undoes whole transactions and cannot leave a partial PoolManager state.", "source": FORNO + " and " + XRPC + " (out/heads.txt, out/forno_heads.json); src/PoolManager.sol:104-114"},
 {"chainIds": [42220, 196], "lens": "L1", "check": "Upcoming forks assumed live within six months: Karst on Celo (Q4 2026, no date) and on X Layer (not scheduled), with Lagoon behind it (not scheduled on the OP registry).",
  "result": "Nothing new beyond cycle 22: CLZ has no executable 0x1e in the PoolManager code, EIP-7825 caps transactions at 16,777,216 gas while liquidity removal touches two ticks with no loop (src/libraries/Pool.sol:146-204), and the swap loop (src/libraries/Pool.sol:344) can be bounded by a price limit. The gasless carriers keep working after Karst under the same per transaction cap, below their allowances.", "source": OPNU},
]

leads = [
 {"chainIds": [196], "lens": "L3", "question": "What per block gasless budget and per sender limits does the X Layer sequencer apply, and can zero-priced handleOps bundles through EntryPoint v0.7 fill a block's gasless budget so that other users' gasless PoolManager swaps through 0x7c5bee2a are delayed?", "why": "The whitelist lets any account run 30,000,000 gas at zero price. Only ordering and inclusion of others are at stake, not funds.", "priority": "low"},
 {"chainIds": [42220], "lens": "L1", "question": "When a celo-reth tag carrying revm 42.0.1 (revm-interpreter 42.0.0) appears, rerun the battery pinned to it and compare its instruction files with upstream, and identify the build behind reth/v2.2.0-7680d6d on onfinality.", "why": "The next Celo client changes the interpreter crate, and a second public provider already runs a build string forno does not.", "priority": "low"},
]

leadResults = [
 {"leadId": "L-1085", "outcome": "cleared", "answer": "Celo unsafe runs about 330 blocks ahead of safe and 1,240 ahead of finalized at one block per second; X Layer about 92 and 1,353. Only the sequencer or an L1 reorganisation before batch inclusion replaces unsafe blocks (operator level), and X Layer's deposit filter acts on L1 deposits at derivation as F-046 records. forno's Geth and reth backends returned the same tags and the same hashes at 28 heights inside the unsafe window. A bridge or fast withdrawal that pays out on an unsafe PoolManager event takes operator-level reorganisation risk; the PoolManager itself is atomic per transaction."},
 {"leadId": "L-1068", "outcome": "finding", "answer": "The whitelist allows EntryPoint v0.7 (30,000,000 gas) and 0x7c5bee2a (50,000,000 gas) for any non-empty calldata. 101 zero-priced transactions in 3,000 blocks emitted PoolManager logs, 95 through 0x7c5bee2a and 2 through the EntryPoint. Any account can therefore send PoolManager swaps and liquidity changes without paying gas. The PoolManager reads no gas price, so this changes cost only; recorded as an information finding with effect degrade."},
 {"leadId": "L-980", "outcome": "inconclusive", "answer": "Karst still has no Celo activation time and no celo-reth tag after v1.0.10 exists; 0x4200..0029 and 0x4200..002A still have an implementation slot of zero and no balance at block 83,798,804. The post-activation sweep stays open."},
 {"leadId": "L-981", "outcome": "inconclusive", "answer": "Operator level. X Layer has not scheduled Karst and v0.0.7.3-rc.1 is still the newest release, so no post-execution format is enabled to read."},
 {"leadId": "L-1022", "outcome": "cleared", "answer": "The deps/optimism submodule of v0.0.7.3-rc.1 is a492b62, and its post_exec settlement, gasless, EVM and handler files equal tag xlayer/v0.1.7."},
 {"leadId": "L-1023", "outcome": "inconclusive", "answer": "No public Celo endpoint traced a mined transaction: forno, publicnode and 1rpc refuse the method, ankr needs a key, drpc errored, and onfinality (reth/v2.2.0-7680d6d) answered internal eth error for a real hash. F-144 stays confirmed from source only."},
 {"leadId": "L-216", "outcome": "inconclusive", "answer": "Operator level. The mainnet filter flag is still not observable from public interfaces."},
]

d = {"unit": "op-stack-custom-gas", "_lenses": ["L1", "L2", "L3", "L4", "L6"], "profiles": profiles, "findings": findings, "cleared": cleared, "leads": leads, "leadResults": leadResults}
json.dump(d, open(OUT, 'w'), indent=1)
print(OUT)
