"""Task 3: rerun a whole mined transaction in pyevm_tx17.py, with calls into node-implemented contracts answered from the
chain's own call tree (callTracer withLog), and compare with the chain: the success flag of every PoolManager frame in
order, the receipt logs, and every changed storage slot of bytecode accounts (prestateTracer diffMode), PoolManager first.
Built on cycles/016/theme-revert-rollback-mined.work/replay.py (read, not changed). Read-only RPC.
usage: python3 replay17.py <chainId> <traceUrl> <txhash> <out.json>"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__)); NR = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(NR, 'tools', 'opdiff')); sys.path.insert(0, HERE)
sys.path.insert(1, os.path.join(NR, 'cycles', '016', 'theme-revert-rollback-mined.work'))
import pyevm_tx17 as P
import scan as S
I = lambda x: int(x, 16) if isinstance(x, str) else int(x or 0)
def R(u, m, p): return S.R(u, m, p, timeout=180)

def pm_frames(node, pm, acc):
    if (node.get('to') or '').lower() == pm and node.get('type') in ('CALL', 'STATICCALL', 'DELEGATECALL', 'CALLCODE'):
        acc.append((S.SEL.get(node.get('input', '')[2:10], node.get('input', '')[2:10]), 'error' not in node))
    for c in node.get('calls', []) or []: pm_frames(c, pm, acc)

def oracle(node, native, acc, nodes):
    to = int(node.get('to') or '0x0', 16)
    if to in native and node.get('type') in ('CALL', 'STATICCALL', 'DELEGATECALL', 'CALLCODE'):
        logs = [(int(l['address'], 16), tuple(int(t, 16) for t in l['topics']), bytes.fromhex(l['data'][2:])) for l in node.get('logs', []) or []]
        acc.setdefault((to, bytes.fromhex((node.get('input') or '0x')[2:])), []).append(('error' not in node, bytes.fromhex((node.get('output') or '0x')[2:]), logs))
        nodes.append(('0x%040x' % to, (node.get('input') or '')[:10], 'error' not in node, len(node.get('calls', []) or [])))
    for c in node.get('calls', []) or []: oracle(c, native, acc, nodes)

def one(cid, url, pm, h):
    tx = R(url, 'eth_getTransactionByHash', [h]); rec = R(url, 'eth_getTransactionReceipt', [h])
    blk = R(url, 'eth_getBlockByNumber', [tx['blockNumber'], False])
    pre = R(url, 'debug_traceTransaction', [h, {'tracer': 'prestateTracer'}])
    dif = R(url, 'debug_traceTransaction', [h, {'tracer': 'prestateTracer', 'tracerConfig': {'diffMode': True}}])
    ct = R(url, 'debug_traceTransaction', [h, {'tracer': 'callTracer', 'tracerConfig': {'withLog': True}}])
    codes, bal, nonces = {}, {}, {}
    for a, v in pre.items():
        ai = int(a, 16)
        if v.get('code') and v['code'] != '0x': codes[ai] = bytes.fromhex(v['code'][2:])
        bal[ai] = I(v.get('balance', '0x0')); nonces[ai] = I(v.get('nonce', 0))
    w = P.World(codes, bal)
    for a, v in pre.items():
        for k, x in (v.get('storage') or {}).items(): w.storage[(int(a, 16), int(k, 16))] = int(x, 16)
    w.native = {a for a, c in codes.items() if 0 < len(c) <= 2}
    orc, nodes = {}, []; oracle(ct, w.native, orc, nodes); w.oracle = orc
    oog = {}
    def ow(n):
        if n.get('type') in ('CALL', 'STATICCALL', 'DELEGATECALL', 'CALLCODE'):
            oog.setdefault((int(n.get('to') or '0x0', 16), bytes.fromhex((n.get('input') or '0x')[2:])), []).append('gas' in (n.get('error') or '').lower())
        for c in n.get('calls', []) or []: ow(c)
    for c in ct.get('calls', []) or []: ow(c)
    w.oog = oog if any(any(v) for v in oog.values()) else None
    w.watch = {int(pm, 16)}; w.max_steps = 60_000_000
    w.ctx = {'origin': int(tx['from'], 16), 'gasprice': I(rec.get('effectiveGasPrice') or tx.get('gasPrice')), 'coinbase': int(blk['miner'], 16),
             'timestamp': I(blk['timestamp']), 'number': I(blk['number']), 'prevrandao': int(blk.get('mixHash') or '0x0', 16),
             'gaslimit': I(blk['gasLimit']), 'chainid': cid, 'basefee': I(blk.get('baseFeePerGas') or '0x0'),
             'exists': {int(a, 16) for a in pre}, 'nonces': nonces, 'gas': I(tx['gas'])}
    if cid in (42161, 4663, 99901) and blk.get('l1BlockNumber'):
        w.ctx['l2number'] = w.ctx['number']; w.ctx['number'] = I(blk['l1BlockNumber'])
    res = {'tx': h, 'block': I(tx['blockNumber']), 'native': sorted('0x%040x' % a for a in w.native), 'nativeCallsInTree': nodes}
    try:
        ok, ret = w.call(int(tx['from'], 16), int(tx['to'], 16), I(tx['value']), bytes.fromhex(tx['input'][2:]), False, 0)
    except NotImplementedError as e:
        res['unsupported'] = str(e)[:160]; return res
    except TimeoutError:
        res['unsupported'] = 'step limit'; return res
    chain_pm = []; pm_frames(ct, pm.lower(), chain_pm)
    ref_pm = [(S.SEL.get(f[2], f[2]), bool(f[3])) for f in w.frames]
    rl = [(l['address'].lower(), tuple(x.lower() for x in l['topics']), l['data'].lower()) for l in rec['logs']]
    ol = [('0x%040x' % a, tuple('0x%064x' % t for t in tp), '0x' + d.hex()) for (a, tp, d) in w.logs]
    exp = {}
    for a, v in (dif.get('pre') or {}).items():
        for k in (v.get('storage') or {}): exp[(int(a, 16), int(k, 16))] = 0
    for a, v in (dif.get('post') or {}).items():
        for k, x in (v.get('storage') or {}).items(): exp[(int(a, 16), int(k, 16))] = int(x, 16)
    prest = {(int(a, 16), int(k, 16)): int(x, 16) for a, v in pre.items() for k, x in (v.get('storage') or {}).items()}
    skip = set(w.native) | {0xa4b05fffffffffffffffffffffffffffffffffff}
    smis = []; pmi = int(pm, 16)
    for key, val in exp.items():
        if key[0] in skip: continue
        if w.storage.get(key, 0) != val: smis.append(['%x' % key[0], '%x' % key[1], hex(val), hex(w.storage.get(key, 0))])
    for key, val in w.storage.items():
        if key[0] in skip: continue
        if key not in exp and prest.get(key, 0) != val: smis.append(['%x' % key[0], '%x' % key[1], 'unchanged', hex(val)])
    res.update({'statusChain': I(rec['status']), 'statusRef': int(ok), 'pmFramesChain': len(chain_pm), 'pmFramesEqual': chain_pm == ref_pm,
                'pmChain': chain_pm, 'pmRef': ref_pm, 'logsChain': len(rl), 'logsRef': len(ol), 'logsEqual': rl == ol,
                'logsMissingInRef': [x[0] for x in rl if x not in ol][:8], 'logsExtraInRef': [x[0] for x in ol if x not in rl][:8],
                'slotsCompared': sum(1 for k in exp if k[0] not in skip), 'pmSlotsCompared': sum(1 for k in exp if k[0] == pmi),
                'nativeSlotsNotModelled': sum(1 for k in exp if k[0] in skip), 'storageMismatch': smis[:20],
                'pmSlotMismatch': [m for m in smis if int(m[0], 16) == pmi], 'oracleCallsUsed': len(w.oracled),
                'oracleCallsLeft': sum(len(v) for v in orc.values()), 'forcedOOG': w.forced, 'steps': w.steps})
    return res

if __name__ == '__main__':
    cid, url, h, out = int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
    nets = {n['chainId']: n for n in json.load(open(os.path.join(NR, 'state', 'networks.json')))['networks']}
    r = one(cid, url, nets[cid]['poolManager'], h)
    json.dump(r, open(out, 'w'), indent=1)
    print({k: v for k, v in r.items() if k not in ('nativeCallsInTree', 'pmChain', 'pmRef', 'native')})
