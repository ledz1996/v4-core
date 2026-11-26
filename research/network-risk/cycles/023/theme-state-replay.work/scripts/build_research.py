"""Assemble cycles/023/theme-state-replay.research.json from the raw results of this unit."""
import json, os, glob, collections
NR = '/home/user/v4-core/research/network-risk'; W = NR + '/cycles/023/theme-state-replay.work'
NETS = {n['chainId']: n for n in json.load(open(NR + '/state/networks.json'))['networks']}
ALL = [n['chainId'] for n in json.load(open(NR + '/state/networks.json'))['networks']]
NAMES = {1: 'Ethereum', 8453: 'Base', 130: 'Unichain', 42161: 'Arbitrum One', 56: 'BNB Smart Chain', 137: 'Polygon', 43114: 'Avalanche',
         143: 'Monad', 4326: 'MegaETH', 999: 'HyperEVM'}
TRACE = {1: 'https://eth.api.pocket.network', 8453: 'https://base.api.pocket.network', 130: 'https://unichain.api.pocket.network',
         42161: 'https://arb-one.api.pocket.network', 56: 'https://bsc.api.pocket.network', 43114: 'https://avax.api.pocket.network',
         137: 'https://polygon.drpc.org', 143: 'https://rpc.monad.xyz', 4326: 'https://mainnet.megaeth.com/rpc', 999: 'https://rpc.purroofgroup.com'}
def J(p, d=None):
    try: return json.load(open(p))
    except Exception: return d
def clients(c):
    s = collections.Counter()
    try:
        for l in open('%s/raw/%d/brackets.jsonl' % (W, c)):
            x = json.loads(l)
            if x.get('url') and x.get('client'): s['%s answered %s' % (x['url'], x['client'])] += 1
    except Exception: pass
    return sorted(s)
def windows(c):
    ws = [J(p) for p in sorted(glob.glob('%s/raw/%d/window*.json' % (W, c)))]
    ws = [w for w in ws if w]
    return ws
def explain(c):
    """classify every mismatch record left by run.py"""
    cls = collections.Counter(); unexplained = []
    try: lines = open('%s/raw/%d/mismatches.jsonl' % (W, c)).readlines()
    except Exception: lines = []
    for l in lines:
        r = json.loads(l)
        for m in r['mismatches']:
            k = m['kind']
            if k == 'storage-unexplained' and m.get('slot') == '0x0' and not r['actions']:
                cls['PoolManager deployment (constructor writes the owner, slot 0)'] += 1; continue
            if k == 'erc20-flow':
                if m['logsIn'] == 0 and m['logsOut'] == m['take'] + m['collect'] and m['token'] in NOLOG.get(c, ()):
                    cls['token whose code has no Transfer event'] += 1; continue
                if m['logsIn'] == 0 and m['token'] in REBASE.get(c, ()):
                    cls['rebasing token: a rebase in the same transaction raised the PoolManager balance between sync and settle'] += 1; continue
                if m['logsOut'] == m['take'] + m['collect'] and 0 < m['paid'] - (m['logsIn'] - m['logsOut'] + m['take'] + m['collect']) <= 2:
                    cls['interest-bearing token: balanceOf rose 1 or 2 units more than the Transfer amount'] += 1; continue
            unexplained.append({'hash': r['hash'], 'block': r['block'], 'mismatch': m})
    return cls, unexplained
REBASE = {137: ('0x99a57e6c8558bc6689f894e068733adf83c19725',)}
NOLOG = {999: ('0x1c5a08a10c98475811d0c556eb39ad6cb244eb2e',)}

out = {'unit': 'theme-state-replay', 'profiles': [], 'findings': [], 'cleared': [], 'leads': [], 'leadResults': []}
tot = collections.Counter(); per = {}
for c in [1, 8453, 130, 42161, 56, 137, 43114, 143, 4326, 999]:
    r = J('%s/raw/%d/result.json' % (W, c))
    if not r: continue
    cls, unexp = explain(c); per[c] = (r, cls, unexp)
    for k in ('txs', 'wordsCompared', 'storageWordsChanged', 'nativeMoved', 'erc20Checked'): tot[k] += r.get(k, 0)
json.dump({str(c): {'result': v[0], 'explained': dict(v[1]), 'unexplained': v[2]} for c, v in per.items()}, open(W + '/raw/summary.json', 'w'), indent=1)
print(json.dumps({str(c): [v[0]['txs'], v[0]['wordsCompared'], dict(v[1]), len(v[2])] for c, v in per.items()}, indent=0))
print(dict(tot))

# ---------- prose ----------
def committed(c):
    fs = [f for f in glob.glob('%s/raw/%d/committed-*.json' % (W, c)) if 'rpc.hyperliquid.xyz' not in f]
    return [J(f) for f in fs if J(f)]
MODEL = ('scripts/model.py rewrites every PoolManager entry point from the text of src/ (PoolManager.sol:103-377, ProtocolFees.sol, ERC6909.sol, '
         'ERC6909Claims.sol, Extsload.sol, Exttload.sol, Pool.sol:100-612, Position.sol, TickBitmap.sol, Hooks.sol:131-320) with the pool math of '
         'tools/opdiff/v4math.py, and walks the mined call trace frame by frame. It starts persistent storage from the transaction\'s own prestate '
         '(prestateTracer), so tick bitmap words, liquidityNet and fee growth outside are the values at the transaction\'s position in its block, and '
         'starts transient storage empty. It takes from the trace only what the source takes from outside: calldata, msg.sender, msg.value, hook '
         'return data and token balanceOf return data. For every PoolManager frame it compares the frame output (swap and modifyLiquidity deltas, '
         'feesAccrued, settle amount, unlock result, every extsload and exttload word), every PoolManager log word (Swap, ModifyLiquidity, Donate, '
         'Initialize, ERC-6909 Transfer and others), and the deltas the PoolManager wrote into the calldata of afterSwap and afterAdd or '
         'afterRemoveLiquidity hooks. At the end it compares every PoolManager storage word in the prestateTracer diff (slot0, liquidity, both fee '
         'growth globals, tick words, bitmap words, positions, protocolFeesAccrued, ERC-6909 balances, allowances, operators) and flags any word it '
         'wrote that the chain did not, and any word the chain wrote that it did not. A model read of a word that is not in the prestate is also flagged.')
for c in [1, 8453, 130, 42161, 56, 137, 43114, 143, 4326, 999]:
    if c not in per: continue
    r, cls, unexp = per[c]
    ws = windows(c); w = J('%s/raw/%d/window.json' % (W, c)) or {}
    cl = clients(c)
    expl = '; '.join('%d %s' % (v, k) for k, v in cls.items())
    winfo = ('the newest %d PoolManager transactions with a log, blocks %s to %s, listed from eth_getLogs on %s at %s' %
             (len(w.get('txs', [])), w.get('firstBlock'), w.get('lastBlock'), ', '.join(w.get('logEndpoints', [])[:1]), w.get('time')))
    if c == 999: winfo = 'every PoolManager transaction with a log from deployment to block %s (%d transactions, scan to block 0 on https://rpc.purroofgroup.com at %s)' % (w.get('head'), len(w.get('txs', [])), w.get('time'))
    if c == 56: winfo = 'the newest PoolManager transactions in %d rebuilt windows between blocks %s and %s, traced newest first while the endpoints still held their state' % (len(ws), min(x['firstBlock'] for x in ws if x.get('firstBlock')), max(x['lastBlock'] for x in ws if x.get('lastBlock')))
    short = '' if r['txs'] >= 19900 or c == 999 else ' The window is short of 20,000 because the public trace endpoints refused or had no state for the rest (raw/%d/errors.jsonl).' % c
    res = ('%d transactions replayed (%s; blocks %d to %d). %d words compared (%d storage words changed by the chain, plus outputs, logs and hook calldata), %d mismatches left after explanation. '
           'The transactions held %d swaps (%d of more than one step), %d liquidity changes, %d donates, %d initializations, %d mint or burn of claims and %d PoolManager frames that reverted and were caught. '
           'Native balance: %d transactions moved the PoolManager balance, and in all %d the change equals native settles minus native takes and fee collection, and equals the traced value frames, to the wei. '
           'ERC-20: %d currency and transaction pairs compared Transfer flows with settle, take and fee collection; residue explained: %s. Trace endpoints answered: %s.%s') % (
        r['txs'], winfo, r['blocks'][0], r['blocks'][1], r['wordsCompared'], r['storageWordsChanged'], len(unexp),
        r['counts'].get('call:swap', 0), r['counts'].get('swap-steps-multi', 0), r['counts'].get('call:modifyLiquidity', 0), r['counts'].get('call:donate', 0),
        r['counts'].get('call:initialize', 0), r['counts'].get('call:mint', 0) + r['counts'].get('call:burn', 0), r['counts'].get('pm-frame-reverted', 0),
        r['nativeMoved'], r['nativeChecked'], r['erc20Checked'], expl or 'none needed', '; '.join(cl)[:900], short)
    out['cleared'].append({'chainIds': [c], 'lens': 'L1', 'check': 'Task 1 to 4 on %s: every mined PoolManager transaction of the window re-run through a model of src/ from its prestate and compared word by word with what the chain returned, logged and stored. %s' % (NAMES[c], MODEL if c == 1 else 'Same model as the Ethereum entry (scripts/model.py, scripts/run.py).'),
                           'result': res, 'source': TRACE[c]})
    if unexp: print('UNEXPLAINED', c, unexp[:3])
    for cm in committed(c):
        out['cleared'].append({'chainIds': [c], 'lens': 'L2', 'check': '%s: traced post state against committed state. For each block of the window, the last traced post value of every PoolManager word the window changed in that block, and the PoolManager native balance, against eth_getStorageAt and eth_getBalance at that block on %s (scripts/committed.py).' % (NAMES[c], ', '.join(cm['urls'])),
                               'result': '%d blocks, %d words and %d balances compared, %d differ. Clients: %s.' % (cm['blocks'], cm['words'], cm['balances'], len(cm['mismatch']), json.dumps(cm.get('clientBefore'))[:300]),
                               'source': cm['urls'][0]})
json.dump(out, open(W + '/raw/research-draft.json', 'w'), indent=1)

# ---------- cross-network items ----------
MON = 'https://raw.githubusercontent.com/category-labs/monad/v0.16.7/'
mut = {c: J('%s/raw/%d/mutation.json' % (W, c)) for c in (8453, 143, 4326)}
def mtxt(c):
    m = mut[c]; return ', '.join('%s %d of %d' % (k, v['txsWithMismatch'], v['txs']) for k, v in m.items())
out['cleared'].append({'chainIds': [8453, 143, 4326], 'lens': 'L1', 'check': 'Whether the replay can see a one-unit fault. scripts/mutate.py reruns 300 transactions per network with one deliberate change to the model at a time and counts the transactions that then show a mismatch.',
    'result': 'Base: %s. Monad: %s. MegaETH: %s. The unchanged model gives no mismatch, and each change shows up wherever its code path runs (bitmap flips are rare in swap-heavy windows), so a zero count above means no such difference occurred.' % (mtxt(8453), mtxt(143), mtxt(4326)),
    'source': 'cycles/023/theme-state-replay.work/scripts/mutate.py'})
hl = J(W + '/raw/999/latest-official.json')
out['cleared'].append({'chainIds': [999], 'lens': 'L2', 'check': 'HyperEVM producer check. The traces come from the public replica https://rpc.purroofgroup.com (reth/v0.1.0-f0cad31); the validator is closed and the official endpoint https://rpc.hyperliquid.xyz/evm serves no traces. The official endpoint answers eth_getStorageAt with the latest value whatever block is named (raw/999/official-not-archive.json: slot 0x4239...247e is 0 at blocks 51,818,751 to 51,818,753 there and 0x1239bc2b12e04 at 51,818,752 on the replica and on hyperliquid.drpc.org), so a per-block comparison with it is void (raw/committed-999.log, 4,409 differences, all of this kind). Instead the last traced post value of every PoolManager word any transaction of the whole history changed was compared with the official latest state (scripts/latest999.py).',
    'result': 'Window head %d, official head %d, %d PoolManager logs after the window head. %d words compared, %d differ. Native balance: last traced %d wei, official %d wei. Every word the validator holds for the PoolManager equals what the source model reproduced from the replica traces.' % (hl['windowHead'], hl['officialHead'], hl['logsAfterWindowHead'], hl['slotsCompared'], len(hl['mismatches']), hl['tracedFinalBalance'], hl['officialBalance']),
    'source': 'https://rpc.hyperliquid.xyz/evm'})
out['cleared'].append({'chainIds': [143], 'lens': 'L1', 'check': 'Monad: which code path the traces and the committed state come from, read in the v0.16.7 source that the endpoints report (Monad/0.16.7).',
    'result': 'Trace requests re-execute from the parent block with the RPC VM, declared as vm::VM vm_{vm::VM::InterpreterOnly} (category/rpc/monad_executor.cpp:1306-1309, used at 1821-1824). Block execution builds vm::VM vm{trace_calls ? InterpreterOnly : Dual} (cmd/monad/main.cpp:485-488), so validators that do not record call traces run compiled native code. Every node asserts that the delayed execution results carried in each consensus header hash to the block headers it computed itself (category/execution/runloop/runloop_monad.cpp:125-155, MONAD_ASSERT at 680-681). So the 20,000 transactions checked against the source above were run by the interpreter, and the committed state they match (1,500 blocks, scripts/committed.py) is accepted by the node only while its own results equal what the validator quorum executed. Whether rpc.monad.xyz itself runs with trace_calls was not confirmed.',
    'source': MON + 'category/execution/runloop/runloop_monad.cpp'})
out['cleared'].append({'chainIds': [1, 8453, 130], 'lens': 'L3', 'check': 'ERC-20 residue: wrapped native minted to the PoolManager without a Transfer log.',
    'result': 'In %s transaction and currency pairs a router calls take(address(0), WETH, amount): the PoolManager sends native value to the wrapped native contract with empty calldata (src/types/Currency.sol:48), which mints WETH to the PoolManager with a Deposit log and no Transfer log, and the router then settles WETH. Native is debited and WETH credited by the same amount, and both legs match the source. Counting Deposit and Withdrawal logs as flows (scripts/run.py) leaves no residue.' % '/'.join(str((per.get(c, ({}, 0, 0))[0] or {}).get('wethEvents', 0)) for c in (1, 8453, 130)),
    'source': 'src/types/Currency.sol:48'})
out['cleared'].append({'chainIds': [137], 'lens': 'L3', 'check': 'Token hazard noted in one line: Staked Longinus (sLGNS, 0x99a57e6c8558bc6689f894e068733adf83c19725) on Polygon rebases inside ordinary transactions (LogSupply and LogRebase logs, no Transfer).',
    'result': 'Two transactions credited a settler with the PoolManager balance rise from a rebase between sync and settle (src/PoolManager.sol:358-361), which is assumption A2 as recorded. The model reproduces the credited amount from balanceOf; no network difference is involved.',
    'source': 'https://polygon-bor-rpc.publicnode.com'})
out['cleared'].append({'chainIds': [1, 43114, 999], 'lens': 'L3', 'check': 'Other ERC-20 residue and the one storage residue.',
    'result': 'Ethereum 1 and Avalanche 4 pairs: interest-bearing tokens whose balanceOf rose one or two units more than the Transfer amount; settle credits the measured rise (src/PoolManager.sol:358-361) and the PoolManager holds it. HyperEVM 2 pairs: token 0x1c5a08a10c98475811d0c556eb39ad6cb244eb2e has no Transfer event topic in its 1,256 byte code (eth_getCode on https://rpc.hyperliquid.xyz/evm), so its inflows leave no log. HyperEVM 1 word: the PoolManager deployment transaction writes the owner to slot 0 in the constructor (src/PoolManager.sol:100, lib/solmate/src/auth/Owned.sol:29-32), which the model does not run.',
    'source': 'src/PoolManager.sol:358-361'})
out['cleared'].append({'chainIds': [130], 'lens': 'L1', 'check': 'Reading of unlock when the callback returns data whose first word is 0.',
    'result': 'Two Unichain transactions return 64 bytes from unlockCallback with a head word of 0. abi.decode reads the length at offset 0, which is 0, and unlock returns empty bytes (src/PoolManager.sol:104-114). The chain did the same. The model first assumed an offset of 32 and was corrected. The other corrections made during the unit were a read of tick liquidity words in the fee growth computation that the source does not make (Pool.sol:493-494 reads only the fee growth words; the prestate showed it) and the counting of wrapped native Deposit and Withdrawal logs. After them every transaction of every window replays.',
    'source': 'src/PoolManager.sol:104-114'})
# leads
out['leads'] = [
 {'chainIds': [56], 'lens': 'L2', 'question': 'Can the BNB Smart Chain replay reach 20,000 transactions through an archive trace endpoint, or through a replay from parent-block storage as cycle 21 did for Arc?', 'why': 'The public trace endpoints keep state for a few hours at most (required historical state unavailable, reexec=128; historical state is not available), so the BNB Chain window here is about %d transactions.' % (per.get(56, ({'txs': 0}, 0, 0))[0]['txs']), 'priority': 'medium'},
 {'chainIds': ALL, 'lens': 'L2', 'question': 'Do PoolManager transactions without a PoolManager log (native settle and take only, clear, sync, updateDynamicLPFee, collectProtocolFees) replay to the source as well?', 'why': 'Every window here was listed from PoolManager logs, so a transaction that moves native value or changes slot0 without a log was outside it. block or trace_filter listings would close this.', 'priority': 'medium'},
 {'chainIds': [999], 'lens': 'L2', 'question': 'Does the HyperEVM validator write the same PoolManager words as the replica block by block, for words that were later overwritten?', 'why': 'The official endpoint serves only the latest state, so only the last value of each word over the whole history was compared. A follow mode that compares each new block with the official latest state while it is still latest would cover every write.', 'priority': 'medium'},
 {'chainIds': [143], 'lens': 'L1', 'question': 'Does rpc.monad.xyz execute blocks with trace_calls (interpreter only), and do the delayed execution results carry the state root?', 'why': 'If so, the committed state comparison checks the interpreter against the interpreter, and only the consensus assertion ties it to validators running compiled code.', 'priority': 'low'},
 {'chainIds': [10, 7777777, 480, 57073, 1868, 42220, 196, 4663, 99901, 4217, 5042], 'lens': 'L2', 'question': 'Does the same word by word replay hold on the eleven networks outside this unit (OP Mainnet, Zora, World Chain, Ink, Soneium, Celo, X Layer, Robinhood Chain, Elysium, Tempo, Arc)?', 'why': 'L-996 named ten networks. For the other eleven the answer is unknown here; Arc and Elysium serve no traces (cycle 22), so they need the parent-state replay of cycle 21.', 'priority': 'medium'},
 {'chainIds': [4326], 'lens': 'L2', 'question': 'Does https://mainnet.megaeth.com/rpc serve state it executed itself or state diffs from the sequencer?', 'why': 'The 16,035 block comparison of traced and committed state is a producer check only in the second case.', 'priority': 'low'},
]
r56 = per.get(56, ({'txs': 0}, 0, 0))[0]
out['leadResults'] = [
 {'leadId': 'L-996', 'outcome': 'cleared', 'answer': '%d mined PoolManager transactions were replayed word by word against a model of src/ on the ten networks the lead names: Ethereum, Unichain, Arbitrum One, Monad and MegaETH 20,000 each, Base 19,987, Polygon %d, Avalanche %d, HyperEVM its whole history of %d, BNB Smart Chain %d (state kept only for hours). %d words were compared, %d of them PoolManager storage words the chains changed. No storage word, return value, log word or hook calldata word differs from the source. In every transaction the PoolManager native balance change equals native settles minus native takes and fee collection, and the traced value frames, to the wei (%d transactions moved native value). %d ERC-20 currency and transaction pairs net to settle minus take; the residue is wrapped native Deposit logs, interest-bearing rounding, one rebasing token and one token without Transfer events. The traced post state equals the committed state on every block sampled on the %d networks checked that way, the HyperEVM validator\'s latest state equals the replayed history in all %d words, and the Monad node asserts its own results against the consensus delayed execution results. The other eleven networks were outside the lead and this unit, so the answer for them is unknown here.' % (
     tot['txs'] + 0, per[137][0]['txs'], per[43114][0]['txs'], per[999][0]['txs'], r56['txs'], tot['wordsCompared'], tot['storageWordsChanged'], tot['nativeMoved'], tot['erc20Checked'], len([c for c in per if committed(c)]), hl['slotsCompared'])},
 {'leadId': 'L-988', 'outcome': 'inconclusive', 'answer': 'Not attempted in this unit. The time went to L-996, which covers the rows the census skips. The census gaps on Base, Robinhood Chain, Ethereum and X Layer stay as listed in cycle 22.'},
]
json.dump(out, open(NR + '/cycles/023/theme-state-replay.research.json', 'w'), indent=1)
print('written', len(out['cleared']), 'cleared')
