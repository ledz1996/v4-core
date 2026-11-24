"""Monad (143): per block, the sum of native value that the recorded call frames of every transaction move
into and out of the PoolManager, against the PoolManager balance difference block production wrote
(eth_getBalance at N and N-1). Value in a frame that reverted, or sits under one, does not count.
The PoolManager has no receive or fallback function (src/PoolManager.sol), so native enters only through
payable entry points (settle, settleFor) or through SELFDESTRUCT; both appear as frames here.
Read-only. Usage: python3 monad_blocknative.py <blocks.json> <out.json> [threads]"""
import sys, json, time, itertools, concurrent.futures as cf
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import rpc
PM = '0x188d586ddcf52439676ca21a244753fa19f9ea8e'
URLS = ['https://rpc.monad.xyz', 'https://rpc1.monad.xyz', 'https://rpc-mainnet.monadinfra.com']
STATE = ['https://rpc3.monad.xyz', 'https://rpc1.monad.xyz', 'https://rpc-mainnet.monadinfra.com']
ctr = itertools.count()
SELS = {'0x3dd45adb': 'settleFor', '0x80f0b44c': 'clear', '0xf5298aca': 'burn', '0x156e29f6': 'mint', '0x11da60b4': 'settle', '0x0b0d9c09': 'take', '0x48c89491': 'unlock'}
def call(urls, m, p, timeout=120):
    last = None
    for k in range(10):
        u = urls[next(ctr) % len(urls)]
        try: return rpc(u, m, p, timeout=timeout)
        except Exception as e: last = e; time.sleep(1 + k)
    raise last
def walk(c, ok, acc):
    ok = ok and not c.get('error')
    v = int(c.get('value') or '0x0', 16)
    t = c.get('type')
    if ok and v and t in ('CALL', 'CREATE', 'CREATE2', 'SELFDESTRUCT', 'CALLCODE'):
        if (c.get('from') or '').lower() == PM: acc['out'] += v; acc['frames'] += 1
        if (c.get('to') or '').lower() == PM: acc['in'] += v; acc['frames'] += 1
        if t == 'SELFDESTRUCT' and (c.get('to') or '').lower() == PM: acc['selfdestructIn'] += v
    if t in ('DELEGATECALL', 'CALLCODE') and (c.get('to') or '').lower() == PM: acc['delegateToPm'] += 1
    if t == 'CALL' and (c.get('to') or '').lower() == PM:
        sel = (c.get('input') or '')[:10]
        if sel in SELS: acc['ops'][SELS[sel] + ('.undone' if not ok else '')] = acc['ops'].get(SELS[sel] + ('.undone' if not ok else ''), 0) + 1
    for k in c.get('calls') or []: walk(k, ok, acc)
def one(b):
    tr = call(URLS, 'debug_traceBlockByNumber', [hex(b), {'tracer': 'callTracer'}])
    acc = {'in': 0, 'out': 0, 'frames': 0, 'selfdestructIn': 0, 'delegateToPm': 0, 'ops': {}}; txs = 0
    for t in tr:
        res = t.get('result', t)
        walk(res, True, acc); txs += 1
    bd = int(call(STATE, 'eth_getBalance', [PM, hex(b)]), 16) - int(call(STATE, 'eth_getBalance', [PM, hex(b - 1)]), 16)
    blk = call(STATE, 'eth_getBlockByNumber', [hex(b), False])
    w = [x for x in (blk.get('withdrawals') or []) if (x.get('address') or '').lower() == PM]
    return {'block': b, 'txs': txs, 'in': str(acc['in']), 'out': str(acc['out']), 'frames': acc['frames'], 'selfdestructIn': str(acc['selfdestructIn']),
            'delegateToPm': acc['delegateToPm'], 'ops': acc['ops'], 'balanceDiff': str(bd), 'withdrawalsToPm': len(w), 'coinbaseIsPm': (blk.get('miner') or '').lower() == PM,
            'diff': str(bd - (acc['in'] - acc['out'])), 'txCountHeader': len(blk['transactions'])}
if __name__ == '__main__':
    blocks = json.load(open(sys.argv[1])); out = sys.argv[2]; th = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    def safe(b):
        try: return one(b)
        except Exception as e: return {'block': b, 'error': str(e)[:200]}
    with cf.ThreadPoolExecutor(th) as ex: res = list(ex.map(safe, blocks))
    ok = [r for r in res if 'diff' in r]
    summ = {'blocks': len(res), 'errors': len(res) - len(ok), 'reconciled': sum(1 for r in ok if r['diff'] == '0'),
            'notReconciled': [r for r in ok if r['diff'] != '0'][:50], 'withNativeFlow': sum(1 for r in ok if r['frames']),
            'traceTxCountMismatch': sum(1 for r in ok if r['txs'] != r['txCountHeader'])}
    tot = {}
    for r in ok:
        for k, v in r['ops'].items(): tot[k] = tot.get(k, 0) + v
    summ['opsInBlocks'] = tot; summ['blocksWithClearOrSettleFor'] = [r['block'] for r in ok if any(k.startswith(('clear', 'settleFor')) for k in r['ops'])]
    json.dump({'summary': summ, 'results': res}, open(out, 'w'), indent=1)
    print(json.dumps(summ, indent=1)[:3000])
