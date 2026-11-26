"""Builds cycles/027/op-stack-eth.research.json from the notes below and the logs in the work directory."""
import json, os, re
W = '/home/user/v4-core/research/network-risk/cycles/027/op-stack-eth.work'
OUT = '/home/user/v4-core/research/network-risk/cycles/027/op-stack-eth.research.json'
CH = [10, 8453, 130, 7777777, 480, 57073, 1868]
NAME = {10: 'OP Mainnet', 8453: 'Base', 130: 'Unichain', 7777777: 'Zora', 480: 'World Chain', 57073: 'Ink', 1868: 'Soneium'}
LOGS = 'file:research/network-risk/cycles/027/op-stack-eth.work/'

def rd(f):
    p = os.path.join(W, f)
    return open(p).read() if os.path.exists(p) else ''

swaps = {}
for l in rd('swaps.log').splitlines():
    m = re.match(r'\s*(\d+)\s+\S+\s+swaps\s+(\d+) tick .*?mismatch\': (\d+)\}.*pairs (\d+) amount (\{.*?\})', l)
    if m: swaps[int(m.group(1))] = (int(m.group(2)), int(m.group(3)), int(m.group(4)), eval(m.group(5)))
replay = {}
for l in rd('replay.log').splitlines():
    m = re.match(r"\('(\w[\w ]*)', '(\w+)'\) \{'replayed': (\d+), 'failed': (\d+), 'maxSteps': (\d+)", l)
    if m: replay.setdefault(m.group(1), []).append((m.group(2), int(m.group(3)), int(m.group(4)), int(m.group(5))))
RN = {'Optimism': 10, 'Base': 8453, 'Unichain': 130, 'Zora': 7777777, 'Worldchain': 480, 'Ink': 57073, 'Soneium': 1868}
rep_by = {RN.get(k, k): v for k, v in replay.items()}
CLIENT = {10: 'op-reth/v2.8.1-72207294 and op-reth/v0.0.0-dev-unknown', 8453: 'reth/v2.5.2-9e380dd/base/v1.5.6', 130: 'op-reth/v2.10.0-rc.4-65e80332',
          7777777: 'conduit-op-reth/v2.5.1-8f0ccac', 480: 'world-chain/v2.8.2-9596311', 57073: 'op-reth/v2.10.0-rc.4-65e80332 (rpc-gel) and op-reth/v0.0.0-dev-unknown (rpc-qnd)',
          1868: 'op-reth/v2.10.0-rc.4-65e80332'}

def rerun_delta(c):
    s = swaps.get(c)
    sw = ''
    if s:
        n, mis, pairs, am = s
        single = am.get('exactIn', 0) + am.get('exactOut', 0) + am.get('target', 0)
        sw = f', and {n} mined swaps satisfy the tick relation with {mis} mismatches, {single} of {pairs} paired swaps matching a single step to the unit'
        rp = rep_by.get(c)
        if rp:
            tot = sum(x[1] for x in rp); fail = sum(x[2] for x in rp); mx = max(x[3] for x in rp)
            sw += f' and {tot - fail} of {tot} sampled multi-step swaps replaying through the whole loop (longest {mx} steps)'
    return {'delta': f'Rerun on {NAME[c]} on 2026-11-26 at the build the endpoint reported ({CLIENT[c]}): 99,985 battery and 85,544 targeted vectors return the specified word, all 250 set 1 and 300 set 2 scripts give the same bytes as the Ethereum reference' + sw + '. A new set of 15,510 vectors with shift, BYTE, SIGNEXTEND and EXP operands whose low limb is small and whose high limbs are set, and MULMOD, ADDMOD and the 512 bit product against moduli 2^256-1, 2^256-2 and 2^256-3, returns the specified word' + (' in four rounds' if c == 10 else '') + '.',
            'source': LOGS + 'battery.log, targeted.log, pmdiff.log, pmdiff2.log, swaps.log, replay.log, hiword.log, hiword-10.log, clientver.txt', 'relevance': 'low'}

LAGOON_DATE = {'delta': 'Lagoon is now in the superchain-registry for OP Mainnet, Unichain, Ink and Soneium with lagoon_time 1799683201 (11 January 2027 16:00:01 UTC); Zora and World Chain have no lagoon_time. The Lagoon execution layer changes no opcode: it lowers the BLS12-381 MSM and pairing input limits and adds the 0x7D post-execution transaction. The PoolManager calls no precompile with input.',
               'source': 'https://raw.githubusercontent.com/ethereum-optimism/superchain-registry/main/superchain/configs/mainnet/op.toml; https://specs.optimism.io/protocol/lagoon/exec-engine.html; https://docs.optimism.io/notices/upgrade-22.md', 'relevance': 'low'}
OPRETH = {'delta': 'op-reth v2.10.0 is tagged after the v2.10.0-rc.4 build that Unichain, Ink and Soneium run. Its Cargo.lock pins the same revm 43.0.3, revm-interpreter 43.0.2, revm-bytecode 43.0.0 and ruint 1.20.0, and the op-revm files handler.rs, evm.rs, precompiles.rs, spec.rs, l1block.rs, api/exec.rs and api/builder.rs are byte identical to rc.4. The instruction table is the stock EthInstructions::new_mainnet_with_spec (op-revm evm.rs:38).',
          'source': 'https://raw.githubusercontent.com/ethereum-optimism/optimism/op-reth/v2.10.0/rust/Cargo.lock; https://raw.githubusercontent.com/ethereum-optimism/optimism/op-reth/v2.10.0/rust/op-revm/src/evm.rs', 'relevance': 'low'}
SPLIT = {'delta': 'mainnet.optimism.io sends the elements of one JSON-RPC batch to different backends: in 30 batches of three web3_clientVersion calls, 18 mixed op-reth/v2.8.1-72207294 with op-reth/v0.0.0-dev-unknown, 11 answered dev only and 1 answered v2.8.1 only. The other six endpoints answered one build in all 30 batches.',
         'source': LOGS + 'batch-clientver.txt (queries to https://mainnet.optimism.io on 2026-11-26)', 'relevance': 'low'}
ETHLIQ = {'delta': 'From Lagoon the ETHLiquidity predeploy 0x4200..0025 is initialised with type(uint128).max wei and pays it out through SuperchainETHBridge.relayETH and refundETH. On 2026-11-26 its proxy has no implementation and a balance of 0 on OP Mainnet, Unichain, Ink and Soneium.',
          'source': 'https://specs.optimism.io/interop/eth-liquidity.html; https://raw.githubusercontent.com/ethereum-optimism/optimism/op-contracts/v10.0.0/packages/contracts-bedrock/src/L2/ETHLiquidity.sol; ' + LOGS + 'interop-predeploys.txt', 'relevance': 'low'}
EVEREST = {'delta': 'Base Everest (no date on Sepolia or mainnet) adds Base Transactions, type 0x79: calls grouped in phases that commit one by one under a journal checkpoint, a separate gas payer, token reimbursement of the payer, parallel nonce lanes and in-band 7702 style delegation. It also bills gas on the declared limit instead of on use. In base v1.6.0-rc.4 a failed phase is undone by checkpoint_revert, which reverts transient storage entries, and the transaction ends in commit_tx, which clears transient storage.',
           'source': 'https://docs.base.org/upgrades/everest/overview; https://docs.base.org/specifications/base-transactions; https://raw.githubusercontent.com/base/base/v1.6.0-rc.4/crates/common/evm/src/eip8130.rs; https://raw.githubusercontent.com/base/base/v1.6.0-rc.4/crates/common/evm/src/spec.rs', 'relevance': 'low'}
BASEREVM = {'delta': 'Base v1.5.6 still links revm-interpreter 42.0.0 and revm-bytecode 42.0.0, one release behind the other six chains. The instruction files arithmetic.rs, bitwise.rs, control.rs, i256.rs, system.rs, memory.rs, macros.rs and host.rs are byte identical between 42.0.0 and 43.0.2; contract.rs differs only inside the Amsterdam gated CREATE block and stack.rs only in how push_slice splits its input. The 43.0.0 fix that makes a failed memory resize return MemoryOOG (revm PR 3864) has no effect on SharedMemory, whose resize always returns true (shared_memory.rs:122-125 at 42.0.0). Base v1.6.0-rc.4 and main still do not wire evm2 into the node.',
            'source': 'https://raw.githubusercontent.com/base/base/v1.5.6/Cargo.lock; https://static.crates.io/crates/revm-interpreter/revm-interpreter-42.0.0.crate; https://static.crates.io/crates/revm-interpreter/revm-interpreter-43.0.2.crate; https://patch-diff.githubusercontent.com/raw/bluealloy/revm/pull/3864.diff; https://raw.githubusercontent.com/base/base/main/crates/common/evm2/README.md', 'relevance': 'low'}
SDM = {'delta': 'Released op-reth uses a null refund policy and never appends a post-execution transaction. Refund policies are an OP Enterprise feature chosen per sequencer and are not published; the spec bounds every refund by the transaction\'s own evmGasUsed.',
       'source': 'https://docs.optimism.io/chain-operators/guides/features/sequencer-defined-metering.md; https://specs.optimism.io/protocol/lagoon/sdm.html', 'relevance': 'low'}
WC = {'delta': 'world-chain v2.8.3 is tagged after the v2.8.2 build the endpoint runs. Its lockfile changes only the world-chain crates, and crates/evm/src/lib.rs and factory.rs are byte identical to v2.8.2.',
      'source': 'https://raw.githubusercontent.com/worldcoin/world-chain/v2.8.3/Cargo.lock; https://raw.githubusercontent.com/worldcoin/world-chain/v2.8.3/crates/evm/src/factory.rs', 'relevance': 'none'}
SWEEP = lambda c: {'delta': f'All 256 addresses 0x4200..0000 to 0x4200..00ff were called on {NAME[c]} from the PoolManager address. Only WETH (0x06) and{" the OP token (0x42) and" if c == 10 else ""} the existing native sinks of F-048 accept a transfer or a value call as the PoolManager makes them; L1BlockNumber (0x13) answers transfer with the L1 block number, which Currency.transfer rejects because the word is not 1.' + (' 0x4200..0042 has no code on Unichain, so a take of that currency moves nothing.' if c == 130 else ''),
                   'source': LOGS + 'predeploy-sweep.json, inner-call.json', 'relevance': 'low'}

profiles = []
for c in CH:
    l1 = [rerun_delta(c)]
    if c == 10: l1 += [SPLIT]
    if c in (130, 57073, 1868): l1 += [OPRETH]
    if c in (10, 130, 57073, 1868): l1 += [LAGOON_DATE]
    if c == 8453: l1 += [BASEREVM]
    if c == 480: l1 += [WC]
    s1 = 'Every vector, script and mined swap matches the specification at the builds answering on 2026-11-26, including 15,510 new vectors with large shift and index operands.'
    if c == 10: s1 += ' The endpoint splits one batch between two op-reth builds.'
    if c == 8453: s1 += ' Base still runs revm-interpreter 42.0.0, whose instruction files equal the 43.0.2 that the others run.'
    profiles.append({'chainId': c, 'lens': 'L1', 'summary': s1, 'deltas': l1})
    l2 = []
    if c == 8453: l2 = [EVEREST]
    profiles.append({'chainId': c, 'lens': 'L2', 'summary': 'Transaction boundaries are unchanged.' + (' Base Everest phases revert and clear transient storage as a single transaction does.' if c == 8453 else ''), 'deltas': l2})
    l3 = []
    if c == 130: l3 = [SDM]
    if c in (10, 130): l3 += [ETHLIQ]
    s3 = 'Nothing new changes the native asset or gas token.'
    if c in (10, 130): s3 = 'From Lagoon a predeploy holds type(uint128).max wei that only valid interop messages release.'
    if c == 8453: s3 = 'Everest gas-limit billing and token reimbursement of payers change who pays fees only.'
    profiles.append({'chainId': c, 'lens': 'L3', 'summary': s3, 'deltas': l3})
    profiles.append({'chainId': c, 'lens': 'L4', 'summary': 'A full sweep of the 0x4200 range with the PoolManager as caller finds no entry point beyond those already recorded.', 'deltas': [SWEEP(c)]})

findings = [
    {'ref': 'new',
     'title': 'The public OP Mainnet endpoint answers the elements of one batch from two op-reth builds, so a batch bracket does not pin an eth_call to a build',
     'chainIds': [10], 'lens': 'L1', 'assumptions': ['A10'], 'effect': 'degrade', 'actor': 'operator', 'severity': 'info',
     'difference': 'Ethereum reference endpoints used in this review answer from one build per request. mainnet.optimism.io routes each element of a JSON-RPC batch on its own, between op-reth/v2.8.1-72207294 and an unversioned op-reth/v0.0.0-dev-unknown.',
     'mechanism': 'In 30 batches of three web3_clientVersion calls sent on 2026-11-26, 18 batches mixed the two builds, 11 named only the unversioned build and 1 named only v2.8.1. A batch that puts web3_clientVersion before and after an eth_call therefore does not show which build ran the call. Every opcode vector and script on OP Mainnet in this and earlier cycles ran on one of the two builds, and every one returned the specified word, so neither build was seen to compute FullMath, TickMath, BitMath or the settlement path differently. What is not shown is that each build alone ran every vector. The four rounds of the new 15,510 vector set reduce the chance that a batch never reached one build, but do not exclude it. The PoolManager computes what the block producer computes; the endpoint builds only answer reads.',
     'impact': 'No funds are at risk. The evidence for OP Mainnet is unpinned per build, and the unversioned build has no published source to read.',
     'preconditions': 'None for the routing itself. A fault would also need one of the two builds to compute an opcode differently and to be the one that produces or validates blocks.',
     'mitigations': 'Run pinned checks against a single-backend endpoint or a self-hosted op-reth of each version, and ask the operator which commit the unversioned build carries.',
     'coreRefs': ['src/libraries/FullMath.sol:24-48', 'src/libraries/TickMath.sol:61-111'],
     'sources': [{'url': 'https://mainnet.optimism.io', 'supports': 'batched web3_clientVersion answers recorded in cycles/027/op-stack-eth.work/batch-clientver.txt'}],
     'evidence': 'primary'},
    {'ref': 'new',
     'title': 'From Lagoon a predeploy on OP Mainnet and Unichain holds type(uint128).max wei that the interop bridge releases, so native pools rest on interop message validity',
     'chainIds': [10, 130], 'lens': 'L3', 'assumptions': ['A3', 'A14'], 'effect': 'siphon', 'actor': 'operator', 'severity': 'low',
     'difference': 'Ethereum has no contract that can mint native ETH. From 11 January 2027 the ETHLiquidity predeploy on OP Mainnet and Unichain starts with type(uint128).max wei and pays ETH to SuperchainETHBridge whenever a cross-chain ETH message from the other chain is relayed, or when an expired send is refunded.',
     'mechanism': 'Native pools settle with msg.value and pay out with a plain value call (src/PoolManager.sol:349-364, src/types/Currency.sol:44-52). The PoolManager cannot tell where the ETH it receives came from. A relayETH on a destination chain mints from ETHLiquidity against an initiating sendETH on the source chain, and the protocol checks that link through the CrossL2Inbox access list at sequencing and through derivation. If a relay of a message that was never initiated were accepted into a canonical block, its recipient would hold ETH that no burn backs, could pay it into native pools as a normal settle and take out the other currency of every native pool up to its liquidity. Derivation replaces a block that holds an invalid executing message with a deposits-only block, which also removes the swaps made with the ETH, so in the canonical chain the ETH and the swaps vanish together. An ordinary account can send a relay transaction, but cannot make an invalid one canonical: that needs the sequencer to include it and the derivation or proof system to accept it. Before Lagoon the proxy at 0x4200..0025 has no implementation and a balance of 0 on all four Lagoon chains (queried 2026-11-26). The contract has no receive or fallback, so a native take to it reverts (ETHLiquidity.sol:63-82).',
     'impact': 'Up to every native ETH pool on OP Mainnet and Unichain, but only through a fault in interop validation or in derivation. No path for an ordinary account was found.',
     'preconditions': 'Lagoon active on 11 January 2027 and a fault that lets an unbacked relayETH or refundETH become canonical, or off-chain parties acting on an unsafe block that is later replaced.',
     'mitigations': 'Treat interop ETH like a bridge: integrations that act on PoolManager payouts should wait for safe blocks after Lagoon. Governance can pause ETHLiquidity through the L1 pause.',
     'coreRefs': ['src/PoolManager.sol:349-364', 'src/types/Currency.sol:44-52'],
     'sources': [{'url': 'https://specs.optimism.io/interop/eth-liquidity.html', 'supports': 'initial balance type(uint128).max wei and mint only by SuperchainETHBridge'},
                 {'url': 'https://raw.githubusercontent.com/ethereum-optimism/optimism/op-contracts/v10.0.0/packages/contracts-bedrock/src/L2/ETHLiquidity.sol', 'supports': 'burn, mint, fund and setPaused, no receive or fallback'},
                 {'url': 'https://docs.optimism.io/notices/upgrade-22.md', 'supports': 'Lagoon activation dates and ETHLiquidity pause'},
                 {'url': 'https://specs.optimism.io/interop/derivation.html', 'supports': 'a block with an invalid executing message is replaced by a deposits-only block'}],
     'evidence': 'secondary'},
]

cleared = [
    {'chainIds': CH, 'lens': 'L1', 'check': 'Battery (99,985), targeted set (85,544), script sets 1 (250) and 2 (300), mined swaps and multi-step replays rerun at the builds answering on 2026-11-26.',
     'result': 'No mismatch on any of the seven chains. Set 1 and set 2 give the same bytes as the Ethereum reference on all scripts. Mined swaps: ' + '; '.join(f'{NAME[c]} {swaps[c][0]} with {swaps[c][1]} tick mismatches' for c in CH if c in swaps) + '.',
     'source': LOGS + 'battery.log, targeted.log, pmdiff.log, pmdiff2.log, swaps.log, replay.log'},
    {'chainIds': CH, 'lens': 'L1', 'check': 'New vectors for a 256 bit library that truncates the shift, byte or sign-extension index to 32 or 64 bits before clamping, or mishandles EXP exponents with only high limbs, and MULMOD, ADDMOD and the 512 bit product against moduli 2^256-1, 2^256-2, 2^256-3, 2^255+1 and (2^128-1)*2^128+1 with operands near the modulus (15,510 vectors, script cycles/027/op-stack-eth.work/scripts/hiword.py, reference from tools/opdiff/battery.py).',
     'result': 'All 15,510 return the specified word on all seven chains, on OP Mainnet in four rounds. In revm-interpreter 42.0.0 and 43.0.2 SHL, SHR, SAR and BYTE clamp the index with usize::try_from over the whole word before calling ruint (macros.rs:122-126, bitwise.rs:107-158), and SIGNEXTEND compares the whole word with 31 (arithmetic.rs:126-137), so the ruint 1.19.0 fast-path truncation on Base cannot be reached. TickMath.sol:61-63 and 111, BitMath and TickBitmap therefore get specified shifts.',
     'source': LOGS + 'hiword.log, hiword-10.log; https://static.crates.io/crates/revm-interpreter/revm-interpreter-42.0.0.crate'},
    {'chainIds': CH, 'lens': 'L1', 'check': 'Jump destination analysis in revm-bytecode 42.0.0 (Base) and 43.0.0 (the others), and the fixes since 41.0.0.',
     'result': 'The two crates have identical sources. analyze_legacy is a scalar loop that marks JUMPDEST bytes and skips PUSH1 to PUSH32 immediates (legacy/analysis.rs:10-62). The fixes of 41.0.0 and 41.0.1 (PRs 3752, 3792, 3800) replace an out-of-bounds pointer computation with wrapping_add and correct the opcode iterator used by tools; none changes which offsets are valid jump targets. The 29 JUMPDEST bytes inside the PoolManager push data therefore stay invalid targets.',
     'source': 'https://static.crates.io/crates/revm-bytecode/revm-bytecode-43.0.0.crate; https://patch-diff.githubusercontent.com/raw/bluealloy/revm/pull/3752.diff'},
    {'chainIds': CH, 'lens': 'L1', 'check': 'PoolManager runtime code at each chain\'s address compared with the hash recorded in networks.json.',
     'result': 'All seven equal the recorded length and hash, Unichain\'s predeploy included (24,050 bytes, 8cc5a065c50fd993).', 'source': LOGS + 'codehash.txt'},
    {'chainIds': CH, 'lens': 'L1', 'check': 'Execution cache key of the reth branches behind the endpoints: op-v2.6.0-2 (op-reth v2.8.1, conduit-op-reth v2.5.1, world-chain v2.8.2), op-v2.7.0-2 (op-reth v2.10.0-rc.4 and v2.10.0) and base-v2.5.2.11 (Base v1.5.6).',
     'result': 'All three use fixed-cache 0.1.10 with storage keyed by the full (Address, StorageKey) pair, accounts by the full Address and code by the full 32 byte code hash (execution-cache/src/cached_state.rs, e.g. lines 965-971 at op-v2.7.0-2). fixed-cache compares the stored key with the requested key before returning a value (lib.rs:322-351), so a hash collision gives a miss, not another slot\'s value. PoolManager slots and transient deltas cannot be served from another key.',
     'source': 'https://raw.githubusercontent.com/ethereum-optimism/reth/op-v2.7.0-2/crates/engine/execution-cache/src/cached_state.rs; https://raw.githubusercontent.com/base/reth/base-v2.5.2.11/crates/engine/execution-cache/src/cached_state.rs; https://static.crates.io/crates/fixed-cache/fixed-cache-0.1.10.crate'},
    {'chainIds': [10, 130, 57073, 1868, 480], 'lens': 'L1', 'check': 'op-rbuilder v0.4.14 and main (revm-interpreter 41.0.0) against the nodes\' 43.0.2 instruction files.',
     'result': 'arithmetic.rs, bitwise.rs, control.rs, i256.rs, system.rs, memory.rs, stack.rs and macros.rs are byte identical. host.rs differs in the SSTORE cold-load skip threshold (cold_storage_additional_cost in 41.0.0, cold_storage_cost in 43.0.2). The EIP-2200 sentry rejects SSTORE with 2,300 gas or less and 100 gas is charged before the check, so the remaining gas at the check exceeds 2,200 and neither threshold is ever met. A builder on 41.0.0 computes the same results and gas for PoolManager code.',
     'source': 'https://raw.githubusercontent.com/flashbots/op-rbuilder/main/Cargo.lock; https://static.crates.io/crates/revm-interpreter/revm-interpreter-41.0.0.crate'},
    {'chainIds': [8453], 'lens': 'L2', 'check': 'Base Everest phases (Base Transactions) and transient storage: can a discarded phase or the end of a phased transaction leave an unlock flag, a delta or a synced currency for later code.',
     'result': 'Each phase runs under a journal checkpoint; a failed phase calls checkpoint_revert, whose journal entries revert transient storage writes (revm-context 43.0.3 journal/inner.rs:622-641), and later phases are skipped. The transaction ends in commit_tx, which clears transient storage (inner.rs:141-171), or in discard_tx on error (eip8130.rs:1815-1835). The PoolManager therefore sees the same lifetimes as in a multicall from one sender: Lock, NonzeroDeltaCount and CurrencyReserves (src/libraries/Lock.sol:13-25, CurrencyReserves.sol:17-36) live for one transaction, and unlock still checks the delta count before it returns (src/PoolManager.sol:104-114).',
     'source': 'https://raw.githubusercontent.com/base/base/v1.6.0-rc.4/crates/common/evm/src/eip8130.rs; https://static.crates.io/crates/revm-context/revm-context-43.0.3.crate'},
    {'chainIds': [8453], 'lens': 'L3', 'check': 'Base Everest gas-limit billing.',
     'result': 'Settlement charges gas_limit times price and reports gasUsed as the limit; the opcode gas schedule and out-of-gas behaviour are unchanged. The PoolManager reads no gas price or gas used, so only the sender\'s fee changes.',
     'source': 'https://docs.base.org/upgrades/everest/overview; https://raw.githubusercontent.com/base/base/v1.6.0-rc.4/crates/common/evm/src/spec.rs'},
    {'chainIds': CH, 'lens': 'L4', 'check': 'L-127: every address 0x4200..0000 to 0x4200..00ff, the Base registries 0x8453..01 and 0x8453..02, the ERC-4337 EntryPoint v0.7 and the WorldID contract on World Chain, called with transfer(address,uint256), balanceOf(PoolManager), empty calldata and empty calldata with 1 wei, first with from set to the PoolManager and then, for the 15 that answered or matter, through a forwarder placed at the PoolManager address so that msg.sender is the PoolManager and tx.origin another account.',
     'result': 'Under the real caller shape only WETH (0x06) and on OP Mainnet the OP token (0x42) accept transfer, as ordinary ERC-20s. L1BlockNumber (0x13) answers every call with the L1 block number (about 26,501,500), which Currency.transfer rejects because the word is not 1 (src/types/Currency.sol:67). Value calls succeed only at the sinks recorded in F-048 (L2ToL1MessagePasser, the four fee vaults, WETH, L1BlockNumber, the EntryPoint) and are debited to the caller first (src/PoolManager.sol:291-297). L2StandardBridge rejects the PoolManager as caller; it accepted only in the plain eth_call where the PoolManager was also tx.origin. The Base registries revert every shape. 0x4200..0042 has no code on Unichain, so a take of that currency succeeds and moves nothing, which is the known no-code case of A4.',
     'source': LOGS + 'predeploy-sweep.json, inner-call.json, scripts/predeploy_sweep.py, scripts/inner_call.py'},
    {'chainIds': [10, 130, 57073, 1868], 'lens': 'L4', 'check': 'Lagoon execution changes against the PoolManager: BLS12-381 input limits, 0x7D transactions, ETHLiquidity pause and message expiry.',
     'result': 'No opcode changes. The BLS limits matter only to calls with input, and the PoolManager calls a precompile only through a native take with empty calldata. The 0x7D transaction runs no EVM code. ETHLiquidity, SuperchainETHBridge and the interop proxies still have no implementation and hold 0 wei on 2026-11-26; ETHLiquidity has no receive or fallback, so a native take to it reverts.',
     'source': 'https://specs.optimism.io/protocol/lagoon/exec-engine.html; https://raw.githubusercontent.com/ethereum-optimism/optimism/op-contracts/v10.0.0/packages/contracts-bedrock/src/L2/ETHLiquidity.sol; ' + LOGS + 'interop-predeploys.txt'},
]

leads = [
    {'chainIds': [57073, 1868], 'lens': 'L3', 'question': 'Ink and Soneium activate Lagoon on 11 January 2027 without interop. Does the upgrade still install ETHLiquidity with type(uint128).max wei there, and can anything on those chains call its mint?', 'why': 'A funded ETHLiquidity on a chain with no dependency set would hold native value that only a bridge with no counterpart could release.', 'priority': 'low'},
    {'chainIds': [10], 'lens': 'L1', 'question': 'Which commit is op-reth/v0.0.0-dev-unknown on mainnet.optimism.io and rpc-qnd.inkonchain.com, and do its op-revm and revm-interpreter files equal v2.10.0?', 'why': 'It answers most OP Mainnet reads, names no version, and batch elements are split between it and v2.8.1, so its results are not pinned.', 'priority': 'low'},
    {'chainIds': [10, 130, 57073, 1868], 'lens': 'L1', 'question': 'On 10 December 2026, rerun the battery, the targeted set and set 1 on OP Sepolia and Unichain Sepolia after Lagoon, and read the implementations installed behind 0x4200..0022 to 0x25.', 'why': 'Lagoon ships to testnets first; the day-one builds are the ones mainnet will run on 11 January.', 'priority': 'medium'},
]

op_rep = rd('replay/run-10.log')
leadResults = [
    {'leadId': 'L-1133', 'outcome': 'finding', 'answer': '30 three-element web3_clientVersion batches to each of the seven endpoints. mainnet.optimism.io mixed op-reth/v2.8.1-72207294 and op-reth/v0.0.0-dev-unknown inside 18 of 30 batches; Base, Unichain, Zora, World Chain, Ink (rpc-gel) and Soneium answered one build in every batch. Recorded as a finding (operator, info). The chains 42161 and 137 of this lead belong to other units and were not queried.'},
    {'leadId': 'L-1057', 'outcome': 'inconclusive', 'answer': 'op-rbuilder has no tag after v0.4.14 and main still pins revm 41.0.0 and optimism rev 85f7c13d, so no builder release names Lagoon. Its instruction files equal those of revm-interpreter 43.0.2 except the SSTORE cold-load skip threshold, which the 2,300 gas sentry makes unreachable, so a builder on it computes the same results for PoolManager code. Which builder will produce 0x7D blocks is still unknown.'},
    {'leadId': 'L-983', 'outcome': 'inconclusive', 'answer': 'Base v1.6.0-rc.4 and main link evm2 rev 9b037449 only through base-common-evm2, which no crate depends on, and its README still says it is not wired into the node. The live path is revm-interpreter 42.0.0 (v1.5.6) or 43.0.2 (rc.4), which clamps shift and byte indices on the whole word before ruint; 15,510 new large-index vectors pass on Base.'},
    {'leadId': 'L-1069', 'outcome': 'inconclusive', 'answer': 'Not attempted this cycle; the unit spent its time on the interpreter angle. No new World Chain replay was run.'},
    {'leadId': 'L-1056', 'outcome': 'inconclusive', 'answer': 'Unichain\'s refund policy is not public: refund policies are an OP Enterprise feature chosen per sequencer, released op-reth uses a null policy, and Lagoon reaches mainnet on 11 January 2027. The spec bounds each refund by the transaction\'s own evmGasUsed, so an ordinary account can at most recover its own gas; refunds move no PoolManager balance.'},
    {'leadId': 'L-1066', 'outcome': 'cleared' if 'finished' in op_rep and '"txWithMismatch": 0' in rd('replay/raw/10/result.json') else 'inconclusive', 'answer': 'OP_REPLAY_ANSWER'},
    {'leadId': 'L-127', 'outcome': 'cleared', 'answer': 'Swept all 256 addresses of the 0x4200 range, the two Base registries and the World Chain EntryPoint and WorldID contracts with the four call shapes, then repeated the shapes through a forwarder at the PoolManager address so that the PoolManager is msg.sender and not tx.origin. Nothing beyond F-048 moves value the caller does not owe; L2StandardBridge rejects the PoolManager; L1BlockNumber\'s transfer answer is not 1 and is rejected by Currency.transfer.'},
    {'leadId': 'L-1071', 'outcome': 'cleared', 'answer': 'The reth branches behind every endpoint of this unit (op-v2.6.0-2, op-v2.7.0-2, base-v2.5.2.11) use fixed-cache 0.1.10 keyed by full (Address, StorageKey), full Address and full code hash, and fixed-cache compares the full key on every hit. Celo, X Layer and Arc builds in this lead belong to other units and were not read.'},
]

res = json.load(open(os.path.join(W, 'replay/raw/10/result.json'))) if os.path.exists(os.path.join(W, 'replay/raw/10/result.json')) else None
ncol = len(os.listdir(os.path.join(W, 'replay/raw/10/tx'))) if os.path.isdir(os.path.join(W, 'replay/raw/10/tx')) else 0
if res:
    ans = f'Collected {ncol} of the 1,474 OP Mainnet transactions left in the cycle 24 window (optimism.drpc.org and op.api.pocket.network now serve traces for those blocks) and replayed them through the cycle 24 model from their prestate traces: {res.get("txs")} transactions, {res.get("wordsCompared")} words compared, {res.get("txWithMismatch")} with a mismatch. The OP Mainnet total is now {18526 + (res.get("txs") or 0)} of 20,000. X Layer, Robinhood Chain, Elysium and BNB Smart Chain belong to other units.'
    cleared.append({'chainIds': [10], 'lens': 'L2', 'check': f'Traced replay of {res.get("txs")} more OP Mainnet PoolManager transactions from the cycle 24 window (L-1066).', 'result': f'{res.get("wordsCompared")} words compared, {res.get("txWithMismatch")} transactions with a mismatch, native mismatches {res.get("nativeMismatch")}.', 'source': LOGS + 'replay/raw/10/result.json, replay/collect-10.log'})
else:
    ans = f'Collected {ncol} of the 1,474 remaining OP Mainnet transactions before the time limit; the replay did not finish. The endpoints now serve traces for those blocks, so the collector in cycles/027/op-stack-eth.work/replay can be resumed.'
for r in leadResults:
    if r['answer'] == 'OP_REPLAY_ANSWER': r['answer'] = ans
    if r['leadId'] == 'L-1066' and res and res.get('txWithMismatch') != 0: r['outcome'] = 'inconclusive'

doc = {'unit': 'op-stack-eth', '_lenses': ['L1', 'L2', 'L3', 'L4'], 'profiles': profiles, 'findings': findings, 'cleared': cleared, 'leads': leads, 'leadResults': leadResults}
json.dump(doc, open(OUT, 'w'), indent=1)
print('written', len(profiles), 'profiles', len(findings), 'findings', len(cleared), 'cleared')
