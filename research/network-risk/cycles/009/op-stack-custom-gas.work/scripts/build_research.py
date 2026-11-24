"""Write cycles/009/op-stack-custom-gas.research.json from the outputs in ../out."""
import json, os
H = os.path.dirname(os.path.abspath(__file__)); O = os.path.join(H, '..', 'out')
OUTF = os.path.normpath(os.path.join(H, '..', '..', 'op-stack-custom-gas.research.json'))
def j(n): return json.load(open(os.path.join(O, n)))
cb, ct, cp, cp2, cx = j('celo-battery-dual.json'), j('celo-targeted-dual.json'), j('celo-build-pmdiff-dual.json'), j('celo-build-pmdiff2-dual.json'), j('celo-extra-dual.json')
xb, xt, xp, xp2, xx = j('xlayer-battery.json'), j('xlayer-targeted.json'), j('xlayer-build-pmdiff.json'), j('xlayer-build-pmdiff2.json'), j('xlayer-extra.json')
sw = {r['chainId']: r for r in j('swaps.json')['results']}
GETH = 'Geth/v0.1.0-untagged-c7ed55b8-20260817/linux-amd64/go1.24.13'; RETH = 'reth/v2.2.0-74cc8bb/x86_64-unknown-linux-gnu'
WD = 'research/network-risk/cycles/009/op-stack-custom-gas.work'
for r in (cb, ct, cp, cp2, cx):
    assert r['dual']['incomplete'] == 0 and not r['dual']['disagree'], r['tool'] if 'tool' in r else r
    assert r['dual']['perClient'].get(GETH) == r['dual']['calls'] == r['dual']['perClient'].get(RETH)
assert cb['mismatchCount'] == ct['mismatchCount'] == cx['mismatchCount'] == 0
assert cp['identicalToStoredEthereumReference'] == 250 and cp2['identicalToStoredEthereumReference'] == 300
assert xb['mismatchCount'] == xt['mismatchCount'] == xx['mismatchCount'] == 0
assert xp['identicalToStoredEthereumReference'] == 250 and xp2['identicalToStoredEthereumReference'] == 300

def dual_note(r): return f"{r['dual']['calls']} requests, each answered by both {RETH} and {GETH} ({r['dual']['attempts']} batches sent)"

GETH_SRC = 'https://raw.githubusercontent.com/celo-org/op-geth/c7ed55b8/core/vm/'
GETH_UP = 'https://raw.githubusercontent.com/ethereum/go-ethereum/v1.16.9/core/vm/'
U256 = 'https://raw.githubusercontent.com/holiman/uint256/v1.3.2/uint256.go'
KONA_MAIN = 'https://raw.githubusercontent.com/celo-org/celo-kona/main/Cargo.lock'
KONA_TAG = 'https://raw.githubusercontent.com/celo-org/celo-kona/refs/tags/celo/reth-v1.0.10/Cargo.lock'
XL_TAG = 'https://raw.githubusercontent.com/okx/xlayer-reth/refs/tags/v0.0.7.3-rc.1/Cargo.lock'
XL_MAIN = 'https://raw.githubusercontent.com/okx/xlayer-reth/main/Cargo.lock'

profiles = [
 {"chainId": 42220, "lens": "L1",
  "summary": "forno.celo.org sends a minority of requests to an op-geth build and the rest to celo-reth. Both answered every chunk of the battery, the targeted set, the extra vectors and both PoolManager script sets for the build of this checkout, with identical bytes and no mismatch from the specification. The op-geth build runs the go-ethereum v1.16.9 interpreter unchanged on holiman/uint256 v1.3.2.",
  "deltas": [
   {"delta": "A JSON-RPC batch of web3_clientVersion and eth_call is answered by one backend. In samples of this cycle the Geth backend " + GETH + " answered 2 of 20 single requests and 14 of 60 batches, and " + RETH + " the rest. The earlier Celo rows of OPCODES.md did not record which backend answered.", "source": "https://forno.celo.org web3_clientVersion batched with eth_call, 2026-11-24, " + WD + "/out/celo-battery-dual.json", "relevance": "low"},
   {"delta": "In op-geth c7ed55b8 the files instructions.go, jump_table.go, analysis_legacy.go, memory.go, memory_table.go, stack.go, eips.go, opcodes.go, operations_acl.go, contract.go, common.go and gas.go are byte identical to go-ethereum v1.16.9. interpreter.go adds three Config fields (PrecompileOverrides, NoMaxCodeSize, CallerOverride), gas_table.go and evm.go honour NoMaxCodeSize, evm.go wraps the precompile lookup to add the Celo transfer precompile under Cel2 and calls CallerOverride on every call kind, and the create path always calls SetCode. go.mod pins holiman/uint256 v1.3.2, the same version as go-ethereum v1.16.9.", "source": GETH_SRC + "evm.go", "relevance": "low"},
   {"delta": "The main branch of celo-kona has left the celo-org/revm fork and takes revm 42.0.1, revm-interpreter 42.0.0 and revm-bytecode 42.0.0 from crates.io with ruint 1.20.0. The production tag celo/reth-v1.0.10 still takes revm-interpreter 35.0.1 from celo-org/revm bd28f94. The next celo-reth release will therefore change the interpreter crate by seven major versions.", "source": KONA_MAIN, "relevance": "low"},
   {"delta": "The op-geth fork's chain configuration has fields up to Jovian and Interop and no Karst field. The OP Stack registry states that op-geth does not support Karst. When Celo activates Karst, the Geth backend behind forno cannot follow it.", "source": "https://raw.githubusercontent.com/celo-org/op-geth/c7ed55b8/params/config.go; https://docs.optimism.io/op-stack/protocol/hardforks/karst", "relevance": "low"}]},
 {"chainId": 42220, "lens": "L2",
  "summary": "The Geth backend of forno is on the canonical chain: at block 83,613,344 it returned the same block hash, state root, PoolManager native balance and slot 0 as the reth backend. Celo ended op-geth support on mainnet on 22 July 2026, so the block producer runs celo-reth.",
  "deltas": [
   {"delta": "60 batched requests at block 83,613,344 (14 answered by Geth, 46 by reth) gave one block hash 0x8b191ad6...948ebd, one state root 0x2ad78e82...297207d, PoolManager balance 0x14baf5b3d67f9e24cab and slot 0 equal to the owner word on both backends. Both heads were within two blocks of each other.", "source": "https://forno.celo.org eth_getBlockByNumber, eth_getBalance and eth_getStorageAt batched with web3_clientVersion, 2026-11-24, " + WD + "/out/forno-heads.json", "relevance": "none"},
   {"delta": "Celo's notice says op-geth support ended on mainnet on 22 July 2026 and that a node still running op-geth can follow the wrong chain.", "source": "https://docs.celo.org/infra-partners/notices/op-geth-deprecation", "relevance": "low"}]},
 {"chainId": 42220, "lens": "L3",
  "summary": "Nothing new on the gas token for this cycle's focus. celo-reth v1.0.4 and v1.0.5 changed CIP-64 handling to match op-geth, and neither change reaches an opcode result inside the PoolManager.",
  "deltas": [
   {"delta": "celo-reth v1.0.4 treats a zero address fee currency as unregistered, where earlier releases executed it as native CELO and op-geth rejected the block, and it enforces balanceOf(caller) >= gasLimit * maxFeePerGas for CIP-64. The release notes state that no canonical block carries the zero address shape.", "source": "https://github.com/celo-org/celo-kona/releases", "relevance": "none"}]},
 {"chainId": 42220, "lens": "L4",
  "summary": "Known weaknesses of the last two years that earlier cycles had not recorded: the chain ID validation bypass for access list transactions (December 2025, fixed with Jovian), two kona proof vulnerabilities that need a batcher or proposer, and the trie seek boundary fix in celo-reth v1.0.9.",
  "deltas": [
   {"delta": "From the L2 migration until 15 December 2025 the Celo client recovered the sender of an EIP-2930 transaction with the transaction's own chain ID, so a transaction signed for another chain could be included on Celo. One such transaction was included. The sequencer proxy filtered them from 15 December 2025 and the code fix shipped with Jovian, which went live on Celo in March 2026.", "source": "https://forum.celo.org/t/incident-report-chain-id-validation-bypass/13168", "relevance": "low"},
   {"delta": "On 28 April 2026 the OP-Succinct FaultDisputeGame on Celo was upgraded for a derivation divergence and an invalid prior output root in kona. Both need the batcher or the proposer.", "source": "https://forum.celo.org/t/op-succinct-security-upgrade-on-celo-mainnet/13274", "relevance": "none"}]},
 {"chainId": 196, "lens": "L1",
  "summary": "The endpoint still reports reth/v2.3.0-f60420a xlayer/v0.0.7. Both the mainnet tag and the main branch of xlayer-reth pin revm 40.0.3, revm-interpreter 37.0.3 and ruint 1.18.0 from crates.io. The battery, the targeted set, the extra vectors, both script sets for the build of this checkout and the mined swap check all agree with the specification and with Ethereum.",
  "deltas": [
   {"delta": "Cargo.lock at tag v0.0.7.3-rc.1 and on main: revm 40.0.3, revm-interpreter 37.0.3, revm-bytecode 11.0.1, revm-handler 20.0.3, op-revm 20.0.0, ruint 1.18.0, all from crates.io. No release since 5 November 2026 changed these pins.", "source": XL_TAG + "; " + XL_MAIN, "relevance": "none"}]},
 {"chainId": 196, "lens": "L2", "summary": "Nothing new on transaction boundaries or state changes outside execution for this cycle's focus.", "deltas": []},
 {"chainId": 196, "lens": "L3", "summary": "Nothing new on the gas token for this cycle's focus. The gasless rule sets the gas price to zero and the PoolManager bytecode reads neither GASPRICE nor BASEFEE.", "deltas": []},
 {"chainId": 196, "lens": "L4",
  "summary": "The known weaknesses of xlayer-reth since the last reading are dependency advisories in networking, compression and archive crates, none in execution.",
  "deltas": [
   {"delta": "xlayer-reth merged dependency bumps for quinn-proto (CVE-2026-31812, remote panic), lz4_flex (GHSA-vvp9-7p8x-rfvv), tar (CVE-2026-33055 and CVE-2026-33056) and yamux (CVE-2026-32314). Each touches networking, snapshot or archive code and none touches revm or the X Layer execution crates.", "source": "https://github.com/okx/xlayer-reth/pull/183; https://github.com/okx/xlayer-reth/pull/208; https://github.com/okx/xlayer-reth/pull/224; https://github.com/okx/xlayer-reth/releases/tag/v0.0.6", "relevance": "none"}]},
]

findings = [
 {"ref": "new",
  "title": "Celo's public endpoint routes a minority of requests to an op-geth build that Celo no longer supports and that has no Karst rules",
  "chainIds": [42220], "lens": "L1", "assumptions": ["A10"], "effect": "degrade", "actor": "operator", "severity": "low",
  "difference": "forno.celo.org load balances celo-reth and " + GETH + ". Celo ended op-geth support on mainnet on 22 July 2026, and the op-geth fork's chain configuration has no Karst field. Today both backends are on the canonical chain and give identical results.",
  "mechanism": "Wallets, routers and quoters that simulate a PoolManager call through forno get an answer from whichever backend serves the request. Today the two backends agree on every opcode vector and every PoolManager script tried this cycle and on block hash and state root. After Celo activates Karst, the Geth backend cannot apply the new rules and stops following the canonical chain, or applies the old rules to new blocks. A share of eth_call and eth_estimateGas requests (14 of 60 in one sample) would then run against stale state or old rules, so a quote, a minimum output computed from it, or a gas estimate for a long swap could be wrong. The PoolManager itself executes in blocks built by celo-reth and is not affected.",
  "impact": "No loss of pool funds. Users who set slippage bounds from a stale quote may get a worse fill or a revert, and an estimate from the wrong rules can make a removal fail for lack of gas and need a retry.",
  "preconditions": "Celo activates Karst, which has no date, while the forno operator still serves the op-geth backend.",
  "mitigations": "The forno operator removes the op-geth backend before Karst. Integrators simulate against a celo-reth endpoint and check web3_clientVersion. Slippage bounds remain the user's protection.",
  "coreRefs": ["src/PoolManager.sol:104-114", "src/libraries/Pool.sol:279-464"],
  "sources": [
   {"url": "https://docs.celo.org/infra-partners/notices/op-geth-deprecation", "supports": "op-geth support on Celo mainnet ended on 22 July 2026 and a node still running it can follow the wrong chain"},
   {"url": "https://raw.githubusercontent.com/celo-org/op-geth/c7ed55b8/params/config.go", "supports": "the fork's ChainConfig has Jovian and Interop fields and no Karst field"},
   {"url": "https://docs.optimism.io/op-stack/protocol/hardforks/karst", "supports": "op-geth does not support Karst"},
   {"url": "https://forno.celo.org web3_clientVersion batched with eth_call and eth_getBlockByNumber, 2026-11-24", "supports": "both backends answer on the public endpoint and agree today (" + WD + "/out/forno-heads.json)"}],
  "evidence": "primary"},
]

cleared = [
 {"chainIds": [42220], "lens": "L1",
  "check": "Lead L-579: the opcode battery and the targeted set on forno.celo.org with every chunk answered by both client families.",
  "result": f"battery.py: {cb['ran']} of {cb['vectors']} vectors, {dual_note(cb)}, 0 mismatches and no disagreement between the two backends. targeted.py: {ct['ran']} of {ct['vectors']} vectors, {dual_note(ct)}, 0 mismatches and no disagreement. The Celo rows of the battery now rest on both clients.",
  "source": WD + "/out/celo-battery-dual.json; " + WD + "/out/celo-targeted-dual.json; https://forno.celo.org"},
 {"chainIds": [42220], "lens": "L1",
  "check": "The PoolManager script sets of OPCODES.md check 2 (pmdiff 250 scripts, pmdiff2 300 scripts), run with the bytecode built from this checkout, on both forno backends.",
  "result": f"pmdiff: {cp['identicalToStoredEthereumReference']} of 250 scripts identical to the stored Ethereum reference of build-pmdiff.json, {dual_note(cp)}, no disagreement. pmdiff2: {cp2['identicalToStoredEthereumReference']} of 300 identical to build-pmdiff2.json, {dual_note(cp2)}, no disagreement. The math libraries, hook call parsing, token return handling and native payouts compute the same bytes on celo-reth and on the op-geth backend.",
  "source": WD + "/out/celo-build-pmdiff-dual.json; " + WD + "/out/celo-build-pmdiff2-dual.json; research/network-risk/opcodes/build-pmdiff.json"},
 {"chainIds": [42220, 196], "lens": "L1",
  "check": "Extra vectors suggested by the reading of holiman/uint256 v1.3.2 and ruint: EXP with even bases (the v1.3.2 shortcut returns zero for an even base when the exponent has more than 8 bits) and odd bases with exponents across every 64 bit limb, SAR, SHL and SHR of negative words at shifts 0, 63 to 65, 127 to 129, 191 to 193, 254 to 257, 2^64 and 2^256-1, SDIV, SMOD, SLT and SGT at INT_MIN, -1 and the tick bounds, SIGNEXTEND and BYTE for every index 0 to 32 and huge indices, ADDMOD and MULMOD with moduli at and above 2^192 (the AddMod fast path) and 2^256-1.",
  "result": f"3,111 vectors. Celo: {dual_note(cx)}, 0 mismatches. X Layer: 0 mismatches. The even base shortcut is correct by reading: an even base to a power of 256 or more is a multiple of 2^256, and for smaller exponents all set bits lie in the first limb, which the first loop covers.",
  "source": WD + "/scripts/extra.py; " + WD + "/out/celo-extra-dual.json; " + WD + "/out/xlayer-extra.json; " + U256},
 {"chainIds": [42220], "lens": "L1",
  "check": "Reading of the op-geth fork at c7ed55b8 (the Geth backend of forno) against go-ethereum v1.16.9: interpreter, jump table, jump destination analysis, memory, stack, call frames and the 256 bit library.",
  "result": "Twelve core/vm files are byte identical to go-ethereum v1.16.9, including instructions.go, jump_table.go, analysis_legacy.go and memory.go. The only interpreter change is three Config fields that the node does not set from chain data. The fork adds the transfer precompile at 0xfd, which refuses callers other than the CELO token and refuses static context (celo_contracts.go lines 61 to 120). holiman/uint256 v1.3.2 is the version go-ethereum v1.16.9 ships; its MulMod with a four limb modulus reduces through a reciprocal (uint256.go lines 720 to 748), SDiv and SMod take absolute values with Neg and restore the sign of the dividend (lines 665 to 685 and 789 to 813), SRsh fills with ones for every limb case (lines 1110 to 1147), Byte returns zero for indices of 32 or more (lines 1187 to 1198) and ExtendSign returns the input for indices above 30 (lines 1260 onward). The release notes of v1.3.1 fixed an aliasing fault in DivMod, which the interpreter does not call.",
  "source": GETH_SRC + "instructions.go; " + GETH_UP + "instructions.go; " + U256 + "; https://github.com/holiman/uint256/releases"},
 {"chainIds": [196], "lens": "L1",
  "check": "Rerun of battery, targeted, pmdiff and pmdiff2 (build of this checkout) on rpc.xlayer.tech at reth/v2.3.0-f60420a xlayer/v0.0.7, with each answer tagged by web3_clientVersion.",
  "result": f"battery {xb['ran']} and targeted {xt['ran']} vectors with 0 mismatches. pmdiff {xp['identicalToStoredEthereumReference']} of 250 and pmdiff2 {xp2['identicalToStoredEthereumReference']} of 300 scripts identical to the stored Ethereum reference. Every answer came from the same build.",
  "source": WD + "/out/xlayer-battery.json; " + WD + "/out/xlayer-targeted.json; " + WD + "/out/xlayer-build-pmdiff.json; " + WD + "/out/xlayer-build-pmdiff2.json"},
 {"chainIds": [42220, 196], "lens": "L1",
  "check": "Mined swaps since the last run: the tick relation and the single step formulas of OPCODES.md check 3, and a step by step replay of the multi step swaps.",
  "result": f"Celo: {sw[42220]['swaps']} swaps, all pass the tick relation; {sw[42220]['pairs']} paired, 87 single step exact to the unit and 18 multi step, all 18 replayed to the unit (up to 32 steps). X Layer: {sw[196]['swaps']} swaps, all pass the tick relation; {sw[196]['pairs']} paired, 2,654 single step exact to the unit and 2 multi step, both replayed to the unit. These ran in blocks built by the sequencers, which the eth_call tests cannot reach.",
  "source": WD + "/out/swaps.json; " + WD + "/out/replay.json"},
 {"chainIds": [42220, 196], "lens": "L1",
  "check": "Pinned interpreter and big integer versions of the production clients and of the next releases, against the withdrawn ruint 1.21.0.",
  "result": "celo/reth-v1.0.10: revm-interpreter 35.0.1 from celo-org/revm bd28f94, ruint 1.20.0. celo-kona main: revm-interpreter 42.0.0 from crates.io, ruint 1.20.0. xlayer-reth v0.0.7.3-rc.1 and main: revm-interpreter 37.0.3, ruint 1.18.0. None pins ruint 1.21.0 and none has moved to the rewritten 1.21 paths.",
  "source": KONA_TAG + "; " + KONA_MAIN + "; " + XL_TAG + "; " + XL_MAIN},
 {"chainIds": [42220], "lens": "L2",
  "check": "Lead L-245, first half: which client produces Celo blocks, and is the Geth backend on forno on the same chain.",
  "result": "Celo ended op-geth support on mainnet on 22 July 2026 and its sequencer releases are celo-reth. The Geth backend returned the same block hash and state root at block 83,613,344 as the reth backend, so it executes the blocks celo-reth produces and agrees with them. The second half of L-245 (the native balance check for CIP-64 value and the transfer precompile caller rule in celo-reth) was answered by cycle 6.",
  "source": "https://docs.celo.org/infra-partners/notices/op-geth-deprecation; " + WD + "/out/forno-heads.json"},
 {"chainIds": [42220], "lens": "L4",
  "check": "Known weakness: the chain ID validation bypass for EIP-2930 transactions (reported 15 December 2025). Could an ordinary account replay a victim's access list transaction from another chain to move the victim's claims or positions at the PoolManager.",
  "result": "The window ran from the L2 migration to 15 December 2025, when the sequencer proxy began filtering such transactions, and the fix shipped in Jovian, active on Celo since March 2026. One such transaction was included and moved no funds. celo-kona keeps an exception for exactly two historical blocks (Sepolia 12,531,083 and mainnet 53,619,115) and filters on block number first, so live transactions cannot match it. The replay never touched pool accounting itself: it executes what the victim signed.",
  "source": "https://forum.celo.org/t/incident-report-chain-id-validation-bypass/13168; https://github.com/celo-org/celo-kona/commit/13d8cd056f8c1d3a974ce96d45943a2380af4632; https://forum.celo.org/t/h1-2026-engineering-retro-h2-2026-roadmap/13528"},
 {"chainIds": [42220], "lens": "L4",
  "check": "Known weaknesses: the kona proof vulnerabilities fixed on Celo on 28 April 2026, and the celo-kona security review hardening of June 2026 (pull request 214).",
  "result": "The proof issues need the batcher or the proposer, which is actor operator and out of scope. Pull request 214 lists Low and informational items in proof configuration, CIP-64 pool checks, tracing and a reservoir gas charge that is inert until Amsterdam. None changes an opcode result or a balance of the PoolManager.",
  "source": "https://forum.celo.org/t/op-succinct-security-upgrade-on-celo-mainnet/13274; https://github.com/celo-org/celo-kona/pull/214"},
 {"chainIds": [196], "lens": "L4",
  "check": "Known weaknesses of xlayer-reth since cycle 6: dependency advisories and releases v0.0.7.3 and v0.0.7.3-rc.1.",
  "result": "The advisories concern quinn-proto, lz4_flex, tar and yamux, used by networking, snapshot and archive code. v0.0.7.3 changed Flashblocks caching, legacy RPC routing, gasless fee application and storage migration; v0.0.7.3-rc.1 added the upstream trie fix. None changes revm, the instruction table or the precompile set.",
  "source": "https://github.com/okx/xlayer-reth/releases; https://github.com/okx/xlayer-reth/pull/183; https://github.com/okx/xlayer-reth/pull/208; https://github.com/okx/xlayer-reth/pull/224"},
]

leads = [
 {"chainIds": [42220], "lens": "L1",
  "question": "celo-kona main moves celo-reth from revm-interpreter 35.0.1 (celo-org fork) to revm-interpreter 42.0.0 from crates.io. When the release that carries it is tagged, does the celo-revm handler still route the transfer precompile, the CIP-64 debit and credit and transient storage clearing as read in cycle 6, and do the battery and both script sets still pass on forno?",
  "why": "The next celo-reth release changes the interpreter crate of the only block producing client by seven major versions, and every Celo reading so far is of the old fork.", "priority": "medium"},
 {"chainIds": [196], "lens": "L1",
  "question": "Does the X Layer sequencer build blocks with the xlayer-reth Flashblocks builder at the same revm 40.0.3 that the public endpoint runs, and do Flashblocks state root caching changes of v0.0.7.3 ever let a built block carry a state that differs from re-execution?",
  "why": "The mined swap check is the only evidence from the block builder path, and X Layer has a single client.", "priority": "low"},
]

leadResults = [
 {"leadId": "L-579", "outcome": "cleared",
  "answer": f"Every request was sent as a JSON-RPC batch of web3_clientVersion and eth_call, which one backend answers, and repeated until both {RETH} and {GETH} had answered it. Battery: 167 chunks, targeted: 143 chunks, extra vectors: 11 chunks, pmdiff of the build: 250 scripts, pmdiff2 of the build: 300 scripts. Both clients answered every one with identical bytes, the vectors match the specification and the scripts match the stored Ethereum reference. The op-geth fork at c7ed55b8 runs the go-ethereum v1.16.9 interpreter files unchanged on holiman/uint256 v1.3.2; its changes are precompile dispatch for the 0xfd transfer precompile and three unused Config hooks. Celo ended op-geth support on 22 July 2026 and the Geth backend agrees with reth on block hash and state root, so the block producer is celo-reth and the Geth backend is a verifying replica."},
]

d = {"unit": "op-stack-custom-gas", "_lenses": ["L1", "L2", "L3", "L4"], "profiles": profiles, "findings": findings,
     "cleared": cleared, "leads": leads, "leadResults": leadResults}
json.dump(d, open(OUTF, 'w'), indent=1, ensure_ascii=False)
print(OUTF)
