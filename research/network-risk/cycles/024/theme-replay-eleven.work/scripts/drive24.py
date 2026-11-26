"""Cycle 24 (L-1014): cycle 23 l997/drive.py with lazyreplay24 (CREATE, CREATE2, NativeCoinAuthority.mint, P256VERIFY),
over the L-997 transactions that cycle 23 set aside (selection and data read from cycles/023/stablecoin-l1.work/l997/raw).
Origin: L-997: cycle 21 drive.py (cycles/021/theme-arc-running-code.work/drive.py) unchanged apart from paths, over the ERC-20-only selection in raw/. usage: drive.py <url> <start> <end> <out.jsonl>"""
import sys, os, json, time
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H); SRC = os.path.join(H, "..", "..", "..", "023", "stablecoin-l1.work", "l997")
import lazyreplay24 as L
from rpc import batch, call
I = L.I; PM = L.PM; EM = L.EM
url, a, b, outp = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
D = json.load(open(SRC + '/raw/txs.json')); LG = json.load(open(SRC + '/raw/logs.json'))
S = {'selected': [json.loads(l)['tx'] for l in open(SRC + '/raw/pass1_all.jsonl') if 'unsupported' in json.loads(l)]}
pmt = '0x' + '0' * 24 + '%040x' % PM
# per block: tx indices that touch the PoolManager by a PoolManager log or a native Transfer log naming it
touch = {}; nat = {}
for l in LG['pm'] + LG['emitter']:
    touch.setdefault(int(l['blockNumber'], 16), set()).add(int(l['transactionIndex'], 16))
for l in LG['emitter']:
    nat.setdefault(int(l['blockNumber'], 16), set()).add(int(l['transactionIndex'], 16))
done = set()
if os.path.exists(outp):
    for line in open(outp): done.add(json.loads(line)['tx'])
fo = open(outp, 'a')
for h in S['selected'][a:b]:
    if h in done: continue
    t0 = time.time()
    tx, rec = D['tx'][h]['tx'], D['tx'][h]['rec']; bn = I(tx['blockNumber']); idx = I(tx['transactionIndex'])
    blk = D['blocks'][str(bn)]
    r = {'tx': h, 'block': bn, 'index': idx, 'to': tx['to'], 'type': tx['type']}
    try:
        base, w, ok, ret, err, rounds = L.replay(url, tx, rec, blk)
    except Exception as e:
        r['error'] = repr(e)[:200]; fo.write(json.dumps(r) + '\n'); fo.flush(); continue
    r['rounds'] = rounds; r['keysFetched'] = len(base.c)
    if w is not None: r['creates'] = getattr(w, 'creates', 0); r['mints'] = getattr(w, 'mints', 0); r['p256'] = getattr(w, 'p256', 0); r['collisions'] = getattr(w, 'collisions', 0)
    if err: r['unsupported'] = err; fo.write(json.dumps(r) + '\n'); fo.flush(); print(h[:12], 'unsupported', err[:80], flush=True); continue
    r['statusChain'] = I(rec['status']); r['statusRef'] = int(ok); r['steps'] = w.steps
    rl = [(l['address'].lower(), [x.lower() for x in l['topics']], l['data'].lower()) for l in rec['logs']]
    ol = [('0x%040x' % ad, ['0x%064x' % t for t in tp], '0x' + d.hex()) for (ad, tp, d) in w.logs]
    r['logsChain'] = len(rl); r['logsRef'] = len(ol); r['logsEqual'] = rl == ol
    if rl != ol:
        r['logMismatch'] = {'chain': [x for x in rl if x not in ol][:20], 'ref': [x for x in ol if x not in rl][:20]}
    r['pmFrames'] = [[f[0], f[2], f[3]] for f in w.frames]
    # PoolManager slots read or written
    keys = sorted({k for k in set(w.storage.keys()) | w.storage.read if k[0] == PM})
    later_pm = any(j > idx for j in touch.get(bn, ()))
    r['laterPmTxInBlock'] = later_pm; r['earlierPmTxInBlock'] = any(j < idx for j in touch.get(bn, ()))
    r['pmSlots'] = len(keys); r['pmSlotsWritten'] = sum(1 for k in w.storage.keys() if k[0] == PM)
    if not later_pm and keys:
        post = []
        for i in range(0, len(keys), 10):
            post += batch(url, [('eth_getStorageAt', ['0x%040x' % PM, hex(k[1]), hex(bn)]) for k in keys[i:i + 10]])
        mis = [[hex(k[1]), v, hex(w.storage.get(k, 0))] for k, v in zip(keys, post) if int(v, 16) != w.storage.get(k, 0)]
        r['pmSlotMismatch'] = mis
    # native flows of the PoolManager and of its payout recipients, from the reference's value logs
    flows = [(tp[1], tp[2], int.from_bytes(d, 'big')) for (ad, tp, d) in w.logs if ad == EM]
    pm_delta = sum(v for f, t, v in flows if t == PM) - sum(v for f, t, v in flows if f == PM)
    r['pmNativeDeltaRef'] = str(pm_delta)
    if nat.get(bn, set()) <= {idx}:
        b0, b1 = batch(url, [('eth_getBalance', ['0x%040x' % PM, hex(bn - 1)]), ('eth_getBalance', ['0x%040x' % PM, hex(bn)])])
        r['pmNativeDeltaChain'] = str(int(b1, 16) - int(b0, 16)); r['pmNativeEqual'] = int(b1, 16) - int(b0, 16) == pm_delta
    rec_chk = []
    for rcp in sorted({t for f, t, v in flows if f == PM}):
        if rcp in (int(tx['from'], 16), int(blk['miner'], 16)): rec_chk.append(['0x%040x' % rcp, 'sender or coinbase']); continue
        A = '0x' + '0' * 24 + '%040x' % rcp
        lg = call(url, 'eth_getLogs', [{'fromBlock': hex(bn), 'toBlock': hex(bn), 'address': '0x%040x' % EM, 'topics': [L.hex(L.T) if False else '0x%064x' % L.T, None, A]}]) + \
             call(url, 'eth_getLogs', [{'fromBlock': hex(bn), 'toBlock': hex(bn), 'address': '0x%040x' % EM, 'topics': ['0x%064x' % L.T, A]}])
        if {I(l['transactionIndex']) for l in lg} - {idx}: rec_chk.append(['0x%040x' % rcp, 'other tx in block']); continue
        b0, b1 = batch(url, [('eth_getBalance', ['0x%040x' % rcp, hex(bn - 1)]), ('eth_getBalance', ['0x%040x' % rcp, hex(bn)])])
        ref = sum(v for f, t, v in flows if t == rcp) - sum(v for f, t, v in flows if f == rcp)
        rec_chk.append(['0x%040x' % rcp, str(int(b1, 16) - int(b0, 16)), str(ref), int(b1, 16) - int(b0, 16) == ref])
    r['recipients'] = rec_chk
    r['secs'] = round(time.time() - t0, 1)
    fo.write(json.dumps(r) + '\n'); fo.flush()
    print(h[:12], idx, r['statusRef'], r['logsEqual'], r.get('pmSlotMismatch'), r.get('pmNativeEqual'), [x[-1] for x in rec_chk], r['secs'], rounds, flush=True)
