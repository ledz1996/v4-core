"""Build cycle 21 established-l1.research.json from the results in this work directory."""
import json, os
W = '/home/user/v4-core/research/network-risk/cycles/021/established-l1.work/'
WR = 'research/network-risk/cycles/021/established-l1.work/'
OUT = '/home/user/v4-core/research/network-risk/cycles/021/established-l1.research.json'


def pm(f):
    p = W + f
    if not os.path.exists(p) and f.endswith('-r2.json'): p = W + f.replace('-r2.json', '.json')
    if not os.path.exists(p): return None
    d = json.load(open(p)); r = d['results'][0]
    return {'name': r['name'], 'identical': r['identical'], 'different': r['different'], 'errors': r['errors'], 'refErr': d.get('referenceErrors', 0)}


def pmtxt(f):
    r = pm(f)
    if r is None: return f + ' did not finish'
    return '%s: %d identical, %d different (%s), %d endpoint errors, %d reference errors' % (r['name'], r['identical'], len(r['different']), r['different'][:20], r['errors'], r['refErr'] or 0)


set1 = '; '.join(pmtxt(f) for f in ['pmdiff-Polygon_quiknode-r2.json', 'pmdiff-BSC_dataseed1-r2.json', 'pmdiff-BSC_48club-r2.json', 'pmdiff-Avalanche-r2.json'])
set2 = '; '.join(pmtxt(f) for f in ['pmdiff2-Polygon_quiknode.json', 'pmdiff2-BSC_dataseed1.json', 'pmdiff2-BSC_48club.json', 'pmdiff2-Avalanche.json'])
gap = json.load(open(W + 'gap56.json')) if os.path.exists(W + 'gap56.json') else None

CV = 'rpc: web3_clientVersion on 2026-11-25T20:54Z, file ' + WR + 'clientversions.txt'
BOR = 'https://raw.githubusercontent.com/0xPolygon/bor/develop/core/vm/mulmod_memo.go'
U256 = 'https://raw.githubusercontent.com/holiman/uint256/v1.3.2/uint256.go'
AVR = 'https://raw.githubusercontent.com/ava-labs/avalanchego/master/RELEASES.md'
AVM = 'https://raw.githubusercontent.com/ava-labs/avalanchego/master/go.mod'
LIB = 'https://raw.githubusercontent.com/ava-labs/libevm/a335c2ecf4df/core/vm/environment.libevm.go'
BSCC = 'https://raw.githubusercontent.com/bnb-chain/bsc/master/params/config.go'
JEN = 'https://docs.chainstack.com/docs/bnb-jenner-hardfork'
BORC = 'https://raw.githubusercontent.com/0xPolygon/bor/develop/params/config.go'
AVU = 'https://raw.githubusercontent.com/ava-labs/avalanchego/master/upgrade/upgrade.go'

profiles = []
def prof(cid, lens, summary, deltas):
    profiles.append({'chainId': cid, 'lens': lens, 'summary': summary, 'deltas': deltas})

prof(137, 'L1', 'Both Polygon endpoints still run bor v2.11.1, whose core/vm has no MULMOD memo. The memo and the widened keccak cache sit only in v2.12.0-beta and develop, and the memo returns what stock MulMod returns for every input.', [
    {'delta': 'polygon-bor-rpc.publicnode.com answered bor/f2a2d63e69f6/v2.11.1-private on go1.26.10 and QuikNode bor/qn-tsw-fra-10240/v2.11.1 on go1.26.11. bor v2.11.2 differs from v2.11.1 only in params/version.go among 24 core/vm, core/state and params files.', 'source': CV + ' and https://raw.githubusercontent.com/0xPolygon/bor/v2.11.2/params/version.go', 'relevance': 'none'},
    {'delta': 'bor v2.11.1 core/vm/instructions.go calls z.MulMod at line 202. v2.12.0-beta and develop call evm.mulmodMemo.mulmod there (core/vm/mulmod_memo.go), which keeps the last full width modulus and its uint256.Reciprocal and then calls MulModWithReciprocal. In holiman/uint256 v1.3.2 MulMod (uint256.go:720-748) computes Reciprocal(m) and calls reduce4 on the same product, and MulModWithReciprocal (uint256.go:688-715) is the same code with the reciprocal passed in, so the result depends only on (x, y, m). The memo compares the whole modulus by value before reuse. FullMath.mulDiv calls mulmod with the full width modulus 2^256-1 on every call (src/libraries/FullMath.sol:24), so this path would serve every swap once the release ships.', 'source': BOR + ' and ' + U256, 'relevance': 'low'},
    {'delta': 'develop adds a widened KECCAK256 cache for inputs of 1 to 8,192 bytes behind evm.Config.keccakCache, which is set only with EnablePrecompileCache. It looks up by the full input and stores the hash by value.', 'source': 'https://raw.githubusercontent.com/0xPolygon/bor/develop/core/vm/instructions.go', 'relevance': 'none'},
])
prof(137, 'L2', 'Failed state sync 3212586 is still pending and pays a bridged token to an ordinary address, not the PoolManager.', [
    {'delta': 'StateReceiver at 0x1001 stores only a hash for failed syncs (failedStateSyncHashes) and replayFailedStateSyncWithData checks it against caller supplied data. The hash for 3212586 is 0x02903d6a...f5e1 and equals keccak256(abi.encode(0xa6fa4fb5...c0aa, data)) for the Heimdall clerk record.', 'source': 'https://raw.githubusercontent.com/0xPolygon/genesis-contracts/master/contracts/StateReceiver.sol and https://heimdall-api.polygon.technology/clerk/event-records/3212586, file ' + WR + 'l791.log', 'relevance': 'none'},
])
prof(137, 'L3', 'No change to gas token, caps or token contracts that the PoolManager meets was found this cycle.', [])
prof(137, 'L4', 'Salvador (block 98,688,600, about 2026-12-08 14:00 UTC at 1.5 s blocks) gives sweeper code to five accounts without code that hold about 70 million POL; none is the PoolManager or a pooled currency contract.', [
    {'delta': 'The five Salvador targets have no code today and hold 15,331,308, 4,295,442, 4,235,983, 3.05 and 46,626,826 POL. develop is still the only branch with SalvadorBlock; v2.12.0-beta does not carry it.', 'source': BORC + ' and rpc: eth_getCode and eth_getBalance on https://rpc-mainnet.matic.quiknode.pro, file ' + WR + 'forks.log', 'relevance': 'low'},
])
prof(56, 'L1', 'Every BNB Chain build reachable today, including each of the two 48 Club builds on its own, answers the whole battery and targeted set as specified.', [
    {'delta': 'bsc-dataseed1 and dataseed2 now answer Geth/v1.8.2/linux-amd64/go1.26.10 with no commit or date suffix, where cycle 19 saw v1.8.2-4e1c8247-20261104. bsc master equals v1.8.2 in 21 core/vm, core/state, params and systemcontracts files. 48 Club still serves two builds, 9b93ce23 and 132104cd, on go1.25.5. bsc.blockrazor.xyz answers Geth/v1.7.8-12d506bc-20261104 on go1.26.10 at the chain head.', 'source': CV + ', file ' + WR + 'l752.log, and https://raw.githubusercontent.com/bnb-chain/bsc/master/version/version.go', 'relevance': 'low'},
])
prof(56, 'L2', 'reth-bsc on publicnode returns an empty eth_getLogs answer, with no error, for blocks below 135,500,000 (a bisection from 135,483,276 found the last empty block at 135,499,999), which explains the gap of L-752.', [
    {'delta': 'For block 135,483,276 reth-bsc serves the block with 118 transactions and returns zero logs for any address, by number and by hash, where 48 Club and blockrazor return 7 PoolManager logs. The first block with logs is exactly 135,500,000, a round segment boundary, 223,601 blocks behind head.', 'source': 'rpc: eth_getLogs on https://bsc-rpc.publicnode.com, https://rpc-bsc.48.club and https://bsc.blockrazor.xyz, file ' + WR + 'l752.log', 'relevance': 'low'},
])
prof(56, 'L3', 'Jenner adds a payment lane that holds back 5 percent of each block from general transactions; a PoolManager exit stays far below the per-transaction cap.', [
    {'delta': 'BEP-703 limits general transactions to 95 percent of block gas from Jenner (2026-12-08 02:30 UTC, timestamp 1796697000). PoolManager calls are general transactions.', 'source': JEN + ' and ' + BSCC, 'relevance': 'none'},
])
prof(56, 'L4', 'No new system contract or precompile beyond the Jenner set recorded in F-007, F-076 and F-139. No fork after Jenner is scheduled in the client source.', [
    {'delta': 'bsc master params/config.go sets JennerTime 1796697000 and AmsterdamTime nil; no later BSC fork time exists.', 'source': BSCC, 'relevance': 'none'},
])
prof(43114, 'L1', 'avalanchego 1.15.3 still answers on both endpoints. The next release, 1.15.4, moves libevm to a commit that changes only the address context given to stateful precompiles.', [
    {'delta': 'avalanchego master (1.15.4, unreleased) pins libevm v1.13.15-0.20261111112450-a335c2ecf4df instead of d398bc4dbe41. Of 24 core/vm and core/state files only core/vm/contracts.libevm.go and environment.libevm.go differ, and the change removes the Raw caller and self fields from the precompile environment. holiman/uint256 stays at v1.2.4.', 'source': AVM + ' and ' + LIB, 'relevance': 'none'},
])
prof(43114, 'L2', 'The C-Chain runs SAE since Helicon; the 1.15.4 notes add only mempool and RPC fixes.', [
    {'delta': '1.15.4 notes: an Rpc-Error-Codes header, removal of some P-Chain and X-Chain balance calls, and a mempool rule that refuses a tip cap of 0 for non-local transactions.', 'source': AVR, 'relevance': 'none'},
])
prof(43114, 'L3', 'No change found.', [])
prof(43114, 'L4', 'Igloo is still unscheduled on Mainnet and Fuji; no other C-Chain upgrade is dated.', [
    {'delta': 'upgrade/upgrade.go on master: HeliconTime 2026-09-22 15:00 UTC, IglooTime UnscheduledActivationTime.', 'source': AVU, 'relevance': 'none'},
])

findings = [{
    'ref': 'new',
    'title': 'The reth-bsc endpoint on publicnode answers PoolManager log queries below block 135,500,000 with an empty list and no error',
    'chainIds': [56], 'lens': 'L2', 'assumptions': ['A14'], 'effect': 'degrade', 'actor': 'operator', 'severity': 'info',
    'difference': 'Ethereum clients that pruned receipts answer a log query for a pruned range with an error. reth-bsc v0.1.4-hotfix on publicnode serves the block body but returns zero logs for every address in blocks below 135,500,000.',
    'mechanism': 'An integration that rebuilds positions, claims or fee state from the PoolManager events Initialize, ModifyLiquidity, Swap and Donate (src/PoolManager.sol:139, 175, 241, 273) through this endpoint sees nothing for older blocks and records no activity. For block 135,483,276 the endpoint returns 0 logs where two other builds return 7 PoolManager logs, and the answer is the same by block number and by block hash. Nothing in the PoolManager depends on logs, so pool state and payouts are unchanged.',
    'impact': 'No funds move. Indexers, front ends and monitoring that use this endpoint can show wrong positions or miss events for older blocks.',
    'preconditions': 'A reader uses this endpoint for history. No attacker action is involved.',
    'mitigations': 'Read history from an archive endpoint and compare a sample of logs with receipts, as gapcheck2.py does.',
    'coreRefs': ['src/PoolManager.sol:139', 'src/PoolManager.sol:241'],
    'sources': [{'url': 'rpc: eth_getLogs on https://bsc-rpc.publicnode.com and https://rpc-bsc.48.club, block 135483276, file ' + WR + 'l752.log', 'supports': 'empty answer on reth-bsc, 7 logs on 48 Club, boundary at 135,500,000'}],
    'evidence': 'primary'}]

cleared = [
    {'chainIds': [137, 56, 43114], 'lens': 'L1', 'check': 'Opcode battery of 99,985 vectors rerun on 2026-11-25 on Polygon (publicnode bor v2.11.1 go1.26.10, QuikNode bor v2.11.1 go1.26.11), BNB Chain (dataseed1 v1.8.2 go1.26.10, 48 Club) and Avalanche (avalanchego 1.15.3 go1.26.10).', 'result': 'Every vector ran on every endpoint with no mismatch.', 'source': WR + 'battery.json'},
    {'chainIds': [137, 56, 43114], 'lens': 'L1', 'check': 'Targeted set of 85,544 vectors (MULMOD, mulDiv 512-bit, ADDMOD, divisions, shifts at limb edges) on the same five endpoints.', 'result': 'No mismatch. QuikNode, dataseed1, 48 Club and Avalanche ran all vectors; publicnode Polygon ran 85,394, one batch of 150 being refused with HTTP 403, and those vectors ran on QuikNode.', 'source': WR + 'targeted.json'},
    {'chainIds': [56], 'lens': 'L1', 'check': 'Battery and targeted set on each 48 Club build separately (L-886): every batch was resent with web3_clientVersion until the tag named the wanted build.', 'result': 'Build 9b93ce23 and build 132104cd each answered all 99,985 battery vectors and all 85,544 targeted vectors with no mismatch. 167 and 143 batches per build were kept, and 124 to 197 batches answered by the other build were discarded.', 'source': WR + 'battery-48-9b93ce23.json, battery-48-132104cd.json, targeted-48-*.json and tags48pin.log'},
    {'chainIds': [137, 56, 43114], 'lens': 'L1', 'check': 'Script set 1 (pmdiff, 250 scripts) against an Ethereum reference: ' + set1, 'result': 'Every script that both sides completed gave the same bytes as Ethereum. Earlier runs against the publicnode Ethereum endpoint lost 3 or 4 reference scripts to HTTP 403, and the reference hashes that did come back equal the stored ones in opcodes/pmdiff.json.', 'source': WR + 'pmdiff-*-r2.json'},
    {'chainIds': [137, 56, 43114], 'lens': 'L1', 'check': 'Script set 2 (pmdiff2, 300 scripts with hook and token doubles): ' + set2, 'result': 'BNB Chain and Avalanche equal Ethereum on all scripts that finished. The 20 Polygon scripts that differ are the same indexes as in opcodes/pmdiff2.json (22, 30, 69, ... 297), the full-range swaps cut short by gas that F-064 and F-115 record.', 'source': WR + 'pmdiff2-*.json'},
    {'chainIds': [137], 'lens': 'L1', 'check': 'Does the MULMOD reciprocal memo of the coming bor release change any mulmod result used by FullMath.mulDiv, mulDivRoundingUp or SqrtPriceMath.getAmount1Delta (src/libraries/FullMath.sol:24, 48, 112; src/libraries/SqrtPriceMath.sol:252)?', 'result': 'No. The memo takes the memo path only for a modulus with a nonzero top limb, compares the full modulus by value before reuse, and calls MulModWithReciprocal, which in uint256 v1.3.2 runs the same reduce4 on the same product as MulMod with a freshly computed reciprocal. Moduli below 2^192, including 2^128 and 2^96 used through mulDiv, take the unchanged stock call. The memo is not in v2.11.1, which both endpoints run.', 'source': BOR + ' and ' + U256 + ' lines 688-748'},
    {'chainIds': [43114], 'lens': 'L1', 'check': 'Interpreter change in the next avalanchego release (libevm d398bc4dbe41 to a335c2ecf4df).', 'result': 'Of instructions.go, interpreter.go, jump_table.go, analysis.go, memory.go, evm.go, contract.go, stack.go, eips.go, gas_table.go, statedb.go, transient_storage.go, journal.go and the libevm hook files, only the precompile environment files change, and only by dropping the Raw address pair. The PoolManager makes no DELEGATECALL and calls no stateful precompile in a pool without attacker code.', 'source': LIB},
    {'chainIds': [137, 56, 43114], 'lens': 'L1', 'check': 'L-928: can the shift rewrite of Go issue 81868 in go1.26.10 break jump destination analysis (BitVec.setN shifts a uint16 left by pos%8 and right by the constant 8) for the PoolManager?', 'result': 'The compiled form was not read: the only local toolchain is go1.24.7 and no go1.26.10 toolchain was installed. For the PoolManager the outcome is settled by behaviour: set 1 on dataseed1 and Avalanche, both go1.26.10 builds, ran the PoolManager bytecode, whose push data crosses a byte border of the bit vector hundreds of times, with every result equal to Ethereum, and 209 JUMPI vectors passed on publicnode bor go1.26.10. A fault in setN would make valid jumps in the PoolManager fail or let a jump land in push data; analysis is per code, so attacker bytecode cannot change the PoolManager bitmap.', 'source': 'https://raw.githubusercontent.com/0xPolygon/bor/v2.11.1/core/vm/analysis_legacy.go lines 37-44 and ' + WR + 'pmdiff-BSC_dataseed1-r2.json'},
    {'chainIds': [137], 'lens': 'L4', 'check': 'L-791: does pending failed state sync 3212586 pay the Polygon PoolManager if any account replays it?', 'result': 'No. The Heimdall record names receiver 0xa6fa4fb5f76172d178d61b04b0ecd319c5d1c0aa (ChildChainManager) and a DEPOSIT of 15,310.28 units (18 decimals) of root token 0x8f693ca8d21b157107184d29d398a8d082b38b76 to 0x08bb17cf80ed16483efa0217480c94c233dd9900. The record hashes to the value stored in failedStateSyncHashes(3212586). The PoolManager address does not occur in the data, so a replay inside a sync and settle bracket raises no PoolManager balance.', 'source': 'https://heimdall-api.polygon.technology/clerk/event-records/3212586 and rpc: eth_call failedStateSyncHashes(3212586) on https://rpc-mainnet.matic.quiknode.pro, file ' + WR + 'l791.log'},
    {'chainIds': [43114], 'lens': 'L2', 'check': 'L-947: which earlier Avalanche results seeded PoolManager or token storage with a full state override instead of stateDiff?', 'result': 'None found. No Python, JavaScript or shell script in tools/ or in any cycle work directory has a state key in an override. pmdiff.py and pmdiff2.py inject code only (pmdiff.py:181), and pmdiff3.py:104 and pmdiff6.py:145 use stateDiff, which libevm applies with the bit 248 transform. The reruns of sets 1 and 2 on Avalanche in this cycle use the same overrides and match Ethereum.', 'source': 'research/network-risk/tools/opdiff/pmdiff3.py:104, research/network-risk/tools/opdiff/pmdiff6.py:145'},
    {'chainIds': [56], 'lens': 'L6', 'check': 'Forks in the next six months on BNB Chain: Jenner and anything after it.', 'result': 'Jenner (2026-12-08 02:30 UTC) is the only scheduled fork. Its EVM effects (CAS20 precompiles, 0x70 millisecond time, 0x68 repricing) were covered by F-007, F-076, F-139 and the cycle 19 Jenner-rule reruns; the payment lane only limits general gas per block. AmsterdamTime is nil.', 'source': BSCC + ' and ' + JEN},
    {'chainIds': [43114], 'lens': 'L6', 'check': 'Forks in the next six months on Avalanche.', 'result': 'Igloo has no activation time on Mainnet or Fuji, so nothing changes for the PoolManager until a release schedules it.', 'source': AVU},
]

leads = [
    {'chainIds': [137], 'lens': 'L1', 'question': 'When bor tags the release that carries Salvador, rerun the battery, the targeted set and sets 1 and 2 on it, with MULMOD vectors that repeat one full-width modulus across calls and then change one limb, to exercise the memo path.', 'why': 'The memo was read but never run in a node; it serves every mulDiv call once shipped.', 'priority': 'medium'},
    {'chainIds': [56], 'lens': 'L1', 'question': 'What does bsc.blockrazor.xyz (Geth/v1.7.8-12d506bc-20261104) run? v1.7.8 predates Pasteur and Jenner, yet it is at the chain head. Is it a builder or validator build with a back-ported fork set, and does it carry the fused-instruction feature that ended in v1.8.0?', 'why': 'A block producer running another interpreter could seal a block that other nodes reject or compute a different result in.', 'priority': 'low'},
]

lr = [
    {'leadId': 'L-928', 'outcome': 'inconclusive', 'answer': 'The SSA form of a go1.26.10 build was not read; the session has go1.24.7 only and nothing was installed. For the PoolManager the question is answered by behaviour: its bytecode ran set 1 on two go1.26.10 builds (dataseed1, avalanchego) with results equal to Ethereum, and JUMPI vectors passed on publicnode bor go1.26.10.'},
    {'leadId': 'L-947', 'outcome': 'cleared', 'answer': 'No script in tools/ or any cycle work directory uses a full state override; set 1 and 2 inject code only and sets 3 and 6 use stateDiff. No Avalanche clearance rested on a raw-key override.'},
    {'leadId': 'L-886', 'outcome': 'cleared', 'answer': 'Each 48 Club build (9b93ce23 and 132104cd) answered the whole battery and targeted set on its own, pinned by resending until the tag matched, with no mismatch. The script sets were run once against the mixed endpoint and matched; they were not pinned.'},
    {'leadId': 'L-893', 'outcome': 'inconclusive', 'answer': 'No tokenless BNB Chain archive endpoint was found. 48 Club and blockrazor answer header not found for block 55,936,232, publicnode asks for a token for archive requests, and nodereal and dataseed refuse log ranges. gapcheck2.py was run on the ten cycle 18 windows and could read only the recent ones.'},
    {'leadId': 'L-791', 'outcome': 'cleared', 'answer': 'State sync 3212586 is a ChildChainManager DEPOSIT of 15,310.28 units of root token 0x8f693ca8... to 0x08bb17cf..., confirmed by hash against failedStateSyncHashes. It does not pay the PoolManager.'},
    {'leadId': 'L-752', 'outcome': 'finding', 'answer': 'reth-bsc on publicnode returns zero logs, with no error, for every block below 135,500,000, for any address, by number and by hash. Recent blocks match 48 Club. Earlier censuses compared logs with receipts on other endpoints (cycles 18 and 19), so they do not rest on this one.'},
    {'leadId': 'L-816', 'outcome': 'inconclusive', 'answer': 'On 2026-11-25 there is still no bor tag with Salvador: v2.11.3, v2.12.0 and v2.12.0-rc1 return 404, v2.11.2 differs from v2.11.1 only in version.go, and SalvadorBlock is only on develop. Rerun at the block is owed.'},
    {'leadId': 'L-805', 'outcome': 'inconclusive', 'answer': 'bsc master equals v1.8.2 in 21 core files and no newer tag exists. dataseed now reports plain v1.8.2. Battery and targeted set pass on dataseed1 and on each 48 Club build. The live rerun after 2026-12-08 02:30 UTC is still owed.'},
    {'leadId': 'L-882', 'outcome': 'inconclusive', 'answer': 'No release carries Salvador. The memo is on by default in v2.12.0-beta and develop and returns the same result as stock MulMod for every input, as read from uint256 v1.3.2. The widened keccak cache needs EnablePrecompileCache. The rerun at the first block after 98,688,600 is owed.'},
]
if gap:
    lr[3]['answer'] += ' Windows read: ' + json.dumps([[w.get('from'), w.get('getLogs')] for w in gap.get('windows', [])])[:600]

d = {'unit': 'established-l1', '_lenses': ['L1', 'L2', 'L3', 'L4'], 'profiles': profiles, 'findings': findings, 'cleared': cleared, 'leads': leads, 'leadResults': lr}
json.dump(d, open(OUT, 'w'), indent=1)
print('wrote', OUT)
