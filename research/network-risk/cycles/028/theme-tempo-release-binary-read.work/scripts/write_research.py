"""Builds theme-tempo-release-binary-read.research.json from the result files of this work directory."""
import json, os, glob, collections

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(W, 'results')
OUT = os.path.join(os.path.dirname(W), 'theme-tempo-release-binary-read.research.json')
REL = 'research/network-risk/cycles/028/theme-tempo-release-binary-read.work/'
ALL = [1, 10, 8453, 130, 7777777, 480, 57073, 1868, 42220, 196, 42161, 4663, 99901, 137, 56, 43114, 143, 4326, 4217, 5042, 999]


def j(name): return json.load(open(os.path.join(R, name)))


def agg(pattern):
    t = collections.Counter(); byop = collections.defaultdict(lambda: [0, 0, 0])
    for f in sorted(glob.glob(os.path.join(R, pattern))):
        d = json.load(open(f))
        for k in ('cases', 'mismatches', 'errors', 'steps'):
            t[k] += d[k]
        for k, v in d['byOp'].items():
            for i in range(3): byop[k][i] += v[i]
    return t, byop


a64, a64op = agg('arith_a64_all_[0-3].json')
x64, x64op = agg('arith_x64_all_[0-3].json')
jda = collections.Counter()
for s in range(4):
    d = j('jd_a64_none_%d.json' % s)
    for k in ('cases', 'mismatches', 'errors'): jda[k] += d[k]
jdx = {k: j('jd_x64_%s.json' % k) for k in ('sse41', 'avx2', 'avx512', 'none')}


def fa(name):
    d = j(name); return d['cases'], d['mismatches']


faults_a = {f: fa('arith_a64_fault_%s.json' % f) for f in ('mulmod_carry', 'recip_mulmod', 'recip_div', 'addmod_fast', 'shr_bound', 'mulmod_max', 'skip_le', 'skip_le_maxmod')}
faults_x = {f: fa('arith_x64_fault_%s.json' % f) for f in ('mulmod_carry', 'recip_div', 'shr_bound')}
faults_jda = {f: fa('jd_a64_%s.json' % f) for f in ('pushx', 'scalar', 'tbx')}
faults_jdx = {f: fa('jd_x64_fault_%s.json' % f) for f in ('sse41_maxsb', 'avx2_maxsb', 'avx512_perm', 'scalar_push')}
cov = j('arith_a64_summary.json')['coverage']


def n(x): return '{:,}'.format(x)


T = 4217
cleared = []


def clr(check, result, source, chains=(T,), lens='L1'):
    cleared.append({'chainIds': list(chains), 'lens': lens, 'check': check, 'result': result, 'source': source})


clr("Which release the Tempo endpoint runs, and whether a later release is published (bracket of the session's RPC use).",
    "rpc.mainnet.tempo.xyz answered web3_clientVersion tempo/v1.19.1-a9d6748/x86_64-unknown-linux-gnu at 23:07 UTC and again at 23:45 UTC on 2026-11-26. The project's binary index at download.tempo.xyz/binaries/ lists v1.14.0 to v1.19.1 and nothing later, and the main branch's Cargo.toml still says version 1.19.0. Both binaries embed the full commit a9d67483a4c21c39cd84d019a45c877ba792c8e2, the version 1.19.1, the features asm_keccak, default, jemalloc, keccak_cache_global and otlp, and build times 2026-11-24T21:42:31Z (x86_64) and 21:42:42Z (aarch64). The endpoint itself is the x86_64 build, so every earlier live test of Tempo ran on x86_64 code.",
    "https://download.tempo.xyz/binaries/ ; " + REL + "results/release_identity.json")
clr("Download and integrity of the v1.19.1 release archives (Task 1). The GitHub release page could not be read: the session proxy answered 403 for github.com/tempoxyz/tempo/releases. The release workflow at a9d6748 (.github/workflows/release.yml lines 436-608) uploads the same artifacts to the R2 bucket that download.tempo.xyz serves, so the archives were taken from there without credentials.",
    "Archive sha256: x86_64 dc48656e6dbedebd23fa984363d0844cde71f3c193929abbb10f4dcf53d1efd1 (49,992,276 bytes), aarch64 73b9d16ea0c3ec84c9893f4e50e473d1458588f6205d146cd94408630a8e8b1b (47,518,378 bytes). Binary sha256: x86_64 77ea6e600123a89c53b760df51560e87ca8de9b96d72c7eb5aa0ad4ec1fd26fd (113,991,408 bytes), aarch64 aa0385450f95ebf84d1dd05df43728b15c2e66bdee4817000b6848e323df2e3b (98,904,688 bytes). All four equal the published .sha256 files, and the SPDX documents name the same archive hashes. The .asc signatures were made 2026-11-24 by EdDSA key EE3C5D41EA963E896F310EC3CBBFA54B20D33446; the copy of that key on keys.openpgp.org carries no user ID, gpg would not import it, and no Tempo page tying the fingerprint to the project was found, so the signatures are not verified. The GitHub attestations could not be read (GitHub API not available). Nothing from the archives was executed or loaded; they were read with tar, readelf, llvm-objdump 18 (which decodes aarch64 itself), objdump and strings, and dl/ is ignored by research/network-risk/.gitignore line 16.",
    "https://download.tempo.xyz/binaries/v1.19.1/ ; https://raw.githubusercontent.com/tempoxyz/tempo/a9d6748/.github/workflows/release.yml")
clr("Identity of the two binaries (Task 1): build id, compiler and linker, symbols and debug information, and the evm2 and ruint versions named in them.",
    "x86_64: ELF64 PIE, GNU build id 8396964a2375733fc8bff726735079399270f31d, .comment rustc 1.100.0 (0ef1bc386 2026-11-09), clang 23.1.0git, LLD 23.1.5, GCC 13.3.0 (C dependencies). aarch64: build id ca8172940c7fa981318b973ab9a590b076c69e8b, rustc 1.100.0 (0ef1bc386 2026-11-09), mold 2.42.1, clang 23.1.0git, GCC 13.3.0. Neither has a .symtab or any .debug section (profile maxperf inherits release with strip = symbols and debug = none, Cargo.toml lines 112-118 and 154-157 at a9d6748; .cargo/config.toml sets no target-cpu); only 10 defined dynamic symbols (allocator exports) remain, so every routine was located by pattern, dispatch table and .eh_frame range. Panic paths name /home/runner/.cargo/git/checkouts/evm2-c00e9c4c9ea851d3/35aa328/ and index.crates.io .../ruint-1.21.1/ in both binaries, matching Cargo.lock at a9d6748 (evm2 rev 35aa32800b147b00e616d4e1869a3835aa86701f, ruint 1.21.1 checksum a0de3fa9..., equal to the sha256 of the crate file read in cycle 20).",
    "https://raw.githubusercontent.com/tempoxyz/tempo/a9d67483a4c21c39cd84d019a45c877ba792c8e2/Cargo.lock ; https://raw.githubusercontent.com/tempoxyz/tempo/a9d67483a4c21c39cd84d019a45c877ba792c8e2/Cargo.toml")
clr("CPU features tested at run time (Task 1).",
    "x86_64: the binary is built for the x86-64 baseline and chooses code by CPU through the std_detect cache at 0x6cba970 (about 500 test sites) and through 120 cpuid sites of other crates. The evm2 jump destination dispatcher at 0x1e29620 tests bits 19, 23 and 27 (avx512f, avx512bw, avx512vbmi), then bit 15 (avx2), then bit 10 (sse4.1) of that word, which are the feature numbers of library/std_detect/src/detect/arch/x86.rs at rustc 0ef1bc386, and calls 0x1e29770, 0x1e29cf0 or 0x1e29fa0, or returns 0 for the scalar loop. The binary has no RUST_STD_DETECT_UNSTABLE override string. No ruint routine and no arithmetic handler reads the cache: ruint picks its x86 code (the div instruction for reciprocals) at compile time. aarch64: the NEON kernel is compiled in unconditionally (analysis/aarch64.rs line 19-20) and the ruint routines use the MG10 reciprocal table, with no run-time choice in either. So on the code paths this unit covers, only the x86_64 jump destination kernel depends on the validator's CPU.",
    "https://raw.githubusercontent.com/rust-lang/rust/0ef1bc386/library/std_detect/src/detect/arch/x86.rs ; " + REL + "build (disassembly, not kept)")
clr("Where the routines are in the shipped code, and what is inlined (Task 2).",
    "Dispatch tables were read from the R_AARCH64_RELATIVE and R_X86_64_RELATIVE relocations: three handler families per binary (aarch64 tables 0x5da9a50, 0x5dc6098, 0x5dc6898; x86_64 0x6becbf8, 0x6c09a28, 0x6c09228). In both binaries ADD, MUL, SUB, the comparisons, AND, OR, XOR, NOT, BYTE, SHL, SHR, SAR and SIGNEXTEND are inlined into their handlers, so ruint's shift functions exist only inside them; EXP (wrapping_pow) is inlined in one family and called by the others; the ADDMOD fast path of modular.rs 37-49 is inlined in the handler (aarch64 0x3b5af74) and add_mod_by_ref is a separate function (aarch64 0x42b9334, x86 0x4af2910) that calls div_rem_bits_plus_one (aarch64 0x42b9448, x86 0x4af2a60) and rem_by_ref. MULMOD handlers all call mul_mod_by_ref (aarch64 0x42bab24, x86 0x4af3d90), with Product, the 2^256-1 end-around carry, rem_nxm_spare_limb and div_nxm inlined. DIV and SDIV call div_rem_by_ref (aarch64 0x18eceac, x86 0x19145b0), MOD and SMOD call rem_by_ref (aarch64 0x18eb894, x86 0x1913350), with div_nxn, div_n1xn, div_nxm, div_nx1, div_nx2 and the reciprocals inlined; submul_max stays separate (aarch64 0x28211b8). The aarch64 MG10 table (reciprocal.rs lines 85-103) appears once, at 0x1350fc4, and is read at 36 places in five functions: these four and a 512 bit div_rem. The x86 binary has no copy of it and computes reciprocals with div (reciprocal.rs line 30). The jump destination analysis is aarch64 0x1d47980 (analyze_neon, the only function with tbx) called from three identical copies of the lazy jump table builder (0x1d477c0, 0x32706b4, 0x4570a68) that inline analyze_scalar; x86 has the dispatcher and three kernels above, called from three identical copies (0x1e294c0, 0x3777260, 0x4e33560).",
    REL + "results/a64_handlers.json, results/a64_arith_funcs.json, results/x64_arith_funcs.json")
clr("Lifted aarch64 jump destination analysis (Task 3): analyze_neon 0x1d47980-0x1d47db8 and the builder's scalar tail, run from their own disassembly in a model written for this unit (scripts/a64emu.py, integer and NEON instructions only), on the PoolManager build of this checkout, 559 windows of it, PUSH1 to PUSH32 with 0x5b in every lane at 130 offsets and 5 tails (with 0x5b and 0x00 prefixes and truncated), 1,200 uniform fills and 6,000 random codes (seed 280281).",
    "%s cases, %s mismatches against the one instruction at a time rule, %s model errors. 308 of the 320 instructions in the range were reached; the 12 not reached are the builder's other lazy-init entry, its zero-length path that the harness enters directly, and one branch that needs a length below 16, which the caller never passes. Planted one-instruction faults are caught: PUSHX 0x5f to 0x5e at 0x1d47a58 fails %s of %s cases, a wrong tbx table register at 0x1d47b34 fails %s of %s, and the scalar tail comparing with 0x60 at 0x1d4793c fails %s of %s. This is the first run of the shipped aarch64 kernel bytes. The 3,026 jump cases of Check 4 were live calls whose case file was not found in the repository, so this set replaces them with a superset of the same kind (jumps into and around push data reduce to the jump destination bitmap tested here)." % (n(jda['cases']), jda['mismatches'], jda['errors'], n(faults_jda['pushx'][1]), n(faults_jda['pushx'][0]), n(faults_jda['tbx'][1]), n(faults_jda['tbx'][0]), n(faults_jda['scalar'][1]), n(faults_jda['scalar'][0])),
    REL + "scripts/jd_a64.py, results/jd_a64_none_0.json to _3.json")
clr("Lifted x86_64 jump destination analysis (Task 3): the dispatcher 0x1e29620, analyze_sse41 0x1e29fa0, analyze_avx2 0x1e29cf0, analyze_avx512vbmi 0x1e29770 and the builder's scalar tail, each forced by setting the std_detect word in the model (scripts/x86vec.py extends the cycle 27 model with SSE, AVX2 and AVX-512 byte, permute and opmask instructions), on the PoolManager build, 330 windows, push lanes at 44 offsets, uniform fills and 1,500 random codes (seed 280282).",
    "Per kernel %s cases: SSE4.1 %s mismatches (357 of 357 instructions reached), AVX2 %s (144 of 144), AVX-512 VBMI %s (247 of 247), scalar only %s. Planted faults are caught: pmaxsb to pmaxub in the successor map at 0x1e2a0af fails %s of %s (the same change at 0x1e2a091, which only selects the block fast path, changed nothing, as expected), vpmaxsb to vpmaxub at 0x1e29ead fails %s of %s, a wrong vpermt2b index at 0x1e29805 fails %s of %s, and the scalar PUSH bound 0x5f to 0x60 at 0x1e295ee fails %s of %s. Cycle 18 ran these kernels from a local build of the source; this is the shipped code." % (
        n(jdx['sse41']['cases']), jdx['sse41']['mismatches'], jdx['avx2']['mismatches'], jdx['avx512']['mismatches'], jdx['none']['mismatches'],
        n(faults_jdx['sse41_maxsb'][1]), n(faults_jdx['sse41_maxsb'][0]), n(faults_jdx['avx2_maxsb'][1]), n(faults_jdx['avx2_maxsb'][0]),
        n(faults_jdx['avx512_perm'][1]), n(faults_jdx['avx512_perm'][0]), n(faults_jdx['scalar_push'][1]), n(faults_jdx['scalar_push'][0])),
    REL + "scripts/jd_x64.py, results/jd_x64_*.json")
clr("Lifted aarch64 arithmetic handlers and ruint routines (Task 3): every handler of the 25 arithmetic, comparison, bitwise and shift opcodes in all three dispatch families, with div_rem_by_ref, rem_by_ref, add_mod_by_ref, div_rem_bits_plus_one, mul_mod_by_ref and submul_max, run on battery.py (99,985), targeted.py (85,544 with the 8,908 vectors of the October 2026 mul_mod fault), and the 21,537 vectors of cycles/025/stablecoin-l1.work/maxmod.py and maxmod2.py (with their 4,500 SqrtPriceMath and FullMath shaped calls), each MULMOD also with modulus 2^256-1 as FullMath.mulDiv's prod1 rebuild does (src/libraries/FullMath.sol:24).",
    "%s handler runs, %s mismatches with Python integers, %s model errors, %s modelled instructions. Coverage of the routines: mul_mod_by_ref %d of %d instructions, div_rem_by_ref %d of %d, rem_by_ref %d of %d, div_rem_bits_plus_one %d of %d, add_mod_by_ref %d of %d, the ADDMOD handler %d of %d; the rest are paths for other operand lengths and panics. Planted faults: a dropped carry in the 2^256-1 path (0x42bac1c) fails %s of %s, the MG10 table read 16 entries off in mul_mod (0x42bb014) fails %s of %s and in div_rem (0x18ed1ec) %s of %s, a wrong borrow select in the ADDMOD fast path %s of %s, SHR bound 0x100 to 0xff %s of %s. The exact ruint 1.21.0 fault, the skip test of knuth.rs 133-136 at 0x42baff4-0x42baffc turned from < into <=, fails %s of %s targeted cases and %s of %s maxmod cases, so the vectors see the October fault in the shipped code. Disabling the 2^256-1 fast path (0x42bab70) changes no result, as expected, because the general path computes the same remainder." % (
        n(a64['cases']), a64['mismatches'], a64['errors'], n(a64['steps']),
        cov['0x42bab24'][1], cov['0x42bab24'][0], cov['0x18eceac'][1], cov['0x18eceac'][0], cov['0x18eb894'][1], cov['0x18eb894'][0],
        cov['0x42b9448'][1], cov['0x42b9448'][0], cov['0x42b9334'][1], cov['0x42b9334'][0], cov['0x3b5af74'][1], cov['0x3b5af74'][0],
        n(faults_a['mulmod_carry'][1]), n(faults_a['mulmod_carry'][0]), n(faults_a['recip_mulmod'][1]), n(faults_a['recip_mulmod'][0]),
        n(faults_a['recip_div'][1]), n(faults_a['recip_div'][0]), n(faults_a['addmod_fast'][1]), n(faults_a['addmod_fast'][0]),
        n(faults_a['shr_bound'][1]), n(faults_a['shr_bound'][0]), n(faults_a['skip_le'][1]), n(faults_a['skip_le'][0]),
        n(faults_a['skip_le_maxmod'][1]), n(faults_a['skip_le_maxmod'][0])),
    REL + "scripts/arith_a64.py, results/arith_a64_all_0.json to _3.json, results/arith_a64_summary.json")
clr("Lifted x86_64 arithmetic handlers and ruint routines (Task 3): the same 25 opcodes in the three x86 dispatch families with mul_mod_by_ref 0x4af3d90, div_rem_by_ref 0x19145b0, rem_by_ref 0x1913350, add_mod_by_ref 0x4af2910 and div_rem_bits_plus_one 0x4af2a60, through the cycle 27 x86 model extended with rip-relative operands, file-backed constants, GOT calls, 32 bit div and the SSE2 moves this code uses (scripts/x86emu2.py), on the same vector sets.",
    "%s handler runs, %s mismatches, %s model errors. Planted faults: a dropped carry in the 2^256-1 path (0x4af3ed0) fails %s of %s, a wrong dividend for the reciprocal div (0x1914a78) fails %s of %s, SHR bound 0x100 to 0xff (0x42acd03) fails %s of %s." % (
        n(x64['cases']), x64['mismatches'], x64['errors'], n(faults_x['mulmod_carry'][1]), n(faults_x['mulmod_carry'][0]),
        n(faults_x['recip_div'][1]), n(faults_x['recip_div'][0]), n(faults_x['shr_bound'][1]), n(faults_x['shr_bound'][0])),
    REL + "scripts/arith_x64.py, results/arith_x64_all_0.json to _3.json")
clr("JUMP and JUMPI handlers of the aarch64 binary (family at 0x5da9a50, handlers 0x3b61654 and 0x3b616c8), read from the disassembly.",
    "JUMPI ORs all four limbs of the condition word and takes the branch on any nonzero bit. Both handlers reject a destination with a nonzero upper limb, compare the low limb with the analysed code length at [ctx+0x88] and test bit dest%8 of byte dest/8 of the table at [ctx+0x80], the table the lifted analysis builds. A taken jump to a non-JUMPDEST byte returns status 42. This matches the specification; these handlers were read, not run in the model.",
    REL + "build/a64.dis 0x3b61654-0x3b61764 (not kept)")
clr("What the results mean for the PoolManager source on Tempo (all networks except Tempo are not affected by this unit).",
    "The arithmetic that src/libraries relies on (FullMath.mulDiv and mulDivRoundingUp's MULMOD with the 2^256-1 modulus and with full width denominators at src/libraries/FullMath.sol:24 and :48, the DIVs at :35, :62, :67, :73, UnsafeMath.divRoundingUp's DIV and MOD, TickMath's SAR, SHL, SHR and BYTE, SqrtPriceMath's MULMOD, TickBitmap's SDIV and SMOD and SIGNEXTEND) gives the specified word in the shipped code of both architectures on every vector, and the jump destination set of the PoolManager runtime is the same in all five shipped kernels. No validator hardware choice among x86_64 SSE4.1, AVX2, AVX-512 VBMI, no SIMD, or aarch64 changes a result. So no difference between validators of different hardware exists here for an ordinary account to use, and none of these paths gives a way to take or lock pool funds.",
    "src/libraries/FullMath.sol:24 ; src/libraries/UnsafeMath.sol ; src/libraries/TickBitmap.sol ; src/libraries/TickMath.sol")

leads = [
    {"chainIds": [T], "lens": "L1", "question": "Lift the remaining PoolManager opcode handlers of both shipped binaries (KECCAK256 with the asm_keccak and keccak_cache_global features, CALLDATALOAD, MCOPY, TLOAD and TSTORE, JUMP and JUMPI) into the a64emu and x86 models and run the battery's sequences through them.", "why": "This unit lifted the arithmetic, shift and jump destination code; the other handlers of the shipped binaries were read only (JUMP, JUMPI) or not at all, and keccak-asm may choose code by CPU.", "priority": "low"},
    {"chainIds": [T], "lens": "L1", "question": "Verify the GPG signature of the v1.19.1 archives with a key whose fingerprint Tempo publishes, and read the GitHub build provenance attestation of the bare binaries.", "why": "The sha256 files match, but they come from the same bucket; the signing key EE3C5D41EA963E896F310EC3CBBFA54B20D33446 could not be tied to the project in this session.", "priority": "low"},
]

lead_results = [
    {"leadId": "L-1151", "outcome": "cleared", "answer": "The x86_64 and aarch64-unknown-linux-gnu tempo v1.19.1 binaries (a9d6748, rustc 1.100.0, evm2 35aa328, ruint 1.21.1) were read without running them. Their jump destination kernels (NEON; SSE4.1, AVX2, AVX-512 VBMI and scalar), and every arithmetic, comparison and shift handler with the ruint routines they call, were lifted from their own disassembly into models and run: %s jump table cases on aarch64 and %s per x86 kernel, %s aarch64 and %s x86 handler runs, with no mismatch and with planted one-instruction faults caught, including the exact ruint 1.21.0 skip test. Statements now resting on the shipped binaries: cycle 10's L-612 and cycle 20's L-906 (NEON kernel; previously a software model of the source), cycle 18's L-582 (x86 kernels; previously a local rustc 1.97 build), cycle 10's aarch64 against x86 arithmetic check and cycle 20's L-879 (previously the x86 build with the fallback forced), and cycle 25's 21,537 vectors (previously the x86 endpoint only). Still resting on source or a local build: the reading of i256 signed division, the EXP gas rule, the handlers outside arithmetic, shifts and jumps, and anything about the aarch64-apple-darwin build. No release after v1.19.1 is published." % (n(jda['cases']), n(jdx['sse41']['cases']), n(a64['cases']), n(x64['cases']))},
    {"leadId": "L-925", "outcome": "cleared", "answer": "Replaced by L-1151 and answered there."},
]

doc = {"unit": "theme-tempo-release-binary-read", "profiles": [], "findings": [], "cleared": cleared, "leads": leads, "leadResults": lead_results}
json.dump(doc, open(OUT, 'w'), indent=1)
print(OUT)
