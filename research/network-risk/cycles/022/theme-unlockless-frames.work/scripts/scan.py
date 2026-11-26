"""Unlockless frame scan (cycle 22, theme-unlockless-frames). Read-only JSON-RPC.
For each candidate transaction (from lister.py output) fetch the callTracer tree (withLog) and the mined receipt,
then list every PoolManager frame with the PoolManager unlock frames above it on the call stack.
Mode 'tx': debug_traceTransaction per candidate + eth_getTransactionReceipt.
Mode 'block': debug_traceBlockByNumber per candidate block (every transaction of the block, candidate or not)
+ eth_getBlockReceipts.
Usage: scan.py <mode> <list.json> <out.jsonl> <threads> <maxblocks> <url> [<url>...]"""
import sys, os, json, time, itertools, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(__file__))
from rpcu import call
mode, lst, out, th, maxb = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
URLS = sys.argv[6:]
L = json.load(open(lst)); PM = L['pm'].lower()
cnt = itertools.count()
SEL = {'0x48c89491': 'unlock', '0xf3cd914c': 'swap', '0x5a6bcfda': 'modifyLiquidity', '0x234266d7': 'donate',
       '0x0b0d9c09': 'take', '0x11da60b4': 'settle', '0x3dd45adb': 'settleFor', '0x80f0b44c': 'clear',
       '0x156e29f6': 'mint', '0xf5298aca': 'burn', '0xa5841194': 'sync', '0x6276cbbe': 'initialize'}
DELTA = {'swap', 'modifyLiquidity', 'donate', 'take', 'settle', 'settleFor', 'clear', 'mint', 'burn'}
ALREADY, LOCKED = '0x5090d6c6', '0x54e3ca0d'
Z = '0x' + '0' * 40


def rpc(m, p, tries=10):
    last = None
    for k in range(tries):
        u = URLS[next(cnt) % len(URLS)]
        res, err = call(u, m, p, timeout=180)
        if err is None and res is not None:
            return res, u
        last = '%s %s' % (u, err or 'null')
        el = (err or '').lower()
        if 'not found' in el and 'transaction' not in el and 'block' not in el:
            break
        time.sleep(2 + 2 * k)
    raise RuntimeError(last)


def walk(fr, acc, nat, logs, anc, revd, depth):
    err = fr.get('error'); r = revd or bool(err)
    to = (fr.get('to') or '').lower(); fm = (fr.get('from') or '').lower(); typ = (fr.get('type') or '').upper()
    val = int(fr.get('value') or '0x0', 16)
    inp = fr.get('input') or '0x'
    me = None
    if to == PM and typ != 'DELEGATECALL':
        s = inp[:10]
        name = SEL.get(s, s)
        bal = [c.get('output') for c in (fr.get('calls') or []) if (c.get('input') or '')[:10] == '0x70a08231'
               and (c.get('input') or '')[34:74] == PM[2:] and not c.get('error')]
        me = len(acc)
        acc.append({'seq': me, 'sel': name, 'type': typ, 'depth': depth, 'anc': anc[-1] if anc else None, 'ancs': list(anc),
                    'rev': r, 'own': bool(err), 'err': (err or '')[:60], 'out': (fr.get('output') or '')[:74],
                    'value': val, 'from': fm, 'arg': ('0x' + inp[34:74]) if len(inp) >= 74 else None, 'bal': bal})
    elif to == PM and typ == 'DELEGATECALL':
        acc.append({'seq': len(acc), 'sel': SEL.get(inp[:10], inp[:10]), 'type': typ, 'depth': depth, 'anc': anc[-1] if anc else None,
                    'ancs': list(anc), 'rev': r, 'own': bool(err), 'err': (err or '')[:60], 'out': '', 'value': val, 'from': fm, 'arg': None, 'bal': []})
    if not r and val and typ in ('CALL', 'SELFDESTRUCT', 'CREATE', 'CREATE2', 'CALLCODE'):
        if fm == PM: nat['out'] += val
        if to == PM: nat['in'] += val
    if not r:
        for lg in fr.get('logs') or []:
            logs.append([(lg.get('address') or '').lower(), [t.lower() for t in (lg.get('topics') or [])], (lg.get('data') or '0x').lower()])
    nanc = anc + [me] if (me is not None and acc[me]['sel'] == 'unlock') else anc
    for c in fr.get('calls') or []:
        walk(c, acc, nat, logs, nanc, r, depth + 1)


def model(frames):
    synced, reserves = None, None; bad = []; n = 0
    for f in frames:
        if f['rev'] or f['type'] == 'DELEGATECALL': continue
        if f['sel'] == 'sync':
            if f['arg'] == Z or f['arg'] is None: synced, reserves = None, None
            else:
                synced = f['arg']; reserves = int(f['bal'][0], 16) if f['bal'] and f['bal'][0] not in (None, '0x') else None
        elif f['sel'] in ('settle', 'settleFor'):
            n += 1
            got = int(f['out'], 16) if f['out'] not in (None, '', '0x') else None
            if synced is None: exp = f['value']
            else:
                now = int(f['bal'][0], 16) if f['bal'] and f['bal'][0] not in (None, '0x') else None
                exp = (now - reserves) if (now is not None and reserves is not None) else None
            if got is None or exp is None or got != exp:
                bad.append({'sel': f['sel'], 'synced': synced, 'exp': exp, 'got': got, 'value': f['value']})
            synced, reserves = None, None
    return synced, bad, n


def analyse(h, blk, idx, tr, rcpt):
    acc = []; nat = {'in': 0, 'out': 0}; logs = []
    walk(tr, acc, nat, logs, [], False, 0)
    ok = not tr.get('error')
    st = int(rcpt.get('status', '0x1'), 16) if rcpt else None
    rlogs = sorted([[(l['address'] or '').lower(), [t.lower() for t in l['topics']], (l['data'] or '0x').lower()] for l in (rcpt.get('logs') or [])]) if rcpt else None
    logsEq = (sorted(logs) == rlogs) if (rcpt is not None and ok) else None
    A = [f['seq'] for f in acc if f['sel'] in DELTA and not f['rev'] and f['type'] != 'DELEGATECALL' and f['anc'] is None]
    failedU = [f['seq'] for f in acc if f['sel'] == 'unlock' and f['own']]
    B = []
    for u in failedU:
        for f in acc:
            if f['seq'] > u and f['sel'] in DELTA and not f['rev'] and f['type'] != 'DELEGATECALL':
                if not (f['anc'] is not None and (f['anc'] > u or f['anc'] in acc[u]['ancs'])):
                    B.append([u, f['seq']])
    laterOkUnlock = any(f['sel'] == 'unlock' and not f['rev'] and f['seq'] > u for u in failedU for f in acc)
    X1 = [f['seq'] for f in acc if f['sel'] == 'unlock' and f['anc'] is None and f['own'] and f['out'][:10] == ALREADY]
    X2 = [f['seq'] for f in acc if f['sel'] in DELTA and f['anc'] is not None and f['own'] and f['out'][:10] == LOCKED and not acc[f['anc']]['own']]
    s, bad, n = model(acc) if ok else (None, [], 0)
    return {'tx': h, 'block': blk, 'idx': idx, 'ok': ok, 'status': st, 'logsEq': logsEq, 'nLogs': len(logs),
            'nPM': len(acc), 'nDelta': sum(1 for f in acc if f['sel'] in DELTA), 'nUnlock': sum(1 for f in acc if f['sel'] == 'unlock'),
            'A': A, 'B': B, 'failedUnlock': len(failedU), 'laterOkUnlock': laterOkUnlock, 'X1': X1, 'X2': X2,
            'endSynced': s, 'bad': bad, 'settleChecks': n, 'natIn': nat['in'], 'natOut': nat['out'],
            'frames': [[f['sel'], f['type'], f['depth'], f['anc'], int(f['rev']), int(f['own']), f['out'][:10], f['value'], f['from'], f['arg']] for f in acc]
            if (acc and (A or B or X1 or X2 or bad or s or failedU)) else len(acc)}


def do_tx(item):
    h, blk, idx = item
    try:
        tr, u1 = rpc('debug_traceTransaction', [h, {'tracer': 'callTracer', 'tracerConfig': {'withLog': True}}])
        rc, u2 = rpc('eth_getTransactionReceipt', [h])
    except Exception as e:
        return [{'tx': h, 'block': blk, 'fail': str(e)[:300]}]
    r = analyse(h, blk, idx, tr, rc); r['via'] = u1
    return [r]


def do_block(blk):
    try:
        trs, u1 = rpc('debug_traceBlockByNumber', [hex(blk), {'tracer': 'callTracer', 'tracerConfig': {'withLog': True}}])
        rcs, u2 = rpc('eth_getBlockReceipts', [hex(blk)])
    except Exception as e:
        return [{'block': blk, 'fail': str(e)[:300]}]
    if len(trs) != len(rcs):
        return [{'block': blk, 'fail': 'trace count %d receipt count %d' % (len(trs), len(rcs))}]
    res = []
    for i, (t, rc) in enumerate(zip(trs, rcs)):
        h = t.get('txHash') or rc['transactionHash']
        if h != rc['transactionHash']:
            res.append({'block': blk, 'fail': 'hash order mismatch at %d' % i}); continue
        tr = t.get('result') or t
        r = analyse(h, blk, i, tr, rc); r['via'] = u1
        if r['nPM'] or h in CAND:
            r['cand'] = h in CAND
            res.append(r)
    res.append({'block': blk, 'blockDone': True, 'nTx': len(trs)})
    return res


txs = {}
for l in L['logs'].values():
    txs[l['tx']] = (l['tx'], l['block'], l['txi'])
CAND = set(txs)
items = sorted(txs.values(), key=lambda x: (-x[1], x[2]))
done = set()
if os.path.exists(out):
    for line in open(out):
        try:
            j = json.loads(line)
        except Exception:
            continue
        if 'fail' in j: continue
        done.add(j.get('tx') if mode == 'tx' else (j['block'] if j.get('blockDone') else None))
if mode == 'tx':
    todo = [it for it in items if it[0] not in done][:maxb]; fn = do_tx
else:
    blocks = []
    for it in items:
        if it[1] not in blocks: blocks.append(it[1])
    todo = [b for b in blocks if b not in done][:maxb]; fn = do_block
f = open(out, 'a')
f.write(json.dumps({'meta': True, 'mode': mode, 'urls': URLS, 'clientVersionStart': {u: call(u, 'web3_clientVersion', []) for u in URLS},
                    'time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'todo': len(todo)}) + '\n')
k = 0; t0 = time.time()
with cf.ThreadPoolExecutor(th) as ex:
    for rs in ex.map(fn, todo):
        for r in rs:
            f.write(json.dumps(r) + '\n')
        k += 1
        if k % 200 == 0: f.flush(); print(k, len(todo), round(time.time() - t0), flush=True)
f.write(json.dumps({'meta': True, 'end': True, 'clientVersionEnd': {u: call(u, 'web3_clientVersion', []) for u in URLS},
                    'time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}) + '\n')
f.close(); print('finished', k, flush=True)
