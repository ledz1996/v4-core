"""Rerun one mined transaction in pyevm2 from the state before it, and compare with what the
block recorded. Read only: debug_traceTransaction (prestateTracer, diffMode, callTracer),
eth_getTransactionByHash, eth_getTransactionReceipt, eth_getBlockByNumber, eth_getStorageAt,
eth_getCode, eth_getBalance.

Compared
  status   receipt status against the rerun's top frame
  logs     receipt logs (written by block production) against the rerun's surviving logs, in order
  frames   every call into the PoolManager in the callTracer tree, in pre-order, against the rerun's:
           input, success and return data
  storage  every PoolManager slot the rerun changed against the diffMode post state, and, when the
           caller says the transaction is the last PoolManager transaction of its block, against
           eth_getStorageAt at the block (state committed by block production)
  branches the (pc, side) pairs of PoolManager JUMPIs the rerun took
"""
import sys, json
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/013/theme-mined-branches.work')
from common import *
import pyevm2
from pyevm2 import World
from families import families
EMPTY = int.from_bytes(keccak(b''), 'big')

class Base:
    def __init__(self, urls, pre, block):
        self.urls = urls; self.block = hex(block - 1); self.misses = []
        self.pre = {int(a, 16): v for a, v in pre.items()}
        self.st = {}
        for a, v in self.pre.items():
            for k, x in (v.get('storage') or {}).items(): self.st[(a, int(k, 16))] = int(x, 16)
    def storage(self, a, k):
        if (a, k) in self.st: return self.st[(a, k)]
        v = int(rpc(self.urls, 'eth_getStorageAt', ['0x%040x' % a, '0x%064x' % k, self.block]), 16)
        self.misses.append(('slot', '0x%040x' % a, hex(k))); self.st[(a, k)] = v; return v
    def code(self, a):
        if a in self.pre and 'code' in self.pre[a]: return bytes.fromhex(self.pre[a]['code'][2:])
        if a in self.pre: return b''
        if 0 < a < 0x12 or a in (0x100, 0x1000): return b''
        c = rpc(self.urls, 'eth_getCode', ['0x%040x' % a, self.block])
        self.misses.append(('code', '0x%040x' % a)); return bytes.fromhex(c[2:])
    def balance(self, a):
        if a in self.pre: return int(self.pre[a].get('balance', '0x0'), 16)
        v = int(rpc(self.urls, 'eth_getBalance', ['0x%040x' % a, self.block]), 16)
        self.misses.append(('balance', '0x%040x' % a)); self.pre[a] = {'balance': hex(v)}; return v
    def exthash_empty(self, a):
        if a in self.pre:
            v = self.pre[a]
            if int(v.get('balance', '0x0'), 16) or int(str(v.get('nonce', 0)), 0): return EMPTY
            return 0
        n = int(rpc(self.urls, 'eth_getTransactionCount', ['0x%040x' % a, self.block]), 16)
        return EMPTY if (n or self.balance(a)) else 0

def tree_pm(node, pm, out):
    if (node.get('to') or '').lower() == pm and node.get('type') in ('CALL', 'STATICCALL'):
        out.append({'input': node.get('input', '0x').lower(), 'ok': 'error' not in node, 'ret': (node.get('output') or '0x').lower(),
                    'err': node.get('error'), 'value': int(node.get('value', '0x0') or '0x0', 16)})
    for c in node.get('calls', []) or []: tree_pm(c, pm, out)

def rerun(cid, h, last_in_block=False, trace_urls=None, state_urls=None, keep=False):
    tu = trace_urls or TRACE[cid]; su = state_urls or STATE[cid]
    pm = NETS[cid]['poolManager'].lower(); pmi = int(pm, 16)
    tx = rpc(su, 'eth_getTransactionByHash', [h]); rc = rpc(su, 'eth_getTransactionReceipt', [h])
    bn = int(rc['blockNumber'], 16); blk = rpc(su, 'eth_getBlockByNumber', [hex(bn), False])
    if not tx.get('to'): return {'tx': h, 'setAside': 'contract creation'}
    pre = rpc(tu, 'debug_traceTransaction', [h, {'tracer': 'prestateTracer'}])
    ct = rpc(tu, 'debug_traceTransaction', [h, {'tracer': 'callTracer', 'tracerConfig': {'withLog': True}}])
    base = Base(su, pre, bn)
    w = World({}); w.base = base; w.watch = pmi; w.frames = []; w.loglist = []
    gp = int(rc.get('effectiveGasPrice') or tx.get('gasPrice') or '0x0', 16)
    frm = int(tx['from'], 16); to = int(tx['to'], 16)
    w.balances[frm] = base.balance(frm) - int(tx['gas'], 16) * gp
    bh = {}
    def blockhash(n):
        if n >= bn or n < bn - 256: return 0
        if n not in bh: bh[n] = int(rpc(su, 'eth_getBlockByNumber', [hex(n), False])['hash'], 16)
        return bh[n]
    w.env = {'origin': frm, 'gasprice': gp, 'coinbase': int(blk['miner'], 16), 'timestamp': int(blk['timestamp'], 16), 'number': bn,
             'prevrandao': int(blk.get('mixHash') or '0x0', 16), 'gaslimit': int(blk['gasLimit'], 16), 'chainid': cid,
             'basefee': int(blk.get('baseFeePerGas') or '0x0', 16), 'blockhash': blockhash}
    w.max_steps = 30_000_000
    # gas is not modelled: frames that ran out of gas in the block are failed in the rerun at the same (callee, input)
    oog = {}
    def ow(n):
        if n.get('type') in ('CALL', 'STATICCALL', 'DELEGATECALL', 'CALLCODE'):
            oog.setdefault((int(n.get('to') or '0x0', 16), bytes.fromhex((n.get('input') or '0x')[2:])), []).append('gas' in (n.get('error') or '').lower())
        for c in n.get('calls', []) or []: ow(c)
    for c in ct.get('calls', []) or []: ow(c)
    w.oog = oog if any(any(v) for v in oog.values()) else None
    res = {'tx': h, 'block': bn, 'index': int(rc['transactionIndex'], 16)}
    try:
        ok, ret = w.call(frm, to, int(tx['value'], 16), bytes.fromhex(tx['input'][2:]), False, 0)
    except NotImplementedError as e:
        res['setAside'] = 'interpreter: ' + str(e)[:80]; return res
    except TimeoutError:
        res['setAside'] = 'step limit'; return res
    res['steps'] = w.steps; res['forcedOOG'] = w.forced
    res['status'] = [int(rc['status'], 16), int(ok)]
    rl = [(int(l['address'], 16), tuple(int(t, 16) for t in l['topics']), bytes.fromhex(l['data'][2:])) for l in rc['logs']]
    if not ok: w.loglist = []
    res['logs'] = [len(rl), len(w.loglist), rl == w.loglist]
    tf = []; tree_pm(ct, pm, tf)
    pf = [{'input': '0x' + f['input'].hex(), 'ok': f.get('ok'), 'ret': '0x' + (f.get('ret') or b'').hex(), 'value': f['value']} for f in w.frames]
    fm = []
    for i in range(max(len(tf), len(pf))):
        a = tf[i] if i < len(tf) else None; b = pf[i] if i < len(pf) else None
        if a is None or b is None or a['input'] != b['input'] or a['ok'] != b['ok'] or (a['ok'] and a['ret'] != b['ret']):
            fm.append({'i': i, 'trace': a and {k: a[k] for k in ('input', 'ok', 'ret', 'err')}, 'rerun': b})
    res['frames'] = [len(tf), len(pf), len(fm) == 0]
    if fm: res['frameMismatch'] = fm[:3]
    res['sels'] = [f['input'][:10] for f in tf]
    # storage the rerun changed in the PoolManager
    wr = {k: v for (a, k), v in w.storage.items() if a == pmi and v != base.st.get((a, k), None)}
    dpost = None
    try:
        d = rpc(tu, 'debug_traceTransaction', [h, {'tracer': 'prestateTracer', 'tracerConfig': {'diffMode': True}}])
        post = {int(a, 16): v for a, v in d.get('post', {}).items()}.get(pmi, {}).get('storage', {}) or {}
        dpre = {int(a, 16): v for a, v in d.get('pre', {}).items()}.get(pmi, {}).get('storage', {}) or {}
        dpost = {int(k, 16): int(v, 16) for k, v in post.items()}
        for k in dpre:
            if int(k, 16) not in dpost: dpost[int(k, 16)] = 0
    except Exception as e:
        res['diffError'] = str(e)[:100]
    if dpost is not None:
        res['storageVsDiff'] = [len(wr), len(dpost), wr == dpost]
        if wr != dpost: res['storageDiffDetail'] = [[hex(k), hex(wr.get(k, -1)), hex(dpost.get(k, -1))] for k in sorted(set(wr) | set(dpost)) if wr.get(k) != dpost.get(k)][:6]
    if last_in_block:
        bad = []
        for k, v in wr.items():
            got = int(rpc(su, 'eth_getStorageAt', [pm, '0x%064x' % k, hex(bn)]), 16)
            if got != v: bad.append([hex(k), hex(v), hex(got)])
        res['storageVsBlock'] = [len(wr), len(bad) == 0]
        if bad: res['storageBlockDetail'] = bad[:6]
    res['misses'] = base.misses[:10]; res['nMisses'] = len(base.misses)
    try:
        res['families'] = families(ct, pm, lambda k: base.storage(pmi, k))
    except Exception as e:
        res['familiesError'] = str(e)[:120]
    res['branches'] = sorted([pc, int(o)] for (a, pc), outs in w.branches.items() if a == pmi for o in outs)
    return res

if __name__ == '__main__':
    r = rerun(int(sys.argv[1]), sys.argv[2], len(sys.argv) > 3 and sys.argv[3] == '1')
    r2 = dict(r); r2['branches'] = len(r.get('branches', []))
    print(json.dumps(r2, indent=1)[:3000])
