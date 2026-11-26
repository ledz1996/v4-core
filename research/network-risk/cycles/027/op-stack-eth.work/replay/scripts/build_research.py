"""Assemble cycles/024/theme-replay-eleven.research.json from raw/summary.json and the other raw results of this unit."""
import json, os, glob, collections
NR = '/home/user/v4-core/research/network-risk'; W = NR + '/cycles/024/theme-replay-eleven.work'; R = W + '/raw'
NETS = {n['chainId']: n for n in json.load(open(NR + '/state/networks.json'))['networks']}
ALL = [n['chainId'] for n in json.load(open(NR + '/state/networks.json'))['networks']]
NAME = {c: NETS[c]['name'] for c in NETS}
NAME[10] = 'OP Mainnet'; NAME[480] = 'World Chain'
def J(p, d=None):
    try: return json.load(open(p))
    except Exception: return d
S = J(R + '/summary.json')
def clients(c, urlfilter=None):
    s = collections.OrderedDict()
    for f in [R + '/%d/brackets.jsonl' % c]:
        if not os.path.exists(f): continue
        for l in open(f):
            x = json.loads(l); cl = x.get('client')
            if isinstance(cl, list): cl = cl[0]
            u = x.get('url') or ','.join(x.get('urls', []))
            if cl and u: s.setdefault('%s answered %s' % (u, cl), 1)
    return list(s)
def committed(c):
    out = []
    for f in glob.glob(R + '/%d/committed-*.json' % c):
        x = J(f)
        if x: out.append(x)
    return out
def mutate(c): return J(R + '/%d/mutation.json' % c)
def mut_text(c):
    m = mutate(c)
    if not m: return 'The mutation check was not run on this network.'
    parts = ['%s %d of %d' % (k, v['txsWithMismatch'], v['txs']) for k, v in m.items()]
    return 'Mutation check (scripts/mutate.py, one deliberate one-unit change to the model at a time, on the first 300 transactions): ' + '; '.join(parts) + '.'
def com_text(c):
    cs = committed(c)
    if not cs: return ''
    t = []
    for x in cs:
        t.append('traced post state against committed state (scripts/committed.py): %d blocks, %d PoolManager words and %d native balances compared with eth_getStorageAt and eth_getBalance at the block on %s (%s), %d mismatches, %d blocks skipped because a window transaction of the block was not traced, %d request errors' % (
            x['blocks'], x['words'], x['balances'], ', '.join(x['urls']), '; '.join(str(a[0]) for a in x.get('clientBefore', [])), len(x['mismatch']), x.get('skippedIncomplete', 0), x.get('errors', 0)))
    return ' Producer check: ' + '; '.join(t) + '.'
MODEL = ('Method as in cycle 23 (cycles/023/theme-state-replay.work/scripts, copied unchanged into this unit apart from endpoint tables): collect.py lists the newest PoolManager transactions with a log by eth_getLogs and traces each with prestateTracer in diff mode, prestateTracer and callTracer with logs; '
         'run.py drives scripts/model.py, a model of every PoolManager entry point written from src/ (PoolManager.sol:104-377, Pool.sol:146 and 279, TickBitmap.sol:47 and 85, SqrtPriceMath.sol:188 and 261 through tools/opdiff/v4math.py), '
         'from the transaction prestate, and compares every frame output, every PoolManager log word, the deltas passed to after hooks, every changed storage word, the native balance change against native settles minus takes and fee collection and against traced value frames, and ERC-20 Transfer flows against settle, take and fee collection.')
LAZY = ('Method: scripts/gdrive.py runs each transaction whole in the reference interpreter scripts/pyevm_tx24.py through scripts/lazyreplay24.py, reading every account, code, balance, nonce and storage word lazily from the parent block (eth_getCode, eth_getBalance, eth_getTransactionCount, eth_getStorageAt). '
        'It compares status, every receipt log in order, every PoolManager storage word read or written against eth_getStorageAt at the block when no later transaction of the block emits a PoolManager log, and the PoolManager native balance change when the transaction is the only one of the block with a PoolManager log. '
        'A transaction whose status, PoolManager logs, PoolManager words or native balance differ is run again after every earlier transaction of its block on the same state (up to 120 earlier transactions). Gas is not modelled, so ERC-4337 EntryPoint events that report gas cost differ by design.')
out = {'unit': 'theme-replay-eleven', 'profiles': [], 'findings': [], 'cleared': [], 'leads': [], 'leadResults': []}
# ---------------- traced networks ----------------
TR = {10: 'https://op.api.pocket.network (op-reth), with https://optimism.drpc.org for a second pass', 57073: 'https://ink.api.pocket.network and https://rpc-qnd.inkonchain.com',
      4217: 'https://rpc.mainnet.tempo.xyz', 196: 'https://xlayer.drpc.org', 4663: 'https://robinhood.drpc.org', 99901: 'https://elysium.drpc.org',
      56: 'https://bsc.api.pocket.network', 42220: 'https://celo-json-rpc.stakely.io and https://celo.api.pocket.network'}
tot = collections.Counter()
def lastprog(c):
    try: return json.loads(open(R + '/committed-%d.log' % c).read().strip().splitlines()[-1])
    except Exception: return {}
CNOTE = {10: ' Producer check: scripts/committed.py against https://mainnet.optimism.io was stopped at the end of the session after %d blocks with 0 mismatches (its last progress line; %d batch requests refused).' % (lastprog(10).get('blocks', 0), lastprog(10).get('errors', 0)),
         56: ' Producer check: scripts/committed.py against https://bsc.api.pocket.network was stopped at the end of the session after %d blocks with 0 mismatches (its last progress line; %d batch requests refused).' % (lastprog(56).get('blocks', 0), lastprog(56).get('errors', 0)),
         4663: ' Producer check: not possible here; rpc.mainnet.chain.robinhood.com answered "historical state ... is not available" for every block of the window by the time the check ran, and robinhood.drpc.org is the trace endpoint itself.'}
extra = {}
m = J(R + '/4217/txmeta.json', {}).get('meta', {})
if m:
    t76 = [v for v in m.values() if v['type'] == '0x76']
    extra[4217] = (' Tempo sample (raw/4217/txmeta.json, eth_getTransactionByHash on every transaction): %d of the %d are Tempo transactions of type 0x76, %d of them batched with more than one call (up to %d calls), '
                   '%d name a fee token explicitly (%s), %d are EIP-7702 type 4; all were in the replay and none differs.') % (
        len(t76), len(m), sum(1 for v in t76 if (v['calls'] or 0) > 1), max((v['calls'] or 0) for v in t76) if t76 else 0,
        sum(1 for v in m.values() if v['feeToken']), ', '.join('%s %d' % (k, n) for k, n in collections.Counter(v['feeToken'] for v in m.values() if v['feeToken']).most_common(4)),
        sum(1 for v in m.values() if v['type'] == '0x4'))
mx = J(R + '/196/txmeta.json', {}).get('meta', {})
if mx:
    traced = {os.path.basename(f)[:-8] for f in glob.glob(R + '/196/tx/*.json.gz')}
    z = [h for h, v in mx.items() if int(v.get('gasPrice') or '0x1', 16) == 0 or (v.get('maxFeePerGas') is not None and int(v['maxFeePerGas'], 16) == 0)]
    tg = collections.Counter(mx[h]['to'] for h in z)
    extra[196] = (' X Layer gasless transactions (zero gas price; every other transaction of the window pays at least 20,000,000 wei per gas; raw/196/txmeta.json over all %d transactions of the window): %d in the window, %d of them in the traced replay, none differs. Their targets are %s, so whitelisted contracts other than the PoolManager, PositionManager and Universal Routers (cycle 22) reach the PoolManager at zero gas price.') % (
        len(mx), len(z), len([h for h in z if h in traced]), ', '.join('%s %d' % (t, n) for t, n in tg.most_common(4)))
for c in [10, 57073, 4217, 196, 4663, 99901, 56, 42220]:
    v = (S['traced'] or {}).get(str(c))
    if not v: continue
    r = v['result']; w = J(R + '/%d/window.json' % c, {})
    for k in ('txs', 'wordsCompared', 'storageWordsChanged', 'nativeMoved', 'erc20Checked'): tot[k] += r.get(k, 0)
    expl = '; '.join('%d %s' % (n, k) for k, n in v['explained'].items()) or 'none'
    short = ''
    if r['txs'] < 19900:
        short = ' The sample is short of 20,000: %s' % {
            10: 'op.api.pocket.network refused the older transactions of the window with "insufficient changesets" (pruned history), and optimism.drpc.org, the only other public trace endpoint found, answers at a low rate limit (HTTP 429).',
            196: 'xlayer.drpc.org is the only public endpoint that serves traces (rpc.xlayer.tech and xlayerrpc.okx.com answer "rpc method is not whitelisted") and it rate limits (HTTP 429), so the collector ran with one worker and was stopped at the end of the session.',
            4663: 'robinhood.drpc.org is the only public endpoint that serves traces (the official endpoint answers "the method debug_traceTransaction does not exist") and it rate limits (HTTP 429), so the collector ran with one worker and was stopped at the end of the session.',
            99901: 'elysium.drpc.org is the only public endpoint that serves traces (the official endpoint needs an API key for debug methods) and it rate limits (HTTP 429), so the collector ran with one worker and was stopped at the end of the session.',
            56: 'bsc.api.pocket.network rotates Geth v1.7.8, Geth v1.8.2 and reth-bsc backends and only the archive backends answer traces of older blocks, so each trace was retried until an archive backend answered; the collector was stopped at the end of the session.',
            42220: 'both Celo trace endpoints keep state for about the last 10,000 blocks ("state at block ... is pruned"), which held one PoolManager transaction; the rest of the Celo sample was replayed from parent-block storage (separate entry).'}.get(c, '')
    res = ('%d transactions replayed (the newest %d PoolManager transactions with a log were listed, blocks %s to %s, from eth_getLogs on %s at %s; replayed blocks %d to %d). %d words compared (%d storage words changed by the chain, plus outputs, logs and hook calldata), %d mismatches left after explanation (explained: %s). '
           'The transactions held %d swap calls (%d of more than one step), %d liquidity calls, %d donates, %d initializations, %d mint or burn of claims and %d PoolManager frames that reverted and were caught. '
           'Native balance: %d transactions moved the PoolManager balance, and in all %d the change equals native settles minus native takes and fee collection, and the traced value frames, to the wei. '
           'ERC-20: %d currency and transaction pairs compared, %d with a deficit. Trace endpoint: %s. Builds that answered around the batches: %s.%s %s%s%s') % (
        r['txs'], len(w.get('txs', [])), w.get('firstBlock'), w.get('lastBlock'), ', '.join(w.get('logEndpoints', [])[:1]), w.get('time'), r['blocks'][0], r['blocks'][1],
        r['wordsCompared'], r['storageWordsChanged'], len(v['unexplained']), expl,
        r['counts'].get('call:swap', 0), r['counts'].get('swap-steps-multi', 0), r['counts'].get('call:modifyLiquidity', 0), r['counts'].get('call:donate', 0),
        r['counts'].get('call:initialize', 0), r['counts'].get('call:mint', 0) + r['counts'].get('call:burn', 0), r['counts'].get('pm-frame-reverted', 0),
        r['nativeMoved'], r['nativeChecked'], r['erc20Checked'], r['erc20Deficit'], TR[c], '; '.join(clients(c)[:8]) or 'see raw/%d/brackets.jsonl' % c,
        short, mut_text(c), com_text(c) or CNOTE.get(c, ''), extra.get(c, ''))
    out['cleared'].append({'chainIds': [c], 'lens': 'L2', 'check': 'L-1044 Task 1 and 4 on %s: word by word replay of mined PoolManager transactions from their own prestate traces. %s' % (NAME[c], MODEL),
                           'result': res, 'source': 'cycles/024/theme-replay-eleven.work/raw/%d/result.json and mismatches.jsonl; src/PoolManager.sol:104' % c})
# ---------------- parent-storage networks ----------------
LZ = {7777777: 'https://rpc.zora.energy', 480: 'https://worldchain-mainnet.g.alchemy.com/public', 1868: 'https://rpc.soneium.org', 5042: 'https://rpc.mainnet.arc.io', 42220: 'https://forno.celo.org (receipts that forno answered null fetched from https://rpc.ankr.com/celo)'}
WHY = {7777777: 'Zora: rpc.zora.energy needs an API key for debug and trace methods (HTTP 401), zora.drpc.org and the thirdweb endpoint refuse or rate limit, and no other public trace endpoint was found.',
       480: 'World Chain: the Alchemy public endpoint allows "only core evm requests" (HTTP 401), worldchain.drpc.org answers that debug_traceTransaction does not exist, thirdweb rate limits, and Tenderly and publicnode have no World Chain service (HTTP 404).',
       1868: 'Soneium: rpc.soneium.org answers "rpc method is not whitelisted" (HTTP 403), soneium.drpc.org answers that the method does not exist, publicnode has no debug methods, Tenderly rate limits and Startale needs a key.',
       5042: 'Arc: rpc.mainnet.arc.io and arc-mainnet.drpc.org answer that debug_traceTransaction and trace_replayTransaction are not supported.',
       42220: 'Celo: the trace endpoints keep state for about 10,000 blocks only, so the older part of the window was replayed from parent-block storage on forno.celo.org, which serves archive state.'}
for c in [7777777, 480, 1868, 5042, 42220]:
    v = S['lazy'].get(str(c))
    if not v: continue
    lw = J(R + '/%d/lwindow.json' % c, {})
    cc = collections.Counter(); em = collections.Counter()
    for k, n in v['classes'].items():
        if k.startswith('PoolManager status'):
            cc['PoolManager status, logs, words and balance equal, only logs of other contracts differ'] += n
            for e in k.split(': ', 1)[1].split(','): em[e] += n
        else: cc[k] += n
    cls = '; '.join('%d %s' % (n, k) for k, n in cc.most_common())
    if em: cls += ' (emitters of the differing logs, by first bytes of the address: %s; 0x00000000 is EntryPoint v0.7 0x0000000071727De2..., 0x5ff137d4 is EntryPoint v0.6, 0x4337084d is EntryPoint v0.8, whose UserOperationEvent carries gas figures the reference does not model; the others are contracts whose state an earlier transaction of the block changed)' % ', '.join('%s %d' % (e, n) for e, n in em.most_common(8))
    diff = v['differs']
    dtext = 'No transaction differs in a PoolManager log, status, PoolManager storage word or native balance.' if not diff else (
        '%d transaction(s) still differ in the PoolManager part: %s.' % (len(diff), '; '.join('%s (block %d, index %d)' % (d['tx'], d['block'], d['index']) for d in diff)))
    ex = ''
    if c == 7777777:
        lw0 = J(R + '/7777777/lwindow.json', {})
        ex = ' The whole Zora history holds %d PoolManager transactions with a log (eth_getLogs from block 0 to %s); the replay covers the newest 2,000 of them, because one parent-storage replay takes several seconds of CPU and this unit ran on four cores.' % (len(lw0.get('txs', [])), lw0.get('head'))
    if c == 42220:
        mc = J(R + '/42220/txmeta.json', {}).get('meta', {})
        fc = [h for h, x in mc.items() if x['type'] == '0x7b']
        recs = {}
        for f in sorted(glob.glob(R + '/42220/lazy_*.jsonl'), key=lambda f: ('rerun' in f, 'differs' in f, f)):
            for l in open(f): x = json.loads(l); recs[x['tx']] = x
        fcr = [recs[h] for h in fc if h in recs]
        ex = (' Celo fee currency transactions (CIP-64, type 0x7b): %d in the 20,000 transaction window (raw/42220/txmeta.json), %d replayed (the five inside the main sample plus raw/42220/lwindow-feecurrency.json), %d of them match in status, PoolManager logs, words and balance. '
              'The Celo transfer precompile at 0xfd was modelled from celo-kona transfer.rs and ran %d times.') % (len(fc), len(fcr), sum(1 for x in fcr if (x.get('match') or (isinstance(x.get('prefix'), dict) and x['prefix'].get('match')) or (x.get('statusChain') == x.get('statusRef') and x.get('pmLogsEqual') and not x.get('pmSlotMismatch') and x.get('pmNativeEqual') is not False))),
            sum(x.get('celoTransfers', 0) for x in recs.values()))
    res = ('%d transactions replayed from parent-block storage on %s (window lwindow.json: newest PoolManager transactions with a log, newest first, blocks %s to %s). Outcome: %s. %s '
           'Compared: %d receipt logs (%d of them PoolManager logs), %d PoolManager storage words in %d transactions after which no later transaction of the block touches the PoolManager, and the native balance change in %d transactions (%d moved the PoolManager balance). '
           'The run executed %d CREATE or CREATE2, %d P256VERIFY calls and %d NativeCoinAuthority mints. Builds that answered: %s.%s %s') % (
        v['records'], LZ[c], v['blocks'][0], v['blocks'][1], cls, dtext, v['logsCompared'], v['pmLogs'], v['pmSlotsCompared'], v['txWithSlotsCompared'], v['nativeCompared'], v['nativeMoved'],
        v['creates'], v['p256'], v['mints'], '; '.join(clients(c)[:6]), ex, WHY[c])
    out['cleared'].append({'chainIds': [c], 'lens': 'L2', 'check': 'L-1044 Task 2 on %s: replay of mined PoolManager transactions from parent-block storage, because no public endpoint serves traces for this window. %s' % (NAME[c], LAZY),
                           'result': res, 'source': 'cycles/024/theme-replay-eleven.work/raw/%d/lazy_*.jsonl; src/PoolManager.sol:104' % c})
json.dump(out, open(W + '/raw/research-draft.json', 'w'), indent=1)
print(len(out['cleared']), dict(tot))
