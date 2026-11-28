"""Cycle 38 arbitrum-family: assemble arbitrum-family.research.json from the files in this work directory."""
import json, os
R = '/home/user/v4-core/research/network-risk'
W = R + '/cycles/038/arbitrum-family.work'
WR = 'research/network-risk/cycles/038/arbitrum-family.work'
J = lambda p: json.load(open(os.path.join(W, p)))

def log(p):
    return open(os.path.join(W, p)).read()

def line(p, cid):
    for l in log(p).splitlines():
        if l.strip().startswith(str(cid) + ' '):
            return ' '.join(l.split())
    return 'no line'

def pin(p):
    j = J(p)
    by = {k.replace('nitro/v3.13.0-rc.9+b72783f-20261116T155937Z/', '').replace('nitro/', ''): v for k, v in j['byBuild'].items()}
    units = sum(v['units'] for v in j['byBuild'].values())
    mm = sum(v['mismatches'] for v in j['byBuild'].values())
    return j, by, units, mm

arb_pv, _, arb_pv_u, arb_pv_m = pin('out/pin-arb1-provevec.json')
arb_ops, _, arb_ops_u, arb_ops_m = pin('out/pin-arb1-ops.json')
arb_pm, _, arb_pm_u, arb_pm_m = pin('out/pin-arb1-pmdiff.json')
arb_pm2, _, arb_pm2_u, arb_pm2_m = pin('out/pin-arb1-pmdiff2.json')
rh_pv, rh_pv_by, rh_pv_u, rh_pv_m = pin('out/rounds-rh-provevec.json')
rh_ops, rh_ops_by, rh_ops_u, rh_ops_m = pin('out/rounds-rh-ops.json')
pv = J('raw/provevec.json')['urls']
prec = J('raw/precscan-final.json')
l5 = J('raw/l5.json')
arbos = J('raw/arbos_state.json')
ra = J('raw/replay-archive.json')
ra_ok = sum(1 for x in ra['results'] if x.get('ok'))

def armix(by):
    a = sum(v['batches'] for k, v in by.items() if k == 'linux-arm64/go1.27.3')
    b = sum(v['batches'] for k, v in by.items() if k == 'linux-amd64/go1.27.3')
    m = sum(v['batches'] for k, v in by.items() if k.startswith('mixed'))
    ja = max([v['jobsComplete'] for k, v in by.items() if k == 'linux-arm64/go1.27.3'] or [0])
    jb = max([v['jobsComplete'] for k, v in by.items() if k == 'linux-amd64/go1.27.3'] or [0])
    return a, b, m, ja, jb

pva, pvb, pvm, pvja, pvjb = armix(rh_pv_by)
opa, opb, opm, opja, opjb = armix(rh_ops_by)

CV = 'nitro/v3.13.0-rc.9+b72783f-20261116T155937Z'
RUN = {}
for c in (42161, 4663, 99901):
    RUN[c] = ('battery.py: %s; targeted.py: %s; pmdiff.py 250: %s; pmdiff2.py 300: %s; swaps.py: %s; callsem.py: %s.' % (
        line('raw/battery.log', c), line('raw/targeted.log', c), line('raw/pmdiff.log', c), line('raw/pmdiff2.log', c),
        line('raw/swaps.log', c), line('raw/callsem.log', c)))

SRC_DOCKER = 'https://hub.docker.com/v2/repositories/offchainlabs/nitro-node/tags?page_size=15&ordering=last_updated'
SRC_ARBDEV = 'https://coinalerts.org/news/articles/719905/'
SRC_TXSUB = 'https://docs.arbitrum.io/notices/transaction-submission-changes-notice'
SRC_COND = 'https://docs.arbitrum.io/notices/eth-send-raw-transaction-conditional-deprecation-notice'
SRC_NOTICES = 'https://docs.arbitrum.io/notices'
SRC_UPG = 'https://docs.arbitrum.foundation/network-upgrades'
SRC_A61 = 'https://docs.arbitrum.io/run-a-node/arbos-releases/arbos61'
SRC_GLAM = 'https://ethereum.org/roadmap/glamsterdam/'
SRC_GLAM2 = 'https://cointelegraph.com/news/ethereum-devs-set-glamsterdams-hoodi-rollout-for-mid-december-after-delays'
SRC_8037 = 'https://eips.ethereum.org/EIPS/eip-8037'
SRC_ELYMD = 'https://elysium.kinetiq.xyz/docs/hypercore-market-data'
SRC_ELYCW = 'https://elysium.kinetiq.xyz/docs/trading-on-hypercore-from-elysium'
SRC_ELYADDR = 'https://elysium.kinetiq.xyz/docs/contract-addresses'
SRC_3124 = 'https://github.com/OffchainLabs/nitro/releases/tag/v3.12.4'
SRC_CHG = 'https://raw.githubusercontent.com/OffchainLabs/nitro/master/CHANGELOG.md'
SRC_STYL = 'https://docs.arbitrum.io/notices/stylus-activation-pause-notice'

prof = []
def P(c, l, s, d=None):
    prof.append({'chainId': c, 'lens': l, 'summary': s, 'deltas': d or []})

docker_delta = {'delta': 'Nitro v3.13.0 shipped on 25 November 2026 as a stripped binary release of commit b72783f, the commit the endpoints already report as v3.13.0-rc.9. Docker Hub lists offchainlabs/nitro-node:v3.13.0-b72783f-stripped with the amd64 image digest sha256:af5059f2... and the arm64 digest sha256:9b0c959e..., the same digests cycle 23 pulled and every later binary lift used, so those lifts describe the final release. No newer image is listed after v3.12.4-960ca0a (19 November).', 'source': SRC_DOCKER, 'relevance': 'none'}

P(42161, 'L1', 'arb1.arbitrum.io/rpc answered %s/linux-arm64/go1.27.3 in every bracket of cycle 38. Reruns: %s replay.py: the 8 multi-step swaps the endpoint cannot serve state for replayed to the unit on the Pocket archive gateway (%d of %d). Lead L-1335: with web3_clientVersion before and after every batch (pinrun.py), the 30,222 provevec vectors (%d words over 3 sends), the 158,342 vectors of the division, modular, EXP, shift, BYTE and SIGNEXTEND subsets (%d words), pmdiff.py 250 (%d answers) and pmdiff2.py 300 (%d answers) all came from the arm64 build with %d mismatches. The amd64 PublicNode build (vlocal 5f02f3f, go1.25.12) answered the 30,222 provevec vectors with %d mismatches.' % (
    CV, RUN[42161], ra_ok, len(ra['results']), arb_pv_u, arb_ops_u, arb_pm_u, arb_pm2_u, arb_pv_m + arb_ops_m + arb_pm_m + arb_pm2_m, pv['https://arbitrum-one-rpc.publicnode.com']['nbad']),
  [docker_delta, {'delta': 'Nitro v3.12.4 (published 19 November 2026) changes only the transaction pre-checker cap for conditional transactions, rejects null for required JSON-RPC arguments and speeds up request decoding. The public CHANGELOG on master still ends at v3.11.0-rc.6.', 'source': SRC_3124, 'relevance': 'none'}])
P(42161, 'L2', 'callsem.py gives the specified call semantics on 50 of 50 cases. The announced transaction submission change makes eth_sendRawTransaction return on admission to the sequencer queue and eth_sendRawTransactionSync return a receipt with a zero blockHash after execution; both are RPC behaviour of the node and leave the state transition unchanged.', [
    {'delta': 'eth_sendRawTransaction will return when the transaction enters the sequencer queue and no longer reports inclusion-time errors; eth_sendRawTransactionSync returns a partial receipt with blockHash zero once executed. Nitro v3.13.0 carries the code, rollout is testnets first and mainnets 14 days later.', 'source': SRC_TXSUB, 'relevance': 'none'},
    {'delta': 'eth_sendRawTransactionConditional (ERC-7796) is disabled at the Arbitrum One and Nova sequencer endpoints on 17 January 2027.', 'source': SRC_COND, 'relevance': 'none'}])
P(42161, 'L4', 'At block %d arbOSVersion() is 0x74 (ArbOS 61) and getScheduledUpgrade() returns zeros. eth_config lists 36 precompiles and the EIP-2935 contract with next null. The 337 precompile and system addresses called from the PoolManager address in the empty, balanceOf and transfer shapes give exactly the cycle 20 answers.' % arbos['42161']['block'], [])
P(42161, 'L5', 'PoolManager code (24,009 bytes, sha256 prefix %s), owner %s and protocol fee controller %s are unchanged at block %d. The rollup on Ethereum still pins wasmModuleRoot 0xc10cd7ec...dc97 (consensus-v61).' % (l5['42161']['codeSha256'], l5['42161']['owner'], l5['42161']['protocolFeeController'], l5['42161']['block']), [])

P(4663, 'L1', 'The endpoint answered rc.9 b72783f from its arm64 and amd64 backends, alternating between script runs. Reruns: %s replay.py: 25 multi-step swaps and 1 other replay to the unit, 1 skipped because the state is not served. Lead L-1329: each provevec and subset batch was sent 10 times on one thread. provevec: %d batches bracketed arm64 on both sides, %d amd64 on both sides, %d mixed, %d words, %d mismatches. Subsets (158,342 vectors in 1,200-vector calls): %d arm64, %d amd64, %d mixed batches, %d words, %d mismatches.' % (
    RUN[4663], pva, pvb, pvm, rh_pv_u, rh_pv_m, opa, opb, opm, rh_ops_u, rh_ops_m), [docker_delta])
P(4663, 'L2', 'callsem.py gives the specified call semantics on 50 of 50 cases. Transaction filtering is still active from timestamp 0x6a3baaa0 (F-001); nothing else in the state model changed.', [])
P(4663, 'L4', 'At block %d arbOSVersion() is 0x74, getScheduledUpgrade() returns zeros, getCollectTips() is 0, two chain owners. The 337 special addresses answer as in cycle 20.' % arbos['4663']['block'], [])
P(4663, 'L5', 'PoolManager code (sha256 prefix %s), owner %s and protocol fee controller %s are unchanged at block %d. Its rollup on Ethereum pins the same consensus-v61 wasmModuleRoot.' % (l5['4663']['codeSha256'], l5['4663']['owner'], l5['4663']['protocolFeeController'], l5['4663']['block']), [])

P(99901, 'L1', 'The endpoint answered nitro/vlocal+unknown-unknown/linux-amd64/go1.25.12 in every bracket. Reruns: %s replay.py: 25 multi-step swaps replay to the unit. The pmdiff2 difference is script 189, the full-range swap that needs more gas than the endpoint grants, as in cycles 28 to 36. Lead L-1335: provevec.py gave %d of 30,222 words wrong, with the same build string before and after. The conduit endpoint rate limits large batches, so the batched pinned runs were replaced by the bracketed single-build scripts.' % (RUN[99901], pv['https://rpc.elysium.kinetiq.xyz']['nbad']), [])
P(99901, 'L2', 'callsem.py gives the specified call semantics on 50 of 50 cases. The endpoint refuses debug_traceBlockByNumber without an API key, so Elysium still has no traced search for a PoolManager action outside unlock.', [])
P(99901, 'L4', 'At block %d arbOSVersion() is 0x74 and getScheduledUpgrade() returns zeros. The 337 special addresses answer as in cycle 20. The HyperCore read precompile and the ElysiumCoreWriter predeploy are still announced for an ArbOS upgrade about four weeks after the 9 November launch, with no address on the contract list (last updated 9 November).' % arbos['99901']['block'], [
    {'delta': 'Kinetiq states that the HyperCore read precompile serves data attested by the sequencer, not proven by HyperCore, and that each read commits to the bytes it serves so that replay is deterministic.', 'source': SRC_ELYMD, 'relevance': 'low'}])
P(99901, 'L5', 'PoolManager code (sha256 prefix %s), owner %s (a contract of 7,310 bytes) and a zero protocol fee controller are unchanged at block %d. The rollup on HyperEVM still pins the consensus-v61 wasmModuleRoot.' % (l5['99901']['codeSha256'], l5['99901']['owner'], l5['99901']['block']), [])

findings = [{
    'ref': 'F-158',
    'title': 'Elysium\'s announced read precompile and core writer predeploy can reach the PoolManager only as a currency or hook that a pool creator names',
    'chainIds': [99901], 'lens': 'L4', 'assumptions': ['A4', 'A7'], 'effect': 'degrade', 'actor': 'pool-creator', 'severity': 'info',
    'difference': 'Kinetiq plans an ArbOS upgrade, about four weeks after the 9 November 2026 launch, that adds a precompile serving HyperCore order books, prices and balances attested by the sequencer, and an ElysiumCoreWriter predeploy that emits order intents and can call the originating contract back with the outcome. Neither address nor interface is published, and getScheduledUpgrade() still returns zeros.',
    'mechanism': 'The PoolManager calls out only to a currency (transfer in take, balanceOf in sync and settle), to the hook of a pool key, and to the native recipient of take (src/types/Currency.sol:39-87, src/PoolManager.sol:279-297 and 349-364). The day after the upgrade an ordinary account can name either new address as a currency or a hook in its own pool. If the read precompile answers balanceOf with a value that moves between sync and settle, settle books the difference as a payment in that currency, and take of that currency succeeds when the precompile returns no data, because the transfer check accepts an empty return (src/types/Currency.sol:64-74). The credit and the debt are both in the precompile currency, so only pools that list it carry them. A callback from the predeploy reaches the PoolManager only if the PoolManager itself sent the intent, which needs one of its three call shapes to match an intent-emitting selector of the predeploy; the interface is unpublished.',
    'impact': 'None for pools that do not list the new addresses. A pool that lists one of them as a currency could be filled with an unbacked balance of that currency.',
    'preconditions': 'Elysium governance ships the upgrade; a pool creator lists the new address as a currency or hook and LPs choose that pool.',
    'mitigations': 'After the upgrade, call both addresses from the PoolManager in the empty, balanceOf and transfer shapes, as cycles 16 to 38 did for the 337 existing ones, and refuse to integrate pools that list them.',
    'coreRefs': ['src/types/Currency.sol:39-87', 'src/PoolManager.sol:279-297', 'src/PoolManager.sol:349-364'],
    'sources': [{'url': SRC_ELYMD, 'supports': 'read precompile ships about four weeks after mainnet; data attested by the sequencer'},
                {'url': SRC_ELYCW, 'supports': 'ElysiumCoreWriter predeploy and result callbacks to the originating contract'},
                {'url': SRC_ELYADDR, 'supports': 'neither address appears on the contract list'}],
    'evidence': 'secondary'}]

cleared = [
 {'chainIds': [42161, 4663, 99901], 'lens': 'L1', 'check': 'Cycle 38 rerun of battery.py, targeted.py, pmdiff.py (250), pmdiff2.py (300), swaps.py, replay.py and callsem.py for the three chain ids, web3_clientVersion recorded before each script.',
  'result': 'Arbitrum One: %s Robinhood Chain: %s Elysium: %s The only difference is Elysium pmdiff2 script 189, the known gas case. Every mined swap passes the tick relation, and every replayed multi-step swap matches to the unit, the 8 Arbitrum One ones on the Pocket archive gateway.' % (RUN[42161], RUN[4663], RUN[99901]),
  'source': WR + '/raw/ (battery.log, targeted.log, pmdiff.log, pmdiff2.log, swaps.log, replay.json, replay-archive.json, callsem.log, clientVersions.log)'},
 {'chainIds': [42161], 'lens': 'L1', 'check': 'Lead L-1335 on Arbitrum One: provevec, the 158,342 subset vectors, pmdiff and pmdiff2, each batch bracketed by web3_clientVersion.',
  'result': 'Every batch named %s/linux-arm64/go1.27.3 on both sides. provevec %d words, subsets %d words, pmdiff %d answers, pmdiff2 %d answers, each job sent three times, 0 mismatches. Arbitrum One answers only from arm64, so this is the first run of the provevec and subset sets with every batch tied to that build by its brackets. The FullMath, SqrtPriceMath and SwapMath sites that use MULMOD, DIV and the 512 bit product (src/libraries/FullMath.sol:14-117) receive the specified words.' % (CV, arb_pv_u, arb_ops_u, arb_pm_u, arb_pm2_u),
  'source': WR + '/out/pin-arb1-provevec.json; pin-arb1-ops.json; pin-arb1-pmdiff.json; pin-arb1-pmdiff2.json'},
 {'chainIds': [99901, 42161], 'lens': 'L1', 'check': 'Lead L-1335 on Elysium and on the go1.25.12 PublicNode build of Arbitrum One: provevec.py with web3_clientVersion before and after.',
  'result': 'Elysium (nitro/vlocal go1.25.12) %d of 30,222 wrong; PublicNode (vlocal 5f02f3f go1.25.12) %d of 30,222 wrong. battery.py, targeted.py and both script sets already ran on Elysium in this cycle with the same build in every bracket.' % (pv['https://rpc.elysium.kinetiq.xyz']['nbad'], pv['https://arbitrum-one-rpc.publicnode.com']['nbad']),
  'source': WR + '/raw/provevec.json'},
 {'chainIds': [4663], 'lens': 'L1', 'check': 'Lead L-1329: Robinhood Chain routes each batch item to an amd64 or arm64 backend; provevec and the subset vectors sent 10 times per job on one thread.',
  'result': 'provevec: %d words, %d mismatches; subsets: %d words, %d mismatches. Batches with arm64 on both brackets: %d and %d; amd64 on both: %d and %d; mixed: %d and %d. With 10 independently routed sends, the chance that one item never reached a given backend is about 2^-10 per item, so both architectures answered nearly every vector. Earlier records: cycle 26 sent targeted and battery to both backends (arch_runs.py), cycle 28 pinned the edge vectors to each, cycle 36 shows both builds in its brackets.' % (rh_pv_u, rh_pv_m, rh_ops_u, rh_ops_m, pva, opa, pvb, opb, pvm, opm),
  'source': WR + '/out/rounds-rh-provevec.json; rounds-rh-ops.json; research/network-risk/cycles/026/arbitrum-family.work/scripts/arch_runs.py'},
 {'chainIds': [42161, 4663], 'lens': 'L1', 'check': 'Release made since cycle 36: is the Nitro v3.13.0 final release a different build from the rc.9 binaries that cycles 23 to 33 lifted?',
  'result': 'No. Docker Hub lists v3.13.0-b72783f-stripped (25 November 2026) with amd64 digest sha256:af5059f239fe78ee... and arm64 digest sha256:9b0c959e2c794725..., equal to the digests cycle 23 recorded (cycles/023/arbitrum-family.work/raw/dockerhub-nitro-node-tags.json). The announcement names the same commit and adds only the transaction submission RPC change.',
  'source': SRC_DOCKER + ' ; ' + SRC_ARBDEV},
 {'chainIds': [42161, 4663, 99901], 'lens': 'L1', 'check': 'Release notes and fix commits since the versions OPCODES.md records: Nitro v3.12.4 notes, the public CHANGELOG on master, the Arbitrum notices page.',
  'result': 'v3.12.4 changes the conditional transaction cap, JSON-RPC null handling and request decoding. The public CHANGELOG still ends at v3.11.0-rc.6 (2026-06-16). The notices page lists the conditional method deprecation, the submission change, the Stylus activation pause, Fusaka compatibility and ArbOS 51 and 61. None touches an opcode, the integer library, jump analysis, memory or storage.',
  'source': SRC_3124 + ' ; ' + SRC_CHG + ' ; ' + SRC_NOTICES},
 {'chainIds': [42161, 4663, 99901], 'lens': 'L4', 'check': 'The 337 precompile and system addresses of cycle 20 (0x1 to 0x11f, 0x800 to 0x81f, 0xa4b000 to 0xa4b00f, 0xfffe, 0xffff), called from each PoolManager address with eth_getCode and eth_call in the empty, balanceOf(PoolManager) and transfer(0x11..11, 1) shapes.',
  'result': 'All %d rows equal the cycle 20 answers after %d rate limited Elysium items were resent one at a time. No address gained code or a new answer, so no special address can book a payment through sync and settle or absorb a take differently than before.' % (prec['rows'], prec['retried']),
  'source': WR + '/raw/precscan-final.json'},
 {'chainIds': [42161, 4663, 99901], 'lens': 'L5', 'check': 'PoolManager code hash, owner, protocol fee controller and the rollup wasmModuleRoot on 2026-11-28.',
  'result': 'All equal networks.json and cycle 36. wasmModuleRoot() is 0xc10cd7ec6acaf1c441a3f6bd0900ad20f15855ba775a96f1939118cbc629dc97 on 0x4DCeB440 and 0x23a19d23 on Ethereum (block 26,510,011) and on 0x508C173d on HyperEVM (block 52,426,660), the consensus-v61 machine.',
  'source': WR + '/raw/l5.json; ' + WR + '/raw/wasmroots.txt'},
 {'chainIds': [42161, 4663, 99901], 'lens': 'L1', 'check': 'Upcoming forks over the next six months: ArbOS upgrades proposed or scheduled, Nitro releases, Ethereum Glamsterdam, Elysium\'s planned upgrade.',
  'result': 'No ArbOS version after 61 is listed or proposed (network upgrades table, ArbOS 61 page), getScheduledUpgrade() is zero and eth_config next is null on all three. Glamsterdam has a Hoodi date of 15 December 2026 and no mainnet date, with mid-January 2027 the earliest; Arbitrum would adopt its rules only through a new ArbOS, which F-145 covers. The submission and conditional method changes are RPC only. Elysium\'s upgrade (read precompile and core writer) is recorded in F-158.',
  'source': SRC_UPG + ' ; ' + SRC_A61 + ' ; ' + SRC_GLAM + ' ; ' + SRC_GLAM2},
 {'chainIds': [42161, 4663, 99901], 'lens': 'L2', 'check': 'Settlement arithmetic against value that arrives outside msg.value (ArbOS deposits, retryable value, fee distribution to the PoolManager address).',
  'result': 'Native settle credits msg.value of the settling call only (src/PoolManager.sol:353-354), and sync of address(0) only resets the synced currency (src/PoolManager.sol:281-283), so native value that reaches the PoolManager by any other path is never booked as anyone\'s payment. Token settles use the balance difference since the caller\'s own sync (src/PoolManager.sol:356-361), which F-137 already covers for bridge deliveries.',
  'source': 'src/PoolManager.sol:279-288; src/PoolManager.sol:349-364'},
]

leads = [
 {'chainIds': [99901], 'lens': 'L4', 'question': 'When Elysium schedules the ArbOS upgrade with the HyperCore read precompile and the ElysiumCoreWriter predeploy, what do both addresses answer to calls from the PoolManager in the empty, balanceOf(PoolManager) and transfer(to, amount) shapes, and does any of them emit an intent whose callback targets the PoolManager?', 'why': 'A predeploy that answers balanceOf with a moving value or that calls the PoolManager back would be a new way for a call from the PoolManager to a special address to change settlement state (F-158).', 'priority': 'medium'},
 {'chainIds': [42161, 4663, 99901], 'lens': 'L1', 'question': 'When an ArbOS version proposes the Amsterdam rules, does EIP-8037\'s reservoir model change what gas() forwards in the PoolManager\'s three external calls (src/types/Currency.sol:48 and 73, src/libraries/Hooks.sol:134), so that a hook or token call that succeeds today runs out of gas?', 'why': 'EIP-8037 notes that gas_left can increase and splits state gas from execution gas; a lower forwarded amount would turn into reverts of swaps and liquidity changes in pools whose hooks write new storage.', 'priority': 'low'},
]

leadResults = [
 {'leadId': 'L-1335', 'outcome': 'cleared', 'answer': 'Arbitrum One (arm64 rc.9 in every bracket): provevec %d words, subsets %d words, pmdiff 250 and pmdiff2 300 three times each, 0 mismatches, plus battery and targeted in full. Elysium (vlocal go1.25.12 in every bracket): provevec 0 of 30,222 wrong, battery 99,985 and targeted 85,544 with 0 mismatches, pmdiff 250 of 250, pmdiff2 299 of 300 (script 189, the known gas case). The go1.25.12 PublicNode build of Arbitrum One also gave 0 of 30,222 wrong. Avalanche (43114) belongs to another unit and was not run here.' % (arb_pv_u, arb_ops_u)},
 {'leadId': 'L-1329', 'outcome': 'cleared', 'answer': 'Each provevec and subset job was sent 10 times on one thread to the per-item routing endpoint: provevec %d words, subsets %d words, 0 mismatches, with %d and %d batches bracketed arm64 on both sides and %d and %d amd64 on both sides. Earlier coverage of both architectures is in cycle 26 (targeted and battery sent to both), cycle 28 (edge vectors pinned to each) and cycle 36 (both builds in the brackets).' % (rh_pv_u, rh_ops_u, pva, opa, pvb, opb)},
]

out = {'unit': 'arbitrum-family', '_lenses': ['L1', 'L2', 'L4', 'L5'], 'profiles': prof, 'findings': findings,
       'cleared': cleared, 'leads': leads, 'leadResults': leadResults}
json.dump(out, open(R + '/cycles/038/arbitrum-family.research.json', 'w'), indent=1)
print('written', len(prof), 'profiles', len(findings), 'findings', len(cleared), 'cleared')
