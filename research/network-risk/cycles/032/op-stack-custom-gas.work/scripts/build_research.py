import json, os
W = '/home/user/v4-core/research/network-risk/cycles/032/op-stack-custom-gas.work'
O = W + '/out'
J = lambda f: json.load(open(os.path.join(O, f)))
bat, tgt, pm, pm2, sw = J('battery.json'), J('targeted.json'), J('pmdiff.json'), J('pmdiff2.json'), J('swaps.json')
pin = J('pinned-stakely.json')

def short(b):
    return b.split('/')[1]
pin_txt = '; '.join('%s %d vectors (%d battery, %d targeted), %d mismatches' % (
    short(b), s['battery']['vectors'] + s['targeted']['vectors'], s['battery']['vectors'], s['targeted']['vectors'],
    s['battery']['mismatches'] + s['targeted']['mismatches']) for b, s in pin['byBuild'].items())
pin_total = sum(s['battery']['vectors'] + s['targeted']['vectors'] for s in pin['byBuild'].values())

GH_XL = 'https://raw.githubusercontent.com/okx/xlayer-reth/refs/heads/main/'
LOCK = {
 'xl007': 'https://raw.githubusercontent.com/okx/xlayer-reth/refs/tags/v0.0.7/Cargo.lock',
 'xl0073': 'https://raw.githubusercontent.com/okx/xlayer-reth/refs/tags/v0.0.7.3/Cargo.lock',
 'xlmain': GH_XL + 'Cargo.lock',
 'celo1010': 'https://raw.githubusercontent.com/celo-org/celo-kona/refs/tags/celo/reth-v1.0.10/Cargo.lock',
 'celomain': 'https://raw.githubusercontent.com/celo-org/celo-kona/refs/heads/main/Cargo.lock',
}
CRATE = 'https://static.crates.io/crates/sha3-asm/sha3-asm-0.1.8.crate'
RPC_NOTE = 'web3_clientVersion on 2026-11-27 08:2x UTC'

profiles = [
 {'chainId': 42220, 'lens': 'L1',
  'summary': 'The celo-reth pins are unchanged: no tag after celo/reth-v1.0.10 exists, and the main branch still carries revm 42.0.1 with ruint 1.20.0, which no release ships. stakely.io now answers from 3cbf835 and 74cc8bb more than from 7680d6d, and all four of its builds returned the specified word on %d pinned vectors.' % pin_total,
  'deltas': [
   {'delta': 'In 40 single calls on 2026-11-27 stakely.io answered reth/v2.2.0-3cbf835 39 times and 74cc8bb once, while in 310 bracketed eth_call batches of the same hour it answered 74cc8bb 154, 7680d6d 98, 3cbf835 34 and 06140ff 24 times. The rotation weights move from hour to hour; 3cbf835 (celo/reth-v1.0.3) is still served.', 'source': 'https://celo-json-rpc.stakely.io (web3_clientVersion and bracketed eth_call batches, 2026-11-27, cycles/032/op-stack-custom-gas.work/out/pinned-stakely.json)', 'relevance': 'low'},
   {'delta': 'Probes for celo/reth-v1.0.11, v1.0.12, v1.1.0, v1.0.11-rc.1, v1.1.0-rc.1 and v2.0.0 return 404, and v1.0.10 returns 200. v1.0.10 pins revm 38.0.0 and revm-interpreter 35.0.1 from celo-org/revm bd28f942 with ruint 1.20.0; main pins revm 42.0.1, revm-interpreter 42.0.0, ruint 1.20.0, alloy-primitives 1.7.3, fixed-cache 0.1.10 and sha3-asm 0.1.8 on reth 2.5.2 4e0169d3.', 'source': LOCK['celomain'], 'relevance': 'low'},
  ]},
 {'chainId': 42220, 'lens': 'L2', 'summary': 'Nothing new on transaction boundaries or state changes outside the EVM this cycle.', 'deltas': []},
 {'chainId': 42220, 'lens': 'L4', 'summary': 'Nothing new on precompiles or predeploys this cycle; the transfer precompile and the engine precompile cache were read in cycle 30 and no pinned crate has moved since.', 'deltas': []},
 {'chainId': 42220, 'lens': 'L6',
  'summary': 'No Celo upgrade is announced: the network notices list only the op-geth end of support (mainnet 22 July 2026) and the CL P2P sync deprecation. OP Upgrade 22 (Lagoon) names OP Mainnet, Unichain, Ink and Soneium only.',
  'deltas': [
   {'delta': 'Every public Celo provider reached that names a build runs celo-reth: forno, publicnode, ankr, 1rpc and tatum answered 74cc8bb on every call, onfinality 7680d6d, stakely four builds. No op-geth answer was seen in this sample, which says nothing about the sequencer.', 'source': 'https://celo-json-rpc.stakely.io, https://celo.api.onfinality.io/public, https://rpc.ankr.com/celo, https://1rpc.io/celo, https://celo-mainnet.gateway.tatum.io, https://celo.publicnode.com (' + RPC_NOTE + ', six calls each)', 'relevance': 'low'},
  ]},
 {'chainId': 196, 'lens': 'L1',
  'summary': 'The xlayer-reth pins are unchanged: v0.0.7 and v0.0.7.3 lock okx/reth 81573d2c, main locks f60420a, and all three keep revm 40.0.3, revm-interpreter 37.0.3, ruint 1.18.0, alloy-primitives 1.6.0, fixed-cache 0.1.10 and sha3-asm 0.1.8. The released Docker image is built with no RUSTFLAGS, so it assembles the baseline keccak1600-x86_64 routine; only the maxperf just recipes with target-cpu=native select keccak1600-avx512vl.',
  'deltas': [
   {'delta': 'DockerfileOp declares ARG RUSTFLAGS="" and builds with cargo build --profile $BUILD_PROFILE, and the justfile build-docker recipe passes only VERGEN build arguments and removes .cargo for production builds, so the official image targets baseline x86-64. sha3-asm 0.1.8 build.rs picks keccak1600-avx512vl only when the target has the avx512vl feature and is not Zen 5.', 'source': GH_XL + 'DockerfileOp', 'relevance': 'low'},
   {'delta': 'sha3-asm 0.1.8 patches keccak1600-avx512vl.pl with keccak1600-avx512vl-cfi.patch: the patch adds the perlasm translator preamble, CFI directives and a push and pop of rbp around SHA3_absorb and SHA3_squeeze. The pushes happen before mov %rsp,%r11 and the pops after lea (%r11),%rsp, and the absorb frame is still realigned with and $-32,%rsp, so as read the patch changes no register or memory the permutation uses.', 'source': CRATE, 'relevance': 'low'},
   {'delta': 'No tag after v0.0.7.3 exists (v0.0.7.4, v0.0.7.4-rc.1, v0.0.7.3-rc.2, v0.0.8, v0.0.8-rc.1 and v0.1.0 return 404). rpc.xlayer.tech and xlayerrpc.okx.com still answer reth/v2.3.0-f60420a xlayer/v0.0.7.', 'source': LOCK['xlmain'], 'relevance': 'none'},
  ]},
 {'chainId': 196, 'lens': 'L2', 'summary': 'Nothing new on transaction boundaries or state changes outside the EVM this cycle.', 'deltas': []},
 {'chainId': 196, 'lens': 'L4', 'summary': 'Nothing new on precompiles or predeploys this cycle; the precompile cache of okx/reth f60420a was read in cycle 30 and the pin has not moved.', 'deltas': []},
 {'chainId': 196, 'lens': 'L6', 'summary': 'No X Layer hard fork is announced after the 10 November 2026 fork. OP Upgrade 22 (Lagoon, with sequencer defined metering and the 0x7D post-execution transaction) does not list X Layer, and its sequencer rebate changes gas paid, not what a PoolManager call returns.',
  'deltas': [
   {'delta': 'OP Stack Upgrade 22 activates Lagoon on OP Mainnet, Unichain, Ink and Soneium only; it adds sequencer defined metering, a 0x7D post-execution transaction at the end of a block and an opGasRefund receipt field. op-reth storage v1 reaches end of support on 26 January 2027.', 'source': 'https://docs.optimism.io/notices/upgrade-22.md', 'relevance': 'none'},
  ]},
]

cleared = [
 {'chainIds': [42220, 196], 'lens': 'L1',
  'check': 'Standard reruns on 2026-11-27 into the cycle 32 work directory through forno.celo.org and rpc.xlayer.tech: battery.py, targeted.py, pmdiff.py (250 scripts), pmdiff2.py (300 scripts), swaps.py and replay.py.',
  'result': 'Both chains returned the specified word on all %d battery and %d targeted vectors; all 250 and 300 scripts are byte-identical to the Ethereum reference; Celo 96 and X Layer 546 newest mined swaps satisfy the tick relation, every paired swap fits a single step or replays (7 Celo multi-step swaps replayed to the unit, up to 23 steps). The forno answers are not pinned to one build.' % (bat['vectors'], tgt.get('vectors', 85544)),
  'source': 'cycles/032/op-stack-custom-gas.work/out/battery.json, targeted.json, pmdiff.json, pmdiff2.json, swaps.json, replay.json (eth_call to https://forno.celo.org and https://rpc.xlayer.tech)'},
 {'chainIds': [42220], 'lens': 'L1',
  'check': 'The battery and targeted vector sets on stakely.io with every eth_call batch sent between two web3_clientVersion calls, so each result is tied to one celo-reth build (scripts/pinned.py).',
  'result': 'All 310 batches were answered whole by one build, with no error: ' + pin_txt + '. 3cbf835 (celo/reth-v1.0.3) is the build cycle 30 reached only through 307 batches of another set; 7680d6d, the onfinality build, got 58,800 vectors here because onfinality itself refused the batch with HTTP rate limit code -32029.',
  'source': 'https://celo-json-rpc.stakely.io (bracketed eth_call batches, 2026-11-27, cycles/032/op-stack-custom-gas.work/out/pinned-stakely.json)'},
 {'chainIds': [196], 'lens': 'L1',
  'check': 'Which keccak routine the released X Layer node runs for KECCAK256, which hashes every pool id (src/types/PoolId.sol:14, 160 bytes, two Keccak blocks), position key (src/libraries/Position.sol:60, 58 bytes), tick bitmap word slot (src/libraries/TickBitmap.sol:70, 64 bytes) and transient delta slot (src/libraries/CurrencyDelta.sol:14, 64 bytes).',
  'result': 'The official image is built with RUSTFLAGS empty, so sha3-asm 0.1.8 assembles keccak1600-x86_64, the routine the endpoint tests in cycles 28 to 32 have exercised with no mismatch. The AVX-512VL routine runs only on nodes built from source with the maxperf recipes on an AVX-512 machine, and the sha3-asm patch to it is bookkeeping only as read. Its output was not run (L-1202 stays open).',
  'source': GH_XL + 'DockerfileOp and ' + GH_XL + 'justfile; ' + CRATE},
 {'chainIds': [42220, 196], 'lens': 'L1',
  'check': 'Whether any celo-reth or xlayer-reth tag after the builds the endpoints run moved the revm, revm-interpreter or ruint pins (lead L-1230).',
  'result': 'No new tag exists for either client. The Cargo.lock files of xlayer-reth v0.0.7, v0.0.7.3 and main agree on revm 40.0.3, revm-interpreter 37.0.3 and ruint 1.18.0; celo/reth-v1.0.10 pins revm 38.0.0 (celo-org/revm bd28f942) and ruint 1.20.0, and celo-kona main revm 42.0.1 with ruint 1.20.0. None pins ruint 1.21.0, the withdrawn release with the MULMOD fault.',
  'source': LOCK['xl007'] + ', ' + LOCK['xl0073'] + ', ' + LOCK['xlmain'] + ', ' + LOCK['celo1010'] + ', ' + LOCK['celomain']},
 {'chainIds': [42220, 196], 'lens': 'L6',
  'check': 'Upcoming forks within six months, assumed to ship, for Celo and X Layer, and OP Upgrade 22 (Lagoon).',
  'result': 'Celo lists no upgrade after Jovian (31 March 2026) and only the op-geth end of support and the CL sync deprecation as active notices. X Layer announces no fork after 10 November 2026. Lagoon names neither chain; if it were adopted, its post-execution transaction and sequencer rebate change gas refunds after execution and do not change an opcode result or a PoolManager return value. The Karst transaction gas cap was cleared in an earlier cycle.',
  'source': 'https://docs.celo.org/operate/notices/overview.md; https://docs.optimism.io/notices/upgrade-22.md'},
]

leads = [
 {'chainIds': [196], 'lens': 'L1', 'question': 'Run keccak1600-avx512vl.pl as patched by sha3-asm 0.1.8 against a reference keccak for lengths 0 to 1,100, with 58, 64 and 160 byte inputs and the 135 to 137 and 271 to 273 block boundaries, on a machine where assembling it is permitted.', 'why': 'Only X Layer nodes built from source with target-cpu=native on AVX-512 hardware run it; the shipped image does not. A wrong hash there would make such a node disagree on every PoolManager slot, which is a node fault, not a fund path.', 'priority': 'low'},
]

leadResults = [
 {'leadId': 'L-1230', 'outcome': 'cleared', 'answer': 'On 2026-11-27 forno.celo.org answered reth/v2.2.0-74cc8bb and rpc.xlayer.tech reth/v2.3.0-f60420a xlayer/v0.0.7. battery.py (99,985), targeted.py (85,544), pmdiff.py (250) and pmdiff2.py (300) all match on both. No tag after celo/reth-v1.0.10 or xlayer-reth v0.0.7.3 exists, and the Cargo.lock files of every tag and both main branches keep the revm, revm-interpreter and ruint pins recorded in OPCODES.md (X Layer ruint 1.18.0, Celo ruint 1.20.0).'},
 {'leadId': 'L-1203', 'outcome': 'inconclusive', 'answer': 'The sequencer build is not published. Of the providers that name a build, forno, publicnode, ankr, 1rpc and tatum serve 74cc8bb, onfinality 7680d6d and stakely four builds including 3cbf835; tenderly and thirdweb hide the build. All four stakely builds returned the specified word on ' + str(pin_total) + ' pinned vectors. The question concerns operator conduct only.'},
 {'leadId': 'L-1202', 'outcome': 'inconclusive', 'answer': 'Generating and assembling the routine was again refused by this session\'s permission policy. Read instead: the sha3-asm 0.1.8 patch adds only CFI and an rbp frame, and the official X Layer image builds with empty RUSTFLAGS, so it runs keccak1600-x86_64; only maxperf source builds on AVX-512 hardware run the VL routine. Restated as a new lead.'},
 {'leadId': 'L-1162', 'outcome': 'inconclusive', 'answer': 'Not searched this cycle, whose focus was the interpreter. F-144 concerns the CIP-64 fee refund, which no PoolManager line reads.'},
 {'leadId': 'L-1067', 'outcome': 'inconclusive', 'answer': 'Not run this cycle; the Celo replay window beyond 2,479 transactions needs more cores than this session has, and the cycle focus was the interpreter. The 7 newest Celo multi-step swaps replayed to the unit in replay.py.'},
]

r = {'unit': 'op-stack-custom-gas', '_lenses': ['L1', 'L2', 'L4', 'L6'], 'profiles': profiles, 'findings': [], 'cleared': cleared, 'leads': leads, 'leadResults': leadResults}
json.dump(r, open('/home/user/v4-core/research/network-risk/cycles/032/op-stack-custom-gas.research.json', 'w'), indent=1)
print('ok')
