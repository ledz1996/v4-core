"""Writes cycles/030/theme-nitro-binary-arith-lift.research.json from the raw results of this work directory."""
import json, os
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = W + '/out/'
OUT = os.path.join(os.path.dirname(W), 'theme-nitro-binary-arith-lift.research.json')
WD = 'research/network-risk/cycles/030/theme-nitro-binary-arith-lift.work/'
S = json.load(open(R + 'summary.json'))
sym = {a: json.load(open(R + 'sym/symcmp-%s.json' % a)) for a in ('amd64', 'arm64')}
jd = {(a, f): json.load(open(R + 'jd/%s-%s.json' % (a, f))) for a in ('amd64', 'arm64') for f in ('none', 'opcode', 'bit')}
fl = {(a, f): json.load(open(R + 'faults/%s-%s.json' % (a, f))) for a in ('amd64', 'arm64') for f in ('carry', 'limb', 'shift')}
ch = json.load(open(R + 'chain/chain.json'))
cov = {a: json.load(open(R + 'coverage-%s.json' % a)) for a in ('amd64', 'arm64')}
ARB = [42161, 4663]


def n(x): return f'{x:,}'


tot = {a: S[a]['cases'] for a in S}
mis = sum(S[a]['mismatches'] for a in S); err = sum(S[a]['errors'] for a in S)
rnd = {a: S[a]['randomByOp'] for a in S}
minrand = min(v[0] for a in rnd for v in rnd[a].values())
sets = ', '.join(f"{k} {n(S['amd64']['bySet'][k][0])}" for k in ('battery', 'targeted', 'c27', 'v4shapes', 'random', 'direct'))
chain_lines = []
for r in ch['results']:
    vers = sorted({p['clientVersionBefore'] for p in r['passes']} | {p['clientVersionAfter'] for p in r['passes']})
    chain_lines.append(f"chain {r['chainId']}: {len(r['passes'])} passes of {n(r['passes'][0]['ran'])} vectors, "
                       f"{sum(len(p['mismatches']) for p in r['passes'])} mismatches, {sum(len(p['errors']) for p in r['passes'])} errors, "
                       f"client versions {'; '.join(vers)}")
pm = jd[('amd64', 'none')]['poolmanager']
fault_txt = '; '.join(f"{a} {f}: {fl[(a, f)]['mismatches']} of {fl[(a, f)]['cases']} cases differ" for a in ('amd64', 'arm64') for f in ('carry', 'limb', 'shift'))
jdf_txt = '; '.join(f"{a} {f}: bitmap programs differing {jd[(a, f)]['bitmapMismatchPrograms']}, PoolManager jump targets judged invalid {jd[(a, f)]['poolmanager']['pushJumpTargetsModelInvalid']}"
                    for a in ('amd64', 'arm64') for f in ('opcode', 'bit'))
covtxt = {a: ', '.join(f"{k} {v[0]}/{v[1]}" for k, v in cov[a]['functions'].items() if k.startswith('uint256.')) for a in cov}

cleared = [
    {"chainIds": ARB, "lens": "L1",
     "check": "Symbol comparison of the Nitro v3.13.0-rc.9 release binaries of commit b72783f (amd64 sha256 a142fcbe..., arm64 ba1fec28..., equal to cycle 23's nitro-binaries.sha256, taken again from Docker Hub layers 35a7cb1a and f4d1a9c1 of offchainlabs/nitro-node) against go-ethereum v1.17.10 core/vm (proxy.golang.org module zip, sha256 6e7ac323...), the *_arbitrum.go files of OffchainLabs/go-ethereum master, and holiman/uint256 v1.3.2 (proxy.golang.org zip, sha256 b3998d66...). pclntab lists %d core/vm and %d uint256 functions in each binary, with the same names in both." % (sym['amd64']['vm']['binaryFunctions'], sym['amd64']['u256']['binaryFunctions']),
     "result": "uint256: the binary has no function that v1.3.2 lacks; the 27 source-only names are small helpers the compiler inlined (lsh64, rsh128, umulHop, umulStep, reciprocal2by1, udivrem2by1, subMulTo, addTo and others) or constructors the node never calls. core/vm: the binary-only names are (*Contract).Jumpdest (an accessor that returns the jumpDests interface at Contract+0x30), (*EVM).ChainRules (returns a pointer to evm+0x100), (*p256Verify).SetArbosVersion (stores one word), DefaultTxProcessor.IsCalldataPricingIncrease7976And7981Enabled, newArbitrumAmsterdamInstructionSet, and the closures of makeDup and makePush, which v1.17.10 replaced by opDup1..16 and opPush3..32. v1.17.10 also has execUntraced and execTraced (the generated interpreter) and layeredJumpDests, which the binary does not contain; the binary's (*EVM).Run (5,568 bytes) dispatches every handler by an indirect call through the operation table and contains no adc, sbb or div instruction. Package variables cannot be listed from the binaries, which carry no symbol table or DWARF; the data addresses that the arithmetic and jump handlers read are listed in the next entry. None of these names touches arithmetic, shifts, comparisons or jump analysis.",
     "source": WD + "out/sym/symcmp-amd64.json, out/sym/symcmp-arm64.json, out/sym/amd64.txt, out/sym/arm64.txt; https://proxy.golang.org/github.com/ethereum/go-ethereum/@v/v1.17.10.zip; https://proxy.golang.org/github.com/holiman/uint256/@v/v1.3.2.zip; https://raw.githubusercontent.com/OffchainLabs/go-ethereum/master/core/vm/contract_arbitrum.go"},
    {"chainIds": ARB, "lens": "L1",
     "check": "Every call target and every data reference of opMulmod, opAddmod, opMul, opDiv, opSdiv, opMod, opSmod, opExp, opSHL, opSHR, opSAR, opByte, opSignExtend, opLt, opGt, opSlt, opSgt, opEq, opIszero, opAdd, opSub, opJump, opJumpi, validJumpdest, isCode, codeBitmapInternal, mapJumpDests.Load/Store and the uint256 functions they reach, in both binaries (objdump and llvm-objdump 18 text, resolved against pclntab).",
     "result": "Each arithmetic handler calls exactly one uint256 method (MulMod, AddMod, Mul, Div, SDiv, Mod, SMod, Exp, Lsh, Rsh, SRsh, Byte, ExtendSign, Slt, Sgt) plus runtime.morestack_noctxt and runtime.panicBounds; opLt, opGt, opEq, opIszero, opAdd and opSub are inline. MulMod reaches umul, Reciprocal, reduce4, udivrem and Mod; AddMod reaches Mod and udivrem; Div, Mod and SMod reach udivrem, udivremBy1 and udivremKnuth (on arm64 also math/bits.Div64); Exp reaches Mul and squared; SRsh reaches Rsh. The only data they read are a 32 byte zero constant (AddMod, amd64 0x3f093e8), the constant one (Exp, amd64 0x3f06d20) and the runtime error value passed to gopanic in Reciprocal. opJump and opJumpi read the abort flag at evm+0x170 and two error values. No handler or helper reads or writes a map, a sync.Pool, a table indexed by operands or any other writable global, so commit b72783f keeps no memo or cache in front of the arithmetic. The only cache on the jump path is the jumpDests map keyed by code hash (isCode, map Load/Store), which an earlier cycle tested on chain (OPCODES.md, Arbitrum family row: one address given code with and without a JUMPDEST at the same offset jumps, fails and jumps again). Each handler entry appears once as a funcval in read-only data (amd64 opMulmod at 0x6ba9028, arm64 at 0x6346d78), so the jump table calls the handler itself with no wrapper. A PrecompileCache type exists (precompile_cache.go of the fork, also in v1.17.10); the PoolManager calls no precompile.",
     "source": WD + "out/calls-amd64.json, out/calls-amd64-u256.json, out/calls-arm64.json, out/calls-amd64-run.json, scripts/calls.py, scripts/funcval.py"},
    {"chainIds": ARB, "lens": "L1",
     "check": "The shipped amd64 handlers run in the cycle 27/28 x86-64 model and the shipped arm64 handlers in the cycle 28 AArch64 model, with a Go register ABI shim and the core/vm stack object laid out as both builds read it (scope+0x8 Stack, Stack+0x8 count, Stack+0x10 arena, arena data/capacity/top at +0x0/+0x8/+0x18), guard words below and above the operands. Vector sets per architecture: %s; random seed 30_1185_02 with at least %s cases per opcode (EXP exponents of up to 16 bits, one in 50 a full 256 bit exponent), v4shapes seed 30_1185_01 (mulDiv numerators of five to eight limbs, denominators 2^96, 2^128, liquidity values, prices), direct calls of uint256 Lt, Gt, Slt, Sgt seed 30_1185_03." % (sets, n(minrand)),
     "result": "amd64 %s cases and arm64 %s cases, %d mismatches and %d model errors in total. Every word equals the Python integer result, the stack count and top move by the arity of the opcode, and no guard word changes. Instruction coverage of the uint256 functions (arm64 sample run): %s. The not-reached instructions are the stack growth and panic paths. MulModWithReciprocal is in the binaries but no handler calls it. The first amd64 pass stopped on 691 SIGNEXTEND cases at movsx rbx,bl in ExtendSign (0xc61dbe), an instruction the x86-64 model lacked; movsx and bts were added to the model (scripts/models.py) and all amd64 sets were run again from the start. No function had to be skipped for a call into the Go runtime: memmove is modelled in Python, and morestack and the panic entries stop the model and were never reached." % (n(tot['amd64']), n(tot['arm64']), mis, err, covtxt['arm64']),
     "source": WD + "out/summary.json, out/runs/, out/coverage-amd64.json, out/coverage-arm64.json, scripts/drive.py, scripts/models.py, scripts/goshim.py"},
    {"chainIds": ARB, "lens": "L1",
     "check": "codeBitmapInternal and (*Contract).validJumpdest of both binaries in the models: the PoolManager runtime (24,009 bytes), the runtime cut inside its last 20 PUSH instructions, 1,056 short programs that end inside PUSH1 to PUSH32, and 300 random programs (seed 30_1185_04); every offset, three offsets past the end and words of 2^63, 2^64, 2^64+0x5b, 2^255 and 2^256-1.",
     "result": "%d programs and %s destinations per architecture; no bitmap byte and no validJumpdest answer differs from the reference. On the PoolManager the model accepts exactly the %d JUMPDEST bytes outside push data and rejects the 29 inside push data; all %d distinct push-constant targets of JUMP and JUMPI (the 387 JUMPIs give the jumpmap's 774 sides) are valid. The isCode map path (jumpDests Load and Store, makeslice) was not run because it calls into the Go runtime; with analysis set, isCode reads the bitmap byte at udest>>3 and tests bit udest&7, as source line contract.go:85 of the fork describes." % (jd[('amd64', 'none')]['programs'], n(jd[('amd64', 'none')]['dests']), pm['jumpdestOutsidePush'], pm['pushJumpTargets']),
     "source": WD + "out/jd/amd64-none.json, out/jd/arm64-none.json, scripts/jd.py"},
    {"chainIds": ARB, "lens": "L1",
     "check": "Planted faults in in-memory patched copies of the disassembly text (the binaries are not modified): a carry flip in umul (adc to add, adcs to adds), a wrong limb index in Rsh, an off-by-one bound in Rsh (64 to 65), a changed PUSH1 bound in codeBitmapInternal, and one flipped bitmap bit at a PoolManager jump target.",
     "result": "Every fault is caught. %s. %s." % (fault_txt, jdf_txt),
     "source": WD + "out/faults/, out/jd/*-opcode.json, out/jd/*-bit.json, scripts/faults.py"},
    {"chainIds": ARB, "lens": "L1",
     "check": "2,000 of the model vectors (seed 30_1185_05, 400 each from random, v4shapes, targeted, c27, battery) sent by eth_call to the tools/opdiff battery dispatcher placed by state override, twice per chain, bracketed by web3_clientVersion.",
     "result": "%s. Arbitrum One answered from linux-arm64 builds and Robinhood Chain from both linux-amd64 and linux-arm64 builds of nitro/v3.13.0-rc.9+b72783f, so the running build agrees with both models on these vectors." % '; '.join(chain_lines),
     "source": WD + "out/chain/chain.json, scripts/chain.py; https://arb1.arbitrum.io/rpc; https://rpc.mainnet.chain.robinhood.com"},
    {"chainIds": ARB, "lens": "L1",
     "check": "Which src/ lines depend on these routines: FullMath.mulDiv reads MULMOD(a, b, not(0)) and MULMOD(a, b, denominator) (src/libraries/FullMath.sol:24, :48) and DIV (:35); TickBitmap.compress reads SIGNEXTEND, SDIV, SMOD and SLT (src/libraries/TickBitmap.sol:19-26) and flipTick SDIV and SAR (:64, :67); TickMath shifts (src/libraries/TickMath.sol:63, :111, :142-145); SqrtPriceMath MULMOD and DIV (src/libraries/SqrtPriceMath.sol:62, :252); UnsafeMath DIV and MOD (src/libraries/UnsafeMath.sol:14, :26).",
     "result": "No routine on these lines gives a different word in either binary, so no ordinary account can steer pool math, tick bitmap words or jump targets through a Nitro arithmetic or jump analysis difference at commit b72783f. Token and hook hazards were out of scope and none was met.",
     "source": "src/libraries/FullMath.sol:24"},
]
leads = [
    {"chainIds": ARB, "lens": "L2",
     "question": "Do opSload, opSstore, opTload and opTstore of Nitro b72783f, and the StateDB methods they call, return the stock word for every slot the PoolManager uses, including transient slots after a reverted inner call?",
     "why": "These handlers and the ArbOS state code behind them are still unread in the release binaries; this unit read only arithmetic, shift, comparison and jump analysis code.", "priority": "low"},
    {"chainIds": ARB, "lens": "L1",
     "question": "Do the call family handlers (opCall, opStaticCall, opDelegateCall), the return data copy and the ArbOS hooks in the state transition (StartTxHook, GasChargingHook, EndTxHook of the TxProcessor) of Nitro b72783f behave as the public fork describes for calls into and out of the PoolManager?",
     "why": "They decide what the PoolManager's token transfers, balanceOf reads and hook calls return, and they remain unread in the binaries.", "priority": "low"},
    {"chainIds": ARB, "lens": "L1",
     "question": "Does the isCode map path of Nitro b72783f (jumpDests Load/Store with makeslice and the code hash compare) store the bitmap under the hash of the code it was computed from, read from the binary rather than from chain behaviour?",
     "why": "The model ran the analysis branch of isCode only, because the map path calls into the Go runtime; an earlier cycle tested this path on chain.", "priority": "low"},
]
res = {
    "unit": "theme-nitro-binary-arith-lift",
    "profiles": [],
    "findings": [],
    "cleared": cleared,
    "leads": leads,
    "leadResults": [
        {"leadId": "L-1185", "outcome": "cleared",
         "answer": "Answered from the release binaries of commit b72783f without the source. The core/vm and uint256 functions in pclntab match go-ethereum v1.17.10 and uint256 v1.3.2 by name except for Arbitrum accessors and the older makeDup and makePush closures. The arithmetic, shift, comparison and jump handlers call only stock uint256 methods and read no writable global, so there is no memo or cache in front of them. Run in x86-64 and AArch64 models, they gave the reference word on %s and %s cases with no mismatch; jump analysis matched on every program, planted faults were caught, and 2,000 vectors sent twice to Arbitrum One and Robinhood Chain matched." % (n(tot['amd64']), n(tot['arm64']))}
    ],
}
json.dump(res, open(OUT, 'w'), indent=1)
print(OUT)
