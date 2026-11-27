"""Writes cycles/031/theme-go-family-binary-lift.research.json from the raw results of this work directory."""
import json, os
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = W + '/out/'
OUT = os.path.join(os.path.dirname(W), 'theme-go-family-binary-lift.research.json')
WD = 'research/network-risk/cycles/031/theme-go-family-binary-lift.work/'
S = json.load(open(R + 'summary.json'))
ch = json.load(open(R + 'chain/chain.json'))
ALL = [1, 10, 8453, 130, 7777777, 480, 57073, 1868, 42220, 196, 42161, 4663, 99901, 137, 56, 43114, 143, 4326, 4217, 5042, 999]
THREE = [56, 137, 43114]
OTHER = [c for c in ALL if c not in THREE]
n = lambda x: f'{x:,}'
T = S['targets']
per = '; '.join(f"{k} {n(v['cases'])}" for k, v in sorted(T.items()))
chain_lines = []
for r in ch['results']:
    vers = sorted({p['clientVersionBefore'] for p in r['passes']} | {p['clientVersionAfter'] for p in r['passes']})
    chain_lines.append(f"chain {r['chainId']} at {r['rpc']}: {len(r['passes'])} passes of {n(r['passes'][0]['ran'])} vectors, "
                       f"{sum(len(p['mismatches']) for p in r['passes'])} mismatches, {sum(len(p['errors']) for p in r['passes'])} errors, builds {'; '.join(vers)}")
jd = S['jd']; fl = S['faults']; mm = S['memo']; ak = S['avaxkey']
faults_txt = '; '.join(f"{k} {v['mismatches']} wrong words in {n(v['cases'])} {v['set']} cases (patch at {v['where']['addr']})" for k, v in sorted(fl.items()))
cleared = [
 {"chainIds": THREE, "lens": "L1",
  "check": "Release binaries fetched into the work directory's dl/ and read only with go version -m, nm, objdump, llvm-objdump-18 and Python, never run: bsc v1.8.2 geth_linux (sha256 3009f958...) and geth-linux-arm64 (85fc2a29...); bor v2.11.2 amd64 and arm64 .deb (9073920f... and be8ab16d..., equal to the published .checksum files); avalanchego v1.15.3 linux amd64 and arm64 tarballs (1479ec72... and 0f2e80df...). Build info: bsc go1.25.14, vcs.revision 54afaff4 (vcs.modified true), holiman/uint256 v1.3.2; bor go1.26.11, GitCommit a4afe5a9 (= tag v2.11.2), PGO build, uint256 v1.3.2; avalanchego go1.26.10, commit 983815fd, libevm v1.13.15-0.20261028200218-d398bc4dbe41, uint256 v1.2.4, coreth grafted into the avalanchego module.",
  "result": "The endpoints answered on 2026-11-27 07:13 and 08:08 UTC: bsc-dataseed1 Geth/v1.8.2-4e1c8247-20261104 with go1.26.10 and later Geth/v1.8.2 without a commit, bsc-rpc.publicnode.com reth-bsc/v0.1.4-hotfix-23b510f, polygon-bor-rpc.publicnode.com bor v2.11.1-private builds cb3d19c5f690, ebcfea01452d and 280514fa9fb7 with go1.26.10, api.avax.network avalanchego/1.15.3 commit 983815fd go 1.26.10. Only the Avalanche endpoint runs the commit and Go version of the shipped binary. The BNB Chain dataseed runs a commit (4e1c8247) and Go version that differ from the release asset, and Polygon's public endpoint runs private v2.11.1 builds, so the released binaries read here describe what an operator who installs the release runs. v1.8.2 schedules mainnet Jenner at 1796697000 (CHANGELOG.md and params/config.go:256 at 54afaff4). bor v2.11.2 params/config.go contains no Salvador.",
  "source": WD + "out/buildinfo-bsc.txt, out/buildinfo-bor.txt, out/buildinfo-avax.txt, out/clientversion-start.txt, out/clientversion-end.txt; https://raw.githubusercontent.com/bnb-chain/bsc/54afaff4da31ac9e49ba646a4f65104edac5a2f3/CHANGELOG.md"},
 {"chainIds": [137], "lens": "L1",
  "check": "Is bor's MULMOD memo (core/vm/mulmod_memo.go on the develop branch) in the newest tagged bor release, and which other caches sit in front of an arithmetic, keccak or jump handler? pclntab of both v2.11.2 binaries (454 core/vm functions, 131 and 132 uint256 functions) compared with the tagged source at a4afe5a9 fetched from raw.githubusercontent.com.",
  "result": "No. The tagged tree and both binaries lack mulmod_memo.go (HTTP 404 at a4afe5a9, v2.11.2 and v2.11.1; 200 on develop), and opMulmod calls the stock uint256.(*Int).MulMod directly. The binary-only names are instantiations of the generic BoundedCache, closures and inlined helpers. Three shared caches exist: a keccak cache keyed by the whole 64-byte input (instructions.go:265-278, used by every mapping and CurrencyDelta slot such as src/libraries/CurrencyDelta.sol:14), an ecrecover cache keyed by the input right-padded to 128 bytes, which equals ecrecover's own padding (evm.go:65-90), and a per-block jump destination cache keyed by code hash (core/parallel_state_processor.go:418). The jump cache can only pair a hash with other code if GetCode and GetCodeHash disagree within one execution; ParallelStateDB caches the code read per address for the whole incarnation (core/state/parallel_statedb.go:365-377) and computes the hash from that same value (:843-935), so they agree. No arithmetic, shift, comparison or jump handler reads a writable global: their data references are .rodata, ErrInvalidJump and errStopToken.",
  "source": WD + "out/sym/bor-amd64.json, out/calls/bor-amd64.txt; https://raw.githubusercontent.com/0xPolygon/bor/a4afe5a9c854ef07ea383bfa0d4e4ca45c62d157/core/vm/instructions.go"},
 {"chainIds": [56], "lens": "L1",
  "check": "Symbol comparison of the bsc v1.8.2 binaries (776 core/vm and 129 uint256 functions each) with core/vm at 54afaff4 and uint256 v1.3.2, and the caches in front of the handlers.",
  "result": "Every binary-only name is a compiler-made wrapper (methods promoted from the embedded disabledPrecompile of the CAS20 precompiles), a closure or an inlined helper. cas20_memo.go concerns token transfer memos, not arithmetic. Arithmetic handlers call the stock uint256 routines. The one cache is a process-wide 2,048-entry LRU of jump destination bitmaps keyed by code hash (contract.go:30 and :101-113). Every call site sets the hash and the code from the same account (evm.go:363, :423, :467, :520 with resolveCode and resolveCodeHash at :700-725), and initcode runs with a zero hash and a local bitmap (evm.go:631), so an entry is always the bitmap of the code whose hash keys it. The contract pool resets Code, CodeHash and analysis on reuse (contract_pool.go:17-38).",
  "source": WD + "out/sym/bsc-amd64.json; https://raw.githubusercontent.com/bnb-chain/bsc/54afaff4da31ac9e49ba646a4f65104edac5a2f3/core/vm/contract.go"},
 {"chainIds": [43114], "lens": "L1",
  "check": "Symbol comparison of the avalanchego v1.15.3 binaries (408 libevm core/vm and 127 uint256 v1.2.4 functions each) with libevm at d398bc4dbe41 and uint256 v1.2.4.",
  "result": "The binary-only names are closures, inlined reflect.TypeOf helpers, method-value wrappers of the call family and the autogenerated P256Verify methods. No cache, memo or table sits in front of an arithmetic, shift, comparison or jump handler. uint256 v1.2.4 keeps Cmp, reduce4 and udivrem out of line, and the model runs them.",
  "source": WD + "out/sym/avax-amd64.json; https://raw.githubusercontent.com/ava-labs/libevm/d398bc4dbe41/core/vm/instructions.go"},
 {"chainIds": THREE, "lens": "L1",
  "check": f"The MULMOD, ADDMOD, MUL, DIV, SDIV, MOD, SMOD, EXP, SHL, SHR, SAR, BYTE, SIGNEXTEND, ADD, SUB, LT, GT, SLT, SGT, EQ and ISZERO handlers of all six binaries, with the uint256 routines they call, run in the cycle 30 x86-64 and AArch64 models with a Go register ABI shim extended to three stack layouts read from opLt and opMulmod (bsc arena, bor fixed 1,024-slot array, libevm slice). Sets: tools/opdiff battery.py and targeted.py vectors, cycle 27 extra vectors, FullMath, SqrtPriceMath and SwapMath operand shapes (seed 31_0731_01), random words (seed 31_0731_02) and direct comparison calls (seed 31_0731_03). Cases per binary: {per}.",
  "result": f"{n(S['total']['cases'])} cases, {S['total']['mismatches']} wrong words and {S['total']['errors']} model errors. No word that FullMath.mulDiv (src/libraries/FullMath.sol:24 and :48), SqrtPriceMath, TickMath, BitMath or TickBitmap reads differs from Python integers on these builds.",
  "source": WD + "out/summary.json and out/runs/"},
 {"chainIds": THREE, "lens": "L1",
  "check": "Jump destination analysis: codeBitmapInternal and (*Contract).validJumpdest (isCode inlined in bor and libevm) of all six binaries in the models on the PoolManager runtime of research/network-risk/build/PoolManager.json, on that runtime cut inside its last 20 PUSH instructions, on programs ending inside PUSH1 to PUSH32 and on 300 random programs (seed 31_0731_04). Contract offsets read per build.",
  "result": "1,399 programs and 112,441 destinations per binary give the reference bitmap and validity. On the PoolManager all six accept exactly the 610 JUMPDEST bytes outside push data and reject the 29 inside it, and all 418 pushed jump targets are valid. The planted PUSH1 bound fault and a flipped bitmap bit each make one pushed PoolManager target invalid on every binary (18656 and 14953).",
  "source": WD + "out/jd/"},
 {"chainIds": [43114], "lens": "L2",
  "check": "Avalanche storage key fold (F-040) in the shipped binaries: extstate.partitionStateKeysHook.TransformStateKey (vms/saevm/cchain/libevm/extstate/statedb.go:48 per pclntab) run in both models on 59,273 keys: constant slots 0 to 63, keccak outputs of (word, slot) for the PoolManager's mapping slot numbers and random slots, those outputs plus 0 to 3, words with bit 248 set and clear, and edge words (seed 31_0731_06). Callers of core/state.transformStateKey found by scanning the 762 libevm core/state, core/vm and extstate functions.",
  "result": "The hook clears bit 248 (and of key byte 0 with 0xfe) and gives the reference on every key; 29,569 keys had the bit set. It is called only from StateDB.GetState, GetCommittedState and SetState, so SLOAD and SSTORE apply it and TLOAD and TSTORE do not. Making two PoolManager slots meet still needs keccak outputs that differ only in bit 248, about 2^128 work as cycle 29 recorded, so no ordinary account can use it.",
  "source": WD + "out/avaxkey-amd64.json, out/avaxkey-arm64.json; https://raw.githubusercontent.com/ava-labs/avalanchego/983815fd993acf846a27749b598f0fea4d876a75/vms/saevm/cchain/libevm/extstate/statedb.go"},
 {"chainIds": [137], "lens": "L1",
  "check": "The develop-branch memo logic, written in Python on top of the shipped bor v2.11.2 uint256.Reciprocal and (*Int).MulModWithReciprocal run in the models with z aliasing the modulus, as the memo calls them, over 50,000 sequence steps per architecture (seed 31_0731_08): one modulus reused, two moduli alternated, one limb of the modulus changed between calls, FullMath order (2^256-1 then the denominator) and moduli under 2^192.",
  "result": "100,000 steps, 25,740 memo hits, no wrong word. A memo that compares only limbs 0 to 2 returned no reference word in 20 of its first 417 steps. A future release that enables the memo would use routines that are correct in this build.",
  "source": WD + "out/memo/"},
 {"chainIds": THREE, "lens": "L1",
  "check": "Planted faults on the in-memory disassembly: a carry removed in umul (bor: in MulMod, where PGO inlines umul), limb 2 read as limb 1 in Rsh, the 64 bound of Rsh moved to 65, and on amd64 opLt reading one limb of the second operand twice.",
  "result": f"Every fault is caught on every binary: {faults_txt}.",
  "source": WD + "out/faults/"},
 {"chainIds": THREE, "lens": "L1",
  "check": "2,000 model vectors (seed 31_0731_05, 400 each from random, v4shapes, targeted, c27 and battery) sent twice by eth_call through the battery dispatcher placed by state override, bracketed by web3_clientVersion.",
  "result": " | ".join(chain_lines),
  "source": WD + "out/chain/chain.json"},
 {"chainIds": OTHER, "lens": "L1",
  "check": "Does this theme apply to the other 18 networks?",
  "result": "No. The theme lifts the shipped binaries of the bsc, bor and avalanchego clients, which only BNB Smart Chain, Polygon and Avalanche run. The other networks run other clients, covered by their own units.",
  "source": "research/network-risk/state/networks.json"},
]
leads = [
 {"chainIds": [137], "lens": "L1", "question": "When bor publishes the release that carries Salvador (block 98,688,600), does its binary contain mulmod_memo.go, from which handler is it reached, and do battery.py, targeted.py and scripts/memoseq.py of this work directory pass on it?", "why": "No tagged release carries Salvador or the memo on 27 November 2026, and the public endpoint runs private v2.11.1 builds, so the code that will run on 8 December is unread.", "priority": "high"},
 {"chainIds": [56], "lens": "L1", "question": "Which commit and Go version do BNB Chain validators run after Jenner, given that bsc-dataseed1 answers with commit 4e1c8247 and go1.26.10 while the v1.8.2 release asset is commit 54afaff4 built with go1.25.14 and marked modified?", "why": "The lifted binary is not the build the endpoint runs; the arithmetic and jump paths of that build are known only through RPC answers.", "priority": "low"},
]
unread = ("Still unread in the binaries: the storage, transient storage and journal routines of bsc and bor, the call family, LOG, "
          "precompile dispatch (bsc CAS20 routing), the interpreter loops (bor's optional switch dispatch in interpreter_dispatch.go), "
          "the KECCAK256 handlers and bor's keccak cache in the model, and reth-bsc, which bsc-rpc.publicnode.com runs.")
cleared[4]['result'] += ' ' + unread
d = {"unit": "theme-go-family-binary-lift", "profiles": [], "findings": [], "cleared": cleared, "leads": leads,
     "leadResults": [{"leadId": "L-1076", "outcome": "inconclusive", "answer": "No tagged bor release carries Salvador. v2.11.2 (a4afe5a9) has no mulmod_memo.go in source or binary; its opMulmod calls stock MulMod. The memo's logic on top of v2.11.2's Reciprocal and MulModWithReciprocal gave no wrong word in 100,000 sequence steps. The Salvador release itself is still unpublished."}]}
json.dump(d, open(OUT, 'w'), indent=1)
print(OUT)
