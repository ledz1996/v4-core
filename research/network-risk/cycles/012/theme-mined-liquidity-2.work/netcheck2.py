"""Monad (143): do the credits and debits that block execution recorded inside each completed unlock
net to zero? Read-only.

For every PoolManager.unlock frame in the recorded call frames (debug_traceTransaction, callTracer)
that succeeded and was not undone by a reverted ancestor, the PoolManager frames under it are
summed per (account, currency) as src/ accounts them:
  swap            +amount0 / +amount1 of the returned BalanceDelta to msg.sender (src/PoolManager.sol:227)
  modifyLiquidity +callerDelta (first returned word) to msg.sender (src/PoolManager.sol:184)
  donate          +returned delta to msg.sender (src/PoolManager.sol:269)
  settle          +returned paid to msg.sender; settleFor(r) to r (src/PoolManager.sol:300-308, 363)
  take            -amount to msg.sender (src/PoolManager.sol:294)
  mint            -amount of currency id to msg.sender; burn +amount; clear -amount (src/PoolManager.sol:310-336)
Cycle 12 extension: pools whose key names a hook are kept. The hook's delta is credited to the hook
address as src/ does (src/PoolManager.sol:178-183, 221-226): for swap it is the pool delta of the Swap event
the frame emitted minus the caller delta the frame returned (src/libraries/Hooks.sol:285-315); for
modifyLiquidity it is the BalanceDelta that the afterAddLiquidity or afterRemoveLiquidity frame returned when
the hook address carries the return-delta flag (src/libraries/Hooks.sol:159-168, 215-244), else zero. unlock completes
only when every delta is zero (src/PoolManager.sol:112), so for the unlocks kept every sum must be
zero. A compiled fault that credited a payer more than the balance rose, or debited a take less
than it paid out, would leave a nonzero sum in an unlock that completed.

Usage: python3 netcheck2.py <select.json with {'txs': [...]}> <out.json> [limit] [threads]
"""
import sys, os, json, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/011/theme-monad-settlement-path.work')
from rpcq import rpc

PM = '0x188d586ddcf52439676ca21a244753fa19f9ea8e'
TR = {'tracer': 'callTracer', 'tracerConfig': {'withLog': True}}
SWAPT = '0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f'
S = {'0x48c89491': 'unlock', '0xf3cd914c': 'swap', '0x5a6bcfda': 'modifyLiquidity', '0x234266d7': 'donate', '0xa5841194': 'sync',
     '0x11da60b4': 'settle', '0x3dd45adb': 'settleFor', '0x0b0d9c09': 'take', '0x156e29f6': 'mint', '0xf5298aca': 'burn', '0x80f0b44c': 'clear',
     '0x1e2eaeaf': 'extsload', '0xf135baaa': 'exttload', '0x35fd631a': 'extsloadN', '0xdbd035ff': 'extsloadA', '0x9bf6645f': 'exttloadA',
     '0x6276cbbe': 'initialize', '0x095bcdb6': 'transfer', '0xfe99049a': 'transferFrom', '0x426a8493': 'approve', '0x558a7297': 'setOperator'}
M128 = (1 << 128) - 1
stats = {'unlocks': 0, 'hookedOps': 0, 'hookDeltaOps': 0}
OPS = {}


def s128(x): x &= M128; return x - (1 << 128) if x >> 127 else x
def w(h, i): h = h[2:] if h.startswith('0x') else h; return int(h[64 * i:64 * (i + 1)] or '0', 16)
def a(h, i): return '0x' + ('%064x' % w(h, i))[24:]


def pm_nodes(n, undone, out):
    err = 'error' in n; u = undone or err
    if (n.get('to') or '').lower() == PM and n.get('type') == 'CALL':
        out.append((n, u))
    for c in n.get('calls', []) or []: pm_nodes(c, u, out)
    return out


def check_unlock(un):
    """Returns ('skip', why) or ('ok', nOps) or ('bad', sums)."""
    sums = {}; ops = 0; stats['unlocks'] += 1
    def add(acct, cur, v):
        if v: sums[(acct, cur)] = sums.get((acct, cur), 0) + v
    for n, u in pm_nodes(un, False, [])[1:]:
        if u: continue  # a frame that reverted, or sits under one, leaves no delta
        inp = (n.get('input') or '0x').lower(); k = S.get(inp[:10]); body = inp[10:]; out = n.get('output') or '0x'
        snd = (n.get('from') or '').lower()
        if k is None: return ('skip', 'unknown selector ' + inp[:10])
        if k == 'unlock': return ('skip', 'nested unlock')
        if k in ('swap', 'modifyLiquidity', 'donate'):
            c0, c1, hooks = a(body, 0), a(body, 1), a(body, 4)
            d = w(out, 0); add(snd, c0, s128(d >> 128)); add(snd, c1, s128(d)); ops += 1
            hk = int(hooks, 16)
            if hk:
                stats['hookedOps'] += 1
                if k == 'swap':
                    lg = [l for l in n.get('logs') or [] if (l.get('topics') or [''])[0].lower() == SWAPT]
                    if len(lg) != 1: return ('skip', 'hooked swap without one Swap log')
                    e0, e1 = s128(w(lg[0]['data'], 0)), s128(w(lg[0]['data'], 1))
                    h0, h1 = e0 - s128(d >> 128), e1 - s128(d)
                    if h0 or h1: stats['hookDeltaOps'] += 1
                    if not os.environ.get('PLANT'): add(hooks, c0, h0); add(hooks, c1, h1)
                elif k == 'modifyLiquidity':
                    liq = w(body, 7); liq = liq - (1 << 256) if liq >> 255 else liq
                    sel, bit = ('0x9f063efc', 2) if liq > 0 else ('0x6c2bbe7e', 1)
                    if hk & bit and snd != hooks:
                        ch = [c for c in n.get('calls') or [] if (c.get('to') or '').lower() == hooks and (c.get('input') or '').lower().startswith(sel)]
                        if len(ch) != 1 or ch[0].get('error'): return ('skip', 'hooked modify without one after-hook frame')
                        hd = w(ch[0].get('output') or '0x', 1)
                        h0, h1 = s128(hd >> 128), s128(hd)
                        if h0 or h1: stats['hookDeltaOps'] += 1
                        if not os.environ.get('PLANT'): add(hooks, c0, h0); add(hooks, c1, h1)
        if k in ('settleFor', 'clear', 'burn', 'mint'): OPS[k] = OPS.get(k, 0) + 1
        if k == 'settle': add(snd, n.get('_cur'), w(out, 0)); ops += 1
        elif k == 'settleFor': add(a(body, 0), n.get('_cur'), w(out, 0)); ops += 1
        elif k == 'take': add(snd, a(body, 0), -w(body, 2)); ops += 1
        elif k == 'mint': add(snd, '0x' + ('%064x' % w(body, 1))[24:], -w(body, 2)); ops += 1
        elif k == 'burn': add(snd, '0x' + ('%064x' % w(body, 1))[24:], w(body, 2)); ops += 1
        elif k == 'clear': add(snd, a(body, 0), -w(body, 1)); ops += 1
    nz = {f'{k[0]}:{k[1]}': v for k, v in sums.items() if v}
    return ('bad', nz) if nz else ('ok', ops)


def mark_currency(n, st, undone=False):
    """Annotate each settle/settleFor frame with the currency synced at that moment, rolling the synced
    currency back over reverted frames (transient storage), as CurrencyReserves keeps it."""
    snap = dict(st); err = 'error' in n
    if (n.get('to') or '').lower() == PM and n.get('type') == 'CALL':
        inp = (n.get('input') or '0x').lower(); k = S.get(inp[:10])
        if k == 'sync' and not err: st['cur'] = a(inp[10:], 0)
        if k in ('settle', 'settleFor'):
            n['_cur'] = st['cur']
            if not err: st['cur'] = '0x' + '0' * 40
    for c in n.get('calls', []) or []: mark_currency(c, st)
    if err: st.clear(); st.update(snap)


def one(h):
    try: t = rpc('debug_traceTransaction', [h, TR])
    except Exception as e: return h, None, str(e)[:200]
    mark_currency(t, {'cur': '0x' + '0' * 40})
    res = []
    for n, u in pm_nodes(t, False, []):
        if S.get((n.get('input') or '')[:10]) != 'unlock' or u: continue
        res.append(check_unlock(n))
    return h, res, None


def main():
    scan = json.load(open(sys.argv[1])); out = sys.argv[2]
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10 ** 9; th = int(sys.argv[4]) if len(sys.argv) > 4 else 12
    sel = scan['txs'][:limit]
    cnt = {'transactions': len(sel), 'errors': 0, 'completedUnlocks': 0, 'checked': 0, 'netZero': 0, 'notZero': 0, 'opsSummed': 0, 'skipped': {}}
    bad = []
    with cf.ThreadPoolExecutor(th) as ex:
        for i, (h, res, e) in enumerate(ex.map(one, sel)):
            if res is None: cnt['errors'] += 1; continue
            for kind, v in res:
                cnt['completedUnlocks'] += 1
                if kind == 'skip': cnt['skipped'][v.split(' 0x')[0]] = cnt['skipped'].get(v.split(' 0x')[0], 0) + 1; continue
                cnt['checked'] += 1
                if kind == 'ok': cnt['netZero'] += 1; cnt['opsSummed'] += v
                else: cnt['notZero'] += 1; bad.append({'tx': h, 'sums': v})
            if i % 1000 == 0: print(i, cnt['netZero'], cnt['notZero'], flush=True)
    cnt['firstNotZero'] = bad[:30]; cnt.update(stats); cnt['opsSeen'] = OPS
    json.dump(cnt, open(out, 'w'), indent=1); print(json.dumps(cnt, indent=1)[:3000])


main()
