"""L-997 second pass: cycle 21 prefix.py (cycles/021/theme-arc-running-code.work/prefix.py) unchanged apart from paths.
the block from its first transaction up to it on one state (lazyreplay.replay_prefix) and compare again.
usage: prefix.py <in.jsonl ...> -> raw/prefix.jsonl"""
import sys, os, json, glob
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(H, "..", "..", "..", "021", "theme-arc-running-code.work")); os.chdir(H)
import lazyreplay as L
from rpc import batch
I = L.I; PM = L.PM; EM = L.EM; U = os.environ.get('URL', 'https://rpc.mainnet.arc.io')
D = json.load(open('raw/txs.json')); LG = json.load(open('raw/logs.json'))
touch = {}
for l in LG['pm'] + LG['emitter']: touch.setdefault(int(l['blockNumber'], 16), set()).add(int(l['transactionIndex'], 16))
def bad(r):
    if 'logsEqual' not in r: return False
    return (not r['logsEqual']) or r['statusRef'] != r['statusChain'] or bool(r.get('pmSlotMismatch')) or r.get('pmNativeEqual') is False or any(x[-1] is False for x in r['recipients'])
SH, NS = int(os.environ.get('SHARD', 0)), int(os.environ.get('NSHARD', 1)); OUT = os.environ.get('OUT', 'raw/prefix.jsonl')
todo = []
for f in sys.argv[1:]:
    for l in open(f):
        r = json.loads(l)
        if bad(r): todo.append(r['tx'])
done = set()
for f in glob.glob('raw/prefix*.jsonl'):
    done |= {json.loads(l)['tx'] for l in open(f)}
fo = open(OUT, 'a')
for n_, h in enumerate(todo):
    if n_ % NS != SH: continue
    if h in done: continue
    tx, rec = D['tx'][h]['tx'], D['tx'][h]['rec']; bn = I(tx['blockNumber']); idx = I(tx['transactionIndex']); blk = D['blocks'][str(bn)]
    hs = blk['transactions'][:idx]
    pairs = []
    for i in range(0, len(hs), 5):
        ch = hs[i:i + 5]; r = batch(U, [('eth_getTransactionByHash', [x]) for x in ch] + [('eth_getTransactionReceipt', [x]) for x in ch])
        pairs += [(r[j], r[len(ch) + j]) for j in range(len(ch))]
    pairs.append((tx, rec))
    out = {'tx': h, 'block': bn, 'index': idx}
    try:
        base, w, ok, ret, err, rounds, notes = L.replay_prefix(U, pairs, blk)
    except Exception as e:
        out['error'] = repr(e)[:200]; fo.write(json.dumps(out) + '\n'); fo.flush(); continue
    out['notes'] = notes; out['rounds'] = rounds
    if err: out['unsupported'] = err; fo.write(json.dumps(out) + '\n'); fo.flush(); print(h[:12], err[:60], flush=True); continue
    rl = [(l['address'].lower(), [x.lower() for x in l['topics']], l['data'].lower()) for l in rec['logs']]
    ol = [('0x%040x' % ad, ['0x%064x' % t for t in tp], '0x' + d.hex()) for (ad, tp, d) in w.logs]
    out.update({'statusChain': I(rec['status']), 'statusRef': int(ok), 'logsEqual': rl == ol, 'logsChain': len(rl), 'logsRef': len(ol)})
    pa = '0x%040x' % PM; pt = '0x' + '0' * 24 + pa[2:]; ea = '0x%040x' % EM
    sub = lambda L_: [x for x in L_ if x[0] == pa]
    nat = lambda L_: [x for x in L_ if x[0] == ea and len(x[1]) == 3 and pt in x[1][1:]]
    out['pmLogsEqual'] = sub(rl) == sub(ol); out['pmLogs'] = len(sub(rl)); out['pmNativeLogsEqual'] = nat(rl) == nat(ol); out['pmNativeLogs'] = len(nat(rl))
    out['diffAddrs'] = sorted({x[0] for x in rl if x not in ol} | {x[0] for x in ol if x not in rl})
    if rl != ol: out['logMismatch'] = {'chain': [x for x in rl if x not in ol][:20], 'ref': [x for x in ol if x not in rl][:20], 'chainOrder': [x[0][:10] + x[1][0][:10] for x in rl], 'refOrder': [x[0][:10] + x[1][0][:10] for x in ol]}
    # PoolManager slots: compare with block N when no later transaction of the block touches the PoolManager (checked in pass one)
    keys = sorted({k for k in set(w.storage.keys()) | w.storage.read if k[0] == PM})
    if not any(j > idx for j in touch.get(bn, ())) and keys:
        post = []
        for i in range(0, len(keys), 10):
            post += batch(U, [('eth_getStorageAt', ['0x%040x' % PM, hex(k[1]), hex(bn)]) for k in keys[i:i + 10]])
        out['pmSlots'] = len(keys); out['pmSlotMismatch'] = [[hex(k[1]), v, hex(w.storage.get(k, 0))] for k, v in zip(keys, post) if int(v, 16) != w.storage.get(k, 0)]
    fo.write(json.dumps(out) + '\n'); fo.flush()
    print(h[:12], idx, out['statusRef'], out['logsEqual'], len(notes), flush=True)
