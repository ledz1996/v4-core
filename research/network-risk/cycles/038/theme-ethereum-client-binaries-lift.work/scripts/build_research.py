"""Cycle 38: builds theme-ethereum-client-binaries-lift.research.json from the outputs in out/."""
import glob, json, os
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = 'research/network-risk/cycles/038/theme-ethereum-client-binaries-lift.work/'
OUT = os.path.join(os.path.dirname(W), 'theme-ethereum-client-binaries-lift.research.json')
NET = json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))
NET = NET if isinstance(NET, list) else NET['networks']
ALL = [n['chainId'] for n in NET]


def agg(pattern, key=None):
    tot = {}
    for f in sorted(glob.glob(os.path.join(W, pattern))):
        d = json.load(open(f))
        k = key(d, f) if key else 'all'
        t = tot.setdefault(k, {'cases': 0, 'mismatches': 0, 'errors': 0, 'files': 0, 'steps': 0, 'ops': set()})
        t['cases'] += d['cases']; t['mismatches'] += d['mismatches']; t['errors'] += d['errors']; t['files'] += 1
        t['steps'] += d.get('steps', 0); t['ops'] |= set(d.get('byOp', {}))
    return tot


h = agg('out/runs/*.json', lambda d, f: d['target'])
loop = agg('out/loop/*.json').get('all', {'cases': 0, 'mismatches': 0, 'errors': 0, 'files': 0, 'steps': 0, 'ops': set()})
reth = agg('out/reth/*.json').get('all', {'cases': 0, 'mismatches': 0, 'errors': 0, 'files': 0, 'steps': 0, 'ops': set()})


def fmt(n): return '{:,}'.format(n)


def hs(t):
    x = h.get(t, {'cases': 0, 'mismatches': 0, 'errors': 0, 'files': 0})
    return '%s cases in %d files, %d mismatches, %d model errors' % (fmt(x['cases']), x['files'], x['mismatches'], x['errors'])


def jd(f):
    p = os.path.join(W, 'out/jd', f)
    return json.load(open(p)) if os.path.exists(p) else None


faults = {}
for f in sorted(glob.glob(os.path.join(W, 'out/faults/*.json'))) + sorted(glob.glob(os.path.join(W, 'out/rarith-fault-*.json'))):
    d = json.load(open(f))
    faults[os.path.basename(f)[:-5]] = (d['mismatches'], d['errors'], d['cases'])
fl = '; '.join('%s %d mismatches %d errors' % (k, a, b) for k, (a, b, c) in faults.items())
jdf = []
for f in ('erigon-amd64-opcode.json', 'erigon-amd64-bit.json', 'erigon-amd64-sse.json'):
    d = jd(f)
    if d:
        jdf.append('%s: %d bitmap and %d validJumpdest mismatching programs' % (f[:-5], len(d['bitmapMismatch']), len(d['validMismatch'])))
for f in ('geth-amd64-opcode.json', 'geth-amd64-bit.json', 'geth-arm64-opcode.json', 'geth-arm64-bit.json'):
    d = jd(f)
    if d:
        jdf.append('%s: %d mismatching program(s), PoolManager destinations accepted %d of 610' % (f[:-5], d['validMismatchPrograms'], d['poolmanager']['modelValidDests']))
for f in sorted(glob.glob(os.path.join(W, 'out/jd/reth-*-fault-*.json'))):
    d = json.load(open(f)); jdf.append('%s: %d mismatches %d errors' % (os.path.basename(f)[:-5], d['mismatches'], d['errors']))
rj = {k: jd('reth-%s.json' % k) for k in ('avx512', 'avx2', 'none')}
ej = jd('erigon-amd64-none.json'); gj = {a: jd('geth-%s-none.json' % a) for a in ('amd64', 'arm64')}
live = json.load(open(os.path.join(W, 'out/live.json')))
conv = {t: json.load(open(os.path.join(W, 'out/conv-%s.json' % t))) for t in ('erigon-amd64', 'geth-amd64')}

GETH_DL = 'https://gethstore.blob.core.windows.net/builds/geth-linux-amd64-1.17.10-1df30b18.tar.gz'
GETH_DL_ARM = 'https://gethstore.blob.core.windows.net/builds/geth-linux-arm64-1.17.10-1df30b18.tar.gz'
RETH_DL = 'https://github.com/paradigmxyz/reth/releases/download/v2.11.0/reth-v2.11.0-x86_64-unknown-linux-gnu.tar.gz'
ERI_DL = 'https://github.com/erigontech/erigon/releases/download/v3.8.2/erigon_v3.8.2_linux_amd64.tar.gz'
GEN = 'https://raw.githubusercontent.com/ethereum/go-ethereum/v1.17.10/core/vm/interpreter_gen.go'
ERUN = 'https://raw.githubusercontent.com/erigontech/erigon/v3.8.2/execution/vm/vm_run_gen.go'
RREL = 'https://raw.githubusercontent.com/paradigmxyz/reth/v2.11.0/.github/workflows/release.yml'
RLOCK = 'https://raw.githubusercontent.com/paradigmxyz/reth/v2.11.0/Cargo.lock'
SRCREF = 'src/libraries/FullMath.sol:24-73, src/libraries/UnsafeMath.sol:14, src/libraries/TickBitmap.sol:20-73, src/libraries/BitMath.sol:16-45, src/libraries/TickMath.sol:61-111'

cleared = []


def C(chains, check, result, source, lens='L1'):
    cleared.append({'chainIds': chains, 'lens': lens, 'check': check, 'result': result, 'source': source})


C([1], 'Task 1: release artefacts of the three Ethereum clients the public endpoints name, fetched into a new dl/ and read as data only (readelf, objdump, nm, strings, go version -m, own Python), with build information.',
  'geth v1.17.10 linux amd64 and arm64 (tarballs geth-linux-{amd64,arm64}-1.17.10-1df30b18): the MD5 values published on geth.ethereum.org/downloads, 944f19920a2457cc62a852229149a21d and 465222ecefa313f3df23331281d8d909, equal the files; the .asc signatures were fetched and not verified, since no signing key was fetched. Build info: go1.27.3, -pgo=default.pgo, tags urfave_cli_no_docs,ckzg,osusergo,netgo, CGO_ENABLED=1, GOAMD64=v1 or GOARM64=v8.0, vcs.revision 1df30b18d9ed35ee9d28ffd4648442c2204554ad, not modified, holiman/uint256 v1.3.2. The binaries are stripped; function names and ranges come from .gopclntab with the text base read from runtime.firstmoduledata (amd64 0x401bc0, arm64 0x400870). '
  'reth v2.11.0 x86_64 (54,478,574 byte tarball, sha256 of the binary not published separately; .asc fetched, not verified): rustc 1.99.1 (58cf8f9c3 2026-10-13), commit b9abbcc1b982755baa9021e6874e2e58936ca65f, build features asm_keccak, jemalloc, keccak_cache_global, min_trace_logs, otlp, otlp_logs, evm2 rev 66687c18 and ruint 1.21.1 (Cargo.lock), and the release workflow builds it with the maxperf profile and -C target-cpu=x86-64-v3 -C target-feature=+pclmulqdq. The handler code uses AVX, AVX2, BMI2 (mulx, shlx, shrx) and LZCNT and no ADX; the jump analysis also has an AVX-512 VBMI kernel chosen at run time. The LLVM compiler of F-129 is linked (revmc builtins present). '
  'erigon v3.8.2 linux amd64 (555,663,020 byte tarball; the checksums.txt inside it lists bff92c1a...8022 for erigon, which the file has; no checksum is published outside the archive): go1.27.4, tags nosqlite,noboltdb, CGO_ENABLED=1, GOAMD64=v2, symbols kept, commit 8a3f3b2c7a34429f101e9a9d05b861120c8e4d77 in its strings, and holiman/uint256 pinned at the untagged commit v1.3.3-0.20260228135838-087f4b32f234. That commit has the same div.go and mod.go as v1.3.2 and rewrites WriteToSlice, the shift helpers and adds in-place methods. The endpoints report Geth/v1.17.10-stable-1df30b18 go1.27.3, reth/v2.11.0-b9abbcc and erigon/3.8.2-8a3f3b2c go1.27.4, the same builds. arm64 artefacts of reth and erigon were not fetched.',
  GETH_DL + '; ' + GETH_DL_ARM + '; https://geth.ethereum.org/downloads; ' + RETH_DL + '; ' + ERI_DL + '; ' + RREL + ' lines 100-102; ' + RLOCK + '; https://raw.githubusercontent.com/holiman/uint256/087f4b32f234/uint256.go; ' + R + 'out/buildinfo-*.txt, dl/build/all-*.txt')
C([1], 'geth v1.17.10 interpreter structure in the release binary: which code an untraced call or block import runs.',
  'Untraced execution runs (*EVM).execUntraced (interpreter_gen.go:18, 21,088 bytes on amd64). Because the release is built with a PGO profile, the bodies of ADD, MUL, SUB, DIV, MULMOD, SIGNEXTEND, LT, GT, SLT, SGT, EQ, ISZERO, AND, OR, NOT, SHL, SHR, SAR, the PUSH and DUP and SWAP cases, JUMP and JUMPI are inlined into that one function and are different machine code from the out-of-line op functions; MUL, DIV, MULMOD, SIGNEXTEND, SLT, SGT, SHL, SHR and SAR still call holiman/uint256 routines, and validJumpdest is called. SDIV, MOD, SMOD, ADDMOD, EXP, BYTE and the rest go through the per-fork table to the out-of-line handlers. Earlier cycles ran only the out-of-line handlers of geth-family builds, so the inlined copies had never run from a binary.',
  GEN + '; ' + R + 'dis/geth-execUntraced-amd64.s, scripts/callmap.py')
C([1], 'Task 2, geth v1.17.10 amd64: the whole generated loop execUntraced run in the x86-64 model on programs of 250 cases each (PUSH1..4, 8, 20, 32 operands, the opcode, the result left on the stack, STOP), with the table ops dispatched to the binary\'s own out-of-line handlers.',
  'Every stacked result equals the Python integer: %s cases over %d files (battery, targeted, v4shapes, c27, ruint121, provevec, pow2, random with seeds 310731_02, 17999, 20261127, 381128_01), %d mismatches, %d model errors, %s emulated instructions, opcodes %s. The words reach FullMath.mulDiv (%s), the sign and shift code of TickMath, TickBitmap and BitMath, and UnsafeMath through the same instructions.' % (fmt(loop['cases']), loop['files'], loop['mismatches'], loop['errors'], fmt(loop['steps']), ', '.join(sorted(loop['ops'])), 'src/libraries/FullMath.sol:24, 48, 62, 67, 73'),
  R + 'scripts/gloop.py, scripts/gdrive.py, out/loop/*.json; ' + SRCREF)
C([1], 'Task 2: the out-of-line handlers of MULMOD, ADDMOD, MUL, DIV, SDIV, MOD, SMOD, EXP, SHL, SHR, SAR, BYTE, SIGNEXTEND and the comparisons of geth v1.17.10 (amd64 and arm64) and erigon v3.8.2 (amd64), with every holiman/uint256 function of each binary, in the cycle 31 models (erigon layout added: Stack inline in CallContext at +0x230, top at +0x8230, handler signature (pc, evm, scope) (pc, []byte, error)).',
  'geth amd64: %s. geth arm64: %s. erigon amd64: %s. Sets: battery, targeted, c27, v4shapes, random and direct comparisons (cycle 31 seeds), ruint121 (the ruint 1.21.0 fault shapes of cycle 17, seed 17999), provevec (cycle 36, seed 20261127) and pow2 (every power of two and its neighbours as divisor of DIV, MOD, SDIV and SMOD, and EXP with base 2, 2^k and 2^256-1, seed 381128_01). Erigon 3.8.2 has no power-of-two or reciprocal shortcut in its released DIV, MOD or MULMOD handlers: opDiv calls uint256 Div and opMulmod calls MulMod; its only special cases are the base 0, 1 and 2 branches of opExp, which the pow2 set covers. The reciprocal paths of F-165 are on erigon main only.' % (hs('geth-amd64'), hs('geth-arm64'), hs('erigon-amd64')),
  R + 'scripts/drive.py, models.py, targets.py, out/runs/*.json; https://raw.githubusercontent.com/erigontech/erigon/v3.8.2/execution/vm/instructions.go lines 75-146, 305-309')
C([1], 'Task 2, reth v2.11.0 x86_64: the 25 arithmetic, comparison, bitwise and shift handlers of both handler families of the binary\'s instruction tables, with every function they reach.',
  'The R_X86_64_RELATIVE relocations hold 26 instruction tables in two families (X 0x7f2fdd0..0x7f35dd0, Y 0x7f375d0..0x7f3d5d0); within a family every fork table points these opcodes at one handler, or at the undefined handler before the opcode existed. Handler ABI read from ADD: rdi packs pc<<11 with the stack length, rsi the stack, rdx the gas, status byte at context+0x147. Both families give the Python word on %s cases (%d files, battery, targeted, v4shapes, c27, ruint121, provevec, pow2, random), %d mismatches, %d model errors, %s emulated instructions, with the pc and stack length checked after every call.' % (fmt(reth['cases']), reth['files'], reth['mismatches'], reth['errors'], fmt(reth['steps'])),
  R + 'scripts/rrel.py, rarith.py, extract2.py, dl/build/reth/arith.s, out/reth/*.json; ' + RLOCK)
C([1], 'Byte conversion routines of the integer library linked into geth and erigon (word to memory, memory, calldata and PUSH bytes to word), since erigon pins an untagged uint256 commit that rewrites WriteToSlice.',
  'WriteToSlice for every destination length 0..40, PutUint256, SetBytes for every length 0..40 and SetBytes1..32 on 45 words (seed 381128_06): erigon %d cases and geth %d cases, 0 mismatches, 0 errors. MSTORE, MLOAD, CALLDATALOAD and PUSH therefore move the words that src/libraries/Hooks.sol and the settlement code read and write the same way on both builds.' % (conv['erigon-amd64']['cases'], conv['geth-amd64']['cases']),
  R + 'scripts/conv.py, out/conv-erigon-amd64.json, out/conv-geth-amd64.json; https://raw.githubusercontent.com/holiman/uint256/087f4b32f234/uint256.go')
gn = gj['amd64']
C([1], 'Task 3: jump destination analysis of each binary on the PoolManager runtime (research/network-risk/build/PoolManager.json, 24,009 bytes), cuts inside its last PUSH instructions, programs that end inside PUSH1..PUSH32 and random programs, and where the analysis is cached.',
  'geth amd64 and arm64 (codeBitmapInternal and (*Contract).validJumpdest with Code at +0x50 and analysis at +0x38): %s programs each, no bitmap or destination mismatch; on the PoolManager the model accepts 610 destinations and rejects the 29 JUMPDEST bytes inside push data, and all 418 pushed jump targets are valid. erigon amd64: both kernels the binary can select, codeBitmapSSE4 (its assembly routine jumpdestBitmapSSE4 for 32-byte steps plus the inlined tail) and codeBitmapGeneric, on %d program runs, then validJumpdest on %s destinations: no mismatch, 610 marked and 29 rejected on the PoolManager by both. reth amd64: the AVX-512 VBMI kernel, the AVX2 kernel (the baseline of this x86-64-v3 build, so no SSE4.1 kernel exists) and the scalar tail, %s, %s and %s programs, 0 mismatches, 0 errors, every instruction of the two vector kernels reached. Caches: geth keeps the bitmap in a layered map keyed by the 32-byte code hash (jumpdests.go), local per EVM and shared, and analyses code without a hash per Contract; erigon keeps it in jumpDestCache, a 64 MB LRU keyed by the code hash bytes and never unwound (contract.go jumpdestAnalysis); reth builds it lazily once per bytecode object (0x42cdb30 takes a once-cell), and its bytecode cache is keyed by code hash as cycle 34 read.' % (
      gn['programs'] if gn else 'n/a', ej['programs'] if ej else 0, fmt(ej['validCalls']) if ej else 0,
      rj['avx512']['cases'] if rj['avx512'] else 'n/a', rj['avx2']['cases'] if rj['avx2'] else 'n/a', rj['none']['cases'] if rj['none'] else 'n/a'),
  R + 'scripts/jd.py, ejd.py, rjd.py, out/jd/*.json; https://raw.githubusercontent.com/ethereum/go-ethereum/v1.17.10/core/vm/jumpdests.go; https://raw.githubusercontent.com/erigontech/erigon/v3.8.2/execution/vm/contract.go; https://raw.githubusercontent.com/erigontech/erigon/v3.8.2/execution/vm/analysis_amd64.go')
C([1], 'Task 5: planted faults show that the checks see a fault in each binary.',
  'Handler and loop faults: %s. Jump analysis faults: %s. Every planted fault gave mismatches or failed runs; the no-fault runs gave none. The cmpskip comparison fault could not be planted in erigon\'s opLt, whose loads do not have the indexed pattern the planter searches for; the limb, carry and shift faults were planted there instead.' % (fl, '; '.join(jdf)),
  R + 'scripts/faults.py, gfaults.py, rfaults.json, rjd_faults.json, out/faults/*.json, out/rarith-fault-*.json, out/jd/*-fault-*.json, out/jd/*-opcode.json, out/jd/*-bit.json, out/jd/erigon-amd64-sse.json')
lr = {r['rpc']: r for r in live['results']}
C([1], 'Task 5, live: 2,000 of the model vectors (seed 381128_05) by eth_call with state override to one endpoint per client release, bracketed by web3_clientVersion.',
  '; '.join('%s answered %s before and %s after: %d of 2,000 run, %d mismatches%s' % (u, r['clientVersionBefore'], r['clientVersionAfter'], r['ran'], r['mismatchCount'],
            ', refused: ' + r['errors'][0][1][:120] if r['errors'] else '') for u, r in lr.items()) + '. The erigon 3.8.2 endpoint refuses eth_call for free use; the refusal was recorded and not worked around, so erigon 3.8.2 is tested from its binary only.',
  R + 'scripts/live.py, out/live.json')
C([1], 'Task 6: what a difference would mean for an ordinary account.',
  'No handler, loop, conversion or jump analysis run of the three release binaries differs from the specification, so no line of src/ computes or decides anything else on these builds, and there is nothing an ordinary account could gain or lock through them. If one client had differed, a block it built would be rejected by the other two, and its eth_call answers would differ from the chain the majority writes; this was not observed.',
  SRCREF + '; src/libraries/SqrtPriceMath.sol, src/libraries/SwapMath.sol, src/libraries/Pool.sol')
others = [c for c in ALL if c != 1]
C(others, 'Scope of this theme on the other 20 networks.',
  'The theme reads the release binaries of Ethereum\'s own execution clients. The other 20 networks run their own client builds, which cycles 28 to 37 lifted or read; this theme does not apply to them and adds nothing there.',
  'research/network-risk/cycles/038/plan.json (unit theme-ethereum-client-binaries-lift)')

leads = [
    {'chainIds': [1], 'lens': 'L1', 'question': 'Run the transient storage, persistent storage and journal revert code of the geth v1.17.10, erigon v3.8.2 and reth v2.11.0 release binaries on the nested-frame sequences of cycles 32 to 37 (Task 4 of this unit, not done this cycle).', 'why': 'The PoolManager keeps the lock, delta count, deltas and synced currency in transient storage (src/libraries/Lock.sol:13-25, NonzeroDeltaCount.sol:14-32, CurrencyDelta.sol:21-39, CurrencyReserves.sol:17-36); these Ethereum binaries have had arithmetic and jump analysis run, not their journals. geth is stripped, so the itabs the cycle 32 scripts find by symbol must be found by pclntab and type data instead.', 'priority': 'high'},
    {'chainIds': [1], 'lens': 'L1', 'question': 'Run erigon v3.8.2\'s per-frame storage read cache from the binary on the cycle 36 reentry sequences, with a planted stamp that does not move on a nested write.', 'why': 'F-165 and cycle 36 cleared the cache from source and a model; it has not run from the shipped machine code and no erigon 3.8.2 endpoint serves eth_call.', 'priority': 'high'},
    {'chainIds': [1], 'lens': 'L1', 'question': 'Run erigon v3.8.2\'s generated loop (*EVM).run (vm_run_gen.go) whole, as gloop.py does for geth: its inlined ADD, SUB, LT, GT, EQ, AND, ISZERO, PUSH, DUP and SWAP cases are different machine code from the handlers that ran.', 'why': 'MUL and DIV in that loop call the uint256 routines that ran, but the inlined comparisons decide the tick and price checks in Pool.swap.', 'priority': 'medium'},
    {'chainIds': [1], 'lens': 'L1', 'question': 'Fetch and run the aarch64 release binaries of reth v2.11.0 and erigon v3.8.2, and the Nethermind and Besu releases, which no public endpoint names.', 'why': 'Only geth arm64 was run this cycle; minority clients still validate blocks.', 'priority': 'low'},
]
res = {'unit': 'theme-ethereum-client-binaries-lift', 'profiles': [], 'findings': [], 'cleared': cleared, 'leads': leads, 'leadResults': []}
json.dump(res, open(OUT, 'w'), indent=1)
print(OUT, len(cleared), 'cleared', len(leads), 'leads')
