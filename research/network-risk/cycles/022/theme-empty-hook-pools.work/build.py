"""Writes ../theme-empty-hook-pools.research.json from the raw data of this work directory."""
import json, os, collections
W = os.path.dirname(os.path.abspath(__file__)); R = lambda f: json.load(open(os.path.join(W, 'raw', f)))
NETS = json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))['networks']
ALL = [n['chainId'] for n in NETS]; NAME = {n['chainId']: n['name'] for n in NETS}
DEC = R('decimals.json')
WD = 'research/network-risk/cycles/022/theme-empty-hook-pools.work/'
NAMES = ['afterRemoveReturnsDelta', 'afterAddReturnsDelta', 'afterSwapReturnsDelta', 'beforeSwapReturnsDelta', 'afterDonate', 'beforeDonate', 'afterSwap', 'beforeSwap', 'afterRemove', 'beforeRemove', 'afterAdd', 'beforeAdd', 'afterInit', 'beforeInit']
def det(c):
    f = os.path.join(W, 'raw', 'detail_%d.json' % c)
    if os.path.exists(f): return json.load(open(f))
    f = os.path.join(W, 'raw', 'posm_%d.json' % c)
    if not os.path.exists(f): return None
    d = json.load(open(f)); C = json.load(open(os.path.join(W, 'raw', 'census_%d.json' % c)))
    ticked = {p['poolId'] for p in d['pools']}
    pools = []
    for p in d['pools']:
        live = [{'salt': '0x%064x' % r['tokenId'], 'tokenOwner': r['owner'], 'addFrom': [], 'liquidity': r['liquidity'], 'tickLower': r['tickLower'], 'tickUpper': r['tickUpper'],
                 'amount0raw': r['amount0raw'], 'amount1raw': r['amount1raw'], 'thirdParty': r['thirdParty']} for r in p['positions']]
        pools.append({'poolId': p['poolId'], 'hook': p['hook'], 'kind': p['kind'], 'flagBits': p['flagBits'], 'flags': [NAMES[i] for i in range(14) if p['flagBits'] >> i & 1], 'creator': p['creator'],
                      'activeLiquidity': p['liquidity'], 'livePositions': live, 'thirdPartyLive': p['thirdPartyLive'], 'currency0': p['currency0'], 'currency1': p['currency1'], 'tickCheck': p['tickCheck']})
    return {'chainId': c, 'pools': pools, 'skippedNoTicks': [p for p in C['hookPools'] if p['poolId'] not in ticked], 'method': 'posm'}
def fmt(c, cur, raw):
    if raw is None: return '?'
    sym, dec = DEC.get('%d:%s' % (c, cur), ('units', 0))
    if not isinstance(dec, int): dec = 0
    v = raw / 10 ** dec
    return ('%.4g %s' % (v, 'native' if sym == 'native' else sym))
tab = R('table.json'); xc = R('xchain.json'); ec = R('emptycall.json'); gs = R('gap-summary.json')
# ---------------- per network census sentence
lines = []
for c in ALL:
    t = tab[str(c)]; d = det(c)
    s = '%s (%d): %s pools to block %s, %d distinct hooks, %d empty and %d delegated, %d pools on them' % (NAME[c], c, format(t['pools'], ','), format(t['block'], ','), t['hooks'], t['empty'], t['deleg'], t['poolsOn'])
    if d:
        live = [p for p in d['pools'] if p['livePositions']]
        third = [p for p in d['pools'] if p['thirdPartyLive']]
        gated3 = [p for p in third if p['flagBits'] & 0x330]
        s += ', %d with live positions, %d with a position of another account than the creator, %d of those with bit 9, 8, 5 or 4' % (len(live), len(third), len(gated3))
        if d.get('skippedNoTicks'): s += ' (%d pools without any initialized tick, so without liquidity, skipped)' % len(d['skippedNoTicks'])
        if d.get('method') == 'posm': s += ' (positions from positionInfo of all %s PositionManager tokens, because no public endpoint served complete BNB Smart Chain log history; the PositionManager positions account for the liquidityGross of every initialized tick)' % format(json.load(open(os.path.join(W, 'raw', 'posm_%d.json' % c)))['tokensScanned'], ',')
    lines.append(s)
census_text = '; '.join(lines) + '.'
# ---------------- gated third-party pools
g3 = []
for c in ALL:
    d = det(c)
    if not d: continue
    for p in d['pools']:
        if p['thirdPartyLive'] and p['flagBits'] & 0x330: g3.append((c, p))
def pdesc(c, p):
    pos = []
    for q in p['livePositions']:
        who = q['tokenOwner'] or ','.join(q['addFrom'])
        pos.append('token %d owned by %s (%s, %s)%s' % (int(q['salt'], 16), who[:10], fmt(c, p['currency0'], q['amount0raw']), fmt(c, p['currency1'], q['amount1raw']), ' third party' if q['thirdParty'] else ' creator'))
    return '%s pool %s (hook %s, bits 0x%x %s, creator %s, liquidity %s): %s' % (NAME[c], p['poolId'], p['hook'], p['flagBits'], '/'.join(p['flags']), (p['creator'] or '?')[:10], format(p['activeLiquidity'], ','), '; '.join(pos))
g3_text = ' '.join(pdesc(c, p) + '.' for c, p in g3)
open(os.path.join(W, 'raw', 'g3.txt'), 'w').write(g3_text)
# ---------------- empty-call result
ec_bad = {c: {t: v for t, v in r['calls'].items() if not (v['ok'] and v['ret'] == '0x')} for c, r in ec['chains'].items()}
ec_n = sum(len(r['calls']) for r in ec['chains'].values())
# ---------------- gap summary text
gtxt = []
for k, v in gs.items():
    rg = v['answeredRanges']
    gtxt.append('%s %s: %d windows answered%s, %d refused, %d sampled blocks, %d log/receipt differences, %d short receipt sets' % (v['chainId'], k.split(' ')[1], v['windowsAnswered'], (' between blocks %s and %s' % (format(rg[0][0], ','), format(rg[-1][1], ','))) if rg else '', v['windowsError'], v['sampledBlocks'], v['logsVsReceiptsMismatch'], v['receiptCountShort']))
gap_text = '; '.join(gtxt) + '.'
sim137 = R('sim_137.json'); sim43114 = R('sim_43114.json')
out = {'unit': 'theme-empty-hook-pools', 'profiles': [], 'findings': [], 'cleared': [], 'leads': [], 'leadResults': []}
# =============== FINDING 1: F-004 update
f1_mech = ('1. initialize checks only the low 14 bits of the hook address and never reads its code (src/PoolManager.sol:126, src/libraries/Hooks.sol:109-127). '
 '2. For liquidityDelta <= 0, beforeModifyLiquidity calls beforeRemoveLiquidity when bit 9 is set (src/libraries/Hooks.sol:203-204) and afterModifyLiquidity calls afterRemoveLiquidity when bit 8 is set (src/libraries/Hooks.sol:232-243); donate calls the donate hooks for bits 5 and 4 (src/libraries/Hooks.sol:317-335). '
 '3. callHook makes a plain CALL with all gas (src/libraries/Hooks.sol:134). An address without code returns success and no data, so result.length < 32 and the call reverts with InvalidHookResponse (src/libraries/Hooks.sol:152-154). The only bypass is msg.sender == hook (src/libraries/Hooks.sol:171-175, 217), which nobody holds for an empty address. '
 '4. This cycle measured the call on all 21 networks: an eth_call from each PoolManager address with beforeRemoveLiquidity calldata to three seeded random addresses, to 0x...20, to 0x...dead0030 and to every empty hook address of that network returned success with empty data in all %d calls (raw/emptycall.json), so the freeze has the same shape everywhere. '
 '5. Census, pool ids recomputed as keccak256(abi.encode(PoolKey)) (src/types/PoolId.sol:10-16) for every Initialize row, EXTCODESIZE of every distinct hook at one block, ModifyLiquidity logs of the pools on empty or delegated hooks, PositionManager ownerOf for each live position and tx.from of the Initialize transaction as creator: %s '
 '6. Pools with bit 9, 8, 5 or 4 and a live position of an account other than the creator: %s '
 '7. eth_call of each third-party owner\'s full DECREASE_LIQUIDITY plus TAKE_PAIR through the PositionManager reverts with 0x1e048e1d (InvalidHookResponse) on Polygon and Avalanche; with a stub hook that returns its selector placed at the hook address by state override the same call succeeds, so the empty hook is the only obstacle (raw/sim_137.json, raw/sim_43114.json).') % (ec_n, census_text, g3_text or 'none')
out['findings'].append({
 'ref': 'F-004', 'title': 'A pool whose hook address has no code on its own network freezes every position when the address sets a removal flag, and live pools on Polygon and Avalanche hold third-party positions frozen this way',
 'chainIds': ALL, 'lens': 'L1', 'assumptions': ['A7', 'A13'], 'effect': 'freeze', 'actor': 'pool-creator', 'severity': 'medium',
 'difference': 'No opcode difference: on all 21 networks a call to an address without code returns success and no data (measured). The networks differ only in which hook addresses are empty: the hook 0xf8c3f4243c4d8c02831a718a7978fd869f094300 (bits 9 and 8) has 2,488 bytes of code on Ethereum, OP Mainnet, Base, Unichain and Arbitrum One and none on Polygon, BNB Smart Chain, World Chain and Avalanche, because it was deployed through the CREATE2 deployer 0x4e59b44847b379578588920ca78fbf26c0b4956c on some networks only, and pool creators on the others named the same address.',
 'mechanism': f1_mech,
 'impact': 'Principal and fees of every position in such a pool, for every holder. Measured third-party exposure is dust: on Polygon about 0.019 POL and 0.0015 USDC across two positions, on Avalanche about 0.045 AVAX and 0.32 USDt across six positions, and nothing on BNB Smart Chain and Base, where the pools on 0xf8c3f424...4300 hold only the positions of their creators. No funds outside these pools are reachable, because the deltas of a removal only involve the pool\'s own currencies and its hook.',
 'preconditions': 'A pool creator names a flagged address that has no code on that network, and other accounts add liquidity. No role is needed for either step. The third-party owners in the Polygon and Avalanche pools are smart accounts and EOAs that also create pools on the same hooks, so they may be one operator; that link was not established.',
 'mitigations': 'Interfaces and routers should read the code at the hook address on the network itself before listing a pool or adding liquidity, and should not infer it from another network. Core could reject an empty hook address in initialize, which would not stop later loss of code (F-013).',
 'coreRefs': ['src/PoolManager.sol:126', 'src/PoolManager.sol:156-183', 'src/libraries/Hooks.sol:109-155', 'src/libraries/Hooks.sol:171-175', 'src/libraries/Hooks.sol:195-245', 'src/libraries/Hooks.sol:317-335', 'src/types/PoolId.sol:10-16'],
 'sources': [
  {'url': 'src/libraries/Hooks.sol:134', 'supports': 'hook call is a plain CALL with all gas'},
  {'url': 'src/libraries/Hooks.sol:152-154', 'supports': 'return data shorter than 32 bytes reverts with InvalidHookResponse'},
  {'url': 'src/libraries/Hooks.sol:203-204', 'supports': 'beforeRemoveLiquidity called for liquidityDelta <= 0 when bit 9 is set'},
  {'url': 'rpc: eth_call from each PoolManager to empty addresses on all 21 networks, file ' + WD + 'raw/emptycall.json', 'supports': 'success with empty return data on every network'},
  {'url': 'rpc: census per network, files ' + WD + 'raw/census_<chainId>.json and raw/detail_<chainId>.json', 'supports': 'empty and delegated hooks, pools on them, live positions, owners and creators'},
  {'url': 'rpc: eth_call PositionManager.modifyLiquidities on https://polygon.gateway.tenderly.co and https://avalanche.gateway.tenderly.co, files ' + WD + 'raw/sim_137.json and raw/sim_43114.json', 'supports': 'removal reverts with 0x1e048e1d as is and passes with a selector stub at the hook address'},
  {'url': 'rpc: eth_getCode and EXTCODESIZE of the hook addresses on all 21 networks, file ' + WD + 'raw/xchain.json', 'supports': '0xf8c3... has code on 1, 10, 8453, 130, 42161 and none on 137, 56, 480, 43114'}],
 'evidence': 'primary'})
# =============== FINDING 2: F-013 update (delegated hook addresses)
deleg = collections.defaultdict(dict)
for c in ALL:
    for h in xc['hooks']:
        r = xc['chains'][str(c)]
        if 'size' in r and r['size'][h] == 23 and r['codePrefix'].get(h, '').startswith('0xef0100'): deleg[h][c] = (r['nonce'][h], '0x' + r['codePrefix'][h][8:48])
dl = '; '.join('%s on %s' % (h, ', '.join('%s (nonce %d, delegate %s)' % (NAME[c], n, t[:10]) for c, (n, t) in v.items())) for h, v in sorted(deleg.items()))
dchains = sorted({c for v in deleg.values() for c in v})
d3 = []
for c in ALL:
    d = det(c)
    if not d: continue
    for p in d['pools']:
        if p['kind'] == 'delegated' and p['livePositions']:
            th = [q for q in p['livePositions'] if q['thirdParty']]
            d3.append('%s pool %s (hook %s, bits 0x%x, creator %s): %d live positions, %d of other accounts%s' % (NAME[c], p['poolId'][:18], p['hook'][:10], p['flagBits'], (p['creator'] or '?')[:10], len(p['livePositions']), len(th),
                      (' (' + '; '.join('token %d of %s holding %s and %s' % (int(q['salt'], 16), (q['tokenOwner'] or '?')[:10], fmt(c, p['currency0'], q['amount0raw']), fmt(c, p['currency1'], q['amount1raw'])) for q in th) + ')') if th else ''))
out['findings'].append({
 'ref': 'F-013', 'title': 'Hook addresses that are EIP-7702 delegated accounts are live on five networks, their holders have repointed them, and one Ethereum pool whose delegated hook sets the after remove liquidity and return delta flags holds a third-party position',
 'chainIds': dchains, 'lens': 'L1', 'assumptions': ['A7'], 'effect': 'both', 'actor': 'pool-creator', 'severity': 'medium',
 'difference': 'On the networks listed, a hook address can be an EOA whose code is a 23 byte delegation indicator 0xef0100 followed by a target address, which its holder can change or clear in any later transaction. Measured: ' + dl + '. The same hook address points at different targets on different networks, so the holders have set the delegation per network.',
 'mechanism': 'initialize accepts any address whose low 14 bits form a valid flag set (src/libraries/Hooks.sol:109-127). Bits 0x258b mean before initialize, after add liquidity, after remove liquidity, before swap, before swap returns delta, after add liquidity returns delta and after remove liquidity returns delta. With bit 8 and bit 0 the hook delta returned by afterRemoveLiquidity is subtracted from the remover\'s delta without bound and credited to the hook (src/libraries/Hooks.sol:232-243, src/PoolManager.sol:177-183), and with no code at all every removal reverts (src/libraries/Hooks.sol:152-154). The holder of the hook account can therefore repoint the delegation to code that takes all of a removal, or clear it to freeze removals. Live pools on delegated hooks with liquidity: ' + '; '.join(d3) + '.',
 'impact': 'Removal proceeds of the third-party positions in pools on delegated hooks with bits 8 and 0, measured on Ethereum at about 0.0035 ETH in pool 0x992c0ab6. Swappers in pools with the before swap returns delta flag. No other pools.',
 'preconditions': 'The victim adds liquidity to a pool whose hook address is a delegated EOA. Only the holder of that account, the hook author, can act.',
 'mitigations': 'Routers and interfaces should treat a hook whose code starts with 0xef0100 as mutable and warn or refuse.',
 'coreRefs': ['src/libraries/Hooks.sol:109-127', 'src/libraries/Hooks.sol:152-154', 'src/libraries/Hooks.sol:232-243', 'src/PoolManager.sol:177-183'],
 'sources': [{'url': 'rpc: EXTCODESIZE, eth_getCode and eth_getTransactionCount of every empty or delegated hook on all 21 networks, file ' + WD + 'raw/xchain.json', 'supports': 'delegation indicators, targets and nonces per network'},
             {'url': 'rpc: ModifyLiquidity logs and PositionManager ownerOf, files ' + WD + 'raw/detail_<chainId>.json', 'supports': 'live positions and their owners in pools on delegated hooks'},
             {'url': 'https://raw.githubusercontent.com/ethereum/EIPs/master/EIPS/eip-7702.md', 'supports': 'delegation indicator 0xef0100 || address, changeable by later authorizations'},
             {'url': 'src/libraries/Hooks.sol:232-243', 'supports': 'afterRemoveLiquidity return delta subtracted from the caller and credited to the hook'}],
 'evidence': 'primary'})
# =============== CLEARED
c = out['cleared']
nrows = sum(tab[str(x)]['pools'] for x in ALL)
c.append({'chainIds': [1], 'lens': 'L1', 'check': 'Lead L-953: which rows, clearances and findings rest on the cycle 17 hook census (hooks7702.json) and the cycle 5 Initialize scan that fed it.',
 'result': 'The cycle 5 scan stores rows as [block, pool id topic, currency0, currency1, fee, tickSpacing, hooks, transaction hash] (cycles/005/theme-shared-hooks.work/init_census.py:36). hooks7702.py read index 7, the transaction hash, as the pool id for the StateView.getLiquidity call and for the poolId field (cycles/017/ethereum-reference.work/hooks7702.py:42 and 45); its hook selection used index 6 and is correct (line 11). So every one of its 21 rows has a wrong poolId and a liquidity reading taken at an unused slot, and its counts of empty and delegated hooks are right for its block. The census stored only those 21 rows; it never read liquidity for pools on hooks with code, so no other row exists to be wrong. What rests on the wrong fields: cleared entry 1489 (cycle 17, also CLEARED.md line 351), the cycle 17 attempt of lead L-046 in ledger.json, the sentence in OPCODES.md line 345 that the 21 pools give no third party a path to funds, and cycle 21 l821.py, which recomputed the ids itself and is correct (cleared 1811). The other readers of the cycle 5 and cycle 6 rows (cycles/005/theme-shared-hooks.work/summ.py:29, klik_frozen_pools.py:17-19, cycles/006/theme-currency-lists.work/census2.py:40, lists.py:27-29, cycles/022/theme-outflow-census.work/census3.py:22) index the rows by field 1 and use field 7 only as a transaction hash. Cleared entries 658 to 678 use only the hook addresses. With the ids recomputed, the Ethereum answer is now 24 pools on 21 hooks (16 empty, 5 delegated) at block 26,496,175; on two of them other accounts hold positions, both on delegated hooks (finding F-013 above). The pool on an empty hook with bit 9 holds only its creator\'s position (F-004).',
 'source': 'cycles/017/ethereum-reference.work/hooks7702.py:42-45; cycles/005/theme-shared-hooks.work/init_census.py:36; ' + WD + 'raw/census_1.json, raw/detail_1.json'})
c.append({'chainIds': ALL, 'lens': 'L1', 'check': 'Whether the pool id stored in the earlier Initialize scans (cycle 5 and cycle 6, extended to head this cycle) equals keccak256(abi.encode(PoolKey)) as src/types/PoolId.sol:10-16 computes it.',
 'result': 'Yes for every row. %s pool keys on the 21 networks were encoded as five 32 byte words (tickSpacing sign extended) and hashed with a Keccak-256 written for this unit and checked against the reference copy (build/kec from kec.c); zero rows differ from the event topic. The earlier scans are complete up to their stated end blocks as far as the gap checks below show, and this cycle appended the Initialize logs from each end block to head (raw/initext_<chainId>.json.gz).' % format(nrows, ','),
 'source': WD + 'raw/census_<chainId>.json (idMismatch is empty on every network), kec.c, census.py'})
c.append({'chainIds': ALL, 'lens': 'L4', 'check': 'Task 3, last part: on which of the 21 networks an address without code does not answer a call from the PoolManager with success and empty data.',
 'result': 'None among the addresses that pools use. eth_call from each PoolManager address with beforeRemoveLiquidity calldata to three addresses from random.Random(\'theme-empty-hook-pools-022\') (%s), to 0x0000000000000000000000000000000000000020, to 0x00000000000000000000000000000000dead0030 and to every hook address that is empty on that network returned success and 0x in all %d calls on all 21 networks, with web3_clientVersion read before and after each network. The special ranges found earlier change the outcome only for addresses that no pool uses: BNB Smart Chain CAS20 ordinals 0x00 and 0x01 and three fixed addresses revert every call after Jenner (F-139), which still freezes a pool flagged for them, and Arc fails only value-carrying calls (F-125), which hook calls are not (value 0 at src/libraries/Hooks.sol:134). Cleared 1392 covers precompiles and system contracts.' % (', '.join(ec['random']), ec_n),
 'source': WD + 'raw/emptycall.json; src/libraries/Hooks.sol:134'})
sims = [r for r in sim137['runs'] + sim43114['runs'] if r['case'] == 'create2Replay']
c.append({'chainIds': [137, 43114, 56, 480], 'lens': 'L5', 'check': 'Task 3: who can place code at 0xf8c3f4243c4d8c02831a718a7978fd869f094300 on the networks where it is empty, and does that account gain control of the removal callbacks.',
 'result': 'Anyone can place code there, and nobody gains control. On Ethereum the address was created at block 21,696,306 by transaction 0x7311a22f...2811 from 0xb7a249bd to the CREATE2 deployer 0x4e59b448 with salt 0x...0492 and 3,272 bytes of init code; keccak256(0xff ++ 0x4e59b448... ++ salt ++ keccak256(initcode)) reproduces the address. The deployer has its 69 byte code on Polygon, Avalanche, BNB Smart Chain and World Chain, and the original call carries no signature of its own, so any account can send the same call there and get the same 2,488 byte runtime, because the address commits to the init code. That runtime has no SSTORE, SLOAD or ORIGIN; it keeps the Ethereum PoolManager address 0x000000000004444c5dc75cb358380d2e3de08a90 as an immutable, checks CALLER against it (PC 0x37b to 0x3aa), and answers beforeRemoveLiquidity with HookNotImplemented (0x0a85dc29) on Ethereum, Base and OP Mainnet. eth_call of the third-party removals with that runtime placed at the hook address by state override reverts with WrappedError(0xf8c3..., 0x21d0ee70, HookNotImplemented, HookCallFailed) in all %d runs on Polygon and Avalanche, so the pools stay frozen after a replay. Other code cannot reach the address: a CREATE2 or CREATE output equal to a fixed 160 bit address, or the signing secret of a CREATE2 output, needs about 2^160 work. The address has nonce 0 on all four networks.' % len(sims),
 'source': WD + 'dl/create2_eth.json, dl/dis_f8c3_runtime.txt, raw/f8c3_checks.txt, raw/sim_137.json, raw/sim_43114.json'})
c.append({'chainIds': [10, 8453, 56, 42161, 4663, 1], 'lens': 'L5', 'check': 'Task 3: pools on 0x0000000000000000000000000000000000000020 (bit 5) and 0x00000000000000000000000000000000dead0030 (bits 5 and 4) that hold third-party positions, on Robinhood Chain pools 0x4996584f... and 0x7d10f8e6....',
 'result': 'No freeze of principal. These flags gate only donate (src/libraries/Hooks.sol:317-335); removal and swaps call no hook (bits 9, 8, 7, 6 unset). Donate to such a pool reverts, which takes nothing from LPs. Nobody can place code at either address: both have nonce 0 and no code on all 21 networks (raw/xchain.json), neither is a precompile or system address on any of them (raw/emptycall.json answers success and empty data), and producing a CREATE or CREATE2 output or a signing secret for a fixed address needs about 2^160 work.',
 'source': WD + 'raw/detail_4663.json, raw/xchain.json, raw/emptycall.json; src/libraries/Hooks.sol:317-335'})
none = [x for x in ALL if tab[str(x)]['poolsOn'] == 0]
c.append({'chainIds': none, 'lens': 'L5', 'check': 'Task 2 on networks where no pool names an empty or delegated hook.',
 'result': 'Answer no on each: ' + '; '.join('%s %s pools and %d hooks, none empty or delegated at block %s' % (NAME[x], format(tab[str(x)]['pools'], ','), tab[str(x)]['hooks'], format(tab[str(x)]['block'], ',')) for x in none) + '.',
 'source': WD + 'raw/census_<chainId>.json'})
nog = [x for x in ALL if tab[str(x)]['poolsOn'] and det(x) and not any(p['thirdPartyLive'] and p['flagBits'] & 0x330 for p in det(x)['pools'])]
c.append({'chainIds': nog, 'lens': 'L5', 'check': 'Task 2 on networks where pools name empty or delegated hooks but no pool with bit 9, 8, 5 or 4 holds a position of another account than its creator.',
 'result': 'Answer no on each. ' + ' '.join(l + '.' for l, x in zip(lines, ALL) if x in nog) + ' Every live position was checked against the pool state: the liquidity of the positions that contain the current tick equals the active liquidity, and the liquidityGross of each tick equals the sum over the live positions that use it.',
 'source': WD + 'raw/detail_<chainId>.json (tickCheck)'})
c.append({'chainIds': sorted({v['chainId'] for v in gs.values()}), 'lens': 'L5', 'check': 'gapcheck2.py on every log endpoint used by this census (ten windows from deployment to head unless STARTS is set, 20 sampled blocks per window with seed \'<chainId>-<window>\', receipts counted against eth_getLogs).',
 'result': gap_text + ' The BNB Smart Chain pocket endpoint and 48 Club were used only for the census and the recent Initialize window; no conclusion rests on pocket logs for BNB Smart Chain, whose positions were read from PositionManager state instead. The BNB Smart Chain and Base pocket differences all have fewer receipt logs than eth_getLogs entries because their receipt sets are short or refused (pruned history, block null); no sample had fewer getLogs entries than receipts. Because receipts could not confirm pocket, every pool read from pocket logs was also checked against the tick bitmap and TickInfo state.',
 'source': WD + 'raw/gap/*.json, raw/gap-summary.json'})
c.append({'chainIds': [1, 10, 8453, 130, 42161], 'lens': 'L1', 'check': 'Hook hazard met in passing: the deployed 0xf8c3f424...4300 sets bits 9 and 8.',
 'result': 'Its runtime answers beforeRemoveLiquidity with HookNotImplemented on the networks where it has code, so pools on it cannot remove liquidity there either; a hook author defect, not a network difference.',
 'source': WD + 'raw/f8c3_checks.txt'})
BBp = []
for x in (8453, 56):
    d = det(x)
    if d is None: BBp.append('%s: the ModifyLiquidity scan did not finish, so third-party positions there are unknown' % NAME[x]); continue
    th = [p for p in d['pools'] if p['thirdPartyLive']]
    gt = [p for p in th if p['flagBits'] & 0x330]
    BBp.append('%s: %d pools with initialized ticks read, %d with another account\'s position, %d of them with bit 9, 8, 5 or 4%s' % (NAME[x], len(d['pools']), len(th), len(gt), (' (' + '; '.join(p['poolId'][:12] + ' on ' + p['hook'][:10] for p in gt) + ')') if gt else ''))
BB = '; '.join(BBp) + '.'
fac = R('factories.json')
c.append({'chainIds': ALL, 'lens': 'L5', 'check': 'Whether the permissionless deterministic factories that a hook deployed on one network could be replayed through exist on all 21 networks.',
 'result': 'Yes. The CREATE2 deployer 0x4e59b44847b379578588920ca78fbf26c0b4956c has its 69 byte code and CreateX 0xba5ed099633d3b313e4d5f7bdc1305d3c28ba5ed its 11,838 byte code on all 21 networks. So a hook address made through 0x4e59b448 or through CreateX CREATE2 on one network can be filled on any other by whoever has the init code, and what that account controls is decided by the init code alone. A CreateX CREATE3 address does not depend on the init code, so when its salt does not carry the deployer in its first 20 bytes (the permissioned deploy protection in the CreateX README) any account can place any code at it on another network. Of the 82 hook addresses in use that are empty on some network, 25 have contract code on another network (raw/xchain.json); only 0xf8c3f424...4300 among them sets bit 9, 8, 5 or 4, and it is cleared above.',
 'source': WD + 'raw/factories.json, raw/xchain.json; https://raw.githubusercontent.com/pcaversaccio/createx/main/README.md (Permissioned Deploy Protection and Cross-Chain Redeploy Protection, lines 576 and 709-734 of the fetched copy)'})
out['leads'].append({'chainIds': [1, 10, 56, 137, 130, 8453, 4663, 43114, 480, 1868, 42161], 'lens': 'L5', 'question': 'For the 24 empty hook addresses that have code on another network and set only swap or add flags, and for any later empty hook that is a CreateX CREATE3 output (for example 0x4cd3be87...c0cc, code on Base with nonce 543, empty on OP Mainnet, BNB Smart Chain, Polygon and Arbitrum One with a third-party position on OP Mainnet), which were made through a replayable factory, and does their init code hand ownership to tx.origin or to an open initializer?',
 'why': 'Such a replay would give an ordinary account the swap callbacks and return deltas of pools that other accounts trade in. Removal stays open in these pools, so LP principal is not at stake, which is why this was not followed here.', 'priority': 'low'})
# =============== LEAD RESULTS
out['leadResults'].append({'leadId': 'L-953', 'outcome': 'cleared', 'answer': c[0]['result']})
out['leadResults'].append({'leadId': 'L-972', 'outcome': 'finding', 'answer': 'Per network, with ids recomputed: ' + census_text + ' Pools with bit 9 or 8 and third-party positions: Polygon 0x4accc6ab... and 0xc5a3738f... and Avalanche 0x07ec041c... and 0x3752b3c6..., all on 0xf8c3f424...4300, frozen (F-004 update); anyone can replay its CREATE2 deployment there but the code is fixed and still reverts, so no account gains control. Bits 5 and 4 only: Robinhood Chain 0x4996584f... and 0x7d10f8e6... on 0x...dead0030, donate blocked, removal open, nobody can place code. Delegated hooks with third-party positions: Ethereum 0x992c0ab6... and 0x08834f72..., controlled by the account holder (F-013 update). ' + BB})
json.dump(out, open('/home/user/v4-core/research/network-risk/cycles/022/theme-empty-hook-pools.research.json', 'w'), indent=1)
print('written', len(out['findings']), len(out['cleared']))
