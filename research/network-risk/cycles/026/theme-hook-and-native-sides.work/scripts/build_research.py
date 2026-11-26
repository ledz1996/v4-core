"""Write cycles/026/theme-hook-and-native-sides.research.json from the outputs in out/. Usage: python3 build_research.py"""
import os, json
HERE = os.path.dirname(os.path.abspath(__file__)); WORK = os.path.dirname(HERE); OUT = os.path.join(WORK, 'out')
NR = os.path.abspath(os.path.join(WORK, '..', '..', '..'))
nets = json.load(open(os.path.join(NR, 'state', 'networks.json')))['networks']
ALL = [n['chainId'] for n in nets]
cmp = json.load(open(os.path.join(OUT, 'compare.json')))
single = json.load(open(os.path.join(OUT, 'single-classified.json')))
cov = json.load(open(os.path.join(OUT, 'coverage.json')))
t4 = {}
for n in nets:
    p = os.path.join(OUT, 'task4', f'chain-{n["chainId"]}.json')
    if os.path.exists(p): t4[n['chainId']] = json.load(open(p))
t4ref = json.load(open(os.path.join(OUT, 'task4-ref-1.json')))
W = 'research/network-risk/cycles/026/theme-hook-and-native-sides.work'
tp = json.load(open(os.path.join(OUT, 'tempo-value-probe.json')))
TEMPO_NOTE = ("With balance overrides the Tempo endpoint moves value inside eth_call, and all native settle cases return the reference words. "
              "Without an override, SELFBALANCE of a contract, BALANCE of 0xb0b and a value CALL of 1 give " + str(tp['no balance override']['selfbalance, call ok, balance(0xb0b)'])
              + " while eth_getBalance answers " + tp['eth_getBalance(0xb0b)'] + " (" + tp['client'] + ", block " + str(int(tp['block'], 16)) + "). "
              "No account holds native value in the EVM, so on the live chain settle credits msg.value 0 and every native take of a nonzero amount fails, "
              "which is the cleared Tempo answer of earlier cycles. The hook cases that failed in Tempo batches at 30 million gas return the reference words when run alone at 50 million.")

def summ(cid):
    s = next(x for x in cmp['summary'] if x['chainId'] == cid)
    rows = single.get(str(cid), [])
    still = [r for r in rows if not r['sameAsReferenceAlone']]
    return s, rows, still

per = []
for n in nets:
    cid = n['chainId']; s, rows, still = summ(cid)
    tags = sorted({r['tag'].replace('N7 native take 1 to ', '').replace('N7 native take 0 to ', '') for r in still})
    per.append(f"{n['name']} ({cid}): {s['cases']} cases, {s['diffVsReference']} differ from the batched reference, "
               f"{len(rows) - len(still)} of those equal the reference when run alone, {len(still)} still differ, all native takes to: "
               f"{', '.join(tags) if tags else 'none'}; client {', '.join(c for c in s['clients'] if not c.startswith('error'))}")

rules = {cid: (v['checked'], len(v['violations'])) for cid, v in t4.items()}
targets = cov['targets']

cleared = [
 {"chainIds": ALL, "lens": "L1",
  "check": "Task 1 and 3: 575 cases through one eth_call each batch at the real PoolManager address of all 21 networks, with this checkout's build placed there by state override, a hook double at addresses whose low 14 bits carry the flags under test, token doubles and a native balance override. Hook functions with correct and wrong selectors, returns of 0 to 128 bytes, reverts with 0 to 2,000 bytes, INVALID in the hook, beforeSwap specified deltas that zero, flip or leave 1 of the amount, int128 bounds, dynamic fee words with and without the override bit, above 1,000,000 and with dirty upper bits, afterSwap, afterAddLiquidity and afterRemoveLiquidity deltas at the int128 bounds and with the return-delta bit off, hooks calling swap, modifyLiquidity, donate, sync, take, settle, mint, burn, clear and unlock from inside every hook function, and the address validation of Hooks.sol:109-127.",
  "result": "Every hook case (groups A to I, 431 cases) returns on every network the words of the reference EVM run of the same batch, apart from cases that ran short of gas in a batch of 8 and equal the reference when run alone (Monad 3, Polygon 3, Tempo 22 at 50 million gas). No network differs from Ethereum on any hook path. " + " | ".join(per),
  "source": f"{W}/out/compare.json and {W}/out/single-classified.json (eth_call results), src/libraries/Hooks.sol:131-168, src/libraries/Hooks.sol:248-315"},
 {"chainIds": ALL, "lens": "L1",
  "check": "The four branch sides that cycle 25 left out: hook delta accounted at src/PoolManager.sol:181, amount to swap of zero at src/libraries/Pool.sol:320, NonzeroNativeValue at src/PoolManager.sol:356 and a failed native payout at src/types/Currency.sol:51 (lead L-1103).",
  "result": f"All four now run on all 21 networks: pc 6230 taken {targets['6230:1']['count']} times (first case: {targets['6230:1']['firstCase']}), pc 18977 taken {targets['18977:1']['count']} times ({targets['18977:1']['firstCase']}), pc 13447 taken {targets['13447:1']['count']} times ({targets['13447:1']['firstCase']}), pc 12839 taken {targets['12839:1']['count']} times ({targets['12839:1']['firstCase']}). The words agree with the reference on every network. Over the build, cycle 26 cases execute {cov['executedHere']} of the 774 sides and add {len(cov['newVsCycle25'])} sides that no cycle 25 case ran; {len(cov['notRunByCycle25or26'])} sides are run by neither cycle's cases, of which {len(cov['scriptSetGapStillNotRun'])} are also among the 52 sides that script sets 1 to 6 never ran (listed in out/coverage.json; compiler-generated decode and panic checks at PoolManager.sol:80, the two redundant success tests at PoolManager.sol:110 and Currency.sol:94, the native branch of balanceOfSelf at Currency.sol:91, and the math sides that jumpmap.json marks unreachable by construction).",
  "source": f"{W}/out/coverage.json, src/PoolManager.sol:181, src/libraries/Pool.sol:320, src/PoolManager.sol:356, src/types/Currency.sol:51"},
 {"chainIds": ALL, "lens": "L1",
  "check": "Task 4: rules that do not come from src/, applied to every case on every network and to the reference: R1 per currency, the PoolManager's balance rise equals what the driver, the hook and S paid less what they took (token doubles), and native value moves only among them except a take to an outside recipient, which removes exactly the amount; R2 driver delta plus hook delta equals the driver delta of the zero-delta baseline with the same actions; R3 a successful unlock ends with count 0 and the count equals the number of nonzero actor deltas; R4 a failed call leaves the count and slot0 unchanged; R5 the PoolManager holds at least the principal of the remaining position (exact fractions).",
  "result": "No violation on any network or in the reference: " + "; ".join(f"{cid}: {c} checks, {v} violations" for cid, (c, v) in sorted(rules.items())) + f". The checker fails when it should: one-unit plants in a copy of the reference results give 90 R1 violations for a PoolManager balance one unit short, 188 (R1, R2, R3) for a hook delta one unit high, and 92 (R3, R4) for a count one too high. The 14 cases whose hook delta is 2^127 or more in size cannot be settled by the driver in one settle (paid.toInt128 at src/PoolManager.sol:364 and the token double's balance), and the PoolManager refuses to close their unlock with CurrencyNotSettled on every network, so no funds move.",
  "source": f"{W}/out/task4/, {W}/out/task4-ref-1.json, {W}/out/plant/plant-summary.json, src/PoolManager.sol:104-114, src/PoolManager.sol:364"},
 {"chainIds": ALL, "lens": "L1",
  "check": "ParseBytes.parseSelector (src/libraries/ParseBytes.sol:9-14) and parseFee (16-21) load a full word into a bytes4 and a uint24 without masking. Does a hook answer with nonzero bytes after the selector, a caller whose address has nonzero upper bytes (so the first calldata word carries them), or a fee word with bits above 24 change the outcome?",
  "result": "No. In the reference EVM with the driver at an address whose upper 16 bytes are nonzero and hooks that pad the selector with 0xff bytes, all ten hook functions are accepted exactly as with zero padding (out/dirtysel.json), so the compiled comparison at Hooks.sol:152 cleans both sides to 4 bytes. Fee words 2^255 | 0x400000 | 500 and 2^24 | 0x400000 | 500 behave as 0x400000 | 500, and 2^24 | 500 as no override, on all 21 networks, because isOverride and removeOverrideFlag mask (src/libraries/LPFeeLibrary.sol:128-145). Only the hook of the pool can choose these words.",
  "source": f"{W}/out/dirtysel.json, src/libraries/ParseBytes.sol:9-21, src/libraries/Hooks.sol:152, src/libraries/LPFeeLibrary.sol:128-145"},
 {"chainIds": ALL, "lens": "L1",
  "check": "Task 2: native value. settle with value in a native pool, settle and settleFor with value while an ERC-20 is synced, sync of native after an ERC-20 sync, settle with zero value, settleFor S, overpayment, a take above the PoolManager's balance and at 2^127, native claims, and native takes of 1 and 0 to 62 recipients (an account without code, a contract that reverts, address zero, the PoolManager itself, precompiles 0x01 to 0x11 and 0x100, and OP Stack, Arbitrum, HyperEVM, Celo, Polygon, BNB Chain, Monad, Avalanche, Arc and Tempo system addresses, EntryPoints, EIP-4788, 2935, 7002 and 7251 contracts and Permit2), on every network.",
  "result": "Every native settle case returns the reference words on every network. settle or settleFor with value while an ERC-20 is synced reverts with NonzeroNativeValue and the value stays with the caller. A take above the PoolManager's balance or at 2^127 reverts. A take to a recipient that rejects value reverts with WrappedError(NativeTransferFailed), so the debit is undone. Where a recipient has code on one network and not on another the outcome differs (listed per network in the first cleared item), and every such difference changes only whether the caller's own payout goes through or lands at that address. A take to the PoolManager itself reverts everywhere, because the contract has no receive or fallback function. No take or settle credited anyone other than the caller or the named recipient.",
  "source": f"{W}/out/compare.json, {W}/out/single-classified.json, src/PoolManager.sol:291-307, src/PoolManager.sol:349-365, src/types/Currency.sol:44-53"},
 {"chainIds": [43114, 999, 137], "lens": "L2",
  "check": "Which precompile addresses answer a value call with empty input differently from Ethereum (Prague and Osaka rules: 0x09 to 0x11 fail on empty input, EIP-2537 says an error burns all gas supplied).",
  "result": "On Avalanche and HyperEVM the addresses 0x0b to 0x11 and 0x100 accept the payout, so they hold no BLS12-381 or P-256 precompile at the endpoint's fork, and a native take there leaves the caller's own value at that address. On the Polygon endpoint (drpc gateway) 0x0a accepts the payout. On every other network these addresses fail as on Ethereum. The PoolManager neither calls precompiles itself nor reads their answers apart from the success flag of a payout the caller chose.",
  "source": "https://eips.ethereum.org/EIPS/eip-2537 and eth_call results in " + W + "/out/single/chain-43114.json, chain-999.json, chain-137.json"},
 {"chainIds": [42220, 5042, 137], "lens": "L3",
  "check": "Native asset with an ERC-20 face (CELO token on Celo, USDC 0x3600..00 on Arc, 0x1010 on Polygon): sync of the face then settle with value, sync of the face then a native take then settle, a native settle before a face sync, and how the face balance follows a native payment.",
  "result": "On all three, sync(face) then settle with value reverts with NonzeroNativeValue (0xb0ec849e); sync(face), a native take of 5 and settle() reverts with Panic 0x11 at the checked subtraction of src/PoolManager.sol:360; a native settle of 7 followed by sync(face) and settle() credits 7 native and 0 face. The face balance of the PoolManager follows the native balance one to one on Celo and Polygon, and on Arc in 6 decimal units (10^27 wei shows as 10^15, and 10^12 wei more as one unit more). The face and native currency ids keep separate deltas, so a payment in one face is never credited in the other. This repeats with the hook driver what F-023, F-032, F-050 and F-008 record.",
  "source": f"{W}/out/faces-42220.json, faces-5042.json, faces-137.json (eth_call results), src/PoolManager.sol:279-288, src/PoolManager.sol:349-365"},
 {"chainIds": [5042], "lens": "L2",
  "check": "Native take to address zero on Arc.",
  "result": "It reverts with WrappedError(NativeTransferFailed) on Arc and succeeds on the other networks, as F-125 records for Arc's value-transfer frame hook. Only the caller's own payout is refused.",
  "source": f"{W}/out/single/chain-5042.json"},
 {"chainIds": [143], "lens": "L1",
  "check": "Monad compiled path: the 575 cases through the cycle 23 harness, interpreter against native x86 code, at v0.16.5 and v0.16.7, one world per case.",
  "result": "562 of 575 cases (v0.16.7) and 561 (v0.16.5) give the same result in both engines and, apart from harness modelling of balances and precompiles, the reference words. All 143 native value cases agree between engines once the harness balance lines are written as 64 hex digits (the first run wrote odd-length hex, which the harness misreads). 13 hook cases differ: the native side reverts the whole unlock with empty data in 12 and the interpreter side in 1. The same PoolManager call sent alone (initialize with an afterInitialize hook that returns 1 to 31 bytes) gives InvalidHookResponse in both engines, a rebuild of the harness that only records each call's result after it returns makes 10 of the 13 agree and leaves 3 others different, and zeroing or filling the native stack changes nothing. A result that moves with host-side bookkeeping points at the harness's host process, not at Monad's EVM semantics. The root cause was not found; it is a lead.",
  "source": f"{W}/out/hx-results.json, {W}/out/hx/bisect, {W}/out/hx/bisect2, {W}/out/hx/trace, {W}/out/hx/notrace, {W}/out/hx/native2, {W}/build/hxtrace/harness_trace.cpp"},
]
for n in nets:
    if n['chainId'] == 4217:
        cleared.append({"chainIds": [4217], "lens": "L2", "check": "Tempo native value cases.",
                        "result": TEMPO_NOTE, "source": f"{W}/out/chain-4217.json, {W}/out/single-classified.json"})

leads = [
 {"chainIds": [143], "lens": "L1", "question": "In the cycle 23 Monad harness, which host-side state makes 13 hook-failure cases of out/hx/rep/diffcases.json revert the whole unlock in one engine only, given that a call-recording rebuild changes which cases differ (13 to 3) and zeroing the native stack does not?",
  "why": "If the cause is in Monad's runtime rather than the harness host (for example a read of memory the runtime did not initialise), the result of a compiled PoolManager frame could depend on process history on the validators. Running build/hxtrace/hx under AddressSanitizer or valgrind would settle it.", "priority": "medium"},
 {"chainIds": [43114, 999], "lens": "L2", "question": "Do Avalanche and HyperEVM plan to add the EIP-2537 and P-256 precompiles at 0x0b to 0x11 and 0x100, and at which fork, so that a payout to those addresses changes from accepted to failing?",
  "why": "Integrations that pay out to arbitrary addresses would see a behaviour change; no pool funds are at stake.", "priority": "low"},
]
lr = [{"leadId": "L-1103", "outcome": "cleared",
       "answer": "The four sides run on all 21 networks through the extended driver with a hook double and native balance overrides, and every network returns the reference words (Pool.sol:320, PoolManager.sol:181, PoolManager.sol:356, Currency.sol:51). No rule of Task 4 is broken."}]
doc = {"unit": "theme-hook-and-native-sides", "profiles": [], "findings": [], "cleared": cleared, "leads": leads, "leadResults": lr}
json.dump(doc, open(os.path.join(NR, 'cycles', '026', 'theme-hook-and-native-sides.research.json'), 'w'), indent=1)
print('written', len(cleared), 'cleared')
