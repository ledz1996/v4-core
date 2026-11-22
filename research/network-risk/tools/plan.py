"""Pick the work for the next cycle, write cycles/NNN/plan.json, and print the compact workflow args as JSON.

Usage: plan.py <YYYY-MM-DD> [--max-units N | --all] [--angles 0,1,2] [--readings N]
The queue never runs dry: cells start at depth 0, every cycle adds leads, verified cells
go stale after STALE cycles, and the angle and focus lens rotate so a revisit asks new questions.
"""
import json, os, sys
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STALE = 6
ANGLES = [
    "Sweep. List every precompile, predeploy, system contract, face of the native asset, wrapped native token, bridge, staking and fee contract on this network. For each one, run eth_call with \"from\" set to the PoolManager address for the call shapes P1, P2, P3 and P5 in ASSUMPTIONS.md (empty calldata with zero value, transfer(address,uint256) with zero and nonzero amount, balanceOf(PoolManager), and each IHooks selector), and record what comes back. Follow up on every target that does not revert.",
    "Opcode differential. For each opcode and call pattern the PoolManager relies on (TSTORE and TLOAD including rollback on revert and clearing at transaction end, CALL with value, CALLVALUE, SELFBALANCE, STATICCALL, RETURNDATASIZE and RETURNDATACOPY, MCOPY, PUSH0, gas forwarding, calls to addresses without code, precompile dispatch), read this network's execution client source and find where it departs from Ethereum's behaviour.",
    "Faces. Find every way one balance at the PoolManager can be reached under two currency ids or in two units on this network (native asset with an ERC-20 face, wrapped native predeploys, bridged and canonical versions sharing storage, tokens with more than one entry point), and walk sync, settle, take, mint and burn across the two faces in every order.",
    "Known weaknesses. Collect security advisories, audit reports, bug bounty write-ups, incident post-mortems and open issues for this network's execution client, precompiles and system contracts from the last two years, including behaviour the network calls by design. For each, decide whether an ordinary account could use it against funds in the PoolManager.",
    "Transaction types. For every transaction type and execution context this network adds (batches, sponsored or fee-token transactions, deposits, retryables, system calls, account abstraction, delegated accounts), work out what msg.sender, msg.value and transient storage look like inside the PoolManager and walk unlock, sync, settle and take through each.",
    "Upcoming forks. Assume every network upgrade scheduled or proposed for the next six months ships. What changes for the PoolManager and for funds already inside it, and what could an ordinary account do the day after?",
    "Pooled assets. Read the PoolManager's largest token balances on this network from chain. For each token, check transfer and balanceOf for behaviour any holder can trigger: rebasing, fees, callbacks, share accounting, special recipients, special amounts.",
    "Exits. Can an ordinary account make another user's swap or liquidity removal impossible to include or always revert on this network (gas caps, storage pricing, per-transaction limits, tick crossing cost, special recipients)?",
]
def main():
    date = sys.argv[1]
    max_units = int(sys.argv[sys.argv.index("--max-units") + 1]) if "--max-units" in sys.argv else 4
    if "--all" in sys.argv: max_units = 99
    forced = [int(x) for x in sys.argv[sys.argv.index("--angles") + 1].split(",")] if "--angles" in sys.argv else None
    L = json.load(open(f"{R}/state/ledger.json")); F = json.load(open(f"{R}/state/findings.json"))["findings"]
    cycle = L["cycle"] + 1
    lenses = sorted(L["lenses"])
    units = []
    for uid, u in L["units"].items():
        cells = [L["cells"][f"{c}:{l}"] for c in u["chainIds"] for l in lenses]
        fresh = sum(1 for c in cells if c["depth"] == 0)
        open_leads = [l for l in L["leads"] if l["status"] == "open" and set(l["chainIds"]) & set(u["chainIds"])]
        unsettled = [f for f in F if f["status"] in ("plausible", "unverified") and set(f["chainIds"]) & set(u["chainIds"])]
        live = [f for f in F if f["status"] == "confirmed" and set(f["chainIds"]) & set(u["chainIds"])]
        age = cycle - max(c["lastCycle"] for c in cells)
        thin = sum(1 for c in cells if c["depth"] == 1)
        # leads raised from cycle 2 on were written under the unprivileged threat model and count in full
        score = (100 * fresh + 6 * sum(1 for l in open_leads if l["priority"] == "high" and l["cycle"] >= 2) + sum(2 if l["cycle"] >= 2 else 0.25 for l in open_leads)
                 + 5 * len(unsettled) + thin + 3 * max(0, age - 1) + (20 if age >= STALE else 0)
                 + 2 * sum(1 for f in live if cycle - f.get("lastVerifiedCycle", 0) >= STALE))
        mode = "baseline" if fresh else "deepen"
        units.append({"score": score, "id": uid, "title": u["title"], "chainIds": u["chainIds"], "mode": mode,
                      "leadIds": [l["id"] for l in sorted(open_leads, key=lambda l: (l["cycle"] < 2, {"high": 0, "medium": 1, "low": 2}[l["priority"]]))][:8],
                      "recheckIds": [f["id"] for f in unsettled][:6]})
    units.sort(key=lambda u: -u["score"])
    baseline = [u for u in units if u["mode"] == "baseline"]
    chosen = baseline if baseline else units[:max_units]
    for i, u in enumerate(chosen):
        if u["mode"] == "baseline":
            u["lenses"] = lenses; u["angles"] = [ANGLES[0]]
        else:
            u["lenses"] = ["L1", "L2", "L3", "L4"]
            u["angles"] = [ANGLES[k] for k in (forced or [(cycle + 3 * i) % len(ANGLES), (cycle + 3 * i + 4) % len(ANGLES)])]
        u.pop("score")
    # the source itself is re-read every cycle, two readings at a time, each from a different direction
    READINGS = [
        ("files-accounting", "Read line by line: src/PoolManager.sol, src/ProtocolFees.sol, src/types/Currency.sol, src/libraries/CurrencyReserves.sol, CurrencyDelta.sol, NonzeroDeltaCount.sol, Lock.sol, Hooks.sol, src/ERC6909.sol, src/ERC6909Claims.sol, src/Extsload.sol, src/Exttload.sol, src/NoDelegateCall.sol, src/libraries/CustomRevert.sol, ParseBytes.sol, src/types/BalanceDelta.sol, BeforeSwapDelta.sol, and lib/solmate/src/auth/Owned.sol."),
        ("files-math", "Read line by line: src/libraries/Pool.sol, Position.sol, SwapMath.sol, SqrtPriceMath.sol, TickMath.sol, TickBitmap.sol, FullMath.sol, SafeCast.sol, LiquidityMath.sol, UnsafeMath.sol, BitMath.sol, LPFeeLibrary.sol, ProtocolFeeLibrary.sol, src/types/Slot0.sol, PoolKey.sol, PoolId.sol, src/libraries/StateLibrary.sol, TransientStateLibrary.sol."),
        ("flow-swap", "Trace one swap from PoolManager.swap to the last delta written: beforeSwap and its returned delta and fee override, Pool.swap step by step (fee split between protocol and LPs, rounding of every amount, tick crossing, liquidity net, price limit), afterSwap and its returned delta, and the two _accountDelta calls. Do it for exact input and exact output, both directions, with and without a hook, with dynamic fee, and at the extremes of tick, price, liquidity and amount. At each step ask who gains if the number is off by one unit, one sign or one cast."),
        ("flow-liquidity", "Trace modifyLiquidity and donate from entry to the last delta written: tick updates, bitmap flips, fee growth inside, Position.update, fees owed, the caller delta and the hook delta from afterAddLiquidity and afterRemoveLiquidity, salt handling, and tick clearing. Cover add, remove, zero delta, full range, single tick spacing, ranges above, below and around the current tick, and repeated adds and removes by different owners on shared ticks. At each step ask whether one owner can withdraw another owner's principal or fees, or leave a tick or position that can no longer be updated."),
        ("tests-replay-core", "The repository's own tests, NatSpec comments and test doubles are the only permitted reference for what the source is meant to do. Replay by reading or by Python transcription every concrete expectation in test/PoolManager.t.sol, test/PoolManager.swap.t.sol, test/PoolManager.clear.t.sol, test/PoolManagerInitialize.t.sol, test/ModifyLiquidity.t.sol, test/Sync.t.sol, test/CustomAccounting.t.sol, test/ERC6909Claims.t.sol, test/NoDelegateCall.t.sol, test/DynamicFees.t.sol, test/DynamicReturnFees.t.sol, test/SkipCallsTestHook.t.sol, test/Extsload.t.sol, test/ProtocolFeesImplementation.t.sol and test/types/Currency.t.sol against the source in src/, including every expectRevert selector and every asserted number. Compare each NatSpec comment in src/interfaces/ with what the implementation does. Read the helper contracts in src/test/ and test/utils/ for behaviour the production code is expected to have. Every place where the source cannot produce what a test or comment states is a candidate: decide whether it gives an ordinary account a way to take or lock funds."),
        ("tests-replay-libraries", "The repository's own tests are the only permitted reference for what the libraries are meant to compute. Replay by Python transcription every concrete vector and boundary in test/libraries/ (TickMath, SqrtPriceMath, SwapMath, FullMath, BitMath, UnsafeMath, TickBitmap, Position, SafeCast, LiquidityMath, LPFeeLibrary, ProtocolFeeLibrary, Hooks, Lock, StateLibrary, Pool, and the rest), test/Tick.t.sol and test/types/, against the source in src/libraries/ and src/types/. Use the gas snapshot files in snapshots/ as a second witness: a snapshot that the source could not plausibly produce marks a changed code path. Every vector, revert or boundary the source cannot reproduce is a candidate: decide whether it gives an ordinary account a way to take or lock funds."),
        ("invariants-settlement", "Write down the invariants of flash accounting and custody as the code implies them (for example: for every currency the PoolManager balance is at least pool reserves plus ERC-6909 supply plus accrued protocol fees; deltas sum to zero when unlock returns; a credit exists only after a matching balance increase or msg.value). Then try to break each with sequences of unlock, sync, settle, settleFor, take, clear, mint, burn, the ERC-6909 transfer functions, initialize, swap, modifyLiquidity and donate, issued by one or two ordinary accounts, including re-entry through unlockCallback, hooks, token callbacks and native transfer recipients, and including the same account acting through settleFor and operators."),
        ("invariants-bits", "Check every place where the code packs, masks, shifts or casts: Slot0 packing, BalanceDelta and BeforeSwapDelta packing and unpacking, fee and protocol fee fields, hook flag bits and the flag validity rules, tick bitmap word and bit positions, ERC-6909 id to currency conversion, transient slot constants and the hash used for delta slots, assembly memory use and cleanup, and every unchecked block. Recompute constants with python3. For each, ask whether a dirty upper bit, an overlap or a wrong width lets an ordinary account change a value it should not control."),
    ]
    n_read = int(sys.argv[sys.argv.index("--readings") + 1]) if "--readings" in sys.argv else 2
    picks = [READINGS[(2 * (cycle - 1) + j) % len(READINGS)] for j in range(n_read)]
    code = [{"id": f"core-code-{k}", "task": t} for k, t in picks]
    # themes are cross-network questions queued by hand in state/themes.json; up to three open ones run per cycle
    tp = f"{R}/state/themes.json"
    if os.path.exists(tp):
        code += [{"id": t["id"], "task": t["task"]} for t in json.load(open(tp))["themes"] if t["status"] == "open"][:3]
    plan = {"cycle": cycle, "date": date, "dir": f"research/network-risk/cycles/{cycle:03d}", "units": chosen, "code": code}
    # the full plan (with the long angle and task texts) goes to disk for the agents; the workflow gets a compact copy
    os.makedirs(f"{R}/cycles/{cycle:03d}", exist_ok=True)
    json.dump(plan, open(f"{R}/cycles/{cycle:03d}/plan.json", "w"), indent=1)
    compact = dict(plan, units=[{k: u[k] for k in ("id", "title", "chainIds", "lenses", "leadIds", "recheckIds")} for u in chosen], code=[{"id": c["id"]} for c in code])
    print(json.dumps(compact))
main()
