"""Pick the work for the next cycle and print the workflow args as JSON.

Usage: plan.py <YYYY-MM-DD> [--max-units N]
The queue never runs dry: cells start at depth 0, every cycle adds leads, verified cells
go stale after STALE cycles, and the angle and focus lens rotate so a revisit asks new questions.
"""
import json, os, sys
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STALE = 6
ANGLES = [
    "Assume an unprivileged attacker who can deploy any token, hook and contract on this network and wants pool funds.",
    "Assume the issuer or admin of a token that pools hold uses every control the chain gives them (freeze, blocklist, seize, pause, upgrade, policy change).",
    "Assume the sequencer, block builder or validator set is hostile: ordering, censorship, forced inclusion, reorgs, privileged transaction types.",
    "Assume a scheduled or proposed network upgrade ships in the next six months. What changes for the PoolManager and for funds already inside it?",
    "Assume a hook author who uses features only this network has (precompiles, system contracts, non-EVM contracts, account delegation).",
    "Follow the money across the boundary: bridges, canonical token contracts, gas-token wrappers, system addresses. Where can a balance the PoolManager relies on change without a transfer the PoolManager sees?",
    "Read the client or node source for this network's execution layer where the docs are vague. Check transient storage clearing, value transfers and precompile dispatch in code.",
    "Look at the transaction types this network adds (batches, sponsored or fee-token transactions, deposits, system calls) and walk each through unlock, sync, settle and take.",
]
def main():
    date = sys.argv[1]
    max_units = int(sys.argv[sys.argv.index("--max-units") + 1]) if "--max-units" in sys.argv else 4
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
        score = (100 * fresh + 6 * sum(1 for l in open_leads if l["priority"] == "high") + 2 * len(open_leads)
                 + 5 * len(unsettled) + thin + 3 * max(0, age - 1) + (20 if age >= STALE else 0)
                 + 2 * sum(1 for f in live if cycle - f.get("lastVerifiedCycle", 0) >= STALE))
        mode = "baseline" if fresh else "deepen"
        units.append({"score": score, "id": uid, "title": u["title"], "chainIds": u["chainIds"], "mode": mode,
                      "leadIds": [l["id"] for l in sorted(open_leads, key=lambda l: {"high": 0, "medium": 1, "low": 2}[l["priority"]])][:8],
                      "recheckIds": [f["id"] for f in unsettled][:6]})
    units.sort(key=lambda u: -u["score"])
    baseline = [u for u in units if u["mode"] == "baseline"]
    chosen = baseline if baseline else units[:max_units]
    for i, u in enumerate(chosen):
        if u["mode"] == "baseline":
            u["lenses"] = lenses; u["angle"] = ANGLES[0]
        else:
            k = (cycle + i) % len(lenses)
            u["lenses"] = [lenses[k], lenses[(k + 3) % len(lenses)]]
            u["angle"] = ANGLES[(cycle + 3 * i) % len(ANGLES)]
        u.pop("score")
    # the source itself is re-read every cycle: two readers in cycle 1, then one reader rotating through the file groups
    groups = [
        ("accounting", "src/PoolManager.sol, src/ProtocolFees.sol, src/types/Currency.sol, src/libraries/CurrencyReserves.sol, src/libraries/CurrencyDelta.sol, src/libraries/NonzeroDeltaCount.sol, src/libraries/Lock.sol, src/libraries/Hooks.sol, src/ERC6909.sol, src/ERC6909Claims.sol, src/Extsload.sol, src/Exttload.sol, src/NoDelegateCall.sol, src/libraries/CustomRevert.sol, src/libraries/ParseBytes.sol, src/types/BalanceDelta.sol, src/types/BeforeSwapDelta.sol, and the lib/ contracts they import"),
        ("math", "src/libraries/Pool.sol, src/libraries/Position.sol, src/libraries/SwapMath.sol, src/libraries/SqrtPriceMath.sol, src/libraries/TickMath.sol, src/libraries/TickBitmap.sol, src/libraries/FullMath.sol, src/libraries/SafeCast.sol, src/libraries/LiquidityMath.sol, src/libraries/UnsafeMath.sol, src/libraries/BitMath.sol, src/libraries/LPFeeLibrary.sol, src/libraries/ProtocolFeeLibrary.sol, src/types/Slot0.sol, src/types/PoolKey.sol, src/types/PoolId.sol, src/libraries/StateLibrary.sol, src/libraries/TransientStateLibrary.sol"),
    ]
    code = [{"id": f"core-code-{g[0]}", "files": g[1]} for g in (groups if cycle == 1 else [groups[cycle % len(groups)]])]
    print(json.dumps({"cycle": cycle, "date": date, "dir": f"research/network-risk/cycles/{cycle:03d}", "units": chosen, "code": code}, indent=1))
main()
