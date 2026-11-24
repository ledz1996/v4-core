"""Cycle 11, theme-closed-producers. Extends cycles/010/theme-megaeth-executor.work/frames.py.
Read only. For PoolManager transactions mined on a network whose block producer is not the code
that answers RPC, compare what the producer wrote (receipt status and logs, and the committed
storage the endpoint serves at the block) with a second execution by debug_traceTransaction.

Per transaction
  - callTracer (withLog): every PoolManager frame, whether a frame at or above it reverted,
    whether a later unlock completed after an undone one, and which selectors ran undone
  - receipt status and logs against the status and the surviving logs of the trace
  - kind of liquidity change from the receipt: ModifyLiquidity with negative delta (removal),
    zero delta (fee collection), positive delta (addition)
  - for removals, fee collections and undone payments (sync, settle, settleFor, take, mint, burn,
    clear): prestateTracer diffMode, and for each PoolManager slot it changed, the post value
    against eth_getStorageAt at the block when this is the last PoolManager transaction of the
    block, and the pre value against eth_getStorageAt at block-1 when it is the first.

Usage: python3 frames2.py <cfg.json> <out.json>
cfg: {"chain":..,"logsUrl":..,"traceUrl":..,"receiptUrl":..,"stateUrl":..,"pm":..,
      "ranges":[[lo,hi],..],"topics":null|[..],"maxTx":N,"threads":N}
"""
import sys, os, json, time, concurrent.futures as cf
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/010/theme-megaeth-executor.work')
from evm import rpc, keccak
import frames as F  # walk, surviving_logs, SEL

MODIFY = '0x' + keccak(b'ModifyLiquidity(bytes32,address,int24,int24,int256,bytes32)').hex()
PAY = {'sync', 'settle', 'settleFor', 'take', 'mint', 'burn', 'clear'}


def R(url, m, p, timeout=90, tries=6):
    last = None
    for k in range(tries):
        try:
            return rpc(url, m, p, timeout=timeout)
        except Exception as e:  # noqa
            last = e
            s = str(e)
            if 'not found' in s.lower() and k >= 1: break
            time.sleep(1.5 * (k + 1))
    raise last


def logs_range(url, pm, lo, hi, topics):
    out = []; span = 2000; a = lo
    while a <= hi:
        b = min(hi, a + span - 1)
        f = {'address': pm, 'fromBlock': hex(a), 'toBlock': hex(b)}
        if topics: f['topics'] = [topics]
        try:
            out += R(url, 'eth_getLogs', [f], tries=3); a = b + 1
            if span < 20000: span *= 2
        except Exception:
            if span <= 10: raise
            span //= 4
    return out


def sgn256(h):
    v = int(h, 16)
    return v - (1 << 256) if v >> 255 else v


def one(cfg, h, blockinfo):
    pm = cfg['pm'].lower()
    t = R(cfg['traceUrl'], 'debug_traceTransaction', [h, {'tracer': 'callTracer', 'tracerConfig': {'withLog': True}}])
    acc = []; F.PM = pm; F.walk(t, [], False, acc)
    rec = R(cfg['receiptUrl'], 'eth_getTransactionReceipt', [h])
    rlogs = [(l['address'].lower(), tuple(x.lower() for x in l['topics']), l['data'].lower()) for l in rec['logs']]
    tl = []; F.surviving_logs(t, False, tl)
    st = 0 if 'error' in t else 1
    res = {'tx': h, 'block': int(rec['blockNumber'], 16), 'statusReceipt': int(rec['status'], 16), 'statusTrace': st,
           'logsReceipt': len(rlogs), 'logsTrace': len(tl), 'logsEqual': rlogs == tl,
           'logsEqualAsMultiset': sorted(rlogs) == sorted(tl), 'pmFrames': len(acc),
           'sels': sorted({a['sel'] for a in acc})}
    undone = [a for a in acc if a['undone']]
    res['undoneSels'] = sorted({a['sel'] for a in undone})
    unl = [a for a in acc if a['sel'] == 'unlock']
    res['revertedThenCompletedUnlock'] = any(a['undone'] and any(not b['undone'] for b in unl[i + 1:]) for i, a in enumerate(unl))
    res['undonePay'] = sorted(set(res['undoneSels']) & PAY)
    kinds = set()
    for (addr, tp, data) in rlogs:
        if addr == pm and tp and tp[0] == MODIFY:
            d = sgn256(data[2 + 128:2 + 192])
            kinds.add('removal' if d < 0 else 'feeCollect' if d == 0 else 'addition')
    res['kinds'] = sorted(kinds)
    if cfg.get('stateUrl') and (kinds & {'removal', 'feeCollect'} or res['undonePay']):
        try:
            d = R(cfg['traceUrl'], 'debug_traceTransaction', [h, {'tracer': 'prestateTracer', 'tracerConfig': {'diffMode': True}}])
            pre = {k.lower(): v for k, v in d.get('pre', {}).items()}.get(pm, {}).get('storage', {}) or {}
            post = {k.lower(): v for k, v in d.get('post', {}).items()}.get(pm, {}).get('storage', {}) or {}
            slots = sorted(set(pre) | set(post))
            first, last = blockinfo.get(h, (False, False))
            cmp = {'slots': len(slots), 'first': first, 'last': last, 'postChecked': 0, 'postMismatch': [], 'preChecked': 0, 'preMismatch': []}
            for sl in slots:
                pv = int(post.get(sl, '0x0'), 16) if sl in post else 0
                if last:
                    got = int(R(cfg['stateUrl'], 'eth_getStorageAt', [pm, sl, hex(res['block'])]), 16); cmp['postChecked'] += 1
                    if got != pv: cmp['postMismatch'].append([sl, hex(pv), hex(got)])
                if first and sl in pre:
                    got = int(R(cfg['stateUrl'], 'eth_getStorageAt', [pm, sl, hex(res['block'] - 1)]), 16); cmp['preChecked'] += 1
                    if got != int(pre[sl], 16): cmp['preMismatch'].append([sl, pre[sl], hex(got)])
            res['state'] = cmp
        except Exception as e:  # noqa
            res['stateError'] = str(e)[:160]
    return res


def main():
    cfg = json.load(open(sys.argv[1])); out = sys.argv[2]
    logs = []
    for lo, hi in cfg['ranges']:
        logs += logs_range(cfg['logsUrl'], cfg['pm'], lo, hi, cfg.get('topics'))
        print('logs', lo, hi, len(logs), flush=True)
    logs.sort(key=lambda x: (int(x['blockNumber'], 16), int(x['transactionIndex'], 16), int(x['logIndex'], 16)))
    hs = list(dict.fromkeys(l['transactionHash'] for l in logs))
    if cfg.get('maxTx') and len(hs) > cfg['maxTx']:
        hs = hs[-cfg['maxTx']:]
    byblock = {}
    for l in logs:
        byblock.setdefault(int(l['blockNumber'], 16), [])
        if l['transactionHash'] not in byblock[int(l['blockNumber'], 16)]: byblock[int(l['blockNumber'], 16)].append(l['transactionHash'])
    binfo = {}
    for b, txs in byblock.items():
        for i, h in enumerate(txs): binfo[h] = (i == 0, i == len(txs) - 1)
    print('txs', len(hs), flush=True)

    def w(h):
        try: return one(cfg, h, binfo)
        except Exception as e: return {'tx': h, 'error': str(e)[:160]}  # noqa
    with cf.ThreadPoolExecutor(cfg.get('threads', 6)) as ex:
        res = list(ex.map(w, hs))
    ok = [r for r in res if 'error' not in r]
    st = [r['state'] for r in ok if 'state' in r]
    summ = {'chain': cfg['chain'], 'ranges': cfg['ranges'], 'traced': len(ok), 'errors': len(res) - len(ok),
            'statusMismatch': sum(r['statusReceipt'] != r['statusTrace'] for r in ok),
            'logsMismatch': sum(not r['logsEqual'] for r in ok), 'logsMismatchMultiset': sum(not r['logsEqualAsMultiset'] for r in ok),
            'withUndonePmFrame': sum(bool(r['undoneSels']) for r in ok),
            'revertedThenCompletedUnlock': sum(r['revertedThenCompletedUnlock'] for r in ok),
            'undonePayTx': sum(bool(r['undonePay']) for r in ok),
            'removal': sum('removal' in r['kinds'] for r in ok), 'feeCollect': sum('feeCollect' in r['kinds'] for r in ok),
            'addition': sum('addition' in r['kinds'] for r in ok),
            'syncOrSettleTx': sum(bool({'sync', 'settle', 'settleFor'} & set(r['sels'])) for r in ok),
            'stateCompared': len(st), 'stateErrors': sum('stateError' in r for r in ok),
            'postSlotsChecked': sum(s['postChecked'] for s in st), 'postMismatch': sum(len(s['postMismatch']) for s in st),
            'preSlotsChecked': sum(s['preChecked'] for s in st), 'preMismatch': sum(len(s['preMismatch']) for s in st)}
    us, ups = {}, {}
    for r in ok:
        for x in r['undoneSels']: us[x] = us.get(x, 0) + 1
        for x in r['undonePay']: ups[x] = ups.get(x, 0) + 1
    summ['undoneSelectors'] = us; summ['undonePaySelectors'] = ups
    interesting = [r for r in ok if r['undoneSels'] or not r['logsEqual'] or r['statusReceipt'] != r['statusTrace']
                   or ('state' in r and (r['state']['postMismatch'] or r['state']['preMismatch']))]
    json.dump({'summary': summ, 'interesting': interesting[:600], 'stateSamples': [r for r in ok if 'state' in r][:300],
               'errors': [r for r in res if 'error' in r][:40]}, open(out, 'w'), indent=1)
    print(json.dumps(summ, indent=1))


if __name__ == '__main__':
    main()
