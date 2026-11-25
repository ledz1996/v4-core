"""Cycle 16, theme-revert-rollback-mined, task 1 second half. Read-only.
For each transaction a scan found (a PoolManager frame undone and a later one not), rerun the whole
transaction in pyevm_tx.py (the reference interpreter of tools/opdiff/pyevm.py with block context,
logs and ecrecover added) from the parent-block state that prestateTracer reports, and compare with
the chain: the own success flag of every PoolManager frame in order, the surviving logs, and the final
value of every storage slot the transaction changed (prestateTracer diffMode).
Usage: python3 replay.py <chainId> <traceUrl> <scan.json> <out.json> [maxTx]"""
import sys, json, time
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/016/theme-revert-rollback-mined.work')
from evm import rpc
import pyevm_tx as P
import scan as S

def R(u, m, p): return S.R(u, m, p, timeout=120)
I = lambda x: int(x, 16) if isinstance(x, str) else int(x or 0)

def pm_frames(node, pm, acc):
    if (node.get('to') or '').lower() == pm and node.get('type') in ('CALL', 'STATICCALL', 'DELEGATECALL', 'CALLCODE'):
        acc.append((S.SEL.get(node.get('input', '')[2:10], node.get('input', '')[2:10]), 'error' not in node))
    for c in node.get('calls', []) or []: pm_frames(c, pm, acc)

def one(cid, url, pm, h, lurl):
    tx = R(lurl, 'eth_getTransactionByHash', [h]); rec = R(lurl, 'eth_getTransactionReceipt', [h])
    blk = R(lurl, 'eth_getBlockByNumber', [tx['blockNumber'], False])
    pre = R(url, 'debug_traceTransaction', [h, {'tracer': 'prestateTracer'}])
    dif = R(url, 'debug_traceTransaction', [h, {'tracer': 'prestateTracer', 'tracerConfig': {'diffMode': True}}])
    ct = R(url, 'debug_traceTransaction', [h, {'tracer': 'callTracer', 'tracerConfig': {'withLog': True}}])
    if not tx.get('to'): return {'tx': h, 'skip': 'creation'}
    codes, bal = {}, {}; w = None
    for a, v in pre.items():
        ai = int(a, 16)
        if v.get('code') and v['code'] != '0x': codes[ai] = bytes.fromhex(v['code'][2:])
        bal[ai] = I(v.get('balance', '0x0'))
    w = P.World(codes, bal)
    for a, v in pre.items():
        for k, x in (v.get('storage') or {}).items(): w.storage[(int(a, 16), int(k, 16))] = int(x, 16)
    w.native = {a for a, c in codes.items() if 0 < len(c) <= 2}
    w.watch = {int(pm, 16)}; w.max_steps = 60_000_000
    w.ctx = {'origin': int(tx['from'], 16), 'gasprice': I(rec.get('effectiveGasPrice') or tx.get('gasPrice')), 'coinbase': int(blk['miner'], 16),
             'timestamp': I(blk['timestamp']), 'number': I(blk['number']), 'prevrandao': int(blk.get('mixHash') or '0x0', 16),
             'gaslimit': I(blk['gasLimit']), 'chainid': cid, 'basefee': I(blk.get('baseFeePerGas') or '0x0'),
             'exists': {int(a, 16) for a in pre}, 'gas': I(tx['gas'])}
    if cid in (42161, 4663, 99901) and blk.get('l1BlockNumber'):
        w.ctx['l2number'] = w.ctx['number']; w.ctx['number'] = I(blk['l1BlockNumber'])
    o = int(tx['from'], 16); fee = I(tx['gas']) * w.ctx['gasprice']
    if bal.get(o, 0) >= fee + I(tx['value']): w.balances[o] -= 0  # gas is not modelled; balance left as reported
    try:
        ok, ret = w.call(o, int(tx['to'], 16), I(tx['value']), bytes.fromhex(tx['input'][2:]), False, 0)
    except NotImplementedError as e:
        return {'tx': h, 'unsupported': str(e)[:120]}
    except TimeoutError:
        return {'tx': h, 'unsupported': 'step limit'}
    chain_pm = []; pm_frames(ct, pm.lower(), chain_pm)
    ref_pm = [(S.SEL.get(f[2], f[2]), bool(f[3])) for f in w.frames]
    rl = [(l['address'].lower(), tuple(x.lower() for x in l['topics']), l['data'].lower()) for l in rec['logs']]
    ol = [('0x%040x' % a, tuple('0x%064x' % t for t in tp), '0x' + d.hex()) for (a, tp, d) in w.logs]
    # storage: every slot the chain changed, and every slot the reference changed
    exp = {}
    for a, v in (dif.get('pre') or {}).items():
        for k in (v.get('storage') or {}): exp[(int(a, 16), int(k, 16))] = 0
    for a, v in (dif.get('post') or {}).items():
        for k, x in (v.get('storage') or {}).items(): exp[(int(a, 16), int(k, 16))] = int(x, 16)
    prest = {(int(a, 16), int(k, 16)): int(x, 16) for a, v in pre.items() for k, x in (v.get('storage') or {}).items()}
    smis = []; SYS = {0xa4b05fffffffffffffffffffffffffffffffffff}  # ArbOS state account: gas pricing bookkeeping the reference does not model
    for key, val in exp.items():
        if key[0] in SYS: continue
        if w.storage.get(key, 0) != val: smis.append(['%x' % key[0], '%x' % key[1], hex(val), hex(w.storage.get(key, 0))])
    for key, val in w.storage.items():
        if key[0] in SYS: continue
        if key not in exp and prest.get(key, 0) != val: smis.append(['%x' % key[0], '%x' % key[1], 'unchanged', hex(val)])
    pmi = int(pm, 16)
    return {'tx': h, 'block': I(tx['blockNumber']), 'statusChain': I(rec['status']), 'statusRef': int(ok),
            'pmFramesChain': len(chain_pm), 'pmFramesEqual': chain_pm == ref_pm, 'pmChain': chain_pm, 'pmRef': ref_pm,
            'logsChain': len(rl), 'logsRef': len(ol), 'logsEqual': rl == ol, 'logsRefInChainOrder': [x for x in rl if x in ol] == ol,
            'extraChainLogs': [x[0] for x in rl if x not in ol][:6],
            'slotsCompared': len(exp), 'pmSlotsCompared': sum(1 for k in exp if k[0] == pmi), 'storageMismatch': smis[:20], 'steps': w.steps}

if __name__ == '__main__':
    cid = int(sys.argv[1]); url = sys.argv[2]; sc = json.load(open(sys.argv[3])); out = sys.argv[4]
    mx = int(sys.argv[5]) if len(sys.argv) > 5 else 20; lurl = sys.argv[6] if len(sys.argv) > 6 else url
    nets = {n['chainId']: n for n in json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))['networks']}
    pm = nets[cid]['poolManager']
    hits = sc['hits']
    # prefer transactions where an undone unlock is followed by a completed one, then by payments in undone frames
    hits.sort(key=lambda r: (not r['revertedThenCompletedUnlock'], not any(p[1] and p[0] in ('sync', 'settle', 'settleFor', 'take', 'mint', 'burn', 'swap') for p in r['pm'])))
    res = []
    for r in hits[:mx]:
        try: res.append(one(cid, url, pm, r['tx'], lurl))
        except Exception as e: res.append({'tx': r['tx'], 'error': str(e)[:200]})
        x = res[-1]; print(cid, x['tx'][:14], {k: x.get(k) for k in ('statusChain', 'statusRef', 'pmFramesChain', 'pmFramesEqual', 'logsEqual', 'logsRefInChainOrder', 'slotsCompared', 'unsupported', 'error')}, len(x.get('storageMismatch', [])), flush=True)
    json.dump(res, open(out, 'w'), indent=1)
