"""Assemble cycle 22 op-stack-custom-gas.research.json from this cycle's readings and outputs."""
import json, os
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(W, 'out')
DST = os.path.join(os.path.dirname(W), 'op-stack-custom-gas.research.json')

def load(n):
    p = os.path.join(OUT, n)
    return json.load(open(p)) if os.path.exists(p) else None

top_x = load('top-xlayer.json')
if top_x is not None:
    xd = top_x['diffs']
    x_shapes = sorted({(d['target'], d['shape']) for d in xd})
    x_targets = sorted({d['target'] for d in xd})
    x_text = (f"X Layer (block {int(top_x['block'],16):,}): {len(top_x['results'])} targets, {len(xd)} shape answers differ between the stub and the top-level call, "
              f"at {len(x_targets)} targets ({', '.join(x_targets[:8])}). Six are balanceOf or transfer answers that reflect value or tokens moved by an "
              "earlier shape of the same stub batch, which the separate top-level calls do not carry. The other two are the L2StandardBridge 0x4200..0010 "
              "with empty calldata. It reverts in both modes, with a 132 byte reason under the stub and with 'not allow bridge' (100 bytes) at top level, where the "
              "caller is also tx.origin. Both modes refuse the native payout.")
else:
    x_text = "X Layer: the top-level run did not finish in this session."

RC = 'https://raw.githubusercontent.com/celo-org/celo-kona/refs/tags/celo/reth-v1.0.10/crates/celo-revm/src/handler.rs'
RCM = 'https://raw.githubusercontent.com/celo-org/celo-kona/main/crates/celo-revm/src/handler.rs'
TP = 'https://raw.githubusercontent.com/celo-org/celo-kona/refs/tags/celo/reth-v1.0.10/crates/celo-revm/src/precompiles/transfer.rs'
ACE = 'https://raw.githubusercontent.com/celo-org/celo-kona/refs/tags/celo/reth-v1.0.10/crates/alloy-celo-evm/src/lib.rs'
GAS = 'https://raw.githubusercontent.com/celo-org/revm/bd28f9420c250df2a5c4a6d8103b51ae06b5c222/crates/interpreter/src/gas.rs'
XMOD = 'https://raw.githubusercontent.com/okx/optimism/refs/tags/xlayer/v0.1.7/rust/alloy-op-evm/src/block/mod.rs'
XGL = 'https://raw.githubusercontent.com/okx/optimism/refs/tags/xlayer/v0.1.7/rust/alloy-op-evm/src/block/xlayer_gasless_contract.rs'
XBL = 'https://raw.githubusercontent.com/okx/optimism/refs/tags/xlayer/v0.1.7/rust/alloy-op-evm/src/block/xlayer_blacklist_contract.rs'
LC = 'https://raw.githubusercontent.com/ethereum-optimism/optimism/develop/packages/contracts-bedrock/src/L2/LiquidityController.sol'
CKR = 'https://github.com/celo-org/celo-kona/releases'
XRR = 'https://github.com/okx/xlayer-reth/releases'
OPV = 'https://newreleases.io/project/github/okx/optimism/release/xlayer%2Fv0.1.7'
LAG = 'https://docs.optimism.io/op-stack/protocol/hardforks/lagoon'
KAR = 'https://docs.optimism.io/op-stack/protocol/hardforks/karst'
ROAD = 'https://forum.celo.org/t/h1-2026-engineering-retro-h2-2026-roadmap/13528'
XST = 'https://status.xlayer.tech/maintenance'
CGT = 'https://specs.optimism.io/protocol/custom-gas-token/predeploys.html'
WD = 'research/network-risk/cycles/022/op-stack-custom-gas.work/out/'

profiles = [
 dict(chainId=42220, lens='L1', summary="forno.celo.org still answers reth/v2.2.0-74cc8bb (celo-reth v1.0.10) and Geth/v0.1.0-untagged-c7ed55b8 (go1.24.13), and no celo-reth release has appeared since v1.0.10. The battery, the targeted set, the battery pinned to each backend, both script sets and the mined swaps all match. The one new client difference is in gas refunds: CIP-64 transactions can get a wrapped refund. It changes no result an opcode or call returns.",
      deltas=[
        dict(delta="celo-revm in celo-reth v1.0.10 passes a negative refund counter to the stock set_final_refund. That function casts it to u64 and caps it at gas used divided by 5. The counter goes negative only for a CIP-64 transaction whose main call refills a fee-currency slot that the debit cleared. Such a transaction gets the maximum refund. celo-kona main clamps the counter to zero from Karst on, and the comment there says blocks before Karst keep the wrapped refund.", source=RCM, relevance='low'),
        dict(delta="The gas.rs file of the revm fork pinned by v1.0.10 (bd28f942) computes the final refund as (refunded as u64).min(gas_used / 5) at lines 199-205. A negative i64 therefore becomes the cap.", source=GAS, relevance='low'),
        dict(delta="The transfer precompile at 0xfd is implemented twice. celo-revm has transfer_run and alloy-celo-evm has transfer_precompile, a DynPrecompile marked stateful in celo_precompiles_map. At tag celo/reth-v1.0.10 both make the same checks in the same order: static context, at least 9,000 gas, caller equal to the CELO token, and input of exactly 96 bytes. Both apply the cold-status restore before Jovian and use the same journal transfer.", source=ACE, relevance='none'),
      ]),
 dict(chainId=42220, lens='L2', summary="The CIP-64 fee debit at v1.0.10 runs inside a journal checkpoint. On success the handler commits it and then clears the debit's transient storage and its self-destruct list before the main call runs. So the PoolManager's lock and its delta slots start empty, as A1 requires.",
      deltas=[dict(delta="cip64_rollbackable_debit_and_deduct_caller commits the debit checkpoint, clears transient_storage and truncates selfdestructed_addresses, and reverts the whole checkpoint when the transaction is rejected (handler.rs around lines 590-690 at the tag).", source=RC, relevance='none')]),
 dict(chainId=42220, lens='L3', summary="Nothing new for CELO or the fee currencies. Karst is still listed for Q4 2026 with no date, and CLZ answers NotActivated today.", deltas=[]),
 dict(chainId=42220, lens='L4', summary="The sixteen-shape sweep from a forwarding stub at the PoolManager address was repeated on 319 targets at block 83,748,106. Every class equals the cycle 6 sweep. The only changed words are the L1 block number returned by 0x4200..0013 and token balances. A top-level comparison of the same shapes found no target that answers differently by call depth. The CGT v2 predeploys 0x4200..0029 and 0x4200..002A exist on Celo only as proxies with no implementation.",
      deltas=[dict(delta="NativeAssetLiquidity (0x4200..0029) and LiquidityController (0x4200..002A) on Celo: proxy code, an implementation slot of zero and a balance of zero (eth_getStorageAt and eth_getBalance on forno, 2026-11-25).", source='https://forno.celo.org', relevance='low')]),
 dict(chainId=196, lens='L1', summary="rpc.xlayer.tech still answers reth/v2.3.0-f60420a xlayer/v0.0.7, and no xlayer-reth release has appeared after v0.0.7.3-rc.1. The battery, the targeted set, both script sets and 412 mined swaps match. CLZ answers NotActivated.", deltas=[]),
 dict(chainId=196, lens='L2', summary="The X Layer block executor at okx/optimism xlayer/v0.1.7 already contains the sequencer-defined metering code and the post-execution transaction code that Lagoon introduces. The code is gated to forks after Karst, and X Layer has not activated Karst. When it runs, it changes only the gas settlement paid by and to the transaction sender, the block beneficiary and the fee vaults.",
      deltas=[dict(delta="post_exec_settlement_deltas (block/mod.rs around lines 700-735) turns a post-execution gas refund into balance deltas for the sender, the beneficiary and the base fee recipient. It skips deposits and post-exec transactions. The comment says SDM and post-exec are enabled only on forks after Karst.", source=XMOD, relevance='low')]),
 dict(chainId=196, lens='L3', summary="Before a zero-priced transaction, the gasless check runs getGaslessAllowance on 0x19787404 as a system call from SYSTEM_ADDRESS. The result is decoded and the state is not committed, so nothing that check runs can change a PoolManager balance.",
      deltas=[dict(delta="is_gasless runs getGaslessAllowance(tx.to, tx.input) through transact_system_call. It treats a non-success or a malformed return as not gasless, and requires the transaction's gas limit to be at most the allowance.", source=XGL, relevance='none')]),
 dict(chainId=196, lens='L4', summary="The TxBlacklist at 0x59055c0e is a proxy to 0xe44bfef3, and its owner is an EOA (0x6ee7bda7, no code). Entries are keyed by the source hash of an L1 deposit. Write functions revert for an arbitrary caller with OwnableUnauthorizedAccount or a custom error, so an ordinary account cannot add an entry. The stub sweep of 311 targets at block 76,879,830 equals cycle 6 class for class.",
      deltas=[dict(delta="Probed by eth_call from 0x1111..1111 on 2026-11-25: owner() returns 0x6ee7bda7af04f61ccf93ab4b8db2289abe76c6aa (eth_getCode empty). Selectors 558a7297 and f2fde38b revert with 0x118cdaa7 (OwnableUnauthorizedAccount), and a75e2e6e and e67f4221 revert with 0x7c214f04.", source='https://rpc.xlayer.tech', relevance='low')]),
]

findings = [dict(
 ref='new',
 title='Celo pays the maximum gas refund to a CIP-64 transaction whose main call refills a fee-currency slot that the debit cleared',
 chainIds=[42220], lens='L1', assumptions=['A10'], effect='degrade', actor='unprivileged', severity='info',
 difference="On Ethereum the refund counter cannot be negative when a transaction ends. On Celo, the CIP-64 debit can clear a slot before the main call runs. The main call prices its SSTOREs against values from before the debit, so refilling that slot takes back a clearing refund that was never counted. The counter ends negative. celo-reth v1.0.10 passes it unchanged to set_final_refund, which casts it to u64 and caps it at one fifth of gas used. The celo-kona main branch clamps the counter to zero only from Karst on.",
 mechanism="A sender pays fees in a fee currency, and the debit takes its balance of that currency to exactly zero. The sender's main call then credits the sender's balance slot in the same currency again, for example through a transfer to itself from another holder or a take of that currency from the PoolManager. That SSTORE carries the -4,800 take-back, and the transaction ends with a negative counter. The handler's refund step on v1.0.10 does nothing to the counter (handler.rs:1213-1215 at the tag), and revm then grants a refund of gas_used / 5. The refund is applied after execution is complete. It changes no opcode result, no GAS reading inside the call and no return data. So no line of src/ computes or decides anything differently, and the PoolManager's balances and deltas are the same as they would be on Ethereum.",
 impact="Only the fee: the sender pays up to 20 percent less gas, and the base fee and tip recipients receive that much less. No PoolManager funds, LP positions or ERC-6909 claims are affected.",
 preconditions="The sender pays in a registered fee currency, the debit empties the sender's balance slot, and the main call refills it. The fork is before Karst, which is the case on Celo today.",
 mitigations="None needed for the PoolManager. Celo's clamp at Karst removes it.",
 coreRefs=['src/PoolManager.sol:104-114', 'src/PoolManager.sol:291-297'],
 sources=[dict(url=RC, supports='v1.0.10 refund() only forwards to the OP handler, with no clamp (lines 1213-1215)'),
          dict(url=RCM, supports='main clamps a negative counter to zero from Karst; its comment and tests describe the wrap to the cap before Karst'),
          dict(url=GAS, supports='set_final_refund casts refunded() to u64 and takes min with gas_used / 5 (lines 199-205)')],
 evidence='primary')]

cleared = [
 dict(chainIds=[42220,196], lens='L1', check="Opcode battery (99,985 vectors) and targeted set (85,544 vectors) rerun on 2026-11-25. The battery was also run pinned to each forno backend with pin.py: 167 batches kept on reth/v2.2.0-74cc8bb and 167 on Geth c7ed55b8.",
      result="0 mismatches and 0 errors on both chains and on both Celo backends.", source=WD+'battery.json, targeted.json, battery-celo-reth.json, battery-celo-geth.json (eth_call on https://forno.celo.org and https://rpc.xlayer.tech)'),
 dict(chainIds=[42220,196], lens='L1', check="PoolManager script sets pmdiff.py (250 scripts) and pmdiff2.py (300 scripts, 16,263 calls) against Ethereum.",
      result="250/250 and 300/300 identical on both chains, with no difference in native payouts.", source=WD+'pmdiff.json, pmdiff2.json'),
 dict(chainIds=[42220,196], lens='L1', check="Recent mined swaps checked with swaps.py and replayed with replay.py.",
      result="Celo: 113 swaps, all exact on the tick relation, and 15 multi-step swaps plus 1 other replayed with no failure (up to 39 steps). X Layer: 412 swaps exact, 354 exact-in and 19 exact-out pairs on the single-step formulas.", source=WD+'swaps.json, replay.json'),
 dict(chainIds=[42220], lens='L4', check="The two implementations of the Celo transfer precompile (celo-revm transfer_run and alloy-celo-evm transfer_precompile) at tag celo/reth-v1.0.10. If they disagreed, a builder and an importer could treat a CELO token transfer from the PoolManager differently.",
      result="Same guards in the same order: static, gas of at least 9,000, caller equal to the CELO token, and input of exactly 96 bytes. Same decoding of from, to and value, the same journal transfer, and the same pre-Jovian cold restore. The DynPrecompile is marked stateful, so the precompile result cache, which skips stateful entries, never serves it.", source=ACE),
 dict(chainIds=[42220], lens='L2', check="Whether the CIP-64 debit can leave transient storage or a self-destruct record that the main call then reads, for example a PoolManager lock or delta slot (src/libraries/Lock.sol, src/libraries/CurrencyDelta.sol).",
      result="At v1.0.10 the debit runs in a checkpoint. On success the handler clears transient_storage and truncates selfdestructed_addresses before the main call. On rejection it reverts the checkpoint. The PoolManager starts each transaction with no lock and no delta.", source=RC),
 dict(chainIds=[42220], lens='L1', check="Whether the wrapped CIP-64 refund on Celo before Karst changes anything the PoolManager computes.",
      result="The refund is applied after execution and affects only the gas fee. No opcode result, GAS reading or return data inside the transaction changes, so no line of src/ decides differently. Recorded as an information finding.", source=GAS),
 dict(chainIds=[196], lens='L3', check="The X Layer gasless allowance check, a system call before each zero-priced transaction, for any state it leaves behind.",
      result="It goes through transact_system_call from SYSTEM_ADDRESS. Only the decoded (allowed, gasLimit) pair is used and the state is not committed, so a PoolManager balance cannot change.", source=XGL),
 dict(chainIds=[196], lens='L2', check="Upcoming forks on X Layer: the sequencer-defined metering and post-execution transaction code already in xlayer/v0.1.7, assumed live within six months.",
      result="It is gated to forks after Karst. post_exec_settlement_deltas moves gas money only between the transaction sender, the block beneficiary and the base fee recipient, and skips deposits. A PoolManager cannot be a transaction sender, so no PoolManager balance and no delta between a sync and a settle can change. Execution is priced as before; the refund comes afterwards.", source=XMOD),
 dict(chainIds=[42220,196], lens='L1', check="Upcoming forks: Lagoon (interop, post-execution transactions, sequencer-defined metering) on these chains within six months.",
      result="Lagoon has no mainnet or Sepolia activation in the OP registry and its spec is not final. Celo has not yet set a time for Karst, and X Layer has not activated it. Lagoon therefore cannot reach either chain in the window. The X Layer code that exists for it is cleared above.", source=LAG),
 dict(chainIds=[42220,196], lens='L4', check="Lead L-414: sixteen call shapes sent through a forwarding stub at the PoolManager address and again as top-level eth_call from the PoolManager address, with the same stub code and balance overrides. The question is whether any target answers differently by depth, returns a hook selector, or returns a 32 byte true to transfer without being a token.",
      result="Celo (block 83,748,106): 319 targets, 7 shape answers differ, all explained by state that earlier shapes of the same stub batch left behind. The 1e15 wei deposited into the WETH predeploy and the EntryPoints shows up in a later balanceOf. That deposit also lets the later transfer(rcpt,1) of the WETH predeploy succeed. The 1 wei of USDm moved by the earlier transfer shape shows up in the PoolManager's balance. In both modes the only answers that start with a hook selector come from the identity precompile 0x04, which echoes its input as it does on Ethereum. The only 32 byte true answers to transfer come from tokens: the WETH predeploy, the CELO token and USDm on Celo, and the WETH predeploy and 0xe538905c on X Layer. " + x_text,
      source=WD+'top-celo.json, top-xlayer.json, sweep-celo.json, sweep-xlayer.json'),
 dict(chainIds=[42220,196], lens='L4', check="Lead L-452 baseline: the stub sweep repeated today against the cycle 6 sweep.",
      result="Every class (success, return length, balance change) is the same on both chains. The changed words are the L1 block number at 0x4200..0013 and token balances.", source=WD+'sweep-celo.json, sweep-xlayer.json'),
 dict(chainIds=[42220], lens='L3', check="Lead L-557, first step: what WRAP and UNWRAP actions do when WETH9 is the CELO token.",
      result="On the CELO token, deposit() and withdraw(1) revert with value 0 and with value 1 (eth_call from a funded EOA). A periphery action that wraps or unwraps through WETH9 therefore reverts the whole transaction and strands nothing. The full mint and removal simulations through the deployed periphery were not run.", source='https://forno.celo.org'),
 dict(chainIds=[42220,196], lens='L1', check="CLZ (EIP-7939) on both chains today.", result="An eth_call with code 60011e returns 'EVM error: NotActivated' on forno and rpc.xlayer.tech, so Osaka rules are not active.", source='https://forno.celo.org, https://rpc.xlayer.tech'),
]

leads = [
 dict(chainIds=[42220], lens='L1', question="When Celo sets a Karst time, does the celo-reth release that carries it contain the refund clamp of celo-kona main, and what predeploy code does the L2 Contract Manager install at 0x4200..0029, 0x4200..002A and the other 0x4200 addresses? Rerun stub_sweep.py and toplevel.py on the first day after activation.", why="LiquidityController.mint delivers native value by SafeSend, a forced send that does not need a receive function. Once a minter is authorized on Celo, native CELO can arrive at the PoolManager between someone's sync of the CELO token and their settle, the F-137 pattern.", priority='medium'),
 dict(chainIds=[196], lens='L2', question="When X Layer schedules Karst, which post-execution transaction format does it enable, and does derivation accept a post-exec transaction whose payload names an address other than the senders, beneficiary and vaults of the block?", why="The settlement deltas read at xlayer/v0.1.7 move gas money only to those three parties. A payload format that let the sequencer credit other accounts would be a balance change outside execution (A2), at operator level.", priority='low'),
]

leadResults = [
 dict(leadId='L-088', outcome='cleared', answer="The fork of 10 November 2026 (op-node xlayer/v0.1.7 with xlayer-reth v0.0.7.3) added Glamsterdam L1 header compatibility, the Gasless whitelist contract and GASLESS_WHITELIST predeploy, and the fix that limits the gasless base-fee bypass to the intended transaction. The release notes on newreleases.io and the X Layer status page say so. The EVM fork list still ends at Jovian, and CLZ answers NotActivated today. Transaction validity changed only for zero-priced whitelisted transactions. Gas rules for priced transactions and the system calls that touch the PoolManager did not change."),
 dict(leadId='L-554', outcome='inconclusive', answer="Operator level. Whether the risk control filter is on in the mainnet sequencer still cannot be observed from outside. Second half, X Layer only: TxBlacklist entries are keyed by the source hash of an L1 deposit (xlayer_blacklist_contract.rs at xlayer/v0.1.7). The contract at 0x59055c0e is owned by the EOA 0x6ee7bda7, and its write functions revert for an arbitrary caller with OwnableUnauthorizedAccount or 0x7c214f04. An ordinary account therefore cannot create an entry for a deposit that pays the PoolManager or a pooled token. Soneium is outside this unit."),
 dict(leadId='L-604', outcome='inconclusive', answer="Still no celo-reth release after v1.0.10 (20 November 2026), and celo-kona main still locks revm-interpreter 42.0.0. Today's battery, targeted set, both script sets and the mined swaps pass on both forno backends. Open until a release ships."),
 dict(leadId='L-557', outcome='inconclusive', answer="Partial. deposit() and withdraw(uint256) on the CELO token revert with and without value, so any WRAP or UNWRAP action of the PositionManager or the Universal Router reverts whole and strands no value. The mint and full-removal simulations through both deployed contracts, which need Permit2 approvals arranged by state override, were not run this cycle."),
 dict(leadId='L-453', outcome='inconclusive', answer="celo-monorepo issue 11750 (Custom Gas Token v2) was closed on 21 July 2026, and its sub-issues could not be read. The OP specification says only the L1 ProxyAdmin owner authorizes LiquidityController minters. In the Optimism develop branch, LiquidityController.mint withdraws from NativeAssetLiquidity and delivers with new SafeSend{value}, a forced send that does not need a receive function in the recipient. So native value can reach the PoolManager outside settle. On Celo today both predeploy proxies have no implementation and a zero balance, so the path is not live. What the transfer precompile and the CELO proxy become after the migration is still unknown."),
 dict(leadId='L-452', outcome='inconclusive', answer="Karst has no activation time on Celo. The baseline sweep was rerun today and equals cycle 6 class for class. The leads list carries the check forward to the first day after activation."),
 dict(leadId='L-414', outcome='cleared', answer="Answered for Celo and X Layer; Ethereum, Monad and MegaETH are outside this unit. With the same stub code at the PoolManager address in both modes, the top-level answers equal the stub answers, apart from state carried between shapes of one stub batch. Only the identity precompile 0x04 echoes a hook selector, as on Ethereum, and only tokens return a 32 byte true to transfer."),
]

d = dict(unit='op-stack-custom-gas', _lenses=['L1','L2','L3','L4'], profiles=profiles, findings=findings, cleared=cleared, leads=leads, leadResults=leadResults)
json.dump(d, open(DST, 'w'), indent=1)
print('wrote', DST)
