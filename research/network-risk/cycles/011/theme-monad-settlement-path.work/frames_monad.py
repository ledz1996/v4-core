"""Monad (143): compiled block execution against interpreter re-execution, for mined PoolManager
transactions. Read-only.

On Monad, debug_traceTransaction with callTracer returns the call frames that block execution
recorded and committed to the database (monad-bft monad-rpc/src/handlers/debug.rs,
monad_debug_traceTransaction -> get_transaction_call_frame; only prestateTracer replays), and
debug_traceCall / eth_call run in an executor whose VM is InterpreterOnly
(category/rpc/monad_executor.cpp:1297-1300 at v0.16.5). Block execution runs the PoolManager as
compiled code once it is hot (category/vm/vm.cpp:142-190).

Every Monad block starts with a system transaction to the staking precompile 0x...1000 at index
0, so the first user transaction sits at index 1 and runs on the parent state plus that system
call. For each PoolManager transaction at index 1 whose block's index 0 is that system call, this
script reads
  A. the recorded frames (debug_traceTransaction, callTracer, withLog) and the receipt, and
  B. the same transaction re-executed by the interpreter at the parent block
     (debug_traceCall with from, to, input, value, gas, access list and authorization list of the
     transaction, callTracer, withLog),
and compares every frame of A and B: type, from, to, value, input, output, error and logs, and
the receipt's status and logs with B's surviving logs. Gas fields are compared separately.
It also classifies the PoolManager calls in each tree (sync, settle, settleFor, take, mint, burn,
clear, unlock) and finds trees in which a reverted frame entered unlock and a later unlock
completed.

Usage: python3 -I frames_monad.py <scan.json> <out.json> [limit] [threads]
"""
import sys, os, json, time, concurrent.futures as cf, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools', 'opdiff'))
from rpcq import rpc
from evm import keccak

PM = '0x188d586ddcf52439676ca21a244753fa19f9ea8e'
STAKING = '0x0000000000000000000000000000000000001000'
SEL = {'0x' + keccak(x.encode())[:4].hex(): x.split('(')[0] for x in [
    'unlock(bytes)', 'swap((address,address,uint24,int24,address),(bool,int256,uint160),bytes)',
    'modifyLiquidity((address,address,uint24,int24,address),(int24,int24,int256,bytes32),bytes)',
    'settle()', 'settleFor(address)', 'take(address,address,uint256)', 'sync(address)', 'mint(address,uint256,uint256)',
    'burn(address,uint256,uint256)', 'donate((address,address,uint24,int24,address),uint256,uint256,bytes)',
    'initialize((address,address,uint24,int24,address),uint160)', 'clear(address,uint256)',
    'extsload(bytes32)', 'exttload(bytes32)', 'extsload(bytes32[])', 'exttload(bytes32[])', 'extsload(bytes32,uint256)',
    'transfer(address,address,uint256,uint256)', 'transferFrom(address,address,uint256,uint256)']}
SETTLE = {'sync', 'settle', 'settleFor', 'take', 'mint', 'burn', 'clear'}
TR = {'tracer': 'callTracer', 'tracerConfig': {'withLog': True}}


def norm_logs(node):
    return [((l.get('address') or '').lower(), tuple(t.lower() for t in l.get('topics', [])), (l.get('data') or '0x').lower()) for l in node.get('logs', []) or []]


def flat(node, out, path='r', undone=False):
    err = 'error' in node
    und = undone or err
    out.append({'path': path, 'type': node.get('type'), 'from': (node.get('from') or '').lower(), 'to': (node.get('to') or '').lower(),
                'value': node.get('value') or '0x0', 'input': (node.get('input') or '0x').lower(), 'output': (node.get('output') or '0x').lower(),
                'error': node.get('error'), 'logs': norm_logs(node), 'gas': node.get('gas'), 'gasUsed': node.get('gasUsed'), 'undone': und})
    for i, c in enumerate(node.get('calls', []) or []):
        flat(c, out, f'{path}.{i}', und)
    return out


def pos(l):
    p = l.get('position', 0)
    return int(p, 16) if isinstance(p, str) else int(p)


def surviving_logs(node, undone=False):
    """Logs of frames that did not revert, in emit order (callTracer 'position' orders logs among child calls)."""
    if undone or 'error' in node: return []
    logs = list(node.get('logs', []) or []); calls = node.get('calls', []) or []
    # a log with position p was emitted after the first p child calls
    out = []; li = 0
    logs_sorted = sorted(enumerate(logs), key=lambda x: (pos(x[1]), x[0]))
    for k in range(len(calls) + 1):
        while li < len(logs_sorted) and pos(logs_sorted[li][1]) <= k:
            l = logs_sorted[li][1]; out.append(((l.get('address') or '').lower(), tuple(t.lower() for t in l.get('topics', [])), (l.get('data') or '0x').lower())); li += 1
        if k < len(calls): out.extend(surviving_logs(calls[k]))
    return out


def events(node, owner, out):
    """Execution order: the caller enters the call, the callee's logs and child calls interleave by
    position, the callee exits. Each event names the contract whose code produced it."""
    me = (node.get('to') or '').lower()
    out.append(('enter', owner, node.get('type'), (node.get('from') or '').lower(), me, node.get('value') or '0x0', (node.get('input') or '0x').lower()))
    logs = sorted(enumerate(node.get('logs', []) or []), key=lambda x: (pos(x[1]), x[0])); calls = node.get('calls', []) or []; li = 0
    for k in range(len(calls) + 1):
        while li < len(logs) and pos(logs[li][1]) <= k:
            l = logs[li][1]; out.append(('log', me, (l.get('address') or '').lower(), tuple(t.lower() for t in l.get('topics', [])), (l.get('data') or '0x').lower())); li += 1
        if k < len(calls): events(calls[k], me, out)
    out.append(('exit', me, (node.get('output') or '0x').lower(), node.get('error')))
    return out


def divergence(rec, rep):
    a = events(rec, 'eoa', []); b = events(rep, 'eoa', [])
    pm_exits = 0
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return {'index': i, 'events': len(a), 'kind': x[0], 'owner': x[1], 'ownerIsPoolManager': x[1] == PM,
                    'pmExitsEqualBefore': pm_exits, 'rec': str(x)[:300], 'rep': str(y)[:300]}
        if x[0] == 'exit' and x[1] == PM: pm_exits += 1
    if len(a) != len(b): return {'index': min(len(a), len(b)), 'events': len(a), 'kind': 'length', 'owner': None, 'ownerIsPoolManager': False, 'pmExitsEqualBefore': pm_exits}
    return None


def classify(frames):
    pm = [f for f in frames if f['to'] == PM]
    kinds = {}
    for f in pm:
        s = SEL.get(f['input'][:10], f['input'][:10])
        kinds[s] = kinds.get(s, 0) + 1
    unl = [f for f in pm if SEL.get(f['input'][:10]) == 'unlock']
    rev_unlock = [f for f in unl if f['undone']]
    done_after = any(not f['undone'] for f in unl[unl.index(rev_unlock[0]) + 1:]) if rev_unlock else False
    settle_in_reverted = any(f['undone'] and SEL.get(f['input'][:10]) in SETTLE for f in pm)
    return kinds, bool(rev_unlock), done_after, settle_in_reverted


def one(t):
    h, b = t['tx'], t['b']
    try:
        tx0 = rpc('eth_getTransactionByBlockNumberAndIndex', [hex(b), '0x0'])
        if (tx0.get('to') or '').lower() != STAKING:
            return {'tx': h, 'skip': 'index 0 is not the staking system call', 'tx0to': tx0.get('to')}
        tx = rpc('eth_getTransactionByHash', [h])
        rec = rpc('debug_traceTransaction', [h, TR])
        rcpt = rpc('eth_getTransactionReceipt', [h])
        call = {'from': tx['from'], 'to': tx['to'], 'data': tx['input'], 'value': tx['value'], 'gas': tx['gas']}
        if tx.get('accessList'): call['accessList'] = tx['accessList']
        if tx.get('authorizationList'): call['authorizationList'] = tx['authorizationList']
        rep = rpc('debug_traceCall', [call, hex(b - 1), TR])
    except Exception as e:
        return {'tx': h, 'err': str(e)[:200]}
    A = flat(rec, []); B = flat(rep, [])
    diffs = []; gasd = 0
    if len(A) != len(B): diffs.append({'what': 'frame count', 'rec': len(A), 'rep': len(B)})
    for fa, fb in zip(A, B):
        for k in ('type', 'from', 'to', 'value', 'input', 'output', 'error', 'logs'):
            if fa[k] != fb[k]:
                diffs.append({'path': fa['path'], 'field': k, 'rec': str(fa[k])[:200], 'rep': str(fb[k])[:200]})
        if fa['gasUsed'] != fb['gasUsed']: gasd += 1
    rstatus = int(rcpt['status'], 16)
    rlogs = [((l['address']).lower(), tuple(x.lower() for x in l['topics']), l['data'].lower()) for l in rcpt['logs']]
    rep_ok = 'error' not in rep
    if rstatus != int(rep_ok): diffs.append({'what': 'receipt status vs replay', 'rec': rstatus, 'rep': int(rep_ok)})
    if rlogs != surviving_logs(rep): diffs.append({'what': 'receipt logs vs replay surviving logs', 'rec': len(rlogs), 'rep': len(surviving_logs(rep))})
    if rlogs != surviving_logs(rec): diffs.append({'what': 'receipt logs vs recorded surviving logs', 'rec': len(rlogs), 'rec2': len(surviving_logs(rec))})
    kinds, rev_unlock, done_after, settle_rev = classify(A)
    dv = divergence(rec, rep)
    pm_exits_total = sum(1 for e in events(rec, 'eoa', []) if e[0] == 'exit' and e[1] == PM)
    if dv and dv['ownerIsPoolManager']:
        os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'raw'), exist_ok=True)
        json.dump({'rec': rec, 'rep': rep, 'receipt': rcpt}, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'raw', h + '.json'), 'w'))
    pm_frames = sum(1 for f in A if f['to'] == PM)
    return {'tx': h, 'b': b, 'status': rstatus, 'frames': len(A), 'pmFrames': pm_frames, 'kinds': kinds, 'revertedUnlock': rev_unlock,
            'completedUnlockAfterRevert': done_after, 'settleInRevertedFrame': settle_rev, 'diffs': diffs[:20], 'nDiffs': len(diffs),
            'gasUsedDiffFrames': gasd, 'divergence': dv, 'pmExits': pm_exits_total, 'pmFramesWithError': sum(1 for f in A if f['to'] == PM and f['error'])}


def main():
    scan = json.load(open(sys.argv[1])); out = sys.argv[2]
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10 ** 9; th = int(sys.argv[4]) if len(sys.argv) > 4 else 6
    txs = {}
    for l in scan['logs']: txs.setdefault(l['tx'], l)
    sel = sorted((t for t in txs.values() if t['i'] == 1), key=lambda t: -t['b'])[:limit]
    print('index-1 PoolManager transactions', len(sel), flush=True)
    res = []
    with cf.ThreadPoolExecutor(th) as ex:
        for i, r in enumerate(ex.map(one, sel)):
            res.append(r)
            if i % 200 == 0: print(i, flush=True)
    ok = [r for r in res if 'diffs' in r]
    summ = {'selected': len(sel), 'compared': len(ok), 'errors': sum(1 for r in res if 'err' in r), 'skipped': sum(1 for r in res if 'skip' in r),
            'withDifference': sum(1 for r in ok if r['nDiffs']), 'framesCompared': sum(r['frames'] for r in ok),
            'pmFramesCompared': sum(r['pmFrames'] for r in ok), 'receiptStatusFailed': sum(1 for r in ok if r['status'] == 0),
            'withGasUsedDifference': sum(1 for r in ok if r['gasUsedDiffFrames']),
            'byKind': {}, 'txsWithKind': {}, 'revertedUnlock': sum(1 for r in ok if r['revertedUnlock']),
            'revertedUnlockThenCompletedUnlock': sum(1 for r in ok if r['completedUnlockAfterRevert']),
            'settlementCallInRevertedFrame': sum(1 for r in ok if r['settleInRevertedFrame']),
            'txsWithFailedPoolManagerFrame': sum(1 for r in ok if r['pmFramesWithError']),
            'identicalEventSequence': sum(1 for r in ok if not r['divergence']),
            'divergenceOwnedByPoolManager': sum(1 for r in ok if r['divergence'] and r['divergence']['ownerIsPoolManager']),
            'divergenceOwnedByOther': sum(1 for r in ok if r['divergence'] and not r['divergence']['ownerIsPoolManager']),
            'poolManagerExitsCompared': sum(r['pmExits'] for r in ok if not r['divergence']) + sum(r['divergence']['pmExitsEqualBefore'] for r in ok if r['divergence']),
            'divergenceOwners': {}}
    for r in ok:
        if r['divergence']:
            o = str(r['divergence']['owner']); summ['divergenceOwners'][o] = summ['divergenceOwners'].get(o, 0) + 1
    for r in ok:
        for k, v in r['kinds'].items():
            summ['byKind'][k] = summ['byKind'].get(k, 0) + v; summ['txsWithKind'][k] = summ['txsWithKind'].get(k, 0) + 1
    summ['blocks'] = [min(r['b'] for r in ok), max(r['b'] for r in ok)] if ok else None
    json.dump({'summary': summ, 'results': res}, open(out, 'w'), indent=1)
    print(json.dumps(summ, indent=1))


main()
