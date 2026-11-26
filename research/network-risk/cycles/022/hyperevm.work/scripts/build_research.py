"""Builds research/network-risk/cycles/022/hyperevm.research.json from the outputs in ../out."""
import json, os
W = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
O = os.path.join(W, 'out')
def j(n):
    p = os.path.join(O, n)
    return json.load(open(p)) if os.path.exists(p) else None
def res(n):
    d = j(n)
    if d is None: return None
    r = d['results'] if isinstance(d, dict) and 'results' in d else d
    return r[0] if isinstance(r, list) and r else r
bo, bh = res('battery-official.json'), res('battery-hyperlend.json')
to, th = res('targeted-official.json'), res('targeted-hyperlend.json')
po = res('pmdiff-official.json'); p2o = res('pmdiff2-official.json'); p2h = res('pmdiff2-hyperlend.json')
r121 = j('ruint121-hyperlend.json'); rsm = j('ruint_shift_model.json')
t12, t6 = j('trace12-b92ad36.json'), j('trace6-b92ad36.json')
def bt(r): return f"{r['ran']}/{r['vectors']} vectors, {r['mismatchCount']} mismatches, {len(r['errors'])} errors" if r else 'not run'
def pm(r, n): return f"{r['identical']}/{n} identical to Ethereum, different {r['different']}, errors {r['errors']}" if r else 'not completed'
def tr(t):
    if not t: return 'not completed'
    x = t['totals']; return f"{x['identical']} of {x['scripts']} scripts identical over {x['steps']:,} steps, {x['different']} different, {x['skipped']} skipped as too heavy for the reference, {x['errors']} endpoint errors (HTTP 429 or answers too large)"
r121r = r121['results'][0] if r121 else None
OFF = 'https://rpc.hyperliquid.xyz/evm'; NB = 'https://rpc.hyperlend.finance'
WD = 'research/network-risk/cycles/022/hyperevm.work'
SRC = 'https://raw.githubusercontent.com/hl-archive-node/nanoreth/nb-20261125-2'

profiles = [
 {"chainId": 999, "lens": "L1",
  "summary": "A public endpoint now serves the nanoreth build on revm 43.0.3 and ruint 1.20.1: rpc.hyperlend.finance answers web3_clientVersion with reth/v0.1.0-b92ad36, the commit of release nb-20261125-2, and grants about 200 million gas to eth_call. The battery, the targeted set and the ruint vectors give the specified word there, as they still do on the official node, which remains on Cancun without CLZ.",
  "deltas": [
   {"delta": "rpc.hyperlend.finance reports reth/v0.1.0-b92ad36 on 10 of 12 samples (the other 2 were HTTP 429), so the revm 43 generation is reachable for the first time through a public endpoint. rpc.purroofgroup.com still reports f0cad31 (revm 29 fork). A probe of GAS under a 10^9 gas request returns 199,995,382 there against 29,979,000 on the official node.", "source": f"{NB} web3_clientVersion and eth_call with state override, 2026-11-25, {WD}/out/clientversions.txt and out/hyperlend-versions.txt", "relevance": "low"},
   {"delta": f"Battery on the b92ad36 endpoint: {bt(bh)}; targeted set: {bt(th)}; cycle 17 ruint vectors: " + (f"{r121r['ran']} of {r121['vectors']} ran, {r121r['mismatchCount']} mismatches, {len(r121r['errors'])} batch lost to HTTP 429" if r121r else 'not run') + ".", "source": f"{NB}, {WD}/out/battery-hyperlend.json, targeted-hyperlend.json, ruint121-hyperlend.json", "relevance": "none"},
   {"delta": "ruint 1.20.1 adds u256 fast paths to wrapping_shl and wrapping_shr (src/bits.rs lines 464-540 and 605-640) and routes Shl and Shr by primitive integers through them (impl_shift, lines 852-925). revm-interpreter 43.0.2 calls them only with shift amounts below 256 (instructions/bitwise.rs lines 120-158). A line by line transcription of both fast paths and of arithmetic_shr matched exact integer shifts on " + (f"{rsm['cases']:,}" if rsm else '?') + " cases (shifts 0 to 300).", "source": f"https://static.crates.io/crates/ruint/ruint-1.20.1.crate (saved cycles/017/hyperevm.work/dl/x-ruint-1.20.1), {WD}/scripts/ruint_shift_model.py and out/ruint_shift_model.json", "relevance": "none"}]},
 {"chainId": 999, "lens": "L2",
  "summary": "In nanoreth nb-20261125-2 every HyperCore system transaction goes through the same revm transact call as a signed transaction and is committed on its own, and revm 43 clears transient storage at every transaction end. The HYPE system address holds about 944.5 million HYPE and its nonce rises with each delivery, so native deliveries are debited from a balance that exists in state.",
  "deltas": [
   {"delta": "System transactions are recognised by gas price 0 and their sender is decoded from the signature s value (s = 1 means 0x2222...2222). They are executed by self.evm.transact and committed per transaction; their gas is not added to block gas. nanoreth sets disable_eip3607 and disable_base_fee for every transaction in replay, with a TODO to restrict them to system transactions.", "source": f"{SRC}/src/node/evm/executor.rs lines 44-49, 241-320; {SRC}/src/node/primitives/transaction.rs lines 38-95; {SRC}/src/node/evm/config.rs lines 356-358", "relevance": "low"},
   {"delta": "0x2222222222222222222222222222222222222222 has 122 bytes of code (a receive function that emits Received), balance 944,493,751.77 HYPE and nonce 1,090,288 at head about 52,250,000.", "source": f"{OFF} eth_getBalance, eth_getCode, eth_getTransactionCount, 2026-11-25", "relevance": "none"}]},
 {"chainId": 999, "lens": "L3",
  "summary": "Nothing new for the gas token or token contracts. The official endpoint still grants about 30 million gas to eth_call, and the block gas limit of small blocks is unchanged.",
  "deltas": []},
 {"chainId": 999, "lens": "L4",
  "summary": "The read precompile range 0x0800 to 0x080D (or the block's highest address) is installed per block from recorded calls in nanoreth nb-20261125-2, and an input the block did not record halts with all gas used. CoreWriter is code installed at block 7,578,300. Neither changed since the earlier cycles, and the PoolManager never calls either unless a caller names them.",
  "deltas": [
   {"delta": "nb-20261125-2 adds a read precompile forwarder that answers unrecorded inputs on RPC paths at the chain head only; block execution never forwards and burns the gas limit as before.", "source": f"{SRC}/src/node/evm/executor.rs lines 101-145 and 373-458", "relevance": "none"}]},
]

cleared = [
 {"chainIds": [999], "lens": "L1", "check": "Rerun of battery.py, targeted.py, pmdiff.py and pmdiff2.py for chain 999 on the official node at head about 52,250,000.",
  "result": f"Battery {bt(bo)}; targeted {bt(to)}; pmdiff {pm(po, 250)}; pmdiff2 {pm(p2o, 300)}. Script 189 is the full-range swap cut short by the 30 million gas the official endpoint grants, as in every cycle since 10. Script 137 was not compared because the Ethereum reference endpoint answered HTTP 403 for it. MULMOD, ADDMOD, DIV, SDIV, MOD, SMOD, SIGNEXTEND, SAR, SHL, SHR, BYTE, EXP, the comparisons, JUMPI, KECCAK256, MCOPY and CALLDATALOAD, and the FullMath and UnsafeMath compositions behind src/libraries/FullMath.sol and src/libraries/SqrtPriceMath.sol, return the specified words.",
  "source": f"{OFF}; {WD}/out/battery-official.json, targeted-official.json, pmdiff-official.json, pmdiff2-official.json"},
 {"chainIds": [999], "lens": "L1", "check": "The same sets on the nanoreth nb-20261125-2 build (revm 43.0.3, ruint 1.20.1) through rpc.hyperlend.finance, the first public endpoint found that reports b92ad36.",
  "result": f"Battery {bt(bh)}; targeted {bt(th)}; pmdiff2 {pm(p2h, 300)}; cycle 17 ruint vectors " + (f"{r121r['ran']} ran with {r121r['mismatchCount']} mismatches" if r121r else 'not run') + f". Step traces against the reference interpreter: sets 1 and 2 {tr(t12)}, set 6 {tr(t6)}. pmdiff2.py asks for 25,000,000 gas (tools/opdiff/pmdiff2.py line 172), so script 189 is cut short there too; cycle 21 ran it at 199,000,000 gas on the same build and got the Ethereum answer 9ffffd01...136a (cycles/021/theme-fullrange-and-claims.work/raw/hyper-hyperlend-189.json). Script 20 was not compared because the Ethereum reference answered HTTP 403; the other 299 reference hashes equal the stored ones in opcodes/pmdiff2.json. The endpoint is load balanced; every sampled answer named b92ad36, but a batch served by another backend cannot be excluded.",
  "source": f"{NB}; {WD}/out/battery-hyperlend.json, targeted-hyperlend.json, pmdiff2-hyperlend.json, ruint121-hyperlend.json, trace12-b92ad36.json, trace6-b92ad36.json"},
 {"chainIds": [999], "lens": "L1", "check": "ruint 1.20.1 changelog entry #634 (shifts by primitive integers without truncating large amounts) on the opcode path.",
  "result": "revm-interpreter 43.0.2 saturates the shift operand to usize and only shifts when it is below 256; at 256 or more SHL and SHR return 0 and SAR returns 0 or all ones by the sign bit (bitwise.rs lines 120-158). The u256 fast paths of wrapping_shl, wrapping_shr and arithmetic_shr were transcribed and agree with exact shifts on all tested amounts. BYTE saturates its index and returns 0 from 32 up (lines 107-117). TickBitmap, BitMath and the Slot0 and BalanceDelta packing (src/libraries/TickBitmap.sol, src/libraries/BitMath.sol) therefore see the specified results.",
  "source": "cycles/017/hyperevm.work/dl/x-revm-interpreter-43.0.2 src/instructions/bitwise.rs lines 107-158; cycles/017/hyperevm.work/dl/x-ruint-1.20.1 src/bits.rs lines 17-19, 414-540, 554-660, 852-925; research/network-risk/cycles/022/hyperevm.work/out/ruint_shift_model.json"},
 {"chainIds": [999], "lens": "L2", "check": "revm 43 transient storage semantics, which nb-20261125-2 runs for every signed and system transaction.",
  "result": "JournalInner.commit_tx, discard_tx and finalize each clear transient storage (journal/inner.rs lines 141-170, 174-200, 207-250); tstore records the previous value only when it changes and a revert reinserts or removes it (inner.rs lines 1060-1106; revm-context-interface entry.rs lines 454-469). The crates match the checksums in the nb-20261125-2 Cargo.lock. The unlock flag, deltas and synced reserves of src/libraries/Lock.sol, CurrencyDelta.sol and CurrencyReserves.sol cannot carry from one transaction to the next on this client.",
  "source": "https://static.crates.io/crates/revm-context/revm-context-43.0.3.crate and revm-context-interface-43.0.2.crate (sha256 9b06efea... and 3068385c..., equal to the Cargo.lock entries), saved in research/network-risk/cycles/022/hyperevm.work/dl"},
 {"chainIds": [999], "lens": "L1", "check": "revm memory_limit, now enabled in nanoreth, against the memory the PoolManager uses.",
  "result": "The limit defaults to 2^32 - 1 bytes (revm-context cfg.rs lines 75-78 and 354-357). Expanding memory that far costs on the order of 10^13 gas, far above any call cap, so no PoolManager call can reach it and no result changes.",
  "source": "research/network-risk/cycles/022/hyperevm.work/dl/x-revm-context-43.0.3 src/cfg.rs; https://raw.githubusercontent.com/hl-archive-node/nanoreth/nb-20261125-2/Cargo.toml lines 74-79"},
 {"chainIds": [999], "lens": "L2", "check": "disable_eip3607 for all transactions in nanoreth replay.",
  "result": "It lets a replayed signed transaction come from an address with code, but the sender still comes from ECDSA recovery for every transaction with nonzero gas price (transaction.rs lines 77-95). No one holds a key for the PoolManager address and HyperEVM has no EIP-7702 (Cancun only, probe below), so it does not let anyone act as the PoolManager.",
  "source": "https://raw.githubusercontent.com/hl-archive-node/nanoreth/nb-20261125-2/src/node/evm/config.rs lines 356-358 and src/node/primitives/transaction.rs lines 77-95"},
 {"chainIds": [999], "lens": "L1", "check": "Upcoming forks: HyperEVM changes announced for the next six months, and the fork level on mainnet and testnet today.",
  "result": "Mainnet and testnet answer CLZ (0x1e) with NotActivated and have no code or output at 0x0b, 0x11 and 0x0100; PUSH0, MCOPY and transient storage work. The announcement channel lists HyperCore trading changes, L1 errors in HyperEVM error responses, the 1 USDC minimum and network upgrades on 11, 12 and 19 November, and no EVM fork. Nothing announced changes an opcode or a path the PoolManager uses, so funds already in it are unaffected the day after.",
  "source": "https://tg.me/hyperliquid_api ; research/network-risk/cycles/022/hyperevm.work/out/probe_fork.json (rpc.hyperliquid.xyz/evm and rpc.hyperliquid-testnet.xyz/evm, 2026-11-25)"},
 {"chainIds": [999], "lens": "L1", "check": "Did the public validator supervisor binary change since cycle 17?",
  "result": "hl-visor downloaded today has sha256 89338207...2e31, byte equal to the cycle 17 copy; hl-node itself is not served (HTTP 403). No new validator build is visible.",
  "source": "https://binaries.hyperliquid.xyz/Mainnet/hl-visor (2026-11-25), research/network-risk/cycles/022/hyperevm.work/dl/hl-visor"},
 {"chainIds": [999], "lens": "L4", "check": "Hooks that call HyperCore read precompiles or CoreWriter (L-068).",
  "result": "Hook hazard, pool-creator level: a precompile error halts with all forwarded gas, so a hook that reads one in beforeRemoveLiquidity can block exits from its own pool (src/libraries/Hooks.sol:131-160). Pools without such a hook are unaffected.",
  "source": "https://raw.githubusercontent.com/hl-archive-node/nanoreth/nb-20261125-2/src/node/evm/executor.rs lines 101-145"},
]

findings = [
 {"ref": "F-020",
  "title": "HyperCore sends unsigned transfers in the name of addresses that never signed, including a contract, and the record that names such an address is outside the deployer's documented action",
  "chainIds": [999], "lens": "L2", "assumptions": ["A2", "A8"], "effect": "freeze", "actor": "operator", "severity": "high",
  "difference": "HyperCore places unsigned system transactions at the top of HyperEVM blocks and states their sender itself, encoded in the signature s value. Under AQAv2 it sends token transfers in the name of the linked contract and of a treasury address. On Ethereum a balance leaves an address only through a transaction that address signed or a call made by its own code.",
  "mechanism": "nanoreth nb-20261125-2 takes the sender of any gas price 0 transaction from its s value with no signature check and executes it through the normal transact path. If HyperCore recorded the PoolManager as the treasury address of an aligned quote asset, such a transaction would call transfer on that token with the PoolManager as msg.sender, and the token balance would fall while pool state, ERC-6909 balances and protocol fee counters still count it as owed, because the PoolManager compares balances only between sync and settle inside one transaction. The last takes in that token would then revert inside the transfer. The aligned quote assets page is unchanged today and still gives no rule that the treasury address must sign or must be an account without code. The PoolManager nonce is still 1 on the official and archive endpoints, so no system transaction has used it as sender.",
  "impact": "All pools and ERC-6909 claims in a token for which HyperCore named the PoolManager as the rebalancing address. Nothing is exposed today.",
  "preconditions": "Two staked deployers of 500,000 HYPE each and a validator vote must name the PoolManager as treasury address. An ordinary account cannot.",
  "mitigations": "Watch the PoolManager nonce, which rises with any system transaction sent in its name. Ask the Hyperliquid team whether the node refuses an address with code as AQAv2 treasury.",
  "coreRefs": ["src/PoolManager.sol:279-288", "src/PoolManager.sol:349-365", "src/types/Currency.sol:40-88"],
  "sources": [
   {"url": "https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/aligned-quote-assets.md", "supports": "Treasury deployer designates the treasury address; activation by validator vote; 9:1 rebalance. Fetched 2026-11-25, byte equal to the cycle 20 copy."},
   {"url": f"{SRC}/src/node/primitives/transaction.rs", "supports": "System transaction sender decoded from s without signature (lines 38-95)."},
   {"url": "https://rpc.hyperliquid.xyz/evm eth_getTransactionCount 0x12D4Fd9C5DeDd00ab8a0bCe2CF0167bbf94b6B1F latest = 0x1, 2026-11-25", "supports": "No system transaction has been sent in the PoolManager name (same on rpc.purroofgroup.com)."}],
  "evidence": "inferred"}]

leads = [
 {"chainIds": [999], "lens": "L1", "question": "When an official HyperEVM endpoint (hl-node) grants more than 30,000,000 gas, or when hl-node is known to run a revm 43 generation, do pmdiff2 script 189 and the step traces match the reference there?", "why": "The validator's own output for the full-range swap and its interpreter generation are still seen only through nanoreth builds.", "priority": "low"}]

lr = [
 {"leadId": "L-977", "outcome": "inconclusive", "answer": "Privileged actor. The aligned quote assets page fetched today is byte equal to the cycle 20 copy and still names no signing rule for the treasury address. nanoreth nb-20261125-2 decodes a system transaction's sender from its s value with no signature (transaction.rs lines 38-95), so the client side shows no check either. F-020 stays plausible at operator level, severity high."},
 {"leadId": "L-974", "outcome": "cleared", "answer": "In nb-20261125-2 each system transaction, both the 0x2222 HYPE deliveries and the linked contract calls, runs through self.evm.transact and is committed alone (executor.rs lines 241-320). revm 43 clears transient storage in commit_tx and discard_tx and reverts frame changes on halt (revm-context journal/inner.rs lines 141-250). A HYPE delivery is an ordinary value call from 0x2222...2222, so recipient code runs. The value comes from that address's balance of 944.5 million HYPE, and its nonce of 1,090,288 rises with each delivery. Nothing reaches the PoolManager lock or a native settle (src/PoolManager.sol:104-114, 349-365) from another transaction."},
 {"leadId": "L-961", "outcome": "inconclusive", "answer": "The official endpoint still grants 29,979,000 gas and still differs on script 189 only. The b92ad36 build at rpc.hyperlend.finance grants about 200 million gas" + (f" and pmdiff2 there gives {pm(p2h, 300)}" if p2h else "") + ". The hl-node result above 30 million gas remains unseen."},
 {"leadId": "L-929", "outcome": "inconclusive", "answer": "The shared tools are outside this unit's write scope (only cycles/022 may be edited), so the rule was not added. Every call this unit made uses block tag latest with no past-block state read, and no override address falls in 0x0800-0x08ff, 0x2222..., 0x3333..., 0x20... or 0x5555... (tools/opdiff/pmdiff.py lines 21-22, pmdiff2.py lines 26-29, evm.py line 175)."},
 {"leadId": "L-920", "outcome": "inconclusive", "answer": "hl-node is not served (HTTP 403) and hl-visor is byte equal to the cycle 17 copy. Whether hl-node moved to revm 43 cannot be read. The b92ad36 build is now public at rpc.hyperlend.finance and passes the battery, the targeted set and the ruint vectors."},
 {"leadId": "L-824", "outcome": "cleared" if (t12 and t6) else "inconclusive", "answer": f"rpc.hyperlend.finance reports reth/v0.1.0-b92ad36. Battery {bt(bh)}, targeted {bt(th)}, ruint vectors " + (f"{r121r['ran']} ran with {r121r['mismatchCount']} mismatches" if r121r else 'not run') + f", step traces sets 1 and 2 {tr(t12)}, set 6 {tr(t6)}."},
 {"leadId": "L-068", "outcome": "cleared", "answer": "Pool-creator level only: a hook that reads a HyperCore precompile can block exits from its own pool. Pools without such a hook are unaffected. Recorded in one line under cleared."},
]

d = {"unit": "hyperevm", "_lenses": ["L1", "L2", "L3", "L4"], "profiles": profiles, "findings": findings, "cleared": cleared, "leads": leads, "leadResults": lr}
json.dump(d, open(os.path.join(W, '..', 'hyperevm.research.json'), 'w'), indent=1)
print('written')
