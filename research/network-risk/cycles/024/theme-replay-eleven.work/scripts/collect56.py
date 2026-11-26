"""Cycle 24 BNB Smart Chain variant (Task 3, L-1024): https://bsc.api.pocket.network rotates Geth v1.7.8, Geth v1.8.2 and
reth-bsc backends; only the archive backends answer traces of older blocks, so a refusal "required historical state
unavailable" is retried up to 12 times, and every transaction record carries web3_clientVersion read just before and just
after its trace calls (rec["clientAround"]), so each record is pinned to the builds that answered around it.

Task 1 collector for theme-state-replay (cycle 23, reused unchanged in cycle 24 theme-replay-eleven except for the endpoint tables). Read-only JSON-RPC only.
usage: collect.py <chainId> <target_txs>
1. Window: PoolManager logs (eth_getLogs on the PoolManager address), newest block first, until <target> distinct
   transactions are listed. The window (block range, head, endpoint) is written to raw/<cid>/window.json.
2. Per transaction, newest first: prestateTracer diffMode (pre and post of every changed word and balance),
   prestateTracer (the value at transaction start of every word the transaction read or wrote), callTracer withLog
   (every frame with value, input, output, error and its logs). Where muxTracer is served, diff and call come in one
   call. Only the PoolManager account is kept from the prestate results; call frames that neither touch the
   PoolManager nor contain a frame that does keep only their type, from, to, value and error.
Every 200 transactions web3_clientVersion is called on the trace endpoint before and after (raw/<cid>/brackets.jsonl).
Refusals and errors are appended to raw/<cid>/errors.jsonl."""
import json, os, sys, time, gzip, threading, queue
from rpcu import call
from eps import NETS
TRACE = {56: ['https://bsc.api.pocket.network'], 10: ['https://op.api.pocket.network'], 57073: ['https://ink.api.pocket.network', 'https://rpc-qnd.inkonchain.com'],
         42220: ['https://celo-json-rpc.stakely.io', 'https://celo.api.pocket.network'], 4217: ['https://rpc.mainnet.tempo.xyz'],
         196: ['https://xlayer.drpc.org'], 4663: ['https://robinhood.drpc.org'], 99901: ['https://elysium.drpc.org'], }
MUX = {'https://op.api.pocket.network', 'https://ink.api.pocket.network', 'https://celo-json-rpc.stakely.io', 'https://celo.api.pocket.network',
       'https://rpc.mainnet.tempo.xyz', 'https://bsc.api.pocket.network'}
MAXSPAN = {}
LOGS = {10: ['https://optimism-rpc.publicnode.com', 'https://mainnet.optimism.io'], 57073: ['https://rpc-gel.inkonchain.com', 'https://rpc-qnd.inkonchain.com'],
        42220: ['https://forno.celo.org', 'https://celo-json-rpc.stakely.io'], 4217: ['https://rpc.mainnet.tempo.xyz'], 196: ['https://rpc.xlayer.tech', 'https://xlayerrpc.okx.com'],
        4663: ['https://rpc.mainnet.chain.robinhood.com'], 99901: ['https://rpc.elysium.kinetiq.xyz'], 56: ['https://bsc-rpc.publicnode.com', 'https://bsc.api.pocket.network'],
        7777777: ['https://rpc.zora.energy'], 480: ['https://worldchain-mainnet.g.alchemy.com/public'], 1868: ['https://rpc.soneium.org'], 5042: ['https://rpc.mainnet.arc.io']}
cid = int(sys.argv[1]); target = int(sys.argv[2]); workers = int(sys.argv[3]) if len(sys.argv) > 3 else 6
PM = NETS[cid]['poolManager'].lower()
D = '../raw/%d' % cid; os.makedirs(D + '/tx', exist_ok=True)
elock = threading.Lock()
def elog(rec):
    with elock:
        open(D + '/errors.jsonl', 'a').write(json.dumps(rec) + '\n')

def window():
    p = D + '/window.json'
    if os.path.exists(p):
        w = json.load(open(p))
        if len(w['txs']) >= target or w.get('complete'): return w
    urls = LOGS[cid]; u = urls[0]
    head = None
    for u in urls:
        h, e = call(u, 'eth_blockNumber', [], 30)
        if h: head = int(h, 16); break
        elog({'stage': 'head', 'url': u, 'err': e})
    txs = {}; logs_n = 0; hi = head; span = 2000; ui = 0; fails = 0
    while len(txs) < target and hi > 0:
        lo = max(0, hi - span + 1)
        r, e = call(urls[ui % len(urls)], 'eth_getLogs', [{'address': PM, 'fromBlock': hex(lo), 'toBlock': hex(hi)}], 90)
        if e:
            elog({'stage': 'logs', 'url': urls[ui % len(urls)], 'range': [lo, hi], 'err': e}); fails += 1
            if 'too large' in e or 'exceeds max' in e or 'range' in e: MAXSPAN[cid] = max(10, min(MAXSPAN.get(cid, 10**9), span // 2)); span = MAXSPAN[cid]; fails -= 1
            elif span > 10: span //= 4
            else: ui += 1
            if fails > 60: break
            time.sleep(1); continue
        for l in r:
            h = l['transactionHash']; b = int(l['blockNumber'], 16)
            txs.setdefault(h, [b, int(l['transactionIndex'], 16)]); logs_n += 1
        hi = lo - 1
        if len(r) < 2000 and span < 100000: span = min(int(span * 1.5), MAXSPAN.get(cid, 10**9))
        elif len(r) > 5000: span = max(10, span // 2)
    order = sorted(txs.items(), key=lambda kv: (-kv[1][0], -kv[1][1]))[:target]
    blocks = [v[0] for _, v in order]
    w = {'chainId': cid, 'poolManager': PM, 'head': head, 'logEndpoints': urls, 'logsRead': logs_n, 'scannedDownTo': hi + 1,
         'firstBlock': min(blocks) if blocks else None, 'lastBlock': max(blocks) if blocks else None,
         'txs': [[h, v[0], v[1]] for h, v in order], 'complete': hi <= 0, 'time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    json.dump(w, open(p, 'w'))
    return w

def prune(f):
    """keep PoolManager related frames and their direct children; strip unrelated subtrees to a stub"""
    kids = [prune(c) for c in f.get('calls', [])]
    rel = f.get('to', '').lower() == PM or f.get('from', '').lower() == PM
    keepk = [k for k in kids if k[1]]
    sub = any(k[1] for k in kids)
    g = {k: f[k] for k in ('type', 'from', 'to', 'value', 'error', 'gas', 'gasUsed') if k in f}
    if rel or f.get('from', '').lower() == PM:
        g.update({k: f[k] for k in ('input', 'output', 'logs') if k in f})
        g['calls'] = [k[0] for k in kids]  # every direct child of a PoolManager frame, and of frames the PoolManager makes
        return g, True
    if sub:
        g['calls'] = [k[0] for k in kids]
        if 'logs' in f: g['logs'] = f['logs']
        return g, True
    lg = list(f.get('logs', []))
    if not f.get('error'):
        def sublogs(x):
            for c in x.get('calls', []):
                if c.get('error'): continue
                for l in c.get('logs', []): yield l
                yield from sublogs(c)
        lg += [dict(l, nested=True) for l in sublogs(f)]
    if lg: g['logs'] = lg
    return g, False

def keep_pm(x):
    if not isinstance(x, dict): return x
    return {k: v for k, v in x.items() if k.lower() == PM}

def trace(u, h, cfg):
    for k in range(12):
        r, e = call(u, 'debug_traceTransaction', [h, cfg], 120)
        if e is None: return r, None
        elog({'stage': 'trace', 'url': u, 'tx': h, 'cfg': cfg.get('tracer'), 'err': e[:300]})
        if '429' in e or 'rate' in e.lower() or 'EXC' in e or 'HTTP 5' in e: time.sleep(2 + 3 * k); continue
        if 'historical state' in e or 'missing trie node' in e: time.sleep(0.3); continue
        return None, e
    return None, e

def one(u, h, b, i):
    p = '%s/tx/%s.json.gz' % (D, h)
    if os.path.exists(p): return True
    rec = {'hash': h, 'block': b, 'index': i, 'url': u, 'clientAround': [call(u, 'web3_clientVersion', [], 20)[0]]}
    if u in MUX:
        r, e = trace(u, h, {'tracer': 'muxTracer', 'tracerConfig': {'prestateTracer': {'diffMode': True, 'disableCode': True}, 'callTracer': {'withLog': True}}})
        if r is None: rec['err'] = e; return False
        diff, ct = r['prestateTracer'], r['callTracer']
    else:
        diff, e = trace(u, h, {'tracer': 'prestateTracer', 'tracerConfig': {'diffMode': True, 'disableCode': True}})
        if diff is None: return False
        ct, e = trace(u, h, {'tracer': 'callTracer', 'tracerConfig': {'withLog': True}})
        if ct is None: return False
    pre, e = trace(u, h, {'tracer': 'prestateTracer', 'tracerConfig': {'disableCode': True}})
    if pre is None: return False
    rec['diff'] = {'pre': keep_pm(diff.get('pre')), 'post': keep_pm(diff.get('post'))}
    for s in ('pre', 'post'):
        for a, v in rec['diff'][s].items(): v.pop('code', None)
    rec['pre'] = keep_pm(pre)
    for a, v in rec['pre'].items(): v.pop('code', None)
    rec['call'] = prune(ct)[0]
    rec['clientAround'].append(call(u, 'web3_clientVersion', [], 20)[0])
    gzip.open(p + '.tmp', 'wt').write(json.dumps(rec)); os.rename(p + '.tmp', p)
    return True

def main():
    w = window(); print('window', len(w['txs']), w['firstBlock'], w['lastBlock'], flush=True)
    todo = [t for t in w['txs'] if not os.path.exists('%s/tx/%s.json.gz' % (D, t[0]))]
    q = queue.Queue(); [q.put(t) for t in todo]
    done = [0]; lock = threading.Lock(); urls = TRACE[cid]
    def br(tag):
        for u in urls:
            v, e = call(u, 'web3_clientVersion', [], 30)
            open(D + '/brackets.jsonl', 'a').write(json.dumps({'tag': tag, 'url': u, 'client': v, 'err': e, 'done': done[0], 't': time.time()}) + '\n')
    br('start')
    def wk(n):
        u = urls[n % len(urls)]
        while True:
            try: t = q.get_nowait()
            except queue.Empty: return
            ok = False
            for j in range(len(urls)):
                ok = one(urls[(n + j) % len(urls)], *t)
                if ok: break
            with lock:
                done[0] += 1
                if done[0] % 200 == 0: br('every200'); print(cid, done[0], len(todo), time.strftime('%H:%M:%S'), flush=True)
    th = [threading.Thread(target=wk, args=(n,)) for n in range(workers)]
    [t.start() for t in th]; [t.join() for t in th]
    br('end')
main()
