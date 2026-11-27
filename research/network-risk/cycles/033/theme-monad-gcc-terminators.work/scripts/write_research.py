"""Cycle 33: write theme-monad-gcc-terminators.research.json from the outputs in out/."""
import json, os, glob, collections
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
O = os.path.join(W, 'out')
R = 'research/network-risk/cycles/033/theme-monad-gcc-terminators.work'
C31 = 'research/network-risk/cycles/031/theme-monad-gcc-real-states.work'
C27 = 'research/network-risk/cycles/027/theme-monad-package-read.work'
J = lambda n: json.load(open(os.path.join(O, n)))
ALL = [1, 10, 8453, 130, 7777777, 480, 57073, 1868, 42220, 196, 42161, 4663, 99901, 137, 56, 43114, 143, 4326, 4217, 5042, 999]
OTHER = [c for c in ALL if c != 143]

term = J('term.json'); synth = J('term-synth.json'); cct = J('cctables.json'); t3 = J('task3.json'); edge = J('edgecheck.json')
kinds = collections.Counter(b['kind'] for b in term['blocks'])
assert term['flagged'] == 0 and term['badRuns'] == 0 and term['stops'] == 0 and len(term['blocks']) == 128
jcc = collections.Counter(j.split()[0] for b in term['blocks'] for j in b['jcc'])
dcs = collections.Counter(); keep = collections.Counter(); tabl = 0; jt = 0
for b in term['blocks']:
    if 'tableFromClangListing' in b: tabl += 1
    if b['kind'] == 'Jump' and any(l.startswith('jnb') for l in b['gccStream']): jt += 1
    if b['kind'] == 'JumpI':
        keep[b['keepStackInNextBlock']] += 1
        d = b['dc']
        if d[0] == '(nil)' and d[1] == '(nil)': dcs['materialised'] += 1
        else: dcs[['Below', 'AboveEqual', 'Above', 'BelowEqual', 'Less', 'GreaterEqual', 'Greater', 'LessEqual', 'Equal', 'NotEqual'][d[2]] + (' negated' if d[1] != '(nil)' else '')] += 1
blocks = {}
for f in glob.glob(os.path.join(O, 'block-0x*.json')):
    for b in json.load(open(f))['blocks']: blocks[b['block']] = b
assert all(b['stream'] == 'equal' and b['badRuns'] == 0 and b['sets'] == 20000 for b in blocks.values()) and len(blocks) == 7
faults = {}
for f in sorted(glob.glob(os.path.join(O, 'term-*.json'))):
    d = json.load(open(f))
    if d.get('fault'): faults['term:' + d['fault']] = (d['runs'], d['badRuns'], d['flagged'])
for f in sorted(glob.glob(os.path.join(O, 'block-*-0x*.json'))):
    d = json.load(open(f))
    if d.get('fault'): faults['block:' + d['fault']] = (d['runs'], d['badRuns'], d['flagged'])
assert all(v[2] > 0 for v in faults.values()), faults
bk = t3['byKind']
inl = t3['inlinedNotRun']
nrun3 = sum(v['sites'] for v in bk.values()); ninl = sum(inl.values())
touched = sum(1 for s in t3['sites'] if s.get('touchedMemorySizeFromListing'))
assert all(v['different'] == 0 for v in bk.values())
e588 = edge['blocks']['0x588a']; e58d6 = edge['blocks']['0x58d6']; e51cf = edge['blocks']['0x51cf']

def fmt(c): return ', '.join('%s %d' % (k, v) for k, v in sorted(c.items(), key=lambda x: -x[1]))

cleared = [
 {"chainIds": [143], "lens": "L1",
  "check": "Task 1 (L-1238), all 128 terminators of the 128 un-entered value blocks: %s. For each block the cycle 31 hook state logged before the terminator (%s/out/states.jsonl, record w=t) was laid out as the gcc 15.2.0 build reads the Stack, deferred comparison included, and the package's whole emit function ran in the cycle 27 x86 model: Emitter::jumpi(Block const&) 0x394df0 with a model Block for the fall-through block (offset +0x28, terminator +0x18, instruction vector +0x0/+0x8, read from the dispatch at 0x394dff to 0x394f2f), Emitter::jump() 0x392400, fallthrough() 0x382980, return_() 0x383060 and stop() 0x36f0f0, with every function of their direct-call closure interpreted from the package text (jumpi_keep_fallthrough_stack 0x3949c0, jumpi_spill_fallthrough_stack 0x3944d0, jumpi_comparison 0x36f500, conditional_jmp 0x36f430, both discharge_deferred_comparison, write_to_final_stack_offsets 0x3816e0, adjust_by_stack_delta<false> 0x399180 and <true> 0x399270, jump_stack_elem_dest, non_literal_jump_dest_operand, jump_non_literal_dest 0x391d30, jump_dest_label 0x36f240, jump_literal_dest, return_with_status_code 0x382c90, mov_stack_elem_to_unaligned_mem<true>, missing_spill_count and the allocators). The Emitter fields these read were set as the code reads them: epilogue label +0x238, error label +0x248, engaged jump table label +0x258/+0x268, keep_stack_in_next_block_ +0x3e0, bytecode_size_ +0x4a4 = 24009, and the jump destination map +0x4a8 (std::unordered_map<size_t, Label>, nodes next/key/Label) holding the 610 JUMPDESTs of the runtime. BaseAssembler::newLabel 0x637530 and bind 0x637650 were recording stubs. The cycle 29 operand decoder dropped the index scale of asmjit memory operands (signature bits 16 and 17); it was fixed, so the jump table load reads [rax+r*4]. Streams were compared with the clang listing body of the terminator with exact rbp and rsp displacements, exact immediates, exact block labels and the condition code, registers and local labels renamed by first appearance (scripts/term.py strict)." % (fmt(kinds), C31),
  "result": "All 128 gcc streams equal the clang listing. Conditional jumps emitted: %s; the jnb and jnz pairs are the range checks of the %d jumps through the jump table, the other %d jumps go to a literal block label. The 31 JUMPI terminators split into %d with a materialised condition and %s; %d keep the fall-through stack in registers and %d spill it, %d of them because the fall-through block is a JUMPDEST. At %d blocks the clang listing uses a limb order of a register row that the hook log does not carry; with the order read from the listing the gcc stream is equal. No terminator stopped on an assertion or left the closure." % (fmt(jcc), jt, kinds['Jump'] - jt, dcs['materialised'], fmt({k: v for k, v in dcs.items() if k != 'materialised'}), keep[1], keep[0], sum(1 for b in term['blocks'] if b['kind'] == 'JumpI' and b['fallthroughBlock']['isJumpdest']), tabl),
  "source": R + "/scripts/term.py ; " + R + "/out/term.json ; " + R + "/out/term.log"},
 {"chainIds": [143], "lens": "L1",
  "check": "Task 2 at the terminator: each of the 128 streams ran in the x86 model %d times (seed 3333), %d runs in all. Label targets were resolved to exits (block label, error label, epilogue, a jump table whose entry d holds 16*d for a JUMPDEST and the error label otherwise, fall through). A deferred comparison's flags came from operand pairs on the edge of a 256-bit compare (equal, one below, one above, top limb equal with lower limbs different, sign bit set on one side, zero, a single limb differing) for the first quarter of the runs and from random pairs after that; elements holding the comparison got the 0 or 1 the flags mean. Jump destinations were JUMPDESTs 60 percent of the time and otherwise 24009, 24008, 0, a JUMPDEST plus one, a JUMPDEST with bit 64, 128, 192 or 255 set, or a random word; materialised conditions were 0, 1, all ones, 2^64, 2^128, 2^192, 2^255 or random. The reference successor is the EVM rule of pyevm.py's JUMP and JUMPI arms (tools/opdiff/pyevm.py, lines listed in out/term.json pyevmJumpArms). For the taken side the words at rbp + 32*i for every index left on the stack, rbp moved by 32 times the block delta and the stack size counter [rsp+48] moved by the delta were checked; for a kept fall-through every location the Stack records for each element; for RETURN the offset and size words at [rbx+192] and [rbx+224] and the status word. A second run (SYNTH=1, out/term-synth.json) put each of the 10 Comparison codes, positive and negated, on each of the %d logged JUMPI states that carry a deferred comparison and drove all 16 flag states in turn, %d runs." % (2000, term['runs'], 14, synth['runs']),
  "result": "No run chose a different successor and no successor word, rbp, counter, result word or status differed: 0 bad runs of %d, and 0 of %d in the synthetic run, so every condition code and its negation is emitted and taken as the comparison means, including the signed ones that no logged state carries." % (term['runs'], synth['runs']),
  "source": R + "/scripts/term.py ; " + R + "/out/term.json ; " + R + "/out/term-synth.json ; research/network-risk/tools/opdiff/pyevm.py"},
 {"chainIds": [143], "lens": "L1",
  "check": "The two lookup tables the JUMPI path reads from the shipped ELF's data, never executed: CSWTCH.2401 at 0x810800, the negate_comparison table that jumpi_keep_fallthrough_stack and jumpi_spill_fallthrough_stack index at 0x394b9a, and the switch table of Emitter::conditional_jmp at 0x8107c0, decoded to the asmjit instruction id of each arm (scripts/cctables.py). Cycle 27 decoded these tables from the harness only.",
  "result": "The negation table maps each of the 10 codes to its negation as virtual_stack.hpp:100-127 says, and the switch sends Below, AboveEqual, Above, BelowEqual, Less, GreaterEqual, Greater, LessEqual, Equal and NotEqual to jb, jae, ja, jbe, jl, jge, jg, jle, je and jne (ids 0x13b, 0x13a, 0x139, 0x13c, 0x142, 0x141, 0x140, 0x143, 0x13e, 0x14a). All 20 entries are as the source says." if cct['ok'] else 'MISMATCH',
  "source": R + "/scripts/cctables.py ; " + R + "/out/cctables.json ; " + C31 + "/dl/category_vm_compiler_ir_x86_virtual_stack.hpp:86-127 ; " + C31 + "/dl/category_vm_compiler_ir_x86_emitter.cpp:3731-3764"},
 {"chainIds": [143], "lens": "L1",
  "check": "Task 2, whole blocks: the FullMath.mulDiv blocks 0x5757, 0x57ca, 0x5860, 0x588a, 0x58d6, 0x58db and the mulDivRoundingUp remainder block 0x51cf. Every code-emitting instruction was emitted by the package's own emit function from its logged state and the terminator by the same functions as above, the limb table threaded from site to site as the Emitter does (a literal shift by 128 renames limbs, so the table at the terminator of 0x5757 differs from the one at its entry). The concatenated stream was compared with the clang listing of the block body, then run from the block entry state with the package's runtime helpers serving every helper call, and compared with pyevm.py run on the block's own bytecode from the same entry stack: the successor and every stack word at block exit. 20,000 operand sets per block (seeds 3334), a third of them with an entry word rewritten so that a word the block compares (the GT of remainder and prod0, the LT of mm and prod0, the GT of prod1 and the denominator at FullMath.sol:30, the EQ at :33) is equal to, one above, one below, equal in the top limb to, or zero against the other, and a third with the multiplicand of the MULMOD made a multiple of the modulus. scripts/edgecheck.py traced 3,000 more sets per block the same way to count which edges are reached.",
  "result": "All seven concatenated streams equal the clang listing, and all 140,000 runs give the successor and every exit word pyevm.py gives (0 bad runs). At 0x588a the branch is require(denominator > prod1) of FullMath.sol:30: it jumps to 0x330 (JUMPDEST PUSH0 DUP1 REVERT) through jae, and took that side in %s of the 20,000 runs; edgecheck found the GT operands equal in %d and one apart in %d of 3,000 sets. At 0x58d6 the prod1 == 0 test of :33 jumps to 0x593c (the div(prod0, denominator) return) in %s runs, with the EQ operands equal in %d, one apart in %d and equal in the top limb only in %d of 3,000. At 0x51cf the remainder test of :112 took the rounding side in %s runs, with the remainder zero in %d of 3,000. Each JUMPI side, both MULMOD remainder cases and the denominator equal to, one below and one above prod1 were reached." % (blocks['0x588a']['outcomes'].get("('jump', 816)"), e588.get('GT@58cf:equal', 0), e588.get('GT@58cf:one-apart', 0), blocks['0x58d6']['outcomes'].get("('jump', 22844)"), e58d6.get('EQ@58d6:equal', 0), e58d6.get('EQ@58d6:one-apart', 0), e58d6.get('EQ@58d6:top-limb-equal', 0), blocks['0x51cf']['outcomes'].get("('jump', 20808)"), e51cf.get('MULMOD@51de:remainder-zero', 0)),
  "source": R + "/scripts/block.py ; " + R + "/out/block-0x5757_0x57ca.json ; " + R + "/out/block-0x5860_0x588a.json ; " + R + "/out/block-0x58d6_0x51cf.json ; " + R + "/out/block-0x58db.json ; " + R + "/out/edgecheck.json ; src/libraries/FullMath.sol:21-37 ; src/libraries/FullMath.sol:109-115"},
 {"chainIds": [143], "lens": "L1",
  "check": "Task 3 (L-1234): the memory, context and SIGNEXTEND sites of the 128 blocks that have a standalone emit function in the gcc build, %d sites: %s. Each ran whole from its logged state with the limb table threaded through its block, MSTORE of a literal word with Stack::alloc_literal 0x3ad360 run from the package, and its stream was compared with the clang listing group of the same pc (scripts/task3.py). SIGNEXTEND (all 10 sites have a literal index) also ran on 2,000 operand sets per site against pyevm.py." % (nrun3, ', '.join('%s %d' % (k, v['sites']) for k, v in bk.items())),
  "result": "All %d streams equal the clang listing. At %d MSTORE sites (0x417, 0x421, 0x487, 0x491, 0x4c6) the listing skips the memory bound check because the offset element was already checked; that is StackElem::touched_memory_size_ (block +0x80, read by touch_memory<V> at 0x395694), which the cycle 31 hook does not log; with it set to 32 the gcc stream is equal. The %d MLOAD and MSTORE calls are the memory growth call (cmp dword ptr [rbx+264], end; jae; mov or lea rdi; call qword ptr [ROD]) with no spill before it, the same in both builds; the routine it reaches, monad_vm_runtime_increase_memory_raw_v1 and _mip3, is byte-equal to the harness (cycle 27) and its trampoline was read in cycle 29. SIGNEXTEND: 20,000 runs, 0 mismatches." % (nrun3, touched, bk['MLOAD']['calls'] + bk['MSTORE']['calls']),
  "source": R + "/scripts/task3.py ; " + R + "/out/task3.json ; " + C31 + "/dl/category_vm_compiler_ir_x86_emitter.cpp:6277-6352"},
 {"chainIds": [143], "lens": "L1",
  "check": "Task 4: planted faults, each a one-line change to the package text in the model or to the model's data, run through the same checks: %s." % '; '.join('%s (%d runs, %d bad, %d blocks flagged)' % (k, v[0], v[1], v[2]) for k, v in sorted(faults.items())),
  "result": "Every fault was caught: an inverted condition code (jae as jb, jne as je), the keep path without negation, a condition test that skips the low limbs or the top limb, a wrong successor rbp (shl 4 for shl 5 in adjust_by_stack_delta), a deferred comparison left in the flags at the JUMPI, a shifted jump destination map, compare operands swapped in the LT and GT emitter, and a deferred comparison discharged after SUB has reused the flags. An unsaved live register around a keccak or sload call could not be planted, because those emitters are inlined into compile_basic_blocks<traits> and were not driven.",
  "source": R + "/scripts/faults33.json ; " + R + "/scripts/faults33b.json ; " + R + "/out/term-faults.log"},
 {"chainIds": [143], "lens": "L1",
  "check": "The build in front of the validators. Read-only calls to https://rpc.monad.xyz on 2026-11-27: web3_clientVersion before and after, eth_getCode of the PoolManager 0x188d586ddcf52439676ca21a244753fa19f9ea8e. The package index https://pkg.category.xyz/dists/noble/main/binary-amd64/Packages.gz was fetched again.",
  "result": "The endpoint answered Monad/0.16.7 (the second web3_clientVersion and eth_blockNumber were refused with 'Rate limit exceeded', recorded and not retried). The code is the 24,009-byte runtime analysed here (sha256 prefix 288b97729c9e4f34, equal byte for byte). The index, last modified 18 November 2026, lists 0.16.7 as the newest monad release with SHA256 3cb9dba5501b61ea3487bd042e2b8d12f871cff0e2e15409210e2cef0f8e81fb, the package read since cycle 27.",
  "source": R + "/out/rpc ; https://rpc.monad.xyz ; https://pkg.category.xyz/dists/noble/main/binary-amd64/Packages.gz"},
 {"chainIds": OTHER, "lens": "L1",
  "check": "Whether this theme applies to the other 20 networks.",
  "result": "It does not. The terminators, memory emitters and block streams examined here are those of Monad's native compiler, which only Monad's validators run. The other networks execute the PoolManager in their own interpreters, whose jump, comparison and memory handling OPCODES.md checks 1 to 4 cover. Nothing in this unit changes a result for them.",
  "source": "research/network-risk/OPCODES.md"},
 {"chainIds": [143], "lens": "L1",
  "check": "The source lines whose branches these blocks hold, read in this repository: FullMath.mulDiv computes prod0 and prod1 by mulmod with not(0) and sub (src/libraries/FullMath.sol:21-26), requires denominator > prod1 (:30), returns div(prod0, denominator) when prod1 == 0 (:33-37), otherwise subtracts the remainder, factors out twos and multiplies by the Newton inverse (:46-99); mulDivRoundingUp adds one when mulmod(a, b, denominator) != 0 and requires the sum to be non-zero (:111-114).",
  "result": "The text does what its comments say. With the branches at :30, :33 and :112 emitted and taken as pyevm.py takes them on Monad's shipped build, no ordinary account can make mulDiv skip the overflow revert, take the 256-bit division on a 512-bit product, or drop a rounding unit.",
  "source": "src/libraries/FullMath.sol:14-116"},
]
leads = [
 {"chainIds": [143], "lens": "L1",
  "question": "Drive the %d remaining sites of the 128 blocks (%s), whose emitters sha3<>, sload<>, sstore<>, tload<> and log<N><> the gcc build inlines into compile_basic_blocks<MonadTraits<r>>: run that function's body for one revision in the model on the logged states, record the spills and argument registers around each runtime call, and compare with the clang listing." % (ninl, ', '.join('%s %d' % kv for kv in sorted(inl.items()))),
  "why": "These sites call keccak, storage and log routines with live words in registers. Their streams are the last emit kinds of these blocks not run from the package; an unsaved register there would change a pool key or slot without changing any word compared so far.",
  "priority": "low"},
 {"chainIds": [143], "lens": "L1",
  "question": "Extend the cycle 31 hook to log StackElem::touched_memory_size_ (block +0x80) and the limb table gpq256_regs_ at every state, and rerun term.py, block.py and task3.py without reading either from the clang listing.",
  "why": "Five MSTORE sites and %d terminators needed one of these two values read back from the listing; logging them removes the last inferred input of the replay." % tabl,
  "priority": "low"},
]
leadResults = [
 {"leadId": "L-1238", "outcome": "cleared",
  "answer": "The shipped JUMPI, JUMP, FallThrough, RETURN and STOP emitters ran on the logged states of all 128 un-entered value blocks and equal the clang listing exactly (condition code, compare operands, targets, rbp and counter adjustments, final stack offsets). 256,000 terminator runs, 22,400 runs over all 10 comparison codes and 16 flag states, and 140,000 whole-block runs of the six mulDiv blocks and the rounding block matched pyevm.py, with each branch side at FullMath.sol:30, :33 and :112 reached and the denominator equal to and one either side of prod1."},
 {"leadId": "L-1234", "outcome": "inconclusive",
  "answer": "381 of the 473 sites ran from the package with equal streams: the 128 terminators and %d memory, context and SIGNEXTEND sites (SIGNEXTEND also on 20,000 value runs). The %d KECCAK256, SLOAD, SSTORE, TLOAD and LOG sites are emitted by inlined templates and were not run; a lead records them." % (nrun3, ninl)},
]
out = {"unit": "theme-monad-gcc-terminators", "profiles": [], "findings": [], "cleared": cleared, "leads": leads, "leadResults": leadResults}
p = '/home/user/v4-core/research/network-risk/cycles/033/theme-monad-gcc-terminators.research.json'
json.dump(out, open(p, 'w'), indent=1)
print('wrote', p, len(cleared), 'cleared', nrun3, ninl, faults)
