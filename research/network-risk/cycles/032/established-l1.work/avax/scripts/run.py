"""Tasks 2 to 4 for theme-state-replay: replay every collected transaction through model.py and compare.
usage: run.py <chainId> [limit]
Writes raw/<cid>/result.json (totals) and raw/<cid>/mismatches.jsonl (every mismatch record in full)."""
import json, os, sys, gzip, glob, time, traceback
sys.setrecursionlimit(20000)
from model import Model, Revert, Unmodelled, I, T_ERC20, U160, keccak
T_DEP = int.from_bytes(keccak(b'Deposit(address,uint256)'), 'big'); T_WDR = int.from_bytes(keccak(b'Withdrawal(address,uint256)'), 'big')
from eps import NETS
cid = int(sys.argv[1]); lim = int(sys.argv[2]) if len(sys.argv) > 2 else 10 ** 9
PM = NETS[cid]['poolManager'].lower(); PMI = int(PM, 16)
D = '../raw/%d' % cid
FIX = int(open('../raw/prune_fix_time.txt').read())
files = sorted(glob.glob(D + '/tx/*.json.gz'))[:lim]
tot = {'chainId': cid, 'txs': 0, 'wordsCompared': 0, 'storageWordsChanged': 0, 'txWithMismatch': 0, 'mismatchKinds': {}, 'counts': {},
       'nativeChecked': 0, 'nativeMismatch': 0, 'nativeMoved': 0, 'erc20Checked': 0, 'erc20Deficit': 0, 'erc20Surplus': 0, 'unmodelled': 0,
       'unreadSlots': 0, 'blocks': [None, None], 'failedTx': 0, 'withModifyLiquidity': 0, 'withSwap': 0, 'withDonate': 0, 'with6909': 0,
       'withInitialize': 0, 'nativeTxs': 0}
out = open(D + '/mismatches.jsonl', 'w')
def logs_all(f):
    for l in f.get('logs', []): yield l
    for c in f.get('calls', []):
        if not c.get('error'): yield from logs_all(c)
t0 = time.time()
for fn in files:
    rec = json.load(gzip.open(fn))
    pre = rec['pre'].get(next((k for k in rec['pre'] if k.lower() == PM), ''), {})
    dpre = next((v for k, v in rec['diff']['pre'].items() if k.lower() == PM), {})
    dpost = next((v for k, v in rec['diff']['post'].items() if k.lower() == PM), {})
    m = Model(PM, pre.get('storage'), I(pre.get('balance')))
    err = None
    try:
        m.frame(rec['call'])
        m.finish(dpre, dpost)
    except (Unmodelled, RecursionError) as e:
        err = 'unmodelled: ' + str(e)[:200]; tot['unmodelled'] += 1
    except Exception as e:
        err = 'exception: ' + traceback.format_exc()[-600:]; tot['unmodelled'] += 1
    tot['txs'] += 1; tot['wordsCompared'] += m.words_compared
    tot['storageWordsChanged'] += len(set((dpost.get('storage') or {})) | set((dpre.get('storage') or {})))
    b = rec['block']; tot['blocks'] = [min(b, tot['blocks'][0] or b), max(b, tot['blocks'][1] or b)]
    if rec['call'].get('error'): tot['failedTx'] += 1
    for k, v in m.counts.items(): tot['counts'][k] = tot['counts'].get(k, 0) + v
    acts = [a[0] for a in m.actions]
    for a, kk in (('modifyLiquidity', 'withModifyLiquidity'), ('swap', 'withSwap'), ('donate', 'withDonate'), ('initialize', 'withInitialize')):
        if a in acts: tot[kk] += 1
    if any(a in acts for a in ('mint', 'burn')): tot['with6909'] += 1
    mm = list(m.mm)
    if m.unread: tot['unreadSlots'] += 1; mm.append({'kind': 'model-read-slot-not-in-prestate', 'slots': [hex(x) for x in sorted(m.unread)][:20]})
    # Task 3, native: balance change = native settles - native takes - native fee collection, and = traced value flows
    if err is None:
        b0, b1 = m.bal_mined
        tot['nativeChecked'] += 1
        if b0 != b1 or m.native['settle'] or m.native['take']: tot['nativeTxs'] += 1
        if b1 != b0: tot['nativeMoved'] += 1
        exp1 = m.native['settle'] - m.native['take'] - m.native['collect']
        exp2 = m.native['in_frames'] - m.native['out_frames']
        if b0 != I(pre.get('balance')) or b1 - b0 != exp1 or b1 - b0 != exp2 or m.bal != b1:
            tot['nativeMismatch'] += 1
            mm.append({'kind': 'native', 'preBalance': I(pre.get('balance')), 'diffPre': b0, 'diffPost': b1, 'settleMinusTake': exp1,
                       'valueFramesNet': exp2, 'model': m.bal, 'flows': m.native})
        # Task 3, ERC-20: Transfer logs into and out of the PoolManager against settles, takes and fee collection
        flows = {}
        rp = '%s/rcpt/%s.json.gz' % (D, rec['hash'])
        if os.path.exists(rp): LG = json.load(gzip.open(rp))['logs']; tot['erc20FromReceipt'] = tot.get('erc20FromReceipt', 0) + 1
        elif os.path.getmtime(fn) < FIX: LG = None; tot['erc20NoLogs'] = tot.get('erc20NoLogs', 0) + 1
        else: LG = list(logs_all(rec['call']))
        for l in (LG or []):
            t = l.get('topics') or []
            if len(t) == 2 and I(t[0]) in (T_DEP, T_WDR) and (I(t[1]) & U160) == PMI and len(l.get('data') or '0x') <= 66:
                # WETH9 Deposit(dst, wad) and Withdrawal(src, wad): a native take with the wrapped native contract as recipient mints to the PoolManager
                a = int(l['address'], 16); amt = I(l.get('data') or '0x0'); tot['wethEvents'] = tot.get('wethEvents', 0) + 1
                flows.setdefault(a, [0, 0])[0 if I(t[0]) == T_DEP else 1] += amt
            if len(t) == 3 and I(t[0]) == T_ERC20:
                a = int(l['address'], 16); fr = I(t[1]) & U160; to = I(t[2]) & U160; amt = I(l.get('data') or '0x0') if len(l.get('data') or '0x') <= 66 else None
                if amt is None: continue
                if to == PMI and fr != PMI: flows.setdefault(a, [0, 0])[0] += amt
                if fr == PMI and to != PMI: flows.setdefault(a, [0, 0])[1] += amt
        for cur in (set(flows) | set(m.erc20)) if LG is not None else []:
            if cur == 0: continue
            fin, fout = flows.get(cur, [0, 0]); e = m.erc20.get(cur, {'paid': 0, 'take': 0, 'collect': 0})
            tot['erc20Checked'] += 1
            net_logs = fin - fout; net_model = e['paid'] - e['take'] - e['collect']
            if net_logs < net_model or fout != e['take'] + e['collect']:
                tot['erc20Deficit'] += 1
                mm.append({'kind': 'erc20-flow', 'token': hex(cur), 'logsIn': fin, 'logsOut': fout, 'paid': e['paid'], 'take': e['take'], 'collect': e['collect'],
                           'hasModifyLiquidity': 'modifyLiquidity' in acts})
            elif net_logs > net_model: tot['erc20Surplus'] += 1
    if err: mm.append({'kind': 'unmodelled', 'err': err})
    if mm:
        tot['txWithMismatch'] += 1
        for x in mm: tot['mismatchKinds'][x['kind']] = tot['mismatchKinds'].get(x['kind'], 0) + 1
        out.write(json.dumps({'hash': rec['hash'], 'block': b, 'index': rec.get('index'), 'url': rec.get('url'), 'mismatches': mm, 'actions': m.actions[:60]}) + '\n')
tot['secs'] = round(time.time() - t0, 1)
json.dump(tot, open(D + '/result.json', 'w'), indent=1)
print(json.dumps(tot))
