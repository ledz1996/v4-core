"""Write cycles/037/theme-rotating-endpoint-build-pins.research.json from the outputs in ../out. Usage: python3 -I build_research.py"""
import json, os
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
O = os.path.join(W, 'out')
REL = 'research/network-risk/cycles/037/theme-rotating-endpoint-build-pins.work/out/'
def L(f): return json.load(open(os.path.join(O, f)))

ALL = [1, 10, 8453, 130, 7777777, 480, 57073, 1868, 42220, 196, 42161, 4663, 99901, 137, 56, 43114, 143, 4326, 4217, 5042, 999]
ONE = [1, 8453, 130, 7777777, 480, 57073, 1868, 196, 42161, 99901, 43114, 143, 4326, 4217, 5042, 999]


def route(f):
    d = L(f); n = sum(d['itemCounts'].values())
    return d['url'], d['batches'], d['multiBuild'], {k: '%d/%d' % (v, n) for k, v in d['itemCounts'].items()}


def short(k): return k.split('/')[1] if k.startswith('bor/') else k


def table(files):
    rows = {}
    for f in files:
        d = L(f + '.json')
        for k, v in d['byBuild'].items():
            r = rows.setdefault(k, {})
            a = r.setdefault(d['set'], [0, 0, 0, 0, d['jobs']])
            a[0] += v['batches']; a[1] += v['units']; a[2] += v['mismatches']; a[3] = max(a[3], v['jobsComplete'])
    out = []
    for k, r in rows.items():
        out.append('%s: ' % short(k) + '; '.join('%s %d of %d jobs, %d units in %d batches, %d differing' % (s, a[3], a[4], a[1], a[0], a[2]) for s, a in r.items()))
    return ' | '.join(out)


routes = {f: route(f) for f in sorted(os.listdir(O)) if f.startswith('route-') and f.endswith('.json')}
rt = lambda f: '%s: %d batches of eight, %d with more than one build, items %s' % routes[f][:2] + (routes[f][2], json.dumps(routes[f][3])) if False else '%s: %d batches of eight, %d with more than one build, items %s' % (routes[f][0], routes[f][1], routes[f][2], json.dumps(routes[f][3]))

op = [L('rounds-op-opsdms.json'), L('rounds-op-opsdms-b.json')]
optot = {}
for d in op:
    for k, v in d['byBuild'].items():
        for p in (k[6:].split('|') if k.startswith('mixed:') else [k, k]): optot[p] = optot.get(p, 0) + v['batches']
opn = sum(optot.values()); opvec = sum(v['units'] for d in op for v in d['byBuild'].values())
pmin = min(optot.values()) / opn

POLY_SRC = [{'url': 'rpc https://polygon-bor-rpc.publicnode.com web3_clientVersion and eth_call batches, 2026-11-27, ' + REL + 'pin-polygon-*.json', 'supports': 'per-build counts and zero opcode mismatches on all five bor v2.11.1-private builds'}]

res = {
    'unit': 'theme-rotating-endpoint-build-pins',
    'profiles': [],
    'findings': [],
    'cleared': [
        {'chainIds': [137, 42220, 56, 10, 196, 4326, 4663] + [c for c in ONE if c not in (196, 4326)], 'lens': 'L1',
         'check': 'Task 1. How each public endpoint routes. 200 JSON-RPC batches of eight web3_clientVersion items to each rotating endpoint (50 to the others), 2026-11-27, script scripts/batch8.py. ' + ' || '.join(rt(f) for f in routes),
         'result': 'polygon-bor-rpc.publicnode.com, forno.celo.org, the three bsc-dataseed hosts, bsc-rpc.publicnode.com and celo.api.pocket.network never split a batch across builds (0 of 200), so a batch bracketed by web3_clientVersion is tied to one build there. mainnet.optimism.io (194 of 200), bsc.api.pocket.network (198 of 200), poly.api.pocket.network (199 of 200) and rpc.mainnet.chain.robinhood.com (48 of 50, the same Nitro b72783f release on linux-arm64 and linux-amd64) route each item on its own, so only sampling statements are valid there. Polygon build strings seen today: on polygon-bor-rpc.publicnode.com a863b8e5cce1 20.5 percent, 280514fa9fb7 18.5, ebcfea01452d 16.0, cb3d19c5f690 23.0, f2a2d63e69f6 22.0 (all bor v2.11.1-private, go1.26.10); on poly.api.pocket.network bor ec9ea5f13f70 v2.11.2 23.8 percent, host-85-195-124-57 v2.11.2 48.8, rom247-smc-n1 v2.11.0-private 16.4, polygon-rpc-fg-2 v2.11.2 6.7, 53506be1b2ee v2.11.1-private 1.8, 769686f18c80 v2.11.1-private 1.5, matic-full-node-de-1 v2.11.2 0.9, and 59db6d2d40c6 v2.11.1-private, which answered only in the later sampling runs. Celo forno answers reth v2.2.0-74cc8bb 83.5 percent and op-geth c7ed55b8 16.5 percent. BNB Chain dataseed answers Geth v1.8.2 84 to 89.5 percent and v1.8.2-4e1c8247 10.5 to 16 percent. OP Mainnet answers op-reth v0.0.0-dev-unknown 62.8 percent and v2.8.1-72207294 37.2 percent. Base and Elysium answered one build each to single requests and to a three item batch; some of their eight item batches came back with an item that had no result.',
         'source': REL + 'route-*.json'},
        {'chainIds': [137], 'lens': 'L1',
         'check': 'Task 2 (L-1315). polygon-bor-rpc.publicnode.com, 2026-11-27 23:03 to 23:08 UTC. Every request a batch [web3_clientVersion, eth_call x K, web3_clientVersion], and every job resent until each of the five builds had answered it with both brackets equal (scripts/pinrun.py). Sets: the MULMOD, ADDMOD, DIV, SDIV, MOD, SMOD, EXP, SHL, SHR, SAR, BYTE, SIGNEXTEND, DIVUP and MULDIV512 vectors of battery.py (seed 20261124) and targeted.py (seed 681), 158,342 vectors (MULMOD 32,513, MULDIV512 29,433, ADDMOD 14,359, SHL, SHR and SAR 11,693 each, SIGNEXTEND and BYTE 7,921 each, DIVUP 7,024, DIV, SDIV, MOD and SMOD 5,860 each, EXP 652); provevec.py (seed 20261127), 30,222 vectors; pmdiff.py 250 scripts (seed 7_2026_11_24) and pmdiff2.py 300 scripts (seed 11_2026_11_24) on the deployed PoolManager code (sha256 a7aaa3ba...). Per build: ' + table(['pin-polygon-ops', 'pin-polygon-provevec', 'pin-polygon-pmdiff', 'pin-polygon-pmdiff2']),
         'result': 'Every one of the five builds answered every vector and every script at least once, and no batch was mixed. No opcode vector differs on any build. The script differences are the 19 pmdiff and 20 pmdiff2 scripts that opcodes/pmdiff.json and opcodes/pmdiff2.json already list for Polygon; each of the 39 gave one and the same answer on all five builds and every repeat. In each the calls before the first difference equal Ethereum (refetched today, equal to the stored reference hash), and at the first difference Polygon fails with empty return data where Ethereum succeeds or reverts with a selector, or the whole script returns nothing: the known gas-limited swaps of opcodes/pmdiff-gas.json (out/firstdiff-pmdiff*.json). The five private builds compute these opcodes and the PoolManager scripts identically to each other and to the specification.',
         'source': REL + 'pin-polygon-ops.json'},
        {'chainIds': [42220], 'lens': 'L1',
         'check': 'Task 2 (L-1316). forno.celo.org, same method and sets, 2026-11-27 23:03 to 23:07 UTC, builds reth v2.2.0-74cc8bb and Geth v0.1.0-untagged-c7ed55b8 (op-geth, go1.24.13). Per build: ' + table(['pin-celo-ops', 'pin-celo-provevec', 'pin-celo-pmdiff', 'pin-celo-pmdiff2']),
         'result': 'Both backends answered all 158,342 subset vectors, all 30,222 provevec vectors and all 550 scripts at least once, with no mismatch and no mixed batch. Neither backend lacks any opcode subset or script.',
         'source': REL + 'pin-celo-ops.json'},
        {'chainIds': [56], 'lens': 'L1',
         'check': 'Task 2 on BNB Chain. bsc-dataseed1.bnbchain.org, same method and sets, builds Geth v1.8.2 and Geth v1.8.2-4e1c8247-20261104 (the latter about 11 percent of answers; a second pass pinned to it, out/pin-bscds1-ops-b.json, completed the 20 subset jobs it had not reached in 60 tries). Per build: ' + table(['pin-bscds1-ops', 'pin-bscds1-ops-b', 'pin-bscds1-provevec', 'pin-bscds1-pmdiff', 'pin-bscds1-pmdiff2']),
         'result': 'Both dataseed builds answered every vector and every script at least once with the reference word and the Ethereum reference hash. bsc-rpc.publicnode.com answers from one build (reth-bsc v0.1.4-hotfix-23b510f), so the theme does not apply to it.',
         'source': REL + 'pin-bscds1-ops.json'},
        {'chainIds': [56, 196, 4326], 'lens': 'L1',
         'check': 'Task 3 (L-1313). provevec.py vectors (30,222: SHL, SHR and SAR for every count 0 to 320 and counts near 2^32, 2^64, 2^128 and 2^255, every BYTE index and SIGNEXTEND width 0 to 39 plus 2^64+3 and 2^256-1, DIV, MOD, SDIV, SMOD, ADDMOD, MULMOD and MULDIV512 by divisors of one to four limbs) in bracketed batches on bsc-rpc.publicnode.com (reth-bsc/v0.1.4-hotfix-23b510f, 26 batches), rpc.xlayer.tech (reth/v2.3.0-f60420a xlayer/v0.0.7, 26 batches) and mainnet.megaeth.com/rpc (mega-reth/v2.3.1-4499c42@mnet-ash-rpc-2, 202 batches of 150 vectors because batches of 1,200 vectors were refused with HTTP 413 payload too large). The same vectors ran on all five Polygon builds, both Celo backends and both BNB dataseed builds above.',
         'result': 'All 30,222 vectors return the specified word on every build named, with both brackets equal in every batch. Shift counts at and past 256, at 2^32 + 1 and near 2^64 return 0 (or all ones for SAR of a negative word), as the specification requires.',
         'source': REL + 'prove-bsc-rpc_publicnode_com.json'},
        {'chainIds': [56, 196, 42220, 4326], 'lens': 'L1',
         'check': 'L-1314. What ruint PR 603 changed, read from CHANGELOG.md and src/bits.rs at v1.18.0, v1.19.0 and v1.20.0, and whether the revm-interpreter 35.0.1, 37.0.3 and 43.0.2 handlers for SHL, SHR, SAR and BYTE bound the count or index before calling ruint.',
         'result': 'The 1.20.0 changelog lists #603 as a fix of overflow-flag false negatives in overflowing_shl and overflowing_shr, with the dependent checked, strict and saturating shifts and byte(). The bits.rs diff from 1.19.0 to 1.20.0 shows three changes. (1) overflowing_shl and overflowing_shr now OR the limbs that are shifted out entirely, and for shl the masked top bits, into the carry; the shifted value itself is unchanged. 1.18.0 and 1.19.0 both have the narrower carry. (2) The u64, u128 and u256 fast paths of wrapping_shl and wrapping_shr cast the count with rhs as u32, which in 1.19.0 turns a count of 2^32 + k into k; 1.20.0 replaces it with shift_amount, which saturates at u32::MAX. These fast paths came with #574 in 1.19.0. In 1.18.0 wrapping_shl and wrapping_shr are overflowing_shl(rhs).0 and overflowing_shr(rhs).0, which return zero once rhs / 64 >= LIMBS, so 1.18.0 has no truncating cast. (3) byte() gains a bounds assert on the big-endian path only. Both earlier readings were therefore partly right: the cast exists in 1.19.0 (MegaETH) and not in 1.18.0 (reth-bsc, X Layer, Celo reth), and the flag fix touches both. None of it reaches an EVM word. In revm-interpreter 35.0.1, 37.0.3 and 43.0.2 the shl and shr handlers compute shift = as_usize_saturated!(op1) and call op2 << shift or op2 >> shift only when shift < 256, else return 0; sar calls arithmetic_shr only when shift < 256, else returns all ones or 0 by the sign bit; byte calls op2.byte(31 - o1) only when o1 < 32. The handlers use the wrapping value and never the overflow flag. On the src/ side every shift count is a constant or a value below 256 (BitMath.sol:15-22 and 40-45, TickMath.sol:142-145) and every BYTE index is masked with 0x1f (BitMath.sol:21, 45), so no line of src/ can produce a count of 2^32 or more.',
         'source': 'https://raw.githubusercontent.com/recmo/uint/v1.20.0/CHANGELOG.md; https://raw.githubusercontent.com/recmo/uint/v1.19.0/src/bits.rs; https://raw.githubusercontent.com/recmo/uint/v1.18.0/src/bits.rs; https://static.crates.io/crates/revm-interpreter/revm-interpreter-35.0.1.crate (src/instructions/bitwise.rs:96-143, macros.rs:185-189); revm-interpreter-37.0.3 and 43.0.2 bitwise.rs:107-158; src/libraries/BitMath.sol:15-22'},
        {'chainIds': [10], 'lens': 'L1',
         'check': 'Task 4. mainnet.optimism.io routes every item of a batch on its own, so no eth_call can be tied to one of its two builds. From the bracket answers of this run (%d samples) the smaller share is %.3f (op-reth v2.8.1-72207294) and the larger %.3f (op-reth v0.0.0-dev-unknown). A request sent n times reaches both builds with probability 1 - p^n - q^n; 99.9 percent needs n >= 16 at the observed share and 17 at the upper 95 percent bound of the larger share (0.662). For all 214 eth_call chunks of the set to have reached both builds with 99.9 percent, n >= 28. The DIV, SDIV, MOD, SMOD, DIVUP, MULMOD, MULDIV512, SHL, SHR and SAR vectors of battery.py and targeted.py (127,489) were sent 28 times in 2,996 batches, %d vectors in all, 2026-11-27 23:06 to 23:20 UTC.' % (opn, pmin, 1 - pmin, opvec),
         'result': 'No vector differs in any of the 28 rounds. At the observed shares each chunk reached both builds with probability 0.999994 and all 214 chunks with probability 0.9988 (0.998 at the upper bound). This is a sampling statement: it says that a build answering at least 35 percent of requests computed each chunk at least once, and nothing about a third build that might answer too rarely to appear among %d bracket answers.' % opn,
         'source': REL + 'rounds-op-opsdms.json'},
        {'chainIds': [56, 137], 'lens': 'L1',
         'check': 'Sampling on the per-item gateways bsc.api.pocket.network and poly.api.pocket.network: provevec three times and the opcode subset set twice, batches bracketed only to sample shares.',
         'result': 'BNB gateway: 407,350 vector answers, no mismatch; brackets name Geth v1.8.2, v1.8.2-54afaff4 (go1.25.14), v1.7.8 (go1.25.12), reth-bsc v0.1.4-hotfix and reth-bsc v0.1.2-968d07d. Polygon gateway: 352,550 vector answers, no mismatch, 90 requests refused for size (code -32602, request size limit); brackets name six bor builds. Neither gateway lets an answer be tied to a build, and the rarest builds (reth-bsc v0.1.2 at 2.3 percent, matic-full-node-de-1 at 0.9 percent) would need about 300 and 730 repetitions per chunk for a 99.9 percent statement, which was not attempted. These gateways are not the endpoints listed in networks.json.',
         'source': REL + 'rounds-bscpocket-ops.json'},
        {'chainIds': ONE, 'lens': 'L1',
         'check': 'Whether the endpoints of the other networks rotate between builds (50 batches of eight web3_clientVersion items each).',
         'result': 'Ethereum (reth v2.11.0-b9abbcc), Base (Base reth v2.5.2 v1.5.6), Unichain, Ink and Soneium (op-reth v2.10.0-rc.4), Zora (conduit-op-reth v2.5.1), World Chain (world-chain v2.8.2), X Layer (reth v2.3.0 xlayer v0.0.7), Arbitrum One (nitro v3.13.0-rc.9 arm64), Elysium (nitro vlocal), Avalanche (avalanchego 1.15.3), Monad (0.16.7), MegaETH (mega-reth v2.3.1), Tempo (v1.19.2), Arc (arc/v1) and HyperEVM each answered with one build string. The theme does not apply to these 16 networks. Robinhood Chain answers from the same Nitro release on two architectures and is recorded as a lead.',
         'source': REL + 'route-ethereum-rpc_publicnode_com.json'},
    ],
    'leads': [
        {'chainIds': [4663], 'lens': 'L1',
         'question': 'rpc.mainnet.chain.robinhood.com routes each item between nitro v3.13.0-rc.9+b72783f linux-arm64 and linux-amd64 (48 of 50 batches mixed). Which earlier Robinhood Chain vectors and scripts reached the arm64 build, and do 30,222 provevec and 158,342 subset vectors repeated until both architectures answered with 99.9 percent show any difference?',
         'why': 'The Go compiler emits different code for the two architectures, and earlier endpoint results on Robinhood Chain are an unrecorded mix of both.', 'priority': 'low'},
    ],
    'leadResults': [
        {'leadId': 'L-1315', 'outcome': 'cleared',
         'answer': 'No stored Polygon output of cycles 32 to 36 records a bracket per request: the battery, targeted, pmdiff and pmdiff2 files of 032, 034 and 036 established-l1 (and 036 established-l1.verify) carry one result per chain, and 034 clientversions.txt names only two of the five builds at 15:11. Those results are relabelled as a sample over an unrecorded mix of the publicnode builds. This cycle tied every vector of the MULMOD, ADDMOD, division, EXP, shift, BYTE, SIGNEXTEND, DIVUP and mulDiv subsets (158,342), provevec (30,222) and both script sets (550) to each of cb3d19c5f690, 280514fa9fb7, a863b8e5cce1, ebcfea01452d and f2a2d63e69f6 at least once, with no opcode mismatch and only the 39 known gas-limited scripts different, identically on all five.'},
        {'leadId': 'L-1316', 'outcome': 'cleared',
         'answer': 'Of the Celo outputs of cycles 32 to 36, only two are tied to builds. 032 pinned-stakely.json (celo-json-rpc.stakely.io): reth 74cc8bb 91,929 vectors, 7680d6d 58,800, 3cbf835 20,400, 06140ff 14,400. 034 pinned-forno.json: reth 74cc8bb 155,144 vectors and op-geth c7ed55b8 30,385, the latter in 51 of 310 jobs, so op-geth had not answered every vector. The battery, targeted, pmdiff and pmdiff2 runs on forno in 032, 034 and 036 op-stack-custom-gas carry no brackets, and the send2000 runs of 035 and 036 bracketed with separate requests whose before and after answers differ in several batches, so neither can be split; they are relabelled as samples. This cycle tied all 158,342 subset vectors, 30,222 provevec vectors and 550 scripts to each of reth 74cc8bb (725, 93, 360 and 346 batches) and op-geth c7ed55b8 (133, 27, 65 and 76 batches), with no mismatch. Neither backend lacks any opcode or script.'},
        {'leadId': 'L-1313', 'outcome': 'cleared',
         'answer': 'provevec.py gave the specified word on all 30,222 vectors on reth-bsc v0.1.4-hotfix-23b510f, X Layer reth v2.3.0-f60420a and mega-reth v2.3.1-4499c42, each batch bracketed and equal, and on the five Polygon, two Celo and two BNB dataseed builds.'},
        {'leadId': 'L-1314', 'outcome': 'cleared',
         'answer': 'PR 603 (ruint 1.20.0) widens the overflow flag of overflowing_shl and overflowing_shr to include limbs shifted out entirely, replaces the truncating rhs as u32 of the wrapping shift fast paths (present only since 1.19.0, #574) with a saturating cast, and adds a big-endian bounds assert to byte(). revm-interpreter 35.0.1, 37.0.3 and 43.0.2 call the shifts only for counts below 256 and byte() only for indices below 32 and never read the flag, so no EVM result on the ruint 1.18.0 or 1.19.0 builds can change.'},
    ],
}
json.dump(res, open(os.path.join(os.path.dirname(W), 'theme-rotating-endpoint-build-pins.research.json'), 'w'), indent=1)
print('written')
