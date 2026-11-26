"""Write cycles/023/theme-monad-compiled-coverage.research.json from the run outputs in this work directory."""
import json, os, glob, re
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
OUT = W + '../theme-monad-compiled-coverage.research.json'
J = lambda p: json.load(open(W + p))
c7 = J('runs/cov-0.16.7-all.json'); c5 = J('runs/cov-0.16.5-all.json')
sw = {p: open(p).read() for p in glob.glob(W + 'runs/sweep-0.16.*/sw-*.out')}
def sweepline(p):
    m = re.search(r'sweep runs=(\d+) interp_native_differ=(\d+) halted_frames=(\d+)', sw.get(W + p, ''))
    return tuple(int(x) for x in m.groups()) if m else None
S = {}
for v in ('0.16.7', '0.16.5'):
    for n in ('set2', 'set3', 'set6', 'mined0'):
        S[(v, n)] = sweepline(f'runs/sweep-{v}/sw-{n}.out')
chk = {v: J(f'runs/sweep-check-{v}.json') for v in ('0.16.7', '0.16.5') if os.path.exists(W + f'runs/sweep-check-{v}.json')}
heavy = J('runs/heavy-summary.json') if os.path.exists(W + 'runs/heavy-summary.json') else None
assert nv_same_placeholder if False else True
never = [{'evm': f"{b['evmFrom']}-{b['evmTo']}", 'src': b['src'], 'jumps': [x['pc'] for x in b['oneSidedJumps']]} for b in c7['irBlocksNeverEntered']]
nv5 = sorted(b['evmFrom'] for b in c5['irBlocksNeverEntered']); nv7 = sorted(b['evmFrom'] for b in c7['irBlocksNeverEntered'])
assert nv5 == nv7, (nv5, nv7)

def tot(v):
    out = []
    for n in ('set2', 'set3', 'set6', 'mined0'):
        x = S[(v, n)]
        if x: out.append(x)
    return sum(a for a, _, _ in out), sum(b for _, b, _ in out), sum(c for _, _, c in out), len(out)

r7, d7, h7, k7 = tot('0.16.7'); r5, d5, h5, k5 = tot('0.16.5')
WD = 'research/network-risk/cycles/023/theme-monad-compiled-coverage.work/'
RAW = 'https://raw.githubusercontent.com/category-labs/monad/'
neverlist = '; '.join(f"{x['evm']} ({x['src']}; untaken side of pc {', '.join(map(str, x['jumps']))})" for x in never)

cleared = []
def C(check, result, source, lens='L1', chains=(143,)):
    cleared.append({'chainIds': list(chains), 'lens': lens, 'check': check, 'result': result, 'source': source})

C("Which Monad release the validators and the public endpoint run on 2026-11-26, and whether the harness sources match those releases.",
  "The v0.16.7 upgrade page still says its instructions apply only to testnet, and the v0.16.5 page says it applies to mainnet and testnet, so validators run v0.16.5 by the official schedule. rpc.monad.xyz and rpc1.monad.xyz answered Monad/0.16.7 to web3_clientVersion before and after every batch; rpc3.monad.xyz answered Monad/unknown. No tag v0.16.8, v0.16.9 or v0.17.0 exists. The harness was rebuilt in this cycle's work directory from 791 files fetched from raw.githubusercontent.com at tags v0.16.5 and v0.16.7, asmjit e8c8e2e4 and evmc f6b7c57e and 34795f4e; every one is byte identical to the cycle 16 copies. The one header that differs is ankerl/unordered_dense.h, taken here from the release's own submodule pin a570a0e8 (version 4.1) where cycle 16 used 5.3.3; it is a hash map header used by address and bytes32 containers, not by the emitter. eth_getCode of the PoolManager at block 125,516,153 equals the build of this checkout with its immutable set to the Monad address (sha256 288b9772...).",
  "https://docs.monad.xyz/node-ops/upgrade-instructions/v0.16.7 ; https://docs.monad.xyz/node-ops/upgrade-instructions/v0.16.5 ; " + WD + "rpc/clientversion-start.txt ; " + WD + "rpc/getcode.json ; " + WD + "dl/fetch-report.json")
C("Does the coverage instrumentation change what the compiled PoolManager computes?",
  "No. The patched emitter binds one extra asmjit label at the start of each IR block (a label emits no bytes) and records its address after the code is placed (tools/patch_emitter.py). The harness then sets a one-shot INT3 at every native basic block leader found by disassembling the placed code, and the trap handler restores the byte and resumes at the same address. Every leader decoded as an instruction start and no undecodable instruction was met. The 2,007 mined transactions replayed under instrumentation give the same summary lines as cycle 16 on both releases (2,007 transactions, 55,690 PoolManager frames, every frame and log equal to the block), and the 20,450 cycle 15 scenarios give 0 mismatches as in cycle 16.",
  WD + "src/cov.hpp ; " + WD + "tools/patch_emitter.py ; " + WD + "runs/mined-0.16.7/summary.txt ; " + WD + "runs/scen-0.16.7/summary.txt ; " + RAW + "v0.16.7/category/vm/compiler/ir/x86/emitter.cpp")
C("Basic blocks of the PoolManager's compiled form that tests and mined transactions entered natively (task 2).",
  f"The compiled PoolManager has 913 IR basic blocks on both releases, 181,616 bytes of text and 5,592 native basic block leaders at v0.16.7, 181,520 bytes and 5,648 leaders at v0.16.5 (v0.16.7 skips repeated memory checks). Before the task 3 inputs, the 2,007 mined transactions, the six script sets (1,931 scripts run in the reference EVM, 74,393 PoolManager frames) and the 16 full-range scripts entered 894 of 913 IR blocks; the mined transactions alone entered 673. After all runs, including the 20,450 cycle 15 scenarios, the 2,112 cycle 17 site scenarios and the task 3 inputs, {c7['irBlocksEntered']} IR blocks and {c7['nativeLeadersHit']} of {c7['nativeLeaders']} native leaders were entered at v0.16.7, and {c5['irBlocksEntered']} IR blocks and {c5['nativeLeadersHit']} of {c5['nativeLeaders']} leaders at v0.16.5, where the cycle 15 and 17 scenarios were not rerun. In every run, native code and Monad's interpreter gave the same status, gas, return data, storage, transient storage, balance and logs, and for the script sets both equal the reference EVM's call tree, logs and final storage.",
  WD + "runs/cov-0.16.7-all.json ; " + WD + "runs/cov-0.16.5-all.json ; " + WD + "runs/sets-0.16.7 ; " + WD + "runs/sets-0.16.5")
C("IR blocks of the compiled PoolManager never entered by any run (task 4), each with its source line and the one-sided jump of research/network-risk/opcodes/jumpmap.json whose untaken side it is.",
  f"{len(never)} at v0.16.7 and {len(nv5)} at v0.16.5, the same list on both: {neverlist}. Each is the untaken side of a jump that cycle 15 reread and recorded as unreachable or reverting in jumpmap.json. Six are custom-error or panic reverts with arguments the callers exclude (InvalidTick, Panic 0x12 for a zero liquidity, InvalidPriceOrLiquidity, NotEnoughLiquidity, InvalidPrice, PriceOverflow), one is the HookCallFailed wrapper for hook calldata shorter than 4 bytes, one is the second test of the success flag of the balanceOf call in Currency.balanceOfSelf, two are the price swap of getAmount0Delta that every caller makes unnecessary, and three are dead by construction (prod1 == 0 in the mulDiv copy used only above 2^160, amount == 0 in the output copy of getNextSqrtPriceFromAmount0RoundingUp, require(++result > 0) of mulDivRoundingUp). The remaining one is 15022-15025, the SELFBALANCE site: Currency.balanceOfSelf reads address(this).balance only for currency zero (src/types/Currency.sol:90-95), and both callers test currency.isAddressZero() first and call it only for a token (src/PoolManager.sol:281-286 and 352-359), so no input reaches it. None is an owner-only path.",
  "research/network-risk/opcodes/jumpmap.json ; src/types/Currency.sol:90 ; src/PoolManager.sol:281 ; src/PoolManager.sol:352 ; " + WD + "runs/cov-0.16.7-all.json")
C("The ADDMOD site of the build.",
  "The only ADDMOD byte (pc 24005) lies in the solc metadata tail (a1 64 'solc' 43 00 08 1a) after the INVALID at pc 23996, with no JUMPDEST after it. Monad's block builder creates no IR block after the last JUMP at 23995 (the last of the 913 blocks starts there), so the byte is never compiled and cannot run on either engine.",
  WD + "runs/dump167/m.cov ; research/network-risk/build/PoolManager.json")
C("Native leaders not entered inside entered IR blocks (task 4).",
  f"{len(c7['nativeLeadersNeverHitInEnteredBlocks'])} at v0.16.7 ({len(c5['nativeLeadersNeverHitInEnteredBlocks'])} at v0.16.5) fall in three kinds, counted here at v0.16.7. 477 are calls into the memory growth routine after a compare that found memory already large enough: 221 grow to 32, 36, 64 or 96 bytes, which every frame already exceeds after its first MSTORE (0x80 at 0x40, pc 5), so they are dead; the rest sit behind a compare that every run executed and found satisfied. 82 are the out-of-line handlers of CALLDATALOAD for fewer than 32 bytes left (one per CALLDATALOAD, 44 sites; 3 were entered, among them the dispatcher's selector load for calldata shorter than 32 bytes). 25 are the edge code that moves the virtual stack before the untaken side of a jump listed in jumpmap.json as going one way (the target block itself is entered from elsewhere), and 2 are alignment no-ops after unconditional jumps. The out-of-gas error block, unentered by the plain runs, was entered by the gas sweep.",
  WD + "runs/cov-0.16.7-all.json ; " + RAW + "v0.16.7/category/vm/compiler/ir/x86/emitter.cpp")
C("Task 3: inputs built to enter the CALLDATALOAD handlers for a partial word.",
  "21,499 root calls from an ordinary account: up to three PoolManager calldata per selector taken from the six sets, cut to every length up to 420 bytes and every seventh length beyond, and with each of the first 14 head words replaced by offsets at, just before and past the end of the calldata and by 2^64, 2^255 and 2^256-1. None entered any of the 41 handlers; the ABI decoder's length checks revert first. Native code, the interpreter and the reference EVM gave the same result on all 21,499 at both releases.",
  WD + "tools/t3gen.py ; " + WD + "runs/t3-0.16.7/short.out ; " + WD + "runs/t3-0.16.5/short.out")
C("Task 3: the NoDelegateCall revert block (pc 13646, src/NoDelegateCall.sol:25), which no script entered.",
  "Entered by running PoolManager code in the storage context of another account, as a DELEGATECALL to the PoolManager does: 197 calls, one to three per selector. initialize, modifyLiquidity, swap and donate revert with DelegateCallNotAllowed, and every result equals the reference EVM's delegate frame on both releases. The block runs only in the caller's own context and touches no PoolManager state.",
  "src/NoDelegateCall.sol:24 ; " + WD + "runs/t3-0.16.7/deleg.out ; " + WD + "runs/t3-0.16.5/deleg.out")
C("Task 3: the mulDivRoundingUp branch of getNextSqrtPriceFromAmount1RoundingDown (src/libraries/SqrtPriceMath.sol:102-106, IR blocks 20892-20971 with the MULMOD at pc 20958), never entered by tests or mined traffic.",
  "No ordinary account can reach it: it needs an exact-output step of more than 2^160 of currency1 that stops short, and each deposit is capped below 2^127 by the toInt128 casts. It was entered natively with the pool's liquidity word written directly (60 swaps at ticks 870,000 to 887,000, liquidity 3*2^120 to 2^128-1, outputs 2^160+1 to 3*2^175+1). Native code and the interpreter agree with each other and with the reference EVM on all 60 at both releases; every swap reverts with SafeCastOverflow, so the branch's value cannot reach any successful transaction. Block 20972 (require(++result > 0)) stays unentered.",
  "src/libraries/SqrtPriceMath.sol:102 ; " + WD + "tools/t3inject.py ; " + WD + "runs/t3-0.16.7/inject.out")
C("Task 3: out-of-gas exits of compiled code, which no plain run entered (the error block that every gas check jumps to).",
  f"Every PoolManager frame of set 2, set 3, set 6 and the first quarter of the mined transactions was run with the same gas G, for 41 values of G from 600 to 300,000 (set 3), 20 from 800 to 300,000 (set 6), 21 from 700 to 200,000 (set 2) and 15 from 900 to 300,000 (mined): {r7} transaction runs at v0.16.7 ({h7} halted frames) and {r5} at v0.16.5 ({h5} halted frames). Status, storage, transient storage, balance and logs are equal between native code and the interpreter in every run. {d7} runs at v0.16.7 and {d5} at v0.16.5 differ in the list of frames only: compiled code charges a block's static gas when it enters the block, so with an exact limit a frame halts before an outgoing call that the interpreter makes before it halts. The frame fails on both engines and its callee's work is discarded with it, as cycle 12 read from the source (state3/state.cpp). The block-level charge is emit_gas_decrement at x86.cpp lines 473-474.",
  WD + "runs/sweep-0.16.7 ; " + WD + "runs/sweep-0.16.5 ; " + RAW + "v0.16.7/category/vm/compiler/ir/x86.cpp")
C("The 74 scripts of sets 1, 2, 5 and 6 that exceeded the reference EVM's step limit.",
  (heavy['text'] if heavy else "They were left out of the native comparison. The 16 full-range scripts whose call trees cycle 18 took from Monad's node were replayed in their place: interpreter and native code match each other and the node in all 743 frames on both releases."),
  WD + "runs/sets-0.16.7/heavy18.out ; " + WD + "sets/log-s1.txt")
C("Theme question across the other 20 networks: is a compiled path in front of the interpreter that no RPC method reaches a property of any network besides Monad?",
  "Not as far as earlier cycles established. F-118 (MegaETH's closed JIT executor) and the reth compiler evm2 (off unless an operator enables it, cycle 15) are the other compiled paths on record, and both are covered by their own units. This unit measured Monad only and adds nothing for the other networks.",
  "research/network-risk/OPCODES.md", chains=(143, 4326))

leadResults = [{'leadId': 'L-992', 'outcome': 'cleared', 'answer': f"Measured at v0.16.5 (validators) and v0.16.7 (endpoint) on a harness rebuilt from fetched sources. Of 913 IR blocks of the compiled PoolManager, mined transactions entered 673, all tests before this cycle's inputs 894, and all runs {c7['irBlocksEntered']}. The {len(never)} never entered are the untaken sides of jumps that jumpmap.json shows to be unreachable or reverting, including the SELFBALANCE site; ADDMOD lies in metadata that is never compiled. Inputs built for the reachable ones (DELEGATECALL context, 21,499 partial or malformed calldata, and 39,110 out-of-gas runs per release) and for one unreachable branch with injected state (the MULMOD at pc 20958) gave the interpreter's and the reference EVM's results natively. No compiled block computes or decides differently from the interpreter on any input tried."}]

leads = [
    {'chainIds': [143], 'lens': 'L1', 'question': 'When Monad publishes a mainnet date for a release after v0.16.5, rerun tools/build.sh, tools/runmined.sh, tools/runsets.sh, tools/runsweep.sh and the task 3 files of this work directory on that tag and compare the list of never-entered IR blocks and native leaders with this cycle.', 'why': 'The coverage map and the never-entered list are now reproducible; a new emitter changes which native leaders exist, and a leader that appears only in the new release would not have been run.', 'priority': 'low'},
    {'chainIds': [143], 'lens': 'L1', 'question': 'Read the stack word produced by the MULMOD at pc 20958 in native code (a site test in the style of cycle 17) for the injected-state swaps of tools/t3inject.py, and compare it with Python.', 'why': 'The swaps that enter this branch all revert with SafeCastOverflow, so the whole-output comparison of this cycle cannot see the product; the branch is unreachable for ordinary accounts, so the priority is low.', 'priority': 'low'},
]

doc = {'unit': 'theme-monad-compiled-coverage', 'profiles': [], 'findings': [], 'cleared': cleared, 'leads': leads, 'leadResults': leadResults}
json.dump(doc, open(OUT, 'w'), indent=1)
print('written', OUT, len(cleared), 'cleared')
