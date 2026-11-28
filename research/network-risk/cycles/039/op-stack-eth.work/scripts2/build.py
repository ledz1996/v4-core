"""Assemble op-stack-eth.research.json for cycle 39 from the work directory results."""
import json, os, sys
W = 'research/network-risk/cycles/039/op-stack-eth.work'
OUT = 'research/network-risk/cycles/039/op-stack-eth.research.json'
ALL = [10, 8453, 130, 7777777, 480, 57073, 1868]
LAG = [10, 130, 57073, 1868]
RC4 = [130, 57073, 1868]

op = {}
p = os.path.join(W, 'out/l1341-op-sample.json')
if os.path.exists(p):
    op = json.load(open(p))

REG = 'https://raw.githubusercontent.com/ethereum-optimism/superchain-registry/main/superchain/configs/mainnet/op.toml'
LOCK11 = 'https://raw.githubusercontent.com/ethereum-optimism/optimism/op-reth/v2.11.0-rc.1/rust/Cargo.lock'
LOCK10 = 'https://raw.githubusercontent.com/ethereum-optimism/optimism/op-reth/v2.10.0/rust/Cargo.lock'
SPEC = 'https://raw.githubusercontent.com/ethereum-optimism/optimism/op-reth/v2.11.0-rc.1/rust/op-revm/src/spec.rs'
PREC = 'https://raw.githubusercontent.com/ethereum-optimism/optimism/op-reth/v2.11.0-rc.1/rust/op-revm/src/precompiles.rs'
HAND = 'https://raw.githubusercontent.com/ethereum-optimism/optimism/op-reth/v2.11.0-rc.1/rust/op-revm/src/handler.rs'
BLK = 'https://raw.githubusercontent.com/ethereum-optimism/optimism/op-reth/v2.11.0-rc.1/rust/alloy-op-evm/src/block/mod.rs'
NULL = 'https://raw.githubusercontent.com/ethereum-optimism/optimism/op-reth/v2.11.0-rc.1/rust/alloy-op-evm/src/post_exec/null.rs'
PMOD = 'https://raw.githubusercontent.com/ethereum-optimism/optimism/op-reth/v2.11.0-rc.1/rust/alloy-op-evm/src/post_exec/mod.rs'
SDM = 'https://raw.githubusercontent.com/ethereum-optimism/specs/main/specs/protocol/lagoon/sdm.md'
EXE = 'https://raw.githubusercontent.com/ethereum-optimism/specs/main/specs/protocol/lagoon/exec-engine.md'
BASEUP = 'https://docs.base.org/upgrades/overview.md'
EVEREST = 'https://docs.base.org/upgrades/everest/overview.md'
ZORA = 'https://raw.githubusercontent.com/ethereum-optimism/superchain-registry/main/superchain/configs/mainnet/zora.toml'
WORLD = 'https://raw.githubusercontent.com/ethereum-optimism/superchain-registry/main/superchain/configs/mainnet/worldchain.toml'

builds = {
    10: 'op-reth/v0.0.0-dev-unknown and op-reth/v2.8.1-72207294 (the endpoint routes each request to one of two builds)',
    8453: 'reth/v2.5.2-9e380dd base/v1.5.6',
    130: 'op-reth/v2.10.0-rc.4-65e80332',
    7777777: 'conduit-op-reth/v2.5.1-8f0ccac',
    480: 'world-chain/v2.8.2-9596311',
    57073: 'op-reth/v2.10.0-rc.4-65e80332 (rpc-gel) and op-reth/v0.0.0-dev-unknown (rpc-qnd)',
    1868: 'op-reth/v2.10.0-rc.4-65e80332',
}
swaps = {10: 3335, 8453: 2101, 130: 5904, 7777777: 461, 480: 210, 57073: 4798, 1868: 464}

rerun_src = W + '/out/clientver.txt, out/battery.log, out/targeted.log, out/pmdiff.log, out/pmdiff2.log, out/swaps.log, out/replay.log, out/lagoonprobe.json'

profiles = []
for c in ALL:
    d1 = [{"delta": f"Rerun on 2026-11-28 from 03:04 UTC at {builds[c]}, the builds cycle 37 recorded and that answered again at 03:23 UTC: 99,985 battery and 85,544 targeted vectors give the specified word, 250 of 250 and 300 of 300 PoolManager scripts are identical to the Ethereum reference, and {swaps[c]} mined swaps give no tick or amount mismatch.",
           "source": W + '/out/clientver.txt', "relevance": "none"}]
    if c in RC4:
        d1.append({"delta": "The final op-reth v2.10.0 release has the same Cargo.lock as v2.10.0-rc.4 (byte equal) and the same op-revm sources, so the rc.4 results describe the final release too. op-reth v2.11.0-rc.1 pins the same revm 43.0.x crates and ruint 1.20.0; its only op-revm change is that a deposit mint now saturates at the largest balance instead of overflowing.",
                   "source": LOCK11, "relevance": "none"})
    if c == 57073:
        d1.append({"delta": "rpc-qnd.inkonchain.com runs every call of debug_traceCall through revm's inspector loop, the loop an op-reth sequencer uses when it produces blocks with a post-execution refund policy. All 185,529 battery and targeted vectors gave the specified word through that loop, and 22 PoolManager scripts gave the same step trace as the reference interpreter over 772,941 steps (8 heavy scripts skipped).",
                   "source": W + '/out/inspect-ink-qnd.json', "relevance": "low"})
    if c == 10:
        d1.append({"delta": "optimism.drpc.org (reports Geth/v10.0.0/drpc, a gateway) ran 184,729 of the 185,529 vectors through debug_traceCall with no mismatch; two batches were refused with HTTP 429.",
                   "source": W + '/out/inspect-op-drpc.json', "relevance": "none"})
    profiles.append({"chainId": c, "lens": "L1", "summary": "Every vector, script and mined swap rerun this cycle matches the specification at the builds the endpoint reports, which are the builds cycle 37 recorded." + (" The final v2.10.0 release and v2.11.0-rc.1 pin the same interpreter and integer crates as the rc.4 build in service." if c in RC4 else "") + (" The inspector loop that a Lagoon sequencer would run also matches." if c == 57073 else ""), "deltas": d1})

    if c in LAG:
        d2 = [{"delta": "Read in alloy-op-evm at op-reth v2.11.0-rc.1: the metering settlement is applied to the state diff after evm.transact returns and before commit. It credits tx.signer() and debits the block beneficiary, the base fee vault and the operator fee vault with checked subtraction. The only refund policy that ships is NullRefundPolicy, whose step hook is empty and whose refund is zero, so a sequencer running this release appends no 0x7D transaction unless an operator plugs in another policy.",
               "source": BLK, "relevance": "low"}]
        s2 = "The Lagoon settlement code and the default refund policy were read at the release that carries them. They move balances only of the transaction signer and the three fee accounts, after execution."
    else:
        d2 = []
        s2 = "Nothing new on storage, transient storage, transaction boundaries or state changes outside the EVM since cycle 37."
    if c in (10, 7777777):
        d2.append({"delta": "No failed deposit with value was found next to a PoolManager transaction: on Zora every deposit in the 406 blocks with a PoolManager log between blocks 51,570,810 and 54,570,810 is the L1 attributes deposit, and none failed" + (f"; on OP Mainnet {op.get('sampled', 0)} sampled blocks with a PoolManager log in the last 200,000 blocks held {op.get('deposits', 0)} deposits and {op.get('failedDeposits', 0)} failed ones" if op else "") + ".",
                   "source": W + '/out/l1341-zora-3m.json', "relevance": "none"})
    profiles.append({"chainId": c, "lens": "L2", "summary": s2, "deltas": d2})

    profiles.append({"chainId": c, "lens": "L3", "summary": "ETH is still the gas token. Nothing new on gas caps or native currency since cycle 37." + (" Lagoon metering refunds lower the gas charged after execution and leave the gas available inside execution unchanged." if c in LAG else ""), "deltas": ([{"delta": "Under Lagoon metering the block gas limit bounds gas before refund and the refund cannot exceed the gas the EVM measured; GAS inside the transaction is unchanged.", "source": SDM, "relevance": "none"}] if c in LAG else [])})

    if c in LAG:
        d6 = [{"delta": "lagoon_time = 1799683201 (11 January 2027 16:00:01 UTC) in the registry, unchanged. op-revm at v2.10.0 and v2.11.0-rc.1 maps OpSpecId::LAGOON to SpecId::OSAKA, the Karst instruction set, and its handler has no Lagoon branch; precompiles.rs replaces only the BLS12-381 MSM and pairing entries.",
               "source": REG, "relevance": "low"},
              {"delta": "eth_call with a block override of time 1799683301 does not run Lagoon rules on this endpoint: a G1 MSM call with 900 zero pairs (144,000 bytes, above the Lagoon limit of 817 pairs) returned 128 bytes both with and without the override. The fork cannot be rehearsed through eth_call before it activates.",
               "source": W + '/out/lagoonprobe.json', "relevance": "low"}]
        s6 = "Lagoon is still the only fork in the next six months, at 1799683201. Its op-reth code keeps the Osaka instruction set, and a block time override does not switch an endpoint to it."
    elif c == 8453:
        d6 = [{"delta": "The Base upgrades page lists Denim as activated on mainnet on 5 November 2026 (recorded in earlier cycles) and Everest (EIP-8430 Base Transactions: batching, sponsorship, token gas payment) with Sepolia and mainnet TBD.", "source": BASEUP, "relevance": "low"}]
        s6 = "Everest is still TBD, so no Base fork is scheduled in the next six months. The time override probe returned the Karst result here too."
    else:
        d6 = [{"delta": "The registry config schedules no fork after Karst" + (" (8 July 2026)" if c == 7777777 else " (21 September 2026)") + "; no lagoon_time is set.", "source": ZORA if c == 7777777 else WORLD, "relevance": "none"}]
        s6 = "No fork is scheduled in the next six months; the registry config has no Lagoon time."
    profiles.append({"chainId": c, "lens": "L6", "summary": s6, "deltas": d6})

cleared = [
    {"chainIds": ALL, "lens": "L1",
     "check": "Rerun of battery.py, targeted.py, pmdiff.py, pmdiff2.py, swaps.py and replay.py for the seven chains on 2026-11-28 from 03:04 UTC, with web3_clientVersion recorded before the runs and again at 03:23 UTC.",
     "result": "Each endpoint answered the build cycle 37 recorded. 99,985 battery and 85,544 targeted vectors (MULMOD, ADDMOD, DIV, SDIV, MOD, SMOD, SIGNEXTEND, SAR, SHL, SHR, BYTE, EXP, comparisons, JUMPI, KECCAK256, MCOPY, CALLDATALOAD and the 512 bit mulDiv shape) gave the specified word on all seven chains. 250 of 250 and 300 of 300 PoolManager scripts were identical to the Ethereum reference. 17,273 mined swaps gave no tick mismatch (one OP Mainnet swap ends on the tick boundary that src/libraries/Pool.sol:430-431 leaves after a downward crossing) and 69 multi-step pairs replayed through the whole swap loop with one Zora replay refused by the endpoint.",
     "source": rerun_src},
    {"chainIds": [57073, 10], "lens": "L1",
     "check": "The battery and targeted vectors through debug_traceCall with callTracer, which runs revm's inspector loop instead of the plain loop. A sequencer that produces Lagoon blocks with a refund policy executes every transaction through this loop (alloy-op-evm PostExecCompositeInspector).",
     "result": "rpc-qnd.inkonchain.com (op-reth/v0.0.0-dev-unknown) returned the specified word for 185,529 of 185,529 vectors. optimism.drpc.org returned it for the 184,729 it served; two batches were refused with HTTP 429. The step traces of 22 PoolManager scripts on rpc-qnd equal the reference interpreter at every step over 772,941 steps (call depth, program counter, opcode and top four stack words).",
     "source": W + '/out/inspect-ink-qnd.json; ' + W + '/out/inspect-op-drpc.json; ' + W + '/out/trace-ink-qnd.json'},
    {"chainIds": LAG, "lens": "L1",
     "check": "Crate pins and op-revm sources of op-reth v2.10.0 (final) and v2.11.0-rc.1 compared with v2.10.0-rc.4, the build in service on Unichain, Ink and Soneium.",
     "result": "v2.10.0 has a Cargo.lock byte equal to rc.4 and identical op-revm sources. v2.11.0-rc.1 pins revm 43.0.3, revm-interpreter 43.0.2, revm-bytecode 43.0.0 and ruint 1.20.0 as before; on the interpreter and integer path only reth-evm, reth-revm (2.7.0 to 2.8.1) and revm-inspectors (0.44.0 to 0.44.3) move. Its op-revm differs only in handler.rs, where the deposit mint is added with saturating addition. No release changes an opcode handler, the integer library, jump analysis or the keccak path that src/libraries/FullMath.sol, TickMath.sol, BitMath.sol, SqrtPriceMath.sol or SwapMath.sol reach.",
     "source": LOCK10 + '; ' + LOCK11 + '; ' + HAND},
    {"chainIds": LAG, "lens": "L1",
     "check": "Which instruction set the Lagoon spec id selects in op-revm.",
     "result": "spec.rs maps both KARST and LAGOON to SpecId::OSAKA, so the opcode table, gas schedule and the EIP-7825 transaction gas cap of Karst carry over unchanged. handler.rs has no Lagoon branch. precompiles.rs lagoon() takes karst() and replaces only the BLS12-381 G1 MSM, G2 MSM and pairing entries, which src/ never calls with an input it builds.",
     "source": SPEC + '; ' + PREC + '; ' + EXE},
    {"chainIds": LAG, "lens": "L2",
     "check": "Lagoon metering settlement as implemented in alloy-op-evm block/mod.rs at op-reth v2.11.0-rc.1, and the refund policy that ships with it.",
     "result": "post_exec_settlement_deltas computes the refund from the gas the EVM reported after evm.transact returns; apply_post_exec_refund_to_state credits tx.signer() and debits the beneficiary, BASE_FEE_RECIPIENT and OPERATOR_FEE_RECIPIENT, with checked_sub that makes an underflow invalidate the block. Nothing runs EVM code after it, so no PoolManager frame can see the new balances inside the refunded transaction, and src/PoolManager.sol:349-364 credits native only from msg.value. The only policy exported by post_exec/mod.rs is NullRefundPolicy, whose inspect_step is empty and whose finish_tx returns a zero refund.",
     "source": BLK + '; ' + NULL + '; ' + PMOD},
    {"chainIds": LAG, "lens": "L3",
     "check": "Whether any path in src/ branches on remaining gas, which a metering refund or a Lagoon gas rule could change.",
     "result": "Outside src/test the only uses of gas() forward all remaining gas to a call: the native transfer and ERC-20 transfer in src/types/Currency.sol:48 and :73 and the hook call in src/libraries/Hooks.sol:134. No branch reads gasleft. The metering refund is applied after execution and cannot change what any of these calls returns.",
     "source": "src/types/Currency.sol:48; src/types/Currency.sol:73; src/libraries/Hooks.sol:134"},
    {"chainIds": [10, 7777777], "lens": "L2",
     "check": "A deposit with value addressed to the PoolManager itself.",
     "result": "The PoolManager has no receive or fallback function and its only payable functions are settle and settleFor (src/PoolManager.sol:300, 305), both behind onlyWhenUnlocked (src/PoolManager.sol:96-99). A deposit with value that calls it directly reverts and its mint stays at the deposit's from address. A deposit that calls an attacker's contract can only do what an ordinary transaction does. The saturating mint of v2.11.0-rc.1 changes nothing below a balance of 2^256 minus the mint.",
     "source": "src/PoolManager.sol:96-99; src/PoolManager.sol:300-307; " + HAND},
]

leads = [
    {"chainIds": LAG, "lens": "L6", "question": "On 11 January 2027 after 16:00:01 UTC (or on the Sepolia chains after 10 December 2026), do battery.py, targeted.py, pmdiff.py and pmdiff2.py give the same results at a block past lagoon_time on OP Mainnet, Unichain, Ink and Soneium?", "why": "eth_call with a block time override keeps Karst rules on every endpoint (out/lagoonprobe.json), so no run before activation exercises the Lagoon spec. The source shows the same instruction set; the live run is the only direct check.", "priority": "low"},
    {"chainIds": LAG, "lens": "L1", "question": "When an op-reth release ships a refund policy other than NullRefundPolicy (block level warming refunds are described in alloy-op-evm block/mod.rs comments), does its inspect_step only read the interpreter it is given as a mutable reference?", "why": "A sequencer runs the policy on every transaction it produces. A policy that wrote to the interpreter would make produced blocks differ from verifier execution; that is a liveness risk under operator control, and a write that verifiers also accepted would change PoolManager results.", "priority": "low"},
]

lr = [
    {"leadId": "L-1344", "outcome": "cleared",
     "answer": "Read op-reth v2.10.0 and v2.11.0-rc.1 (the registry already carries lagoon_time 1799683201; the release source that embeds it could not be fetched, the superchain config archive returned 404). Lagoon in op-revm maps to SpecId::OSAKA, the Karst instruction set, with no new opcode, no handler branch and no change to the EIP-7825 per transaction gas cap. precompiles.rs changes only the three BLS12-381 input limits. Deposit handling changes only in that the mint saturates at the largest balance. The execution side otherwise adds the 0x7D post-execution transaction and the metering settlement after each transaction, whose only shipped policy refunds nothing. The interpreter and integer crates are the same versions as the rc.4 build that every vector and script already ran on. Nothing changes what pool math or a long swap returns on 11 January 2027."},
    {"leadId": "L-1341", "outcome": "inconclusive",
     "answer": "No such block was found. On Zora all 406 blocks with a PoolManager log between 51,570,810 and 54,570,810 hold only the L1 attributes deposit, none failed." + (f" On OP Mainnet {op.get('sampled')} of {op.get('pmBlocks')} blocks with a PoolManager log in the last 200,000 blocks were sampled: {op.get('deposits')} deposits, {op.get('failedDeposits')} failed" + (f", hits {op.get('hits')[:3]}" if op.get('hits') else "") + "." if op else " The OP Mainnet scan could not finish. mainnet.optimism.io answers eth_getBlockReceipts with 'rpc method is not whitelisted' (queried 2026-11-28), optimism-rpc.publicnode.com found 4,056 blocks with a PoolManager log in the last 60,000 blocks but refused 26 log windows and then the receipt queries with HTTP 403 before the sample of 800 finished (console output of that run; its log was overwritten by the next run), and optimism.drpc.org refused 2,000 block log windows with HTTP 400 (out/l1341-op-sample.log, out/l1341-op-sample-drpc-empty.json).") + " The source settles the question for the PoolManager anyway: native credit comes only from msg.value (src/PoolManager.sol:352-354) and each deposit is its own transaction, so a failed deposit's mint cannot reach another transaction's deltas."},
    {"leadId": "L-1328", "outcome": "inconclusive",
     "answer": "No endpoint simulates the mint. OP Mainnet and Zora reject eth_call and eth_estimateGas from an empty account with OutOfFunds and refuse debug_traceCall (not whitelisted, or an API key is needed). optimism.drpc.org and rpc-qnd.inkonchain.com accept debug_traceCall with type 0x7e, mint and sourceHash fields, but the prestate diff shows only the sender's nonce change and no mint or value movement, so the fields are ignored and the call runs as an ordinary call. The row therefore still rests on the specification and on op-revm handler.rs, which credits the mint to the caller before execution and keeps it on failure."},
]

doc = {"unit": "op-stack-eth", "_lenses": ["L1", "L2", "L3", "L6"], "profiles": profiles, "findings": [], "cleared": cleared, "leads": leads, "leadResults": lr}
if op:
    cleared.append({"chainIds": [10, 7777777], "lens": "L2", "check": "Search for a failed deposit before a PoolManager transaction in the same block (L-1341).",
                    "result": f"Zora: 406 blocks with a PoolManager log in 3,000,000 blocks, 406 deposits, 0 failed. OP Mainnet: {op.get('sampled')} sampled blocks of {op.get('pmBlocks')} with a PoolManager log in the last 200,000 blocks, {op.get('deposits')} deposits, {op.get('failedDeposits')} failed.",
                    "source": W + '/out/l1341-zora-3m.json; ' + W + '/out/l1341-op-sample.json'})
json.dump(doc, open(OUT, 'w'), indent=1)
print('written', len(profiles), 'profiles', len(cleared), 'cleared')
