"""Cycle 25 copy of cycle 24 replaycov.py (testnet PoolManager addresses added, PMADDR/PMCID env). Cycle 24, theme-producer-branch-coverage, tasks 1 and 2.
Run every PoolManager frame of the transactions that cycle 23 replayed (theme-state-replay.work/raw/<cid>/tx) through
pyevm_cov (tools/opdiff/pyevm.py with two counters) from the recorded prestate, offline. Calls the PoolManager makes to
other contracts are answered from the recorded call tree (callTracer): recorded success, return data, and the
PoolManager frames recorded inside them are executed in order with their recorded caller, value and input (method of
cycle 13 pmreplay.py). Checked per transaction: every PoolManager frame's success flag and return data against the call
tree, every outgoing call's target, value and input against the call tree, and the PoolManager storage the rerun wrote
against the diffMode post state. Counted: each side of each JUMPI, and operands of watched instructions.
usage: replaycov.py <cid> <shard> <nshards> [limit]   writes ../out/<cid>/shard<k>.json"""
import sys, os, json, gzip, glob, time
sys.setrecursionlimit(20000)
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import pyevm_cov as P
from sites import sites
NR = '/home/user/v4-core/research/network-risk'
RAW = NR + '/cycles/023/theme-state-replay.work/raw'
NETS = {n['chainId']: n for n in json.load(open(NR + '/state/networks.json'))['networks']}
NETS.update({6343: {'poolManager': '0xea338f5d6065c384e4defd7784b59e9c36c94e4d'}})
if os.environ.get('PMADDR'): NETS[int(os.environ['PMCID'])] = {'poolManager': os.environ['PMADDR']}
B = json.load(open(NR + '/build/PoolManager.json'))
WOPS = {'MULMOD','ADDMOD','SAR','SIGNEXTEND','BYTE','SHL','SHR','SDIV','SMOD','DIV','MOD','EXP','SLT','SGT','LT','GT','MUL','ADD','SUB'}
NARG = {'MULMOD': 3, 'ADDMOD': 3}
M = (1 << 256) - 1
def s256(x): return x - (1 << 256) if x >> 255 else x
def code_for(pm):
    c = bytearray(bytes.fromhex(B['runtime']))
    for r in B['immutableReferences']['1375']:
        c[r['start']:r['start'] + 32] = int(pm, 16).to_bytes(32, 'big')
    return bytes(c)
class Div(Exception): pass
KIDS = ('CALL', 'STATICCALL', 'DELEGATECALL', 'CALLCODE')
class PMWorld(P.World):
    def call(self, caller, to, value, data, static, depth, code_addr=None, storage_addr=None, apparent=None):
        ca = to if code_addr is None else code_addr
        if ca == self.pm and to == self.pm:
            node = self.pending
            if 'gas' in (node.get('error') or '').lower():
                self.forced += 1; self.frames.append((node, False, b'', True)); return False, b''
            snap = self.snapshot()
            self.balances[self.pm] = self.balances.get(self.pm, 0) + value
            self.stack.append([node, 0])
            try:
                ok, ret = self.run(self.pm, self.pm, caller, value, data, static, depth)
            except P.Halt:
                ok, ret = False, b''
            fr = self.stack.pop()
            kids = [c for c in node.get('calls', []) or [] if c.get('type') in KIDS]
            if ok and fr[1] != len(kids): self.divs.append({'kind': 'fewer outgoing calls', 'made': fr[1], 'recorded': len(kids)})
            if not ok: self.restore(snap)
            self.frames.append((node, ok, ret, False)); return ok, ret
        top = self.stack[-1]; node = top[0]
        kids = [c for c in node.get('calls', []) or [] if c.get('type') in KIDS]
        if top[1] >= len(kids):
            self.divs.append({'kind': 'extra outgoing call', 'to': '0x%040x' % to, 'input': bytes(data[:36]).hex()}); raise Div()
        rec = kids[top[1]]; top[1] += 1
        if int(rec.get('to') or '0x0', 16) != to or (rec.get('input') or '0x').lower() != '0x' + bytes(data).hex() or int(rec.get('value') or '0x0', 16) != value:
            self.divs.append({'kind': 'outgoing call differs', 'recordedTo': rec.get('to'), 'to': '0x%040x' % to, 'recordedInput': (rec.get('input') or '')[:74],
                              'input': '0x' + bytes(data[:36]).hex()}); raise Div()
        snap = self.snapshot()
        if value: self.balances[self.pm] = self.balances.get(self.pm, 0) - value
        self.replay_children(rec)
        ok = 'error' not in rec
        if not ok: self.restore(snap)
        return ok, bytes.fromhex((rec.get('output') or '0x')[2:]) if ok or rec.get('output') else b''
    def replay_children(self, n):
        for c in n.get('calls', []) or []:
            if c.get('type') not in KIDS + ('CREATE', 'CREATE2'): continue
            if int(c.get('to') or '0x0', 16) == self.pm and c.get('type') in ('CALL', 'STATICCALL'):
                self.pending = c
                self.call(int(c['from'], 16), self.pm, int(c.get('value') or '0x0', 16), bytes.fromhex((c.get('input') or '0x')[2:]), c['type'] == 'STATICCALL', 1)
            else:
                snap = self.snapshot(); self.replay_children(c)
                if 'error' in c: self.restore(snap)
class Stat:
    __slots__ = ('n', 'mn', 'mx', 'smn', 'smx', 'neg', 'bl')
def main():
    cid, shard, nsh = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]); lim = int(sys.argv[4]) if len(sys.argv) > 4 else 10 ** 9
    pm = NETS[cid]['poolManager'].lower(); pmi = int(pm, 16); code = code_for(pm)
    files = sorted(glob.glob(os.environ['RAWDIR'] + '/*.json.gz') if os.environ.get('RAWDIR') else glob.glob('%s/%d/tx/*.json.gz' % (RAW, cid)))[:lim][shard::nsh]
    watch = {}; nm = {}
    for p, n, f, l, s in sites():
        if n in WOPS: watch[p] = n
    W = {}  # pc -> [count, per-operand [min,max,smin,smax,neg,bitlenset]]
    DET = {}
    MINP, MAXP = 4295128739, 1461446703485210103287273052203988822378723970342
    def bm(v): v = s256(v); return ('neg' if v < 0 else 'nonneg', 'bit0' if v & 0xff == 0 else ('bit255' if v & 0xff == 255 else 'mid'))
    DETAIL = {19307: lambda st: bm(st[-2]), 21130: lambda st: bm(st[-2]), 16675: lambda st: bm(st[-2]),
              16746: lambda st: ('absTick>821736' if st[-1] > 887272 - 65536 else ('absTick=0' if st[-1] == 0 else 'mid'),),
              16736: lambda st: ('tickNeg' if s256(st[-2]) < 0 else 'tickNonneg',),
              17995: lambda st: ('a<2^16' if st[-1] < 65536 else ('b-a<2^16' if 0 <= st[-2] - st[-1] < 65536 else 'mid'), 'a<=b' if st[-1] <= st[-2] else 'a>b'),
              17796: lambda st: ('yNeg' if s256(st[-2]) & (1 << 127) else 'yNonneg',)}
    def cb(pc, op, st):
        if pc in DETAIL:
            k = (pc,) + DETAIL[pc](st); DET[k] = DET.get(k, 0) + 1
        k = NARG.get(watch[pc], 2) if watch[pc] not in ('SIGNEXTEND',) else 2
        e = W.get(pc)
        if e is None: e = W[pc] = [0, [[M + 1, -1, 1 << 256, -(1 << 256), 0, set()] for _ in range(k)]]
        e[0] += 1
        for i in range(k):
            v = st[-1 - i]; a = e[1][i]
            if v < a[0]: a[0] = v
            if v > a[1]: a[1] = v
            sv = s256(v)
            if sv < a[2]: a[2] = sv
            if sv > a[3]: a[3] = sv
            if sv < 0: a[4] += 1
            a[5].add(v.bit_length())
    bc = {}; tot = {'txs': 0, 'frames': 0, 'frameMismatch': 0, 'div': 0, 'storageMismatch': 0, 'storageChecked': 0, 'forcedOOG': 0,
                    'setAside': 0, 'steps': 0, 'failedTxRecorded': 0}
    pertx = {}; bad = []
    t0 = time.time()
    for fn in files:
        rec = json.load(gzip.open(fn))
        pre = next((v for k, v in rec['pre'].items() if k.lower() == pm), {})
        dpre = next((v for k, v in rec['diff']['pre'].items() if k.lower() == pm), {})
        dpost = next((v for k, v in rec['diff']['post'].items() if k.lower() == pm), {})
        w = PMWorld({pmi: code}, {pmi: int(pre.get('balance', '0x0'), 16)})
        for k, v in (pre.get('storage') or {}).items(): w.storage[(pmi, int(k, 16))] = int(v, 16)
        base = dict(w.storage)
        w.pm = pmi; w.frames = []; w.stack = []; w.divs = []; w.forced = 0; w.max_steps = 50_000_000
        w.watch = set(watch); w.watch_addr = pmi; w.watch_cb = cb
        ct = rec['call']; tot['txs'] += 1
        if ct.get('error'): tot['failedTxRecorded'] += 1
        try:
            if (ct.get('to') or '').lower() == pm:
                w.pending = ct; w.call(int(ct['from'], 16), pmi, int(ct.get('value') or '0x0', 16), bytes.fromhex(ct['input'][2:]), False, 0)
            else:
                w.replay_children(ct)
        except Div:
            tot['div'] += 1; bad.append({'hash': rec['hash'], 'kind': 'divergence', 'divs': w.divs[:3]}); continue
        except (NotImplementedError, TimeoutError) as e:
            tot['setAside'] += 1; bad.append({'hash': rec['hash'], 'kind': 'setAside', 'err': str(e)[:200]}); continue
        tot['steps'] += w.steps; tot['forcedOOG'] += w.forced; tot['frames'] += len(w.frames)
        fm = [(nd, ok, ret) for nd, ok, ret, forced in w.frames if not forced and (ok != ('error' not in nd) or (ok and '0x' + ret.hex() != (nd.get('output') or '0x').lower()))]
        if fm:
            tot['frameMismatch'] += 1
            bad.append({'hash': rec['hash'], 'kind': 'frame', 'detail': [{'input': nd.get('input', '')[:200], 'ok': ok, 'ret': ret.hex()[:400], 'recErr': nd.get('error'), 'recOut': (nd.get('output') or '')[:402]} for nd, ok, ret in fm[:3]]})
        if not ct.get('error'):
            wr = {k: v for (a, k), v in w.storage.items() if a == pmi and v != base.get((a, k))}
            post = {int(k, 16): int(v, 16) for k, v in (dpost.get('storage') or {}).items()}
            for k in (dpre.get('storage') or {}):
                if int(k, 16) not in post: post[int(k, 16)] = 0
            post = {k: v for k, v in post.items() if v != base.get((pmi, k))}
            tot['storageChecked'] += 1
            if wr != post:
                tot['storageMismatch'] += 1
                bad.append({'hash': rec['hash'], 'kind': 'storage', 'detail': [[hex(k), hex(wr.get(k, -1)), hex(post.get(k, -1))] for k in sorted(set(wr) | set(post)) if wr.get(k) != post.get(k)][:20]})
        keys = []
        for (a, pc, side), c in w.bcount.items():
            bc[(pc, side)] = bc.get((pc, side), 0) + c; keys.append(pc * 2 + int(side))
        pertx[rec['hash']] = sorted(keys)
    tot['secs'] = round(time.time() - t0, 1)
    out = {'chainId': cid, 'shard': shard, 'nshards': nsh, 'totals': tot, 'mismatches': bad,
           'branches': {'%d:%d' % (pc, int(s)): c for (pc, s), c in bc.items()},
           'watch': {str(pc): [watch[pc], e[0], [[a[0], a[1], a[2], a[3], a[4], sorted(a[5])] for a in e[1]]] for pc, e in W.items()},
           'pertx': pertx, 'detail': {'|'.join(map(str, k)): v for k, v in DET.items()}}
    os.makedirs('%s/../out/%d' % (HERE, cid), exist_ok=True)
    json.dump(out, open('%s/../out/%d/%sshard%d.json' % (HERE, cid, os.environ.get('OUTTAG', ''), shard), 'w'))
    print(json.dumps(tot))
if __name__ == '__main__': main()
