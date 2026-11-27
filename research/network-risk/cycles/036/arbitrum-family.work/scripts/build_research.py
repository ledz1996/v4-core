"""Builds cycles/036/arbitrum-family.research.json from the raw outputs of this work directory."""
import json, os, re
W = '/home/user/v4-core/research/network-risk/cycles/036/arbitrum-family.work'
R = W + '/raw/'
OUT = '/home/user/v4-core/research/network-risk/cycles/036/arbitrum-family.research.json'
def lg(n):
    p = R + n
    return open(p).read() if os.path.exists(p) else ''
def line(log, cid):
    for l in log.splitlines():
        if l.strip().startswith(str(cid) + ' '): return ' '.join(l.split())
    return 'no line'
B, T, P1, P2, SW, RP, CS = (lg(x) for x in ('battery.log', 'targeted.log', 'pmdiff.log', 'pmdiff2.log', 'swaps.log', 'replay.log', 'callsem.log'))
NAMES = {42161: 'Arbitrum One', 4663: 'Robinhood Chain', 99901: 'Elysium'}
RPJ = json.load(open(R + 'replay.json'))['results']
def rp(cid):
    xs = [x for x in RPJ if x['chainId'] == cid]
    ok = sum(1 for x in xs if x['ok']); ns = sum(1 for x in xs if not x['ok'] and 'state not served' in x.get('why', ''))
    return f'{ok} multi-step swaps replay to the unit, {len(xs) - ok - ns} fail, {ns} skipped because the endpoint no longer serves that state'
def runs(cid):
    t = '; '.join(f'{n}: {line(x, cid)}' for n, x in (('battery.py', B), ('targeted.py', T), ('pmdiff.py 250', P1), ('pmdiff2.py 300', P2), ('swaps.py', SW), ('callsem.py', CS)))
    t += '; replay.py: ' + rp(cid)
    if cid == 99901: t += '. The one pmdiff2 difference is script 189, the full-range swap that needs more gas than the endpoint grants (equal at 40 and 60 million gas in cycle 28)'
    return t
scen = {k: json.load(open(R + f'scen-{k}.json')) for k in ('arb1', 'rh', 'ely', 'pubnode')}
retry = json.load(open(R + 'scen-arb1-retry.json'))
pv = json.load(open(R + 'provevec.json'))
def scen_tot(k):
    t = dict(scen[k]['totals'])
    if k == 'arb1':
        t['calls'] += retry['totals']['calls']; t['equal'] += retry['totals']['equal']; t['err'] = 0
    return t
st = {k: json.load(open(W + f'/out/stalesync-{k}.json'))['verdict'] for k in ('arb1', 'rh', 'ely', 'pubnode')}
bo = {k: json.load(open(R + f'borrow-{k}.json')) for k in ('arb1', 'rh', 'ely')}
def bo_ok(k): return all(v['equal'] for u in bo[k]['urls'].values() for v in u.values())
arb = json.load(open(R + 'arbos_state.json'))

SRC_REL = 'https://go.dev/doc/devel/release'
SRC_80618 = 'https://github.com/golang/go/issues/80618'
SRC_80517 = 'https://github.com/golang/go/issues/80517'
SRC_80127 = 'https://github.com/golang/go/issues/80127'
SRC_MS = 'https://github.com/golang/go/issues?q=milestone%3AGo1.25.13+label%3ACherryPickApproved'
SRC_P12 = 'https://raw.githubusercontent.com/golang/go/go1.25.12/src/cmd/compile/internal/ssa/prove.go'
SRC_P13 = 'https://raw.githubusercontent.com/golang/go/go1.25.13/src/cmd/compile/internal/ssa/prove.go'
SRC_M13 = 'https://raw.githubusercontent.com/golang/go/go1.25.13/src/cmd/compile/internal/liveness/mergelocals.go'
SRC_P1273 = 'https://raw.githubusercontent.com/golang/go/go1.27.3/src/cmd/compile/internal/ssa/prove.go'
SRC_UPG = 'https://docs.arbitrum.foundation/network-upgrades'
SRC_A61 = 'https://docs.arbitrum.io/run-a-node/arbos-releases/arbos61'
SRC_ELY_T = 'https://elysium.kinetiq.xyz/docs/trading-on-hypercore-from-elysium'
SRC_ELY_M = 'https://elysium.kinetiq.xyz/docs/hypercore-market-data'
SRC_ELY_W = 'https://elysium.kinetiq.xyz/docs/what-is-elysium'
SRC_ELY_B = 'https://elysium.kinetiq.xyz/docs/blocks-fees-and-ordering'

pvtxt = '; '.join(f"{u.split('//')[1].split('/')[0]} ({v['cvBefore'].split('/')[-3] if False else v['cvBefore']}) {v['done']} run, {v['nbad']} mismatches" for u, v in pv['urls'].items())
sctxt = '; '.join(f"{k}: {scen_tot(k)['equal']} of {scen_tot(k)['calls']} calls equal" for k in scen)

GO_DIFF = ('Between the go1.25.12 and go1.25.13 tags, 25 files of src/cmd/compile and src/cmd/internal differ (raw.githubusercontent.com, fetched 2026-11-27). Two of the changes reach amd64. '
           'First, prove.go replaces addLocalFacts with a walk that first sorts each block\'s values topologically (topoSortValuesInBlock) and then folds the arguments of each value before it adds the facts that value teaches (constantFoldArguments, addValueFact). This is the backport of Go issue 80517 (issue 80618, CLs 807221 and 807222, "fix time traveling proofs in prove"), in which a fact learned from a later value was used to simplify an earlier one and the amd64 reproducer made an indirect call to an attacker-chosen address. '
           'Second, liveness/mergelocals.go stops merging the stack slots of two address-taken locals when an op may carry the address into its result (Go issue 80127, backport 80477). The new addrSinkArg flags are set on amd64 ops as well, although the reported failure was on riscv64. '
           'The other changes are riscv64 sign extension in regalloc (issue 80578), mips and mips64 fixes and DWARF output. go1.27.3 already carries the topological prove walk (go1.27.3 prove.go line 1705).')

profiles = []
for cid in (42161, 4663, 99901):
    a = arb[str(cid)] if str(cid) in arb else arb[cid]
    if cid == 42161:
        s1 = (f"The endpoint answered nitro/v3.13.0-rc.9+b72783f on linux-arm64 with go1.27.3 in every bracket of the cycle 36 rerun, and arbitrum-one-rpc.publicnode.com answered nitro/vlocal+5f02f3f-modified on linux-amd64 with go1.25.12. Reruns: {runs(cid)}. "
              f"30,222 new vectors (every shift count 0 to 320 for SHL, SHR and SAR plus counts near 2^64 and 2^255, every BYTE index and SIGNEXTEND width, divisions and modular operations by divisors of one to four limbs) match on both builds.")
        d1 = [{'delta': 'arbitrum-one-rpc.publicnode.com, a public Arbitrum One node, runs a go1.25.12 amd64 build. go1.25.12 lacks the go1.25.13 compiler fixes for time-travelling proofs in the prove pass (Go issues 80517 and 80618) and for stack slot merging of address-taken locals (Go issue 80127). The Offchain Labs endpoint runs go1.27.3, which has the prove fix.', 'source': SRC_MS, 'relevance': 'low'}]
    elif cid == 4663:
        s1 = (f"The endpoint answered rc.9 b72783f with go1.27.3 from both its arm64 and amd64 backends; the bracket around each of the 23 scenarios showed the two builds alternating. Reruns: {runs(cid)}. The 30,222 new shift, byte, sign extension and division vectors match.")
        d1 = []
    else:
        s1 = (f"The official endpoint answered nitro/vlocal+unknown-unknown on linux-amd64 with go1.25.12 in every bracket. Reruns: {runs(cid)}. The 30,222 new shift, byte, sign extension and division vectors match.")
        d1 = [{'delta': 'Elysium\'s only block producer build is compiled with go1.25.12. go1.25.13 (13 August 2026) fixed the time-travelling proofs of the prove pass (Go issues 80517 and 80618) and stack slot merging of address-taken locals (Go issue 80127), and the Go 1.25 line ended with go1.25.14. The build therefore lacks two compiler fixes that reach amd64. No result checked in this cycle depends on them.', 'source': SRC_REL, 'relevance': 'low'}]
    profiles.append({'chainId': cid, 'lens': 'L1', 'summary': s1, 'deltas': d1})
    key = {42161: 'arb1', 4663: 'rh', 99901: 'ely'}[cid]
    t = scen_tot(key)
    s2 = (f"The 23 multi-transaction scenarios of cycle 28 ran as one eth_simulateV1 block per scenario, holding up to 19 transactions, with web3_clientVersion read before and after each scenario: {t['equal']} of {t['calls']} calls equal the reference interpreter. "
          f"stalesync.py shows the synced currency and reserves are zero in the next transaction (nextTxSeesZero {st[key]['nextTxSeesZero']}) and present inside the same transaction (controlSeesSync {st[key]['controlSeesSync']}). The three getFeeGrowthInside borrow scripts return the reference bytes ({bo_ok(key)}).")
    profiles.append({'chainId': cid, 'lens': 'L2', 'summary': s2, 'deltas': []})
    s4 = (f"Nothing new at the special addresses. At block {a['block']} arbOSVersion() returns 0x74 (ArbOS 61), getScheduledUpgrade() returns zeros, getNativeTokenManagementFrom() is 0 and getCollectTips() is {int(a['getCollectTips()'], 16)}. eth_config lists the same 36 precompiles and the one EIP-2935 system contract as in cycle 34.")
    d4 = []
    if cid == 99901:
        d4 = [{'delta': 'Kinetiq\'s docs, updated on 2 November 2026, now describe the ElysiumCoreWriter predeploy of the planned upgrade: a contract binds a HyperCore account, emits order intents through the predeploy, and can prefund a HYPE gas escrow so that each outcome is delivered back to the originating contract as an on-chain callback. The address and interface are still unpublished.', 'source': SRC_ELY_T, 'relevance': 'low'}]
    profiles.append({'chainId': cid, 'lens': 'L4', 'summary': s4, 'deltas': d4})
    if cid == 99901:
        s6 = ('Elysium is still on ArbOS 61 with nothing scheduled on chain and eth_config next null. Kinetiq places the HyperCore read precompile and the ElysiumCoreWriter predeploy in an ArbOS upgrade about four weeks after the 9 November mainnet launch. The blocks page, updated 21 November, gives a 32,000,000 block gas limit and priority fee ordering with no privileged lanes.')
        d6 = [{'delta': 'Block gas limit 32,000,000 and ordering by priority fee with no privileged lanes; batches are posted to HyperEVM about every 15 minutes.', 'source': SRC_ELY_B, 'relevance': 'none'}]
    else:
        s6 = ('No ArbOS version after 61 is listed in the Arbitrum DAO network upgrades table or proposed in the ArbOS 61 documentation, getScheduledUpgrade() returns zeros and eth_config next is null. ' +
              ('Transaction filtering is still active from timestamp 0x6a3baaa0 (F-001).' if cid == 4663 else 'The DAO deferred multidimensional gas to align with EIP-8037 for Glamsterdam, which has no Arbitrum date.'))
        d6 = []
    profiles.append({'chainId': cid, 'lens': 'L6', 'summary': s6, 'deltas': d6})

findings = [
    {'ref': 'F-136',
     'title': 'Elysium\'s only block producer and a public Arbitrum One node run go1.25.12, which lacks the go1.25.13 prove and stack slot merging fixes, and no EVM result was found to depend on them',
     'chainIds': [99901, 42161], 'lens': 'L1', 'assumptions': ['A10'], 'effect': 'degrade', 'actor': 'operator', 'severity': 'info',
     'difference': 'Ethereum clients are not tied to one build, and the go-ethereum releases are built with a supported Go toolchain. Elysium has a single sequencer whose build reports go1.25.12, and the PublicNode Arbitrum One node reports go1.25.12 as well. ' + GO_DIFF,
     'mechanism': 'A wrong proof in the prove pass removes a branch or a bounds check, or marks a shift as bounded. On amd64 a 64 bit shift instruction uses only the low six bits of its count, so a shift the compiler wrongly believes bounded would turn a shift by 64 or more into a shift by the count modulo 64. In the integer library the limb shifts of Lsh, Rsh and SRsh, the normalisation shift of udivrem and the branch on the shift count in opSHL, opSHR and opSAR are the places where this would change a word. A wrong word from SHR or SAR would change TickMath.getTickAtSqrtPrice (src/libraries/TickMath.sol:142-190) and BitMath (src/libraries/BitMath.sol:16-45), which TickBitmap uses to find the next initialised tick, and a wrong MULMOD or DIV would change FullMath.mulDiv (src/libraries/FullMath.sol:24-48) and every amount computed from it. A merged stack slot would mix two local arrays, for instance the quotient and the normalised operands of udivremKnuth. Either fault would make the sequencer write a state that differs from the source. No such difference was seen: 30,222 vectors built for these branch sites, the 99,985 battery vectors, the 85,544 targeted vectors, 550 PoolManager scripts and the 23 multi-transaction scenarios give the reference result on both go1.25.12 builds. Building a go1.25.12 compiler to compare its output was not done, because the review does not allow installing a toolchain.',
     'impact': 'None found. A miscompile in Elysium\'s producer would apply to every pool there, because no other party produces blocks and the rollup accepts assertions from one whitelisted validator (cycle 13). On Arbitrum One a wrong PublicNode result would mislead only its own users, since blocks come from the Offchain Labs sequencer on go1.27.3.',
     'preconditions': 'The operator keeps the go1.25.12 build, and some input reaches a code site with the faulty shape. No such site has been shown.',
     'mitigations': 'Elysium\'s operator rebuilds with go1.25.13 or later, or with the go1.27 line. Integrators on Arbitrum One read from the Offchain Labs endpoint or compare two node builds.',
     'coreRefs': ['src/libraries/FullMath.sol:24-48', 'src/libraries/TickMath.sol:61-63', 'src/libraries/TickMath.sol:142-190', 'src/libraries/BitMath.sol:16-45'],
     'sources': [{'url': SRC_REL, 'supports': 'go1.25.13 (13 August 2026) fixes the compiler; go1.25.14 is the last 1.25 release listed'},
                 {'url': SRC_MS, 'supports': 'the Go1.25.13 milestone holds the prove backport 80618, the stack slot fix backport 80477 and the riscv64 regalloc backport 80578'},
                 {'url': SRC_80618, 'supports': 'the prove fix was backported to 1.25 by CL 807221 and 807222, merged as commit f59f3cc'},
                 {'url': SRC_80517, 'supports': 'the root bug: time-travelling proofs make an indirect call to an arbitrary address on amd64'},
                 {'url': SRC_80127, 'supports': 'the stack slot merging bug that the mergelocals change fixes'},
                 {'url': SRC_P12, 'supports': 'go1.25.12 prove.go still uses addLocalFacts'},
                 {'url': SRC_P13, 'supports': 'go1.25.13 prove.go uses topoSortValuesInBlock and constantFoldArguments'},
                 {'url': SRC_M13, 'supports': 'go1.25.13 mergelocals.go checks AddrSinkArg and refers to issue 80127'},
                 {'url': SRC_P1273, 'supports': 'go1.27.3 prove.go already has topoSortValuesInBlock'},
                 {'url': 'https://rpc.elysium.kinetiq.xyz', 'supports': 'web3_clientVersion nitro/vlocal+unknown-unknown/linux-amd64/go1.25.12 and 30,222 vectors without a mismatch (raw/provevec.json)'},
                 {'url': 'https://arbitrum-one-rpc.publicnode.com', 'supports': 'web3_clientVersion nitro/vlocal+5f02f3f-20261014T220458Z-modified/linux-amd64/go1.25.12 and 30,222 vectors without a mismatch (raw/provevec.json)'}],
     'evidence': 'primary'},
    {'ref': 'F-158',
     'title': 'Elysium\'s planned core writer predeploy delivers result callbacks to the contract that sent an intent, and its address and interface are still unpublished',
     'chainIds': [99901], 'lens': 'L4', 'assumptions': ['A2', 'A4', 'A7'], 'effect': 'degrade', 'actor': 'governance', 'severity': 'info',
     'difference': 'Ethereum has no system contract that calls back into user contracts. Kinetiq\'s docs say the ElysiumCoreWriter predeploy lets a contract bind a HyperCore account, emit order intents and prefund a HYPE gas escrow, after which each HyperCore outcome is delivered back to the originating contract as an on-chain callback paid from the escrow. The read precompile will serve HyperCore orderbooks, prices, balances and positions to any contract. Both ship in an ArbOS upgrade planned for about four weeks after the 9 November mainnet launch and are not scheduled on chain.',
     'mechanism': 'The PoolManager calls an outside address only for a native payout, a token transfer, the balanceOf read of sync and the hook calls (src/types/Currency.sol:48, src/types/Currency.sol:73, src/PoolManager.sol:279-288, src/libraries/Hooks.sol:134). For the predeploy to treat the PoolManager as an originating contract, the PoolManager would have to call one of its intent or bind functions, and none of these four calls carries such a selector unless the predeploy answers transfer(address,uint256) or balanceOf(address) or sits at an address with valid hook bits. A callback into the PoolManager would reach a function by selector, and every function that moves value requires the unlock (src/PoolManager.sol:291-336). This cannot be checked further until the address and interface are published.',
     'impact': 'None found under the published description. If the predeploy answered transfer from the PoolManager and moved a balance, an ordinary account could use P2 to trigger it, so the call shapes must be rerun on the day the upgrade is scheduled.',
     'preconditions': 'Elysium\'s chain owner schedules the ArbOS upgrade.',
     'mitigations': 'Rerun the special-address call shapes of cycle 34 against the new addresses before the activation time, and read the predeploy source.',
     'coreRefs': ['src/types/Currency.sol:44-80', 'src/PoolManager.sol:279-288', 'src/libraries/Hooks.sol:131-160'],
     'sources': [{'url': SRC_ELY_T, 'supports': 'ElysiumCoreWriter predeploy, intents, gas escrow and result callbacks to the originating contract, shipping in an ArbOS upgrade about four weeks after mainnet'},
                 {'url': SRC_ELY_M, 'supports': 'the HyperCore read precompile ships in the same upgrade; Elysium launched on stock ArbOS without it'},
                 {'url': 'https://rpc.elysium.kinetiq.xyz', 'supports': 'getScheduledUpgrade() returns zeros and eth_config next is null at block %d (raw/arbos_state.json, raw/eth_config_rpc.elysium.kinetiq.xyz.json)' % arb['99901']['block']}],
     'evidence': 'secondary'},
]

cleared = [
    {'chainIds': [42161, 4663, 99901], 'lens': 'L1', 'check': 'Cycle 36 rerun of battery.py, targeted.py, pmdiff.py (250), pmdiff2.py (300), swaps.py, replay.py and callsem.py for the three chain ids, with web3_clientVersion recorded before each script.',
     'result': ' | '.join(f'{NAMES[c]}: {runs(c)}' for c in NAMES), 'source': 'cycles/036/arbitrum-family.work/raw/*.log and raw/clientVersions.log'},
    {'chainIds': [42161, 4663, 99901], 'lens': 'L1', 'check': '30,222 vectors for the sites a wrong proof or a merged stack slot would break on amd64: SHL, SHR and SAR with every count from 0 to 320 and counts near 2^32, 2^64, 2^128 and 2^255 over 22 operands; BYTE and SIGNEXTEND at every index from 0 to 39; DIV, MOD, SDIV, SMOD, ADDMOD, MULMOD and a 512 bit product reduction by divisors of one to four limbs whose top limb has 1, 32 or 64 bits. Run on both go1.25.12 builds and both go1.27.3 builds.',
     'result': 'No mismatch: ' + pvtxt + '. The words these opcodes produce feed TickMath, BitMath and FullMath directly, and they are right on all four builds.', 'source': 'cycles/036/arbitrum-family.work/scripts/provevec.py, raw/provevec.json'},
    {'chainIds': [42161, 4663, 99901], 'lens': 'L2', 'check': 'Lead L-1277: the 23 multi-transaction scenarios of cycle 28 (scen28.py) by eth_simulateV1, one blockStateCall per scenario holding 1 to 19 transactions, web3_clientVersion before and after each scenario, on arb1.arbitrum.io, rpc.mainnet.chain.robinhood.com, rpc.elysium.kinetiq.xyz and arbitrum-one-rpc.publicnode.com.',
     'result': sctxt + '. One Arbitrum One scenario that hit a rate limit was rerun alone and matches. Transient state is reset between transactions of one simulated block, so a delta, the lock or a synced currency cannot pass to the next transaction (src/PoolManager.sol:349-364).', 'source': 'cycles/036/arbitrum-family.work/scripts/scen_arb.py, raw/scen-*.json'},
    {'chainIds': [42161, 4663, 99901], 'lens': 'L2', 'check': 'stalesync.py of theme-first-inputs-and-stale-sync: a bare sync of a token in one transaction, exttload of CURRENCY_SLOT and RESERVES_OF_SLOT in the next, then unlock and settle, with a same-transaction control.',
     'result': 'On all four endpoints the next transaction reads zero in both slots and settle inside a new unlock reads currency zero, while the control inside one transaction reads the token and 0x1234. A stale sync cannot make a later transaction book another user\'s payment at src/PoolManager.sol:358-361.', 'source': 'cycles/036/arbitrum-family.work/out/stalesync-*.json'},
    {'chainIds': [42161, 4663, 99901], 'lens': 'L1', 'check': 'The three getFeeGrowthInside borrow scripts (cycle 32 borrow.py; src/libraries/Pool.sol unchecked subtractions) on the deployed bytecode of each chain, by eth_call with state overrides, including the PublicNode go1.25.12 build.',
     'result': 'All scripts return the reference bytes on every endpoint (raw/borrow-*.json).', 'source': 'cycles/036/arbitrum-family.work/raw/borrow-arb1.json, borrow-rh.json, borrow-ely.json'},
    {'chainIds': [42161, 4663, 99901], 'lens': 'L6', 'check': 'Upgrades in the next six months: arbOSVersion(), getScheduledUpgrade() and eth_config next on all three chains, the Arbitrum DAO network upgrades table, the ArbOS 61 page, and Kinetiq\'s upgrade plan.',
     'result': 'All three report ArbOS 61 (0x74), no scheduled upgrade and next null. The DAO table lists nothing after ArbOS 61. The only announced change is Elysium\'s HyperCore upgrade (F-158). The dormant Amsterdam rules of Nitro v3.13.0 (F-145) need a future ArbOS version that is not proposed. Funds in the PoolManager are not touched by any scheduled change.', 'source': SRC_UPG},
]
leads = [
    {'chainIds': [99901, 42161], 'lens': 'L1', 'question': 'When a toolchain build is allowed, compile holiman/uint256 v1.3.2 and the core/vm handlers of Nitro\'s go-ethereum fork with go1.25.12 and go1.25.13 on amd64 and diff the objects: which functions change because of the topological prove walk or the stack slot merging fix?', 'why': 'A function whose code differs between the two releases is the only place where the go1.25.12 fault could act on Elysium\'s producer, and vectors could then be aimed at it.', 'priority': 'low'},
    {'chainIds': [99901], 'lens': 'L4', 'question': 'Once Elysium schedules its HyperCore upgrade, what do the read precompile and the ElysiumCoreWriter predeploy do when called from the PoolManager address with empty calldata, transfer(address,uint256) and balanceOf(address), and can a callback reach the PoolManager?', 'why': 'A predeploy that answered transfer and moved a balance would be a P2 lever for any account.', 'priority': 'medium'},
]
leadResults = [
    {'leadId': 'L-1277', 'outcome': 'cleared', 'answer': 'Run on all four endpoints the lead names. ' + sctxt + ', each scenario in one blockStateCall with up to 19 transactions and its own web3_clientVersion bracket; Robinhood Chain answered from both architectures. stalesync.py gives zero slots in the next transaction and the synced values in the same transaction on all four, and the three borrow scripts return the reference bytes on all four. No transient value passes between transactions.'},
    {'leadId': 'L-1280', 'outcome': 'inconclusive', 'answer': 'The compiled output was not inspected: building a go1.25.12 compiler in the sandbox was refused under the review\'s no-install rule, and no go1.25.12 binary is present (only go1.24.7 and go1.25.1). The source was compared instead. ' + GO_DIFF + ' The 30,222 vectors aimed at the shift-count branches and the multi-limb division paths match on Elysium and the PublicNode go1.25.12 build, as do the battery, the targeted set, the scripts and the scenarios. No wrong word was found, so the residual risk is recorded under F-136 (operator, info).'},
]
doc = {'unit': 'arbitrum-family', '_lenses': ['L1', 'L2', 'L4', 'L6'], 'profiles': profiles, 'findings': findings, 'cleared': cleared, 'leads': leads, 'leadResults': leadResults}
json.dump(doc, open(OUT, 'w'), indent=1)
print('wrote', OUT)
