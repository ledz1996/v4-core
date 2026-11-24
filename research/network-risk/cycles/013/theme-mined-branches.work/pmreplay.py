"""PoolManager-only replay of a mined transaction in pyevm2.

Every frame of the PoolManager in the block's call tree is executed again in pyevm2 from the
PoolManager's storage before the transaction. Calls the PoolManager makes to other contracts
(tokens, hooks, unlock callbacks) are answered from the call tree: the recorded success flag
and return data are handed back, and the PoolManager frames recorded inside that call are
executed first, in order, with their recorded caller, value and input. A call recorded as
failed rolls back what the PoolManager frames inside it did. Gas, other contracts' code and
their state therefore cannot make the rerun diverge; only the PoolManager's own code, storage,
transient storage and the data it was given are in play.

Checked against block production: each PoolManager frame's success and return data (the
call tree), the PoolManager's logs against the receipt, and every storage word the rerun
changed against the diffMode post state and, for the last PoolManager transaction of a block,
against eth_getStorageAt at the block. Any outgoing call whose callee or input differs from
the recorded one is a divergence and is reported.
"""
import sys, json
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/013/theme-mined-branches.work')
from common import *
import pyevm2
from pyevm2 import World
from rerun import Base
from families import families

class Div(Exception): pass

class PMWorld(World):
    def call(self, caller, to, value, data, static, depth, code_addr=None, storage_addr=None):
        ca = to if code_addr is None else code_addr
        if ca == self.pm and to == self.pm:
            node = self.pending
            if 'gas' in (node.get('error') or '').lower():
                # gas is not modelled: a PoolManager frame that ran out of gas in the block fails here without running
                self.forced += 1
                self.frames.append({'input': '0x' + bytes(data).hex(), 'ok': False, 'ret': '0x', 'node': node, 'forced': True})
                return False, b''
            snap = self.snapshot()
            self.balances[self.pm] = self.bal(self.pm) + value
            self.stack.append([node, 0])
            try:
                ok, ret = self.run(self.pm, self.pm, caller, value, data, static, depth)
            except pyevm2.Halt:
                ok, ret = False, b''
            fr = self.stack.pop()
            kids = [c for c in node.get('calls', []) or [] if c.get('type') in ('CALL', 'STATICCALL', 'DELEGATECALL', 'CALLCODE')]
            if ok and fr[1] != len(kids): self.divs.append({'kind': 'fewer outgoing calls', 'made': fr[1], 'recorded': len(kids)})
            if not ok: self.restore(snap)
            self.frames.append({'input': '0x' + bytes(data).hex(), 'ok': ok, 'ret': '0x' + ret.hex(), 'node': node})
            return ok, ret
        # an outgoing call from the PoolManager: answer it from the recorded tree
        top = self.stack[-1]; node = top[0]
        kids = [c for c in node.get('calls', []) or [] if c.get('type') in ('CALL', 'STATICCALL', 'DELEGATECALL', 'CALLCODE')]
        if top[1] >= len(kids):
            self.divs.append({'kind': 'extra outgoing call', 'to': '0x%040x' % to, 'input': bytes(data[:36]).hex()}); raise Div()
        rec = kids[top[1]]; top[1] += 1
        if int(rec.get('to') or '0x0', 16) != to or (rec.get('input') or '0x').lower() != '0x' + bytes(data).hex() or int(rec.get('value') or '0x0', 16) != value:
            self.divs.append({'kind': 'outgoing call differs', 'recordedTo': rec.get('to'), 'to': '0x%040x' % to, 'recordedInput': (rec.get('input') or '')[:74],
                              'input': '0x' + bytes(data[:36]).hex(), 'value': [int(rec.get('value') or '0x0', 16), value]}); raise Div()
        snap = self.snapshot()
        if value:
            self.balances[self.pm] = self.bal(self.pm) - value
        self.replay_children(rec)
        ok = 'error' not in rec
        if not ok: self.restore(snap)
        return ok, bytes.fromhex((rec.get('output') or '0x')[2:]) if ok or rec.get('output') else b''

    def replay_children(self, n):
        for c in n.get('calls', []) or []:
            if c.get('type') not in ('CALL', 'STATICCALL', 'DELEGATECALL', 'CALLCODE', 'CREATE', 'CREATE2'): continue
            if int(c.get('to') or '0x0', 16) == self.pm and c.get('type') in ('CALL', 'STATICCALL'):
                self.pending = c
                ok, ret = self.call(int(c['from'], 16), self.pm, int(c.get('value') or '0x0', 16), bytes.fromhex((c.get('input') or '0x')[2:]), c['type'] == 'STATICCALL', 1)
            else:
                snap = self.snapshot()
                # value the PoolManager receives from a frame that is not its own call is not modelled; frames into it are
                self.replay_children(c)
                if 'error' in c: self.restore(snap)

def pmreplay(cid, h, last_in_block=False):
    tu = TRACE[cid]; su = STATE[cid]
    pm = NETS[cid]['poolManager'].lower(); pmi = int(pm, 16)
    rc = rpc(RECEIPT.get(cid, su), 'eth_getTransactionReceipt', [h]); bn = int(rc['blockNumber'], 16)
    ct = rpc(tu, 'debug_traceTransaction', [h, {'tracer': 'callTracer', 'tracerConfig': {'withLog': True}}])
    pre = rpc(tu, 'debug_traceTransaction', [h, {'tracer': 'prestateTracer'}])
    pre = {a: v for a, v in pre.items() if a.lower() == pm}
    base = Base(su, pre, bn)
    code = bytes.fromhex(rpc(su, 'eth_getCode', [pm, hex(bn - 1)])[2:])
    w = PMWorld({pmi: code}); w.base = base; w.pm = pmi; w.frames = []; w.loglist = []; w.stack = []; w.divs = []
    w.env = {}; w.max_steps = 50_000_000
    res = {'tx': h, 'block': bn, 'index': int(rc['transactionIndex'], 16), 'status': int(rc['status'], 16)}
    try:
        if (ct.get('to') or '').lower() == pm:
            w.pending = ct
            w.call(int(ct['from'], 16), pmi, int(ct.get('value') or '0x0', 16), bytes.fromhex(ct['input'][2:]), False, 0)
        else:
            w.replay_children(ct)
            if 'error' in ct: w.loglist = []; w.storage = {}
    except Div:
        res['divergence'] = w.divs[:3]; return res
    except NotImplementedError as e:
        res['setAside'] = 'interpreter: ' + str(e)[:80]; return res
    except TimeoutError:
        res['setAside'] = 'step limit'; return res
    if w.divs: res['divergence'] = w.divs[:3]
    res['steps'] = w.steps; res['forcedOOG'] = w.forced
    # frames
    fm = [f for f in w.frames if f['ok'] != ('error' not in f['node']) or (f['ok'] and f['ret'] != (f['node'].get('output') or '0x').lower())]
    res['frames'] = [len(w.frames), len(fm) == 0]
    if fm: res['frameMismatch'] = [{'input': f['input'][:74], 'ok': f['ok'], 'ret': f['ret'][:140], 'recOk': 'error' not in f['node'], 'recRet': (f['node'].get('output') or '')[:140], 'recErr': f['node'].get('error')} for f in fm[:3]]
    rl = [(int(l['address'], 16), tuple(int(t, 16) for t in l['topics']), bytes.fromhex(l['data'][2:])) for l in rc['logs'] if l['address'].lower() == pm]
    if res['status'] == 0: rl = []
    pl = [x for x in w.loglist if x[0] == pmi]
    res['logs'] = [len(rl), len(pl), rl == pl]
    wr = {k: v for (a, k), v in w.storage.items() if a == pmi and v != base.st.get((a, k), None)}
    try:
        d = rpc(tu, 'debug_traceTransaction', [h, {'tracer': 'prestateTracer', 'tracerConfig': {'diffMode': True}}])
        post = {a.lower(): v for a, v in d.get('post', {}).items()}.get(pm, {}).get('storage', {}) or {}
        dpre = {a.lower(): v for a, v in d.get('pre', {}).items()}.get(pm, {}).get('storage', {}) or {}
        dpost = {int(k, 16): int(v, 16) for k, v in post.items()}
        for k in dpre:
            if int(k, 16) not in dpost: dpost[int(k, 16)] = 0
        res['storageVsDiff'] = [len(wr), len(dpost), wr == dpost]
        if wr != dpost: res['storageDiffDetail'] = [[hex(k), hex(wr.get(k, -1)), hex(dpost.get(k, -1))] for k in sorted(set(wr) | set(dpost)) if wr.get(k) != dpost.get(k)][:6]
    except Exception as e:
        res['diffError'] = str(e)[:100]
    if last_in_block:
        bad = []
        for k, v in wr.items():
            got = int(rpc(su, 'eth_getStorageAt', [pm, '0x%064x' % k, hex(bn)]), 16)
            if got != v: bad.append([hex(k), hex(v), hex(got)])
        res['storageVsBlock'] = [len(wr), len(bad) == 0]
        if bad: res['storageBlockDetail'] = bad[:6]
    res['nMisses'] = len(base.misses)
    try: res['families'] = families(ct, pm, lambda k: base.storage(pmi, k))
    except Exception as e: res['familiesError'] = str(e)[:120]
    res['branches'] = sorted([pc, int(o)] for (a, pc), outs in w.branches.items() if a == pmi for o in outs)
    return res

if __name__ == '__main__':
    r = pmreplay(int(sys.argv[1]), sys.argv[2], len(sys.argv) > 3 and sys.argv[3] == '1')
    r['branches'] = len(r.get('branches', []))
    print(json.dumps(r)[:2500])
